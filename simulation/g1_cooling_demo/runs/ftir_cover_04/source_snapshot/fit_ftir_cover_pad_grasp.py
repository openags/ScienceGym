"""Search object-relative cover grasps that actually contact tactile pads.

The earlier authored fit allowed any index/thumb mesh to be nearest the bar.
This offline search requires the distal tactile pad meshes themselves. Scene
placement and recorded plant poses are not used to produce the candidates.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

import fcl
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'viewer/cooling_concept_v2'))
from source_geometry import fk,robot_meshes,KIN
from cary_distal_hand import distal_hand_manager


def search(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    meshes=robot_meshes('right');names=['right_index_force_sensor_3','right_thumb_force_sensor_4']
    centers=[meshes[n].centroid for n in names]
    preset={f'right_{f}_1_joint':1.1 for f in ['middle','ring','little']}
    configurations=[]
    for index,thumb1,thumb2 in itertools.product(np.linspace(.4,1.15,31),np.linspace(.5,1.3,17),np.linspace(0,.45,31)):
        q=dict(preset,right_index_1_joint=float(index),right_thumb_1_joint=float(thumb1),right_thumb_2_joint=float(thumb2))
        world=fk(q);inverse=np.linalg.inv(world['right_palm_force_sensor']);pads=[inverse@world[n] for n in names]
        points=[(T@np.r_[c,1])[:3] for T,c in zip(pads,centers)];gap=points[1]-points[0];length=np.linalg.norm(gap)
        if not .008<length<.015:continue
        gap/=length;normals=[T[:3,2] for T in pads];a=normals[0]@gap;b=-normals[1]@gap
        if normals[0]@normals[1]>-.6 or not (min(a,b)>.5 or max(a,b)<-.5):continue
        configurations.append(dict(q=q,points=points,length=length,facing=[float(a),float(b)],
                                   score=abs(length-.0105)+.002*(2-abs(a)-abs(b))))
    configurations.sort(key=lambda r:r['score'])
    print('pad_configurations',len(configurations),flush=True)
    revision=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json'
    geometry=ROOT/json.loads(revision.read_text())['geometry_override']['path']
    scene=trimesh.load(geometry,force='scene',process=False)
    bar_T,bar_mesh=scene.graph['lid_handle_bar'];bar=scene.geometry[bar_mesh].copy();bar.apply_transform(bar_T);origin=bar.centroid
    obstacles=trimesh.collision.CollisionManager()
    for name in scene.graph.nodes_geometry:
        T,key=scene.graph[name];T=T.copy();T[:3,3]-=origin;obstacles.add_object(name,scene.geometry[key],T)
    target=obstacles._objs['lid_handle_bar']['obj'];hand=distal_hand_manager('right')
    graph=defaultdict(list)
    for joint in KIN['joints']:
        weight=int(joint['type']=='revolute');graph[joint['parent']].append((joint['id'],weight));graph[joint['id']].append((joint['parent'],weight))
    adjacent=set()
    for link in hand._objs:
        pending=[(link,None,0)]
        while pending:
            name,parent,depth=pending.pop()
            if depth>1:continue
            if name in hand._objs:adjacent.add(tuple(sorted((name,link))))
            pending.extend((n,name,depth+w) for n,w in graph[name] if n!=parent)
    tested=0;records=[];near=[]
    for ci,config in enumerate(configurations[:160]):
        q=config['q'];world=fk(q);inverse=np.linalg.inv(world['right_palm_force_sensor']);local={n:inverse@world[n] for n in hand._objs}
        for name,T in local.items():hand.set_transform(name,T)
        _,pairs=hand.in_collision_internal(return_names=True)
        if any(tuple(sorted(p)) not in adjacent for p in pairs):continue
        middle=np.mean(config['points'],axis=0);gap=config['points'][1]-config['points'][0];gap/=np.linalg.norm(gap)
        toward=middle-gap*(middle@gap);toward/=np.linalg.norm(toward);basis=np.column_stack([gap,toward,np.cross(gap,toward)])
        for tilt,sign,bias in itertools.product(np.linspace(-.8,.8,9),[-1,1],np.linspace(-.002,.002,9)):
            normal=np.array([0.,0,sign]);direction=np.array([np.sin(tilt),np.cos(tilt),0])
            rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@basis.T
            palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=-rotation@middle+normal*bias
            for name,T in local.items():hand.set_transform(name,palm@T)
            tested+=1
            # Source triangle distance, not distance to a whole-finger hull.
            distances=[];contacts=[]
            for name in names:
                result=fcl.DistanceResult();fcl.distance(hand._objs[name]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),result)
                distances.append(float(result.min_distance));contacts.append(np.asarray(result.nearest_points[1]))
            if min(distances)<1e-6 or max(distances)>.002:continue
            radial=[p[1:] for p in contacts];opposition=float(radial[0]@radial[1]/max(1e-12,np.linalg.norm(radial[0])*np.linalg.norm(radial[1])))
            if opposition>-.5:continue
            if hand.in_collision_other(obstacles):continue
            record=dict(q=q,handle_frame_from_palm=palm.tolist(),pad_parts=names,pad_gaps_m=distances,
                        opposition_dot=opposition,tilt_rad=float(tilt),sign=sign,bias_m=float(bias))
            near.append(record)
            if max(distances)<.0005:records.append(record)
        if ci%20==0:print('pad_fit',ci,'tested',tested,'near',len(near),'accepted',len(records),flush=True)
    near.sort(key=lambda r:max(r['pad_gaps_m']));records.sort(key=lambda r:max(r['pad_gaps_m']))
    report=dict(scope=__doc__,configuration_candidates=len(configurations),tested=tested,
                candidates=records,near_candidates=near[:100],seconds=time.monotonic()-started,
                geometry_sha256=hashlib.sha256(geometry.read_bytes()).hexdigest(),
                builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                limitations=['Local source-hand/instrument geometry only.',
                             'Whole-body reach, compiled contact model, forces and execution still require review.'])
    (out/'pad_grasps.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(accepted=len(records),near=len(near),seconds=report['seconds'],best=near[:2])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);a=parser.parse_args();search(a.out)
