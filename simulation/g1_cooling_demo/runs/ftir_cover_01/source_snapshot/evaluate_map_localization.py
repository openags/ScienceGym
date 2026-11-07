"""Evaluate map registration on retained pixels; read truth only for scoring."""
import argparse,hashlib,json
from pathlib import Path
import mujoco
import numpy as np
from depth_io import load
from map_localization import MapLocalization


def evaluate(folder,out,times):
    folder=Path(folder);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    sensor=dict(np.load(folder/'sensor_observations.npz'));poses=json.loads((folder/'actor_pose_estimates.json').read_text())
    pose_times=np.array([p['time_s'] for p in poses]);model=mujoco.MjModel.from_xml_path(str(folder/'controller_model/world.xml'));data=mujoco.MjData(model)
    locator=MapLocalization(model,data);joints=[j for j in range(model.njnt) if model.jnt_type[j]==mujoco.mjtJoint.mjJNT_HINGE]
    qa=model.jnt_qposadr[joints];va=model.jnt_dofadr[joints];rows=[];wanted=set(times)
    try:
        for t,depth in load(folder):
            selected=next((x for x in wanted if abs(t-x)<.001),None)
            if selected is None:continue
            wanted.remove(selected);i=int(np.argmin(abs(sensor['time_s']-t)));k=int(np.argmin(abs(pose_times-t)))
            assert abs(sensor['time_s'][i]-t)<1e-6 and abs(pose_times[k]-t)<.011
            data.qpos[:3]=poses[k]['estimated_root_position_m'];data.qpos[3:7]=sensor['imu_quaternion'][i]
            data.qpos[qa]=sensor['joint_position'][i];data.qvel[va]=sensor['joint_velocity'][i];data.qvel[3:6]=sensor['imu_gyro'][i]
            mujoco.mj_kinematics(model,data);mujoco.mj_camlight(model,data);initial=data.qpos[:3].copy();result=locator.register(depth)
            rows.append(dict(time_s=float(t),initial_estimate_m=initial.tolist(),result=result));print('registered',round(t,2),result['accepted'],result.get('correction_m'),flush=True)
    finally:locator.close()
    assert not wanted,wanted
    # Evaluation starts after registration has produced its estimates.
    truth=dict(np.load(folder/'trace.npz'))
    for row in rows:
        i=int(np.argmin(abs(truth['time']-row['time_s'])));actual=truth['qpos'][i,:3]
        row['initial_error_m']=(np.array(row['initial_estimate_m'])-actual).tolist()
        if row['result']['accepted']:row['registered_error_m']=(np.array(row['result']['position_m'])-actual).tolist()
    report=dict(scope=__doc__,recorded_run=str(folder),rows=rows,accepted=sum(r['result']['accepted'] for r in rows),samples=len(rows),
                source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['map_localization.py','evaluate_map_localization.py']})
    for n in report['source_sha256']:(out/n).write_bytes(Path(__file__).with_name(n).read_bytes())
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(accepted=report['accepted'],samples=len(rows),initial_max_m=max(np.linalg.norm(r['initial_error_m']) for r in rows),registered_max_m=max((np.linalg.norm(r['registered_error_m']) for r in rows if 'registered_error_m' in r),default=None))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('out');p.add_argument('--times',type=float,nargs='+',default=[14.,15.,20.,30.,40.,50.,60.,70.,80.,90.]);a=p.parse_args();evaluate(a.folder,a.out,a.times)
