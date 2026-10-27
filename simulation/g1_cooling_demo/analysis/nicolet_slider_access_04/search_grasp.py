"""Search source-pad reference grasps through the unchanged sliding window.

Refinement uses source-pad surface extent rather than only a central point.
Offline geometry proposals only. The full selected Inspire hand and terminal
wrist are checked against the prepared instrument and installed accessory.
No arm reach, approach/closure, contact force or physical execution is claimed.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time

import fcl
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
VIEW = ROOT / 'viewer/cooling_concept_v2'
sys.path[:0] = [str(VIEW), str(ROOT / 'simulation/g1_cooling_demo')]
from source_geometry import KIN, fk, robot_meshes, set_hand
from cary_distal_hand import distal_hand_manager
from fit_ftir_cover_pad_grasp import source_limits_ok

REFERENCE = {'gold_reference_holder', 'gold_reference_shoulder', 'diffuse_gold_reference_face'}
JOINTS = ['left_index_1_joint', 'left_thumb_1_joint', 'left_thumb_2_joint']


def translate(point):
    result = np.eye(4)
    result[:3, 3] = point
    return result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_environment():
    paths = [VIEW / 'runtime_scene.json', VIEW / 'optical_setup.json',
             ROOT / 'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json',
             ROOT / 'assets/pike_integratir_dtgs_v1/interfaces.json',
             ROOT / 'assets/nicolet_6700_v1/interfaces.json']
    runtime, setup, revision, interface, nicolet = [json.loads(p.read_text()) for p in paths]
    assets = {a['id']: a for a in runtime['assets']}
    port = np.array(setup['ports']['ftir_sample']['position_m'])
    slider = set(next(i for i in nicolet['interfaces'] if i['id'] == 'sample_access_slider')['parts'])
    env, reference = trimesh.collision.CollisionManager(), trimesh.collision.CollisionManager()
    rest, meshes = {}, {}
    for identity in ['nicolet', 'pike']:
        asset = assets[identity]
        path = ROOT / (revision['geometry_override']['path'] if identity == 'nicolet' else asset['geometry'])
        paths.append(path)
        scene = trimesh.load(path, force='scene', process=False)
        for name in scene.graph.nodes_geometry:
            if identity == 'pike' and name not in set(interface['module_parts']) | REFERENCE:
                continue
            T, key = scene.graph[name]
            override = setup['parts'].get(identity, {}).get(name)
            if override:
                T = np.array(override['matrix']) @ T
            T = translate(np.array(asset['position_m']) - port) @ T
            if identity == 'nicolet' and name in slider:
                T = translate([0, .104, 0]) @ T
            mesh = scene.geometry[key]
            if identity == 'pike' and name in REFERENCE:
                reference.add_object(name, mesh, T)
                rest[name] = T
                meshes[name] = mesh.copy()
                meshes[name].apply_transform(T)
            else:
                env.add_object(identity + '::' + name, mesh, T)
    return env, reference, rest, meshes, paths, port


def main():
    started = time.monotonic()
    output = HERE / 'review.json'
    if output.exists():
        raise FileExistsError('Preserve previous search results: ' + str(output))
    env, reference, rest, target_meshes, paths, port = load_environment()
    source = robot_meshes('left')
    hand = distal_hand_manager('left')
    limits = {j['name']: j['limits'] for j in KIN['joints'] if j['name'] in JOINTS}
    lower = np.array([limits[n]['lower'] + .001 for n in JOINTS] + [-.2] * 3 + [-np.pi] * 3)
    upper = np.array([limits[n]['upper'] - .001 for n in JOINTS] + [.2] * 3 + [np.pi] * 3)
    graph = defaultdict(list)
    for j in KIN['joints']:
        weight = int(j['type'] == 'revolute')
        graph[j['parent']].append((j['id'], weight))
        graph[j['id']].append((j['parent'], weight))
    adjacent = set()
    for link in hand._objs:
        queue = [(link, None, 0)]
        while queue:
            name, parent, depth = queue.pop()
            if depth > 1:
                continue
            if name in hand._objs:
                adjacent.add(tuple(sorted([name, link])))
            queue.extend((n, name, depth + w) for n, w in graph[name] if n != parent)
    holder = target_meshes['gold_reference_holder']
    center = holder.bounds.mean(0)
    radius = float(np.mean(holder.extents[:2]) / 2)
    rng = np.random.default_rng(20261028)
    candidates, fits, rejected = [], [], Counter()
    placements = []
    checked = 0
    combinations = [(3, 4), (2, 4)]
    for index_pad, thumb_pad in combinations:
        names = [f'left_index_force_sensor_{index_pad}', f'left_thumb_force_sensor_{thumb_pad}']
        centers, normals, boundaries, samples = [], [], [], []
        for name in names:
            # Millimetres avoid trimesh's metre-scale absolute proximity epsilon.
            mesh = source[name].copy()
            mesh.apply_scale(1000)
            probe = mesh.bounds.mean(0)
            probe[2] = mesh.bounds[1, 2] + 10
            point, _, face = trimesh.proximity.closest_point(mesh, [probe])
            centers.append(point[0] / 1000)
            samples.append(np.vstack([mesh.vertices, mesh.triangles_center]) / 1000)
            normals.append(mesh.face_normals[face[0]])
            assert normals[-1][2] > .5
            exposed = mesh.vertices[np.unique(mesh.faces[mesh.face_normals[:, 2] > .5])] / 1000
            boundaries.append(ConvexHull(exposed[:, :2]).equations)

        def pose(x):
            q = dict(zip(JOINTS, map(float, x[:3])))
            world = fk(q)
            palm = translate(x[3:6])
            palm[:3, :3] = Rotation.from_rotvec(x[6:]).as_matrix()
            base = palm @ np.linalg.inv(world['left_palm_force_sensor'])
            return q, palm, [base @ world[n] for n in names]

        def residual(x):
            _, palm, transforms = pose(x)
            result, radial = [], []
            for T, point, normal, surface in zip(transforms, centers, normals, samples):
                p = T[:3, :3] @ point + T[:3, 3]
                r = np.r_[p[:2] - center[:2], 0.]
                distance = np.linalg.norm(r)
                r /= max(distance, 1e-9)
                radial.append(r)
                world_surface = surface @ T[:3, :3].T + T[:3, 3]
                nearest_radius = np.min(np.linalg.norm(world_surface[:, :2] - center[:2], axis=1))
                result.extend([600 * (nearest_radius - radius - .0004),
                               *list(2 * (T[:3, :3] @ normal + r)),
                               100 * (p[2] - contact_height)])
            result.extend([2 * max(0., radial[0] @ radial[1] + .8),
                           60 * max(0., desired_palm_height - palm[2, 3])])
            return result

        for trial in range(24):
            desired_palm_height = [.085, .105, .125][trial // 8]
            contact_height = center[2] + (.004 if trial % 2 else 0.)
            initial_q = [.55, 1.10, .15] if trial == 0 else rng.uniform(lower[:3], upper[:3])
            world = fk(dict(zip(JOINTS, initial_q)))
            base = np.linalg.inv(world['left_palm_force_sensor'])
            pts = [(base @ world[n] @ np.r_[c, 1.])[:3] for n, c in zip(names, centers)]
            midpoint = np.mean(pts, axis=0)
            direction = pts[1] - pts[0]
            direction /= np.linalg.norm(direction)
            toward = midpoint - direction * (midpoint @ direction)
            toward /= np.linalg.norm(toward)
            local = np.column_stack([direction, toward, np.cross(direction, toward)])
            tilt = [0., -.6, .6, 1.0][trial % 4]
            forward = np.array([0., np.sin(tilt), -np.cos(tilt)])
            R = np.column_stack([[1., 0., 0.], forward, np.cross([1., 0., 0.], forward)]) @ local.T
            x0 = np.r_[initial_q, center - R @ midpoint, Rotation.from_matrix(R).as_rotvec()]
            result = least_squares(residual, np.clip(x0, lower + 1e-7, upper - 1e-7),
                                   bounds=(lower, upper), max_nfev=140)
            q, palm, transforms = pose(result.x)
            assert source_limits_ok(q)
            set_hand(hand, 'left', q, palm)
            gaps, margins, exposed, points = [], [], [], []
            for name, T, boundary in zip(names, transforms, boundaries):
                distance = fcl.DistanceResult()
                fcl.distance(hand._objs[name]['obj'], reference._objs['gold_reference_holder']['obj'],
                             fcl.DistanceRequest(enable_nearest_points=True), distance)
                gaps.append(float(distance.min_distance))
                local_contact = (np.linalg.inv(T) @ np.r_[distance.nearest_points[0], 1.])[:3]
                mesh = source[name].copy()
                mesh.apply_scale(1000)
                _, _, face = trimesh.proximity.closest_point(mesh, [1000 * local_contact])
                exposed.append(bool(mesh.face_normals[face[0], 2] > .5))
                margins.append(float(np.min(-(boundary[:, :2] @ local_contact[:2] + boundary[:, 2]))))
                points.append(np.asarray(distance.nearest_points[1]))
            radials = [p[:2] - center[:2] for p in points]
            opposition = float(radials[0] @ radials[1] / max(1e-12, np.linalg.norm(radials[0]) * np.linalg.norm(radials[1])))
            pad_ok = (min(gaps) > .00005 and max(gaps) < .001 and min(margins) > .0004
                      and all(exposed) and opposition < -.6)
            fits.append(dict(pads=names, trial=trial, q=q, palm_matrix=palm.tolist(), cost=float(result.cost),
                             desired_palm_height_m=desired_palm_height, contact_height_m=contact_height,
                             pad_gaps_m=gaps, exposed=exposed, projected_margin_m=margins,
                             opposition_dot=opposition, passed_pad_screen=pad_ok))
            if not pad_ok:
                rejected['pad_fit'] += 1
                print('fit', names, trial, 'pad rejected', np.round(gaps, 6).tolist(), flush=True)
                continue
            for fold in [.4, .8, 1.1, 1.35]:
                fingers = dict(q, **{f'left_{f}_1_joint': fold for f in ['middle', 'ring', 'little']})
                assert source_limits_ok(fingers)
                for angle in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                    Z = np.eye(4)
                    Z[:3, :3] = Rotation.from_euler('z', angle).as_matrix()
                    Z[:3, 3] = center - Z[:3, :3] @ center
                    proposed = Z @ palm
                    set_hand(hand, 'left', fingers, proposed)
                    checked += 1
                    _, pairs = hand.in_collision_other(reference, return_names=True)
                    record = dict(pad_fit_index=len(fits)-1, q=fingers, yaw_rad=float(angle), palm_matrix=proposed.tolist())
                    if pairs:
                        placements.append(dict(record, rejected='reference_contact', pairs=sorted([sorted(p) for p in pairs])))
                        rejected['reference_contact'] += 1
                        continue
                    _, pairs = hand.in_collision_internal(return_names=True)
                    if any(tuple(sorted(p)) not in adjacent for p in pairs):
                        placements.append(dict(record, rejected='nonadjacent_self_contact', pairs=sorted([sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent])))
                        rejected['nonadjacent_self_contact'] += 1
                        continue
                    _, pairs = hand.in_collision_other(env, return_names=True)
                    if pairs:
                        placements.append(dict(record, rejected='instrument_contact', pairs=sorted([sorted(p) for p in pairs])))
                        rejected['instrument_contact'] += 1
                        continue
                    placements.append(dict(record, rejected=None))
                    failures = []
                    waypoints = [[0, -.035, .180], [0, -.035, .030], [0, 0, .030], [0, 0, 0]]
                    for phase, (a, b) in enumerate(zip(waypoints[:-1], waypoints[1:])):
                        for fraction in np.linspace(0, 1, 61):
                            delta = (1 - fraction) * np.array(a) + fraction * np.array(b)
                            set_hand(hand, 'left', fingers, translate(delta) @ proposed)
                            _, pairs = hand.in_collision_other(env, return_names=True)
                            if pairs:
                                failures.append(dict(phase=phase, fraction=float(fraction), pairs=sorted([sorted(p) for p in pairs])))
                    candidates.append(dict(pad_fit_index=len(fits) - 1, q=fingers,
                                           palm_at_port=proposed.tolist(), yaw_rad=float(angle),
                                           waypoints_m=waypoints, states=183,
                                           hand_path_passed=not failures, failures=failures))
            print('fit', names, trial, 'placements', checked, 'seated', len(candidates), flush=True)
    paths.extend([Path(__file__), VIEW / 'source_geometry.py', VIEW / 'cary_distal_hand.py',
                  ROOT / 'simulation/g1_cooling_demo/fit_ftir_cover_pad_grasp.py',
                  ROOT / 'assets/cooling_lab_v1/scene.json'])
    manifest = json.loads((ROOT / 'assets/cooling_lab_v1/scene.json').read_text())
    paths.append(ROOT / next(a['geometry'] for a in manifest['assets'] if a['id'] == 'g1'))
    report = dict(scope=__doc__,source_hashes={str(p.relative_to(ROOT)): sha(p) for p in paths},
                  cover_angle_rad=0., slider_travel_m=.104, port_world_m=port.tolist(),
                  holder_bounds_port_frame_m=holder.bounds.tolist(), fits=fits,
                  tested_placements=checked, rejected=dict(rejected), candidates=candidates, placements=placements,
                  passed_hand_paths=sum(c['hand_path_passed'] for c in candidates),
                  source_joint_and_mimic_limits_checked=True, equipment_geometry_changed=False,
                  physical_execution=False, whole_arm_checked=False, approach_and_closure_checked=False,
                  seconds=time.monotonic() - started)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['tested_placements', 'rejected', 'passed_hand_paths', 'seconds']}), flush=True)


if __name__ == '__main__':
    main()
