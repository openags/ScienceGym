"""Fit source-relative cover grasps with margin inside the exposed pad faces.

The old minimum-distance objective could choose a pad edge. This search aims
the central +Z source surface at the cylindrical handle, then independently
checks exact triangle distances, projected margins and whole-hand clearance.
The selected exposed CAD surface is a planning region, not a vendor tactile
calibration. Neither scene placement nor recorded plant state enters the fit.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time

import fcl
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import trimesh

from fit_ftir_cover_pad_grasp import ROOT, KIN, fk, robot_meshes, distal_hand_manager, source_limits_ok


def search(seed_file, out, trials=48):
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    prior=json.loads(Path(seed_file).read_text());seed=np.array(prior['handle_frame_from_palm'])
    fixed=dict(prior['nominal_grip_q']);names=prior['pad_grasp']['pad_parts'];meshes=robot_meshes('right')
    centers={};normals={};boundaries={};samples={};metric_meshes={}
    for name in names:
        mesh=meshes[name];probe=mesh.bounds.mean(axis=0);probe[2]=mesh.bounds[1,2]+.01
        metric_meshes[name]=mesh.copy();metric_meshes[name].apply_scale(1000.)
        point,_,face=trimesh.proximity.closest_point(metric_meshes[name],[probe*1000.])
        centers[name]=point[0]/1000.;normals[name]=mesh.face_normals[face[0]]
        if normals[name][2]<.5:raise ValueError('The central source surface is not exposed toward +Z')
        exposed=mesh.vertices[np.unique(mesh.faces[mesh.face_normals[:,2]>.5])]
        boundaries[name]=ConvexHull(exposed[:,:2]).equations
        samples[name]=np.vstack([mesh.vertices,mesh.triangles_center,mesh.vertices[mesh.edges_unique].mean(axis=1)])
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
    joints=['right_index_1_joint','right_thumb_1_joint','right_thumb_2_joint']
    x0=np.r_[[fixed[n] for n in joints],np.zeros(6)]
    low=np.array([.45,.60,.05,-.012,-.012,-.012,-.4,-.4,-.4])
    high=np.array([1.10,1.1591,.42,.012,.012,.012,.4,.4,.4])
    def pose(x):
        q=dict(fixed,**dict(zip(joints,map(float,x[:3]))));palm=seed.copy()
        palm[:3,3]+=x[3:6];palm[:3,:3]=Rotation.from_rotvec(x[6:9]).as_matrix()@seed[:3,:3]
        world=fk(q);base=palm@np.linalg.inv(world['right_palm_force_sensor'])
        return q,palm,{n:base@world[n] for n in hand._objs}
    def residual(x):
        _,_,transforms=pose(x);result=[];radials=[]
        for name in names:
            T=transforms[name];point=T[:3,:3]@centers[name]+T[:3,3]
            radial=np.r_[0.,point[1:]];radius=np.linalg.norm(radial);radial/=max(radius,1e-9)
            normal=T[:3,:3]@normals[name];radials.append(radial)
            surface=samples[name]@T[:3,:3].T+T[:3,3]
            closest_radius=float(np.min(np.linalg.norm(surface[:,1:],axis=1)))
            result.extend([2000*(closest_radius-.0043),*list(2*(normal+radial)),100*max(0.,abs(point[0])-.030)])
        result.extend([max(0.,radials[0]@radials[1]+.95),*list(.002*(x[:3]-x0[:3])),*list(.2*x[3:6]),*list(.005*x[6:])])
        return result
    rng=np.random.default_rng(846);records=[];rejected=[];seen=set()
    for trial in range(trials):
        initial=x0 if trial==0 else x0+rng.normal(size=9)*[.06,.07,.04,.003,.003,.003,.10,.10,.10]
        initial=np.clip(initial,low+1e-7,high-1e-7)
        solution=least_squares(residual,initial,bounds=(low,high),max_nfev=180,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        q,palm,transforms=pose(solution.x);closed=dict(q)
        for n in [joints[0],joints[2]]:closed[n]+=.08
        if not source_limits_ok(q) or not source_limits_ok(closed):raise AssertionError('Candidate escaped source limits')
        for name,T in transforms.items():hand.set_transform(name,T)
        distances=[];points=[];margins=[];exposed=[];local_points=[]
        for name in names:
            result=fcl.DistanceResult();fcl.distance(hand._objs[name]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),result)
            distances.append(float(result.min_distance));points.append(np.asarray(result.nearest_points[1])[1:])
            local=(np.linalg.inv(transforms[name])@np.r_[result.nearest_points[0],1.])[:3];local_points.append(local.tolist())
            _,_,face=trimesh.proximity.closest_point(metric_meshes[name],[local*1000.]);exposed.append(bool(meshes[name].face_normals[face[0],2]>.5))
            boundary=boundaries[name];margins.append(float(np.min(-(boundary[:,:2]@local[:2]+boundary[:,2]))))
        opposed=float(points[0]@points[1]/max(np.linalg.norm(points[0])*np.linalg.norm(points[1]),1e-12))
        _,pairs=hand.in_collision_internal(return_names=True);self_pairs=[sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent]
        _,environment_pairs=hand.in_collision_other(obstacles,return_names=True)
        passed=min(distances)>.00005 and max(distances)<.0005 and min(margins)>.0005 and all(exposed) and opposed<-.8 and not self_pairs and not environment_pairs
        row=dict(trial=trial,q=q,handle_frame_from_palm=palm.tolist(),pad_parts=names,pad_gaps_m=distances,
                 opposition_dot=opposed,projected_pad_margin_m=margins,pad_exposed_contact=exposed,
                 pad_local_contact_m=local_points,self_contact_pairs=self_pairs,instrument_contact_pairs=[list(p) for p in sorted(environment_pairs)],
                 optimization_cost=float(solution.cost),evaluations=int(solution.nfev))
        key=tuple(np.round(solution.x,6))
        if passed and key not in seen:records.append(row);seen.add(key)
        else:rejected.append(row)
        print('center_fit',trial,'accepted',len(records),'margins_mm',np.round(np.array(margins)*1000,3).tolist(),
              'gaps_mm',np.round(np.array(distances)*1000,3).tolist(),'self',len(self_pairs),'case',len(environment_pairs),flush=True)
    records.sort(key=lambda r:-min(r['projected_pad_margin_m']))
    report=dict(scope=__doc__,candidates=records,rejected=rejected,source_limits_checked=True,seconds=time.monotonic()-started,
                central_source_points_m={n:p.tolist() for n,p in centers.items()},minimum_projected_margin_m=.0005,
                seed_sha256=hashlib.sha256(Path(seed_file).read_bytes()).hexdigest(),geometry_sha256=hashlib.sha256(geometry.read_bytes()).hexdigest(),
                builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),qualified=False)
    (out/'pad_grasps.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',required=True);p.add_argument('--out',required=True);p.add_argument('--trials',type=int,default=48)
    a=p.parse_args();search(a.seed,a.out,a.trials)
