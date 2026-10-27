"""Independently check the exported cover, keys, contacts and acquisition order.

Source meshes are checked against the exported whole laboratory. Cover and key
transforms are reconstructed from their actual instrument interfaces. The
acquisition checks establish the represented operation sequence, not spectra.
"""
import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import fcl
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from source_geometry import ROOT, manifest_for_export, robot_meshes
from audit_geometry import ARTICULATED, matrix, mesh_scene, joined
from environment_poses import EnvironmentPoses
from deformed_geometry import DeformedGeometry


def translation(xyz):
    value=np.eye(4);value[:3,3]=xyz;return value


def audit(folder):
    folder=Path(folder);receipt=json.loads((folder/'export.json').read_text())
    assert receipt['episode']=='ftir_measurement'
    manifest=manifest_for_export(folder);assets={a['id']:a for a in manifest['assets']}
    config=json.loads((folder/'source/single_measurement_episode.json').read_text())
    segments={s['id']:s for s in config['segments']}
    interface_path=ROOT/'assets/nicolet_6700_v1/interfaces.json'
    interface_bytes=interface_path.read_bytes();interfaces=json.loads(interface_bytes)
    (folder/'nicolet_interfaces.json').write_bytes(interface_bytes)
    cover_names=set(interfaces['cover_parts']);keys={'scan_key_'+str(i) for i in range(4)};moving_names=cover_names|keys
    moving=trimesh.collision.CollisionManager();obstacles=trimesh.collision.CollisionManager();defaults={};instances=[];rest={}
    source=mesh_scene(manifest['architecture']['path'])
    for name in source.graph.nodes_geometry:
        pose,key=source.graph[name];obstacles.add_object('room::'+name,source.geometry[key],pose)
    for identity,asset in assets.items():
        if identity=='g1':continue
        source=mesh_scene(asset['geometry'])
        if identity in ARTICULATED:
            for name in source.graph.nodes_geometry:
                pose,key=source.graph[name];label=identity+'::'+name
                if identity=='nicolet' and name in moving_names:
                    moving.add_object(label,source.geometry[key],pose);rest[name]=pose
                else:obstacles.add_object(label,source.geometry[key],pose);defaults[label]=(identity,pose)
        else:obstacles.add_object(identity,joined(source));instances.append(identity)
    for extra in receipt['scene']['extraGeometry']:
        mesh=trimesh.Trimesh(vertices=np.array(extra['vertices']).reshape(-1,3),faces=np.array(extra['indices']).reshape(-1,3),process=False)
        obstacles.add_object('extra::'+extra['id'],mesh)
    poses=EnvironmentPoses(obstacles,instances,defaults);deformation=DeformedGeometry(folder,manifest)
    hand=trimesh.collision.CollisionManager()
    for name,mesh in robot_meshes('right').items():
        if 'index' in name or 'thumb' in name:hand.add_object(name,mesh)
    def gap(digit,target):
        distances=[]
        for name in hand._objs:
            if digit not in name:continue
            result=fcl.DistanceResult();fcl.distance(hand._objs[name]['obj'],target,fcl.DistanceRequest(),result)
            distances.append(float(result.min_distance))
        return min(distances)
    cover=next(i for i in interfaces['interfaces'] if i['id']=='sample_cover')
    normal=np.array(assets['nicolet']['normalization_matrix'])
    pivot=(normal@np.r_[cover['pivot_m'],1.])[:3]
    controls={i['id']:i for i in interfaces['interfaces'] if i['kind']=='push_button'}
    setup=json.loads((folder/'source/optical_setup.json').read_text())
    ref=json.loads((folder/'source/reference_transfer.json').read_text())
    sample_pose=translation(np.array(setup['ports']['ftir_sample']['position_m'])+[0,0,.000001])
    protected=translation(ref['storage_offset_m'])
    failures=[];kinematic=[];contacts=[];acquisition=[];pressed=set();seen_acquisitions=[]
    active_acquisition=None;acquisition_buttons=set()
    max_object=0.;maximum_gap={};samples=0;digest=hashlib.sha256();bounded=defaultdict(int)
    print('mechanism_geometry_ready',len(obstacles._objs),flush=True)
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            digest.update(line.encode());frame=json.loads(line);samples+=1;state=frame['measurement_state'];segment=segments[frame['phase']]
            poses.update(frame);deformation.apply(obstacles,frame)
            if samples%200==1:poses.verify(frame)
            actual={p['name']:matrix(p['matrix']) for p in frame['parts'] if p['asset']=='nicolet'}
            for name in moving_names:moving.set_transform('nicolet::'+name,actual[name])
            _,pairs,data=moving.in_collision_other(obstacles,return_names=True,return_data=True)
            bad={}
            for item in data:
                pair=tuple(sorted(item.names));depth=abs(float(item.depth))
                if depth<=1e-7:bounded['numeric_surface_contact']+=1;continue
                bad[pair]=max(depth,bad.get(pair,0.))
            if bad:failures.append(dict(time_s=frame['time_s'],phase=frame['phase'],pairs=[dict(parts=list(p),depth_m=v) for p,v in bad.items()]))
            rotate=np.eye(4);rotate[:3,:3]=Rotation.from_euler('x',state['cover_angle_rad']).as_matrix()
            cover_delta=translation(pivot)@rotate@translation(-pivot)
            group=matrix(frame['groups']['nicolet']);expected={n:group@cover_delta@rest[n] for n in cover_names}
            for identity,info in controls.items():
                name='scan_key_'+identity.split('_')[-1]
                travel=state['button_travel_m'] if state['button']==identity else 0.
                expected[name]=group@translation(np.array(info['axis'])*travel)@rest[name]
            error=max(float(np.max(abs(actual[n]-expected[n]))) for n in moving_names);max_object=max(max_object,error)
            if error>1e-7 or not -.0000001<=state['button_travel_m']<=.0003001:
                kinematic.append(dict(time_s=frame['time_s'],phase=frame['phase'],matrix_error=error,button_travel_m=state['button_travel_m']))
            for name in hand._objs:hand.set_transform(name,matrix(frame['links'][name]))
            if state['button'] and state['button_travel_m']>1e-8:
                target=moving._objs['nicolet::scan_key_'+state['button'].split('_')[-1]]['obj'];distance=gap('index',target)
                maximum_gap['button_index']=max(maximum_gap.get('button_index',0.),distance)
                if not 1e-6<=distance<=.00025:contacts.append(dict(time_s=frame['time_s'],phase=frame['phase'],kind='button',gap_m=distance))
                else:pressed.add(state['button'])
            e=state['source_action_elapsed_s']
            if state['source_action'] in ['ftir_open','ftir_close'] and e is not None and 8.2<=e<=11.2:
                target=moving._objs['nicolet::lid_handle_bar']['obj'];distances={d:gap(d,target) for d in ['index','thumb']}
                for digit,distance in distances.items():maximum_gap['cover_'+digit]=max(maximum_gap.get('cover_'+digit,0.),distance)
                if not all(1e-6<=d<=.00025 for d in distances.values()):contacts.append(dict(time_s=frame['time_s'],phase=frame['phase'],kind='cover',gaps_m=distances))
            if state['acquisition']:
                kind=state['acquisition']['kind'];needed={'scan_1','scan_2'} if kind=='background' else {'scan_0','scan_2'}
                if active_acquisition!=kind:
                    acquisition_buttons=set(pressed);pressed.clear();active_acquisition=kind
                ref_delta=np.array(state['reference_delta']);reference_expected=np.eye(4) if kind=='background' else protected
                problems=[]
                if abs(state['cover_angle_rad'])>1e-7:problems.append('compartment_open')
                if not needed<=acquisition_buttons:problems.append('missing_valid_button_contact')
                if np.max(abs(ref_delta-reference_expected))>1e-6:problems.append('wrong_reference_location')
                if kind=='sample' and np.max(abs(matrix(frame['groups']['optical_witness_white'])-sample_pose))>1e-6:problems.append('sample_not_at_port')
                if segment['tool_held'] or segment['held_specimen']:problems.append('held_object_during_acquisition')
                if problems:acquisition.append(dict(time_s=frame['time_s'],phase=frame['phase'],problems=problems))
                if not seen_acquisitions or seen_acquisitions[-1]!=kind:seen_acquisitions.append(kind)
            else:active_acquisition=None
            if samples%400==0:print('mechanism_checked',samples,flush=True)
    assert samples==receipt['frame_count'] and digest.hexdigest()==receipt['frames_sha256']
    result=dict(scope=__doc__,passed=not(failures or kinematic or contacts or acquisition) and seen_acquisitions==['background','sample'],
                samples=samples,intersection_frames=failures,kinematic_failures=kinematic,contact_failures=contacts,
                acquisition_sequence_failures=acquisition,acquisition_order=seen_acquisitions,
                maximum_object_matrix_error=max_object,maximum_grip_gaps_m=maximum_gap,
                bounded_contacts=dict(bounded),frames_sha256=digest.hexdigest(),
                interface_sha256=hashlib.sha256(interface_bytes).hexdigest(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'ftir_mechanism_review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],samples=samples,collisions=len(failures),kinematic=len(kinematic),
                          contacts=len(contacts),acquisition=len(acquisition),maximum_grip_gaps_m=maximum_gap)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
