"""Labeled static visibility fixtures from the failed continuous approach 08.

Torso and window states are changed only in this offline evaluator. The
observer receives rendered RGB-D and native robot proprioception. These are
not executed motions, safe-pose proofs, calibration or manipulation success.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import mujoco
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
RUN = BASE/'runs/ftir_approach_08'
sys.path.insert(0, str(RUN/'actor_bundle/code'))
from ftir_slider_posture import initialize_slider
from ftir_slider_outcome import SliderRangeObservation
from ftir_vision import KeyRowObservation
from observations import StateEstimate, robot_joints


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    output = HERE/'candidate_views.json'
    if output.exists() or (HERE/'candidate_contract.json').exists():raise FileExistsError(output)
    result = json.loads((RUN/'result.json').read_text())
    event = next(e for e in result['actor_last_output']['events'] if 'grip_observations' in e)
    m = mujoco.MjModel.from_xml_path(str(RUN/'world.xml'))
    m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    d = mujoco.MjData(m)
    trace = dict(np.load(RUN/'trace.npz'))
    index = max(0, int(np.argmin(abs(trace['time']-225.5)))-1)
    pose = trace['qpos'][index].copy()
    actual = float(pose[int(m.joint('nicolet_door_slide').qposadr[0])])
    angles = [-.555, -.550, -.545, -.605, -.600, -.595]
    openings = [0., .060, .064, .065, .066, .068, .070, actual, .074, .075, .076, .080, .104]
    contract = dict(source_run=str(RUN),retained_preintegration_trace_index=index,
                    retained_time_s=float(trace['time'][index]),torso_yaws_rad=angles,
                    labeled_openings_m=openings,physical_requirement_m=[.065,.075],
                    observer_guard_m=[.066,.074],maximum_accepted_position_error_m=.001,
                    observer_changed=False,physical_execution=False,scope=__doc__)
    (HERE/'candidate_contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    cm = mujoco.MjModel.from_xml_path(str(RUN/'controller_model/world.xml'))
    xy = result['actor_last_output']['estimated_root_position_m'][:2]
    cd = initialize_slider(cm, xy)
    estimate = StateEstimate(cm,cd)
    prior = RUN/'policy_source/slider_push_prior.json'
    shape = RUN/'object_shape_source/nicolet_passive_dynamics.glb'
    observer = SliderRangeObservation(cm,cd,prior,shape,event['grip_observations'])
    keys = KeyRowObservation(cm,cd)
    names = [m.joint(j).name for j in robot_joints(m)]
    depth_renderer = mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000);depth_renderer.enable_depth_rendering()
    color_renderer = mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000)
    option = mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    rows=[]
    try:
        for yaw in angles:
            for opening in openings:
                d.qpos[:]=pose;d.qvel[:]=0.
                d.joint('waist_yaw_joint').qpos[0]=yaw
                d.joint('nicolet_door_slide').qpos[0]=opening
                mujoco.mj_forward(m,d)
                packet=dict(time_s=float(len(rows)),depth=None,
                            joint_position=np.array([d.sensor(n+'_encoder').data[0] for n in names]),
                            joint_velocity=np.array([d.sensor(n+'_velocity').data[0] for n in names]),
                            imu_quaternion=d.sensor('imu_orientation').data.copy(),
                            imu_gyro=d.sensor('imu_angular_velocity').data.copy())
                estimate.update(packet)
                depth_renderer.update_scene(d,camera='head_depth',scene_option=option)
                depth=depth_renderer.render().copy()
                color_renderer.update_scene(d,camera='head_rgb',scene_option=option)
                rgb=color_renderer.render().copy()
                key=keys.observe(rgb,depth);outcome=observer.observe(depth,key)
                predicted=outcome.get('baseline_corrected_position_m')
                filename=None
                if opening==actual:
                    filename=f'candidate_actual_opening_yaw_{yaw:.3f}.png';Image.fromarray(rgb).save(HERE/filename)
                row=dict(evaluator_yaw_rad=yaw,evaluator_opening_m=opening,
                         expected_in_physical_range=.065<=opening<=.075,
                         key_accepted=bool(key and key['accepted']),observation=outcome,
                         absolute_error_m=None if predicted is None else abs(predicted-opening),image=filename)
                rows.append(row)
                print(json.dumps(row),flush=True)
    finally:
        depth_renderer.close();color_renderer.close()
    deps=[Path(__file__),HERE/'candidate_contract.json',RUN/'world.xml',RUN/'controller_model/world.xml',
          RUN/'trace.npz',RUN/'result.json',prior,shape]
    deps += [RUN/'actor_bundle/code'/n for n in ['ftir_slider_outcome.py','ftir_slider_vision.py','ftir_vision.py','observations.py']]
    report=dict(rows=rows,physical_execution=False,observer_changed=False,
                false_acceptances=sum(r['observation']['accepted'] and not r['expected_in_physical_range'] for r in rows),
                source_sha256={str(p):sha(p) for p in deps},scope=__doc__)
    output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
