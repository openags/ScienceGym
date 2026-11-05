"""Recheck source G1/Inspire hand seeds against the passive tool's real rest mesh.

Earlier movie poses are seeds only. Require collision-free source hand/wrist
geometry and opposed tactile-pad proximity on the outer tool arms. This local
geometric check does not establish support, closure force, pickup or arm reach.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

import fcl
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import KIN, fk, set_hand
from cary_distal_hand import distal_hand_manager


def run(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    seeds_path = ROOT/'viewer/cooling_concept_v2/previews/tweezers_right_fit.json'
    seeds = json.loads(seeds_path.read_text())['candidates']
    asset = trimesh.load(source/'rest_geometry.glb', force='scene', process=False)
    parts = defaultdict(list)
    for name in asset.graph.nodes_geometry:
        transform, key = asset.graph[name]
        mesh = asset.geometry[key].copy(); mesh.apply_transform(transform)
        group = 'positive' if name.startswith('positive_') else 'negative' if name.startswith('negative_') else 'heel'
        parts[group].append(mesh)
    tool = trimesh.collision.CollisionManager()
    for group, meshes in parts.items():
        tool.add_object(group, trimesh.util.concatenate(meshes))
    hand = distal_hand_manager('right')
    pads = [n for n in hand._objs if n in ['right_index_force_sensor_2', 'right_index_force_sensor_3',
                                          'right_thumb_force_sensor_3', 'right_thumb_force_sensor_4']]
    assert len(pads) == 4
    graph = defaultdict(list)
    for joint in KIN['joints']:
        weight = int(joint['type'] == 'revolute')
        graph[joint['parent']].append((joint['id'], weight))
        graph[joint['id']].append((joint['parent'], weight))
    adjacent = set()
    for link in hand._objs:
        pending = [(link, None, 0)]
        while pending:
            name, parent, depth = pending.pop()
            if depth > 1:
                continue
            if name in hand._objs:
                adjacent.add(tuple(sorted((link, name))))
            pending.extend((n, name, depth+w) for n,w in graph[name] if n != parent)
    contract = dict(scope=__doc__, seed_count=len(seeds),
                    tool_translation_from_legacy_frame_m=[.065,0,0],
                    translation_offsets_m=dict(x=[-.002,0,.002], y=[-.001,0,.001], z=[-.002,0,.002]),
                    minimum_pad_clearance_m=.00002, maximum_pad_clearance_m=.0005,
                    minimum_inward_normal_component=.7,
                    gripping_axial_interval_m=[.045,.110],
                    full_body_or_dynamics_checked=False,
                    source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [Path(__file__), source/'rest_geometry.glb', seeds_path,
                                             ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json',
                                             ROOT/'viewer/cooling_concept_v2/source_geometry.py',
                                             ROOT/'viewer/cooling_concept_v2/cary_distal_hand.py']},
                    kinematics_sha256=hashlib.sha256(json.dumps(KIN, sort_keys=True).encode()).hexdigest())
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    outcomes = defaultdict(int); accepted = []; nearest = []
    tested = 0
    for number, seed in enumerate(seeds):
        q = seed['q']
        palm = np.asarray(seed['palm_matrix']).copy()
        # Earlier asset had its tip at -65 mm; this asset has its tip at zero.
        palm[:3,3] += [.065,0,0]
        for dx,dy,dz in itertools.product([-.002,0,.002],[-.001,0,.001],[-.002,0,.002]):
            pose = palm.copy(); pose[:3,3] += [dx,dy,dz]
            set_hand(hand, 'right', q, pose);tested += 1
            _, pairs = hand.in_collision_internal(return_names=True)
            if any(tuple(sorted(pair)) not in adjacent for pair in pairs):
                outcomes['self_intersection'] += 1;continue
            if hand.in_collision_other(tool):
                outcomes['hand_tool_intersection'] += 1;continue
            contacts = []
            for pad in pads:
                for group, sign in [('negative',1),('positive',-1)]:
                    result = fcl.DistanceResult()
                    fcl.distance(hand._objs[pad]['obj'], tool._objs[group]['obj'],
                                 fcl.DistanceRequest(enable_nearest_points=True), result)
                    distance = float(result.min_distance)
                    p_hand, p_tool = map(np.asarray, result.nearest_points)
                    direction = (p_tool-p_hand)/max(distance,1e-12)
                    contacts.append(dict(pad=pad, arm=group, clearance_m=distance,
                                         inward_component=float(sign*direction[1]),
                                         tool_point_m=p_tool.tolist()))
            choices=[]
            for index, thumb in itertools.product([c for c in contacts if 'index' in c['pad']],
                                                  [c for c in contacts if 'thumb' in c['pad']]):
                if index['arm'] == thumb['arm']:
                    continue
                if min(index['clearance_m'], thumb['clearance_m']) <= .00002:
                    continue
                if min(index['inward_component'], thumb['inward_component']) < .7:
                    continue
                if not all(.045 <= c['tool_point_m'][0] <= .110 for c in [index, thumb]):
                    continue
                choices.append([index,thumb])
            if not choices:
                outcomes['no_opposed_outer_pad_pair'] += 1;continue
            choice = min(choices, key=lambda pair:max(c['clearance_m'] for c in pair))
            record = dict(seed=number, q=q, source_tool_from_palm=pose.tolist(), contacts=choice,
                          maximum_pad_clearance_m=max(c['clearance_m'] for c in choice))
            nearest.append(record)
            if record['maximum_pad_clearance_m'] <= .0005:
                accepted.append(record);outcomes['candidate'] += 1
            else:
                outcomes['pads_too_far'] += 1
    nearest.sort(key=lambda r:r['maximum_pad_clearance_m'])
    accepted.sort(key=lambda r:r['maximum_pad_clearance_m'])
    result = dict(passed_local_pad_geometry=bool(accepted), candidates=accepted,
                  nearest_candidates=nearest[:20], rejection_counts=dict(outcomes), tested=tested,
                  seconds=time.monotonic()-started, qualified_robot_grasp=False,
                  contract_sha256=hashlib.sha256((output/'contract.json').read_bytes()).hexdigest(),
                  scope=__doc__)
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['candidates','nearest_candidates']}), flush=True)
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args()
    run(a.source,a.output)
