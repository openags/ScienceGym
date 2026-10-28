"""Solve whole-arm hand approaches followed by the Cary reference extraction.

Both hands begin at explicit pregrasp poses. The left hand supports the
reference before the right tool retracts its clamp. This extends the earlier
closed-grasp candidate; free-arm entry, walking and reference storage remain
to compose and independently review.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
from cary_bimanual_ik import solve
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE,make_base,canonical
from source_geometry import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--approaches',default='previews/cary_exchange_approach_01/approaches.json')
    parser.add_argument('--staging',default='previews/long_forceps_staging_08/staging.json')
    parser.add_argument('--x',nargs='+',type=float,default=[2.55,2.65,2.45])
    parser.add_argument('--y',nargs='+',type=float,default=[7.85,7.80])
    parser.add_argument('--yaw',type=float,default=1.4)
    args=parser.parse_args();out=HERE/'previews'/('cary_exchange_entry_'+args.trial);out.mkdir(exist_ok=False)
    approaches=json.loads((HERE/args.approaches).read_text());old=json.loads((HERE/approaches['exchange']).read_text())['candidates'][0]
    names=['plan_cary_exchange_entry.py','cary_tool_pickup_scene.py','cary_bimanual_ik.py','cary_tool_scene.py',
        'cary_clamp_scene.py','cary_clamp.py','cary_access_scene.py','optical_choreography.py',
        'optical_delivery.py','source_geometry.py','long_forceps.py','tweezers_geometry.py',
        'cary_access_episode.json','motion_poses.json',args.approaches,approaches['exchange'],args.staging]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(args.staging);rest=scene.access_episode['segments'][-1]['rows'][-1]['q']
    scene.reference_grasp=np.array(old['reference_grasp'])
    failures=[];candidates=[];started=time.monotonic()
    print('complete laboratory loaded',len(scene.obstacles._objs),flush=True)
    for x,y in itertools.product(args.x,args.y):
        for ci,c in enumerate(approaches['candidates']):
            base=make_base(x,y,args.yaw,rest);scene.set_reference(np.eye(4))
            q=canonical(old['rows'][0]['q']);rows=[];failure={}
            path=[dict(r,gap_m=.014,angle_rad=0.) for r in c['rows']]
            path += [dict(r,closure=1.,reference_held=True,
                left_q={n:v for n,v in r['q'].items() if n.startswith('left_') and any(t in n for t in ['thumb','index','middle','ring','little'])},
                right_q=scene.hand_q(1.)) for r in old['rows']]
            for row in path:
                q.update(row['left_q']);q.update(row['right_q'])
                targets={side:np.array(row[side+'_palm']) for side in ['left','right']}
                q,errors=solve(base,targets,q)
                if any(v['position_m']>1e-7 or v['angle_rad']>1e-6 for v in errors.values()):failure['ik']=errors
                scene.set_clamp(row['gap_m'],row['angle_rad'])
                failure.update(scene.check(base,q,tool_held=True,closure=row['closure'],reference_held=row['reference_held']))
                for name,check in [('reference_environment',scene.reference_clearance),('clamp_environment',scene.clamp_clearance)]:
                    collisions=check()
                    if collisions:failure[name]=collisions
                if failure:break
                rows.append(dict(stage=row['stage'],q=q,root=base.tolist(),tool_held=True,closure=row['closure'],
                    reference_held=row['reference_held'],reference_delta=scene.reference_delta.tolist(),
                    left_palm=row['left_palm'],right_palm=row['right_palm'],gap_m=row['gap_m'],angle_rad=row['angle_rad'],errors=errors))
            if failure:
                failures.append(dict(base=[x,y,args.yaw],choice=ci,stage=row['stage'],failure=failure,completed_rows=rows,q=q))
                print('rejected',x,y,row['stage'],'after',len(rows),failure,flush=True)
            else:
                candidates.append(dict(base=[x,y,args.yaw],choice=ci,rows=rows,tool_T_palm=old['tool_T_palm'],reference_grasp=old['reference_grasp']))
                print('accepted',len(rows),'states',flush=True);break
        if candidates:break
    report=dict(scope=__doc__,passed=bool(candidates),candidates=candidates,failures=failures,source_sha256=pins,
        approaches=args.approaches,staging=args.staging,seconds=time.monotonic()-started,
        model_manifest_sha256=hashlib.sha256((ROOT/'assets/cooling_lab_v1/scene.json').read_bytes()).hexdigest(),
        limitations=['Starts with held tool at pregrasp; free-arm entry, walking and protected reference storage remain required.',
                     'Planning omits ankle meshes; independent interpolated review remains required.',
                     'No force, balance, dynamics or sensor-control qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
