"""Offline native-state diagnosis of tool slip; never an actor input."""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from run_dex3_walking import sha


def diagnose(candidate, checkpoint, output):
    candidate, checkpoint, output = map(Path, (candidate, checkpoint, output))
    output.mkdir(parents=True, exist_ok=False)
    prior = json.loads((candidate / 'policy_source/tool_prior.json').read_text())
    trace = dict(np.load(checkpoint / 'trace.npz'))
    native = dict(np.load(checkpoint / 'tool_actuation_native.npz'))
    events = json.loads((checkpoint / 'events.json').read_text())
    m = mujoco.MjModel.from_xml_path(str(candidate / 'world.xml'))
    d = mujoco.MjData(m)
    tool_from_wrist = np.asarray(prior['grasp_geometry']['source_tool_from_wrist'])[:3, :3]
    sample_times = [55.992, 58., 60., 63., 65., 66.789, 67.2, 67.5, 68., 68.475]
    rows = []
    for t in sample_times:
        i = min(int(np.searchsorted(trace['time'], t)), len(trace['time']) - 1)
        d.qpos[:], d.qvel[:] = trace['qpos'][i], trace['qvel'][i]
        mujoco.mj_forward(m, d)
        wrist = d.site('right_wrist_reference')
        world_from_wrist = wrist.xmat.reshape(3, 3)
        tool = d.body('tweezer')
        world_from_tool = tool.xmat.reshape(3, 3)
        features, jacobians = [], []
        for feature in prior['robot_contact_features']:
            body = m.body(feature['body']).id
            point = d.xpos[body] + d.xmat[body].reshape(3, 3) @ np.asarray(feature['point_local_m'])
            jp, jr = np.zeros((3, m.nv)), np.zeros((3, m.nv))
            mujoco.mj_jac(m, d, jp, jr, point, body)
            own = tool_from_wrist @ world_from_wrist.T @ (point - wrist.xpos)
            actual = world_from_tool.T @ (point - tool.xpos)
            features.append(dict(body=feature['body'], nominal_tool_axes_wrist_point_m=own.tolist(),
                                 actual_tool_frame_point_m=actual.tolist()))
            finger = feature['body'].split('right_hand_', 1)[1].split('_')[0]
            finger_jacobians = {}
            for joint in range(m.njnt):
                name = m.joint(joint).name
                if name.startswith('right_hand_' + finger + '_'):
                    finger_jacobians[name] = (tool_from_wrist @ world_from_wrist.T @ jp[:, m.jnt_dofadr[joint]]).tolist()
            jacobians.append(finger_jacobians)
        j = min(int(np.searchsorted(native['time_s'], t)), len(native['time_s']) - 1)
        rows.append(dict(time_s=float(trace['time'][i]), phase=str(native['phase'][j]),
            actual_tip_gap_m=float(native['tip_gap_m'][j]), actual_finger_load_n=native['force_n'][j].tolist(),
            features=features, own_feature_jacobian_in_nominal_tool_axes_m_per_rad=jacobians,
            actual_tool_position_in_wrist_m=(world_from_wrist.T @ (tool.xpos - wrist.xpos)).tolist()))
    for row in rows:
        row['tool_wrist_drift_from_start_m'] = float(np.linalg.norm(
            np.asarray(row['actual_tool_position_in_wrist_m']) - rows[0]['actual_tool_position_in_wrist_m']))
        for i, feature in enumerate(row['features']):
            feature['own_motion_from_start_m'] = (np.asarray(feature['nominal_tool_axes_wrist_point_m']) -
                rows[0]['features'][i]['nominal_tool_axes_wrist_point_m']).tolist()
            feature['relative_tool_contact_shift_m'] = (np.asarray(feature['actual_tool_frame_point_m']) -
                rows[0]['features'][i]['actual_tool_frame_point_m']).tolist()
    report = dict(scope=__doc__, candidate=str(candidate), checkpoint=str(checkpoint),
        trace_sha256=sha(checkpoint / 'trace.npz'), model_sha256=sha(candidate / 'world.xml'),
        native_tool_record_sha256=sha(checkpoint / 'tool_actuation_native.npz'),
        diagnostic_sha256=sha(__file__), events=events, samples=rows,
        interpretation='Own material-point kinematics and actual tool motion are separated. This diagnostic uses evaluator truth and cannot be loaded by the controller.',
        qualified_tool_use=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    for row in rows:
        print(round(row['time_s'], 3), row['phase'], 'gap_mm', round(1000 * row['actual_tip_gap_m'], 3),
              'drift_mm', round(1000 * row['tool_wrist_drift_from_start_m'], 3),
              'load_N', np.round(row['actual_finger_load_n'], 3).tolist(),
              'own_dx_mm', [round(1000 * f['own_motion_from_start_m'][0], 3) for f in row['features']],
              'contact_dx_mm', [round(1000 * f['relative_tool_contact_shift_m'][0], 3) for f in row['features']], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate')
    p.add_argument('checkpoint')
    p.add_argument('output')
    a = p.parse_args()
    diagnose(a.candidate, a.checkpoint, a.output)
