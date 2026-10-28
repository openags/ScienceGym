"""Check apparatus/cover geometry against the room, cart and each other.

Horizontal resting contact is admissible only when all payload vertices stay
above the support top. Other surface intersections are retained. This review
does not infer friction, support forces, or stability from geometric clearance.
"""
import argparse,gzip,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT,MANIFEST,ASSETS

def matrix(values):return np.asarray(values).reshape(4,4).T
def scene(path):return trimesh.load(ROOT/path,force='scene',process=False)
def combined(source):
    parts=[]
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];mesh=source.geometry[key].copy();mesh.apply_transform(transform);parts.append(mesh)
    return trimesh.util.concatenate(parts)

def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text())
    obstacles=trimesh.collision.CollisionManager();moving={name:trimesh.collision.CollisionManager() for name in ['cooler_white','cooler_black','lid_white','lid_black']}
    payload_meshes={};part_owner={};instances=[];articulated=set();support_top={}
    source=scene(MANIFEST['architecture']['path'])
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];label='architecture::'+name;mesh=source.geometry[key];obstacles.add_object(label,mesh,transform)
        if name.endswith('_worktop'):
            support_top[label]=float((mesh.vertices@transform[2,:3]+transform[2,3]).max())
    for identity,asset in ASSETS.items():
        if identity=='g1':continue
        source=scene(asset['geometry'])
        if identity in moving or identity in ['bath','cary','nicolet']:
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];label=identity+'::'+name;mesh=source.geometry[key]
                if identity in moving:
                    moving[identity].add_object(label,mesh,transform);part_owner[label]=identity;payload_meshes[label]=mesh.vertices
                else:obstacles.add_object(label,mesh,transform);articulated.add(label)
        else:obstacles.add_object(identity,combined(source));instances.append(identity)
    extras={};deck_vertices=None
    for item in receipt['scene'].get('extraGeometry',[]):
        label='extra::'+item['id'];mesh=trimesh.Trimesh(vertices=np.asarray(item['vertices']).reshape(-1,3),faces=np.asarray(item['indices']).reshape(-1,3),process=False)
        owner=('lid_white' if item['id'].endswith('white') else 'lid_black') if item['id'].startswith('aperture_lid_') else None
        extras[item['id']]=(label,owner)
        if owner:moving[owner].add_object(label,mesh);part_owner[label]=owner;payload_meshes[label]=mesh.vertices
        else:obstacles.add_object(label,mesh)
        if item['id']=='transport_leveling_deck':deck_vertices=mesh.vertices
    failures=[];counts=defaultdict(int);support_samples=0;count=0
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            frame=json.loads(line);count+=1;bottoms={identity:float('inf') for identity in moving};top_of_plate={}
            for identity in instances:obstacles.set_transform(identity,matrix(frame['groups'][identity]))
            for part in frame['parts']:
                label=part['asset']+'::'+part['name'];transform=matrix(part['matrix'])
                if label in part_owner:
                    identity=part_owner[label];moving[identity].set_transform(label,transform)
                    bottoms[identity]=min(bottoms[identity],float((payload_meshes[label]@transform[2,:3]+transform[2,3]).min()))
                    if part['name'].endswith('__aperture_plate'):top_of_plate[identity]=float((payload_meshes[label]@transform[2,:3]+transform[2,3]).max())
                elif label in articulated:obstacles.set_transform(label,transform)
            for identity,values in frame.get('extra_matrices',{}).items():
                label,owner=extras[identity];transform=matrix(values)
                if owner:
                    moving[owner].set_transform(label,transform);bottoms[owner]=min(bottoms[owner],float((payload_meshes[label]@transform[2,:3]+transform[2,3]).min()))
                else:obstacles.set_transform(label,transform)
                if identity=='transport_leveling_deck':support_top[label]=float((deck_vertices@transform[2,:3]+transform[2,3]).max())
            unexpected=[]
            for identity,manager in moving.items():
                _,pairs=manager.in_collision_other(obstacles,return_names=True)
                for payload,obstacle in pairs:
                    if obstacle in support_top and bottoms[identity]>=support_top[obstacle]-.00001:support_samples+=1;continue
                    unexpected.append([payload,obstacle])
            for left,right in [('cooler_white','cooler_black'),('lid_white','cooler_white'),('lid_black','cooler_black'),('lid_white','cooler_black'),('lid_black','cooler_white')]:
                _,pairs=moving[left].in_collision_other(moving[right],return_names=True)
                for a,b in pairs:
                    if left.startswith('lid_') and b.endswith('__aperture_plate') and bottoms[left]>=top_of_plate[right]-.00001:support_samples+=1;continue
                    unexpected.append([a,b])
            if unexpected:
                failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=unexpected));counts[frame['phase']]+=1
            if count%200==0:print('payload_checked',count,flush=True)
    report=dict(passed=not failures,scope=__doc__,samples=count,admissible_horizontal_contact_pairs=support_samples,phase_counts=dict(counts),intersection_frames=failures,verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'payload_clearance_review.json').write_text(json.dumps(report,indent=2)+'\n');print('payload_review',count,len(failures),dict(counts),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
