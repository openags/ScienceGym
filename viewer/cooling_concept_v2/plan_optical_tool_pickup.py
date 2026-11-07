"""Plan a real approach, closure and lift from ordinary tray-supported tweezers."""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
from optical_choreography import HERE,Scene,Space,canonical,load_json,make_base,solve_palm,solve_position
from plan_optical_approaches import plan
from source_geometry import hand_manager,set_hand


def seed_targets(requests):
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page();page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=''));page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
        output=page.evaluate('''async requests=>{const{HandIK}=await import('./hand_ik.js'),T=await import('three'),m=await(await fetch('./runtime_scene.json')).json(),kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;kin.joints.find(j=>j.name==='right_shoulder_roll_joint').limits.upper=-.025;const ik=new HandIK(kin);for(const r of requests){const root=new T.Matrix4().fromArray(r.base.flat()).transpose(),target=new T.Matrix4().fromArray(r.target.flat()).transpose().premultiply(root.invert()),q={...r.q};r.error=ik.solve(q,'right',new T.Vector3().setFromMatrixPosition(target),target);r.rotationError=ik.lastRotationError;r.q=q;}return requests;}''',requests)
        browser.close();return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--endpoints-only',action='store_true');parser.add_argument('--reuse-endpoints',action='store_true');args=parser.parse_args();began=time.monotonic()
    scene=Scene();poses=load_json('motion_poses.json');rest=canonical({**poses['poses']['rest'],**poses['poses']['stance']});closed=scene.hand_q(0.)
    target=scene.tool_rest@scene.tool_T_palm;requests=[];hand=hand_manager('right');approaches=[]
    scene.state(make_base(10.,7.85,1.4,rest),rest)
    for c in reversed(scene.staging['candidates']):
        if not c['passed']:continue
        for offset in [[0,0,-.05],[0,0,.05],[-.04,0,-.04],[.04,0,-.04],[.04,0,0],[-.04,0,0]]:
            world_offset=scene.tool_rest[:3,:3]@np.array(offset);clear=True
            for u in np.linspace(0,1,41):
                palm=target.copy();palm[:3,3]+=world_offset*(1-u);set_hand(hand,'right',c['open_q'],palm)
                if hand.in_collision_other(scene.tool) or hand.in_collision_other(scene.obstacles) or any(hand.in_collision_other(m) for m in scene.specimens.values()):clear=False;break
            if clear:approaches.append(dict(opened=c['open_q'],offset=world_offset.tolist(),tool_frame_offset=offset))
    print('local approach candidates',len(approaches),flush=True)
    (HERE/'previews/optical_tool_approach_choices.json').write_text(json.dumps(approaches,indent=2)+'\n');assert approaches,'No collision-free hand approach direction'
    chosen=approaches[0];opened=chosen['opened'];pre=target.copy();pre[:3,3]+=chosen['offset']
    for x,y,waist,yaw in itertools.product([10.00,9.95,10.05],[7.90,7.85,7.95],[.15,.3],[-.4,0,.4]):
        base=make_base(x,y,1.4,rest);seed={**rest,**opened,'waist_pitch_joint':waist,'waist_yaw_joint':yaw}
        requests.append(dict(base=base.tolist(),target=pre.tolist(),q=seed,stance=dict(x=x,y=y,yaw=1.4,waist=waist,waist_yaw_seed=yaw)))
    candidates=[]
    if args.reuse_endpoints:candidates=load_json('previews/optical_tool_pickup_endpoints.json')['candidates']
    else:
        requests=seed_targets(requests)
        for i,request in enumerate(requests):
            base=np.array(request['base']);q,error,angular=solve_palm(base,pre,request['q'],waist=True);first=scene.check(base,q)
            row=dict(stance=request['stance'],base=base.tolist(),q=q,error_m=error,orientation_error_rad=angular,collision=first)
            row['passed']=error<1e-7 and angular<1e-6 and not first and not scene.check(base,rest);candidates.append(row)
            print('pregrasp',i,'pass',row['passed'],'error',error,'collision',first,flush=True)
    report=dict(scope=__doc__,open_hand=opened,closed_hand=closed,candidates=candidates,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['optical_choreography.py','plan_optical_tool_pickup.py','previews/tweezers_staging.json','previews/tweezers_closure.json','previews/specimen_tool_fit.json']})
    if args.reuse_endpoints:report['source_sha256']['previews/optical_tool_pickup_endpoints.json']=hashlib.sha256((HERE/'previews/optical_tool_pickup_endpoints.json').read_bytes()).hexdigest()
    else:(HERE/'previews/optical_tool_pickup_endpoints.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.endpoints_only:return
    for candidate in (c for c in candidates if c['passed']):
        base=np.array(candidate['base']);q=dict(candidate['q']);contact=[];bad=False
        for u in np.linspace(0,1,41):
            desired=pre*(1-u)+target*u;desired[3]=[0,0,0,1]
            q,error,angular=solve_palm(base,desired,q,waist=True);failure=scene.check(base,q)
            contact.append(dict(stage='approach_tool',q=dict(q),error_m=error,rotation_error_rad=angular,failure=failure,tool_held=False,closure=0.))
            if error>1e-7 or angular>1e-6 or failure:bad=True;break
        if bad:print('rejected approach',candidate['stance'],contact[-1]['failure'],contact[-1].get('error_m'),flush=True);continue
        grasp_q=dict(q)
        for u in np.linspace(0,1,41):
            q={**grasp_q,**{n:opened[n]*(1-u)+closed[n]*u for n in opened}};failure=scene.check(base,q)
            contact.append(dict(stage='close_hand_on_tool',q=dict(q),failure=failure,tool_held=False,closure=0.))
            if failure:bad=True;break
        if bad:print('rejected closure',candidate['stance'],contact[-1]['failure'],flush=True);continue
        q=canonical(q)
        for u in np.linspace(0,1,41):
            desired=target.copy();desired[:3,3]+=[0,-.04*u,.06*u]
            q,error=solve_position(base,desired[:3,3],q);failure=scene.check(base,q,tool_held=True)
            contact.append(dict(stage='lift_tool',q=dict(q),error_m=error,orientation_constraint='free; tool follows the actual palm transform',failure=failure,tool_held=True,closure=0.))
            if error>1e-5 or failure:bad=True;break
        if bad:print('rejected lift',candidate['stance'],contact[-1]['failure'],contact[-1].get('error_m'),flush=True);continue
        space=Space(scene,base,rest,candidate['q'],{},open_hand=opened);print('plan entry',candidate['stance'],flush=True)
        path=plan(space);entry=[dict(q=space.q_at(v)) for v in path]
        result=dict(scope=__doc__,source_sha256=report['source_sha256'],stance=candidate['stance'],root=base.tolist(),entry=entry,contact=contact,open_hand=opened,approach=chosen,tool_rest=scene.tool_rest.tolist(),tray_position_m=scene.tray_position.tolist(),tray_matrix=scene.tray_matrix.tolist(),layout_transform_from_local_support_fit=scene.staging_transform.tolist(),specimen_staging={k:v.tolist() for k,v in scene.specimen_rest.items()},passed_local_geometry=True,collision_queries=space.calls,wall_seconds=time.monotonic()-began,whole_scene_validation_pending=True)
        (HERE/'previews/optical_tool_pickup_path.json').write_text(json.dumps(result,indent=2)+'\n');print('pickup planned',len(entry),len(contact),result['wall_seconds'],flush=True);return
    raise RuntimeError('No complete pickup path survived the local geometry review')


if __name__=='__main__':main()
