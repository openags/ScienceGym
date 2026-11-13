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
from support_geometry import load_support


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(fit,output,pregrasp_index=None):
    fit,output=Path(fit).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,output/Path(__file__).name)
    shutil.copyfile(Path(__file__).with_name('support_geometry.py'),output/'support_geometry.py')
    original=json.loads(fit.read_text())
    if pregrasp_index is None:assert original['passed_local_pad_geometry']
    previous=json.loads((fit.parent/'contract.json').read_text())
    assert sha(fit.parent/'contract.json')==original['contract_sha256']
    support_path=ROOT/previous['support_review']
    assert sha(support_path)==previous['support_review_sha256']
    initial,world_from_source,obstacles,support_receipt=load_support(support_path,ROOT)
    (output/'support_geometry.json').write_text(json.dumps(support_receipt,indent=2)+'\n')
    source_path=next(ROOT/p for p in previous['source_hashes'] if p.endswith('/rest_geometry.glb'))
    assert sha(source_path)==previous['source_hashes'][str(source_path.relative_to(ROOT))]
    source=trimesh.load(source_path,force='scene',process=False);parts=defaultdict(list)
    for n in source.graph.nodes_geometry:
        t,key=source.graph[n];mesh=source.geometry[key].copy();mesh.apply_transform(t)
        parts['positive' if n.startswith('positive_') else 'negative' if n.startswith('negative_') else 'heel'].append(mesh)
    tool=trimesh.collision.CollisionManager()
    for n,v in parts.items():tool.add_object(n,trimesh.util.concatenate(v))
    hand=distal_hand_manager('right');meshes=robot_meshes()
    candidate=original['candidates'][0] if pregrasp_index is None else original['nearest_candidates'][pregrasp_index]
    palm=np.asarray(candidate['source_tool_from_palm'])
    graph=defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for n in hand._objs:
        queue=[(n,None,0)]
        while queue:
            link,parent,depth=queue.pop()
            if depth>1:continue
            adjacent.add(tuple(sorted([n,link])))
            queue.extend((child,link,depth+w) for child,w in graph[link] if child!=parent)
    limits=next(j['limits'] for j in KIN['joints'] if j['name']=='right_middle_1_joint')
    values=np.linspace(limits['lower'],limits['upper'],41)
    contract=dict(scope=__doc__,fit_sha256=sha(fit),source_geometry_sha256=sha(source_path),
        pregrasp_index=pregrasp_index,static_pinch_acceptance_claimed=pregrasp_index is None,
        support_geometry_sha256=sha(output/'support_geometry.json'),
        support_review_sha256=sha(support_path),script_sha256=sha(__file__),
        middle_joint_angles_rad=values.tolist(),other_joints=candidate['q'],
        source_tool_from_palm=palm.tolist(),minimum_plane_clearance_m=.001)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    rows=[]
    for value in values:
        q=dict(candidate['q']);q['right_middle_1_joint']=float(value)
        set_hand(hand,'right',q,palm)
        _,pairs=hand.in_collision_other(tool,return_names=True)
        obstacle_pairs=set()
        if obstacles:_,obstacle_pairs=hand.in_collision_other(obstacles,return_names=True)
        _,self_pairs=hand.in_collision_internal(return_names=True)
        self_pairs=[sorted(p) for p in self_pairs if tuple(sorted(p)) not in adjacent]
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
                tf=palm@inv@world[n];point=tf[:3,:3].T@(a-tf[:3,3])
                shifted=dict(q);shifted['right_middle_1_joint']+=1e-5
                after=fk(shifted);after=palm@np.linalg.inv(after['right_palm_force_sensor'])@after[n]
                velocity=(after[:3,:3]@point+after[:3,3]-a)/1e-5
                nearest.append(dict(body=n,arm=side,gap_m=d,inward_normal_component=float(sign*(b-a)[1]/max(d,1e-12)),
                                    source_tool_point_m=b.tolist(),contact_direction=((b-a)/max(d,1e-12)).tolist(),
                                    middle_closure_velocity_m_rad=velocity.tolist()))
        nearest.sort(key=lambda r:r['gap_m'])
        rows.append(dict(middle_joint_angle_rad=float(value),support_plane_clearance_m=plane,
                         hand_tool_intersections=sorted([list(p) for p in pairs]),nearest_middle_contacts=nearest[:4],
                         hand_support_intersections=sorted([sorted(p) for p in obstacle_pairs]),
                         nonadjacent_self_intersections=self_pairs))
    result=dict(scope=__doc__,contract_sha256=sha(output/'contract.json'),samples=rows,
                qualified_robot_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    clear=[r for r in rows if not r['hand_tool_intersections'] and not r['hand_support_intersections']
           and not r['nonadjacent_self_intersections'] and r['support_plane_clearance_m']>=.001]
    clear.sort(key=lambda r:r['nearest_middle_contacts'][0]['gap_m'])
    print(json.dumps(dict(samples=len(rows),collision_free_above_plane=len(clear),nearest_clear=clear[:2])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fit');p.add_argument('output');p.add_argument('--pregrasp-index',type=int)
    a=p.parse_args();run(a.fit,a.output,a.pregrasp_index)
