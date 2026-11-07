"""Source-geometry planning primitives for a complete optical exchange episode.

Authored kinematics only. Local search includes the FTIR bench, nearby source
equipment, the ordinary tray, the deforming tweezers and both witnesses.
Ankle meshes are omitted from this planning tier; full-scene, sole, source
speed, swept clearance and dynamics reviews remain separate obligations.
"""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,ASSETS,KIN,fk,robot_meshes
from plan_reference_storage import geometry,translation
from plan_specimen_port import palm_fk
from tweezers_geometry import meshes as tool_meshes
from fit_specimen_tool import profile

HERE=Path(__file__).resolve().parent
JOINTS={j['name']:j for j in KIN['joints'] if j['type']=='revolute'}
ARM=[n for n in JOINTS if n.startswith('right_') and any(k in n for k in ['shoulder','elbow','wrist'])]
INDEPENDENT=[n for n,j in JOINTS.items() if not j.get('mimic')]


def canonical(q):return {n:float(q.get(n,0)) for n in INDEPENDENT}


def load_json(path):return json.loads((HERE/path).read_text())


def make_base(x,y,yaw,q):
    world=fk(q);poses=load_json('motion_poses.json')
    bottom=min(float((np.array(vertices)@world[n][2,:3]+world[n][2,3]).min()) for n,vertices in poses['sole_vertices_m'].items())
    base=np.eye(4);base[:3,:3]=Rotation.from_euler('z',yaw).as_matrix();base[:3,3]=[x,y,-bottom];return base


def solve_palm(base,target,seed,waist=False):
    names=ARM+(['waist_pitch_joint','waist_yaw_joint'] if waist else []);q=canonical(seed)
    limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names])
    limits[names.index('right_shoulder_roll_joint'),1]=-.025
    if waist:limits[-2]=[0,.4];limits[-1]=[-.6,.6]
    initial=np.clip([q[n] for n in names],limits[:,0]+1e-8,limits[:,1]-1e-8)
    def residual(values):
        actual=base@palm_fk({**q,**dict(zip(names,values))})
        return np.r_[(actual[:3,3]-target[:3,3])*10,Rotation.from_matrix(target[:3,:3].T@actual[:3,:3]).as_rotvec()]
    result=least_squares(lambda v:np.r_[residual(v),(v-initial)*1e-7],initial,bounds=(limits[:,0],limits[:,1]),max_nfev=180,ftol=1e-12,xtol=1e-12,gtol=1e-12)
    q.update(dict(zip(names,map(float,result.x))));error=residual(result.x)
    return q,float(np.linalg.norm(error[:3])/10),float(np.linalg.norm(error[3:]))


def solve_position(base,target,seed):
    """Lift a held empty tool without unnecessarily fixing its wrist orientation."""
    names=ARM+['waist_pitch_joint','waist_yaw_joint'];q=canonical(seed)
    limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names]);limits[names.index('right_shoulder_roll_joint'),1]=-.025;limits[-2]=[0,.4];limits[-1]=[-.6,.6]
    initial=np.clip([q[n] for n in names],limits[:,0]+1e-8,limits[:,1]-1e-8)
    def residual(values):
        actual=base@palm_fk({**q,**dict(zip(names,values))})
        return np.r_[(actual[:3,3]-target)*10,(values-initial)*.001]
    result=least_squares(residual,initial,bounds=(limits[:,0],limits[:,1]),max_nfev=100,ftol=1e-12,xtol=1e-12,gtol=1e-12)
    q.update(dict(zip(names,map(float,result.x))));return q,float(np.linalg.norm(residual(result.x)[:3])/10)


class Scene:
    def __init__(self):
        self.setup=load_json('optical_setup.json');self.fit=load_json('previews/specimen_tool_fit.json');self.closure=load_json('previews/tweezers_closure.json');self.staging=load_json('previews/tweezers_staging.json')
        original_tool=np.array(self.staging['tool_world_matrix']);turn=np.eye(4);turn[:3,:3]=Rotation.from_euler('z',np.pi).as_matrix()
        self.staging_transform=translation([10.30,8.25,original_tool[2,3]])@turn@translation(-original_tool[:3,3])
        self.tool_rest=self.staging_transform@original_tool
        self.tray_matrix=self.staging_transform@translation(self.staging['tray_position_m']);self.tray_position=self.tray_matrix[:3,3]
        self.tool_T_palm=np.array(self.fit['tool_T_palm']);self.holder_T_tool=np.array(self.fit['holder_T_tool'])
        self.palm_T_tool=np.linalg.inv(self.tool_T_palm);self.tool_T_holder=np.linalg.inv(self.holder_T_tool)
        self.specimen_rest={'white':translation([10.40,8.20,.850001]),'black':translation([10.47,8.20,.850001])}
        self.specimen_port=translation(np.array(self.setup['ports']['ftir_sample']['position_m'])+[0,0,.000001])
        self.obstacles,reference,rest=geometry(self.setup)
        offset=load_json('reference_transfer.json')['segments'][-1]['rows'][-1]['reference_offset'];gold=trimesh.load(ROOT/ASSETS['pike']['geometry'],force='scene',process=False)
        for name,world in rest.items():
            _,key=gold.graph[name.split('::')[1]];self.obstacles.add_object(name,gold.geometry[key],translation(offset)@world)
        tray=trimesh.load(ROOT/ASSETS['tray_white']['geometry'],force='scene',process=False)
        for name in tray.graph.nodes_geometry:
            local,key=tray.graph[name];self.obstacles.add_object('optical_tray::'+name,tray.geometry[key],self.tray_matrix@local)
        self.robot=trimesh.collision.CollisionManager();self.meshes={n:m for n,m in robot_meshes().items() if 'ankle' not in n}
        for name,mesh in self.meshes.items():self.robot.add_object(name,mesh)
        self.specimens={};self.specimen_parts={}
        for kind in ['white','black']:
            scene=trimesh.load(ROOT/f'assets/cooling_optical_specimens_v1/witness_{kind}.glb',force='scene',process=False);manager=trimesh.collision.CollisionManager();local={}
            for name in scene.graph.nodes_geometry:
                transform,key=scene.graph[name];manager.add_object(name,scene.geometry[key],transform);local[name]=transform
            self.specimens[kind]=manager;self.specimen_parts[kind]=local
        graph=defaultdict(list)
        for j in KIN['joints']:
            weight=int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
        self.adjacent=set()
        for link in self.meshes:
            stack=[(link,None,0)]
            while stack:
                name,parent,d=stack.pop()
                if d>1:continue
                if name in self.meshes:self.adjacent.add(tuple(sorted((link,name))))
                stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)
        self.tool=None;self.last_closure=None

    def state(self,base,q,tool_held=False,closure=0.,held_specimen=None,stored=None):
        if self.last_closure!=closure:
            self.tool=trimesh.collision.CollisionManager()
            for name,mesh in tool_meshes(closure).items():self.tool.add_object(name,mesh)
            self.last_closure=closure
        world=fk(q);tool=base@world['right_palm_force_sensor']@self.palm_T_tool if tool_held else self.tool_rest
        for name in self.meshes:self.robot.set_transform(name,base@world[name])
        for name in self.tool._objs:self.tool.set_transform(name,tool)
        poses={kind:np.array((stored or {}).get(kind,self.specimen_rest[kind])) for kind in self.specimens}
        if held_specimen:poses[held_specimen]=tool@self.tool_T_holder
        for kind,manager in self.specimens.items():
            for name,local in self.specimen_parts[kind].items():manager.set_transform(name,poses[kind]@local)
        return dict(tool=tool,holders=poses)

    def check(self,base,q,**state):
        self.state(base,q,**state);_,pairs=self.robot.in_collision_internal(return_names=True)
        bad=sorted(p for p in pairs if tuple(sorted(p)) not in self.adjacent)
        if bad:return dict(self_intersections=bad)
        for label,a,b in [('robot_environment',self.robot,self.obstacles),('robot_tool',self.robot,self.tool),('tool_environment',self.tool,self.obstacles)]:
            hit,pairs=a.in_collision_other(b,return_names=True)
            if hit:return {label:sorted(pairs)}
        for kind,manager in self.specimens.items():
            for label,a,b in [('robot_specimen',self.robot,manager),('tool_specimen',self.tool,manager),('specimen_environment',manager,self.obstacles)]:
                hit,pairs=a.in_collision_other(b,return_names=True)
                if hit:return {label+'_'+kind:sorted(pairs)}
        hit,pairs=self.specimens['white'].in_collision_other(self.specimens['black'],return_names=True)
        return dict(specimen_intersections=sorted(pairs)) if hit else {}

    def hand_q(self,closure):return profile(closure,self.closure)


class Space:
    def __init__(self,scene,base,start,goal,state,open_hand=None):
        self.scene=scene;self.base=base;self.q=canonical(start);self.state_options=state;self.open_hand=open_hand;self.names=ARM+['waist_pitch_joint','waist_yaw_joint'];self.calls=0;self.cache={}
        self.bounds=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in self.names]);self.bounds[self.names.index('right_shoulder_roll_joint'),1]=-.025;self.bounds[-2]=[0,.4];self.bounds[-1]=[-.6,.6]
        self.start=np.array([start.get(n,0) for n in self.names]);self.goal=np.array([goal.get(n,0) for n in self.names]);self.scale=np.array([1.]*7+[3.,2.])
        if open_hand:
            self.names+=['finger_fold'];self.bounds=np.vstack([self.bounds,[0,1]]);self.start=np.r_[self.start,0.];self.goal=np.r_[self.goal,1.];self.scale=np.r_[self.scale,1.]

    def q_at(self,values):
        q={**self.q,**dict(zip(self.names,values))}
        if self.open_hand:q.update({n:v*values[-1] for n,v in self.open_hand.items()});q.pop('finger_fold',None)
        return canonical(q)

    def free(self,values):
        key=tuple(np.round(values,7))
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if np.any(values<self.bounds[:,0]-1e-7) or np.any(values>self.bounds[:,1]+1e-7):self.last_rejection='joint bounds';return False
        self.last_rejection=self.scene.check(self.base,self.q_at(values),**self.state_options);ok=not self.last_rejection;self.cache[key]=ok;return ok

    def distance(self,a,b):return float(np.linalg.norm((a-b)*self.scale))

    def edge(self,a,b):
        count=max(1,int(np.ceil(self.distance(a,b)/.025)))
        return all(self.free(a+(b-a)*i/count) for i in range(1,count+1))
