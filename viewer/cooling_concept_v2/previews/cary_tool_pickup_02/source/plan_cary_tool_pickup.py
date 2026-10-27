"""Plan empty-hand entry, opposed grip and lift of the Cary long forceps.

Use the complete existing laboratory and actual source-joint kinematics. This
fixed-stance segment starts with the robot at the pickup station; the walking
connection, independent interpolated review and physical forces remain open.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE,Space,canonical,make_base,solve_palm
from plan_optical_approaches import plan
from source_geometry import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--approaches',default='previews/long_forceps_approach_01/approaches.json')
    parser.add_argument('--choices',nargs='+',type=int,default=[0,1,2])
    parser.add_argument('--x',nargs='+',type=float,default=[1.45,1.55,1.65])
    parser.add_argument('--y',nargs='+',type=float,default=[7.85,7.90,7.80])
    parser.add_argument('--yaw',type=float,default=1.4)
    args=parser.parse_args();out=HERE/'previews'/('cary_tool_pickup_'+args.trial);out.mkdir(exist_ok=False)
    choices=json.loads((HERE/args.approaches).read_text());staging=json.loads((HERE/choices['staging']).read_text())
    names=['plan_cary_tool_pickup.py','cary_tool_pickup_scene.py','cary_tool_scene.py','cary_clamp_scene.py',
        'cary_clamp.py','cary_access_scene.py','optical_choreography.py','optical_delivery.py',
        'plan_optical_approaches.py','source_geometry.py','long_forceps.py','tweezers_geometry.py',
        'cary_access_episode.json','motion_poses.json',args.approaches,choices['staging'],staging['profile']]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(choices['staging']);started=time.monotonic()
    print('complete laboratory loaded',len(scene.obstacles._objs),'obstacles',flush=True)
    rest=canonical(scene.access_episode['segments'][-1]['rows'][-1]['q'])
    target=scene.tool_rest@scene.tool_T_palm;failures=[];candidates=[];tested=0
    for x,y,ci in itertools.product(args.x,args.y,args.choices):
        c=choices['candidates'][ci];base=make_base(x,y,args.yaw,rest)
        pre=np.array(c['approach'][0]['palm']);opened=c['open_hand'];closed=c['closed_hand']
        collision=scene.check(base,rest,tool_held=False,closure=0.)
        if collision:
            failures.append(dict(base=[x,y,args.yaw],choice=ci,stage='rest',failure=collision));continue
        for posture in ['forward','rest']:
            tested+=1;seed={**rest,**opened}
            if posture=='forward':seed.update(right_shoulder_pitch_joint=-.8,right_shoulder_roll_joint=-.45,
                right_shoulder_yaw_joint=-.4,right_elbow_joint=1.2,waist_pitch_joint=.15)
            q,error,angle=solve_palm(base,pre,seed,waist=True)
            failure=scene.check(base,q,tool_held=False,closure=0.)
            if error>1e-7 or angle>1e-6:failure['ik']=dict(position_m=error,angle_rad=angle)
            if failure:
                failures.append(dict(base=[x,y,args.yaw],choice=ci,posture=posture,stage='pregrasp',failure=failure,q=q));continue
            pre_q=dict(q);rows=[];bad=False
            print('pregrasp clear',x,y,ci,posture,flush=True)
            def append(stage,q,held=False,error=0.,angle=0.):
                nonlocal bad
                failure=scene.check(base,q,tool_held=held,closure=0.)
                if error>1e-7 or angle>1e-6:failure['ik']=dict(position_m=error,angle_rad=angle)
                row=dict(stage=stage,q=dict(q),root=base.tolist(),tool_held=held,closure=0.,
                    tool_matrix=scene.state(base,q,tool_held=held,closure=0.)['tool'].tolist(),
                    error_m=error,angle_rad=angle,failure=failure)
                rows.append(row);bad=bool(failure)
                return bad
            for r in c['approach']:
                q,error,angle=solve_palm(base,np.array(r['palm']),q,waist=True)
                if append('approach_tool',q,error=error,angle=angle):break
            if not bad:
                arm=dict(q)
                for r in c['closure']:
                    q={**arm,**r['q']}
                    if append('close_hand',q):break
            if not bad:
                for u in np.linspace(0.,1.,61):
                    desired=target.copy();desired[:3,3]+=[0,-.06*u,.12*u]
                    q,error,angle=solve_palm(base,desired,q,waist=True)
                    if append('lift_tool',q,held=True,error=error,angle=angle):break
            if bad:
                failures.append(dict(base=[x,y,args.yaw],choice=ci,posture=posture,stage=rows[-1]['stage'],
                    failure=rows[-1]['failure'],completed_rows=rows))
                print('rejected',rows[-1]['stage'],rows[-1]['failure'],flush=True);continue
            space=Space(scene,base,rest,pre_q,dict(tool_held=False,closure=0.),open_hand=opened)
            try:entry=plan(space)
            except RuntimeError as error:
                failures.append(dict(base=[x,y,args.yaw],choice=ci,posture=posture,stage='free_entry',
                    failure=str(error),completed_rows=rows));print('entry rejected',str(error),flush=True);continue
            entry_rows=[dict(stage='free_entry',q=space.q_at(v),root=base.tolist(),tool_held=False,closure=0.) for v in entry]
            candidates.append(dict(base=[x,y,args.yaw],choice=ci,posture=posture,entry=entry_rows,rows=rows,
                tool_rest=scene.tool_rest.tolist(),tool_T_palm=scene.tool_T_palm.tolist(),collision_queries=space.calls))
            print('accepted pickup',len(entry_rows),'entry knots',len(rows),'contact states',flush=True);break
        (out/'progress.json').write_text(json.dumps(dict(tested=tested,failures=failures,completed=False),indent=2)+'\n')
        if candidates:break
    geometry={a['geometry']:a['geometry_sha256'] for a in scene.manifest['assets']}
    geometry[scene.manifest['architecture']['path']]=scene.manifest['architecture']['sha256']
    for path in ['assets/cooling_lab_v1/scene.json',scene.cary_geometry,
                 'assets/cary_internal_dra_2500_v1/revisions/working_clamp/prepared_dra_candidate.glb']:
        geometry[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    report=dict(scope=__doc__,passed=bool(candidates),candidates=candidates,failures=failures,tested=tested,
        source_sha256=pins,geometry_sha256=geometry,approaches=args.approaches,staging=choices['staging'],
        seconds=time.monotonic()-started,
        limitations=['Starts at the pickup stance; access-to-pickup walking connection remains to compose.',
                     'Planning omits ankle meshes; independent dense source-geometry review remains required.',
                     'No force, friction, balance, dynamics or sensor-control qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],tested=tested,seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
