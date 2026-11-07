"""Fit official three-finger hand contacts to the supported passive tweezer.

Source exterior points propose a grasp; original hand/tool meshes and the
unchanged official collision model independently screen it. This is authoring,
not an executed approach, supported grasp or full-body qualification.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

import fcl
import mujoco
import numpy as np
from scipy.optimize import least_squares
import trimesh

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'simulation/g1_cooling_demo/analysis/g1_dex3_comparison_01'
TOOL = ROOT / 'assets/idealtek_aa_sa_t6_v1'
sys.path[:0] = [str(SOURCE), str(TOOL)]
from fit_cover_grasp import SourceHand, NAMES, PARTS, digest, exposed_points
from support_geometry import load_support
from build_passive import profile


def run(output, seeds_per_pair=10, axis_sign=1, heel_support=False, support_review=None, contact_height_offset=0.):
    started = time.monotonic()
    out = Path(output).resolve(); out.mkdir(parents=True, exist_ok=False)
    snapshots = out / 'source_snapshot'; snapshots.mkdir()
    for p in [Path(__file__), SOURCE / 'fit_cover_grasp.py', TOOL / 'support_geometry.py', TOOL / 'build_passive.py']:
        shutil.copyfile(p, snapshots / p.name)
    hand = SourceHand()
    # A static root changes MuJoCo parent filtering. A free wrist reproduces
    # the topology of a mounted articulated robot hand without disabling any
    # collision pair. No dynamics or motion of this diagnostic root is run.
    xml = ET.parse(SOURCE / 'hand_inspection.xml').getroot()
    ET.SubElement(xml.find('worldbody/body'), 'freejoint', name='diagnostic_free_wrist')
    model_text = ET.tostring(xml, encoding='unicode')
    (out / 'hand_self_check.xml').write_text(model_text)
    sm = mujoco.MjModel.from_xml_string(model_text); sd = mujoco.MjData(sm)
    support_path = Path(support_review).resolve() if support_review else TOOL / 'tray_support_12/review.json'
    _, world_from_source, obstacles, support_receipt = load_support(support_path, ROOT)
    (out / 'support_geometry.json').write_text(json.dumps(support_receipt, indent=2) + '\n')
    supported = json.loads(support_path.read_text())
    tm = mujoco.MjModel.from_xml_path(str(support_path.parent / 'support.xml')); td = mujoco.MjData(tm)
    td.qpos[:] = supported['full_final_qpos']; mujoco.mj_forward(tm, td)
    tool_root = tm.body('tweezer').id
    descendants = {tool_root}
    for b in range(tool_root + 1, tm.nbody):
        if int(tm.body_parentid[b]) in descendants: descendants.add(b)
    groups = defaultdict(list)
    source_from_world = np.linalg.inv(world_from_source)
    for g in range(tm.ngeom):
        if int(tm.geom_bodyid[g]) not in descendants or not (tm.geom_contype[g] or tm.geom_conaffinity[g]): continue
        if tm.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            k = tm.geom_dataid[g]
            v = tm.mesh_vert[tm.mesh_vertadr[k]:tm.mesh_vertadr[k]+tm.mesh_vertnum[k]].copy()
            f = tm.mesh_face[tm.mesh_faceadr[k]:tm.mesh_faceadr[k]+tm.mesh_facenum[k]].copy()
            mesh = trimesh.Trimesh(vertices=v, faces=f, process=False)
        elif tm.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
            mesh = trimesh.creation.box(extents=2*tm.geom_size[g])
        else: raise ValueError('Unexpected tool geometry')
        T = np.eye(4); T[:3,:3] = td.geom_xmat[g].reshape(3,3); T[:3,3] = td.geom_xpos[g]
        mesh.apply_transform(source_from_world @ T)
        name = tm.geom(g).name
        groups['negative' if name.startswith('negative') else 'positive' if name.startswith('positive') else 'heel'].append(mesh)
    tool_meshes = {n: trimesh.util.concatenate(parts) for n, parts in groups.items()}
    heel_bounds = tool_meshes['heel'].bounds
    if not np.isfinite(contact_height_offset) or abs(contact_height_offset) > .0025:
        raise ValueError('Contact height offset must stay within 2.5 mm of the original contact plane')
    if heel_support:
        selected_height = float(heel_bounds[:,2].mean()) + contact_height_offset
        assert heel_bounds[0,2]+.0005 <= selected_height <= heel_bounds[1,2]-.0005
    tool = trimesh.collision.CollisionManager()
    for n, mesh in tool_meshes.items(): tool.add_object(n, mesh)
    scale = json.loads((TOOL / 'revisions/passive_07/model_review.json').read_text())['inferred_interior_thickness_scale']
    features = {n: [r for r in exposed_points(hand.meshes[n], 1 if 'thumb' in n else 0) if r['side']==1] for n in PARTS}
    source_files = [SOURCE / 'source.json', SOURCE / 'hand_inspection.xml', support_path,
                    support_path.parent / 'support.xml', TOOL / 'revisions/passive_07/model_review.json',
                    *snapshots.iterdir(), *[SOURCE / 'meshes' / (n + '.STL') for n in hand.meshes]]
    contract = dict(scope=__doc__, source_hashes={str(p.relative_to(ROOT)): digest(p) for p in source_files},
        model_self_check='Unchanged official collisions; diagnostic free wrist preserves dynamic parent filtering',
        proposal_geometry='Source exterior rays and rest beam profile; independent acceptance uses actual supported-state meshes',
        minimum_gap_m=.00002, maximum_gap_m=.0006, minimum_normal_opposition=.75,
        maximum_compiled_self_penetration_m=.00002, minimum_support_clearance_m=.001,
        seeds_per_pair=seeds_per_pair, seed=61105, tool_x_along_wrist_z_sign=axis_sign, full_body_checked=False,
        middle_finger_rigid_heel_support=heel_support,
        authored_contact_height_offset_m=contact_height_offset,
        support_review=str(support_path.relative_to(ROOT)),
        heel_bounds_source_m=heel_bounds.tolist(),
        visual_joint_overlap='Report original source mesh assembly overlaps separately; never delete source triangles')
    (out / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    old = json.loads((ROOT / 'simulation/g1_cooling_demo/analysis/dex3_cover_grasp_02/grasps.json').read_text())
    old = [r for r in old['rows'] if r['local_bar_pass']]
    rng = np.random.default_rng(61105)
    # q[0] remains zero in this planar family. The other six joints are
    # independent; index and middle can accommodate the tapered tool.
    lower = np.r_[[hand.limits[n]['intersection'][0]+.001 for n in NAMES[1:]], [.07,-.02,-np.pi,.045]]
    upper = np.r_[[hand.limits[n]['intersection'][1]-.001 for n in NAMES[1:]], [.20,.14,np.pi,.085]]
    if heel_support:
        # Keep the same original hand/tool surfaces. Only the authored grasp
        # family changes: middle on the rigid heel, thumb/index on the beams.
        lower[-1], upper[-1] = .09, .13
    rows = []; accepted = []
    for thumb_idx in range(3):
        for finger_idx in range(3):
            chosen = [features[PARTS[0]][thumb_idx], features[PARTS[1]][finger_idx], features[PARTS[2]][finger_idx]]
            points = [np.asarray(r['point_m']) for r in chosen]
            normals = [np.asarray(r['normal']) for r in chosen]
            def state(x):
                q = np.r_[0., x[:6]]
                poses = hand.forward(q)
                normal = np.array([np.cos(x[8]), np.sin(x[8]), 0.])
                axis = np.array([0.,0.,float(axis_sign)])
                R = np.column_stack([axis, normal, np.cross(axis, normal)])
                center = np.array([x[6], x[7], 0.])
                S = np.eye(4); S[:3,:3] = R.T; S[:3,3] = np.array([x[9],0.,.00575+contact_height_offset])-R.T@center
                transforms = {n: S@T for n,T in poses.items()}
                return q, S, transforms
            def residual(x):
                _, _, transforms = state(x); values = []
                for n, p, normal, sign in zip(PARTS, points, normals, [-1,1,1]):
                    T = transforms[n]; a = T[:3,:3]@p+T[:3,3]
                    if heel_support and n == PARTS[2]:
                        outer = float(heel_bounds[1,1])
                        height = float(heel_bounds[:,2].mean()) + contact_height_offset
                    else:
                        _, thick, center = profile(a[0], scale)
                        outer = center+thick/2
                        height = .00575 + contact_height_offset
                    values.extend([(a[1]-sign*(outer+.0003))/.001, (a[2]-height)/.001])
                    values.extend(2*(T[:3,:3]@normal-np.array([0.,-sign,0.])))
                    if heel_support and n == PARTS[2]:
                        values.extend([(a[0]-heel_bounds[:,0].mean())/.001,0.])
                    else:
                        values.extend([min(0.,a[0]-.025)/.001, max(0.,a[0]-.115)/.001])
                return np.r_[values, .0001*x[:6]]
            for seed_index in range(seeds_per_pair):
                r = old[(seed_index*43) % len(old)]
                x = np.r_[[r['q'][n] for n in NAMES[1:]], r['bar_center_wrist_m'][:2], -.5, .065]
                if heel_support: x[-1] = .10
                if seed_index: x[:6] += rng.normal(0,.14,6); x[8] += rng.normal(0,.3)
                result = least_squares(residual, np.clip(x,lower,upper), bounds=(lower,upper),
                                       max_nfev=160, ftol=1e-8, xtol=1e-8, gtol=1e-8)
                q, S, transforms = state(result.x)
                for n,T in transforms.items(): hand.manager.set_transform(n,T)
                _, tool_pairs = hand.manager.in_collision_other(tool, return_names=True)
                _, visual_self = hand.manager.in_collision_internal(return_names=True)
                visual_self = [list(p) for p in sorted(visual_self) if tuple(sorted(p)) not in hand.adjacent]
                for n,v in zip(NAMES,q): sd.joint(n).qpos[0] = v
                mujoco.mj_forward(sm,sd)
                self_contacts = [dict(parts=[sm.body(sm.geom_bodyid[g]).name for g in c.geom], distance_m=float(c.dist))
                                 for c in sd.contact if c.dist < -.00002]
                contacts = []
                sides = ['negative','positive','heel' if heel_support else 'positive']
                for n,side,sign in zip(PARTS,sides,[-1,1,1]):
                    d=fcl.DistanceResult(); fcl.distance(hand.manager._objs[n]['obj'],tool._objs[side]['obj'],
                        fcl.DistanceRequest(enable_nearest_points=True),d)
                    a,b=map(np.asarray,d.nearest_points); gap=float(d.min_distance)
                    inward=float(-sign*(b-a)[1]/max(gap,1e-12))
                    contacts.append(dict(part=n,side=side,gap_m=gap,point_source_m=b.tolist(),
                                         point_hand_local_m=(np.linalg.inv(transforms[n])@np.r_[a,1])[:3].tolist(),
                                         inward_component=inward))
                support_clearance = min(float((mesh.vertices@(world_from_source@transforms[n])[:3,:3].T+
                    (world_from_source@transforms[n])[:3,3])[:,2].min()) for n,mesh in hand.meshes.items())
                _, obstacle_pairs = hand.manager.in_collision_other(obstacles,return_names=True)
                tray_gap = float(hand.manager.min_distance_other(obstacles))
                cxs = [c['point_source_m'][0] for c in contacts]
                checks = dict(no_tool_intersections=not tool_pairs, official_self_contact_clear=not self_contacts,
                    triple_contact_clearance=all(.00002<c['gap_m']<.0006 for c in contacts),
                    contact_normals=all(c['inward_component']>.75 for c in contacts),
                    axial_support_brackets_thumb=min(cxs[1:])+.005<cxs[0]<max(cxs[1:])-.005,
                    hand_above_plane=support_clearance>.001, tray_clearance=not obstacle_pairs and tray_gap>.001)
                row=dict(q=dict(zip(NAMES,map(float,q))),source_tool_from_wrist=S.tolist(),contacts=contacts,
                    checks={k:bool(v) for k,v in checks.items()},source_visual_self_intersections=visual_self,
                    compiled_self_contacts=self_contacts,tool_intersections=[list(p) for p in sorted(tool_pairs)],
                    tray_intersections=[list(p) for p in sorted(obstacle_pairs)],tray_gap_m=tray_gap,
                    support_plane_clearance_m=support_clearance, cost=float(result.cost),evaluations=int(result.nfev),
                    feature_lengths_m=[p['longitudinal_m'] for p in chosen], seed_index=seed_index)
                rows.append(row)
                if all(checks.values()): accepted.append(row)
            print(json.dumps(dict(features=[thumb_idx,finger_idx],tested=len(rows),candidates=len(accepted),seconds=time.monotonic()-started)),flush=True)
            (out/'trials.json').write_text(json.dumps(rows,indent=2)+'\n')
    report=dict(scope=__doc__,candidates=accepted,nearest_candidates=sorted(rows,key=lambda r:(sum(not v for v in r['checks'].values()),r['cost']))[:15],
                tested=len(rows),accepted_count=len(accepted),contract_sha256=digest(out/'contract.json'),
                seconds=time.monotonic()-started,qualified_grasp=False,full_body_checked=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['tested','accepted_count','seconds','qualified_grasp']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
    parser.add_argument('--seeds',type=int,default=10)
    parser.add_argument('--axis-sign',type=int,choices=[-1,1],default=1)
    parser.add_argument('--heel-support',action='store_true',
                        help='Fit the middle finger to the original rigid heel while thumb/index contact the beams')
    parser.add_argument('--support-review',help='Passed unactuated support review; defaults to the original tray placement')
    parser.add_argument('--contact-height-offset',type=float,default=0.,help='Authored side-contact height offset in metres, at most 2.5 mm')
    args=parser.parse_args();run(args.out,args.seeds,args.axis_sign,args.heel_support,args.support_review,args.contact_height_offset)
