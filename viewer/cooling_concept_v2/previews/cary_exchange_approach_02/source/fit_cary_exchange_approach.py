"""Screen both hand approaches before the planned Cary reference extraction.

The left hand approaches and supports the reference backing. The right hand
then lowers a partially closed ordinary forceps around the clamp arm and
closes its jaws. Source meshes include both terminal wrist housings. Full-arm
connections, interpolation, forces and complete measurement remain separate.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene
from cary_distal_hand import distal_hand_manager
from long_forceps import meshes
from optical_choreography import HERE
from source_geometry import set_hand


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--exchange',default='previews/cary_bimanual_exchange_04/plan.json')
    parser.add_argument('--profile',default='previews/long_forceps_closure_03/profile.json')
    parser.add_argument('--right-lift-m',type=float,default=.10)
    args=parser.parse_args();out=HERE/'previews'/('cary_exchange_approach_'+args.trial);out.mkdir(exist_ok=False)
    names=['fit_cary_exchange_approach.py','cary_clamp_scene.py','cary_clamp.py','cary_access_scene.py',
        'cary_distal_hand.py','source_geometry.py','long_forceps.py','cary_access_episode.json',args.exchange,args.profile]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    exchange=json.loads((HERE/args.exchange).read_text())['candidates'][0];initial=exchange['rows'][0]
    profile=json.loads((HERE/args.profile).read_text());assert profile['passed']
    assert np.max(abs(np.array(profile['palm_matrix'])-np.array(exchange['tool_T_palm'])))<1e-12
    access=json.loads((HERE/'cary_access_episode.json').read_text())['segments'][-1]['rows'][-1]
    scene=CaryClampScene(local_only=True);scene.set_access(lid=access['lid_m'],cover=access['cover_matrix'])
    scene.set_clamp(initial['gap_m'],initial['angle_rad'])
    left=distal_hand_manager('left');right=distal_hand_manager('right')
    left_target=np.array(initial['left_palm']);right_target=np.array(initial['right_palm'])
    palm_T_tool=np.linalg.inv(exchange['tool_T_palm']);tool_cache={}
    left_closed={n:v for n,v in initial['q'].items() if n.startswith('left_') and any(t in n for t in ['thumb','index','middle','ring','little'])}
    def right_q(amount):
        rows=profile['rows'];return {n:float(np.interp(amount,[r['closure'] for r in rows],[r['q'][n] for r in rows])) for n in rows[0]['q']}
    def check(left_pose,right_pose,lq,amount):
        rq=right_q(amount);set_hand(left,'left',lq,left_pose);set_hand(right,'right',rq,right_pose)
        if amount not in tool_cache:
            manager=trimesh.collision.CollisionManager()
            for n,m in meshes(amount).items():manager.add_object(n,m)
            tool_cache[amount]=manager
        tool=tool_cache[amount];tool_pose=right_pose@palm_T_tool
        for n in tool._objs:tool.set_transform(n,tool_pose)
        failure={}
        for name,a,b in [('left_environment',left,scene.obstacles),('right_environment',right,scene.obstacles),
                         ('tool_environment',tool,scene.obstacles),('hands',left,right),
                         ('left_tool',left,tool),('right_tool',right,tool)]:
            _,pairs=a.in_collision_other(b,return_names=True)
            if pairs:failure[name]=sorted(pairs)
        return failure,rq
    failures=[];accepted=[];started=time.monotonic()
    for di,dt,amount in itertools.product([.1,.2],[.05,.1],[.6,.8,.9]):
        opened={**left_closed,'left_index_1_joint':left_closed['left_index_1_joint']-di,
                'left_thumb_2_joint':left_closed['left_thumb_2_joint']-dt}
        left_pre=left_target.copy();left_pre[:3,3]+=[0,-.06,0]
        right_pre=right_target.copy();right_pre[:3,3]+=[0,0,args.right_lift_m]
        rows=[];failed=False
        phases=[('left_approach',41),('left_close',41),('right_lower',51),('right_close',31)]
        for stage,count in phases:
            for u in np.linspace(0.,1.,count):
                lp=left_target.copy();rp=right_pre.copy();lq=dict(left_closed);closure=amount
                if stage=='left_approach':lp[:3,3]+=[0,-.06*(1-u),0];lq=opened
                elif stage=='left_close':lq={n:opened[n]*(1-u)+left_closed[n]*u for n in opened}
                elif stage=='right_lower':rp[:3,3]=right_target[:3,3]+[0,0,args.right_lift_m*(1-u)]
                elif stage=='right_close':rp=right_target;closure=amount+(1-amount)*u
                failure,rq=check(lp,rp,lq,float(closure))
                if failure:
                    failures.append(dict(index_delta=di,thumb_delta=dt,preclosure=amount,stage=stage,fraction=float(u),failure=failure,completed_states=len(rows)))
                    failed=True;break
                rows.append(dict(stage=stage,fraction=float(u),left_palm=lp.tolist(),right_palm=rp.tolist(),
                    left_q=dict(lq),right_q=rq,closure=float(closure),reference_held=stage in ['right_lower','right_close']))
            if failed:break
        if not failed:
            accepted.append(dict(index_delta=di,thumb_delta=dt,preclosure=amount,rows=rows,
                tool_T_palm=exchange['tool_T_palm'],reference_grasp=exchange['reference_grasp']))
            print('accepted both approaches',len(rows),'states',flush=True);break
        print('rejected',di,dt,amount,failures[-1]['stage'],failures[-1]['failure'],flush=True)
    report=dict(scope=__doc__,candidates=accepted,failures=failures,source_sha256=pins,exchange=args.exchange,
        seconds=time.monotonic()-started,right_lift_m=args.right_lift_m,
        limitations=['Local pair and instrument geometry only; whole-body and room checks remain required.',
                     'No source-hand self-collision interpolation audit, forces, friction, sensor-control or measurement qualification.'])
    (out/'approaches.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(accepted),failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
