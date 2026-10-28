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
    parser.add_argument('--aisle-y',type=float,default=7.65)
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
    initial=np.array(start['root']);goal=np.array(end['root'])
    aisle_start=initial.copy();aisle_start[1,3]=args.aisle_y
    aisle_end=goal.copy();aisle_end[1,3]=args.aisle_y
    rows=[];clock=0.
    for a,b in zip([initial,aisle_start,aisle_end],[aisle_start,aisle_end,goal]):
        leg=translation_steps(a,b,start['q'])
        for row in leg:
            row['time_s']+=clock
            if rows and abs(row['time_s']-rows[-1]['time_s'])<1e-8:continue
            rows.append(row)
        clock=rows[-1]['time_s']
    for row in rows:
        row.update(lid_m=.15,cover_matrix=start['cover_matrix'])
        row['failure']=scene.check(np.array(row['root']),row['q'])
    failures=[r for r in rows if r['failure']]
    report=dict(scope=__doc__,passed_planning_geometry=not failures,rows=rows,
        source_sha256=pins,extension_source=args.extension,aisle_y_m=args.aisle_y,
        limitations=['Source geometry and planted-foot kinematics only; no balance or dynamics qualification.'])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=not failures,states=len(rows),failure_count=len(failures),
        first_failure=failures[0]['failure'] if failures else None)),flush=True)
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
