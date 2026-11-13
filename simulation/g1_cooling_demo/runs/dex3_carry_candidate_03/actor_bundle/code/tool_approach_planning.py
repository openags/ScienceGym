"""Propose an arm approach using RGB-D geometry and an unposed grasp prior.

Only the robot model, fixed architectural map, observed point cloud, estimated
tool frame and tool-local grasp geometry enter this planner. No plant object
state or prerecorded arm path is used. Sampled clearance is a planning check;
independent continuous physical execution remains required.
"""
import mujoco
import numpy as np
import trimesh
from scipy.spatial import cKDTree

from ftir_hand import ArmIK
from joint_rrt import plan as plan_rrt
from robot_source_meshes import robot_source_meshes, source_adjacency
from source_proximity import SourceClearance


def depth_points(depth, world_from_camera, fovy):
    depth=np.asarray(depth,dtype=float);h,w=depth.shape
    fy=h/(2*np.tan(np.deg2rad(fovy/2)))
    y,x=np.mgrid[:h,:w]
    local=np.stack([(x+.5-w/2)*depth/fy,-(y+.5-h/2)*depth/fy,-depth],axis=-1)
    T=np.asarray(world_from_camera)
    valid=np.isfinite(depth)&(depth>.05)&(depth<2.)
    return local[valid]@T[:3,:3].T+T[:3,3]


def depth_surface(depth,world_from_camera,fovy):
    """Connect adjacent valid depth pixels, excluding depth discontinuities."""
    depth=np.asarray(depth);h,w=depth.shape
    valid=np.isfinite(depth)&(depth>.05)&(depth<2.)
    ids=np.full((h,w),-1,dtype=int);ids[valid]=np.arange(valid.sum())
    faces=np.concatenate([np.stack([ids[:-1,:-1],ids[1:,:-1],ids[:-1,1:]],axis=-1).reshape(-1,3),
        np.stack([ids[1:,1:],ids[:-1,1:],ids[1:,:-1]],axis=-1).reshape(-1,3)])
    faces=faces[np.all(faces>=0,axis=1)]
    points=depth_points(depth,world_from_camera,fovy)
    triangles=points[faces]
    edges=np.stack([triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0],triangles[:,2]-triangles[:,1]],axis=1)
    faces=faces[np.max(np.linalg.norm(edges,axis=2),axis=1)<.006]
    return trimesh.Trimesh(vertices=points,faces=faces,process=False)


class ToolApproachPlanner:
    def __init__(self, model, robot_qpos, pose, grasp, tool_mesh, observed_surface, observed_tool_points):
        self.m=model;self.d=mujoco.MjData(model);self.d.qpos[:]=robot_qpos
        self.ik=ArmIK(model)
        # A source-limit-safe elbow family; not a hidden source-limit change.
        self.ik.low[3]=max(self.ik.low[3],.15)
        self.grasp=grasp
        def midpoint():
            w=self.d.site('right_wrist_reference')
            pts=np.array([self.d.body(r['body']).xpos+self.d.body(r['body']).xmat.reshape(3,3)@np.asarray(r['point_local_m'])
                for r in grasp['robot_contact_features']])
            return w.xmat.reshape(3,3).T@(np.array([.5,.25,.25])@pts-w.xpos)
        for n,v in grasp['grasp_hand_q'].items():self.d.joint(n).qpos[0]=v
        mujoco.mj_forward(model,self.d);closed_midpoint=midpoint()
        for n,v in grasp['pregrasp_hand_q'].items():self.d.joint(n).qpos[0]=v
        mujoco.mj_forward(model,self.d);self.initial=self.d.qpos.copy()
        self.registration=np.eye(4)
        self.registration[:3,:3]=pose['rotation_matrix'];self.registration[:3,3]=pose['position_m']
        self.target=self.registration@np.asarray(grasp['source_tool_from_wrist'])
        self.target[:3,3]-=self.target[:3,:3]@(midpoint()-closed_midpoint)
        # The original body uses group 2; the official three-finger subtree
        # preserves its source visual group 1. Both must be planned.
        self.source=robot_source_meshes(model,visual_groups=(1,2))
        required={model.body(b).name for b in range(model.nbody)
            if (model.body(b).name or '').startswith('right_hand_')}
        if not required.issubset(self.source) or 'right_wrist_yaw_link' not in self.source:
            raise ValueError('Right hand or wrist source geometry is absent from planning')
        self.robot=trimesh.collision.CollisionManager()
        for name,mesh in self.source.items():
            b=model.body(name).id;T=np.eye(4);T[:3,:3]=self.d.xmat[b].reshape(3,3);T[:3,3]=self.d.xpos[b]
            self.robot.add_object(name,mesh,T)
        self.environment=trimesh.collision.CollisionManager();meshes={}
        meshes['observed_tool_shape']=tool_mesh
        self.environment.add_object('observed_tool_shape',tool_mesh,self.registration)
        # Public map only. Handled objects are deliberately absent from it.
        for g in range(model.ngeom):
            if model.body(model.geom_bodyid[g]).name!='lab_architecture' or model.geom_group[g]!=2:continue
            mid=model.geom_dataid[g];va,vn=model.mesh_vertadr[mid],model.mesh_vertnum[mid]
            fa,fn=model.mesh_faceadr[mid],model.mesh_facenum[mid]
            mesh=trimesh.Trimesh(vertices=model.mesh_vert[va:va+vn],faces=model.mesh_face[fa:fa+fn],process=False)
            T=np.eye(4);T[:3,:3]=self.d.geom_xmat[g].reshape(3,3);T[:3,3]=self.d.geom_xpos[g]
            pts=mesh.vertices@T[:3,:3].T+T[:3,3]
            if np.any(pts.max(0)<self.d.qpos[:3]-1.3) or np.any(pts.min(0)>self.d.qpos[:3]+1.3):continue
            name='architecture::'+model.geom(g).name
            meshes[name]=mesh;self.environment.add_object(name,mesh,T)
        points=np.asarray(observed_surface.vertices,dtype=float)
        # Observed surfaces remain obstacles. The known tool is represented
        # by its registered original mesh instead of duplicate pixel faces.
        # Remove only the exact pixels belonging to the detected component;
        # a bounding box must not erase nearby tray/support observations.
        component=np.asarray(observed_tool_points,dtype=float)
        inside=cKDTree(component).query(points)[0]<1e-8
        keep=(~inside)&np.all(abs(points-self.d.qpos[:3])<1.2,axis=1)&(points[:,2]>.82)
        faces=observed_surface.faces[np.all(keep[observed_surface.faces],axis=1)]
        if len(faces):
            mesh=trimesh.Trimesh(vertices=points,faces=faces,process=False)
            mesh.remove_unreferenced_vertices()
            meshes['observed_depth_surface']=mesh;self.environment.add_object('observed_depth_surface',mesh)
        self.observed_faces=len(faces)
        self.environment_meshes=meshes
        # Finger coordinates are fixed during this arm path. Original palm
        # assembly overlap is not changed or removed; native contact checking
        # and the execution evaluator still use official collision geometry.
        active=list(self.ik.joints)
        adjacent=source_adjacency(model,self.source)
        self.clearance=SourceClearance(model,self.d,self.robot,self.source,self.environment,meshes,
            active,adjacent,check_fixed_environment=False)
        self.last_clearance=None

    def state(self,q):
        self.d.qpos[:]=self.initial;self.d.qpos[self.ik.qa]=q
        mujoco.mj_kinematics(self.m,self.d);mujoco.mj_comPos(self.m,self.d)

    def valid(self,q,margin=.0001):
        self.state(q);self.last_clearance=self.clearance.check(margin)
        return self.last_clearance['clear']

    def observed_arm_clearance(self,robot_qpos,margin):
        """Check the instantaneous right arm against current body and map.

        This is a new encoder-derived state, not a claim that the other body
        joints stayed at their planning values. Other-body self-collisions and
        support are outside this arm guard and remain full-plant obligations.
        The original fixed-state guard is restored for later path queries.
        """
        q=np.asarray(robot_qpos,dtype=float)
        hand=[self.m.joint(n).qposadr[0] for n in self.grasp['pregrasp_hand_q']]
        if np.max(abs(q[hand]-self.initial[hand]))>.002:
            return dict(clear=False,kind='preshape_tracking_error')
        saved=self.d.qpos.copy();fixed=self.clearance.fixed_state.copy()
        try:
            self.d.qpos[:]=q;mujoco.mj_kinematics(self.m,self.d);mujoco.mj_comPos(self.m,self.d)
            self.clearance.fixed_state=self.d.qpos[self.clearance.fixed].copy()
            return self.clearance.check(margin)
        finally:
            self.clearance.fixed_state=fixed;self.d.qpos[:]=saved
            mujoco.mj_kinematics(self.m,self.d);mujoco.mj_comPos(self.m,self.d)

    def build(self):
        home=self.initial[self.ik.qa].copy();attempts=[]
        if not self.valid(home):
            return dict(planned=False,reason='initial_clearance',detail=self.last_clearance)
        # IK proposals come from current encoders and generic elbow seeds,
        # not from an earlier authored full-body grasp pose.
        seeds=[home,np.array([-.8,-.3,.5,.7,0.,.8,.3]),np.array([-.8,-.5,0.,1.4,0.,0.,0.])]
        for index,seed in enumerate(seeds):
            self.state(home)
            final,pe,re=self.ik.solve(self.d,self.target[:3,3],self.target[:3,:3],np.clip(seed,self.ik.low,self.ik.high))
            row=dict(seed=index,position_error_m=pe,rotation_error_rad=re);attempts.append(row)
            if pe>.0005 or re>.01:row['failure']='grasp_ik';continue
            if not self.valid(final):row.update(failure='grasp_clearance',detail=self.last_clearance);continue
            # First arrive above the supported tool, then lower with the hand
            # open. The last segment is separately checked at 1 mm spacing.
            row['raised_proposals']=[];entry=None
            for height in [.04,.03,.02,.015]:
                raised=self.target[:3,3]+np.array([0.,0.,height])
                q,pe,re=self.ik.solve(self.d,raised,self.target[:3,:3],final)
                proposal=dict(height_m=height,position_error_m=pe,rotation_error_rad=re)
                row['raised_proposals'].append(proposal)
                if pe>.0005 or re>.01:proposal['failure']='ik';continue
                if not self.valid(q,.002):proposal.update(failure='clearance',detail=self.last_clearance);continue
                entry=q;row['selected_approach_height_m']=height;break
            if entry is None:row['failure']='raised_approach';continue
            approach=[entry.copy()];previous=entry.copy();bad=None
            for fraction in np.linspace(0,1,41)[1:]:
                self.state(previous)
                q,pe,re=self.ik.solve(self.d,raised+fraction*(self.target[:3,3]-raised),self.target[:3,:3],previous)
                if pe>.0005 or re>.01 or not self.valid(q):
                    bad=dict(fraction=float(fraction),position_error_m=pe,rotation_error_rad=re,clearance=self.last_clearance);break
                approach.append(q.copy());previous=q
            if bad:row.update(failure='lowering_segment',detail=bad);continue
            path,metrics=plan_rrt(home,entry,self.ik.low,self.ik.high,lambda q:self.valid(q,.002),seed=7351,iterations=3000)
            row['rrt']=metrics
            if path is None:row['failure']='entry_path';continue
            return dict(planned=True,entry_path=[q.tolist() for q in path],lowering_path=[q.tolist() for q in approach],
                target_wrist_position_m=self.target[:3,3].tolist(),target_wrist_rotation=self.target[:3,:3].tolist(),
                pregrasp_hand_q=self.grasp['pregrasp_hand_q'],attempts=attempts,observed_surface_faces=self.observed_faces,
                clearance_metrics=self.clearance.metrics(),physical_execution=False,qualified_approach=False,
                unobserved_free_space_certified=False)
        return dict(planned=False,attempts=attempts,observed_surface_faces=self.observed_faces,qualified_approach=False)
