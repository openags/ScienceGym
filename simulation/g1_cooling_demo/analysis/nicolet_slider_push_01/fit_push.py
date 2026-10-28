"""Screen fingertip pushes of the documented sample-window grip.

The 70 mm opening is an inferred intermediate step for cover-edge access, not
a claim of full slider travel or gold-reference exchange. Source meshes and
joint limits are unchanged. This script checks the hand and terminal wrist;
whole-arm reach, visual tracking, force control and physics require execution.
"""
from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path
import sys
import time

import fcl
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
VIEW=ROOT/'viewer/cooling_concept_v2'
LOADER=HERE.parent/'nicolet_slider_access_03/search_grasp.py'
sys.path[:0]=[str(VIEW),str(ROOT/'simulation/g1_cooling_demo'),str(LOADER.parent)]
from search_grasp import load_environment,translate,sha
from source_geometry import KIN,fk,robot_meshes,set_hand
from cary_distal_hand import distal_hand_manager
from fit_ftir_cover_pad_grasp import source_limits_ok


def get_transform(obj):
    T=np.eye(4);T[:3,:3]=obj.getRotation();T[:3,3]=obj.getTranslation();return T


def main():
    started=time.monotonic();output=HERE/'review.json'
    if output.exists():raise FileExistsError(output)
    env,reference,_,_,paths,port=load_environment()
    ids=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    slider=next(i for i in ids['interfaces'] if i['id']=='sample_access_slider')
    rest={}
    for n in slider['parts']:
        name='nicolet::'+n;rest[name]=translate([0,-.104,0])@get_transform(env._objs[name]['obj'])
        env.set_transform(name,rest[name])
    target='nicolet::sample_access_slider_grip'
    scene=trimesh.load(paths[5],force='scene',process=False)
    _,key=scene.graph['sample_access_slider_grip'];grip=scene.geometry[key].copy();grip.apply_transform(rest[target])
    source=robot_meshes('right');pad_name='right_index_force_sensor_3';pad=source[pad_name]
    probe=pad.copy();probe.apply_scale(1000);point=probe.bounds.mean(0);point[2]=probe.bounds[1,2]+10
    _,_,face=trimesh.proximity.closest_point(probe,[point]);normal=probe.face_normals[face[0]]
    tangent=np.array([1.,0,0]);tangent-=normal*(normal@tangent);tangent/=np.linalg.norm(tangent)
    local_basis=np.column_stack([tangent,np.cross(normal,tangent),normal])
    exposed=pad.vertices[np.unique(pad.faces[pad.face_normals[:,2]>.5])]
    boundary=ConvexHull(exposed[:,:2]).equations
    hand=distal_hand_manager('right');graph=defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for link in hand._objs:
        pending=[(link,None,0)]
        while pending:
            n,parent,distance=pending.pop()
            if distance>1:continue
            if n in hand._objs:adjacent.add(tuple(sorted([link,n])))
            pending.extend((v,n,distance+w) for v,w in graph[n] if v!=parent)
    candidates=[];rejections=Counter();failures=[];tested=0
    for index,thumb1,thumb2 in itertools.product([0.,.2,.4,.6,.8,1.], [.2,.8,1.1], [.1,.4]):
        q={f'right_{f}_1_joint':1.25 for f in ['middle','ring','little']}
        q.update(right_index_1_joint=index,right_thumb_1_joint=thumb1,right_thumb_2_joint=thumb2)
        assert source_limits_ok(q)
        world=fk(q);relative=np.linalg.inv(world['right_palm_force_sensor'])@world[pad_name]
        pad_points=pad.vertices@relative[:3,:3].T+relative[:3,3]
        set_hand(hand,'right',q,np.eye(4));_,pairs=hand.in_collision_internal(return_names=True)
        bad=[sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent]
        if bad:
            failures.append(dict(q=q,reason='nonadjacent_self_contact',pairs=bad));continue
        for tilt in np.deg2rad([0.,15.,30.,45.,60.]):
            inward=np.array([0.,np.cos(tilt),-np.sin(tilt)]);outward=-inward
            basis=np.column_stack([[1.,0.,0.],np.cross(inward,[1.,0.,0.]),inward])
            heights=grip.vertices@outward
            surface=grip.vertices[heights>heights.max()-1e-6].mean(0)
            for roll in np.linspace(0.,2*np.pi,36,endpoint=False):
                R=Rotation.from_rotvec(inward*roll).as_matrix()@basis@local_basis.T@relative[:3,:3].T
                rotated=pad_points@R.T;distance=rotated@outward
                contact=rotated[distance<distance.min()+1e-6].mean(0)
                palm=translate(surface+.0003*outward-contact);palm[:3,:3]=R
                tested+=1
                if palm[2,3]<grip.bounds[1,2]+.04:
                    rejections['palm_below_approach_region']+=1;continue
                for n,T in rest.items():env.set_transform(n,T)
                set_hand(hand,'right',q,palm)
                result=fcl.DistanceResult()
                fcl.distance(hand._objs[pad_name]['obj'],env._objs[target]['obj'],
                             fcl.DistanceRequest(enable_nearest_points=True),result)
                local=(np.linalg.inv(palm@relative)@np.r_[result.nearest_points[0],1.])[:3]
                _,_,face=trimesh.proximity.closest_point(probe,[1000*local])
                margin=float(np.min(-(boundary[:,:2]@local[:2]+boundary[:,2])))
                if not (.00005<result.min_distance<.0006 and probe.face_normals[face[0],2]>.5 and margin>.0003):
                    rejections['pad_contact_region']+=1;continue
                _,pairs=hand.in_collision_other(env,return_names=True)
                if pairs:
                    rejections['initial_instrument_contact']+=1
                    failures.append(dict(q=q,tilt_rad=float(tilt),roll_rad=float(roll),reason='initial_instrument_contact',pairs=sorted([sorted(p) for p in pairs])))
                    continue
                path_failures=[]
                for travel in np.linspace(0.,.070,71):
                    shift=translate([0.,travel,0.])
                    for n,T in rest.items():env.set_transform(n,shift@T)
                    set_hand(hand,'right',q,shift@palm)
                    _,pairs=hand.in_collision_other(env,return_names=True)
                    if pairs:path_failures.append(dict(travel_m=float(travel),pairs=sorted([sorted(p) for p in pairs])))
                candidates.append(dict(q=q,tilt_rad=float(tilt),roll_rad=float(roll),palm_in_port_frame=palm.tolist(),
                                       source_pad=pad_name,pad_gap_m=float(result.min_distance),pad_margin_m=margin,
                                       outward_surface_normal=outward.tolist(),surface_in_port_frame=surface.tolist(),
                                       path_failures=path_failures,passed_distal_path=not path_failures))
        print('push_shape',index,thumb1,thumb2,'candidates',len(candidates),'paths',sum(c['passed_distal_path'] for c in candidates),flush=True)
    paths.extend([Path(__file__),LOADER,VIEW/'source_geometry.py',VIEW/'cary_distal_hand.py',
                  ROOT/'simulation/g1_cooling_demo/fit_ftir_cover_pad_grasp.py',ROOT/'assets/cooling_lab_v1/scene.json'])
    manifest=json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
    paths.append(ROOT/next(a['geometry'] for a in manifest['assets'] if a['id']=='g1'))
    report=dict(scope=__doc__,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},
                tested=tested,rejections=dict(rejections),failures=failures,candidates=candidates,
                passed_distal_paths=sum(c['passed_distal_path'] for c in candidates),
                source_joint_and_mimic_limits_checked=True,slider_target_m=.070,initial_slider_m=0.,
                world_port_m=port.tolist(),grip_bounds_port_frame_m=grip.bounds.tolist(),
                source_meshes_changed=False,whole_arm_checked=False,physics_qualified=False,
                seconds=time.monotonic()-started)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(candidates),passed=report['passed_distal_paths'],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
