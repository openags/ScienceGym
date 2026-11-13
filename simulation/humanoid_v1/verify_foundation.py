"""Recompute H2 standing evidence from every saved physical state."""
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial import ConvexHull
from world import ASSET, load, sha


def verify(directory):
    directory = Path(directory)
    result = json.loads((directory / 'result.json').read_text())
    cfg = result['configuration']; case = cfg['case']; checks = []
    def check(name, passed, **values):
        checks.append(dict(name=name, passed=bool(passed), **values))
    changed = []
    for name, digest in result['input_sha256'].items():
        p = directory / name if name == 'workcell.xml' else directory / 'source_snapshot' / name
        if sha(p) != digest: changed.append(name)
    check('input_archive_integrity', not changed, changed=changed)
    source_path = directory / 'source_snapshot/robot_source.json'
    check('robot_manifest_identity', sha(source_path) == cfg['source_sha256'])
    source = json.loads(source_path.read_text())
    changed = [name for name, digest in source['files_sha256'].items() if sha(ASSET / name) != digest]
    check('original_robot_files_unchanged', not changed, changed=changed)
    check('trace_hash', sha(directory / 'physics_trace.npz') == result['artifacts_sha256']['physics_trace.npz'])
    with np.load(directory / 'physics_trace.npz') as archive: t = {k: archive[k] for k in archive.files}
    times = t['time']; check('finite_trace', all(np.isfinite(v).all() for v in t.values()))
    check('continuous_clock_from_initialization', times[0] == 0 and np.all(np.diff(times) > 0) and np.max(np.diff(times)) <= .005001,
          samples=len(times), maximum_interval_s=float(np.max(np.diff(times))))
    check('trace_reaches_recorded_end', abs(times[-1] - result['simulated_seconds']) < 1e-9)
    m = load(directory / 'workcell.xml'); d = mujoco.MjData(m)
    check('matching_physics_engine', result['engine_version'] == mujoco.__version__)
    # Reintegrate saved motor commands from the initial state, without resetting
    # positions between intervals or invoking the controller that made them.
    d.qpos[:] = t['qpos'][0]; d.qvel[:] = t['qvel'][0]
    d.qacc_warmstart[:] = t['qacc_warmstart'][0]; d.time = float(times[0])
    position_error = velocity_error = 0.
    intervals_on_grid = True
    for k in range(len(times) - 1):
        interval = (times[k + 1] - times[k]) / m.opt.timestep
        intervals_on_grid &= abs(interval - round(interval)) < 1e-7
        d.ctrl[:] = t['ctrl'][k]
        d.qfrc_applied[:] = t['qfrc_applied'][k]; d.xfrc_applied[:] = t['xfrc_applied'][k]
        for _ in range(round(interval)): mujoco.mj_step(m, d)
        position_error = max(position_error, float(np.max(abs(d.qpos - t['qpos'][k + 1]))))
        velocity_error = max(velocity_error, float(np.max(abs(d.qvel - t['qvel'][k + 1]))))
    check('motor_commands_reproduce_continuous_dynamics', intervals_on_grid and position_error < 1e-7 and velocity_error < 1e-7,
          maximum_position_error=position_error, maximum_velocity_error=velocity_error, tolerance=1e-7)
    d = mujoco.MjData(m)
    m.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART)
    check('floating_body_with_31_joint_motors', m.nq == 38 and m.nv == 37 and m.nu == 31
          and m.joint('floating_base_joint').type[0] == mujoco.mjtJoint.mjJNT_FREE
          and 0 not in m.actuator_trnid[:, 0], nq=m.nq, nv=m.nv, actuators=m.nu)
    check('no_mocap_or_equality_support', m.nmocap == 0 and m.neq == 0)
    check('no_external_support_forces', not np.any(t['qfrc_applied']) and not np.any(t['xfrc_applied'])
          and not np.any(m.body_gravcomp) and np.allclose(m.opt.gravity, [0, 0, -9.81]))
    check('pelvis_inertia_from_official_urdf', abs(m.body('pelvis').mass[0] - 8.5477) < 1e-9,
          pelvis_mass_kg=float(m.body('pelvis').mass[0]), total_mass_kg=float(m.body_mass.sum()))
    check('commands_within_source_motor_limits', np.all(t['ctrl'] >= m.actuator_ctrlrange[:, 0] - 1e-8)
          and np.all(t['ctrl'] <= m.actuator_ctrlrange[:, 1] + 1e-8),
          peak_command_ratio=float(np.max(abs(t['ctrl']) / m.actuator_ctrlrange[:, 1])))
    check('numerical_guards', not any(result['numerics']['warnings'])
          and result['numerics']['maximum_solver_iterations'] < m.opt.iterations,
          maximum_iterations=result['numerics']['maximum_solver_iterations'])
    check('hand_and_manipulation_credit_withheld', not result['hand_model_present'] and not result['manipulation_accepted']
          and not result['whole_paper_validated'] and not source['target_hand_model_present'])
    check('continuous_root_motion', np.max(np.linalg.norm(np.diff(t['qpos'][:, :3], axis=0), axis=1) / np.diff(times)) < 3.)
    check('unit_root_quaternions', np.max(abs(np.linalg.norm(t['qpos'][:, 3:7], axis=1) - 1)) < 1e-6)
    bounded_joints = np.flatnonzero(m.jnt_limited)
    angles = t['qpos'][:, m.jnt_qposadr[bounded_joints]]
    check('source_joint_ranges', np.all(angles >= m.jnt_range[bounded_joints, 0] - .001)
          and np.all(angles <= m.jnt_range[bounded_joints, 1] + .001))
    feet = {m.body(side + '_ankle_pitch_link').id: side for side in ['left', 'right']}
    foot_loads, margins, collisions, endpoints, tilts, foot_positions = [], [], [], [], [], []
    floor_id = m.geom('floor').id if case != 'no_floor' else -1
    for k, at in enumerate(times):
        d.qpos[:] = t['qpos'][k]; d.qvel[:] = t['qvel'][k]; d.ctrl[:] = t['ctrl'][k]
        mujoco.mj_forward(m, d)
        supported_load = {'left': 0., 'right': 0.}; points = []
        for i, contact in enumerate(d.contact):
            bodies = [int(m.geom_bodyid[g]) for g in contact.geom]
            force = np.zeros(6); mujoco.mj_contactForce(m, d, i, force)
            world_force = contact.frame.reshape(3, 3).T @ force[:3]
            foot_id = next((b for b in bodies if b in feet), None)
            if floor_id in contact.geom and foot_id is not None:
                sign = 1 if bodies[1] == foot_id else -1
                supported_load[feet[foot_id]] += sign * world_force[2]
                if force[0] > 1.: points.append(contact.pos[:2])
            elif force[0] > 2. and len(collisions) < 10:
                collisions.append(dict(time_s=float(at), bodies=[m.body(b).name for b in bodies], normal_N=float(force[0])))
        foot_loads.append([supported_load['left'], supported_load['right']])
        margin = -1.
        if len(points) >= 3:
            hull = ConvexHull(np.array(points)); xy = d.subtree_com[m.body('pelvis').id, :2]
            margin = float(np.min(-(hull.equations[:, :2] @ xy + hull.equations[:, 2])))
        margins.append(margin)
        endpoints.append([d.site(s + '_wrist_reference').xpos.copy() for s in ['left', 'right']])
        foot_positions.append([d.site(s + '_sole').xpos.copy() for s in ['left', 'right']])
        tilts.append(float(np.arccos(np.clip(d.body('pelvis').xmat[8], -1, 1))))
    loads = np.array(foot_loads); endpoints = np.array(endpoints); foot_positions = np.array(foot_positions)
    if case == 'nominal':
        stable = times >= 1.
        check('complete_stance_reach_return_chain', result['status'] == 'foundation_completed' and result['failure'] is None
              and [e['label'] for e in result['observations']] == ['initial_state', 'stance_settled', 'bilateral_reach_held', 'wrists_returned', 'foundation_finished']
              and abs(times[-1] - 20.) < 1e-8)
        check('both_feet_bear_load', np.min(loads[stable]) > 50., minimum_per_foot_N=float(np.min(loads[stable])))
        ratios = loads[stable].sum(axis=1) / (m.body_mass.sum() * 9.81)
        check('ground_bears_body_weight', np.min(ratios) > .85 and np.max(ratios) < 1.15,
              minimum_weight_ratio=float(np.min(ratios)), maximum_weight_ratio=float(np.max(ratios)))
        check('com_projection_inside_loaded_support', np.min(np.array(margins)[stable]) > .005,
              minimum_margin_m=float(np.min(np.array(margins)[stable])))
        check('no_unintended_contact', not collisions, failures=collisions)
        check('bounded_upright_tilt', max(tilts) < .05, maximum_rad=max(tilts))
        drift = np.max(np.linalg.norm(foot_positions[:, :, :2] - foot_positions[0, :, :2], axis=2))
        check('feet_do_not_slide', drift < .005, maximum_horizontal_drift_m=float(drift))
        for label, at, field in [('reach', 10., 'goal_wrist_positions_m'), ('return', 18., 'start_wrist_positions_m')]:
            k = int(np.argmin(abs(times - at)))
            errors = {s: float(np.linalg.norm(endpoints[k, i] - cfg[field][s])) for i, s in enumerate(['left', 'right'])}
            check('both_wrist_' + label, abs(times[k] - at) < 1e-8 and max(errors.values()) < .003, errors_m=errors)
        travel = np.max(np.linalg.norm(endpoints - endpoints[0], axis=2), axis=0)
        check('both_wrists_actually_move', np.min(travel) > .10, displacement_m=travel.tolist())
    else:
        check('physical_counterexample_rejected', result['status'] == 'failed'
              and any(s in (result['failure'] or '') for s in ['lost standing height', 'tilt exceeded', 'Missing physical foot support']), failure=result['failure'])
        if case == 'motors_off': check('all_motors_physically_disabled', not np.any(t['ctrl']))
        if case == 'no_floor':
            check('ground_physically_absent', all(m.geom(i).name != 'floor' for i in range(m.ngeom)))
            check('missing_support_observed_in_physics', np.max(abs(loads)) == 0 and t['qpos'][-1, 2] < t['qpos'][0, 2] - .001)
        check('invalid_support_not_credited', not any(e['label'] == 'foundation_finished' for e in result['observations']))
    report = dict(passed=all(c['passed'] for c in checks), case=case, checks=checks,
                  result_sha256=sha(directory / 'result.json'), verifier_sha256=sha(Path(__file__)),
                  manipulation_accepted=False, whole_paper_validated=False,
                  scope='H2 body standing and unloaded wrist reach/return; no articulated Dex5-S hand, grasp, walking or paper-step acceptance')
    (directory / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('directory', type=Path)
    report = verify(parser.parse_args().directory)
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']), failed=[c for c in report['checks'] if not c['passed']]), indent=2))
    raise SystemExit(0 if report['passed'] else 1)
