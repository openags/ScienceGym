"""Fit opposed source-hand contact surfaces while retaining the tool's support.

Offline authoring only. Material contact points are geometric optimization
features, not sensors or runtime observations. Independent source-mesh checks
must accept the result before any contact experiment can use it. No grasp,
whole-body reach, approach trajectory or dynamics qualification is granted.
"""
import argparse
from collections import defaultdict
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
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import KIN, fk, set_hand, robot_meshes
from cary_distal_hand import distal_hand_manager


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(fit, output):
    fit, output = Path(fit).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'source_snapshot').mkdir()
    shutil.copyfile(__file__, output/'source_snapshot'/Path(__file__).name)
    previous = json.loads(fit.read_text())
    prior = json.loads((fit.parent/'contract.json').read_text())
    assert sha(fit.parent/'contract.json') == previous['contract_sha256']
    support_path = ROOT/prior['support_review']
    assert sha(support_path) == prior['support_review_sha256']
    support = json.loads(support_path.read_text()); assert support['passed']
    geometry = next(ROOT/p for p in prior['source_hashes'] if p.endswith('/rest_geometry.glb'))
    assert sha(geometry) == prior['source_hashes'][str(geometry.relative_to(ROOT))]
    original = previous['candidates'][0]
    palm0 = np.asarray(original['source_tool_from_palm'])
    q0 = dict(original['q'])
    source = trimesh.load(geometry, force='scene', process=False)
    parts = defaultdict(list)
    for name in source.graph.nodes_geometry:
        transform, key = source.graph[name]
        mesh = source.geometry[key].copy(); mesh.apply_transform(transform)
        group = 'positive' if name.startswith('positive_') else 'negative' if name.startswith('negative_') else 'heel'
        parts[group].append(mesh)
    tool = trimesh.collision.CollisionManager()
    tool_meshes = {n:trimesh.util.concatenate(v) for n,v in parts.items()}
    for name, mesh in tool_meshes.items():tool.add_object(name,mesh)
    meshes = robot_meshes()
    hand = distal_hand_manager('right',meshes)
    vertices = {n:meshes[n].vertices[ConvexHull(meshes[n].vertices).vertices] for n in hand._objs}
    initial = np.asarray(support['final_qpos'])
    world_from_source = np.eye(4)
    world_from_source[:3,:3] = Rotation.from_quat(np.r_[initial[4:7],initial[3]]).as_matrix()
    world_from_source[:3,3] = initial[:3]-world_from_source[:3,:3]@np.array([.13,0,.00575])
    graph = defaultdict(list)
    for joint in KIN['joints']:
        weight = int(joint['type']=='revolute')
        graph[joint['parent']].append((joint['id'],weight))
        graph[joint['id']].append((joint['parent'],weight))
    adjacent = set()
    for name in hand._objs:
        queue = [(name,None,0)]
        while queue:
            link,parent,depth = queue.pop()
            if depth>1:continue
            adjacent.add(tuple(sorted([name,link])))
            queue.extend((n,link,depth+w) for n,w in graph[link] if n!=parent)
    drivers = ['right_index_1_joint','right_thumb_1_joint','right_thumb_2_joint']
    limits = {j['name']:j['limits'] for j in KIN['joints'] if j['name'] in drivers}
    bounds = (np.r_[[-5.]*3,[-1.]*3,[limits[n]['lower'] for n in drivers]],
              np.r_[[5.]*3,[1.]*3,[limits[n]['upper'] for n in drivers]])
    pairs = [('right_index_force_sensor_2','right_thumb_force_sensor_4'),
             ('right_index_force_sensor_3','right_thumb_force_sensor_4'),
             ('right_index_2','right_thumb_4')]
    axial_targets = [.060,.075,.090,.105]
    contract = dict(scope=__doc__,fit_sha256=sha(fit),support_review=str(support_path.relative_to(ROOT)),
        support_review_sha256=sha(support_path),source_hashes={
            str(geometry.relative_to(ROOT)):sha(geometry),str(Path(__file__).relative_to(ROOT)):sha(__file__),
            str((ROOT/'viewer/cooling_concept_v2/source_geometry.py').relative_to(ROOT)):sha(ROOT/'viewer/cooling_concept_v2/source_geometry.py'),
            str((ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json').relative_to(ROOT)):sha(ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json')},
        source_visual_geometry_sha256=sha(ROOT/'assets/unitree_g1_inspire_v1/geometry.glb') if (ROOT/'assets/unitree_g1_inspire_v1/geometry.glb').exists() else None,
        kinematics_sha256=hashlib.sha256(json.dumps(KIN,sort_keys=True).encode()).hexdigest(),
        contact_body_pairs=pairs,axial_targets_m=axial_targets,target_height_m=.00575,
        minimum_pad_clearance_m=.00002,maximum_pad_clearance_m=.0005,
        maximum_contact_axial_offset_m=.002,maximum_contact_height_offset_m=.002,
        minimum_inward_normal_component=.7,minimum_hand_support_clearance_m=.001,
        allowed_translation_from_seed_m=.05,allowed_rotation_vector_components_rad=1.,
        solver='scipy least_squares; material points and directions; source mesh rejection afterwards',
        maximum_solver_evaluations=160,full_body_or_dynamics_checked=False)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    started=time.monotonic();trials=[];accepted=[]

    def coordinates(x):
        q=dict(q0);q.update(zip(drivers,map(float,x[6:])))
        palm=palm0.copy();palm[:3,:3]=Rotation.from_rotvec(x[3:6]).as_matrix()@palm0[:3,:3]
        palm[:3,3]+=x[:3]*.01
        world=fk(q);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
        transforms={n:base@world[n] for n in hand._objs}
        return q,palm,transforms

    def distance(body,group):
        result=fcl.DistanceResult()
        fcl.distance(hand._objs[body]['obj'],tool._objs[group]['obj'],
                     fcl.DistanceRequest(enable_nearest_points=True),result)
        return float(result.min_distance),*[np.asarray(p) for p in result.nearest_points]

    seed=np.r_[np.zeros(6),[q0[n] for n in drivers]]
    _,_,seed_transforms=coordinates(seed)
    for pair, axial in itertools.product(pairs,axial_targets):
        set_hand(hand,'right',q0,palm0)
        features=[];targets=[];normals=[]
        for name,side,sign in zip(pair,['negative','positive'],[1.,-1.]):
            gap,point,tool_point=distance(name,side)
            assert gap>0
            tf=seed_transforms[name]
            features.append((tf[:3,:3].T@(point-tf[:3,3]),tf[:3,:3].T@((tool_point-point)/gap)))
            # Surface point is queried from the actual rest mesh, not an
            # invented rectangular tool cross-section.
            surface,_,_=trimesh.proximity.closest_point(tool_meshes[side],[[axial,-sign*.05,.00575]])
            inward=np.array([0.,sign,0.]);targets.append(surface[0]-.0003*inward);normals.append(inward)

        def residual(x):
            _,_,transforms=coordinates(x);values=[]
            for name,(point,normal),target,inward in zip(pair,features,targets,normals):
                tf=transforms[name]
                values.extend((tf[:3,:3]@point+tf[:3,3]-target)/.001)
                values.extend((tf[:3,:3]@normal-inward)*2.)
            for name,tf in transforms.items():
                placed=world_from_source@tf
                clearance=(vertices[name]@placed[2,:3]+placed[2,3]).min()
                values.append(min(0.,clearance-.0012)/.001)
            values.extend((x-seed)*.025)
            return np.asarray(values)

        solution=least_squares(residual,seed,bounds=bounds,max_nfev=160,
                               diff_step=1e-5,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        q,palm,transforms=coordinates(solution.x)
        set_hand(hand,'right',q,palm)
        _,tool_pairs=hand.in_collision_other(tool,return_names=True)
        _,self_pairs=hand.in_collision_internal(return_names=True)
        self_pairs=[sorted(p) for p in self_pairs if tuple(sorted(p)) not in adjacent]
        clearance=min(float((vertices[n]@(world_from_source@tf)[2,:3]+(world_from_source@tf)[2,3]).min())
                      for n,tf in transforms.items())
        contacts=[]
        for name,side,sign in zip(pair,['negative','positive'],[1.,-1.]):
            gap,a,b=distance(name,side)
            contacts.append(dict(pad=name,arm=side,clearance_m=gap,
                inward_component=float(sign*(b-a)[1]/max(gap,1e-12)),tool_point_m=b.tolist()))
        alignment=np.abs(np.asarray(contacts[0]['tool_point_m'])-contacts[1]['tool_point_m'])
        values=dict(q)
        for joint in KIN['joints']:
            if joint.get('mimic'):
                m=joint['mimic'];values[joint['name']]=float(m.get('offset',0))+float(m.get('multiplier',1))*values.get(m['joint'],0)
        limits_ok=all(j['limits']['lower']<=values[j['name']]<=j['limits']['upper'] for j in KIN['joints']
                      if j.get('limits') and j['name'] in values)
        checks=dict(no_tool_intersections=not tool_pairs,no_nonadjacent_self_intersections=not self_pairs,
            support_clearance=clearance>=.001,source_joint_limits=limits_ok,
            opposed_contact_clearance=all(.00002<c['clearance_m']<=.0005 for c in contacts),
            opposed_normals=all(c['inward_component']>=.7 for c in contacts),
            axial_contact_alignment=alignment[0]<=.002,height_contact_alignment=alignment[2]<=.002)
        record=dict(q=q,source_tool_from_palm=palm.tolist(),contacts=contacts,
            maximum_pad_clearance_m=max(c['clearance_m'] for c in contacts),
            hand_support_clearance_m=clearance,source_joint_limits_ok=limits_ok,
            contact_axial_offset_m=float(alignment[0]),contact_height_offset_m=float(alignment[2]),
            target_axial_m=axial,contact_pair=pair,checks={k:bool(v) for k,v in checks.items()},
            tool_intersections=sorted([sorted(p) for p in tool_pairs]),self_intersections=self_pairs,
            solver_cost=float(solution.cost),solver_evaluations=int(solution.nfev))
        trials.append(record)
        if all(checks.values()):accepted.append(record)
        print(json.dumps(dict(trial=len(trials),pair=pair,axial=axial,checks=record['checks'],
                             contact_offsets_mm=(alignment[[0,2]]*1000).tolist(),clearance_mm=clearance*1000)),flush=True)
        (output/'trials.json').write_text(json.dumps(trials,indent=2)+'\n')
    accepted.sort(key=lambda r:r['contact_axial_offset_m']+r['contact_height_offset_m'])
    result=dict(scope=__doc__,passed_local_pad_geometry=bool(accepted),candidates=accepted,
        nearest_candidates=sorted(trials,key=lambda r:r['solver_cost'])[:20],tested=len(trials),
        seconds=time.monotonic()-started,contract_sha256=sha(output/'contract.json'),qualified_robot_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(tested=len(trials),accepted=len(accepted),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fit');p.add_argument('output');a=p.parse_args()
    run(a.fit,a.output)
