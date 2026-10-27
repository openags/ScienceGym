"""Extend the Cary opening using grounded steps and an already reviewed approach.

Reverse the previous 150 mm opening's withdrawal, push the lid by stepping
forward while preserving palm contact, release, step back, and reuse the
reviewed withdrawal. This avoids assuming a crowded fixed-root arm-return
path exists. The exported composition still needs independent review.
"""
import argparse
import hashlib
import json
import numpy as np
from cary_access_scene import CaryAccessScene
from cary_contact_ik import ContactIK
from cary_grounded_steps import translation_steps
from optical_choreography import HERE, canonical
from source_geometry import fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');args=parser.parse_args()
    folder=HERE/'previews'/('cary_lid_stepped_'+args.trial);folder.mkdir(exist_ok=False)
    names=['extend_cary_lid.py','cary_access_scene.py','cary_contact_ik.py','cary_grounded_steps.py',
           'optical_choreography.py','source_geometry.py','previews/cary_lid_operation_08.json',
           'previews/cary_cover_carry_03.json']
    pins={}
    for n in names:
        data=(HERE/n).read_bytes();p=folder/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);pins[n]=hashlib.sha256(data).hexdigest()
    prior=json.loads((HERE/'previews/cary_lid_operation_08.json').read_text())
    cover=json.loads((HERE/'previews/cary_cover_carry_03.json').read_text())['rows'][-1]['cover_matrix']
    scene=CaryAccessScene(cover_candidate=True);scene.set_access(lid=.15,cover=cover);solver=ContactIK(scene,include_cover=False,include_bay=True)
    base=np.array(prior['root']);initial_base=base.copy();rows=[]
    def require_target(stage,position,angle,contact=True):
        # A held handle requires exact contact. Once released, the palm is a
        # free-space clearance waypoint, with no object attached to its target.
        position_limit,angle_limit=(1e-7,1e-6) if contact else (.001,.01)
        if position>position_limit or angle>angle_limit:
            failure=dict(stage=stage,position_m=position,angle_rad=angle,
                position_limit_m=position_limit,angle_limit_rad=angle_limit)
            (folder/'rejected.json').write_text(json.dumps(dict(scope=__doc__,
                rows=rows,ik_failure=failure,source_sha256=pins),indent=2)+'\n')
            raise RuntimeError(str(failure))
    def check(stage,q,root,lid,time_s=None):
        scene.set_access(lid=lid,cover=cover)
        failure=scene.check(root,q)
        mechanism=scene.access_clearance('lid')
        if mechanism:failure['lid_environment']=mechanism
        row=dict(stage=stage,q=canonical(q),root=np.asarray(root).tolist(),lid_m=float(lid),cover_matrix=cover,failure=failure)
        if time_s is not None:row['time_s']=float(time_s)
        rows.append(row)
        if failure:
            (folder/'rejected.json').write_text(json.dumps(dict(scope=__doc__,rows=rows,source_sha256=pins),indent=2)+'\n')
            raise RuntimeError(str(dict(stage=stage,failure=failure)))
        return row
    withdrawal=[r for r in prior['contact'] if r['stage']=='withdraw']
    release=[r for r in prior['contact'] if r['stage']=='release']
    # Fully sample the reviewed free-arm edge, not only its endpoints.
    entry=list(reversed(prior['exit']))
    for a,b in zip(entry,entry[1:]):
        for u in np.linspace(0,1,61):
            check('known_entry',{n:a['q'][n]*(1-u)+b['q'][n]*u for n in a['q']},base,.15)
    for row in reversed(withdrawal):check('approach_pull',row['q'],base,.15)
    for row in reversed(release):check('close_on_pull',row['q'],base,.15)
    q=dict(rows[-1]['q']);grasp=base@fk(q)['right_palm_force_sensor'];goal=base.copy();goal[1,3]+=.05
    steps=translation_steps(base,goal,q)
    for step in steps:
        root=np.array(step['root']);lid=.15+root[1,3]-base[1,3]
        target=grasp.copy();target[1,3]+=lid-.15
        seed={**q,**{n:v for n,v in step['q'].items() if any(s in n for s in ['hip','knee','ankle'])}}
        scene.set_access(lid=lid,cover=cover);q,position,angle=solver.solve(root,target,seed)
        require_target('step_push',position,angle)
        check('step_push_lid',q,root,lid,step['time_s'])
    base=goal;closed=dict(q);opened=release[-1]['q'];hand_names=list(prior['grasp']['opened'])
    for u in np.linspace(0,1,31):
        q={**closed,**{n:closed[n]*(1-u)+opened[n]*u for n in hand_names}}
        check('release_pull',q,base,.20)
    released_palm=base@fk(q)['right_palm_force_sensor']
    for u in np.linspace(0,1,21):
        target=released_palm.copy();target[2,3]+=.02*u
        q,position,angle=solver.solve(base,target,q)
        require_target('clear_pull',position,angle,contact=False)
        check('lift_clear_of_pull',q,base,.20)['free_palm_target_error']=dict(position_m=position,angle_rad=angle)
    for step in translation_steps(base,initial_base,q):
        root=np.array(step['root']);target=released_palm.copy();target[1,3]+=root[1,3]-base[1,3];target[2,3]+=.02
        seed={**q,**{n:v for n,v in step['q'].items() if any(s in n for s in ['hip','knee','ankle'])}}
        q,position,angle=solver.solve(root,target,seed)
        require_target('step_back',position,angle,contact=False)
        check('step_back_after_release',q,root,.20,step['time_s'])['free_palm_target_error']=dict(position_m=position,angle_rad=angle)
    base=initial_base;current=rows[-1]['q'];target=release[-1]['q']
    for u in np.linspace(0,1,61):check('recover_known_arm_pose',{n:current[n]*(1-u)+target[n]*u for n in current},base,.20)
    for row in withdrawal:check('known_withdraw',row['q'],base,.20)
    for a,b in zip(prior['exit'],prior['exit'][1:]):
        for u in np.linspace(0,1,61):check('known_return',{n:a['q'][n]*(1-u)+b['q'][n]*u for n in a['q']},base,.20)
    report=dict(scope=__doc__,passed_planning_geometry=True,initial_lid_m=.15,final_lid_m=.20,
        initial_root=initial_base.tolist(),rows=rows,source_sha256=pins,
        limitations=['Sampled source geometry and grounded sole kinematics only.',
                     'No force retention, balance, dynamics or composed-renderer review yet.'])
    (folder/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print('planned',len(rows),'states',flush=True)


if __name__=='__main__':main()
