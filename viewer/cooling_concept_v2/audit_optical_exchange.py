"""Review tools and identified optical witnesses in the exported full lab.

Checks source FK, object ownership/poses, and source-triangle clearance for
both witnesses, tweezers and their ordinary support tray. No force, balance,
sensor-control, acquisition, delivery, or complete-paper qualification.
"""
import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT,manifest_for_export,fk
from audit_geometry import ARTICULATED,matrix,mesh_scene,joined
from deformed_geometry import DeformedGeometry

TARGETS={'tweezers_white','tray_white','optical_witness_white','optical_witness_black'}


def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text());manifest=manifest_for_export(folder)
    assert receipt.get('episode')=='ftir'
    config=json.loads((folder/'source/optical_episode.json').read_text())
    assert hashlib.sha256((folder/'source/optical_episode.json').read_bytes()).hexdigest()==receipt['source_sha256']['optical_episode.json']
    segments={s['id']:s for s in config['segments']}
    assert len(segments)==len(config['segments'])
    obstacles=trimesh.collision.CollisionManager();objects=trimesh.collision.CollisionManager();defaults={};instances=[]
    source=mesh_scene(manifest['architecture']['path'])
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];obstacles.add_object('room::'+name,source.geometry[key],transform)
    for asset in manifest['assets']:
        identity=asset['id']
        if identity=='g1':continue
        source=mesh_scene(asset['geometry'])
        if identity in TARGETS:objects.add_object(identity,joined(source))
        elif identity in ARTICULATED:
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];label=identity+'::'+name
                obstacles.add_object(label,source.geometry[key],transform);defaults[label]=(identity,transform)
        else:obstacles.add_object(identity,joined(source));instances.append(identity)
    assert set(objects._objs)==TARGETS
    for item in receipt['scene']['extraGeometry']:
        obstacles.add_object('extra::'+item['id'],trimesh.Trimesh(vertices=np.array(item['vertices']).reshape(-1,3),faces=np.array(item['indices']).reshape(-1,3),process=False))
    deformation=DeformedGeometry(folder,manifest)
    assert set(deformation.definitions)=={'tweezers_white'}
    palm_to_tool=np.linalg.inv(config['tool_T_palm']);tool_to_holder=np.linalg.inv(config['holder_T_tool'])
    failures=[];kinematic_failures=[];counts=defaultdict(int);seen=set();samples=0;maximum_fk_error=0.;maximum_object_error=0.;digest=hashlib.sha256()
    print('optical_geometry_ready',len(obstacles._objs),'obstacles',flush=True)
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            digest.update(line.encode());frame=json.loads(line);samples+=1;segment=segments[frame['phase']];seen.add(segment['id'])
            for identity in instances:obstacles.set_transform(identity,matrix(frame['groups'][identity]))
            for label,(identity,rest) in defaults.items():obstacles.set_transform(label,matrix(frame['groups'][identity])@rest)
            for part in frame['parts']:
                label=part['asset']+'::'+part['name']
                if label in defaults:obstacles.set_transform(label,matrix(part['matrix']))
            for identity,transform in frame['extra_matrices'].items():obstacles.set_transform('extra::'+identity,matrix(transform))
            for identity in TARGETS:objects.set_transform(identity,matrix(frame['groups'][identity]))
            deformation.apply(objects,frame)
            _,pairs,contacts=objects.in_collision_other(obstacles,return_names=True,return_data=True)
            _,internal,internal_contacts=objects.in_collision_internal(return_names=True,return_data=True)
            unexpected=[]
            for a,b in list(pairs)+list(internal):
                selected=[c for c in contacts+internal_contacts if c.names=={a,b}]
                unexpected.append(dict(pair=[a,b],maximum_depth_m=max((float(c.depth) for c in selected),default=None)))
            if unexpected:
                failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=unexpected));counts[frame['phase']]+=1
            root=matrix(frame['groups']['g1']);world=fk(frame['joints'])
            link_error=max(float(np.max(abs(matrix(frame['links'][name])-root@pose))) for name,pose in world.items())
            maximum_fk_error=max(maximum_fk_error,link_error)
            tool=root@world['right_palm_force_sensor']@palm_to_tool if segment['tool_held'] else np.array(config['tool_rest'])
            expected={'tweezers_white':tool,'tray_white':np.array(config['tray_matrix'])}
            for kind in ['white','black']:
                expected['optical_witness_'+kind]=tool@tool_to_holder if segment['held_specimen']==kind else np.array(segment['stored_specimens'][kind])
            object_error=max(float(np.max(abs(matrix(frame['groups'][name])-pose))) for name,pose in expected.items());maximum_object_error=max(maximum_object_error,object_error)
            state=frame['optical_state']
            ownership_match=state=={key:segment[key] for key in ['tool_held','held_specimen','stored_specimens']}
            if link_error>1e-7 or object_error>1e-7 or not ownership_match:
                kinematic_failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],maximum_link_error=link_error,maximum_object_error=object_error,ownership_match=ownership_match))
            if samples%200==0:print('optical_checked',samples,flush=True)
    assert samples==receipt['frame_count'] and digest.hexdigest()==receipt['frames_sha256']
    missing_phases=sorted(set(segments)-seen)
    result=dict(scope=__doc__,passed=not(failures or kinematic_failures or missing_phases),samples=samples,segment_count=len(segments),missing_phases=missing_phases,intersection_frames=failures,phase_counts=dict(counts),kinematic_failures=kinematic_failures,maximum_source_fk_matrix_error=maximum_fk_error,maximum_object_matrix_error=maximum_object_error,maximum_render_source_vertex_error_m=deformation.maximum_vertex_error_m,frames_sha256=digest.hexdigest(),source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['audit_optical_exchange.py','deformed_geometry.py','source_geometry.py','audit_geometry.py']})
    (folder/'optical_exchange_review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],samples=samples,collision_frames=len(failures),kinematic_failures=len(kinematic_failures),missing_phases=missing_phases)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
