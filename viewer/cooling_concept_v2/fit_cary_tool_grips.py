"""Check alternate source-hand grips of the existing closed ordinary tweezers."""
import hashlib
import json
import fcl
import numpy as np
import trimesh
from scipy.optimize import least_squares
from optical_choreography import HERE, JOINTS
from source_geometry import hand_manager, set_hand
from tweezers_geometry import meshes


def main():
    source = HERE/'previews/tweezers_right_fit.json'
    output = HERE/'previews/cary_tool_grips_01.json'
    if output.exists():
        raise FileExistsError(output)
    search = json.loads(source.read_text())
    hand = hand_manager('right')
    tool = trimesh.collision.CollisionManager()
    for name, mesh in meshes(1.).items():
        tool.add_object(name, mesh)
    names = ['right_index_1_joint', 'right_thumb_2_joint']
    bounds = np.array([[JOINTS[n]['limits']['lower'], JOINTS[n]['limits']['upper']] for n in names])
    rows = []
    for i, c in enumerate(search['candidates']):
        if abs(c['index_contact'][2][0]-c['thumb_contact'][2][0]) > .02:
            continue
        palm = np.array(c['palm_matrix'])
        q = dict(c['q'])
        def residual(values):
            q.update(dict(zip(names, values)))
            set_hand(hand, 'right', q, palm)
            gaps = []
            for contact in [c['index_contact'], c['thumb_contact']]:
                distance = fcl.DistanceResult()
                fcl.distance(hand._objs[contact[3]]['obj'], tool._objs[contact[1]]['obj'],
                             fcl.DistanceRequest(), distance)
                gaps.append(float(distance.min_distance))
            return np.array(gaps)-.000125
        initial = np.clip([q[n] for n in names], bounds[:, 0]+1e-8, bounds[:, 1]-1e-8)
        result = least_squares(residual, initial, bounds=(bounds[:, 0], bounds[:, 1]),
            diff_step=1e-4, max_nfev=100, ftol=1e-12, xtol=1e-12, gtol=1e-12)
        gaps = residual(result.x)+.000125
        collision, pairs = hand.in_collision_other(tool, return_names=True)
        accepted = not collision and min(gaps)>1e-6 and max(gaps)<.00025
        row = dict(source_candidate=i, q={k:float(v) for k, v in q.items()},
            palm_matrix=palm.tolist(), gaps_m=gaps.tolist(), accepted=bool(accepted),
            intersections=sorted([sorted(p) for p in pairs]))
        rows.append(row)
        print(i, 'accepted', bool(accepted), 'gaps', gaps, flush=True)
    report = dict(scope=__doc__, closure=1., candidates=rows,
        source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
                       for n in ['fit_cary_tool_grips.py', 'source_geometry.py', 'tweezers_geometry.py']},
        input_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    output.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
