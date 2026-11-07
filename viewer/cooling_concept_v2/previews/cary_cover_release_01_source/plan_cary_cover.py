"""Plan source-G1 approach, grip and supported release of the Cary hood.

The main lid is partially open. The ordinary removable hood stays registered
to the actual palm after grip; no separate object trajectory is used while
held. This plans kinematics, not retention forces or dynamic balance. Walking
and placement are separate continuations and must share the final state.
"""
import argparse,hashlib,itertools,json,time
import numpy as np
from cary_access_scene import CaryAccessScene,translation
from cary_contact_ik import ContactIK
from optical_choreography import HERE,Space,canonical,load_json,make_base
from plan_optical_tool_pickup import seed_targets
from plan_optical_approaches import plan
from source_geometry import ROOT,fk,hand_manager,set_hand


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01');parser.add_argument('--lid',type=float,default=.15);args=parser.parse_args()
    started=time.monotonic();prefix='cary_cover_release_'+args.trial
    snapshot=HERE/'previews'/(prefix+'_source');snapshot.mkdir(exist_ok=True)
    names=['plan_cary_cover.py','cary_access_scene.py','cary_contact_ik.py','optical_choreography.py','previews/cary_cover_grasps_refined.json']
    sources={n:(HERE/n).read_bytes() for n in names}
    for n,data in sources.items():
        dest=snapshot/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    scene=CaryAccessScene(cover_candidate=True);scene.set_access(lid=args.lid)
    solver=ContactIK(scene);grasps=load_json('previews/cary_cover_grasps_refined.json')
    poses=load_json('motion_poses.json');rest=canonical({**poses['poses']['rest'],**poses['poses']['stance']})
    hand=hand_manager('right');local=scene.local_obstacles();paths=[]
    for index,candidate in enumerate(grasps['candidates']):
        if max(candidate['finger_gap_m'],candidate['thumb_gap_m'])>.00025:continue
        target=np.array(candidate['palm_matrix']);target[:3,3]+=grasps['handle_center_m']
        for factor,offset in itertools.product([.85,.65,.4],[[0,0,.06],[0,-.02,.06],[0,.02,.06]]):
            opened={**candidate['q'],'right_index_1_joint':candidate['q']['right_index_1_joint']*factor,'right_thumb_2_joint':candidate['q']['right_thumb_2_joint']*factor};rows=[]
            for stage in ['approach','close']:
                for u in np.linspace(0,1,31):
                    palm=target.copy();palm[:3,3]+=np.array(offset)*(1-u) if stage=='approach' else 0
                    q=opened if stage=='approach' else {n:opened[n]*(1-u)+candidate['q'][n]*u for n in opened}
                    set_hand(hand,'right',q,palm)
                    if hand.in_collision_other(local):break
                    rows.append(dict(stage=stage,palm=palm.tolist(),hand_q=dict(q)))
                else:continue
                break
            if len(rows)==62:
                paths.append(dict(candidate=index,profile=candidate,opened=opened,offset=offset,target=target.tolist(),rows=rows));break
    print('local hand paths',len(paths),flush=True)
    (HERE/'previews'/(prefix+'_hand_paths.json')).write_text(json.dumps(paths,indent=2)+'\n')
    if not paths:raise RuntimeError('No clear approach to the hood handle')
    requests=[]
    for i,path in enumerate(paths):
        for x,y,yaw,waist in itertools.product([2.50,2.45,2.55],[7.70,7.65,7.75],[1.4,np.pi/2],[0.,.15]):
            q={**rest,**path['opened'],'waist_pitch_joint':waist};base=make_base(x,y,yaw,q)
            requests.append(dict(base=base.tolist(),target=path['rows'][0]['palm'],q=q,path=i,stance=dict(x=x,y=y,yaw=yaw)))
    rejected=[]
    for attempt,seed in enumerate(seed_targets(requests)):
        scene.set_access(lid=args.lid);path=paths[seed['path']];base=np.array(seed['base'])
        q,error,angle=solver.solve(base,np.array(seed['target']),seed['q']);failure=scene.check(base,q)
        if error>1e-7 or angle>1e-6 or failure or scene.check(base,rest):
            rejected.append(dict(attempt=attempt,stage='pregrasp',error_m=error,rotation_error_rad=angle,failure=failure));continue
        first=dict(q);contact=[];bad=False;grasp=np.array(path['target']);inverse_grasp=np.linalg.inv(grasp)
        trajectory=[dict(stage=r['stage'],palm=r['palm'],hand_q=r['hand_q'],held=False) for r in path['rows']]
        for stage,a,b in [('unhook',[0,0,0],[0,0,.006]),('release_forward',[0,0,.006],[0,-.025,.006])]:
            for u in np.linspace(0,1,21):
                offset=np.array(a)*(1-u)+np.array(b)*u
                trajectory.append(dict(stage=stage,palm=(translation(offset)@grasp).tolist(),hand_q=path['profile']['q'],held=True))
        for row in trajectory:
            desired=np.array(row['palm']);q.update(row['hand_q'])
            scene.set_access(lid=args.lid,cover=desired@inverse_grasp if row['held'] else None)
            q,error,angle=solver.solve(base,desired,q)
            actual=base@fk(q)['right_palm_force_sensor'];cover=actual@inverse_grasp if row['held'] else np.eye(4)
            scene.set_access(lid=args.lid,cover=cover);failure=scene.check(base,q)
            mechanism=scene.access_clearance('cover') if row['held'] else []
            contact.append(dict(stage=row['stage'],q=dict(q),cover_matrix=cover.tolist(),held=row['held'],lid_m=args.lid,error_m=error,rotation_error_rad=angle,failure=failure,mechanism_failures=mechanism,bounded_contacts=scene.last_bounded_contacts if row['held'] else []))
            if error>1e-7 or angle>1e-6 or failure or mechanism:bad=True;break
        if bad:
            rejected.append(dict(attempt=attempt,stage=contact[-1]['stage'],last=contact[-1]));print('rejected',attempt,contact[-1]['stage'],error,failure,mechanism[:1],flush=True);continue
        print('contact path',attempt,'passed; planning entry',flush=True)
        try:
            scene.set_access(lid=args.lid);space=Space(scene,base,rest,first,{},open_hand=path['opened'])
            entry=[dict(q=space.q_at(v),cover_matrix=np.eye(4).tolist(),held=False,lid_m=args.lid) for v in plan(space)]
        except RuntimeError as exc:
            rejected.append(dict(attempt=attempt,stage='entry',failure=str(exc)));continue
        report=dict(scope=__doc__,passed_planning_geometry=True,independent_composed_review_pending=True,root=base.tolist(),stance=seed['stance'],grasp=path,grasp_palm_world=grasp.tolist(),entry=entry,contact=contact,rejected=rejected,seconds=time.monotonic()-started,geometry=scene.cary_geometry,geometry_sha256=hashlib.sha256((ROOT/scene.cary_geometry).read_bytes()).hexdigest(),source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(data).hexdigest() for n,data in sources.items()})
        (HERE/'previews'/(prefix+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('hood release planned',report['seconds'],flush=True);return
    (HERE/'previews'/(prefix+'_rejected.json')).write_text(json.dumps(dict(paths=paths,rejected=rejected),indent=2)+'\n')
    raise RuntimeError('No source-geometry hood release passed')


if __name__=='__main__':main()
