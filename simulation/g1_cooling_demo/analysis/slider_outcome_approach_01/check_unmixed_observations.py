"""Counterfactual depth-buffer fixtures; no new physical execution credit.

Use retained robot poses, native RGB and proprioception; re-render depth with
MSAA disabled. Re-estimate the closed baseline before testing the unchanged
observer. Static labeled window positions test false acceptance separately.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import inspect_visible_surfaces as v
import mujoco
import numpy as np
from ftir_slider_vision import SliderObservation
from sensor_rendering import depth_renderer


def main():
    run=v.BASE/'runs/ftir_approach_09';out=Path(__file__).with_name('unmixed_observations_09.json')
    if out.exists():raise FileExistsError(out)
    responses=json.loads((run/'actor_responses.json').read_text())
    baseline_times=[r['time_s'] for r in responses if (r.get('grip_observation') or {}).get('accepted')][-8:]
    times=baseline_times+[225.5+.1*i for i in range(8)]
    sensors=dict(np.load(run/'sensor_observations.npz'));trace=dict(np.load(run/'trace.npz'))
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));cd=v.initialize_slider(cm)
    estimate=v.StateEstimate(cm,cd);keys=v.KeyRowObservation(cm,cd)
    args=(cm,cd,run/'policy_source/slider_push_prior.json',run/'object_shape_source/nicolet_passive_dynamics.glb')
    closed=SliderObservation(*args);baselines=[];observer=None;rows=[]
    original_samples=int(m.vis.quality.offsamples);renderer=depth_renderer(m,360,640)
    if int(m.vis.quality.offsamples)!=original_samples:raise ValueError('Model rendering preference not restored')
    context_samples=int(renderer._mjr_context.offSamples)
    if context_samples!=0:raise ValueError('Depth context is multisampled')
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    rgb_cache={}
    for time in times:
        rgb_cache[time]=v.frame(run,'head_rgb_index.json','chunks',time)
    def observe(time,opening=None):
        i=int(np.argmin(abs(sensors['time_s']-time)));ti=max(0,int(np.argmin(abs(trace['time']-time)))-1)
        d.qpos[:]=trace['qpos'][ti]
        if opening is not None:d.joint('nicolet_door_slide').qpos[0]=opening
        mujoco.mj_forward(m,d)
        renderer.update_scene(d,camera='head_depth',scene_option=option);depth=renderer.render().copy()
        packet={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
        packet['depth']=depth;estimate.update(packet)
        key=keys.observe(rgb_cache[time],depth)
        fit=(closed if observer is None else observer).observe(depth,key)
        row=dict(time_s=time,observation=fit,key_accepted=bool(key and key['accepted']),labeled_window_position_m=opening)
        if observer is not None:
            actual=float(d.joint('nicolet_door_slide').qpos[0]);prediction=fit.get('baseline_corrected_position_m')
            row.update(evaluated_actual_slider_m=actual,absolute_error_m=None if prediction is None else abs(prediction-actual),
                       expected_in_physical_range=.065<=actual<=.075)
        rows.append(row);print(json.dumps(row),flush=True)
        return fit
    try:
        for time in baseline_times:baselines.append(observe(time))
        observer=v.SliderRangeObservation(*args,baselines)
        for time in times[8:]:observe(time)
        for opening in [0.,.060,.064,.065,.066,.068,.070,.074,.075,.076,.080,.104]:observe(225.5,opening)
    finally:renderer.close()
    outcome=rows[8:16];labels=rows[16:]
    checks=dict(eight_closed_baselines=len(baselines)==8 and all(r['accepted'] for r in baselines),
                eight_accepted_outcome_frames=len(outcome)==8 and all(r['observation']['accepted'] for r in outcome),
                accepted_error_below_one_mm=all(r['absolute_error_m']<.001 for r in rows[8:] if r['observation']['accepted']),
                no_out_of_range_false_acceptance=not any(r['observation']['accepted'] and not r['expected_in_physical_range'] for r in labels),
                pixel_centre_depth_context=context_samples==0,model_render_preference_preserved=int(m.vis.quality.offsamples)==original_samples)
    report=dict(scope=__doc__,passed=all(checks.values()),checks=checks,rows=rows,
                physical_execution=False,native_depth_replay=False,original_rgb_multisamples=original_samples,depth_context_multisamples=context_samples,
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),v.BASE/'sensor_rendering.py',v.BASE/'run_ftir_press.py',v.BASE/'ftir_slider_vision.py',v.BASE/'ftir_slider_outcome.py',run/'world.xml',run/'trace.npz',run/'result.json']})
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(checks),flush=True)


if __name__=='__main__':main()
