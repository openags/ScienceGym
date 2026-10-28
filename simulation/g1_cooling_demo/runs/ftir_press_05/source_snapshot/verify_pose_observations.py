"""Independent scoring of CAD pose observations and the declared level carry."""
import argparse,hashlib,json
from pathlib import Path
import mujoco,numpy as np,trimesh
from scipy.spatial.transform import Rotation


def verify(folder):
    folder=Path(folder);root=Path(__file__).resolve().parents[2]
    result=json.loads((folder/'result.json').read_text());trace=dict(np.load(folder/'trace.npz'))
    model=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));adr=model.joint('tray_free').qposadr[0]
    poses=trace['qpos'][:,adr:adr+7];rotations=Rotation.from_quat(poses[:,[4,5,6,3]])
    tilt=np.degrees(np.arccos(np.clip(rotations.as_matrix()[:,2,2],-1,1)))
    checks=[]
    def check(name,value,**details):checks.append(dict(name=name,passed=bool(value),**details))
    prior=json.loads((folder/'shape_prior.json').read_text());shape=np.load(folder/'object_shape_source/tray_geometry.npz')
    source=root/'assets/cooling_lab_v1/geometry/buerkle_4208_0022.glb'
    mesh=trimesh.load(source,force='scene').to_geometry()
    check('shape_prior_is_only_declared_cad',set(shape.files)=={'vertices','faces'} and np.array_equal(shape['vertices'],mesh.vertices) and np.array_equal(shape['faces'],mesh.faces) and prior['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest())
    observations=json.loads((folder/'policy_observations.json').read_text());errors=[];symmetry=Rotation.from_euler('z',180,degrees=True).as_matrix()
    for row in observations:
        observation=row['observation'];time=row['capture_time_s']
        i=int(np.argmin(abs(trace['time']-time)));assert abs(trace['time'][i]-time)<.0021
        actual=rotations[i].as_matrix();predicted=np.asarray(observation['rotation_matrix'])
        rotation_error=min(float(np.degrees(Rotation.from_matrix(predicted@r.T).magnitude())) for r in [actual,actual@symmetry])
        translation_error=float(np.linalg.norm(np.array(observation['position_m'])-poses[i,:3]))
        errors.append(dict(time_s=time,translation_error_m=translation_error,orientation_error_deg=rotation_error,estimated_tilt_deg=observation['tilt_deg'],actual_tilt_deg=float(tilt[i])))
    bad=[e for e in errors if e['translation_error_m']>.01 or e['orientation_error_deg']>3]
    check('accepted_pose_estimates_within_declared_development_bounds',bool(errors) and not bad,samples=len(errors),failures=len(bad),first_failures=bad[:20])
    lifted=poses[:,2]-poses[0,2]>.03
    maximum_tilt=float(np.max(tilt[lifted])) if np.any(lifted) else None
    check('level_carry_below_eight_degrees',np.any(lifted) and maximum_tilt<8,maximum_tilt_while_lifted_deg=maximum_tilt,threshold_deg=8)
    events=result['actor_last_output'].get('policy_events',[]);transfers=[e for e in events if e['state']=='transfer'];authorized=[]
    for event in transfers:
        evidence=event.get('evidence') or {};i=int(np.argmin(abs(trace['time']-event['time_s'])))
        authorized.append(bool(evidence.get('accepted')) and evidence.get('tilt_deg',180)<8 and tilt[i]<10)
    check('transfer_requires_observed_level_pose',len(transfers)==2 and all(authorized),transfer_count=len(transfers),actual_level_at_transfer=authorized)
    check('task_completed_without_recovery_abort',result['status']=='completed' and not any(e['state'].startswith('recover_') for e in events))
    out=dict(passed=all(c['passed'] for c in checks),checks=checks,
             metrics=dict(accepted_observations=len(errors),maximum_translation_error_m=max((e['translation_error_m'] for e in errors),default=None),maximum_orientation_error_deg=max((e['orientation_error_deg'] for e in errors),default=None)),
             scope='Development pose and level-carry checks only; not payload, collision, reliability or paper qualification.',
             trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    archive=folder/'verification_source';archive.mkdir(exist_ok=True);(archive/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (folder/'pose_verification.json').write_text(json.dumps(out,indent=2)+'\n');(folder/'pose_errors.json').write_text(json.dumps(errors)+'\n')
    print(json.dumps(out));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
    if not verify(a.folder)['passed']:raise SystemExit(1)
