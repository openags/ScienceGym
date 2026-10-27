"""Check the moving gold standard in the complete measurement laboratory.

Uses the verified environment-pose cache and exact deformed tool geometry.
The earlier general reference reviewer is retained for historical traces.

Robot/reference intersections are covered by audit_geometry. This reviewer
checks reference/environment surfaces, admitting bounded non-optical support
at the protective-cap rim and integrating-sphere top panel. No force/stability
claim; optical-face intersections remain failures.
"""
import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from source_geometry import ROOT, manifest_for_export
from audit_geometry import ARTICULATED
from audit_payload_clearance import matrix, scene, combined
from environment_poses import EnvironmentPoses
from deformed_geometry import DeformedGeometry

REFERENCE={'gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face'}


def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text());manifest=manifest_for_export(folder)
    obstacles=trimesh.collision.CollisionManager();reference=trimesh.collision.CollisionManager();defaults={};instances=[];moving=set();support_vertices={}
    source=scene(manifest['architecture']['path'])
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];obstacles.add_object('room::'+name,source.geometry[key],transform)
    for asset in manifest['assets']:
        identity=asset['id']
        if identity=='g1':continue
        source=scene(asset['geometry'])
        if identity in ARTICULATED:
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];label=identity+'::'+name
                if identity=='pike' and name in ['gold_reference_shoulder','top_sample_panel']:support_vertices[label]=source.geometry[key].vertices.copy()
                if identity=='pike' and name in REFERENCE:reference.add_object(label,source.geometry[key],transform);moving.add(label)
                else:obstacles.add_object(label,source.geometry[key],transform);defaults[label]=(identity,transform)
        else:obstacles.add_object(identity,combined(source));instances.append(identity)
    for item in receipt['scene']['extraGeometry']:
        mesh=trimesh.Trimesh(vertices=np.asarray(item['vertices']).reshape(-1,3),faces=np.asarray(item['indices']).reshape(-1,3),process=False)
        obstacles.add_object('extra::'+item['id'],mesh)
    config=json.loads((folder/'source/reference_transfer.json').read_text());cap_floor=np.array(config['cap_floor_m'])
    poses=EnvironmentPoses(obstacles,instances,defaults);deformation=DeformedGeometry(folder,manifest)
    assert receipt['episode']=='ftir_measurement'
    counts=defaultdict(int);failures=[];support_samples=0;maximum_support_depth=0.;port_support_samples=0;maximum_port_support_depth=0.;samples=0
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            frame=json.loads(line);samples+=1
            poses.update(frame);deformation.apply(obstacles,frame)
            if samples%200==1:poses.verify(frame)
            support_planes={}
            for part in frame['parts']:
                label=part['asset']+'::'+part['name']
                if label in moving:reference.set_transform(label,matrix(part['matrix']))
                if label in support_vertices:
                    transform=matrix(part['matrix']);heights=support_vertices[label]@transform[2,:3]+transform[2,3]
                    support_planes[label]=(float(heights.min()),float(heights.max()))
            _,pairs,contacts=reference.in_collision_other(obstacles,return_names=True,return_data=True);unexpected=[]
            for a,b in pairs:
                selected=[c for c in contacts if c.names=={a,b}]
                depth=max((float(c.depth) for c in selected),default=float('inf'))
                points=np.array([c.point for c in selected])
                at_rim=len(points)>0 and np.all(np.abs(points[:,2]-(cap_floor[2]+.024))<1e-5) and np.all(np.linalg.norm(points[:,:2]-cap_floor[:2],axis=1)>=.025-1e-5) and np.all(np.linalg.norm(points[:,:2]-cap_floor[:2],axis=1)<=.028+1e-5)
                if a=='pike::gold_reference_holder' and b=='pike::reference_protective_cap' and depth<1e-6 and at_rim:
                    support_samples+=1;maximum_support_depth=max(maximum_support_depth,depth)
                elif a=='pike::gold_reference_shoulder' and b=='pike::top_sample_panel' and depth<1e-6 and support_planes[a][0]>=support_planes[b][1]-1e-6 and len(points)>0 and np.all(np.abs(points[:,2]-support_planes[b][1])<1e-6):
                    port_support_samples+=1;maximum_port_support_depth=max(maximum_port_support_depth,depth)
                else:unexpected.append(dict(pair=[a,b],maximum_depth_m=depth))
            if unexpected:failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=unexpected));counts[frame['phase']]+=1
            if samples%200==0:print('reference_checked',samples,flush=True)
    result=dict(scope=__doc__,passed=not failures,samples=samples,intersection_frames=failures,phase_counts=dict(counts),admissible_cap_rim_contact_samples=support_samples,
                maximum_admissible_cap_contact_depth_m=maximum_support_depth,admissible_port_support_samples=port_support_samples,maximum_admissible_port_contact_depth_m=maximum_port_support_depth,
                support_tolerance_m=1e-6,verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                pose_cache_verification=dict(samples=poses.verification_count,maximum_matrix_error=poses.maximum_verification_error),
                deformed_tool_vertex_error_m=deformation.maximum_vertex_error_m)
    (folder/'reference_clearance_review.json').write_text(json.dumps(result,indent=2)+'\n');print('reference_review',samples,len(failures),dict(counts),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
