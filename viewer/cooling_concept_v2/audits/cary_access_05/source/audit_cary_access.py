"""Independently review exported Cary moving parts and source hand ownership.

Source triangles are tested against the entire exported room. Exact source FK,
held-hood registration, lid-axis motion, finger clearances and bench seating are
checked. This is sampled geometry, not contact forces or dynamic qualification.
"""
import argparse,gzip,hashlib,json
from collections import defaultdict
from pathlib import Path
import fcl,numpy as np,trimesh
from source_geometry import manifest_for_export,fk,robot_meshes
from audit_geometry import ARTICULATED,matrix,mesh_scene,joined
from environment_poses import EnvironmentPoses


def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text());manifest=manifest_for_export(folder)
    assert receipt['episode']=='cary_access'
    config=json.loads((folder/'source/cary_access_episode.json').read_text());segments={s['id']:s for s in config['segments']};assert len(segments)==len(config['segments'])
    cover_names=set(config['cover_parts']);lid_names=set(config['lid_parts']);moving_names=cover_names|lid_names
    obstacles=trimesh.collision.CollisionManager();cover=trimesh.collision.CollisionManager();lid=trimesh.collision.CollisionManager();defaults={};instances=[];cary_meshes={}
    source=mesh_scene(manifest['architecture']['path']);worktop=None
    for n in source.graph.nodes_geometry:
        pose,key=source.graph[n];mesh=source.geometry[key];obstacles.add_object('room::'+n,mesh,pose)
        if n=='cary_bench_worktop':worktop=trimesh.transform_points(mesh.vertices,pose)
    assert worktop is not None
    for asset in manifest['assets']:
        identity=asset['id']
        if identity=='g1':continue
        source=mesh_scene(asset['geometry'])
        if identity in ARTICULATED:
            for n in source.graph.nodes_geometry:
                pose,key=source.graph[n];mesh=source.geometry[key];label=identity+'::'+n
                if identity=='cary':cary_meshes[n]=mesh
                if identity=='cary' and n in moving_names:(cover if n in cover_names else lid).add_object(label,mesh,pose)
                else:obstacles.add_object(label,mesh,pose);defaults[label]=(identity,pose)
        else:obstacles.add_object(identity,joined(source));instances.append(identity)
    for item in receipt['scene']['extraGeometry']:
        obstacles.add_object('extra::'+item['id'],trimesh.Trimesh(vertices=np.array(item['vertices']).reshape(-1,3),faces=np.array(item['indices']).reshape(-1,3),process=False))
    poses=EnvironmentPoses(obstacles,instances,defaults);rest={p['name']:matrix(p['matrix']) for p in config['initial_scene']['parts'] if p['asset']=='cary'};inverse_grasp=np.linalg.inv(config['grasp_palm_world'])
    fingers={n:mesh for n,mesh in robot_meshes('right').items() if 'index' in n or 'thumb' in n};finger_manager=trimesh.collision.CollisionManager()
    for n,mesh in fingers.items():finger_manager.add_object(n,mesh)
    failures=[];kinematic=[];grip_failures=[];support_failures=[];bounded=defaultdict(int);bounded_overlap={};max_fk=0.;max_object=0.;max_gap={};support_min=1.;support_max=-1.;samples=0;seen=set();digest=hashlib.sha256()
    print('cary_geometry_ready',len(obstacles._objs),flush=True)
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            digest.update(line.encode());frame=json.loads(line);samples+=1;segment=segments[frame['phase']];seen.add(frame['phase']);poses.update(frame)
            if samples%200==1:poses.verify(frame)
            parts={p['name']:matrix(p['matrix']) for p in frame['parts'] if p['asset']=='cary'}
            for names,manager in [(cover_names,cover),(lid_names,lid)]:
                for n in names:manager.set_transform('cary::'+n,parts[n])
            unexpected={}
            for a,b in [(cover,obstacles),(lid,obstacles),(cover,lid)]:
                _,pairs,contacts=a.in_collision_other(b,return_names=True,return_data=True)
                for contact in contacts:
                    pair=tuple(sorted(contact.names));depth=abs(float(contact.depth))
                    if depth<=1e-7:continue
                    short=[n.split('::',1)[1] if n.startswith('cary::') else '' for n in pair]
                    sheet=next((n for n in short if n.startswith('extension_cover_side_')),None)
                    bearing=next((n for n in short if n.startswith('extension_base_rail_') or n=='extension_hinge_bar'),None)
                    if sheet and bearing:
                        x=trimesh.transform_points(cary_meshes[sheet].vertices,parts[sheet])[:,0];y=trimesh.transform_points(cary_meshes[bearing].vertices,parts[bearing])[:,0]
                        normal_overlap=float(min(x.max(),y.max())-max(x.min(),y.min()))
                        if normal_overlap<=1e-6:
                            label=' / '.join(pair);bounded[label]+=1;bounded_overlap[label]=max(bounded_overlap.get(label,-1.),normal_overlap);continue
                    # The front skirt seats on the retained base plate. These
                    # nominally coincident horizontal faces can produce an FCL
                    # tangential depth; bound their actual Z overlap instead.
                    if set(short)=={'extension_cover_front','extension_base_plate'}:
                        x=trimesh.transform_points(cary_meshes['extension_cover_front'].vertices,parts['extension_cover_front'])[:,2];y=trimesh.transform_points(cary_meshes['extension_base_plate'].vertices,parts['extension_base_plate'])[:,2]
                        normal_overlap=float(min(x.max(),y.max())-max(x.min(),y.min()))
                        if normal_overlap<=1e-6:
                            label=' / '.join(pair);bounded[label]+=1;bounded_overlap[label]=max(bounded_overlap.get(label,-1.),normal_overlap);continue
                    unexpected[pair]=max(depth,unexpected.get(pair,0.))
            if unexpected:failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=[dict(parts=list(pair),depth_m=value) for pair,value in unexpected.items()]))
            root=matrix(frame['groups']['g1']);world=fk(frame['joints']);fk_error=max(float(np.max(abs(matrix(frame['links'][n])-root@p))) for n,p in world.items());max_fk=max(max_fk,fk_error)
            state=frame['cary_state'];delta=root@world['right_palm_force_sensor']@inverse_grasp if segment['cover_held'] else np.array(segment['rows'][0]['cover_matrix'])
            slide=np.eye(4);slide[1,3]=state['lid_m']
            object_error=max(float(np.max(abs(parts[n]-(delta if n in cover_names else slide)@rest[n]))) for n in moving_names);max_object=max(max_object,object_error)
            if fk_error>1e-7 or object_error>1e-7 or state['cover_held']!=segment['cover_held']:kinematic.append(dict(time_s=frame['time_s'],phase=frame['phase'],fk_error=fk_error,object_error=object_error))
            if segment['cover_held'] or segment.get('lid_held',segment['id']=='lid_slide'):
                handle=(cover._objs['cary::extension_pull_bar'] if segment['cover_held'] else lid._objs['cary::sample_lid_pull'])['obj'];kind='cover' if segment['cover_held'] else 'lid';gaps={}
                for name in fingers:finger_manager.set_transform(name,root@world[name])
                for finger in ['index','thumb']:
                    values=[]
                    for n in fingers:
                        if finger not in n:continue
                        distance=fcl.DistanceResult();fcl.distance(finger_manager._objs[n]['obj'],handle,fcl.DistanceRequest(),distance);values.append(float(distance.min_distance))
                    gaps[finger]=min(values);max_gap[kind+'_'+finger]=max(max_gap.get(kind+'_'+finger,0),gaps[finger])
                if min(gaps.values())<1e-6 or max(gaps.values())>.00025:grip_failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],kind=kind,gaps_m=gaps))
            if not segment['cover_held'] and np.linalg.norm(delta[:3,3])>.001:
                points=np.vstack([trimesh.transform_points(cary_meshes[n].vertices,parts[n]) for n in cover_names]);lo=points.min(axis=0);hi=points.max(axis=0);gap=float(lo[2]-worktop[:,2].max());support_min=min(support_min,gap);support_max=max(support_max,gap)
                if not(-1e-6<=gap<=1e-5 and np.all(lo[:2]>=worktop[:,:2].min(axis=0)) and np.all(hi[:2]<=worktop[:,:2].max(axis=0))):support_failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],gap_m=gap,bounds_m=[lo.tolist(),hi.tolist()]))
            if samples%400==0:print('cary_checked',samples,flush=True)
    assert samples==receipt['frame_count'] and digest.hexdigest()==receipt['frames_sha256']
    missing=sorted(set(receipt['selected_phases'])-seen)
    result=dict(scope=__doc__,passed=not(failures or kinematic or grip_failures or support_failures or missing),samples=samples,missing_phases=missing,intersection_frames=failures,kinematic_failures=kinematic,grip_clearance_failures=grip_failures,support_failures=support_failures,bounded_bearing_contact_counts=dict(bounded),maximum_bounded_normal_overlap_m=bounded_overlap,maximum_source_fk_matrix_error=max_fk,maximum_object_matrix_error=max_object,maximum_grip_gaps_m=max_gap,bench_seating_gap_range_m=[support_min,support_max],frames_sha256=digest.hexdigest(),source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['audit_cary_access.py','source_geometry.py','environment_poses.py','audit_geometry.py']})
    (folder/'cary_access_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],samples=samples,collision_frames=len(failures),kinematic_failures=len(kinematic),grip_failures=len(grip_failures),support_failures=len(support_failures),maximum_grip_gaps_m=max_gap)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
