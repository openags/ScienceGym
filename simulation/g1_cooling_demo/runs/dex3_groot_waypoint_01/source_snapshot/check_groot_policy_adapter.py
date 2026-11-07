"""Compare the adapter with inspected upstream preprocessing on real sensors.

The upstream tensor conversion and unused gait-clock calculation are omitted;
the original 86-feature assembly and six-frame history statements execute
unchanged. Both paths use the pinned, unmodified official ONNX weights.
"""
import argparse
import ast
from collections import deque
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import mujoco
import numpy as np
import yaml

from groot_walking_actor import GrootBodyPolicy
from observations import robot_joints
from run_dex3_walking import sha
from walking_actor import SDK_JOINTS

HERE = Path(__file__).resolve().parent


def check(recording, output):
    recording, output = Path(recording).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    directory = HERE / 'locomotion_groot_policy'
    source = directory / 'reference/g1_gear_wbc_policy.py'
    utility = directory / 'reference/gear_wbc_utils.py'
    utilities = ast.parse(utility.read_text())
    helpers = [node for node in utilities.body if isinstance(node, ast.FunctionDef) and
               node.name in {'quat_rotate_inverse', 'get_gravity_orientation'}]
    namespace = {'np': np, 'Dict': dict, 'Any': object}
    exec(compile(ast.Module(body=helpers, type_ignores=[]), str(utility), 'exec'), namespace)
    cls = next(node for node in ast.parse(source.read_text()).body if isinstance(node, ast.ClassDef))
    compute = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'compute_observation')
    start = next(i for i, node in enumerate(compute.body) if isinstance(node, ast.Assign) and
                 any(isinstance(target, ast.Name) and target.id == 'body_indices' for target in node.targets))
    compute.body = compute.body[start:]
    history = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'set_observation')
    history.body = [node for node in history.body if not isinstance(node, ast.Assert) and not
        (isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute) and target.attr == 'obs_tensor'
                                            for target in node.targets))]
    exec(compile(ast.Module(body=[compute, history], type_ignores=[]), str(source), 'exec'), namespace)
    cfg = yaml.safe_load((directory / 'policy.yaml').read_text())
    for name in ['default_angles', 'cmd_scale', 'cmd_init']:
        cfg[name] = np.asarray(cfg[name], dtype=np.float32)
    ref = SimpleNamespace(config=cfg, action=np.zeros(15, dtype=np.float32), cmd=cfg['cmd_init'].copy(),
        height_cmd=cfg['height_cmd'], roll_cmd=0., pitch_cmd=0., yaw_cmd=0.,
        robot_model=SimpleNamespace(get_joint_group_indices=lambda name: list(range(29))),
        obs_history=deque(maxlen=6), obs_buffer=np.zeros(516, dtype=np.float32))
    ref.compute_observation = lambda observation: namespace['compute_observation'](ref, observation)
    adapter = GrootBodyPolicy(directory)
    model = mujoco.MjModel.from_xml_path(str(recording / 'controller_model/world.xml'))
    names = [model.joint(j).name for j in robot_joints(model)]
    body = [names.index(name) for name in SDK_JOINTS]
    sensor = dict(np.load(recording / 'sensors.npz'))
    feature_error = action_error = 0.
    samples = []
    for i in range(0, len(sensor['time_s']), 20):
        q, dq = sensor['joint_position'][i, body], sensor['joint_velocity'][i, body]
        quat, omega = sensor['imu_quaternion'][i], sensor['imu_gyro'][i]
        command = np.array([.2 if 2 <= sensor['time_s'][i] < 8 else 0., 0., 0.], dtype=np.float32)
        observation = dict(q=q, dq=dq, floating_base_pose=np.r_[np.zeros(3), quat],
                           floating_base_vel=np.r_[np.zeros(3), omega])
        namespace['set_observation'](ref, observation)
        actual = adapter.infer(q, dq, quat, omega, command)
        feature_error = max(feature_error, float(np.max(abs(ref.obs_buffer - np.concatenate(adapter.history)))))
        ref.cmd = command.copy()
        mode = 'balance' if np.linalg.norm(command) < .05 else 'walk'
        session = adapter.sessions[mode]
        ref.action = session.run(None, {session.get_inputs()[0].name: ref.obs_buffer[None]})[0].reshape(15)
        expected = ref.action * cfg['action_scale'] + cfg['default_angles']
        action_error = max(action_error, float(np.max(abs(actual - expected))))
        samples.append(dict(time_s=float(sensor['time_s'][i]), mode=mode))
    report = dict(scope=__doc__, passed=feature_error <= 1e-6 and action_error <= 1e-6,
        samples=len(samples), modes=sorted({row['mode'] for row in samples}),
        maximum_feature_error=feature_error, maximum_action_reference_error=action_error,
        float32_comparison_tolerance=1e-6, sensor_sha256=sha(recording / 'sensors.npz'),
        upstream_policy_sha256=sha(source), upstream_utility_sha256=sha(utility),
        adapter_sha256=sha(HERE / 'groot_walking_actor.py'), checker_sha256=sha(__file__),
        policy_source_sha256=sha(directory / 'SOURCE.json'), qualified_walking=False)
    for p in [Path(__file__), HERE / 'groot_walking_actor.py', source, utility]:
        shutil.copyfile(p, output / p.name)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording')
    p.add_argument('output')
    a = p.parse_args()
    check(a.recording, a.output)
