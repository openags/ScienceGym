"""Connect carried forceps to the two Cary pregrasp poses without hand jumps.

First partially close the held tool in free space. Move the right arm to its
clear elevated pregrasp, then move the open left hand to the reference approach
pose while keeping the tool steady. All planner edges check complete-room
source geometry; independent interpolation and physics remain required.
"""
import argparse
import hashlib
import json
import time
import numpy as np
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE,Space,JOINTS,canonical
from plan_optical_approaches import plan


class LeftEntrySpace(Space):
    def __init__(self,scene,base,start,goal,state,opened):
        super().__init__(scene,base,start,goal,state)
        self.names=[n for n in JOINTS if n.startswith('left_') and any(k in n for k in ['shoulder','elbow','wrist'])]
        self.bounds=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in self.names])
        self.bounds[self.names.index('left_shoulder_roll_joint'),0]=.025
        self.start=np.r_[[start[n] for n in self.names],0.]
        self.goal=np.r_[[goal[n] for n in self.names],1.]
        self.names+=['finger_fold'];self.bounds=np.vstack([self.bounds,[0,1]])
        self.scale=np.ones(len(self.names));self.open_hand=opened


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--transfer',default='previews/cary_tool_transfer_to_exchange_01/plan.json')
    parser.add_argument('--exchange',default='previews/cary_exchange_entry_01/plan.json')
    args=parser.parse_args();out=HERE/'previews'/('cary_exchange_free_'+args.trial);out.mkdir(exist_ok=False)
    transfer=json.loads((HERE/args.transfer).read_text());exchange=json.loads((HERE/args.exchange).read_text())
    assert transfer['passed'] and exchange['passed']
    names=['plan_cary_exchange_free.py','cary_tool_pickup_scene.py','cary_tool_scene.py','cary_clamp_scene.py',
        'cary_clamp.py','cary_access_scene.py','optical_choreography.py','optical_delivery.py','plan_optical_approaches.py',
        'source_geometry.py','long_forceps.py','tweezers_geometry.py','cary_access_episode.json',args.transfer,args.exchange,exchange['staging']]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(exchange['staging']);first=transfer['rows'][-1];target=exchange['candidates'][0]['rows'][0]
    base=np.array(first['root']);assert np.max(abs(base-np.array(target['root'])))<1e-8
    q=canonical(first['q']);rows=[];failure={};paths=[];started=time.monotonic();amount=target['closure']
    for c in np.linspace(0.,amount,41):
        q={**q,**scene.hand_q(float(c))};failure=scene.check(base,q,tool_held=True,closure=float(c))
        if failure:break
        rows.append(dict(stage='preclose_tool',q=dict(q),root=base.tolist(),tool_held=True,closure=float(c)))
    if not failure:
        mid=dict(q)
        for n,v in target['q'].items():
            if n in ['waist_pitch_joint','waist_yaw_joint'] or (n.startswith('right_') and any(k in n for k in ['shoulder','elbow','wrist'])):mid[n]=v
        state=dict(tool_held=True,closure=amount)
        spaces=[('right_to_pregrasp',Space(scene,base,q,mid,state)),
                ('left_to_pregrasp',LeftEntrySpace(scene,base,mid,target['q'],state,
                    {n:v for n,v in target['q'].items() if n.startswith('left_') and any(k in n for k in ['thumb','index','middle','ring','little'])}))]
        for stage,space in spaces:
            try:
                print('planning',stage,flush=True);path=plan(space)
                part=[dict(stage=stage,q=space.q_at(v),root=base.tolist(),tool_held=True,closure=amount) for v in path]
                rows+=part;paths.append(dict(stage=stage,rows=part,collision_queries=space.calls))
            except RuntimeError as error:failure=dict(stage=stage,error=str(error));break
    error=max(abs(rows[-1]['q'][n]-target['q'][n]) for n in target['q']) if rows else None
    report=dict(scope=__doc__,passed=not failure and error is not None and error<1e-6,rows=rows,paths=paths,
        failure=failure,endpoint_joint_error_rad=error,source_sha256=pins,transfer=args.transfer,exchange=args.exchange,
        seconds=time.monotonic()-started,
        limitations=['Planner excludes ankle housings; final speed-retimed interpolation must be independently checked.',
                     'No force, balance, dynamics, sensor-control or full measurement qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],knots=len(rows),failure=failure,seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
