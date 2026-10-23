"""Record standing and unloaded bilateral wrist motion with the official H2.

No hand model, grasp or paper task is accepted by this diagnostic foundation.
"""
import os
os.environ.setdefault('MUJOCO_GL', 'egl')
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import numpy as np
import mujoco
from world import HERE, ASSET, build, load, initialize, sha
from standing import StandingController


def smooth(t):
    t = np.clip(t, 0., 1.)
    return 10 * t**3 - 15 * t**4 + 6 * t**5


def trajectory(at):
    returning = at >= 11
    fraction = (at - (11 if returning else 3)) / 5
    position = smooth(fraction)
    velocity = (30 * fraction**2 - 60 * fraction**3 + 30 * fraction**4) / 5 if 0 < fraction < 1 else 0.
    acceleration = (60 * fraction - 180 * fraction**2 + 120 * fraction**3) / 25 if 0 < fraction < 1 else 0.
    return (1 - position, -velocity, -acceleration) if returning else (position, velocity, acceleration)


def execute(out, *, seed=0, timestep=.001, case='nominal'):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise ValueError('Use a new output directory; prior evidence is immutable')
    source_files = ['world.py', 'standing.py', 'run_foundation.py']
    pins = {n: sha(HERE / n) for n in source_files}
    (out / 'source_snapshot').mkdir()
    for n in source_files: shutil.copyfile(HERE / n, out / 'source_snapshot' / n)
    shutil.copyfile(ASSET / 'SOURCE.json', out / 'source_snapshot/robot_source.json')
    cfg = build(out / 'workcell.xml', timestep=timestep, floor=case != 'no_floor')
    cfg.update(seed=seed, case=case, control_period_s=.005, trace_period_s=.005)
    pins['workcell.xml'] = sha(out / 'workcell.xml')
    model = load(out / 'workcell.xml'); data = initialize(model, seed=seed)
    controller = StandingController(model, data)
    start = {s: data.site(s + '_wrist_reference').xpos.copy() for s in ['left', 'right']}
    goal = {s: start[s] + [.13, .035 if s == 'left' else -.035, -.10] for s in start}
    cfg['start_wrist_positions_m'] = {s: p.tolist() for s, p in start.items()}
    cfg['goal_wrist_positions_m'] = {s: p.tolist() for s, p in goal.items()}
    states, events = [], []
    maximum_solver_iterations = 0
    failure = None
    def save():
        state = (float(data.time), data.qpos.copy(), data.qvel.copy(), data.ctrl.copy(),
                 data.qfrc_applied.copy(), data.xfrc_applied.copy(), data.qacc_warmstart.copy())
        if not states or data.time > states[-1][0] + 1e-10:
            states.append(state)
        else:
            # Event snapshots precede control updates. Keep the command actually
            # held over the following interval, including the first interval.
            states[-1] = state
    def event(label):
        save()
        events.append(dict(label=label, time_s=float(data.time),
                           wrist_positions_m={s: data.site(s + '_wrist_reference').xpos.tolist() for s in start},
                           root_position_m=data.qpos[:3].tolist()))
        print(label, round(data.time, 3), flush=True)
    stride = round(.005 / timestep)
    foot_bodies = {model.body(s + '_ankle_pitch_link').id for s in start}
    floor_id = model.geom('floor').id if case != 'no_floor' else -1
    checkpoints = {0: 'initial_state', round(3 / timestep): 'stance_settled',
                   round(10 / timestep): 'bilateral_reach_held', round(18 / timestep): 'wrists_returned'}
    try:
        for step in range(round(20 / timestep) + 1):
            if step in checkpoints: event(checkpoints[step])
            if step == round(20 / timestep): break
            if step % stride == 0:
                if data.time >= .02:
                    supported_load = {body: 0. for body in foot_bodies}
                    for index, contact in enumerate(data.contact):
                        bodies = [int(model.geom_bodyid[g]) for g in contact.geom]
                        foot = next((b for b in bodies if b in foot_bodies), None)
                        if floor_id in contact.geom and foot is not None:
                            force = np.zeros(6); mujoco.mj_contactForce(model, data, index, force)
                            world_force = contact.frame.reshape(3, 3).T @ force[:3]
                            supported_load[foot] += (1 if bodies[1] == foot else -1) * world_force[2]
                    if min(supported_load.values()) < 25.:
                        raise RuntimeError('Missing physical foot support')
                phase, speed, acceleration = trajectory(data.time)
                targets = {s: dict(position=start[s] + phase * (goal[s] - start[s]),
                                   velocity=speed * (goal[s] - start[s]),
                                   acceleration=acceleration * (goal[s] - start[s])) for s in start}
                data.ctrl[:] = 0 if case == 'motors_off' else controller.torque(wrist_targets=targets)
                save()
            mujoco.mj_step(model, data)
            maximum_solver_iterations = max(maximum_solver_iterations, int(max(data.solver_niter)))
            if any(w.number for w in data.warning): raise RuntimeError('MuJoCo numerical warning')
            if not np.isfinite(data.qpos).all(): raise RuntimeError('Nonfinite state')
            if maximum_solver_iterations >= model.opt.iterations: raise RuntimeError('Physics solver iteration limit reached')
            if data.qpos[2] < .85: raise RuntimeError('Floating pelvis lost standing height')
            if abs(data.qpos[4]) > .15 or abs(data.qpos[5]) > .15: raise RuntimeError('Floating pelvis tilt exceeded stance bound')
        event('foundation_finished')
    except BaseException as exc:
        failure = type(exc).__name__ + ': ' + str(exc)
        print(failure, flush=True)
    finally:
        save()
        keys = ['time', 'qpos', 'qvel', 'ctrl', 'qfrc_applied', 'xfrc_applied', 'qacc_warmstart']
        np.savez_compressed(out / 'physics_trace.npz', **{k: np.array([s[i] for s in states]) for i, k in enumerate(keys)})
        if any(sha(HERE / n) != pins[n] for n in source_files): failure = 'Source changed during execution'
        result = dict(status='foundation_completed' if failure is None else 'failed', failure=failure,
                      created_at=datetime.now(timezone.utc).isoformat(), configuration=cfg,
                      engine_version=mujoco.__version__, simulated_seconds=float(data.time), observations=events,
                      numerics=dict(maximum_solver_iterations=maximum_solver_iterations,
                                    maximum_control_solver_iterations=controller.maximum_iterations,
                                    warnings=[int(w.number) for w in data.warning]),
                      input_sha256=pins, source_archive='source_snapshot',
                      artifacts_sha256={'physics_trace.npz': sha(out / 'physics_trace.npz')},
                      hand_model_present=False, manipulation_accepted=False, whole_paper_validated=False,
                      scope=cfg['scope'])
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--timestep', type=float, choices=[.001, .0005], default=.001)
    parser.add_argument('--case', choices=['nominal', 'motors_off', 'no_floor'], default='nominal')
    args = parser.parse_args()
    r = execute(args.out, seed=args.seed, timestep=args.timestep, case=args.case)
    print(r['status'], flush=True)
    raise SystemExit(0 if r['status'] == 'foundation_completed' else 1)
