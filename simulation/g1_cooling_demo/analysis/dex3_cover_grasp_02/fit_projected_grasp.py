"""Refine Dex3 grasps using projected source surfaces, then exact meshes.

The handle axis stays parallel to the finger-joint axes in this initial family.
Projected hulls propose contacts only; FCL checks the unchanged source meshes.
Source assembly overlaps are reported, never silently accepted as task success.
"""
import argparse
import itertools
import json
from pathlib import Path
import time

import fcl
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
import trimesh

from fit_cover_grasp import HERE, NAMES, PARTS, SourceHand, digest, handle_mesh


def polygon_distance(point, polygon):
    edges = np.roll(polygon, -1, axis=0) - polygon
    u = np.clip(np.sum((point - polygon) * edges, axis=1) / np.sum(edges * edges, axis=1), 0, 1)
    nearest = polygon + u[:, None] * edges
    distances = np.linalg.norm(point - nearest, axis=1); i = int(np.argmin(distances))
    inside = np.all(edges[:, 0] * (point-polygon)[:, 1] - edges[:, 1] * (point-polygon)[:, 0] >= 0)
    return float(distances[i]) * (-1 if inside else 1), nearest[i]


def run(out, seed_file):
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    hand=SourceHand();bar,device_path,device_center=handle_mesh()
    targets=trimesh.collision.CollisionManager();targets.add_object('bar',bar)
    polygons={name: mesh.vertices[ConvexHull(mesh.vertices[:,:2]).vertices,:2] for name,mesh in hand.meshes.items() if name in PARTS}
    lower=[hand.limits[NAMES[i]]['intersection'][0]+.01 for i in [1,2,3,4]]+[.07,-.04]
    upper=[hand.limits[NAMES[i]]['intersection'][1]-.01 for i in [1,2,3,4]]+[.22,.13]
    old=json.loads(Path(seed_file).read_text())
    seeds=[]
    for r in sorted(old['rejected'],key=lambda r:r['cost']):
        x=np.r_[[r['q'][NAMES[i]] for i in [1,2,3,4]],r['bar_center_wrist_m'][:2]]
        if all(np.linalg.norm(x-y)>.1 for y in seeds):seeds.append(x)
    rng=np.random.default_rng(27029);seeds.extend(rng.uniform(lower,upper) for _ in range(12))
    rows=[]; trial=0
    for thumb_length,finger_length in itertools.product([.030,.038,.046],repeat=2):
        lengths=[thumb_length,finger_length,finger_length]
        def state(x,update=False):
            q=[0.,x[0],x[1],x[2],x[3],x[2],x[3]]
            return q,hand.forward(q,update)
        def residual(x):
            _,poses=state(x);res=[];normals=[]
            for name,length in zip(PARTS,lengths):
                T=poses[name];local=T[:2,:2].T@(x[4:6]-T[:2,3])
                distance,point=polygon_distance(local,polygons[name])
                direction=(local-point)/max(abs(distance),1e-9);normals.append(T[:2,:2]@direction)
                axis=1 if 'thumb' in name else 0
                res.extend([1000*(distance-.0043),100*(point[axis]-length)])
            return np.r_[res,3*(normals[0]+normals[1]),.0001*x[:4]]
        for initial in seeds:
            sol=least_squares(residual,np.clip(initial,lower,upper),bounds=(lower,upper),max_nfev=180,
                              ftol=1e-9,xtol=1e-9,gtol=1e-9)
            q,poses=state(sol.x,True);Tbar=np.eye(4);Tbar[:2,3]=sol.x[4:6];targets.set_transform('bar',Tbar)
            gaps=[];points=[];radials=[];central=[]
            for name in PARTS:
                d=fcl.DistanceResult();fcl.distance(hand.manager._objs[name]['obj'],targets._objs['bar']['obj'],
                    fcl.DistanceRequest(enable_nearest_points=True),d)
                gaps.append(float(d.min_distance));T=poses[name]
                local=T[:3,:3].T@(np.asarray(d.nearest_points[0])-T[:3,3]);points.append(local.tolist())
                radial=np.asarray(d.nearest_points[1])[:2]-sol.x[4:6];radial/=max(np.linalg.norm(radial),1e-12);radials.append(radial)
                axis=1 if 'thumb' in name else 0;central.append(bool(.025<=local[axis]<=.048 and abs(local[2])<=.009))
            _,self_pairs=hand.manager.in_collision_internal(return_names=True)
            self_pairs=[list(p) for p in sorted(self_pairs) if tuple(sorted(p)) not in hand.adjacent]
            _,bar_pairs=hand.manager.in_collision_other(targets,return_names=True)
            opposition=[float(radials[0]@r) for r in radials[1:]]
            hand.model.opt.disableflags &= ~int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
            mujoco.mj_forward(hand.model,hand.data)
            compiled=[dict(parts=[hand.model.body(hand.model.geom_bodyid[int(g)]).name for g in c.geom],distance_m=float(c.dist))
                      for c in hand.data.contact if c.dist < -2e-5]
            hand.model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
            local_bar_pass=min(gaps)>.00005 and max(gaps)<.0005 and all(central) and max(opposition)<-.8 and not bar_pairs
            rows.append(dict(trial=trial,q=dict(zip(NAMES,map(float,q))),bar_center_wrist_m=[*map(float,sol.x[4:6]),0.],
                             gap_m=gaps,contact_local_m=dict(zip(PARTS,points)),opposition_dot=opposition,
                             contacts_within_inferred_distal_region=central,self_collision_pairs=self_pairs,
                             bar_collision_pairs=[list(p) for p in sorted(bar_pairs)],
                             compiled_self_penetrations=compiled,local_bar_pass=bool(local_bar_pass),
                             all_source_geometry_pass=bool(local_bar_pass and not self_pairs and not compiled),
                             cost=float(sol.cost),evaluations=int(sol.nfev)))
            trial+=1
        print('lengths',thumb_length,finger_length,'trials',trial,'bar candidates',sum(r['local_bar_pass'] for r in rows),flush=True)
    report=dict(scope=__doc__,rows=rows,source_limits=hand.limits,
                bar_grasp_candidates=sum(r['local_bar_pass'] for r in rows),
                all_source_geometry_candidates=sum(r['all_source_geometry_pass'] for r in rows),
                source_json_sha256=digest(HERE/'source.json'),device_sha256=digest(device_path),
                builder_sha256=digest(__file__),dependency_sha256=digest(HERE/'fit_cover_grasp.py'),
                seed_sha256=digest(seed_file),seconds=time.monotonic()-started,
                full_instrument_checked=False,physics_qualified=False)
    (out/'grasps.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['bar_grasp_candidates','all_source_geometry_candidates','seconds']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',required=True)
    a=p.parse_args();run(a.out,a.seed)
