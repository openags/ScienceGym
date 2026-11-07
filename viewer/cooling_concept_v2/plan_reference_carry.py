"""Plan a held-reference arm path around the instrument into cap preplacement.

The reference follows source palm FK rigidly during this geometric search.
Free-arm approach, closing, the sidestep gait and force qualification are
separate obligations. The cap remains a versioned, inferred candidate.
"""
import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh

from source_geometry import KIN, fk, robot_meshes
from plan_optical_approaches import plan
from plan_reference_storage import HERE, geometry, translation


class Space:
    def __init__(self, solved):
        self.calls=0;self.cache={}
        start=next(r for r in reversed(solved['rows']) if r['stage']=='proposed_carrying_step')
        final=np.array(solved['final_offset'])
        goal=min((r for r in solved['rows'] if r['stage']=='seat_reference_in_cap'),key=lambda r:abs(r['offset'][2]-final[2]-.03))
        assert goal['error']<.0003 and goal['rotationError']<.003
        self.base=np.array(start['root']);self.q=dict(start['q']);self.goal_q=goal['q']
        self.names=[j['name'] for j in KIN['joints'] if j['name'].startswith('left_') and any(s in j['name'] for s in ['shoulder','elbow','wrist']) and j['type']=='revolute']+['waist_pitch_joint']
        limits={j['name']:j['limits'] for j in KIN['joints'] if j['type']=='revolute'}
        self.bounds=np.array([[limits[n]['lower']+.0005,limits[n]['upper']-.0005] for n in self.names])
        self.bounds[self.names.index('left_shoulder_roll_joint'),0]=.025;self.bounds[-1]=[0,.4]
        self.start=np.array([self.q.get(n,0) for n in self.names]);self.goal=np.array([goal['q'].get(n,0) for n in self.names]);self.scale=np.array([1.]*7+[3.])
        setup=json.loads((HERE/'optical_setup.json').read_text());lift=json.loads((HERE/'reference_lift_path.json').read_text())
        self.obstacles,self.reference,rest=geometry(setup,solved['cap_floor_m'])
        initial_palm=translation(setup['ports']['ftir_sample']['position_m'])@np.array(lift['grasp']['palm_matrix'])
        self.reference_in_palm={n:np.linalg.inv(initial_palm)@m for n,m in rest.items()}
        self.reference_origin_in_palm=np.linalg.inv(initial_palm)@translation(setup['ports']['ftir_sample']['position_m'])
        self.robot=trimesh.collision.CollisionManager();self.meshes={n:m for n,m in robot_meshes().items() if 'ankle' not in n}
        for name,mesh in self.meshes.items():self.robot.add_object(name,mesh)
        graph=defaultdict(list)
        for j in KIN['joints']:
            w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
        self.adjacent=set()
        for link in self.meshes:
            stack=[(link,None,0)]
            while stack:
                name,parent,d=stack.pop()
                if d>1:continue
                if name in self.meshes:self.adjacent.add(tuple(sorted((link,name))))
                stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)

    def state(self,values):
        q={**self.q,**dict(zip(self.names,values))};world=fk(q);palm=self.base@world['left_palm_force_sensor']
        for name in self.meshes:self.robot.set_transform(name,self.base@world[name])
        for name,local in self.reference_in_palm.items():self.reference.set_transform(name,palm@local)
        return q,palm

    def free(self,values):
        key=tuple(np.round(values,6))
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if np.any(values<self.bounds[:,0]-1e-6) or np.any(values>self.bounds[:,1]+1e-6):self.last_rejection='joint bounds';return False
        q,palm=self.state(values)
        # Keep the optical reference generally face down while it is held.
        orientation=(palm@self.reference_origin_in_palm)[:3,:3]
        if orientation[2,2]<np.cos(np.deg2rad(60)):self.last_rejection='reference tilt exceeds 60 degrees';self.cache[key]=False;return False
        _,pairs=self.robot.in_collision_internal(return_names=True)
        own=[p for p in pairs if tuple(sorted(p)) not in self.adjacent];ok=not own;self.last_rejection=dict(self=own)
        if ok:
            hit,pairs=self.robot.in_collision_other(self.obstacles,return_names=True);ok=not hit;self.last_rejection=dict(environment=sorted(pairs))
        if ok:
            hit,pairs=self.reference.in_collision_other(self.obstacles,return_names=True);ok=not hit;self.last_rejection=dict(reference_environment=sorted(pairs))
        if ok:
            hit,pairs=self.robot.in_collision_other(self.reference,return_names=True);ok=not hit;self.last_rejection=dict(reference_hand=sorted(pairs))
        self.cache[key]=ok;return ok

    def edge(self,a,b):
        steps=max(1,int(np.ceil(self.distance(a,b)/.035)))
        return all(self.free(a+(b-a)*u/steps) for u in range(1,steps+1))

    def distance(self,a,b):return np.linalg.norm((a-b)*self.scale)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('solved');args=parser.parse_args()
    source=Path(args.solved);solved=json.loads(source.read_text());out=HERE/'previews/reference_carry_path.json'
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['plan_reference_carry.py','plan_reference_storage.py','plan_optical_approaches.py','source_geometry.py','optical_setup.json','reference_lift_path.json']}
    began=time.monotonic();space=Space(solved);print('start',space.free(space.start),space.last_rejection,'goal',space.free(space.goal),space.last_rejection,flush=True)
    path=plan(space)
    effective={j['name']:j['limits']['velocity'] for j in KIN['joints'] if j['type']=='revolute'}
    limits=np.array([min(effective[n],.6 if n=='waist_pitch_joint' else 1.2) for n in space.names]);segments=np.maximum(.25,1.6*np.max(np.abs(np.diff(path,axis=0))/limits,axis=1))
    rows=[]
    for t,values in zip(np.r_[0,np.cumsum(segments)],path):
        q,palm=space.state(values);rows.append(dict(time_s=float(t),q=q,reference_origin_world=(palm@space.reference_origin_in_palm).tolist()))
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    result=dict(scope=__doc__,source_sha256=pins,endpoint_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),root=space.base.tolist(),joints=space.names,knots=[v.tolist() for v in path],rows=rows,
                passed_planner_edges=True,collision_queries=space.calls,wall_seconds=time.monotonic()-began,duration_s=float(sum(segments)),selected_speed_caps_rad_s=limits.tolist(),whole_scene_validation_pending=True)
    if out.exists():out.rename(out.with_name('reference_carry_path_'+hashlib.sha256(out.read_bytes()).hexdigest()[:12]+'.json'))
    out.write_text(json.dumps(result,indent=2)+'\n');(HERE/'previews/reference_storage_endpoints.json').write_bytes(source.read_bytes())
    print(json.dumps({k:v for k,v in result.items() if k in ['passed_planner_edges','collision_queries','wall_seconds','duration_s']}),flush=True)


if __name__=='__main__':main()
