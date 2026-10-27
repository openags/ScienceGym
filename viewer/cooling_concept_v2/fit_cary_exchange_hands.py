"""Search actual Inspire hand meshes at the installed Cary reference/clamp.

Both the 150 mm lid opening and the removed hood retain their reviewed
positions. This is a local grasp search, not a body trajectory or force test.
No reference is removed or declared supported by this geometric probe.
"""
import argparse
import hashlib
import itertools
import json
import time
import fcl
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene, CANDIDATE
from optical_choreography import HERE
from source_geometry import ROOT, ASSETS, fk, hand_manager, set_hand


def nearest(hand, target, finger):
    result = []
    for name in hand._objs:
        if finger not in name:
            continue
        distance = fcl.DistanceResult()
        fcl.distance(hand._objs[name]['obj'], target,
                     fcl.DistanceRequest(enable_nearest_points=True), distance)
        result.append((name, float(distance.min_distance),
                       np.array(distance.nearest_points[1])))
    return min(result, key=lambda row: row[1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['reference', 'clamp'], required=True)
    parser.add_argument('--trial', default='01')
    parser.add_argument('--tilts', nargs='+', type=float, default=[-.45, 0., .45])
    parser.add_argument('--biases', nargs='+', type=float, default=[-.003, 0., .003])
    args = parser.parse_args()
    output = HERE/'previews'/f'cary_{args.target}_hand_{args.trial}.json'
    if output.exists():
        raise FileExistsError(output)
    snapshot = output.with_suffix('')
    snapshot.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name in ['fit_cary_exchange_hands.py', 'cary_clamp_scene.py', 'cary_clamp.py',
                 'cary_access_scene.py', 'source_geometry.py', 'optical_setup.json',
                 'previews/cary_cover_carry_03.json']:
        data = (HERE/name).read_bytes()
        dest = snapshot/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        sources[name] = hashlib.sha256(data).hexdigest()
    started = time.monotonic()
    scene = CaryClampScene(local_only=True)
    cover = json.loads((HERE/'previews/cary_cover_carry_03.json').read_text())['rows'][-1]['cover_matrix']
    scene.set_access(lid=.15, cover=cover)
    side = 'left' if args.target == 'reference' else 'right'
    hand = hand_manager(side)
    obstacles = scene.local_obstacles()
    part = 'large_reference_holder' if args.target == 'reference' else 'sample_clamp_slider'
    target = obstacles._objs['dra::'+part]['obj']
    if args.target == 'reference':
        mesh = scene.reference_meshes[part].copy()
        mesh.apply_transform(scene.reference_rest[part])
        center = mesh.bounds.mean(axis=0)
        index_values = np.linspace(.05, .85, 9)
        thumb_values = np.linspace(.05, .65, 9)
    else:
        center = trimesh.transform_points(np.array([[.039, -.130, .084]]),
                                          scene.clamp_poses[part])[0]
        index_values = np.linspace(.45, 1.05, 9)
        thumb_values = np.linspace(.05, .65, 9)
    tested, candidates = 0, []
    for index, thumb in itertools.product(index_values, thumb_values):
        q = {f'{side}_{f}_1_joint': 1.1 for f in ['middle', 'ring', 'little']}
        q.update({f'{side}_index_1_joint': float(index),
                  f'{side}_thumb_1_joint': 1.1641,
                  f'{side}_thumb_2_joint': float(thumb)})
        world = fk(q)
        inverse = np.linalg.inv(world[side+'_palm_force_sensor'])
        finger = (inverse @ world[side+'_index_force_sensor_3'])[:3, 3]
        thumb_tip = (inverse @ world[side+'_thumb_force_sensor_4'])[:3, 3]
        middle = (finger+thumb_tip)/2
        gap = thumb_tip-finger
        gap /= np.linalg.norm(gap)
        forward = middle-gap*(middle@gap)
        forward /= np.linalg.norm(forward)
        local = np.column_stack([gap, forward, np.cross(gap, forward)])
        for theta, tilt, bias in itertools.product(np.arange(12)*np.pi/6, args.tilts, args.biases):
            normal = np.array([np.cos(theta), 0., np.sin(theta)])
            direction = np.array([-np.sin(theta)*np.sin(tilt), np.cos(tilt),
                                  np.cos(theta)*np.sin(tilt)])
            rotation = np.column_stack([normal, direction, np.cross(normal, direction)]) @ local.T
            palm = np.eye(4)
            palm[:3, :3] = rotation
            palm[:3, 3] = center + [0, bias, 0] - rotation @ middle
            set_hand(hand, side, q, palm)
            tested += 1
            if hand.in_collision_other(obstacles):
                continue
            _, pairs = hand.in_collision_internal(return_names=True)
            if any('thumb' in a and any(f in b for f in ['index', 'middle', 'ring', 'little']) or
                   'thumb' in b and any(f in a for f in ['index', 'middle', 'ring', 'little']) for a, b in pairs):
                continue
            a, b = nearest(hand, target, 'index'), nearest(hand, target, 'thumb')
            if max(a[1], b[1]) > .003:
                continue
            av, bv = (a[2]-center)[[0, 2]], (b[2]-center)[[0, 2]]
            dot = float(av@bv/max(1e-12, np.linalg.norm(av)*np.linalg.norm(bv)))
            if dot > -.5:
                continue
            candidates.append(dict(q=q, palm_matrix=palm.tolist(), finger_gap_m=a[1],
                thumb_gap_m=b[1], finger_part=a[0], thumb_part=b[0],
                contacts=[a[2].tolist(), b[2].tolist()], opposition_dot=dot,
                theta_rad=float(theta), tilt_rad=float(tilt), bias_y_m=float(bias)))
        if tested % 972 == 0:
            print(args.target, tested, 'candidates', len(candidates), flush=True)
    candidates.sort(key=lambda c: max(c['finger_gap_m'], c['thumb_gap_m']))
    report = dict(scope=__doc__, target=args.target, side=side, target_part=part,
        tilts_rad=args.tilts, biases_y_m=args.biases,
        center_m=center.tolist(), lid_opening_m=.15, cover_matrix=cover,
        tested=tested, candidates=candidates, seconds=time.monotonic()-started,
        source_snapshot=str(snapshot.relative_to(HERE)), source_sha256=sources,
        geometry_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
                        for path in [CANDIDATE, scene.cary_geometry, ASSETS['g1']['geometry']]})
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(target=args.target, tested=tested, candidates=len(candidates),
                          best=candidates[:1], seconds=report['seconds'])), flush=True)


if __name__ == '__main__':
    main()
