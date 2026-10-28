"""Diagnose a contact-plane opening estimate from native-derived robot states.

Predictions are saved before loading the plant. A sloped grip converts normal
preload displacement into slider travel; a 70 mm wrist stroke need not produce
a 70 mm opening. This is an offline development check, not a new controller.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import mujoco
import numpy as np
from ftir_hand import PointingHand
from observations import robot_joints


def run(folder, output):
    folder,output=Path(folder).resolve(),Path(output).resolve()
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    result=json.loads((folder/'result.json').read_text())
    planned=next(e for e in result['actor_last_output']['events'] if e['state']=='observed_geometry_path_planned')
    solution=planned['solution'];candidate=solution['candidate']
    m=mujoco.MjModel.from_xml_path(str(folder/'actor_bundle/model/world.xml'));d=mujoco.MjData(m)
    joints=robot_joints(m);qa=m.jnt_qposadr[joints]
    hand=PointingHand(m,candidate['hand_q'])
    normal=np.array(solution['outward_normal']);axis=np.array(solution['direction'])
    denominator=float(normal@axis)
    if abs(denominator)<.1:raise ValueError('Grip plane is insufficiently observable along the slider axis')
    R=np.array(solution['contact_palm_rotation']);heights=(hand.pad_vertices@R.T)@normal
    pad_local=hand.pad_vertices[heights<heights.min()+2e-5].mean(axis=0)
    surface=np.array(solution['device_rotation'])@np.array(candidate['surface_m'])+np.array(solution['device_translation_m'])
    baseline=float(np.median([r['estimated_slider_offset_m'] for r in planned['grip_observations'][-8:]]))
    sensors=dict(np.load(folder/'sensor_observations.npz'))
    responses=json.loads((folder/'actor_responses.json').read_text())
    predictions=[]
    for response in responses:
        if response.get('policy_state')!='push':continue
        t=response['time_s'];i=int(np.argmin(abs(sensors['time_s']-t)))
        if abs(sensors['time_s'][i]-t)>1e-8:raise ValueError('Missing native encoder packet')
        d.qpos[qa]=sensors['joint_position'][i];d.qpos[3:7]=sensors['imu_quaternion'][i]
        d.qpos[:3]=response['estimated_root_position_m'];mujoco.mj_kinematics(m,d)
        pad=hand.observed_contact_point(d,pad_local)
        raw=float(normal@(pad-surface)/denominator)
        predictions.append(dict(time_s=t,raw_plane_position_m=raw,
                                closed_baseline_corrected_position_m=raw-baseline,
                                filtered_distal_load_n=response['touch']['filtered_distal_index_n']))
    pre=dict(source='Native encoders/IMU, recorded actor base estimate, observed key/CAD registration and pad contact geometry',
             no_plant_loaded_before_predictions=True,normal_dot_slider_axis=denominator,
             closed_baseline_m=baseline,normal_pressure_to_slider_displacement_ratio=1./denominator,
             predictions=predictions)
    (output/'predictions.json').write_text(json.dumps(pre,indent=2)+'\n')
    # Evaluator only; none of this truth is used to compute the predictions.
    plant=mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    trace=dict(np.load(folder/'trace.npz'));slider=plant.joint('nicolet_door_slide').qposadr[0]
    rows=[]
    for row in predictions:
        i=int(np.argmin(abs(trace['time']-row['time_s'])));truth=float(trace['qpos'][i,slider])
        rows.append(dict(**row,actual_slider_position_m=truth,
                         raw_error_m=row['raw_plane_position_m']-truth,
                         corrected_error_m=row['closed_baseline_corrected_position_m']-truth))
    loaded=[r for r in rows if r['filtered_distal_load_n']>.2]
    metrics={key:dict(max_abs_m=max(abs(r[key]) for r in loaded),median_m=float(np.median([r[key] for r in loaded])))
             for key in ['raw_error_m','corrected_error_m']}
    report=dict(development_only=True,qualified_execution=False,run=folder.name,loaded_rows=len(loaded),
                metrics=metrics,rows=rows,
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),output/'predictions.json',folder/'result.json',folder/'sensor_observations.npz',folder/'trace.npz']})
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(run=folder.name,denominator=denominator,baseline_m=baseline,metrics=metrics)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('output');a=p.parse_args();run(a.folder,a.output)
