"""Fit a visible, nonintersecting hand configuration around a frame upright.

Geometric fixture only: this does not establish frictional grasp stability.
"""
import json,itertools,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh
import fcl

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
manifest=json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
kin=next(s['kinematics'] for s in manifest['inspection_states'] if s['id']=='g1_hands_inspection')
assets={a['id']:a for a in manifest['assets']}

def fk(q):
    world={kin['root_link']:np.array(kin['root_matrix'])}
    for j in kin['joints']:
        value=q.get(j['name'],0)
        if j['mimic']:value=float(j['mimic'].get('offset',0))+float(j['mimic'].get('multiplier',1))*q.get(j['mimic']['joint'],0);q[j['name']]=value
        transform=np.array(j['origin_matrix']);axis=np.array(j['axis'])
        if value:
            turn=np.eye(4);turn[:3,:3]=Rotation.from_rotvec(axis*value).as_matrix();transform=transform@turn
        world[j['id']]=world[j['parent']]@transform
    return world

robot=trimesh.load(ROOT/assets['g1']['geometry'],force='scene',process=False);pieces=defaultdict(list)
for name in robot.graph.nodes_geometry:
    link=kin['part_links'].get(name,'')
    if not link.startswith('left_') or not any(k in link for k in ['base_link','palm','index','middle','ring','little','thumb']):continue
    transform,key=robot.graph[name];mesh=robot.geometry[key].copy();mesh.apply_transform(np.linalg.inv(kin['bind_world'][link])@transform);pieces[link].append(mesh)
hand=trimesh.collision.CollisionManager()
for link,parts in pieces.items():hand.add_object(link,trimesh.util.concatenate(parts))
cooler=trimesh.load(ROOT/assets['cooler_white']['geometry'],force='scene',process=False);obstacles=trimesh.collision.CollisionManager()
for name in cooler.graph.nodes_geometry:
    transform,key=cooler.graph[name];obstacles.add_object(name,cooler.geometry[key],transform)
zero=fk({});palm=zero['left_palm_force_sensor'];finger=(np.linalg.inv(palm)@zero['left_index_force_sensor_3'])[:3,3];finger[2]=0;finger/=np.linalg.norm(finger)
local=np.column_stack([finger,np.cross([0,0,1],finger),[0,0,1]])
normal=np.array([1.,0,0]);forward=np.array([0.,1,0]);orientation=np.column_stack([forward,np.cross(normal,forward),normal])@local.T
valid=[];tested=0;start=time.monotonic()
for x,y,angle in itertools.product(np.arange(.219,.271,.006),np.arange(-.065,.036,.01),np.arange(.25,1.26,.1)):
    q={f'left_{finger}_1_joint':float(angle) for finger in ['index','middle','ring','little']}
    # Thumb stays open in this search; a separate opposed-thumb fit is required.
    world=fk(q);pose=np.eye(4);pose[:3,:3]=orientation;pose[:3,3]=[-x,y,.135];base=pose@np.linalg.inv(world['left_palm_force_sensor'])
    for link in pieces:hand.set_transform(link,base@world[link])
    tested+=1
    if hand.in_collision_other(obstacles):continue
    distance,names=hand.min_distance_other(obstacles,return_names=True)
    if distance<.003:valid.append(dict(palm_x_m=-float(x),palm_y_m=float(y),finger_angle_rad=float(angle),minimum_distance_m=distance,nearest_pair=names))
print('tested',tested,'valid',len(valid),'seconds',time.monotonic()-start,flush=True)
(HERE/'previews/grasp_search.json').write_text(json.dumps(dict(tested=tested,candidates=sorted(valid,key=lambda v:v['minimum_distance_m']),scope='Nonintersecting hand and apparatus surfaces only; opposed-thumb and support qualification remain required'),indent=2)+'\n')

opposed=[];tube=obstacles._objs['COOLER_WHITE__frame_tube_left']['obj']
for candidate in sorted(valid,key=lambda v:v['minimum_distance_m'])[:24]:
    for thumb1,thumb2 in itertools.product(np.linspace(.3,1.1641,12),np.linspace(0,.5864,10)):
        q={f'left_{finger}_1_joint':candidate['finger_angle_rad'] for finger in ['index','middle','ring','little']}
        q.update(left_thumb_1_joint=float(thumb1),left_thumb_2_joint=float(thumb2));world=fk(q)
        pose=np.eye(4);pose[:3,:3]=orientation;pose[:3,3]=[candidate['palm_x_m'],candidate['palm_y_m'],.135];base=pose@np.linalg.inv(world['left_palm_force_sensor'])
        for link in pieces:hand.set_transform(link,base@world[link])
        if hand.in_collision_other(obstacles):continue
        def nearest(link):
            result=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],tube,fcl.DistanceRequest(enable_nearest_points=True),result)
            return float(result.min_distance),np.asarray(result.nearest_points[1])
        thumb_distance,thumb_point=nearest('left_thumb_force_sensor_4')
        if thumb_distance>.008:continue
        candidates=[(link,*nearest(link)) for link in ['left_index_2','left_middle_2','left_ring_2','left_little_2']]
        finger,fd,fp=min(candidates,key=lambda item:item[1]);a=thumb_point[:2]-[-.1875,.03];b=fp[:2]-[-.1875,.03]
        opposition=float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)))
        if opposition<-.4:opposed.append(dict(**candidate,thumb_1_rad=float(thumb1),thumb_2_rad=float(thumb2),thumb_gap_m=thumb_distance,finger=finger,finger_gap_m=fd,contact_radial_dot=opposition,thumb_contact_point_m=thumb_point.tolist(),finger_contact_point_m=fp.tolist()))
opposed.sort(key=lambda item:item['thumb_gap_m']+item['finger_gap_m'])
(HERE/'previews/opposed_grasp_search.json').write_text(json.dumps(dict(candidates=opposed,scope='Exact source-surface proximity on opposite sides of an upright; no force stability claim'),indent=2)+'\n')
print('opposed_candidates',len(opposed),'best',opposed[:1],flush=True)
