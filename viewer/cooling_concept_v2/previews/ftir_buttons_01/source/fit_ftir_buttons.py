"""Fit source Inspire fingertips to the actual Nicolet acquisition buttons.

This local geometric search includes the terminal wrist and the closed
instrument. It plans contact approach, not electrical acquisition or force.
Whole-body reach and the composed workflow need separate checks.
"""
import argparse
import hashlib
import itertools
import json
import time
from collections import defaultdict

import fcl
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

from cary_distal_hand import distal_hand_manager
from source_geometry import ROOT, ASSETS, KIN, fk, robot_meshes, set_hand, hand_orientation

HERE = __import__('pathlib').Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    args = parser.parse_args()
    out = HERE / 'previews' / ('ftir_buttons_' + args.trial)
    out.mkdir(exist_ok=False)
    pins = {}
    for name in ['fit_ftir_buttons.py', 'cary_distal_hand.py', 'source_geometry.py', 'optical_setup.json']:
        data = (HERE / name).read_bytes()
        dest = out / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        pins[name] = hashlib.sha256(data).hexdigest()
    setup = json.loads((HERE / 'optical_setup.json').read_text())
    interface_path = ROOT / 'assets/nicolet_6700_v1/interfaces.json'
    interfaces = json.loads(interface_path.read_text())
    body = robot_meshes()
    hand = distal_hand_manager('right', body)
    obstacles = trimesh.collision.CollisionManager()
    for identity in ['nicolet', 'pike']:
        asset = ASSETS[identity]
        source = trimesh.load(ROOT / asset['geometry'], force='scene', process=False)
        base = np.eye(4)
        base[:3, 3] = asset['position_m']
        for name in source.graph.nodes_geometry:
            transform, key = source.graph[name]
            transform = np.array(setup['parts'].get(identity, {}).get(name, {}).get('matrix', np.eye(4))) @ transform
            obstacles.add_object(identity + '::' + name, source.geometry[key], base @ transform)
    placement = np.array(ASSETS['nicolet']['normalization_matrix'])
    placement[:3, 3] += ASSETS['nicolet']['position_m']
    buttons = []
    for info in interfaces['interfaces']:
        if info['id'] not in ['scan_0', 'scan_1', 'scan_2']:
            continue
        axis = placement[:3, :3] @ np.array(info['axis'])
        center = (placement @ np.r_[info['center_m'], 1.])[:3]
        buttons.append(dict(id=info['id'], label=info['label'], axis=axis,
                            surface=center - axis * .00075,
                            part='nicolet::scan_key_' + info['id'].split('_')[-1]))
    graph = defaultdict(list)
    for j in KIN['joints']:
        weight = int(j['type'] == 'revolute')
        graph[j['parent']].append((j['id'], weight))
        graph[j['id']].append((j['parent'], weight))
    adjacent = set()
    for link in hand._objs:
        stack = [(link, None, 0)]
        while stack:
            name, parent, depth = stack.pop()
            if depth > 1:
                continue
            if name in hand._objs:
                adjacent.add(tuple(sorted((link, name))))
            stack.extend((child, name, depth + w) for child, w in graph[name] if child != parent)
    accepted, rejected = [], []
    started = time.monotonic()
    for index, thumb, pitch, azimuth in itertools.product([0., .15, .3], [.2, .6, 1.],
                                                         [35., 50., 65., 80.], [-.35, 0., .35]):
        q = {f'right_{digit}_1_joint': 1.25 for digit in ['middle', 'ring', 'little']}
        q.update(right_index_1_joint=index, right_thumb_1_joint=1., right_thumb_2_joint=thumb)
        a = np.deg2rad(pitch)
        rotz = Rotation.from_euler('z', azimuth).as_matrix()
        orientation = hand_orientation('right', rotz @ [0., np.cos(a), -np.sin(a)],
                                       rotz @ [0., -np.sin(a), -np.cos(a)])
        world = fk(q)
        inverse = np.linalg.inv(world['right_palm_force_sensor'])
        vertices = np.vstack([trimesh.transform_points(mesh.vertices, inverse @ world[n])
                              for n, mesh in body.items() if n.startswith('right_index')])
        oriented = vertices @ orientation.T
        # Place the actual lowest source fingertip surface at the button face.
        normal = -buttons[0]['axis']
        heights = oriented @ normal
        tip = oriented[heights <= heights.min() + 1e-6].mean(axis=0)
        poses, failure = [], None
        for button in buttons:
            palm = np.eye(4)
            palm[:3, :3] = orientation
            palm[:3, 3] = button['surface'] - tip + normal * .00002
            distances = []
            for lift in np.linspace(.06, 0., 13):
                approach = palm.copy()
                approach[:3, 3] += normal * lift
                set_hand(hand, 'right', q, approach)
                hit, pairs = hand.in_collision_other(obstacles, return_names=True)
                if hit:
                    failure = dict(button=button['id'], lift_m=float(lift), environment=sorted(pairs))
                    break
                _, pairs = hand.in_collision_internal(return_names=True)
                bad = [p for p in pairs if tuple(sorted(p)) not in adjacent]
                if bad:
                    failure = dict(button=button['id'], self_intersections=sorted(bad))
                    break
            if failure:
                break
            target = obstacles._objs[button['part']]['obj']
            for n in hand._objs:
                if not n.startswith('right_index'):
                    continue
                result = fcl.DistanceResult()
                fcl.distance(hand._objs[n]['obj'], target,
                             fcl.DistanceRequest(enable_nearest_points=True), result)
                distances.append((float(result.min_distance), n))
            gap, closest = min(distances)
            if not 0. <= gap < .0001:
                failure = dict(button=button['id'], fingertip_gap_m=gap)
                break
            poses.append(dict(button=button['id'], label=button['label'], palm=palm.tolist(),
                              outward_normal=normal.tolist(), fingertip_gap_m=gap, closest_part=closest))
        parameters = dict(index=index, thumb=thumb, pitch_degrees=pitch, azimuth=azimuth)
        if failure:
            rejected.append(dict(parameters=parameters, failure=failure))
        else:
            accepted.append(dict(parameters=parameters, q=q, buttons=poses))
        if len(accepted) >= 12:
            break
    report = dict(scope=__doc__, passed=bool(accepted), candidates=accepted, failures=rejected,
                  seconds=time.monotonic()-started, source_sha256=pins,
                  geometry_sha256={n:ASSETS[n]['geometry_sha256'] for n in ['g1','nicolet','pike']},
                  interface_sha256=hashlib.sha256(interface_path.read_bytes()).hexdigest(),
                  limitations=['Local closed-instrument approach only; no whole-body reach yet.',
                               '20 micrometre target contact clearance is an authored contact tolerance.',
                               'Button travel, forces, acquisition and complete workflow are not validated.'])
    (out / 'fit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], candidates=len(accepted), rejected=len(rejected),
                          seconds=report['seconds'])), flush=True)


if __name__ == '__main__':
    main()
