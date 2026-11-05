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
import shutil

import fcl
import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import KIN, fk, set_hand, robot_meshes
from cary_distal_hand import distal_hand_manager


def run(source, output, support=None, refine_from=None, finger_step=.004, finger_radius=5, seed_limit=20,
        thumb_spread_offsets=(0.,)):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'source_snapshot').mkdir()
    shutil.copyfile(__file__, output/'source_snapshot'/Path(__file__).name)
    started = time.monotonic()
    seeds_path = ROOT/'viewer/cooling_concept_v2/previews/tweezers_right_fit.json'
    seeds = json.loads(seeds_path.read_text())['candidates']
    if refine_from:
        if not support:
            raise ValueError('Finger refinement requires a reviewed support pose')
        seeds_path = Path(refine_from).resolve()
        previous = json.loads(seeds_path.read_text())
        prior_contract_path = seeds_path.parent/'contract.json'
        assert hashlib.sha256(prior_contract_path.read_bytes()).hexdigest() == previous['contract_sha256']
        prior_contract = json.loads(prior_contract_path.read_text())
        assert prior_contract['support_review_sha256'] == hashlib.sha256(Path(support).read_bytes()).hexdigest()
        geometry_key = str((source/'rest_geometry.glb').relative_to(ROOT))
        assert prior_contract['source_hashes'][geometry_key] == hashlib.sha256((source/'rest_geometry.glb').read_bytes()).hexdigest()
        seeds = []
        if not 0 < finger_step <= .02 or not 1 <= finger_radius <= 10 or not 1 <= seed_limit <= 20:
            raise ValueError('Invalid bounded finger refinement grid')
        finger_offsets = [float(v) for v in np.arange(-finger_radius,finger_radius+1)*finger_step]
        if not thumb_spread_offsets or not all(np.isfinite(v) and abs(v)<=.1 for v in thumb_spread_offsets):
            raise ValueError('Invalid bounded thumb spread refinement')
        for prior_index, candidate in enumerate(previous['nearest_candidates'][:seed_limit]):
            for index_offset, thumb_offset, spread_offset in itertools.product(finger_offsets,finger_offsets,thumb_spread_offsets):
                q = dict(candidate['q'])
                q['right_index_1_joint'] += index_offset
                q['right_thumb_2_joint'] += thumb_offset
                q['right_thumb_1_joint'] += spread_offset
                seeds.append(dict(q=q, source_tool_from_palm=candidate['source_tool_from_palm'],
                                  previous_candidate=prior_index,
                                  finger_offsets_rad=[index_offset,thumb_offset],thumb_spread_offset_rad=spread_offset))
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
    hand_meshes = robot_meshes() if support else None
    world_from_source = None
    if support:
        support = Path(support).resolve()
        support_report = json.loads(support.read_text())
        assert support_report['passed']
        initial = np.asarray(support_report['final_qpos'])
        world_from_source = np.eye(4)
        world_from_source[:3,:3] = Rotation.from_quat(np.r_[initial[4:7],initial[3]]).as_matrix()
        world_from_source[:3,3] = initial[:3]-world_from_source[:3,:3]@np.array([.13,0,.00575])
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
    if support:
        contract.update(support_review=str(support.relative_to(ROOT)),
                        support_review_sha256=hashlib.sha256(support.read_bytes()).hexdigest(),
                        minimum_hand_support_clearance_m=.001,
                        rotation_offsets_rad=dict(x=[-.3,-.15,0,.15,.3],y=[-.3,-.15,0,.15,.3]),
                        rotation_center_in_source_m=[.065,0,.00575])
        contract['translation_offsets_m']['z'] = [-.002,0,.002,.004]
    if refine_from:
        contract.update(refinement_input=str(seeds_path.relative_to(ROOT)),
                        refinement_input_sha256=hashlib.sha256(seeds_path.read_bytes()).hexdigest(),
                        refinement_contract_sha256=hashlib.sha256(prior_contract_path.read_bytes()).hexdigest(),
                        refinement_parent_candidates=min(seed_limit,len(previous['nearest_candidates'])),
                        finger_offsets_rad={'right_index_1_joint':finger_offsets,
                                            'right_thumb_2_joint':finger_offsets,
                                            'right_thumb_1_joint':list(thumb_spread_offsets)},
                        tool_translation_from_legacy_frame_m=[0,0,0],
                        rotation_offsets_rad=dict(x=[0.],y=[0.]),
                        translation_offsets_m=dict(x=[0.],y=[0.],z=[0.]))
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    outcomes = defaultdict(int); accepted = []; nearest = []
    tested = 0
    for number, seed in enumerate(seeds):
        q = seed['q']
        if refine_from:
            palm = np.asarray(seed['source_tool_from_palm']).copy()
        else:
            palm = np.asarray(seed['palm_matrix']).copy()
            # Earlier asset had its tip at -65 mm; this asset has its tip at zero.
            palm[:3,3] += [.065,0,0]
        set_hand(hand, 'right', q, palm)
        _, pairs = hand.in_collision_internal(return_names=True)
        if any(tuple(sorted(pair)) not in adjacent for pair in pairs):
            outcomes['self_intersection_seed'] += 1;continue
        values = dict(q)
        valid_limits = True
        for joint in KIN['joints']:
            if joint.get('mimic'):
                mimic=joint['mimic'];values[joint['name']]=float(mimic.get('offset',0))+float(mimic.get('multiplier',1))*values.get(mimic['joint'],0)
            if joint.get('limits') and joint['name'] in values:
                valid_limits &= joint['limits']['lower'] <= values[joint['name']] <= joint['limits']['upper']
        if not valid_limits:
            outcomes['source_joint_limits'] += 1;continue
        if support:
            world=fk(q);inverse=np.linalg.inv(world['right_palm_force_sensor'])
            points=[]
            for name in hand._objs:
                transform=inverse@world[name]
                points.append(hand_meshes[name].vertices@transform[:3,:3].T+transform[:3,3])
            points=np.concatenate(points)
            # Linear support-plane clearance has the same extremum on the hull.
            hull=points[ConvexHull(points).vertices]
        angles = [-.3,-.15,0,.15,.3] if support and not refine_from else [0.]
        xs = contract['translation_offsets_m']['x']
        ys = contract['translation_offsets_m']['y']
        zs = contract['translation_offsets_m']['z']
        for ax,ay,dx,dy,dz in itertools.product(angles,angles,xs,ys,zs):
            rotation=Rotation.from_euler('xy',[ax,ay]).as_matrix()
            center=np.array([.065,0,.00575])
            pose = palm.copy();pose[:3,:3]=rotation@palm[:3,:3]
            pose[:3,3]=rotation@(palm[:3,3]-center)+center+[dx,dy,dz]
            tested += 1
            clearance = None
            if support:
                placed = world_from_source@pose
                clearance = float((hull@placed[2,:3]+placed[2,3]).min())
                if clearance < .001:
                    outcomes['support_intersection_or_clearance'] += 1;continue
            set_hand(hand, 'right', q, pose)
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
                          maximum_pad_clearance_m=max(c['clearance_m'] for c in choice),
                          source_joint_limits_ok=True, hand_support_clearance_m=clearance)
            if refine_from:
                record.update(previous_candidate=seed['previous_candidate'],
                              finger_offsets_rad=seed['finger_offsets_rad'],
                              thumb_spread_offset_rad=seed['thumb_spread_offset_rad'])
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
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--support')
    p.add_argument('--refine-from');p.add_argument('--finger-step',type=float,default=.004)
    p.add_argument('--finger-radius',type=int,default=5);p.add_argument('--seed-limit',type=int,default=20)
    p.add_argument('--thumb-spread-offsets',type=float,nargs='+',default=[0.]);a=p.parse_args()
    run(a.source,a.output,a.support,a.refine_from,a.finger_step,a.finger_radius,a.seed_limit,a.thumb_spread_offsets)
