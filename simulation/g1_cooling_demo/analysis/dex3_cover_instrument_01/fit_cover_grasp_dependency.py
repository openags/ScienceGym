"""Search official Dex3 source geometry against the existing FTIR handle.

This is a local static grasp screen, not robot, sensor or dynamics validation.
Both successful and rejected candidates are retained. Source URDF/MJCF joint
limits are intersected, with their discrepancy recorded, rather than enlarged.
Planning regions are inferred exposed distal surfaces, not calibrated taxels.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import fcl
import mujoco
import numpy as np
from scipy.optimize import least_squares
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
NAMES = ['right_hand_thumb_0_joint', 'right_hand_thumb_1_joint', 'right_hand_thumb_2_joint',
         'right_hand_index_0_joint', 'right_hand_index_1_joint',
         'right_hand_middle_0_joint', 'right_hand_middle_1_joint']
PARTS = ['right_hand_thumb_2_link', 'right_hand_index_1_link', 'right_hand_middle_1_link']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SourceHand:
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_path(str(HERE / 'hand_inspection.xml'))
        self.model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
        self.data = mujoco.MjData(self.model)
        xml = ET.parse(HERE / 'hand_inspection.xml').getroot()
        urdf = ET.parse(HERE / 'g1_29dof_with_hand_rev_1_0.urdf').getroot()
        self.limits = {}
        for name in NAMES:
            j = self.model.joint(name)
            spec = urdf.find(f"joint[@name='{name}']/limit")
            source = [float(spec.get('lower')), float(spec.get('upper'))]
            bounds = [max(j.range[0], source[0]), min(j.range[1], source[1])]
            self.limits[name] = dict(urdf=source, mjcf=j.range.tolist(), intersection=bounds,
                                     effort_nm=float(spec.get('effort')), velocity_rad_s=float(spec.get('velocity')))
        self.meshes = {}
        self.body_ids = {}
        self.local = {}
        self.manager = trimesh.collision.CollisionManager()
        for body in xml.findall('.//body'):
            bid = int(mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, body.get('name')))
            for geom in body.findall("geom[@group='1']"):
                name = geom.get('mesh')
                path = HERE / 'meshes' / xml.find(f"asset/mesh[@name='{name}']").get('file')
                mesh = trimesh.load(path, force='mesh')
                T = np.eye(4)
                T[:3, 3] = np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
                quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
                R = np.zeros(9); mujoco.mju_quat2Mat(R, quat); T[:3, :3] = R.reshape(3, 3)
                self.meshes[name] = mesh; self.body_ids[name] = bid; self.local[name] = T
                self.manager.add_object(name, mesh)
        self.adjacent = set()
        for a, b in itertools.combinations(self.meshes, 2):
            i, j = self.body_ids[a], self.body_ids[b]
            if i == j or self.model.body_parentid[i] == j or self.model.body_parentid[j] == i:
                self.adjacent.add(tuple(sorted((a, b))))

    def forward(self, q, update_manager=False):
        for name, value in zip(NAMES, q):
            lo, hi = self.limits[name]['intersection']
            if not lo - 1e-9 <= value <= hi + 1e-9:
                raise ValueError(f'Out-of-source-range joint: {name} {value}')
            self.data.joint(name).qpos[0] = value
        mujoco.mj_kinematics(self.model, self.data)
        transforms = {}
        for name, bid in self.body_ids.items():
            T = np.eye(4); T[:3, :3] = self.data.xmat[bid].reshape(3, 3); T[:3, 3] = self.data.xpos[bid]
            transforms[name] = T @ self.local[name]
            if update_manager:
                self.manager.set_transform(name, transforms[name])
        return transforms


def exposed_points(mesh, longitudinal_axis):
    # Ray tests in millimetres avoid absolute tolerances on small CAD faces.
    scaled = mesh.copy(); scaled.apply_scale(1000)
    cross_axis = 1 - longitudinal_axis
    records = []
    for length in [.030, .038, .046]:
        for sign in [-1, 1]:
            origin = np.zeros(3); origin[longitudinal_axis] = length * 1000; origin[cross_axis] = sign * 100
            direction = np.zeros(3); direction[cross_axis] = -sign
            hits, _, faces = scaled.ray.intersects_location([origin], [direction], multiple_hits=True)
            if not len(hits):
                continue
            i = int(np.argmin(np.linalg.norm(hits - origin, axis=1)))
            point = hits[i] / 1000; normal = mesh.face_normals[int(faces[i])]
            if normal[cross_axis] * sign < .7:
                raise ValueError('Outermost surface has an inconsistent source normal')
            records.append(dict(point_m=point.tolist(), normal=normal.tolist(), side=sign,
                                face=int(faces[i]), longitudinal_m=length))
    return records


def handle_mesh():
    revision = json.loads((ROOT / 'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json').read_text())
    path = ROOT / revision['geometry_override']['path']
    scene = trimesh.load(path, force='scene', process=False)
    T, key = scene.graph['lid_handle_bar']; bar = scene.geometry[key].copy(); bar.apply_transform(T)
    center = bar.bounds.mean(axis=0); bar.apply_translation(-center)
    # Source bar axis X -> hand-frame Z. A proper rotation, no reflection.
    R = np.array([[0., 1, 0], [0, 0, 1], [1, 0, 0]])
    T = np.eye(4); T[:3, :3] = R; bar.apply_transform(T)
    return bar, path, center


def run(out, seeds):
    started = time.monotonic(); out = Path(out); out.mkdir(parents=True, exist_ok=False)
    hand = SourceHand(); bar, device_path, device_center = handle_mesh()
    radius = float(np.max(np.linalg.norm(bar.vertices[:, :2], axis=1)))
    if not .00399 < radius < .00401:
        raise ValueError(f'Unexpected handle radius: {radius}')
    targets = trimesh.collision.CollisionManager(); targets.add_object('bar', bar)
    regions = {name: exposed_points(hand.meshes[name], 1 if 'thumb' in name else 0) for name in PARTS}
    lower = [hand.limits[NAMES[i]]['intersection'][0] + .01 for i in [1, 2, 3, 4]] + [.07, -.04]
    upper = [hand.limits[NAMES[i]]['intersection'][1] - .01 for i in [1, 2, 3, 4]] + [.22, .13]
    rng = np.random.default_rng(27028); accepted = []; rejected = []; trial = 0
    for ti, thumb in enumerate(regions[PARTS[0]]):
        for fi, finger in enumerate(regions[PARTS[1]]):
            points = [np.array(x['point_m']) for x in [thumb, finger, finger]]
            normals = [np.array(x['normal']) for x in [thumb, finger, finger]]
            def state(x, update=False):
                q = [0., x[0], x[1], x[2], x[3], x[2], x[3]]
                return q, hand.forward(q, update)
            def residual(x):
                _, poses = state(x); centers = []; ns = []
                for name, point, normal in zip(PARTS, points, normals):
                    T = poses[name]; p = T[:3, :3] @ point + T[:3, 3]; n = T[:3, :3] @ normal
                    centers.extend(1000 * (p[:2] + (radius + .0003) * n[:2] - x[4:6])); ns.append(n)
                return np.r_[centers, 2 * (ns[0] + ns[1]), .001 * x[:4]]
            for seed in range(seeds):
                initial = rng.uniform(lower, upper)
                sol = least_squares(residual, initial, bounds=(lower, upper), max_nfev=120,
                                    ftol=1e-9, xtol=1e-9, gtol=1e-9)
                q, poses = state(sol.x, True); Tbar = np.eye(4); Tbar[:2, 3] = sol.x[4:6]
                targets.set_transform('bar', Tbar)
                gaps = []; contacts = []; normal_alignment = []; central = []; radials = []
                for name, desired_normal in zip(PARTS, normals):
                    distance = fcl.DistanceResult()
                    fcl.distance(hand.manager._objs[name]['obj'], targets._objs['bar']['obj'],
                                 fcl.DistanceRequest(enable_nearest_points=True), distance)
                    gaps.append(float(distance.min_distance))
                    contact = np.asarray(distance.nearest_points[0]); T = poses[name]
                    local = T[:3, :3].T @ (contact - T[:3, 3]); contacts.append(local.tolist())
                    radial = np.asarray(distance.nearest_points[1])[:2] - sol.x[4:6]
                    radial /= max(np.linalg.norm(radial), 1e-12); radials.append(radial)
                    source_normal = T[:3, :3] @ desired_normal
                    normal_alignment.append(float(-source_normal[:2] @ radial))
                    axis = 1 if 'thumb' in name else 0
                    central.append(bool(.025 <= local[axis] <= .048 and abs(local[2]) <= .009))
                _, self_pairs = hand.manager.in_collision_internal(return_names=True)
                self_pairs = [list(p) for p in sorted(self_pairs) if tuple(sorted(p)) not in hand.adjacent]
                _, bar_pairs = hand.manager.in_collision_other(targets, return_names=True)
                opposition = [float(radials[0] @ r) for r in radials[1:]]
                passed = (min(gaps) > .00005 and max(gaps) < .0005 and min(normal_alignment) > .9
                          and all(central) and max(opposition) < -.8 and not self_pairs and not bar_pairs)
                row = dict(trial=trial, region_indices=[ti, fi], q=dict(zip(NAMES, map(float, q))),
                           bar_center_wrist_m=[*map(float, sol.x[4:6]), 0.], gap_m=gaps,
                           contact_local_m=dict(zip(PARTS, contacts)), normal_alignment=normal_alignment,
                           contacts_within_inferred_distal_region=central, opposition_dot=opposition,
                           self_collision_pairs=self_pairs, bar_collision_pairs=[list(p) for p in sorted(bar_pairs)],
                           cost=float(sol.cost), evaluations=int(sol.nfev), passed=bool(passed))
                (accepted if passed else rejected).append(row); trial += 1
            print('regions', ti, fi, 'trials', trial, 'accepted', len(accepted), flush=True)
    report = dict(scope=__doc__,candidates=accepted,rejected=rejected,limits=hand.limits,source_regions=regions,
                  target_radius_m=radius,target_half_length_m=float(bar.extents[2]/2),
                  source_handle_center_m=device_center.tolist(),seconds=time.monotonic()-started,
                  source_json_sha256=digest(HERE/'source.json'),device_sha256=digest(device_path),
                  builder_sha256=digest(__file__),full_instrument_checked=False,physics_qualified=False)
    (out/'grasps.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(trials=trial,candidates=len(accepted),seconds=report['seconds'])),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--seeds',type=int,default=6)
    args=parser.parse_args();run(args.out,args.seeds)
