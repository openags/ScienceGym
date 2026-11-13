"""Check the entire moving cart and its added deck against source room geometry.

Cargo-to-cart checks are performed separately by audit_payload_clearance.py.
This is geometric clearance only, not rolling contact or load stability.
"""
import argparse,gzip,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT,MANIFEST,ASSETS
from audit_payload_clearance import matrix,scene,combined

def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text())
    obstacles=trimesh.collision.CollisionManager();cart=trimesh.collision.CollisionManager();floor_tops={};instances=[];animated=set();local={};cart_vertices={}
    roles={p['id']:p['role'] for p in MANIFEST['architecture']['part_records']}
    source=scene(MANIFEST['architecture']['path'])
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];mesh=source.geometry[key];label='architecture::'+name;obstacles.add_object(label,mesh,transform)
        if roles.get(name)=='floor':floor_tops[label]=float((mesh.vertices@transform[2,:3]+transform[2,3]).max())
    source=scene(ASSETS['utility_cart']['geometry'])
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];mesh=source.geometry[key];cart.add_object(name,mesh,transform);local[name]=transform;cart_vertices[name]=mesh.vertices
    # These identities travel as cart cargo or are checked against the cart by
    # the separate payload and robot reviews; do not duplicate internal contact.
    excluded={'g1','utility_cart','cooler_white','cooler_black','daq','smu_white','smu_black'}
    for identity,asset in ASSETS.items():
        if identity in excluded:continue
        source=scene(asset['geometry'])
        if identity in ['bath','cary','nicolet']:
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];label=identity+'::'+name;obstacles.add_object(label,source.geometry[key],transform);animated.add(label)
        else:obstacles.add_object(identity,combined(source));instances.append(identity)
    extras=[]
    for item in receipt['scene'].get('extraGeometry',[]):
        if not item['id'].startswith('transport_'):continue
        mesh=trimesh.Trimesh(vertices=np.asarray(item['vertices']).reshape(-1,3),faces=np.asarray(item['indices']).reshape(-1,3),process=False);cart.add_object(item['id'],mesh);extras.append(item['id']);cart_vertices[item['id']]=mesh.vertices
    frames=[];counts=defaultdict(int);checked=0;floor_contacts=0
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            frame=json.loads(line)
            if frame['action'] not in ['push','push_grip','push_release']:continue
            checked+=1;root=matrix(frame['groups']['utility_cart']);bottom=float('inf')
            for name,rest in local.items():
                transform=root@rest;cart.set_transform(name,transform);bottom=min(bottom,float((cart_vertices[name]@transform[2,:3]+transform[2,3]).min()))
            for name in extras:
                transform=matrix(frame['extra_matrices'][name]);cart.set_transform(name,transform);bottom=min(bottom,float((cart_vertices[name]@transform[2,:3]+transform[2,3]).min()))
            for identity in instances:obstacles.set_transform(identity,matrix(frame['groups'][identity]))
            for part in frame['parts']:
                name=part['asset']+'::'+part['name']
                if name in animated:obstacles.set_transform(name,matrix(part['matrix']))
            _,pairs=cart.in_collision_other(obstacles,return_names=True);unexpected=[]
            for a,b in pairs:
                if b in floor_tops and bottom>=floor_tops[b]-.00001:floor_contacts+=1;continue
                unexpected.append([a,b])
            if unexpected:frames.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=unexpected));counts[frame['phase']]+=1
    report=dict(passed=checked>0 and not frames,scope=__doc__,sampled_states=checked,admissible_floor_contact_pairs=floor_contacts,phase_counts=dict(counts),intersection_frames=frames,verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'cart_clearance_review.json').write_text(json.dumps(report,indent=2)+'\n');print('cart_review',checked,len(frames),dict(counts),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
