"""Collect each identified witness from its existing Cary-side support pose.

This is transfer preparation, not Cary measurement or sample-clamp actuation.
No specimen pose changes during approach/closure; the held transform starts
only after the source tool tips reach the annular wall.
"""
import argparse,hashlib,itertools,json,time
import numpy as np
from optical_choreography import HERE,canonical,load_json,make_base,solve_palm
from optical_delivery import DeliveryScene
from plan_optical_exchange import joint_path
from plan_optical_tool_pickup import seed_targets


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['white','black'],required=True);args=parser.parse_args();kind=args.kind;began=time.monotonic()
    scene=DeliveryScene();holder=scene.cary_staging[kind];port=load_json('previews/specimen_port_refined.json')['candidates'][0]
    carry=canonical(port['rows'][-1]['q']);empty_carry={**carry,**scene.hand_q(0.)};stored=dict(scene.cary_staging)
    if kind=='black':stored['white']=np.array(load_json('previews/optical_white_exchange.json')['initial_holder'])
    target=holder@scene.holder_T_tool@scene.tool_T_palm;pre=target.copy();pre[2,3]+=.02;requests=[]
    for x,y,waist in itertools.product([2.90,2.97,3.05,3.15],[7.85,7.9],[.15,.3]):
        base=make_base(x,y,1.4,carry);q={**empty_carry,'waist_pitch_joint':waist}
        requests.append(dict(base=base.tolist(),target=pre.tolist(),q=q,stance=dict(x=x,y=y,yaw=1.4)))
    candidates=[]
    for i,request in enumerate(seed_targets(requests)):
        base=np.array(request['base']);q,error,angle=solve_palm(base,pre,request['q'],waist=True)
        failure=scene.check(base,q,tool_held=True,stored=stored);carry_failure=scene.check(base,empty_carry,tool_held=True,stored=stored)
        row=dict(root=request['base'],q=q,error_m=error,rotation_error_rad=angle,failure=failure,carry_failure=carry_failure,stance=request['stance'],passed=error<1e-7 and angle<1e-6 and not(failure or carry_failure));candidates.append(row)
        print(kind,'candidate',i,row['passed'],error,failure,carry_failure,flush=True)
    (HERE/'previews'/('cary_'+kind+'_collection_candidates.json')).write_text(json.dumps(candidates,indent=2)+'\n')
    rejected=[]
    for candidate in [c for c in candidates if c['passed']]:
        base=np.array(candidate['root']);q=dict(candidate['q']);contact=[];bad=False;amount=scene.fit['carrier_grip_closure']
        for stage in ['lower_open_tips','close_tweezers','lift_witness']:
            body=dict(q)
            for u in np.linspace(0,1,41):
                if stage=='close_tweezers':q={**body,**scene.hand_q(amount*u)};error=angle=0.
                else:
                    desired=target.copy();desired[2,3]+=.02*(1-u) if stage=='lower_open_tips' else .03*u
                    q,error,angle=solve_palm(base,desired,q,waist=True)
                closure=0. if stage=='lower_open_tips' else amount*u if stage=='close_tweezers' else amount
                held=kind if stage=='lift_witness' else None
                failure=scene.check(base,q,tool_held=True,closure=closure,held_specimen=held,stored=stored)
                contact.append(dict(stage=stage,q=dict(q),closure=closure,held_specimen=held,error_m=error,rotation_error_rad=angle,failure=failure))
                if error>1e-7 or angle>1e-6 or failure:bad=True;break
            if bad:break
        if bad:
            rejected.append(dict(candidate=candidate,last=contact[-1]));print(kind,'rejected contact',contact[-1],flush=True);continue
        incoming=joint_path(scene,base,empty_carry,candidate['q'],dict(tool_held=True,stored=stored))
        outgoing=joint_path(scene,base,q,carry,dict(tool_held=True,closure=amount,held_specimen=kind,stored=stored))
        result=dict(scope=__doc__,kind=kind,root=base.tolist(),stance=candidate['stance'],initial_holder=holder.tolist(),incoming=incoming,contact=contact,outgoing=outgoing,rejected_contact_candidates=rejected,passed_planning_geometry=True,independent_composed_review_pending=True,wall_seconds=time.monotonic()-began,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['plan_cary_collection.py','optical_delivery.py','optical_choreography.py','previews/specimen_port_refined.json','previews/specimen_tool_fit.json']})
        (HERE/'previews'/('cary_'+kind+'_collection.json')).write_text(json.dumps(result,indent=2)+'\n');print(kind,'collection planned',result['wall_seconds'],flush=True);return
    (HERE/'previews'/('cary_'+kind+'_collection_rejected.json')).write_text(json.dumps(rejected,indent=2)+'\n')
    raise RuntimeError('No clear Cary collection path for '+kind)


if __name__=='__main__':main()
