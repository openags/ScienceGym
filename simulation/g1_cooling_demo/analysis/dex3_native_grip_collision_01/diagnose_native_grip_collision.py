"""Replay a retained half-second grip window with bounded CCD comparisons.

Motor commands come from the recorded diagnostic, not a new closed-loop actor.
Only native collision-detection options differ between cases. No geometry,
contact compliance, force bound, time step or acceptance criterion is changed.
This restored-state attribution cannot qualify a grasp or carrying episode.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np

from frozen_collision_plugins import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('diagnostic', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run, source, out = [v.resolve() for v in [args.run, args.diagnostic, args.output]]
    contract = json.loads((run/'contract.json').read_text())
    report = json.loads((source/'result.json').read_text())
    assert sha(run/'contract.json') == report['actor_contract_sha256']
    assert sha(source/'trace.npz') == report['trace_sha256']
    assert sha(run/'world.xml') == contract['model_sha256']
    native = report['prelift_native_observation']
    assert sha(source/'prelift_native_window.npz') == native['native_window_sha256']
    trace = dict(np.load(source/'trace.npz'))
    with np.load(source/'prelift_native_window.npz') as recorded:
        first_time = float(recorded['time_s'][0])
    first = int(np.searchsorted(trace['time'], first_time, side='right')-1)
    last = int(np.searchsorted(trace['time'], native['time_s']))
    out.mkdir(parents=True, exist_ok=False)
    for path in [Path(__file__), Path(__file__).with_name('frozen_collision_plugins.py')]:
        shutil.copyfile(path, out/path.name)
    rows = []
    cases = ['original', 'tight_native', 'single_contact_native', 'legacy_ccd']
    for case in cases:
        model = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
        if case == 'tight_native':
            model.opt.ccd_tolerance = 1e-10
            model.opt.ccd_iterations = 1000
        elif case == 'single_contact_native':
            model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_MULTICCD)
        elif case == 'legacy_ccd':
            model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
        data = mujoco.MjData(model)
        data.time = float(trace['time'][first])
        data.qpos[:], data.qvel[:] = trace['qpos'][first], trace['qvel'][first]
        mujoco.mj_forward(model, data)
        # Use the same body-set definition as the independent physical evaluator.
        tool = {i for i in range(model.nbody) if model.body(i).name.startswith('tweezer')}
        allowed = {model.body(n).id for n in contract['allowed_tool_contact_bodies']}
        limits = contract['physical_acceptance']
        stride = round(.001/model.opt.timestep)
        times, forces, losses = [], [], []
        qerror = verror = peak_penetration = 0.
        started = time.monotonic()
        for i in range(first, last):
            qerror = max(qerror, float(np.max(abs(data.qpos-trace['qpos'][i]))))
            verror = max(verror, float(np.max(abs(data.qvel-trace['qvel'][i]))))
            data.ctrl[:] = trace['ctrl'][i]
            for _ in range(stride):
                current = float(data.time)
                mujoco.mj_step(model, data)
                force = dict(thumb=0., index=0., middle=0.)
                contacts = []
                for ci, c in enumerate(data.contact):
                    bodies = set(map(int, model.geom_bodyid[c.geom]))
                    if not (bodies & tool and bodies & allowed):
                        continue
                    name = model.body(next(iter(bodies & allowed))).name
                    finger = next(f for f in force if f in name)
                    wrench = np.zeros(6)
                    mujoco.mj_contactForce(model, data, ci, wrench)
                    force[finger] += max(0., float(wrench[0]))
                    peak_penetration = max(peak_penetration, -float(c.dist))
                    contacts.append(dict(finger=finger, parts=[model.geom(int(g)).name for g in c.geom],
                                         distance_m=float(c.dist), normal_force_n=float(wrench[0]),
                                         normal=c.frame[:3].tolist()))
                values = [force[n] for n in ['thumb', 'index', 'middle']]
                times.append(current)
                forces.append(values)
                loaded = force['thumb'] > limits['minimum_thumb_load_n'] and min(force['index'], force['middle']) > limits['minimum_each_opposing_finger_load_n']
                if not loaded:
                    losses.append(dict(time_s=current, forces_n=values, contacts=contacts))
                if np.any(data.xfrc_applied) or np.any(data.qfrc_applied):
                    raise RuntimeError('Unexpected external force')
        np.savez_compressed(out/(case+'.npz'), time_s=times, force_n=forces)
        row = dict(case=case, ccd_tolerance_m=float(model.opt.ccd_tolerance),
                   ccd_iterations=int(model.opt.ccd_iterations), disableflags=int(model.opt.disableflags),
                   samples=len(times), lost_samples=len(losses), lost_steps=losses,
                   maximum_q_difference_from_recording=qerror, maximum_v_difference_from_recording=verror,
                   maximum_hand_tool_penetration_m=peak_penetration,
                   warning_counts=data.warning.number.tolist(), wall_seconds=time.monotonic()-started)
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k != 'lost_steps'}), flush=True)
        review = dict(scope=__doc__, source_result_sha256=sha(source/'result.json'),
                      run_contract_sha256=sha(run/'contract.json'), script_sha256=sha(__file__),
                      window_start_s=float(trace['time'][first]), window_end_s=float(trace['time'][last]),
                      cases=rows, complete=len(rows)==len(cases), qualified_carry=False,
                      physical_acceptance_unchanged=True)
        (out/'review.json').write_text(json.dumps(review, indent=2)+'\n')


if __name__ == '__main__':
    main()
