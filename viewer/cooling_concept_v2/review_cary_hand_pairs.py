"""Reject locally clear Cary grasps whose two actual hands intersect.

Inputs must describe the same installed reference, clamp and access state.
This is a necessary pair test only; reach, approach, force retention and
whole-body motion still require separate planning and review.
"""
import argparse
import hashlib
import itertools
import json
import numpy as np
from optical_choreography import HERE
from source_geometry import hand_manager, set_hand


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    files = [HERE/'previews'/f'cary_{name}_hand_{args.trial}.json' for name in ['reference', 'clamp']]
    sources = [json.loads(p.read_text()) for p in files]
    left, right = sources
    assert left['side'] == 'left' and right['side'] == 'right'
    for key in ['lid_opening_m', 'cover_matrix', 'geometry_sha256']:
        assert left[key] == right[key], key
    hands = [hand_manager(side) for side in ['left', 'right']]
    rows = []
    for i, a in enumerate(left['candidates']):
        set_hand(hands[0], 'left', a['q'], np.array(a['palm_matrix']))
        for j, b in enumerate(right['candidates']):
            set_hand(hands[1], 'right', b['q'], np.array(b['palm_matrix']))
            collision, parts = hands[0].in_collision_other(hands[1], return_names=True)
            rows.append(dict(reference_candidate=i, clamp_candidate=j,
                intersects=bool(collision), pairs=sorted([sorted(p) for p in parts]),
                clearance_m=float(hands[0].min_distance_other(hands[1])) if not collision else None))
    clear = sorted([r for r in rows if not r['intersects']], key=lambda r:-r['clearance_m'])
    report = dict(scope=__doc__, tested_pairs=len(rows), compatible_pairs=clear,
        incompatible_pairs=[r for r in rows if r['intersects']],
        inputs={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
                       for n in ['review_cary_hand_pairs.py', 'source_geometry.py']},
        whole_body_qualified=False, contact_force_qualified=False)
    path = HERE/'previews'/f'cary_hand_pairs_{args.trial}.json'
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(tested=len(rows), compatible=len(clear), best=clear[:3])), flush=True)


if __name__ == '__main__':
    main()
