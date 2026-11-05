"""Author source-hand grasps from finger opposition, independently of film poses.

The first search uses source tactile surfaces and source joint/mimic kinematics.
It fits the actual arm spacing before placing the tool-relative palm. Every
candidate is then checked against the complete source hand, wrist, free tray
and support plane. This is offline geometry only, never a grasp qualification
or an actor observation. Failed searches and all accepted alternatives remain.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import time

import fcl
import numpy as np
import trimesh
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import KIN, ASSETS, fk, set_hand, robot_meshes
from cary_distal_hand import distal_hand_manager
from support_geometry import load_support


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, support, output):
    source, support, output = [Path(p).resolve() for p in (source, support, output)]
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output/'source_snapshot'; snapshot.mkdir()
    for path in [Path(__file__), Path(__file__).with_name('support_geometry.py'),
                 ROOT/'viewer/cooling_concept_v2/source_geometry.py',
                 ROOT/'viewer/cooling_concept_v2/cary_distal_hand.py']:
        shutil.copyfile(path, snapshot/path.name)
    initial, world_from_source, obstacles, receipt = load_support(support, ROOT)
    (output/'support_geometry.json').write_text(json.dumps(receipt, indent=2)+'\n')
    geometry = source/'rest_geometry.glb'
    scene = trimesh.load(geometry, force='scene', process=False)
    parts = defaultdict(list)
    for name in scene.graph.nodes_geometry:
        transform, key = scene.graph[name]
        mesh = scene.geometry[key].copy(); mesh.apply_transform(transform)
        group = 'positive' if name.startswith('positive_') else 'negative' if name.startswith('negative_') else 'heel'
        parts[group].append(mesh)
    tool_meshes = {name: trimesh.util.concatenate(p) for name, p in parts.items()}
    tool = trimesh.collision.CollisionManager()
    for name, mesh in tool_meshes.items(): tool.add_object(name, mesh)
    meshes = robot_meshes()
    hand = distal_hand_manager('right', meshes)
    hulls = {name: meshes[name].convex_hull for name in hand._objs}
    proxies = trimesh.collision.CollisionManager()
    for name, mesh in hulls.items(): proxies.add_object(name, mesh)
    drivers = ['right_index_1_joint', 'right_thumb_1_joint', 'right_thumb_2_joint']
    limits = {j['name']: j['limits'] for j in KIN['joints'] if j['name'] in drivers}
    lower = np.array([limits[n]['lower'] for n in drivers])
    upper = np.array([limits[n]['upper'] for n in drivers])
    local_joints = []
    found = {'right_base_link'}
    for j in KIN['joints']:
        if j['parent'] in found:
            local_joints.append((j, np.asarray(j['origin_matrix']), np.asarray(j['axis'])))
            found.add(j['id'])

    def hand_fk(q):
        values = dict(zip(drivers, q)); transforms = {'right_base_link': np.eye(4)}
        for j, origin, axis in local_joints:
            if j['mimic']:
                m = j['mimic']; values[j['name']] = float(m.get('offset', 0))+float(m.get('multiplier', 1))*values.get(m['joint'], 0)
            angle = values.get(j['name'], 0)
            t = origin.copy()
            if angle: t[:3, :3] = t[:3, :3]@Rotation.from_rotvec(axis*angle).as_matrix()
            transforms[j['id']] = transforms[j['parent']]@t
        inverse = np.linalg.inv(transforms['right_palm_force_sensor'])
        return {name: inverse@t for name, t in transforms.items()}

    # Verify the optimized kinematic path against the existing source FK,
    # including all fingertip mimic joints, before using it for authoring.
    fk_error = 0.
    for q in [lower, upper, (lower+upper)/2]:
        a = hand_fk(q); b = fk(dict(zip(drivers, q)))
        inv = np.linalg.inv(b['right_palm_force_sensor'])
        fk_error = max(fk_error, max(float(np.max(abs(t-inv@b[n]))) for n, t in a.items()))
    assert fk_error < 1e-12
    pads = ['right_index_force_sensor_2', 'right_index_force_sensor_3',
            'right_thumb_force_sensor_3', 'right_thumb_force_sensor_4']
    features = {}
    for name in pads:
        points, _, faces = trimesh.proximity.closest_point(meshes[name], [[0, 0, .01]])
        features[name] = (points[0], meshes[name].face_normals[faces[0]])

    def intrinsic(q, pair):
        transforms = hand_fk(q); positions = []; normals = []; velocities = []
        for name, driver in zip(pair, [0, 2]):
            point, normal = features[name]; tf = transforms[name]
            position = tf[:3, :3]@point+tf[:3, 3]
            shifted = np.asarray(q).copy(); shifted[driver] += 1e-5
            after = hand_fk(shifted)[name]
            v = (after[:3, :3]@point+after[:3, 3]-position)/1e-5
            positions.append(position); normals.append(tf[:3, :3]@normal)
            velocities.append(v/max(np.linalg.norm(v), 1e-12))
        delta = positions[1]-positions[0]; distance = np.linalg.norm(delta)
        direction = delta/max(distance, 1e-12)
        return positions, distance, direction, [float(normals[0]@direction), float(-normals[1]@direction)], [float(velocities[0]@direction), float(-velocities[1]@direction)]

    graph = defaultdict(list)
    for j in KIN['joints']:
        w = int(j['type'] == 'revolute')
        graph[j['parent']].append((j['id'], w)); graph[j['id']].append((j['parent'], w))
    adjacent = set()
    for name in hand._objs:
        queue = [(name, None, 0)]
        while queue:
            link, parent, depth = queue.pop()
            if depth > 1: continue
            adjacent.add(tuple(sorted([name, link])))
            queue.extend((n, link, depth+w) for n, w in graph[link] if n != parent)
    contract = dict(scope=__doc__, support_review=str(support.relative_to(ROOT)),
        support_review_sha256=sha(support), support_geometry_sha256=sha(output/'support_geometry.json'),
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in [geometry, *snapshot.iterdir(), ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json']},
        source_visual_geometry_sha256=sha(ROOT/ASSETS['g1']['geometry']),
        kinematics_sha256=hashlib.sha256(json.dumps(KIN, sort_keys=True).encode()).hexdigest(),
        source_fk_maximum_error=fk_error, driver_limits=limits,
        surface_features={n: dict(point=p.tolist(), normal=v.tolist()) for n, (p, v) in features.items()},
        contact_pairs=list(itertools.product(pads[:2], pads[2:])),
        axial_targets_m=[.055, .075, .095], target_height_m=.00575,
        joint_seed_fractions=[.15, .5, .85], palm_roll_count=32,
        nonacting_finger_angles_rad=[0., .5, 1.1], initial_surface_gap_m=.0003,
        minimum_pad_clearance_m=.00002, maximum_pad_clearance_m=.0005,
        minimum_inward_normal_component=.7, minimum_inward_closure_velocity_component=.8,
        maximum_contact_axial_offset_m=.002, maximum_contact_height_offset_m=.002,
        minimum_support_clearance_m=.001, intrinsic_width_error_limit_m=.00015,
        intrinsic_solve_maximum_evaluations=120,
        full_body_or_dynamics_checked=False)
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    started = time.monotonic(); solves = []; selected = []
    for pair, axial in itertools.product(contract['contact_pairs'], contract['axial_targets_m']):
        surfaces = []
        for side, sign in [('negative', -1), ('positive', 1)]:
            point, _, _ = trimesh.proximity.closest_point(tool_meshes[side], [[axial, sign*.05, .00575]])
            surfaces.append(point[0]+[0, sign*.0003, 0])
        target_delta = surfaces[1]-surfaces[0]
        width = float(np.linalg.norm(target_delta))

        def residual(q):
            _, distance, _, normals, velocities = intrinsic(q, pair)
            return [(distance-width)/.001, *[min(0., n-.82)*8 for n in normals],
                    *[min(0., v-.9)*8 for v in velocities]]

        distinct = []
        for fractions in itertools.product(contract['joint_seed_fractions'], repeat=3):
            seed = lower+(upper-lower)*fractions
            solution = least_squares(residual, seed, bounds=(lower, upper), max_nfev=120,
                                     diff_step=1e-5, ftol=1e-7, xtol=1e-7, gtol=1e-7)
            points, distance, direction, normals, velocities = intrinsic(solution.x, pair)
            checks = dict(width=bool(abs(distance-width) <= .00015),
                          normals=min(normals) >= .7, velocities=min(velocities) >= .8)
            record = dict(pair=pair, axial_m=axial, q=dict(zip(drivers, solution.x.tolist())),
                target_width_m=width, actual_width_m=float(distance), normal_components=normals,
                velocity_components=velocities, checks=checks, cost=float(solution.cost),
                evaluations=int(solution.nfev), seed_fraction=fractions)
            solves.append(record)
            if all(checks.values()) and all(np.linalg.norm(solution.x-p) > .015 for p in distinct):
                distinct.append(solution.x)
                selected.append((record, points, direction, surfaces))
        (output/'intrinsic_trials.json').write_text(json.dumps(solves, indent=2)+'\n')
        print(json.dumps(dict(stage='intrinsic', pair=pair, axial=axial, accepted_distinct=len(distinct),
                              trials=len(solves), seconds=time.monotonic()-started)), flush=True)

    trials = []; accepted = []; rejected = Counter()
    for candidate, points, direction, surfaces in selected:
        q = candidate['q'].copy(); mid = (points[0]+points[1])/2
        target = (surfaces[0]+surfaces[1])/2
        x0 = np.cross(direction, [0, 0, 1])
        if np.linalg.norm(x0) < .1: x0 = np.cross(direction, [1, 0, 0])
        x0 /= np.linalg.norm(x0); z0 = np.cross(x0, direction)
        for roll, other in itertools.product(np.linspace(0, 2*np.pi, 32, endpoint=False), [0., .5, 1.1]):
            x = np.cos(roll)*x0+np.sin(roll)*z0; z = np.cross(x, direction)
            palm = np.eye(4); palm[:3, :3] = np.stack([x, direction, z]); palm[:3, 3] = target-palm[:3, :3]@mid
            q.update({f'right_{finger}_1_joint': other for finger in ['middle', 'ring', 'little']})
            world = fk(q); inv = palm@np.linalg.inv(world['right_palm_force_sensor'])
            transforms = {n: inv@world[n] for n in hand._objs}
            clearance = min(float((hulls[n].vertices@(world_from_source@tf)[2, :3]+(world_from_source@tf)[2, 3]).min())
                            for n, tf in transforms.items())
            if clearance < .001: rejected['plane_clearance'] += 1; continue
            for n, tf in transforms.items(): proxies.set_transform(n, tf)
            if obstacles and (proxies.in_collision_other(obstacles) or proxies.min_distance_other(obstacles) < .001):
                rejected['conservative_tray_clearance'] += 1; continue
            for n, tf in transforms.items(): hand.set_transform(n, tf)
            _, tool_pairs = hand.in_collision_other(tool, return_names=True)
            if tool_pairs: rejected['source_hand_tool_intersection'] += 1; continue
            _, self_pairs = hand.in_collision_internal(return_names=True)
            self_pairs = [sorted(p) for p in self_pairs if tuple(sorted(p)) not in adjacent]
            if self_pairs: rejected['source_hand_self_intersection'] += 1; continue
            obstacle_clearance = None
            if obstacles:
                if hand.in_collision_other(obstacles): rejected['source_hand_tray_intersection'] += 1; continue
                obstacle_clearance = float(hand.min_distance_other(obstacles))
                if obstacle_clearance < .001: rejected['source_hand_tray_clearance'] += 1; continue
            contacts = []
            for name, side, sign, driver in zip(candidate['pair'], ['negative', 'positive'], [1., -1.], [drivers[0], drivers[2]]):
                result = fcl.DistanceResult()
                fcl.distance(hand._objs[name]['obj'], tool._objs[side]['obj'], fcl.DistanceRequest(enable_nearest_points=True), result)
                gap = float(result.min_distance); a, b = map(np.asarray, result.nearest_points)
                tf = transforms[name]; point = tf[:3, :3].T@(a-tf[:3, 3])
                shifted = dict(q); shifted[driver] += 1e-5
                after = fk(shifted); after = palm@np.linalg.inv(after['right_palm_force_sensor'])@after[name]
                v = (after[:3, :3]@point+after[:3, 3]-a)/1e-5; v /= max(np.linalg.norm(v), 1e-12)
                contacts.append(dict(pad=name, arm=side, clearance_m=gap,
                    inward_component=float(sign*(b-a)[1]/max(gap, 1e-12)), tool_point_m=b.tolist(),
                    closure_velocity_direction=v.tolist(), inward_closure_component=float(sign*v[1])))
            alignment = np.abs(np.asarray(contacts[0]['tool_point_m'])-contacts[1]['tool_point_m'])
            checks = dict(no_tool_intersections=True, no_nonadjacent_self_intersections=True,
                no_support_obstacle_intersections=True, support_obstacle_clearance=obstacle_clearance is None or obstacle_clearance >= .001,
                support_clearance=clearance >= .001, source_joint_limits=True,
                opposed_contact_clearance=all(.00002 < c['clearance_m'] <= .0005 for c in contacts),
                opposed_normals=all(c['inward_component'] >= .7 for c in contacts),
                opposed_closure_directions=all(c['inward_closure_component'] >= .8 for c in contacts),
                axial_contact_alignment=alignment[0] <= .002, height_contact_alignment=alignment[2] <= .002)
            record = dict(q=dict(q), source_tool_from_palm=palm.tolist(), contacts=contacts,
                hand_support_clearance_m=clearance, support_obstacle_clearance_m=obstacle_clearance,
                contact_axial_offset_m=float(alignment[0]), contact_height_offset_m=float(alignment[2]),
                contact_pair=candidate['pair'], target_axial_m=candidate['axial_m'], roll_rad=float(roll),
                checks={k: bool(v) for k, v in checks.items()}, intrinsic=candidate)
            trials.append(record)
            if all(checks.values()): accepted.append(record)
            else: rejected.update(k for k, v in checks.items() if not v)
        print(json.dumps(dict(stage='placed', candidates=len(trials), accepted=len(accepted), rejected=dict(rejected))), flush=True)
        (output/'trials.json').write_text(json.dumps(trials, indent=2)+'\n')
    accepted.sort(key=lambda r: r['contact_axial_offset_m']+r['contact_height_offset_m'])
    result = dict(scope=__doc__, passed_local_pad_geometry=bool(accepted), candidates=accepted,
        nearest_candidates=sorted(trials, key=lambda r: sum(not v for v in r['checks'].values()))[:20],
        intrinsic_trials=len(solves), distinct_intrinsic_candidates=len(selected),
        tested=len(trials)+sum(rejected[k] for k in ['plane_clearance', 'conservative_tray_clearance', 'source_hand_tool_intersection', 'source_hand_self_intersection', 'source_hand_tray_intersection', 'source_hand_tray_clearance']),
        rejection_counts=dict(rejected), seconds=time.monotonic()-started,
        contract_sha256=sha(output/'contract.json'), qualified_robot_grasp=False)
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['candidates', 'nearest_candidates', 'scope']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('source'); parser.add_argument('support'); parser.add_argument('output')
    args = parser.parse_args(); run(args.source, args.support, args.output)
