"""Plan G1 approach, finger closure, sliding, release and withdrawal at Cary.

Uses source hand/whole-body geometry in the established laboratory. This is
authored kinematics; contact-force and floating-base validation remain open.
"""
import argparse,hashlib,itertools,json,time
import numpy as np
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE,Space,canonical,load_json,make_base,solve_palm
from plan_optical_tool_pickup import seed_targets
from plan_optical_approaches import plan
from source_geometry import hand_manager,set_hand
from cary_contact_ik import ContactIK


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='04');args=parser.parse_args()
    began=time.monotonic();prefix='cary_lid_operation_'+args.trial;snapshot=HERE/'previews'/('cary_lid_operation_source_'+args.trial);snapshot.mkdir(exist_ok=True)
    sources={n:(HERE/n).read_bytes() for n in ['plan_cary_lid.py','cary_access_scene.py','cary_contact_ik.py','previews/cary_lid_grasps.json','optical_choreography.py']}
    for n,data in sources.items():
        out=snapshot/n;out.parent.mkdir(exist_ok=True,parents=True);out.write_bytes(data)
    scene=CaryAccessScene(cover_candidate=True);grasps=load_json('previews/cary_lid_grasps.json');solver=ContactIK(scene)
    poses=load_json('motion_poses.json');rest=canonical({**poses['poses']['rest'],**poses['poses']['stance']})
    hand=hand_manager('right');local=scene.local_obstacles();hand_paths=[]
    for index,c in enumerate(grasps['candidates'][:160]):
        target=np.array(c['palm_matrix']);target[:3,3]+=grasps['handle_center_m'];found=False
        for factor,offset in itertools.product([.85,.65,.4],[[0,0,.05],[0,-.02,.05],[0,.02,.05]]):
            opened={**c['q'],'right_index_1_joint':c['q']['right_index_1_joint']*factor,'right_thumb_2_joint':c['q']['right_thumb_2_joint']*factor}
            rows=[]
            for stage in ['approach','close']:
                for u in np.linspace(0,1,31):
                    palm=target.copy();palm[:3,3]+=np.array(offset)*(1-u) if stage=='approach' else 0
                    q=opened if stage=='approach' else {n:opened[n]*(1-u)+c['q'][n]*u for n in opened}
                    set_hand(hand,'right',q,palm)
                    if hand.in_collision_other(local):break
                    rows.append(dict(stage=stage,q=dict(q),palm=palm.tolist()))
                else:continue
                break
            if len(rows)==62:
                hand_paths.append(dict(candidate=index,profile=c,opened=opened,offset=offset,target=target.tolist(),rows=rows));found=True;break
        if found:print('hand path',index,'count',len(hand_paths),flush=True)
        if len(hand_paths)>=12:break
    (HERE/'previews'/(prefix+'_hand_paths.json')).write_text(json.dumps(hand_paths,indent=2)+'\n')
    if not hand_paths:raise RuntimeError('No geometrically clear local approach/closure')
    requests=[]
    for i,path in enumerate(hand_paths):
        if path['profile']['normal_sign']!= -1:continue
        pre=np.array(path['rows'][0]['palm'])
        for x,y,yaw,waist in itertools.product([2.24,2.30,2.36],[7.85,7.90],[1.4,np.pi/2],[0.,.2]):
            q={**rest,**path['opened'],'waist_pitch_joint':waist};base=make_base(x,y,yaw,q)
            requests.append(dict(base=base.tolist(),target=pre.tolist(),q=q,path=i,stance=dict(x=x,y=y,yaw=yaw)))
    seeded=seed_targets(requests);rejected=[]
    ordered=sorted(enumerate(seeded),key=lambda pair:(abs(pair[1]['stance']['x']-2.36)+abs(pair[1]['stance']['y']-7.90)+(0 if hand_paths[pair[1]['path']]['profile']['tilt_rad']>.5 else 1)))
    for attempt,seed in ordered:
        scene.set_access();path=hand_paths[seed['path']];base=np.array(seed['base']);pre=np.array(seed['target'])
        q,error,angle=solver.solve(base,pre,seed['q']);failure=scene.check(base,q)
        if error>1e-7 or angle>1e-6 or failure or scene.check(base,rest):
            rejected.append(dict(attempt=attempt,stage='pregrasp',error_m=error,rotation_error_rad=angle,failure=failure));continue
        first=dict(q);contact=[];bad=False
        for row in path['rows']:
            desired=np.array(row['palm']);q.update(row['q']);q,error,angle=solver.solve(base,desired,q);failure=scene.check(base,q)
            contact.append(dict(stage=row['stage'],q=dict(q),lid_m=0.,error_m=error,rotation_error_rad=angle,failure=failure))
            if error>1e-7 or angle>1e-6 or failure:bad=True;break
        if not bad:
            target=np.array(path['target'])
            for u in np.linspace(0,1,62):
                desired=target.copy();desired[1,3]+=.305*u;scene.set_access(lid=.305*u)
                q,error,angle=solver.solve(base,desired,q);failure=scene.check(base,q)
                contact.append(dict(stage='slide',q=dict(q),lid_m=float(.305*u),error_m=error,rotation_error_rad=angle,failure=failure))
                if error>1e-7 or angle>1e-6 or failure:bad=True;break
        if not bad:
            for row in reversed(path['rows']):
                desired=np.array(row['palm']);desired[1,3]+=.305;q.update(row['q']);q,error,angle=solver.solve(base,desired,q);failure=scene.check(base,q)
                contact.append(dict(stage='release' if row['stage']=='close' else 'withdraw',q=dict(q),lid_m=.305,error_m=error,rotation_error_rad=angle,failure=failure))
                if error>1e-7 or angle>1e-6 or failure:bad=True;break
        if bad:
            rejected.append(dict(attempt=attempt,stage=contact[-1]['stage'],last=contact[-1]));print('rejected',attempt,contact[-1]['stage'],error,failure,flush=True);continue
        print('contact path',attempt,'passed; plan arm approaches',flush=True)
        try:
            scene.set_access();space=Space(scene,base,rest,first,{},open_hand=path['opened']);entry=[dict(q=space.q_at(v),lid_m=0.) for v in plan(space)]
            scene.set_access(lid=.305);space=Space(scene,base,rest,q,{},open_hand=path['opened']);exit_path=[dict(q=space.q_at(v),lid_m=.305) for v in reversed(plan(space))]
        except RuntimeError as e:
            rejected.append(dict(attempt=attempt,stage='free_arm',failure=str(e)));print('rejected free-arm',attempt,str(e),flush=True);continue
        report=dict(scope=__doc__,passed_planning_geometry=True,independent_composed_review_pending=True,root=base.tolist(),stance=seed['stance'],grasp=path,entry=entry,contact=contact,exit=exit_path,rejected=rejected,seconds=time.monotonic()-began,source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(data).hexdigest() for n,data in sources.items()})
        report['geometry']=scene.cary_geometry
        report['geometry_sha256']=hashlib.sha256((__import__('source_geometry').ROOT/scene.cary_geometry).read_bytes()).hexdigest()
        (HERE/'previews'/(prefix+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('lid operation planned',report['seconds'],flush=True);return
    (HERE/'previews'/(prefix+'_rejected.json')).write_text(json.dumps(dict(hand_paths=hand_paths,rejected=rejected),indent=2)+'\n')
    raise RuntimeError('No full-body lid operation candidate passed')


if __name__=='__main__':main()
