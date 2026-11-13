"""Refine a heel-support grasp with a free wrist orientation and original assets.

The planar fit fixes the tool axis to the wrist axis. Here all seven source hand
joints and a bounded six-dimensional wrist adjustment can change. Tray clearance
is an optimization objective and is independently checked with original meshes;
there is no object movement, contact filtering or dynamic execution credit.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import time

import fcl
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import trimesh

from fit_dex3_tweezer import ROOT, SOURCE, TOOL, SourceHand, NAMES, PARTS, digest, exposed_points, load_support, profile


def run(fit_path, output, seeds=3):
    started=time.monotonic()
    fit_path,output=Path(fit_path).resolve(),Path(output).resolve()
    fit=json.loads(fit_path.read_text());fc=json.loads((fit_path.parent/'contract.json').read_text())
    assert fit['contract_sha256']==digest(fit_path.parent/'contract.json')
    assert fc['middle_finger_rigid_heel_support'] and fc.get('thumb_source_tool_y_side',-1)==-1
    for name,h in fc['source_hashes'].items(): assert digest(ROOT/name)==h,name
    support_path=TOOL/'tray_support_12/review.json'
    _,W,obstacles,receipt=load_support(support_path,ROOT)
    supported=json.loads(support_path.read_text())
    tm=mujoco.MjModel.from_xml_path(str(support_path.parent/'support.xml'));td=mujoco.MjData(tm)
    td.qpos[:]=supported['full_final_qpos'];mujoco.mj_forward(tm,td)
    tool_bodies={tm.body('tweezer').id}
    for b in range(tm.nbody):
        if int(tm.body_parentid[b]) in tool_bodies:tool_bodies.add(b)
    groups=defaultdict(list)
    for g in range(tm.ngeom):
        if int(tm.geom_bodyid[g]) not in tool_bodies or not (tm.geom_contype[g] or tm.geom_conaffinity[g]):continue
        if tm.geom_type[g]==mujoco.mjtGeom.mjGEOM_MESH:
            k=tm.geom_dataid[g]
            mesh=trimesh.Trimesh(vertices=tm.mesh_vert[tm.mesh_vertadr[k]:tm.mesh_vertadr[k]+tm.mesh_vertnum[k]].copy(),
                faces=tm.mesh_face[tm.mesh_faceadr[k]:tm.mesh_faceadr[k]+tm.mesh_facenum[k]].copy(),process=False)
        elif tm.geom_type[g]==mujoco.mjtGeom.mjGEOM_BOX:mesh=trimesh.creation.box(extents=2*tm.geom_size[g])
        else:raise ValueError('Unexpected source tool primitive')
        T=np.eye(4);T[:3,:3]=td.geom_xmat[g].reshape(3,3);T[:3,3]=td.geom_xpos[g]
        mesh.apply_transform(np.linalg.inv(W)@T)
        name=tm.geom(g).name
        groups['negative' if name.startswith('negative') else 'positive' if name.startswith('positive') else 'heel'].append(mesh)
    meshes={k:trimesh.util.concatenate(v) for k,v in groups.items()}
    tool=trimesh.collision.CollisionManager()
    for n,mesh in meshes.items():tool.add_object(n,mesh)
    heel_bounds=meshes['heel'].bounds
    hand=SourceHand();sm=mujoco.MjModel.from_xml_path(str(fit_path.parent/'hand_self_check.xml'));sd=mujoco.MjData(sm)
    scale=json.loads((TOOL/'revisions/passive_07/model_review.json').read_text())['inferred_interior_thickness_scale']
    features={n:[x for x in exposed_points(hand.meshes[n],1 if 'thumb' in n else 0) if x['side']==1] for n in PARTS}
    trials=json.loads((fit_path.parent/'trials.json').read_text())
    choices=sorted([(i,r) for i,r in enumerate(trials) if all(v for k,v in r['checks'].items() if k!='tray_clearance')],key=lambda x:x[1]['cost'])
    selected=[];seen=set()
    for index,row in choices:
        key=tuple(row['feature_lengths_m'])
        if key in seen:continue
        seen.add(key);selected.append((index,row))
        if len(selected)>=seeds:break
    assert selected
    output.mkdir(parents=True,exist_ok=False);snap=output/'source_snapshot';snap.mkdir()
    for p in [Path(__file__),Path(__file__).with_name('fit_dex3_tweezer.py'),SOURCE/'fit_cover_grasp.py',TOOL/'support_geometry.py',TOOL/'build_passive.py']:
        shutil.copyfile(p,snap/p.name)
    contract=dict(scope=__doc__,support_review=str(support_path.relative_to(ROOT)),support=receipt,
        source_hashes={str(p.relative_to(ROOT)):digest(p) for p in [fit_path,fit_path.parent/'contract.json',fit_path.parent/'trials.json',
                      fit_path.parent/'hand_self_check.xml',support_path,support_path.parent/'support.xml',*snap.iterdir()]},
        minimum_gap_m=.00002,maximum_gap_m=.0006,minimum_normal_opposition=.75,
        minimum_support_clearance_m=.001,maximum_compiled_self_penetration_m=.00002,
        middle_finger_rigid_heel_support=True,thumb_source_tool_y_side=-1,
        wrist_translation_adjustment_bound_m=.03,wrist_rotvec_adjustment_component_bound_rad=.5,
        source_joints_preserved=True,initial_tool_placement_unchanged=True,full_body_checked=False)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    rows=[];accepted=[]
    for seed_index,(original_index,original) in enumerate(selected):
        S0=np.asarray(original['source_tool_from_wrist'])
        chosen=[min(features[n],key=lambda x:abs(x['longitudinal_m']-length)) for n,length in zip(PARTS,original['feature_lengths_m'])]
        points=[np.asarray(x['point_m']) for x in chosen];normals=[np.asarray(x['normal']) for x in chosen]
        def state(x):
            S=S0.copy();S[:3,:3]=Rotation.from_rotvec(x[10:13]).as_matrix()@S0[:3,:3];S[:3,3]+=x[7:10]
            transforms={n:S@T for n,T in hand.forward(x[:7]).items()}
            for n,T in transforms.items():hand.manager.set_transform(n,T)
            return S,transforms
        def residual(x):
            _,transforms=state(x);values=[]
            for n,p,normal,sign in zip(PARTS,points,normals,[-1,1,1]):
                T=transforms[n];a=T[:3,:3]@p+T[:3,3]
                if n==PARTS[2]:
                    outer=heel_bounds[1,1];zmin,zmax=heel_bounds[:,2]+[.0006,-.0006]
                    values.extend([(a[0]-heel_bounds[:,0].mean())/.001,0.])
                else:
                    _,thick,center=profile(a[0],scale);outer=center+thick/2
                    zmin,zmax=.00325,.00825
                    values.extend([min(0.,a[0]-.025)/.001,max(0.,a[0]-.115)/.001])
                values.append((a[1]-sign*(outer+.0003))/.001)
                values.extend([min(0.,a[2]-zmin)/.001,max(0.,a[2]-zmax)/.001])
                values.extend(.25*(T[:3,:3]@normal-np.array([0.,-sign,0.])))
            gap=float(hand.manager.min_distance_other(obstacles))
            values.append(2.*min(0.,gap-.0013)/.001)
            return np.r_[values,.005*x[7:10]/.01,.005*x[10:13]]
        x0=np.r_[[original['q'][n] for n in NAMES],np.zeros(6)]
        low=np.r_[[hand.limits[n]['intersection'][0]+.001 for n in NAMES],[-.03]*3,[-.5]*3]
        high=np.r_[[hand.limits[n]['intersection'][1]-.001 for n in NAMES],[.03]*3,[.5]*3]
        result=least_squares(residual,np.clip(x0,low,high),bounds=(low,high),max_nfev=120,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        S,transforms=state(result.x)
        _,tool_pairs=hand.manager.in_collision_other(tool,return_names=True)
        _,tray_pairs=hand.manager.in_collision_other(obstacles,return_names=True)
        tray_gap=float(hand.manager.min_distance_other(obstacles))
        for n,v in zip(NAMES,result.x[:7]):sd.joint(n).qpos[0]=v
        mujoco.mj_forward(sm,sd)
        self_contacts=[dict(parts=[sm.body(sm.geom_bodyid[g]).name for g in c.geom],distance_m=float(c.dist)) for c in sd.contact if c.dist<-.00002]
        contacts=[]
        for n,side,sign in zip(PARTS,['negative','positive','heel'],[-1,1,1]):
            distance=fcl.DistanceResult();fcl.distance(hand.manager._objs[n]['obj'],tool._objs[side]['obj'],fcl.DistanceRequest(enable_nearest_points=True),distance)
            a,b=map(np.asarray,distance.nearest_points);gap=float(distance.min_distance)
            contacts.append(dict(part=n,side=side,gap_m=gap,point_source_m=b.tolist(),
                point_hand_local_m=(np.linalg.inv(transforms[n])@np.r_[a,1])[:3].tolist(),inward_component=float(-sign*(b-a)[1]/max(gap,1e-12))))
        plane_gap=min(float((mesh.vertices@(W@transforms[n])[:3,:3].T+(W@transforms[n])[:3,3])[:,2].min()) for n,mesh in hand.meshes.items())
        xs=[c['point_source_m'][0] for c in contacts]
        checks=dict(no_tool_intersections=not tool_pairs,official_self_contact_clear=not self_contacts,
            triple_contact_clearance=all(.00002<c['gap_m']<.0006 for c in contacts),contact_normals=all(c['inward_component']>.75 for c in contacts),
            axial_support_brackets_thumb=min(xs[1:])+.005<xs[0]<max(xs[1:])-.005,
            hand_above_plane=plane_gap>.001,tray_clearance=not tray_pairs and tray_gap>.001)
        row=dict(q=dict(zip(NAMES,map(float,result.x[:7]))),source_tool_from_wrist=S.tolist(),contacts=contacts,
            checks={k:bool(v) for k,v in checks.items()},tray_gap_m=tray_gap,support_plane_clearance_m=plane_gap,
            tool_intersections=[list(x) for x in sorted(tool_pairs)],tray_intersections=[list(x) for x in sorted(tray_pairs)],
            compiled_self_contacts=self_contacts,seed_trial_index=original_index,cost=float(result.cost),evaluations=int(result.nfev),
            feature_lengths_m=original['feature_lengths_m'],wrist_adjustment=result.x[7:].tolist())
        rows.append(row)
        if all(checks.values()):accepted.append(row)
        (output/'trials.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(json.dumps(dict(seed=seed_index,accepted=len(accepted),checks=row['checks'],tray_gap_m=tray_gap,seconds=time.monotonic()-started)),flush=True)
    report=dict(scope=__doc__,candidates=accepted,nearest_candidates=rows,tested=len(rows),accepted_count=len(accepted),
        contract_sha256=digest(output/'contract.json'),seconds=time.monotonic()-started,qualified_grasp=False,full_body_checked=False)
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['tested','accepted_count','seconds']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fit');p.add_argument('output');p.add_argument('--seeds',type=int,default=3)
    a=p.parse_args();run(a.fit,a.output,a.seeds)
