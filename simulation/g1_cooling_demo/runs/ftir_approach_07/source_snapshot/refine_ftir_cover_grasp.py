"""Refine a source-relative grasp within hand limits, preserving palm rotation.

The seed is geometry only, not a plant pose. Its invalid thumb-1 target is
replaced by an interior source-limit value before any optimization.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import time

import fcl
import numpy as np
from scipy.optimize import least_squares
import trimesh

from fit_ftir_cover_pad_grasp import ROOT, KIN, fk, robot_meshes, distal_hand_manager, source_limits_ok


def search(seed_file, out):
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    prior=json.loads(Path(seed_file).read_text());seed=np.array(prior['handle_frame_from_palm'])
    fixed=dict(prior['nominal_grip_q']);fixed['right_thumb_1_joint']=next(j['limits']['upper'] for j in KIN['joints'] if j['name']=='right_thumb_1_joint')-.005
    meshes=robot_meshes('right');names=['right_index_force_sensor_3','right_thumb_force_sensor_4']
    samples={n:np.vstack([meshes[n].vertices,meshes[n].triangles_center,meshes[n].vertices[meshes[n].edges_unique].mean(axis=1)]) for n in names}
    revision=json.loads((ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json').read_text())
    geometry=ROOT/revision['geometry_override']['path'];scene=trimesh.load(geometry,force='scene',process=False)
    T,key=scene.graph['lid_handle_bar'];bar=scene.geometry[key].copy();bar.apply_transform(T);origin=bar.centroid
    obstacles=trimesh.collision.CollisionManager()
    for name in scene.graph.nodes_geometry:
        T,key=scene.graph[name];T=T.copy();T[:3,3]-=origin;obstacles.add_object(name,scene.geometry[key],T)
    target=obstacles._objs['lid_handle_bar']['obj'];hand=distal_hand_manager('right')
    graph=defaultdict(list)
    for j in KIN['joints']:
        weight=int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
    adjacent=set()
    for link in hand._objs:
        pending=[(link,None,0)]
        while pending:
            n,parent,depth=pending.pop()
            if depth>1:continue
            if n in hand._objs:adjacent.add(tuple(sorted([n,link])))
            pending.extend((v,n,depth+w) for v,w in graph[n] if v!=parent)
    x0=np.array([fixed['right_index_1_joint'],fixed['right_thumb_2_joint'],0.,0.])
    low=np.array([.65,.15,-.008,-.008]);high=np.array([.95,.4,.008,.008])
    def pose(x):
        q=dict(fixed,right_index_1_joint=float(x[0]),right_thumb_2_joint=float(x[1]))
        palm=seed.copy();palm[1:3,3]+=x[2:4]
        world=fk(q);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
        return q,palm,{n:base@world[n] for n in hand._objs}
    def residual(x):
        _,_,transforms=pose(x);gaps=[];radials=[]
        for n in names:
            T=transforms[n];points=samples[n]@T[:3,:3].T+T[:3,3]
            radii=np.linalg.norm(points[:,1:],axis=1);i=np.argmin(radii)
            gaps.append(radii[i]-.004);radials.append(points[i,1:]/max(radii[i],1e-9))
        opposition=radials[0]@radials[1]
        return np.r_[2000*(np.array(gaps)-.0003),max(0.,opposition+.8),.002*(x[:2]-x0[:2]),.3*x[2:]]
    rng=np.random.default_rng(846);records=[];rejected=[];seen=set()
    for trial in range(32):
        initial=x0 if trial==0 else np.clip(x0+rng.normal(size=4)*[.035,.035,.003,.003],low+1e-6,high-1e-6)
        solution=least_squares(residual,initial,bounds=(low,high),max_nfev=120,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        q,palm,transforms=pose(solution.x)
        if not source_limits_ok(q) or not source_limits_ok(dict(q,right_index_1_joint=q['right_index_1_joint']+.08,right_thumb_2_joint=q['right_thumb_2_joint']+.08)):
            raise AssertionError('Refinement escaped source limits')
        for n,T in transforms.items():hand.set_transform(n,T)
        distances=[];points=[]
        for n in names:
            result=fcl.DistanceResult();fcl.distance(hand._objs[n]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),result)
            distances.append(float(result.min_distance));points.append(np.asarray(result.nearest_points[1])[1:])
        opposed=float(points[0]@points[1]/max(np.linalg.norm(points[0])*np.linalg.norm(points[1]),1e-12))
        _,pairs=hand.in_collision_internal(return_names=True);self_contact=any(tuple(sorted(p)) not in adjacent for p in pairs)
        environment_contact=hand.in_collision_other(obstacles)
        passed=min(distances)>.00005 and max(distances)<.0005 and opposed<-.8 and not self_contact and not environment_contact
        row=dict(trial=trial,q=q,handle_frame_from_palm=palm.tolist(),pad_parts=names,pad_gaps_m=distances,opposition_dot=opposed,
                 self_contact=self_contact,instrument_contact=environment_contact)
        key=tuple(np.round(solution.x,6))
        if passed and key not in seen:records.append(row);seen.add(key)
        else:rejected.append(row)
        print('refine',trial,'accepted',len(records),'gaps',distances,'self',self_contact,'case',environment_contact,flush=True)
    report=dict(scope=__doc__,candidates=records,rejected=rejected,source_limits_checked=True,seconds=time.monotonic()-started,
                seed_sha256=hashlib.sha256(Path(seed_file).read_bytes()).hexdigest(),geometry_sha256=hashlib.sha256(geometry.read_bytes()).hexdigest(),
                builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'pad_grasps.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',required=True);p.add_argument('--out',required=True);a=p.parse_args();search(a.seed,a.out)
