"""Withdraw the lifted long forceps to a posture clear at both Cary stances.

The palm may change orientation while keeping the source grip. Check the
actual whole-body/tool meshes and the destination before planning the walk.
This supplies no dynamic carrying or balance qualification.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
from scipy.optimize import least_squares
from cary_bimanual_ik import palm_fk
from cary_tool_pickup_scene import CaryToolPickupScene
from optical_choreography import HERE,ARM,JOINTS,Space,solve_position
from plan_optical_approaches import plan
from source_geometry import fk


def arm_position(base,target,seed):
    q=dict(seed);bounds=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in ARM])
    bounds[ARM.index('right_shoulder_roll_joint'),1]=-.025
    initial=np.clip([q[n] for n in ARM],bounds[:,0]+1e-8,bounds[:,1]-1e-8)
    def residual(values):
        actual=base@palm_fk({**q,**dict(zip(ARM,values))},'right')
        return np.r_[(actual[:3,3]-target)*10,(values-initial)*.001]
    result=least_squares(residual,initial,bounds=(bounds[:,0],bounds[:,1]),max_nfev=100,ftol=1e-12,xtol=1e-12,gtol=1e-12)
    q.update(dict(zip(ARM,map(float,result.x))))
    return q,float(np.linalg.norm(residual(result.x)[:3])/10)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--pickup',default='previews/cary_tool_pickup_02/plan.json')
    parser.add_argument('--exchange',default='previews/cary_exchange_entry_01/plan.json')
    parser.add_argument('--joint-search',action='store_true',help='Search upright joint postures instead of prescribing a Cartesian retreat.')
    args=parser.parse_args();out=HERE/'previews'/('cary_tool_carry_'+args.trial);out.mkdir(exist_ok=False)
    pickup=json.loads((HERE/args.pickup).read_text());exchange=json.loads((HERE/args.exchange).read_text())
    assert pickup['passed'] and exchange['passed']
    names=['plan_cary_tool_carry.py','cary_tool_pickup_scene.py','cary_tool_scene.py','cary_clamp_scene.py',
        'cary_clamp.py','cary_access_scene.py','optical_choreography.py','optical_delivery.py',
        'source_geometry.py','cary_bimanual_ik.py','plan_optical_approaches.py','long_forceps.py','tweezers_geometry.py','cary_access_episode.json',
        args.pickup,args.exchange,pickup['staging']]
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryToolPickupScene(pickup['staging']);initial=pickup['candidates'][0]['rows'][-1]
    base=np.array(initial['root']);goal=np.array(exchange['candidates'][0]['rows'][0]['root'])
    assert np.max(abs(base[:3,:3]-goal[:3,:3]))<1e-10
    palm=base@fk(initial['q'])['right_palm_force_sensor'];failures=[];accepted=[];started=time.monotonic()
    strategies=[('upright_then_withdraw',[0,-.12,.04]),('upright_then_withdraw',[0,-.10,.06]),
                ('straighten_waist',[0.,0.]),('straighten_waist',[.1,0.])]
    strategies += [('withdraw_palm',offset) for offset in [[0,-.12,.04],[0,-.10,.06],[.03,-.12,.04],[0,-.16,.06]]]
    if args.joint_search:strategies=[]
    for strategy,parameters in strategies:
        q=dict(initial['q']);rows=[];failure={}
        if strategy=='upright_then_withdraw':
            for u in np.linspace(0.,1.,41):
                q=dict(initial['q'])
                for n in ['waist_pitch_joint','waist_yaw_joint']:q[n]=initial['q'][n]*(1-u)
                failure=scene.check(base,q,tool_held=True,closure=0.)
                if failure:break
                rows.append(dict(stage='straighten_waist',q=q,root=base.tolist(),tool_held=True,closure=0.,error_m=0.))
            if failure:
                failures.append(dict(strategy=strategy,parameters=parameters,fraction=float(u),failure=failure,completed_rows=rows));continue
            upright_palm=base@fk(q)['right_palm_force_sensor']
        for u in np.linspace(0.,1.,61):
            if strategy=='straighten_waist':
                q=dict(initial['q']);error=0.
                for n,value in zip(['waist_pitch_joint','waist_yaw_joint'],parameters):q[n]=initial['q'][n]*(1-u)+value*u
            elif strategy=='upright_then_withdraw':
                desired=upright_palm[:3,3]+np.array(parameters)*u;q,error=arm_position(base,desired,q)
            else:
                desired=palm[:3,3]+np.array(parameters)*u;q,error=solve_position(base,desired,q)
            failure=scene.check(base,q,tool_held=True,closure=0.)
            if error>1e-5:failure['palm_position_error_m']=error
            if failure:break
            rows.append(dict(stage=strategy,q=q,root=base.tolist(),tool_held=True,closure=0.,
                error_m=error,orientation_constraint='free; held tool follows source palm FK'))
        if not failure:failure=scene.check(goal,q,tool_held=True,closure=0.)
        if failure:failures.append(dict(strategy=strategy,parameters=parameters,fraction=float(u),failure=failure,completed_rows=rows))
        else:
            accepted.append(dict(strategy=strategy,parameters=parameters,rows=rows,destination_root=goal.tolist()));break
    if args.joint_search:
        for pitch,roll,yaw,elbow in itertools.product([-.4,0.,-.7],[-.4,-.7],[0.,-.5],[1.1,1.5,.7]):
            q=dict(initial['q']);q.update(waist_pitch_joint=0.,waist_yaw_joint=0.,right_shoulder_pitch_joint=pitch,
                right_shoulder_roll_joint=roll,right_shoulder_yaw_joint=yaw,right_elbow_joint=elbow,
                right_wrist_roll_joint=0.,right_wrist_pitch_joint=0.,right_wrist_yaw_joint=0.)
            failure=scene.check(base,q,tool_held=True,closure=0.)
            if not failure:failure=scene.check(goal,q,tool_held=True,closure=0.)
            if failure:
                failures.append(dict(strategy='upright_joint_posture',parameters=[pitch,roll,yaw,elbow],failure=failure));continue
            space=Space(scene,base,initial['q'],q,dict(tool_held=True,closure=0.))
            try:
                print('planning upright carry',[pitch,roll,yaw,elbow],flush=True);path=plan(space)
            except RuntimeError as error:
                failures.append(dict(strategy='upright_joint_path',parameters=[pitch,roll,yaw,elbow],failure=str(error)));continue
            rows=[dict(stage='fold_tool_to_carry',q=space.q_at(v),root=base.tolist(),tool_held=True,closure=0.) for v in path]
            accepted.append(dict(strategy='upright_joint_posture',parameters=[pitch,roll,yaw,elbow],rows=rows,
                destination_root=goal.tolist(),collision_queries=space.calls));break
    report=dict(scope=__doc__,passed=bool(accepted),candidates=accepted,failures=failures,
        source_sha256=pins,pickup=args.pickup,exchange=args.exchange,seconds=time.monotonic()-started,
        limitations=['Planning omits ankle housings; independent interpolation and complete walk review remain required.',
                     'No physical grip, balance, dynamics or sensor-policy qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],failures=len(failures),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
