"""Tighten left-hand reference grasps without touching the PTFE optical face."""
import argparse
import hashlib
import json
import numpy as np
from scipy.optimize import minimize
from cary_clamp_scene import CaryClampScene
from fit_cary_exchange_hands import nearest
from optical_choreography import HERE
from source_geometry import hand_manager, set_hand


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    output = HERE/'previews'/f'cary_reference_refined_{args.trial}'
    output.mkdir(exist_ok=False)
    names = ['refine_cary_reference_grasp.py', 'fit_cary_exchange_hands.py',
             'cary_clamp_scene.py', 'source_geometry.py', 'previews/cary_reference_hand_02.json']
    sources = {}
    for name in names:
        data = (HERE/name).read_bytes()
        dest = output/'source'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        sources[name] = hashlib.sha256(data).hexdigest()
    scene = CaryClampScene(local_only=True)
    cover = json.loads((HERE/'previews/cary_cover_carry_03.json').read_text())['rows'][-1]['cover_matrix']
    scene.set_access(lid=.20, cover=cover)
    obstacles = scene.local_obstacles()
    target = obstacles._objs['dra::large_reference_holder']['obj']
    source = json.loads((HERE/names[-1]).read_text())
    hand = hand_manager('left')
    results = []
    for number, c in enumerate(source['candidates']):
        initial = np.array([c['q']['left_index_1_joint'], c['q']['left_thumb_2_joint'], 0., 0., 0.])
        bounds = [(initial[0]-.06, initial[0]+.06), (initial[1]-.06, initial[1]+.06),
                  (-.0015, .0015), (-.0015, .0015), (-.0015, .0015)]
        def evaluate(values):
            q = {**c['q'], 'left_index_1_joint':float(values[0]), 'left_thumb_2_joint':float(values[1])}
            palm = np.array(c['palm_matrix'])
            palm[:3, 3] += values[2:]
            set_hand(hand, 'left', q, palm)
            if hand.in_collision_other(obstacles):
                return 1e6, None
            _, pairs = hand.in_collision_internal(return_names=True)
            if any('thumb' in a and any(f in b for f in ['index', 'middle', 'ring', 'little']) or
                   'thumb' in b and any(f in a for f in ['index', 'middle', 'ring', 'little']) for a, b in pairs):
                return 1e6, None
            a, b = nearest(hand, target, 'index'), nearest(hand, target, 'thumb')
            score = 1e6*((a[1]-.000125)**2+(b[1]-.000125)**2)
            return score, dict(source_candidate=number, q=q, palm_matrix=palm.tolist(),
                finger_gap_m=a[1], thumb_gap_m=b[1], finger_part=a[0], thumb_part=b[0],
                contacts=[a[2].tolist(), b[2].tolist()])
        fit = minimize(lambda v:evaluate(v)[0], initial, method='Powell', bounds=bounds,
                       options={'xtol':1e-8, 'ftol':1e-10, 'maxiter':50})
        choices = [evaluate(initial), evaluate(fit.x)]
        score, row = min(choices, key=lambda v:v[0])
        if row is not None:
            row['queries'] = int(fit.nfev)
            row['accepted_clearance'] = min(row['finger_gap_m'], row['thumb_gap_m'])>1e-6 and max(row['finger_gap_m'], row['thumb_gap_m'])<=.00025
            results.append(row)
            print(number, 'gaps', row['finger_gap_m'], row['thumb_gap_m'], 'accepted', row['accepted_clearance'], flush=True)
    report = dict(scope=__doc__, candidates=results, source_sha256=sources,
        accepted=sum(r['accepted_clearance'] for r in results), lid_opening_m=.20,
        limitations=['No body reach, approach/closure or force retention qualification.'])
    (output/'grasps.json').write_text(json.dumps(report, indent=2)+'\n')
    print('accepted', report['accepted'], flush=True)


if __name__ == '__main__':
    main()
