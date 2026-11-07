"""Post-run, truth-side diagnosis; never an input to the isolated actor."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'simulation/g1_cooling_demo'))
from ftir_hand import PointingHand


def inspect(folder):
    folder = Path(folder).resolve()
    trace = dict(np.load(folder/'trace.npz'))
    result = json.loads((folder/'result.json').read_text())
    event = next(e for e in result['actor_last_output']['events']
                 if e['state'] == 'observed_geometry_path_planned')
    solution = event['solution']
    normal = np.array(solution['outward_normal'])
    direction = np.array(solution['direction'])
    rotation = np.array(solution['contact_palm_rotation'])
    model = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    data = mujoco.MjData(model)
    hand = PointingHand(model)
    heights = (hand.pad_vertices@rotation.T)@normal
    pad = hand.pad_vertices[heights < heights.min()+2e-5].mean(axis=0)
    slide_qa = int(model.joint('nicolet_door_slide').qposadr[0])
    rows = []
    monitors = [json.loads(line) for line in (folder/'actor_monitor.jsonl').read_text().splitlines()]
    for t in np.arange(44., 49.01, .25):
        index = int(np.argmin(abs(trace['time']-t)))
        data.qpos[:] = trace['qpos'][index]
        data.qvel[:] = trace['qvel'][index]
        mujoco.mj_forward(model, data)
        nominal = mujoco.MjData(model)
        nominal.qpos[:] = data.qpos
        for name, value in solution['candidate']['hand_q'].items():
            nominal.joint(name).qpos[0] = value
        # Same affine source mimic relation used by the planner.
        for i in range(model.neq):
            a, b = model.eq_obj1id[i], model.eq_obj2id[i]
            if model.eq_type[i] == mujoco.mjtEq.mjEQ_JOINT:
                nominal.qpos[model.jnt_qposadr[a]] = model.eq_data[i,0]+model.eq_data[i,1]*nominal.qpos[model.jnt_qposadr[b]]
        mujoco.mj_kinematics(model, nominal)
        tip = hand.observed_contact_point(data, pad)
        ideal_tip = hand.observed_contact_point(nominal, pad)
        monitor = min(monitors, key=lambda x: abs(x['time_s']-t))
        command = monitor.get('commanded_pose') or {}
        target = command.get('position_m')
        error = None if target is None else np.array(target)-data.site('right_wrist_reference').xpos
        rows.append(dict(time_s=float(trace['time'][index]), policy_state=monitor['policy_state'],
            slider_m=float(data.qpos[slide_qa]), touch=monitor['touch'],
            index_q=[float(data.joint('right_index_'+str(i)+'_joint').qpos[0]) for i in [1,2]],
            pad_deflection_normal_m=float((tip-ideal_tip)@normal),
            pad_deflection_push_m=float((tip-ideal_tip)@direction),
            wrist_error_normal_m=None if error is None else float(error@normal),
            wrist_error_push_m=None if error is None else float(error@direction)))
    report = dict(run=str(folder.relative_to(ROOT)), observations=rows,
                  maximum_slider_travel_m=float(trace['qpos'][:,slide_qa].max()),
                  final_slider_travel_m=float(trace['qpos'][-1,slide_qa]),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),
                  scope='Post-run finger deflection and wrist tracking diagnosis; no success or causal proof.')
    output = Path(__file__).parent/(folder.name+'_contact_diagnosis.json')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('folder')
    inspect(parser.parse_args().folder)
