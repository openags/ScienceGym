"""Explore lifting the cover by the front edge of its open sample window.

The manual establishes the separate slider and hinged cover. This grasp is
an inferred robot strategy, not a manufacturer procedure. Equipment geometry
is unchanged. The slider is prepared open for this geometry screen; opening
it, whole-arm reach, approach, forces and execution remain unqualified.
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
LOADER = HERE.parent / 'nicolet_slider_access_03/search_grasp.py'
sys.path[:0] = [str(VIEW), str(ROOT/'simulation/g1_cooling_demo'), str(LOADER.parent)]
from search_grasp import load_environment, translate, sha
from source_geometry import KIN, fk, robot_meshes, set_hand
from cary_distal_hand import distal_hand_manager
from fit_ftir_cover_pad_grasp import source_limits_ok


def object_transform(obj):
    T = np.eye(4)
    T[:3, :3] = obj.getRotation()
    T[:3, 3] = obj.getTranslation()
    return T


def main():
    started = time.monotonic()
    out = HERE/'review.json'
    if out.exists():
        raise FileExistsError(out)
    env, reference, _, _, paths, port = load_environment()
    scene = trimesh.load(paths[5], force='scene', process=False)
    meshes = {}
    for name in scene.graph.nodes_geometry:
        _, key = scene.graph[name]
        mesh = scene.geometry[key].copy()
        mesh.apply_transform(object_transform(env._objs['nicolet::'+name]['obj']))
        meshes[name] = mesh
    lid = meshes['sample_bay_lid']
    front = meshes['sample_cover_front_lip'].bounds.mean(0)
    # Existing opening front edge is 34 mm rearward of the front lip datum.
    # Place the inferred pinch 8 mm inside the frame, retaining source size.
    patch = np.array([front[0], front[1]+.026, lid.bounds.mean(0)[2]])
    thickness = float(lid.extents[2])
    pivot = front + [0., .266, .006]
    interfaces = json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    moving = {'nicolet::'+n for n in interfaces['cover_parts']}
    rest = {name: object_transform(env._objs[name]['obj']) for name in moving}
    source = robot_meshes('right')
    hand = distal_hand_manager('right')
    joints = ['right_index_1_joint', 'right_thumb_1_joint', 'right_thumb_2_joint']
    limits = {j['name']: j['limits'] for j in KIN['joints'] if j['name'] in joints}
    low = np.r_[[limits[n]['lower']+.001 for n in joints], [-.15, -.15, -.02], [-np.pi]*3]
    high = np.r_[[limits[n]['upper']-.001 for n in joints], [.15, .15, .2], [np.pi]*3]
    graph = defaultdict(list)
    for j in KIN['joints']:
        w = int(j['type']=='revolute')
        graph[j['parent']].append((j['id'], w))
        graph[j['id']].append((j['parent'], w))
    adjacent = set()
    for link in hand._objs:
        pending = [(link, None, 0)]
        while pending:
            n, parent, depth = pending.pop()
            if depth > 1: continue
            if n in hand._objs: adjacent.add(tuple(sorted([link, n])))
            pending.extend((v, n, depth+w) for v, w in graph[n] if v != parent)
    rng = np.random.default_rng(316)
    fits, candidates, placements = [], [], []
    rejection = Counter()
    for ip, tp in [(3, 4), (2, 4), (3, 1)]:
        names = [f'right_index_force_sensor_{ip}', f'right_thumb_force_sensor_{tp}']
        points, normals, samples, bounds = [], [], [], []
        for n in names:
            mesh = source[n].copy(); mesh.apply_scale(1000)
            probe = mesh.bounds.mean(0); probe[2] = mesh.bounds[1, 2]+10
            p, _, face = trimesh.proximity.closest_point(mesh, [probe])
            points.append(p[0]/1000); normals.append(mesh.face_normals[face[0]])
            samples.append(np.vstack([mesh.vertices, mesh.triangles_center])/1000)
            exposed = mesh.vertices[np.unique(mesh.faces[mesh.face_normals[:, 2]>.5])]/1000
            bounds.append(ConvexHull(exposed[:, :2]).equations)

        def pose(x):
            q = dict(zip(joints, map(float, x[:3])))
            palm = translate(x[3:6]); palm[:3, :3] = Rotation.from_rotvec(x[6:]).as_matrix()
            world = fk(q); base = palm @ np.linalg.inv(world['right_palm_force_sensor'])
            return q, palm, [base @ world[n] for n in names]

        def residual(x):
            _, palm, transforms = pose(x); residuals = []
            for sign, T, p, n, surface in zip([1., -1.], transforms, points, normals, samples):
                contact = T[:3, :3] @ p + T[:3, 3]
                vertices = surface @ T[:3, :3].T + T[:3, 3]
                extreme = vertices[:, 2].max() if sign == 1 else vertices[:, 2].min()
                residuals.extend([800*(extreme+sign*(thickness/2+.00035)),
                                  *list(3*(T[:3, :3]@n-[0., 0., sign])),
                                  *list(100*contact[:2])])
            residuals.append(30*max(0., .045-palm[2, 3]))
            return residuals

        for trial in range(10):
            q0 = [.95, 1.12, .36] if trial == 0 else rng.uniform(low[:3], high[:3])
            w = fk(dict(zip(joints, q0))); inv = np.linalg.inv(w['right_palm_force_sensor'])
            pts = [(inv @ w[n] @ np.r_[p, 1.])[:3] for n, p in zip(names, points)]
            middle = np.mean(pts, axis=0); gap = pts[1]-pts[0]; gap /= np.linalg.norm(gap)
            toward = middle-gap*(middle@gap); toward /= np.linalg.norm(toward)
            local = np.column_stack([gap, toward, np.cross(gap, toward)])
            R = np.column_stack([[0., 0., 1.], [0., -1., 0.], [1., 0., 0.]]) @ local.T
            x0 = np.r_[q0, -R@middle, Rotation.from_matrix(R).as_rotvec()]
            solved = least_squares(residual, np.clip(x0, low+1e-7, high-1e-7),
                                   bounds=(low, high), max_nfev=180)
            q, palm, transforms = pose(solved.x)
            assert source_limits_ok(q)
            fits.append(dict(pads=names, trial=trial, q=q, palm_relative_patch=palm.tolist(),
                             cost=float(solved.cost), residual_norm=float(np.linalg.norm(solved.fun))))
            for fold in [.2, .8, 1.3]:
                fingers = dict(q, **{f'right_{f}_1_joint': fold for f in ['middle','ring','little']})
                assert source_limits_ok(fingers)
                for yaw in np.linspace(0, 2*np.pi, 36, endpoint=False):
                    Z = np.eye(4); Z[:3, :3] = Rotation.from_euler('z', yaw).as_matrix()
                    for dx in [-.035, 0., .035]:
                        for n, T in rest.items(): env.set_transform(n, T)
                        actual = translate(patch+[dx,0.,0.]) @ Z @ palm
                        set_hand(hand, 'right', fingers, actual)
                        row = dict(fit=len(fits)-1, fold=fold, yaw_rad=float(yaw), x_offset_m=dx)
                        gaps, exposed, margins, contacted = [], [], [], []
                        world = fk(fingers); base = actual @ np.linalg.inv(world['right_palm_force_sensor'])
                        for n, boundary in zip(names, bounds):
                            result = fcl.DistanceResult()
                            fcl.distance(hand._objs[n]['obj'], env._objs['nicolet::sample_bay_lid']['obj'],
                                         fcl.DistanceRequest(enable_nearest_points=True), result)
                            gaps.append(float(result.min_distance))
                            local_point = (np.linalg.inv(base@world[n]) @ np.r_[result.nearest_points[0],1.])[:3]
                            mesh = source[n].copy(); mesh.apply_scale(1000)
                            _, _, face = trimesh.proximity.closest_point(mesh, [1000*local_point])
                            exposed.append(bool(mesh.face_normals[face[0],2]>.5))
                            margins.append(float(np.min(-(boundary[:,:2]@local_point[:2]+boundary[:,2]))))
                            contacted.append(np.asarray(result.nearest_points[1]))
                        pad_ok = (min(gaps)>.00005 and max(gaps)<.001 and all(exposed)
                                  and min(margins)>.0003 and contacted[1][2]-contacted[0][2]>.9*thickness)
                        if not pad_ok:
                            rejection['pad_surface'] += 1
                            continue
                        _, pairs = hand.in_collision_internal(return_names=True)
                        pairs = [sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent]
                        if pairs:
                            rejection['self_contact'] += 1
                            placements.append(dict(row, rejected='self_contact', pairs=pairs))
                            continue
                        _, pairs = hand.in_collision_other(env, return_names=True)
                        if pairs:
                            rejection['instrument_contact'] += 1
                            placements.append(dict(row, rejected='instrument_contact', pairs=sorted([sorted(p) for p in pairs])))
                            continue
                        arc_failures = []
                        for degrees in np.linspace(0.,65.,66):
                            arc = np.eye(4); arc[:3,:3] = Rotation.from_euler('x',-degrees,degrees=True).as_matrix()
                            arc[:3,3] = pivot-arc[:3,:3]@pivot
                            for n,T in rest.items(): env.set_transform(n,arc@T)
                            set_hand(hand,'right',fingers,arc@actual)
                            _,pairs = hand.in_collision_other(env,return_names=True)
                            if pairs: arc_failures.append(dict(degrees=float(degrees),pairs=sorted([sorted(p) for p in pairs])))
                        candidates.append(dict(row,q=fingers,palm_in_port_frame=actual.tolist(),pad_gaps_m=gaps,
                                               projected_margins_m=margins,arc_failures=arc_failures,
                                               passed_distal_arc=not arc_failures))
            print('edge_fit', names, trial, 'seated',len(candidates),'passed_arcs',sum(c['passed_distal_arc'] for c in candidates),flush=True)
    paths.extend([Path(__file__),LOADER,VIEW/'source_geometry.py',VIEW/'cary_distal_hand.py',
                  ROOT/'simulation/g1_cooling_demo/fit_ftir_cover_pad_grasp.py',ROOT/'assets/cooling_lab_v1/scene.json'])
    manifest=json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
    paths.append(ROOT/next(a['geometry'] for a in manifest['assets'] if a['id']=='g1'))
    report=dict(scope=__doc__,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},
                patch_in_port_frame_m=patch.tolist(),hinge_in_port_frame_m=pivot.tolist(),
                lid_thickness_m=thickness,slider_prepared_travel_m=.104,world_port_m=port.tolist(),
                fits=fits,rejected=dict(rejection),placements=placements,candidates=candidates,
                passed_distal_arcs=sum(c['passed_distal_arc'] for c in candidates),
                source_joint_and_mimic_limits_checked=True,equipment_geometry_changed=False,
                approach_and_closure_checked=False,whole_arm_checked=False,physics_qualified=False,
                seconds=time.monotonic()-started)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(seated=len(candidates),passed_arcs=report['passed_distal_arcs'],seconds=report['seconds'])),flush=True)


if __name__ == '__main__':
    main()
