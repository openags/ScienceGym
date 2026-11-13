"""Check Dex3 bar candidates against the complete unchanged source FTIR.

All rolls are about the source handle axis, without moving or scaling the
instrument. The floating official robot checks its native hand self-colliders;
the fixed-wrist preview has different parent collision filtering and is not
used for this check. Raw visual assembly intersections remain explicit.
"""
import argparse
import json
from pathlib import Path
import time

import fcl
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from fit_cover_grasp import HERE, NAMES, SourceHand, digest, handle_mesh


def run(seed, out):
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    source=json.loads(Path(seed).read_text());hand=SourceHand();_,device_path,center=handle_mesh()
    scene=trimesh.load(device_path,force='scene',process=False);instrument=trimesh.collision.CollisionManager()
    for name in scene.graph.nodes_geometry:
        T,key=scene.graph[name];instrument.add_object(name,scene.geometry[key],T)
    full=mujoco.MjModel.from_xml_path(str(HERE/'g1_29dof_with_hand_rev_1_0.xml'));data=mujoco.MjData(full)
    hand_ids={int(mujoco.mj_name2id(full,mujoco.mjtObj.mjOBJ_BODY,name)) for name in set(hand.model.body(i).name for i in hand.body_ids.values())}
    candidates=[];rejected=[];assemblies=[];seen=[]
    for row in sorted((r for r in source['rows'] if r['local_bar_pass']),key=lambda r:r['cost']):
        q=np.array([row['q'][n] for n in NAMES]);bar=np.array(row['bar_center_wrist_m'])
        if any(np.linalg.norm(q-prev)<.03 for prev in seen):continue
        seen.append(q);poses=hand.forward(q,True)
        for n,v in zip(NAMES,q):data.joint(n).qpos[0]=v
        mujoco.mj_forward(full,data)
        native=[]
        for c in data.contact:
            a,b=[int(full.geom_bodyid[int(g)]) for g in c.geom]
            if a in hand_ids and b in hand_ids and c.dist < -2e-5:
                native.append(dict(parts=[full.body(a).name,full.body(b).name],distance_m=float(c.dist)))
        raw=[]
        for a,b in row['self_collision_pairs']:
            contacts=fcl.CollisionResult()
            fcl.collide(hand.manager._objs[a]['obj'],hand.manager._objs[b]['obj'],
                        fcl.CollisionRequest(num_max_contacts=100000,enable_contact=True),contacts)
            local=(np.array([c.pos for c in contacts.contacts])-poses[b][:3,3])@poses[b][:3,:3]
            raw.append(dict(parts=[a,b],contact_count=len(contacts.contacts),truncated=len(contacts.contacts)>=100000,
                            coordinates_in=b,contact_bounds_m=[local.min(0).tolist(),local.max(0).tolist()]))
        assemblies.append(dict(source_trial=row['trial'],q=row['q'],native_penetrations=native,raw_visual_intersections=raw))
        for degrees in range(0,360,5):
            R=Rotation.from_rotvec([np.deg2rad(degrees),0,0]).as_matrix()@np.array([[0.,0,1],[1,0,0],[0,1,0]])
            T=np.eye(4);T[:3,:3]=R;T[:3,3]=center-R@bar
            for name,pose in poses.items():hand.manager.set_transform(name,T@pose)
            _,pairs=hand.manager.in_collision_other(instrument,return_names=True)
            result=dict(source_trial=row['trial'],q=row['q'],roll_deg=degrees,instrument_frame_from_wrist=T.tolist(),
                        source_pad_gaps_m=row['gap_m'],instrument_collision_pairs=[list(p) for p in sorted(pairs)],
                        native_self_penetrations=native,raw_visual_assembly_overlap_present=bool(raw))
            if not pairs and not native:candidates.append(result)
            else:rejected.append(result)
        print('hand poses',len(seen),'instrument candidates',len(candidates),flush=True)
    report=dict(scope=__doc__,candidates=candidates,rejected=rejected,source_assembly_reviews=assemblies,
                hand_configurations=len(seen),roll_samples_per_configuration=72,
                full_robot_reach_checked=False,raw_assembly_overlap_resolved=False,physics_qualified=False,
                seed_sha256=digest(seed),device_sha256=digest(device_path),builder_sha256=digest(__file__),
                dependency_sha256=digest(HERE/'fit_cover_grasp.py'),seconds=time.monotonic()-started)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(hand_configurations=len(seen),candidates=len(candidates),seconds=report['seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.seed,a.out)
