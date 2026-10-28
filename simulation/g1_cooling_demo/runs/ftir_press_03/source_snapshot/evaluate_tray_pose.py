"""Estimate tray pose from retained sensors, then score against held-out truth."""
import argparse,hashlib,json
from pathlib import Path
import mujoco
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from depth_io import load
from map_localization import MapLocalization
from tracking import TrayTracker
from tray_pose import TrayPose


def evaluate(folder,out,times):
    folder=Path(folder);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    names=['tray_pose.py','evaluate_tray_pose.py','map_localization.py','tracking.py']
    pins={}
    for name in names:
        path=Path(__file__).with_name(name);(out/name).write_bytes(path.read_bytes());pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    root=Path(__file__).resolve().parents[2]
    source=root/'assets/cooling_lab_v1/geometry/buerkle_4208_0022.glb'
    mesh=trimesh.load(source,force='scene').to_geometry();estimator=TrayPose(mesh.vertices,mesh.faces)
    sensor=dict(np.load(folder/'sensor_observations.npz'));poses=json.loads((folder/'actor_pose_estimates.json').read_text())
    pose_times=np.array([p['time_s'] for p in poses]);model=mujoco.MjModel.from_xml_path(str(folder/'controller_model/world.xml'));data=mujoco.MjData(model)
    locator=MapLocalization(model,data);tracker=TrayTracker(model,data)
    joints=[j for j in range(model.njnt) if model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
    qa=model.jnt_qposadr[joints];rows=[];wanted=set(times)
    try:
        for t,depth in load(folder):
            selected=next((x for x in wanted if abs(t-x)<.001),None)
            if selected is None:continue
            wanted.remove(selected);i=int(np.argmin(abs(sensor['time_s']-t)));k=int(np.argmin(abs(pose_times-t)))
            data.qpos[:3]=poses[k]['estimated_root_position_m'];data.qpos[3:7]=sensor['imu_quaternion'][i];data.qpos[qa]=sensor['joint_position'][i]
            mujoco.mj_kinematics(model,data);mujoco.mj_camlight(model,data)
            localization=locator.register(depth)
            if not localization['accepted']:raise RuntimeError('Static map localization failed')
            old=tracker.observe(depth);h,w=depth.shape;fy=h/(2*np.tan(np.radians(58)/2));v,u=np.mgrid[:h,:w]
            camera=model.camera('head_depth').id
            xyz=np.stack([(u+.5-w/2)*depth/fy,-(v+.5-h/2)*depth/fy,-depth],axis=-1)
            world=xyz@data.cam_xmat[camera].reshape(3,3).T+data.cam_xpos[camera]
            cloud=world[tracker.last_mask]
            fit=estimator.estimate(cloud)
            np.savez_compressed(out/f'cloud_{t:.1f}.npz',points=cloud)
            rows.append(dict(time_s=float(t),map_registration=localization,legacy_observation=old,estimate=fit))
            print('fit',round(t,2),fit.get('accepted'),round(fit.get('tilt_deg',-1),2),round(fit.get('inlier_fraction',0),3),flush=True)
    finally:locator.close();tracker.close()
    if wanted:raise RuntimeError('Missing requested depth frames: '+str(wanted))
    # Truth is read only here, after every estimate has been produced.
    truth=dict(np.load(folder/'trace.npz'));plant=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));adr=plant.joint('tray_free').qposadr[0]
    for row in rows:
        i=int(np.argmin(abs(truth['time']-row['time_s'])));pose=truth['qpos'][i,adr:adr+7];actual=Rotation.from_quat(pose[[4,5,6,3]]).as_matrix()
        row['true_tilt_deg']=float(np.degrees(np.arccos(np.clip(actual[2,2],-1,1))))
        estimate=row['estimate']
        if 'position_m' in estimate:
            row['translation_error_m']=(np.asarray(estimate['position_m'])-pose[:3]).tolist()
            # Tray geometry has 180-degree yaw symmetry. Score both equivalent poses.
            predicted=np.asarray(estimate['rotation_matrix']);symmetry=Rotation.from_euler('z',180,degrees=True).as_matrix()
            row['orientation_error_deg']=min(float(np.degrees(Rotation.from_matrix(predicted@alternative.T).magnitude())) for alternative in [actual,actual@symmetry])
    report=dict(recorded_run=str(folder),rows=rows,source_sha256=pins,shape_prior_path=str(source.relative_to(root)),shape_prior_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope=__doc__,runtime_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([dict(time=r['time_s'],accepted=r['estimate']['accepted'],tilt=r['estimate'].get('tilt_deg'),true_tilt=r['true_tilt_deg'],position_error_mm=float(np.linalg.norm(r['translation_error_m'])*1000) if 'translation_error_m' in r else None,orientation_error_deg=r.get('orientation_error_deg')) for r in rows]),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('out');p.add_argument('--times',nargs='+',type=float,default=[15.,25.,29.,31.,33.,34.,36.,38.,40.,43.,48.,52.,62.,67.,70.,78.,87.,95.]);a=p.parse_args();evaluate(a.folder,a.out,a.times)
