"""Plan from robot encoders/IMU, observed key row and unposed public CAD.

The actor's static architectural map contains the bench. No loose laboratory
asset poses, device joints, recorded arm path or physical contact list enters
this module. Device motion below is a geometric prediction, not a plant write.
"""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from ftir_cover_geometry import register
from ftir_hand import ArmIK,mimic
from joint_rrt import plan as plan_rrt
from robot_source_meshes import robot_source_meshes,source_adjacency
from source_proximity import SourceClearance


class SliderPlanner:
    def __init__(self,model,estimated,observations,prior_path,shape_path):
        self.m=model;self.d=mujoco.MjData(model);self.d.qpos[:]=estimated.qpos
        mimic(model,self.d);mujoco.mj_forward(model,self.d)
        self.initial=self.d.qpos.copy();self.ik=ArmIK(model)
        self.prior=json.loads(Path(prior_path).read_text())
        if hashlib.sha256(Path(shape_path).read_bytes()).hexdigest()!=self.prior['source_shape_sha256']:
            raise ValueError('Known device shape changed')
        if len(observations)<8:raise ValueError('Need eight accepted key-row observations')
        frames=[register(o,self.prior) for o in observations[-8:]]
        self.rotation=Rotation.from_matrix(np.array([R for R,t in frames])).mean().as_matrix()
        self.translation=np.median([t for R,t in frames],axis=0)
        self.registration=np.eye(4);self.registration[:3,:3]=self.rotation;self.registration[:3,3]=self.translation
        self.environment=trimesh.collision.CollisionManager();meshes={};self.slider_rest={}
        scene=trimesh.load(shape_path,force='scene',process=False)
        for name in scene.graph.nodes_geometry:
            T,key=scene.graph[name];mesh=scene.geometry[key]
            transform=self.registration@T
            meshes[name]=mesh;self.environment.add_object(name,mesh,transform)
            if name in self.prior['slider_parts']:self.slider_rest[name]=transform
        # This map is already part of the isolated public controller model.
        # A conservative radius bounds the entire active arm from the pelvis.
        for g in range(model.ngeom):
            if model.body(model.geom_bodyid[g]).name!='lab_architecture' or model.geom_group[g]!=2:continue
            mid=model.geom_dataid[g];va,vn=model.mesh_vertadr[mid],model.mesh_vertnum[mid]
            fa,fn=model.mesh_faceadr[mid],model.mesh_facenum[mid]
            mesh=trimesh.Trimesh(vertices=model.mesh_vert[va:va+vn],faces=model.mesh_face[fa:fa+fn],process=False)
            T=np.eye(4);T[:3,:3]=self.d.geom_xmat[g].reshape(3,3);T[:3,3]=self.d.geom_xpos[g]
            points=mesh.vertices@T[:3,:3].T+T[:3,3]
            if np.any(points.max(0)<self.d.qpos[:3]-1.5) or np.any(points.min(0)>self.d.qpos[:3]+1.5):continue
            name='architecture::'+model.geom(g).name;meshes[name]=mesh;self.environment.add_object(name,mesh,T)
        self.source=robot_source_meshes(model);self.robot=trimesh.collision.CollisionManager()
        for name,mesh in self.source.items():
            b=model.body(name).id;T=np.eye(4);T[:3,:3]=self.d.xmat[b].reshape(3,3);T[:3,3]=self.d.xpos[b]
            self.robot.add_object(name,mesh,T)
        active=[j for j in range(model.njnt) if model.joint(j).name.startswith('right_') and
                any(k in model.joint(j).name for k in ['shoulder','elbow','wrist','index','thumb','middle','ring','little'])]
        adjacent=source_adjacency(model,self.source)
        self.clearance=SourceClearance(model,self.d,self.robot,self.source,self.environment,meshes,active,adjacent,check_fixed_environment=False)
        _,pairs=self.robot.in_collision_internal(return_names=True)
        _,external=self.robot.in_collision_other(self.environment,return_names=True)
        self.baseline=dict(self_intersections=[sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent],
                           environment_intersections=sorted([list(p) for p in external]))
        # Only frozen assembly overlaps may remain in the baseline. The
        # constant-qpos guard protects this assumption during each search.
        if not self.clearance.check(.002)['clear']:
            raise ValueError('Operating arm collides before planning')

    def state(self,q,hand,travel=0.):
        self.d.qpos[:]=self.initial;self.d.qpos[self.ik.qa]=q
        for n,v in hand.items():self.d.joint(n).qpos[0]=v
        mimic(self.m,self.d);mujoco.mj_forward(self.m,self.d)
        shift=self.rotation@np.asarray(self.prior['slider_axis'])*travel
        for n,T in self.slider_rest.items():
            moved=T.copy();moved[:3,3]+=shift;self.environment.set_transform(n,moved)
        self.clearance.update_environment()

    def valid(self,q,hand,travel=0.,margin=.002):
        self.state(q,hand,travel)
        return self.clearance.check(margin)['clear']

    def build(self,*,maximum_candidates=12):
        home=self.initial[self.ik.qa].copy();attempts=[]
        for candidate in self.prior['candidates'][:maximum_candidates]:
            hand=candidate['hand_q'];self.state(home,hand)
            target=self.registration@np.asarray(candidate['palm_in_device'])
            normal=self.rotation@np.asarray(candidate['outward_surface_normal'])
            direction=self.rotation@np.asarray(self.prior['slider_axis'])
            pre=target[:3,3]+normal*.02;finish=target[:3,3]+direction*.07
            seed=np.clip([-.8,-.4,0,1.4,0,0,0],self.ik.low,self.ik.high)
            entry,pe,re=self.ik.solve(self.d,pre,target[:3,:3],seed)
            attempt=dict(candidate=candidate['id'],entry_position_error_m=pe,entry_rotation_error_rad=re)
            attempts.append(attempt)
            if pe>.003 or re>.035:attempt['failure']='entry_ik';continue
            hand0={n:float(self.initial[self.m.joint(n).qposadr[0]]) for n in hand}
            if not all(self.valid(home,{n:hand0[n]+u*(v-hand0[n]) for n,v in hand.items()}) for u in np.linspace(0,1,41)):
                attempt['failure']='hand_preparation';continue
            states=[];previous=pre;previous_travel=0.;seed=entry.copy();failure=None
            for phase,goal,travel in [('align',target[:3,3],0.),('push',finish,.07),
                    ('withdraw',finish+normal*.03,.07),('clear_to_entry',pre,.07)]:
                for u in np.linspace(0,1,61):
                    blend=3*u*u-2*u*u*u;position=previous+blend*(goal-previous)
                    self.state(seed,hand,previous_travel+blend*(travel-previous_travel))
                    seed,pe,re=self.ik.solve(self.d,position,target[:3,:3],seed)
                    if pe>.003 or re>.035:failure=phase+'_ik';break
                    if not self.valid(seed,hand,previous_travel+blend*(travel-previous_travel),margin=0.):failure=phase+'_collision';break
                    states.append(dict(phase=phase,fraction=float(u),arm_q=seed.tolist(),position_m=position.tolist()))
                if failure:break
                previous,previous_travel=goal,travel
            if failure:attempt['failure']=failure;continue
            path,metrics=plan_rrt(home,entry,self.ik.low,self.ik.high,lambda q:self.valid(q,hand),seed=7349)
            attempt['rrt']=metrics
            if path is None:attempt['failure']='free_space_entry';continue
            # The post-contact IK nullspace may differ from the entry seed.
            # Explicitly bridge it before retracing the free-space polyline.
            retreat=[seed.copy(),*path[::-1]]
            clear=all(self.valid(a+u*(b-a),hand,.07) for a,b in zip(retreat[:-1],retreat[1:])
                      for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.008))+1)))
            clear=clear and all(self.valid(home,{n:v+u*(hand0[n]-v) for n,v in hand.items()},.07) for u in np.linspace(0,1,41))
            if not clear:attempt['failure']='return_path';continue
            return dict(candidate=candidate,entry_path=[q.tolist() for q in path],return_path=[q.tolist() for q in retreat],
                        contact_states=states,device_rotation=self.rotation.tolist(),device_translation_m=self.translation.tolist(),
                        contact_palm_position_m=target[:3,3].tolist(),contact_palm_rotation=target[:3,:3].tolist(),
                        outward_normal=normal.tolist(),direction=direction.tolist(),initial_hand_q=hand0,
                        attempts=attempts,baseline=self.baseline,clearance_metrics=self.clearance.metrics(),
                        geometry_only=True,physical_execution=False)
        raise RuntimeError('No observed-geometry approach/return path: '+json.dumps(attempts))
