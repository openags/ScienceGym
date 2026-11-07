"""Return from supported hood storage to the further-opening stance."""
import argparse
import hashlib
import json
import numpy as np
from cary_access_scene import CaryAccessScene
from cary_grounded_steps import translation_steps
from optical_choreography import HERE


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',default='01')
    parser.add_argument('--extension',default='previews/cary_lid_stepped_04/plan.json')
    args=parser.parse_args()
    out=HERE/'previews'/('cary_return_'+args.trial);out.mkdir(exist_ok=False)
    inputs=['plan_cary_return.py','cary_access_scene.py','cary_grounded_steps.py',
        'optical_choreography.py','source_geometry.py','cary_access_episode.json',args.extension]
    pins={}
    for name in inputs:
        data=(HERE/name).read_bytes();dest=out/'source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        pins[name]=hashlib.sha256(data).hexdigest()
    source=json.loads((HERE/'cary_access_episode.json').read_text())
    assert source['segments'][-1]['id']=='hood_return_hand'
    start=source['segments'][-1]['rows'][-1]
    end=json.loads((HERE/args.extension).read_text())['rows'][0]
    assert max(abs(start['q'][n]-end['q'][n]) for n in start['q'])<1e-7
    scene=CaryAccessScene(cover_candidate=True)
    scene.set_access(lid=.15,cover=start['cover_matrix'])
    rows=translation_steps(start['root'],end['root'],start['q'])
    for row in rows:
        row.update(lid_m=.15,cover_matrix=start['cover_matrix'])
        row['failure']=scene.check(np.array(row['root']),row['q'])
    failures=[r for r in rows if r['failure']]
    report=dict(scope=__doc__,passed_planning_geometry=not failures,rows=rows,
        source_sha256=pins,extension_source=args.extension,
        limitations=['Source geometry and planted-foot kinematics only; no balance or dynamics qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=not failures,states=len(rows),first_failure=failures[:1])),flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
