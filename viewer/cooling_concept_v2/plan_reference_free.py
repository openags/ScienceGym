"""Plan open-hand entry/exit around the gold reference and protective cap.

The root is stationary and the reference stays on its support. Finger folding
is part of the searched state. These paths still require independent full-scene
and phase-transition review when integrated with the film.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from source_geometry import KIN, fk
from plan_optical_approaches import plan
from plan_reference_carry import Space as CarrySpace
from plan_reference_storage import HERE, translation


class Space(CarrySpace):
    def __init__(self,solved,kind):
        super().__init__(solved)
        target=next(r for r in solved['rows'] if r['stage']=='lower_open_hand') if kind=='port_entry' else next(r for r in reversed(solved['rows']) if r['stage']=='withdraw_open_hand')
        self.base=np.array(target['root']);self.names+=['reference_finger_fold']
        poses=json.loads((HERE/'motion_poses.json').read_text());self.q={**poses['poses']['rest'],**poses['poses']['stance']}
        for name in self.names[:-2]:self.q[name]=poses['poses']['rest'].get(name,0.)
        self.q['waist_pitch_joint']=0.
        profile=json.loads((HERE/'reference_lift_path.json').read_text())['grasp']['q']
        self.open_hand={n:(.4 if n=='left_index_1_joint' else .10 if n=='left_thumb_2_joint' else v) for n,v in profile.items()}
        self.start=np.array([self.q.get(n,0.) for n in self.names]);self.goal=np.array([target['q'].get(n,0.) for n in self.names]);self.goal[-1]=1.
        self.bounds=np.vstack([self.bounds,[0.,1.]]);self.scale=np.r_[self.scale,1.]
        setup=json.loads((HERE/'optical_setup.json').read_text());grasp=json.loads((HERE/'reference_lift_path.json').read_text())['grasp']
        initial=translation(setup['ports']['ftir_sample']['position_m'])@np.array(grasp['palm_matrix'])
        delta=translation([0,0,0] if kind=='port_entry' else solved['final_offset'])
        for name,local in self.reference_in_palm.items():self.reference.set_transform(name,delta@initial@local)

    def state(self,values):
        q={**self.q,**dict(zip(self.names[:-1],values[:-1]))}
        q.update({n:v*values[-1] for n,v in self.open_hand.items()})
        world=fk(q)
        for name in self.meshes:self.robot.set_transform(name,self.base@world[name])
        return q,self.base@world['left_palm_force_sensor']

    def free(self,values):
        key=tuple(np.round(values,6))
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if np.any(values<self.bounds[:,0]-1e-6) or np.any(values>self.bounds[:,1]+1e-6):self.last_rejection='joint bounds';return False
        self.state(values)
        _,pairs=self.robot.in_collision_internal(return_names=True)
        own=[p for p in pairs if tuple(sorted(p)) not in self.adjacent];ok=not own;self.last_rejection=dict(self=own)
        if ok:
            hit,pairs=self.robot.in_collision_other(self.obstacles,return_names=True);ok=not hit;self.last_rejection=dict(environment=sorted(pairs))
        if ok:
            hit,pairs=self.robot.in_collision_other(self.reference,return_names=True);ok=not hit;self.last_rejection=dict(reference_hand=sorted(pairs))
        self.cache[key]=ok;return ok


def main():
    parser=argparse.ArgumentParser();parser.add_argument('solved');parser.add_argument('--kind',choices=['port_entry','cap_exit']);args=parser.parse_args()
    source=Path(args.solved);solved=json.loads(source.read_text())
    files=['plan_reference_free.py','plan_reference_carry.py','plan_reference_storage.py','plan_optical_approaches.py','source_geometry.py','optical_setup.json','motion_poses.json','reference_lift_path.json']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files}
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'};effective={n:j['limits']['velocity'] for n,j in joints.items()}
    for name,j in joints.items():
        root=name;multiplier=1.
        while joints[root].get('mimic'):
            m=joints[root]['mimic'];multiplier*=float(m.get('multiplier',1));root=m['joint']
        if multiplier:effective[root]=min(effective[root],j['limits']['velocity']/abs(multiplier))
    for kind in ([args.kind] if args.kind else ['port_entry','cap_exit']):
        began=time.monotonic();space=Space(solved,kind);print(kind,'start',space.free(space.start),space.last_rejection,'goal',space.free(space.goal),space.last_rejection,flush=True)
        path=plan(space);fold_cap=min(.45,*(effective[n]/abs(v) for n,v in space.open_hand.items() if v))
        limits=np.array([min(effective[n],.6 if n=='waist_pitch_joint' else 1.2) for n in space.names[:-1]]+[fold_cap])
        segments=np.maximum(.25,1.6*np.max(np.abs(np.diff(path,axis=0))/limits,axis=1));rows=[]
        for t,values in zip(np.r_[0,np.cumsum(segments)],path):
            q,palm=space.state(values);rows.append(dict(time_s=float(t),q=q))
        assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
        result=dict(scope=__doc__,kind=kind,source_sha256=pins,endpoint_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),root=space.base.tolist(),rows=rows,
                    joints=space.names,knots=[v.tolist() for v in path],open_hand=space.open_hand,passed_planner_edges=True,collision_queries=space.calls,
                    wall_seconds=time.monotonic()-began,duration_s=float(sum(segments)),selected_speed_caps_rad_s=limits.tolist(),whole_scene_validation_pending=True)
        out=HERE/'previews'/('reference_'+kind+'_path.json')
        if out.exists():out.rename(out.with_name(out.stem+'_'+hashlib.sha256(out.read_bytes()).hexdigest()[:12]+'.json'))
        out.write_text(json.dumps(result,indent=2)+'\n')
        print(kind,json.dumps({k:v for k,v in result.items() if k in ['passed_planner_edges','collision_queries','wall_seconds','duration_s']}),flush=True)


if __name__=='__main__':main()
