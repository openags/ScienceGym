"""Solve both complete G1 arms for a source-checked Cary reference extraction.

This starts at established tool/reference grasps. The output is a whole-body
reach and extraction candidate, not a complete pickup or measurement episode.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
from cary_bimanual_ik import solve,palm_fk
from cary_tool_scene import CaryToolScene
from optical_choreography import HERE,make_base,canonical
from source_geometry import ROOT,ASSETS,fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--trial',default='01')
    parser.add_argument('--extraction',default='previews/cary_reference_extraction_01/search.json')
    parser.add_argument('--max-candidates',type=int,default=1)
    args=parser.parse_args();out=HERE/'previews'/('cary_bimanual_exchange_'+args.trial);out.mkdir(exist_ok=False)
    extraction=json.loads((HERE/args.extraction).read_text())
    clamps=json.loads((HERE/extraction['clamp_source']).read_text())
    references=json.loads((HERE/extraction['reference_source']).read_text())
    names=['plan_cary_bimanual_exchange.py','cary_bimanual_ik.py','cary_tool_scene.py',
        'cary_clamp_scene.py','cary_clamp.py','cary_access_scene.py','long_forceps.py',
        'optical_choreography.py','optical_delivery.py','source_geometry.py',args.extraction,
        extraction['clamp_source'],extraction['reference_source'],'previews/cary_lid_operation_08.json']
    pins={}
    for name in names:
        data=(HERE/name).read_bytes();dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        pins[name]=hashlib.sha256(data).hexdigest()
    initial=json.loads((HERE/names[-1]).read_text())['exit'][-1]['q']
    assert max(np.max(abs(fk(initial)[side+'_palm_force_sensor']-palm_fk(initial,side))) for side in ['left','right'])<1e-10
    sample=extraction['candidates'][0];c=clamps['candidates'][sample['clamp_candidate']];r=references['candidates'][sample['reference_candidate']]
    scene=CaryToolScene(c['tool_T_palm'],r['palm_matrix'])
    scene.set_access(lid=extraction['lid_opening_m'],cover=extraction['cover_matrix'])
    failures=[];accepted=[];tested=0;started=time.monotonic()
    # Test all selected directions for the first viable arm stance before
    # changing the stance; failed reach and mesh evidence are retained.
    for x,y,yaw in itertools.product([2.65,2.55,2.75,2.45,2.85],
            [7.85,7.80,7.90,7.95],[np.pi/2,1.4,1.7,1.2,1.9]):
        for ei,e in enumerate(extraction['candidates']):
            c=clamps['candidates'][e['clamp_candidate']];r=references['candidates'][e['reference_candidate']]
            scene.palm_T_tool=np.linalg.inv(np.array(c['tool_T_palm']));scene.reference_grasp=np.array(r['palm_matrix'])
            seed=canonical({**initial,**c['right_q'],**e['left_q']});base=make_base(x,y,yaw,seed)
            first=c['rows'][0];targets={'left':np.array(r['palm_matrix']),'right':np.array(first['right_palm'])}
            q,errors=solve(base,targets,seed);tested+=1
            if any(v['position_m']>1e-7 or v['angle_rad']>1e-6 for v in errors.values()):
                failures.append(dict(base=[x,y,yaw],extraction_candidate=ei,stage='initial_ik',errors=errors));continue
            scene.set_clamp(first['gap_m'],first['angle_rad'])
            failure=scene.check(base,q,tool_held=True,closure=1.,reference_held=True)
            if failure:
                failures.append(dict(base=[x,y,yaw],extraction_candidate=ei,stage='initial_collision',failure=failure,q=q));continue
            print('initial body fit',x,y,yaw,'extraction',ei,flush=True)
            path=[dict(stage='retract_clamp',gap_m=s['gap_m'],angle_rad=s['angle_rad'],left_palm=r['palm_matrix'],right_palm=s['right_palm']) for s in c['rows'] if s['phase']=='pull']
            path += [dict(stage=s['stage'],gap_m=c['rows'][-1]['gap_m'],angle_rad=c['rows'][-1]['angle_rad'],left_palm=s['left_palm'],right_palm=c['rows'][-1]['right_palm']) for s in e['rows']]
            rows=[];failure={}
            for row in path:
                targets={side:np.array(row[side+'_palm']) for side in ['left','right']}
                q,errors=solve(base,targets,q)
                if any(v['position_m']>1e-7 or v['angle_rad']>1e-6 for v in errors.values()):failure=dict(ik=errors)
                scene.set_clamp(row['gap_m'],row['angle_rad'])
                collision=scene.check(base,q,tool_held=True,closure=1.,reference_held=True)
                if collision:failure.update(collision)
                reference_collision=scene.reference_clearance()
                if reference_collision:failure['reference_environment']=reference_collision
                if failure:
                    failures.append(dict(base=[x,y,yaw],extraction_candidate=ei,stage=row['stage'],failure=failure,completed_states=len(rows),q=q));break
                rows.append({**row,'q':q,'root':base.tolist(),'errors':errors,
                    'reference_delta':scene.reference_delta.tolist()})
            if not failure:
                accepted.append(dict(extraction_candidate=ei,base=[x,y,yaw],rows=rows,
                    tool_T_palm=c['tool_T_palm'],reference_grasp=r['palm_matrix']))
                print('accepted full extraction',len(rows),'states',flush=True)
                if len(accepted)>=args.max_candidates:break
        if len(accepted)>=args.max_candidates:break
        if tested%20==0:print('tested',tested,'latest',failures[-1]['stage'],flush=True)
    report=dict(scope=__doc__,tested=tested,candidates=accepted,failures=failures,
        source_sha256=pins,extraction_source=args.extraction,
        geometry_sha256={ASSETS['g1']['geometry']:hashlib.sha256((ROOT/ASSETS['g1']['geometry']).read_bytes()).hexdigest(),**extraction['geometry_sha256']},
        seconds=time.monotonic()-started,
        limitations=['Starts at closed grasps; no hand approach or tool pickup.',
                     'Planning omits ankle meshes; independent interpolated source review remains required.',
                     'No grip forces, balance, dynamics, sensor policy or full measurement qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=tested,candidates=len(accepted),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
