"""Test static-map localization on the actual coupon-observation frames.

The estimator receives the original pixels, robot encoders/IMU and public
controller map. Object and camera truth are read only after all predictions.
This retained-input experiment is not a newly executed robot trajectory.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from map_localization import MapLocalization
from observations import StateEstimate
from optical_coupon_observation import detect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path)
    p.add_argument('original_review',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args();run=a.run.resolve();out=a.output.resolve()
    old=json.loads(a.original_review.read_text())
    result=json.loads((run/'result.json').read_text())
    contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'result.json')==old['result_sha256']
    assert sha(run/'contract.json')==old['contract_sha256']==result['contract_sha256']
    assert sha(run/'sensors.npz')==result['sensors_sha256']
    assert sha(run/'camera_index.json')==old['camera_index_sha256']
    assert sha(run/'world.xml')==contract['model_sha256']
    assert sha(run/'policy_source/tool_prior.json')==contract['controller_prior_sha256']
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'map_localization.py','observations.py',
                 'optical_coupon_observation.py','build_tool_station.py']:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    prior=json.loads((run/'policy_source/tool_prior.json').read_text())
    m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    d=mujoco.MjData(m);d.qpos[:]=prior['initial_robot_qpos'];mujoco.mj_forward(m,d)
    est=StateEstimate(m,d)
    g=m.geom('lab_part_1514').id;k=m.geom_dataid[g]
    vertices=m.mesh_vert[m.mesh_vertadr[k]:m.mesh_vertadr[k]+m.mesh_vertnum[k]]
    vertices=vertices@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g]
    lo,hi=vertices.min(0),vertices.max(0);lo[2]=hi[2]+.002;hi[2]+=.18
    sensors=dict(np.load(run/'sensors.npz'))
    frames=json.loads((run/'camera_index.json').read_text());rows=[];locator=None

    def camera(name):
        cid=m.camera(name).id;T=np.eye(4)
        T[:3,:3]=d.cam_xmat[cid].reshape(3,3);T[:3,3]=d.cam_xpos[cid]
        return T,float(m.cam_fovy[cid])

    try:
        for entry in old['observed_frame_diagnostics']:
            t=entry['time_s'];i=int(np.argmin(abs(sensors['time_s']-t)))
            assert abs(sensors['time_s'][i]-t)<1e-9
            obs={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
            # Each frame begins with the original fixed-foot estimate, so a
            # previous diagnostic correction cannot leak into a later input.
            est.update(dict(obs,depth=None))
            frame=frames[entry['frame_id']];path=run/frame['file']
            assert sha(path)==frame['sha256']
            with np.load(path) as z:rgb=z['head_rgb'];depth=z['head_depth']
            if locator is None:
                locator=MapLocalization(m,d,width=depth.shape[1],height=depth.shape[0],pixel_center=.5)
            registration=locator.register(depth)
            D,df=camera('head_depth');C,cf=camera('head_rgb')
            found=detect(rgb,depth,D,C,df,cf,[lo,hi]) if registration['accepted'] else None
            rows.append(dict(time_s=t,frame_id=entry['frame_id'],frame_sha256=frame['sha256'],
                registration=registration,observation=found,estimated_camera_m=D[:3,3].tolist()))
            print('registered',t,registration['accepted'],registration.get('correction_m'),flush=True)
        # Missing depth must not manufacture a valid static-map registration.
        est.update(dict(obs,depth=None))
        blank=locator.register(np.full_like(depth,np.nan))
    finally:
        if locator is not None:locator.close()
    del sensors
    # All estimator calls finish before opening native trajectory/object truth.
    assert sha(run/'trace.npz')==result['trace_sha256']==old['trace_sha256']
    plant=mujoco.MjModel.from_xml_path(str(run/'world.xml'));truth=mujoco.MjData(plant)
    trace=np.load(run/'trace.npz');times=trace['time'];q=trace['qpos']
    gid=plant.geom('optical_copper_witness').id;mid=plant.geom_dataid[gid]
    points=plant.mesh_vert[plant.mesh_vertadr[mid]:plant.mesh_vertadr[mid]+plant.mesh_vertnum[mid]]
    local_center=(points.min(0)+points.max(0))/2;centers=[];normals=[]
    for row in rows:
        i=int(np.argmin(abs(times-row['time_s'])));assert abs(times[i]-row['time_s'])<1e-8
        truth.qpos[:]=q[i];mujoco.mj_forward(plant,truth)
        center=truth.geom_xpos[gid]+truth.geom_xmat[gid].reshape(3,3)@local_center
        normal=truth.body('optical_witness_white').xmat.reshape(3,3)[:,2].copy()
        if normal@(np.asarray(row['estimated_camera_m'])-center)<0:normal=-normal
        if row['observation'] and row['observation']['candidate_found']:
            candidate=row['observation']['candidate'];c=np.asarray(candidate['center_m']);n=np.asarray(candidate['normal_toward_camera'])
            row.update(center_error_m=float(np.linalg.norm(c-center)),
                normal_error_rad=float(np.arccos(np.clip(n@normal,-1,1))))
            centers.append(c);normals.append(n)
    trace.close();del q
    complete=len(centers)==4
    error=angle=None;stable=False
    if complete:
        fitted=np.median(centers,axis=0);n=np.mean(normals,axis=0);n/=np.linalg.norm(n)
        error=float(np.linalg.norm(fitted-center));angle=float(np.arccos(np.clip(n@normal,-1,1)))
        stable=bool(np.max(np.linalg.norm(np.asarray(centers)-fitted,axis=1))<=.001 and np.min(np.asarray(normals)@n)>=np.cos(.03))
    checks=dict(four_registered_observations=complete,missing_depth_rejected=not blank['accepted'],
        four_frame_stability=stable,center_within_one_millimetre=error is not None and error<=.001,
        normal_within_five_degrees=angle is not None and angle<=np.deg2rad(5))
    checks={name:bool(value) for name,value in checks.items()}
    report=dict(scope=__doc__,checks=checks,passed_recorded_observation_test=all(checks.values()),
        accepted_center_error_m=error,accepted_normal_error_rad=angle,frames=rows,blank_depth=blank,
        original_review_sha256=sha(a.original_review),source_result_sha256=sha(run/'result.json'),
        source_trace_sha256=result['trace_sha256'],source_sensor_sha256=result['sensors_sha256'],
        predictor_sha256=sha(run/'controller_model/world.xml'),
        source_sha256={f.name:sha(f) for f in out.glob('*.py')},
        fresh_robot_execution=False,qualified_perception=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checks=checks,accepted_center_error_m=error)),flush=True)
    if not all(checks.values()):raise SystemExit(1)


if __name__=='__main__':main()
