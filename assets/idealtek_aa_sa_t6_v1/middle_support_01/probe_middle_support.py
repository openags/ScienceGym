"""Inspect a third source finger as support for a free-tool grasp candidate.

Offline geometry only. The tool and finger positions are authoring inputs,
not actor observations. No fixture, altered hand or physical success is added.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys

import fcl
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'viewer/cooling_concept_v2'))
from cary_distal_hand import distal_hand_manager
from source_geometry import fk,set_hand,robot_meshes,KIN


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(fit,output):
    fit,output=Path(fit).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,output/Path(__file__).name)
    original=json.loads(fit.read_text())
    assert original['passed_local_pad_geometry']
    previous=json.loads((fit.parent/'contract.json').read_text())
    assert sha(fit.parent/'contract.json')==original['contract_sha256']
    support_path=ROOT/previous['support_review']
    assert sha(support_path)==previous['support_review_sha256']
    support=json.loads(support_path.read_text());assert support['passed']
    source_path=next(ROOT/p for p in previous['source_hashes'] if p.endswith('/rest_geometry.glb'))
    assert sha(source_path)==previous['source_hashes'][str(source_path.relative_to(ROOT))]
    source=trimesh.load(source_path,force='scene',process=False);parts=defaultdict(list)
    for n in source.graph.nodes_geometry:
        t,key=source.graph[n];mesh=source.geometry[key].copy();mesh.apply_transform(t)
        parts['positive' if n.startswith('positive_') else 'negative' if n.startswith('negative_') else 'heel'].append(mesh)
    tool=trimesh.collision.CollisionManager()
    for n,v in parts.items():tool.add_object(n,trimesh.util.concatenate(v))
    hand=distal_hand_manager('right');meshes=robot_meshes()
    initial=np.asarray(support['final_qpos']);world_from_source=np.eye(4)
    world_from_source[:3,:3]=Rotation.from_quat(np.r_[initial[4:7],initial[3]]).as_matrix()
    world_from_source[:3,3]=initial[:3]-world_from_source[:3,:3]@np.array([.13,0,.00575])
    candidate=original['candidates'][0];palm=np.asarray(candidate['source_tool_from_palm'])
    limits=next(j['limits'] for j in KIN['joints'] if j['name']=='right_middle_1_joint')
    values=np.linspace(limits['lower'],limits['upper'],41)
    contract=dict(scope=__doc__,fit_sha256=sha(fit),source_geometry_sha256=sha(source_path),
        support_review_sha256=sha(support_path),script_sha256=sha(__file__),
        middle_joint_angles_rad=values.tolist(),other_joints=candidate['q'],
        source_tool_from_palm=palm.tolist(),minimum_plane_clearance_m=.001)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    rows=[]
    for value in values:
        q=dict(candidate['q']);q['right_middle_1_joint']=float(value)
        set_hand(hand,'right',q,palm)
        _,pairs=hand.in_collision_other(tool,return_names=True)
        world=fk(q);inv=np.linalg.inv(world['right_palm_force_sensor'])
        plane=float('inf')
        for n in hand._objs:
            transform=world_from_source@palm@inv@world[n]
            plane=min(plane,float((meshes[n].vertices@transform[2,:3]+transform[2,3]).min()))
        nearest=[]
        for n in hand._objs:
            if not n.startswith('right_middle'):continue
            for side,sign in [('negative',1),('positive',-1)]:
                result=fcl.DistanceResult()
                fcl.distance(hand._objs[n]['obj'],tool._objs[side]['obj'],fcl.DistanceRequest(enable_nearest_points=True),result)
                d=float(result.min_distance);a,b=map(np.asarray,result.nearest_points)
                nearest.append(dict(body=n,arm=side,gap_m=d,inward_normal_component=float(sign*(b-a)[1]/max(d,1e-12)),
                                    source_tool_point_m=b.tolist()))
        nearest.sort(key=lambda r:r['gap_m'])
        rows.append(dict(middle_joint_angle_rad=float(value),support_plane_clearance_m=plane,
                         hand_tool_intersections=sorted([list(p) for p in pairs]),nearest_middle_contacts=nearest[:4]))
    result=dict(scope=__doc__,contract_sha256=sha(output/'contract.json'),samples=rows,
                qualified_robot_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    clear=[r for r in rows if not r['hand_tool_intersections'] and r['support_plane_clearance_m']>=.001]
    clear.sort(key=lambda r:r['nearest_middle_contacts'][0]['gap_m'])
    print(json.dumps(dict(samples=len(rows),collision_free_above_plane=len(clear),nearest_clear=clear[:2])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fit');p.add_argument('output');a=p.parse_args();run(a.fit,a.output)
