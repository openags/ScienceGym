"""Review reference grasp and cap contact segments before film integration.

The transfer between the carrying step and cap preplacement is excluded here;
it has a separate held-object path planner. This is sampled source geometry,
without forces, animated sidestep legs or whole-laboratory acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
from plan_reference_storage import HERE, review


def main():
    parser=argparse.ArgumentParser();parser.add_argument('solved');args=parser.parse_args()
    source=Path(args.solved);data=json.loads(source.read_text())
    stages=['lower_open_hand','close_reference_grip','lift_reference','proposed_carrying_step','seat_reference_in_cap','release_reference','withdraw_open_hand']
    rows=[r for r in data['rows'] if r['stage'] in stages]
    files=['review_reference_contacts.py','plan_reference_storage.py','source_geometry.py','optical_setup.json','build_reference_cap_candidate.py']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files}
    checks=review(rows,json.loads((HERE/'optical_setup.json').read_text()),data['final_offset'],data['cap_floor_m'])
    counts={s:{n:sum(bool(c[n]) for c in checks if c['stage']==s) for n in ['self_intersections','environment','reference_hand','reference_environment']} for s in stages}
    maximum_position_error=max(r['error'] for r in rows);maximum_rotation_error=max(r['rotationError'] for r in rows)
    result=dict(scope=__doc__,endpoint_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_sha256=pins,cap_floor_m=data['cap_floor_m'],rows=rows,checks=checks,counts=counts,
                maximum_position_error_m=maximum_position_error,maximum_rotation_error_rad=maximum_rotation_error,
                passed=not any(any(c.values()) for c in counts.values()) and maximum_position_error<.003 and maximum_rotation_error<.02)
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items())
    out=HERE/'previews/reference_contact_review.json'
    if out.exists():out.rename(out.with_name('reference_contact_review_'+hashlib.sha256(out.read_bytes()).hexdigest()[:12]+'.json'))
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['passed','counts','maximum_position_error_m','maximum_rotation_error_rad']}),flush=True)


if __name__=='__main__':main()
