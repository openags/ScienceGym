"""Inspect the official hand's palm/thumb interference across source limits.

Offline authoring diagnostic only. Uses original visual triangles, separately
from the source's simplified collision box. No collision filter is changed and
no execution or grasp credit is granted.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

import fcl
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'simulation/g1_cooling_demo/analysis/g1_dex3_comparison_01'
sys.path.insert(0, str(SOURCE))
from fit_cover_grasp import SourceHand, NAMES, digest


def run(output):
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    hand = SourceHand()
    pair = ['right_hand_palm_link', 'right_hand_thumb_1_link']
    rows = []
    for spread in np.linspace(-.9, .9, 13):
        for proximal in np.linspace(-1., .6, 17):
            q = [spread, proximal, -.4, .9, .6, .9, .6]
            poses = hand.forward(q, True)
            request = fcl.CollisionRequest(num_max_contacts=128, enable_contact=True)
            result = fcl.CollisionResult()
            fcl.collide(hand.manager._objs[pair[0]]['obj'],
                        hand.manager._objs[pair[1]]['obj'], request, result)
            distance = fcl.DistanceResult()
            if not result.is_collision:
                fcl.distance(hand.manager._objs[pair[0]]['obj'],
                             hand.manager._objs[pair[1]]['obj'],
                             fcl.DistanceRequest(enable_nearest_points=True), distance)
            contacts = sorted(result.contacts, key=lambda c: c.penetration_depth, reverse=True)
            rows.append(dict(q=dict(zip(NAMES, map(float, q))),
                             intersects=bool(result.is_collision),
                             clearance_m=None if result.is_collision else float(distance.min_distance),
                             maximum_reported_triangle_depth_m=max((float(c.penetration_depth) for c in contacts), default=0.),
                             deepest_points_wrist_m=[np.asarray(c.pos).tolist() for c in contacts[:4]]))
    report = dict(scope=__doc__, source_json_sha256=digest(SOURCE / 'source.json'),
                  source_model_sha256=digest(SOURCE / 'hand_inspection.xml'),
                  source_mesh_sha256={name: digest(SOURCE / 'meshes' / (name + '.STL')) for name in pair},
                  dependency_sha256=digest(SOURCE / 'fit_cover_grasp.py'),
                  builder_sha256=digest(__file__), rows=rows,
                  clear_configurations=sum(not r['intersects'] for r in rows),
                  tested=len(rows), qualified_grasp=False)
    (out / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['clear_configurations', 'tested', 'qualified_grasp']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    run(parser.parse_args().out)
