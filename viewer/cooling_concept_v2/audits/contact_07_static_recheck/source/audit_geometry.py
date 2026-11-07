"""Check authored transforms against the actual source triangles using FCL.

This is a sampled geometric review, not a dynamics or force validation.
Every intersection is retained; intended contacts require separate review.
"""
import argparse,gzip,hashlib,json,time
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[2]
ARTICULATED={'cooler_white','cooler_black','cary','nicolet','bath','dra','pike'}

def matrix(a):return np.asarray(a).reshape(4,4).T
def mesh_scene(path):return trimesh.load(ROOT/path,force='scene',process=False)
def joined(scene):
    pieces=[]
    for n in scene.graph.nodes_geometry:
        transform,key=scene.graph[n];mesh=scene.geometry[key].copy();mesh.apply_transform(transform);pieces.append(mesh)
    return trimesh.util.concatenate(pieces)

def audit(folder):
    folder=Path(folder);manifest=json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())
    kin=next(s['kinematics'] for s in manifest['inspection_states'] if s['id']=='g1_hands_inspection')
    environment=trimesh.collision.CollisionManager();robot=trimesh.collision.CollisionManager()
    source=mesh_scene(manifest['architecture']['path']);roles={p['id']:p['role'] for p in manifest['architecture']['part_records']};floor_tops={}
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];environment.add_object('architecture::'+name,source.geometry[key],transform)
        if roles.get(name)=='floor':floor_tops['architecture::'+name]=float((source.geometry[key].vertices@transform[2,:3]+transform[2,3]).max())
    robot_meshes=defaultdict(list);instances=[];parts=set()
    for asset in manifest['assets']:
        source=mesh_scene(asset['geometry']);identity=asset['id']
        if identity=='g1':
            for name in source.graph.nodes_geometry:
                if name not in kin['part_links']:continue
                link=kin['part_links'][name];transform,key=source.graph[name]
                mesh=source.geometry[key].copy();mesh.apply_transform(np.linalg.inv(kin['bind_world'][link])@transform)
                robot_meshes[link].append(mesh)
        elif identity in ARTICULATED:
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];label=identity+'::'+name
                environment.add_object(label,source.geometry[key],transform);parts.add(label)
        else:
            environment.add_object(identity,joined(source));instances.append(identity)
    for link,pieces in robot_meshes.items():robot.add_object(link,trimesh.util.concatenate(pieces))
    print('geometry_ready',len(environment._objs),'obstacles',len(robot_meshes),'robot_links',flush=True)
    failures={};frame_count=0;phase_counts=defaultdict(int);began=time.monotonic()
    receipt=json.loads((folder/'export.json').read_text());extras=receipt['scene'].get('extraGeometry',[])
    for item in extras:
        mesh=trimesh.Trimesh(vertices=np.asarray(item['vertices']).reshape(-1,3),faces=np.asarray(item['indices']).reshape(-1,3),process=False)
        environment.add_object('extra::'+item['id'],mesh)
    if not extras and (folder/'source/hand_ik.js').exists():
        deck=trimesh.creation.box(extents=[.90,.43,.008]);deck.apply_translation([-.105,0,.851])
        environment.add_object('transport_leveling_deck',deck)
    contact_summary={};carry_gaps=[]
    frame_digest=hashlib.sha256()
    stream=gzip.open(folder/'frames.jsonl.gz','rt') if (folder/'frames.jsonl.gz').exists() else (folder/'frames.jsonl').open()
    for line in stream:
        frame_digest.update(line.encode())
        frame=json.loads(line);frame_count+=1
        for identity in instances:environment.set_transform(identity,matrix(frame['groups'][identity]))
        if 'transport_leveling_deck' in environment._objs:environment.set_transform('transport_leveling_deck',matrix(frame['groups']['utility_cart']))
        for identity,transform in frame.get('extra_matrices',{}).items():environment.set_transform('extra::'+identity,matrix(transform))
        for part in frame['parts']:
            label=part['asset']+'::'+part['name']
            if label in parts:environment.set_transform(label,matrix(part['matrix']))
        for link in robot_meshes:robot.set_transform(link,matrix(frame['links'][link]))
        _,pairs,contacts=robot.in_collision_other(environment,return_names=True,return_data=True)
        unexpected=[]
        for link,obstacle in pairs:
            # Only sole-floor contact is automatically admissible here.
            if link.endswith('ankle_roll_link') and obstacle in floor_tops:
                transform=matrix(frame['links'][link]);bottom=min(float((mesh.vertices@transform[2,:3]+transform[2,3]).min()) for mesh in robot_meshes[link])
                if bottom>=floor_tops[obstacle]-.00001:continue
            unexpected.append([link,obstacle])
            key=link+' / '+obstacle
            if key not in contact_summary:contact_summary[key]=dict(first_time_s=frame['time_s'],last_time_s=frame['time_s'],samples=0,phases=[])
            item=contact_summary[key];item['last_time_s']=frame['time_s'];item['samples']+=1
            if frame['phase'] not in item['phases']:item['phases'].append(frame['phase'])
        if unexpected:
            failures[str(frame['time_s'])]=dict(phase=frame['phase'],pairs=unexpected);phase_counts[frame['phase']]+=1
        if frame['action']=='carry':
            for target in frame.get('hand_targets',[]):
                actual=matrix(frame['links'][target['side']+'_palm_force_sensor'])[:3,3]
                carry_gaps.append(dict(time_s=frame['time_s'],phase=frame['phase'],object=target['object'],side=target['side'],actual_palm_to_authored_target_m=float(np.linalg.norm(actual-target['target_m']))))
        if frame_count%200==0:print('checked',frame_count,'wall_s',round(time.monotonic()-began,1),flush=True)
    stream.close()
    report=dict(passed=False,scope='Sampled exact-triangle intersections and palm proximity; intersections include intended contacts awaiting classification; no physical simulation claim',frames=frame_count,frames_with_nonfloor_intersections=len(failures),phase_counts=dict(phase_counts),contact_pairs=contact_summary,carry_contact_samples=carry_gaps,frames_sha256=frame_digest.hexdigest(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'geometry_review.json').write_text(json.dumps(report,indent=2)+'\n')
    (folder/'intersection_frames.json').write_text(json.dumps(failures,indent=2)+'\n')
    print(json.dumps(dict(frames=frame_count,intersection_frames=len(failures),phase_counts=dict(phase_counts))),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
