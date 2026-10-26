"""Source-frame geometry helpers shared by development collision reviews."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
KIN = next(s['kinematics'] for s in MANIFEST['inspection_states'] if s['id']=='g1_hands_inspection')
ASSETS = {a['id']:a for a in MANIFEST['assets']}

def fk(values):
    q = dict(values)
    world = {KIN['root_link']:np.array(KIN['root_matrix'])}
    for joint in KIN['joints']:
        if joint['mimic']:
            m=joint['mimic'];q[joint['name']]=float(m.get('offset',0))+float(m.get('multiplier',1))*q.get(m['joint'],0)
        value=q.get(joint['name'],0);transform=np.array(joint['origin_matrix'])
        if value:
            rotation=np.eye(4);rotation[:3,:3]=Rotation.from_rotvec(np.array(joint['axis'])*value).as_matrix();transform=transform@rotation
        world[joint['id']]=world[joint['parent']]@transform
    return world

def robot_meshes(side=None):
    scene=trimesh.load(ROOT/ASSETS['g1']['geometry'],force='scene',process=False);pieces=defaultdict(list)
    for name in scene.graph.nodes_geometry:
        link=KIN['part_links'].get(name)
        if not link or (side and (not link.startswith(side+'_') or not any(k in link for k in ['base_link','palm','index','middle','ring','little','thumb']))):continue
        transform,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(np.linalg.inv(KIN['bind_world'][link])@transform);pieces[link].append(mesh)
    return {link:trimesh.util.concatenate(parts) for link,parts in pieces.items()}

def asset_manager(identity):
    scene=trimesh.load(ROOT/ASSETS[identity]['geometry'],force='scene',process=False);manager=trimesh.collision.CollisionManager()
    for name in scene.graph.nodes_geometry:
        transform,key=scene.graph[name];manager.add_object(name,scene.geometry[key],transform)
    return manager

def hand_manager(side):
    manager=trimesh.collision.CollisionManager()
    for name,mesh in robot_meshes(side).items():manager.add_object(name,mesh)
    return manager

def set_hand(manager,side,q,palm):
    world=fk(q);base=palm@np.linalg.inv(world[side+'_palm_force_sensor'])
    for link in manager._objs:manager.set_transform(link,base@world[link])

def hand_orientation(side,forward,normal):
    zero=fk({});palm=zero[side+'_palm_force_sensor'];finger=(np.linalg.inv(palm)@zero[side+'_index_force_sensor_3'])[:3,3];finger[2]=0;finger/=np.linalg.norm(finger)
    local=np.column_stack([finger,np.cross([0,0,1],finger),[0,0,1]])
    forward=np.array(forward,dtype=float);forward/=np.linalg.norm(forward);normal=np.array(normal,dtype=float);normal/=np.linalg.norm(normal)
    return np.column_stack([forward,np.cross(normal,forward),normal])@local.T
