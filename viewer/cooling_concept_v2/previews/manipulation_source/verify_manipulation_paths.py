"""Check all free-hand joint states, including inactive-hand relaxation.

The source cover choreography relaxes the left fingers while its right hand
approaches. Complete this endpoint condition continuously, recheck the exact
mesh path, then expand generalized finger variables into actual source joints.
These local path checks do not replace full-film review.
"""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from plan_manipulation_approaches import HERE,Geometry,Space
from source_geometry import KIN


def main():
    packet=json.loads((HERE/'previews/manipulation_approach_inputs.json').read_text())
    geometry=Geometry();output=HERE/'previews/verified_manipulation_paths';output.mkdir(exist_ok=True)
    independent=[j['name'] for j in KIN['joints'] if j['type']=='revolute' and not j.get('mimic')]
    for name,source in packet['frames'].items():
        candidates=[HERE/'previews'/folder/(name+'.json') for folder in ['manipulation_paths','reused_manipulation_paths']]
        records=[(f,json.loads(f.read_text())) for f in candidates if f.exists()]
        records=[(f,r) for f,r in records if r.get('passed')]
        if not records:continue
        file,record=records[0];source_hash=hashlib.sha256(file.read_bytes()).hexdigest();dest=output/(name+'.json')
        if dest.exists() and json.loads(dest.read_text()).get('source_plan_sha256')==source_hash:continue
        assert record['source_sha256']==packet['source_sha256']
        assert record['input_sha256']==hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
        space=Space(source,packet['extraGeometry'],geometry);base_converter=space.values_to_q
        def complete(values):
            q=base_converter(values)
            if source['kind']=='lid':
                amount=q['right_middle_1_joint']/source['target']['joints']['right_middle_1_joint']
                for finger in ['index','middle','ring','little']:
                    key='left_'+finger+'_1_joint';a=source['start']['joints'].get(key,0);b=source['target']['joints'].get(key,0)
                    q[key]=a+(b-a)*amount
            return q
        space.values_to_q=complete;knots=np.array(record['knots']);began=time.monotonic()
        assert record['joints']==space.names
        endpoint_error=max(abs(complete(v).get(n,0)-expected['joints'].get(n,0)) for v,expected in [(knots[0],source['start']),(knots[-1],source['target'])] for n in independent)
        passed=endpoint_error<1e-8 and space.free(knots[0]) and all(space.edge(a,b) for a,b in zip(knots,knots[1:]))
        full=[complete(v) for v in knots]
        names=[n for n in independent if any(abs(q.get(n,0)-source['start']['joints'].get(n,0))>1e-10 for q in full)]
        result=dict(name=name,passed=passed,scope=__doc__,source_sha256=packet['source_sha256'],input_sha256=record['input_sha256'],
                    source_plan_sha256=source_hash,source_plan=str(file.relative_to(HERE)),
                    verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    geometry_checker_sha256=hashlib.sha256((HERE/'plan_manipulation_approaches.py').read_bytes()).hexdigest(),
                    joints=names,knots=[[q.get(n,0) for n in names] for q in full],generalized_finger_joint={},
                    endpoint_maximum_joint_error_rad=endpoint_error,collision_queries=space.calls,seconds=time.monotonic()-began)
        if not passed:result['rejection']=getattr(space,'last_rejection','endpoint mismatch')
        dest.write_text(json.dumps(result,indent=2)+'\n')
        print(name,passed,'endpoint_error',endpoint_error,'queries',space.calls,flush=True)


if __name__=='__main__':main()
