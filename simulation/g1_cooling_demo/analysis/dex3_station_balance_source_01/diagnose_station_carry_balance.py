"""Reproduce a failed station carry and inspect only its actor's own estimates.

Run beside a frozen copy of the recorded actor modules. No physical state,
contact force or simulator object pose enters the replayed controller.
"""
import argparse
import json
from pathlib import Path
import pickle

import mujoco
import numpy as np

from station_pickup_actor import StationPickupActor
from verify_dex3_ftir_controller import difference, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    read = lambda name:json.loads((a.run/name).read_text())
    result, receipt = read('result.json'), read('actor_isolation.json')
    for name, key in [('sensors.npz', 'sensors_sha256'), ('responses.pkl', 'responses_sha256'),
                      ('camera_index.json', 'camera_index_sha256')]:
        assert sha(a.run/name) == result[key]
    model_path = a.run/'actor_bundle/model/world.xml'
    assert sha(model_path) == receipt['bundled_model_sha256']
    m = mujoco.MjModel.from_xml_path(str(model_path))
    prior = read('policy_source/tool_prior.json')
    prior['tool_shape_path'] = str((a.run/'object_shape_source/tool_shape.glb').resolve())
    assert sha(prior['tool_shape_path']) == prior['tool_shape_sha256']
    actor = StationPickupActor(m, a.run/'policy_source', read('walking_prior.json'), prior,
                              read('policy_source/preparation_targets.json'))
    sensors = dict(np.load(a.run/'sensors.npz'))
    responses = pickle.loads((a.run/'responses.pkl').read_bytes())
    frames = read('camera_index.json')
    count, maximum, failed_at, terminal_error = 0, 0., None, None
    samples = []
    try:
        for i, expected in enumerate(responses):
            packet = {k:v[i] for k, v in sensors.items() if k != 'camera_frame_id'}
            frame_id = int(sensors['camera_frame_id'][i])
            packet.update(head_rgb=None, head_depth=None)
            if frame_id >= 0:
                entry = frames[frame_id]
                assert sha(a.run/entry['file']) == entry['sha256']
                with np.load(a.run/entry['file']) as frame:
                    packet.update({k:frame[k] for k in frame.files})
            try:
                actual = actor.update(packet)
            except Exception as error:
                terminal_error = type(error).__name__+': '+str(error)
                # Reproduce the recorded wrapper, including its truncated
                # top-level event history. Recovered nested events are a
                # separate diagnostic artifact, never a rewritten recording.
                actual = dict(torque=np.zeros(m.nu), error=terminal_error,
                              events=list(actor.events), phase=actor.phase)
            maximum = max(maximum, difference(expected, {k:v for k, v in actual.items() if k != 'events'}))
            count += 1
            if maximum > 1e-10:
                failed_at = float(packet['time_s'])
                break
            pickup = actor.pickup
            walker = None if pickup is None else pickup.walker
            if walker is not None and walker.balance is not None and (i % 100 == 0 or terminal_error):
                b, d = walker.balance, walker.d
                com = d.subtree_com[m.body('pelvis').id]
                rows = []
                for j in m.actuator_trnid[:, 0]:
                    value = float(d.qpos[m.jnt_qposadr[j]])
                    lo, hi = m.jnt_range[j]
                    margin = min(value-lo, hi-value)
                    if margin < .04:
                        rows.append(dict(joint=m.joint(j).name, position_rad=value, margin_rad=float(margin)))
                samples.append(dict(time_s=float(packet['time_s']), phase=walker.phase, steps=walker.steps,
                    com_m=com.tolist(), com_target_m=b.com_target.tolist(),
                    com_xy_error_m=float(np.linalg.norm(com[:2]-b.com_target[:2])),
                    estimated_root_m=d.qpos[:3].tolist(), estimated_xy_speed_m_s=float(np.linalg.norm(d.qvel[:2])),
                    sole_targets_m=np.asarray(b.foot_positions).tolist(), support=walker.estimate.support.tolist(),
                    near_source_joint_limits=rows))
            if i % 10000 == 0:
                print('carry_balance_prefix', float(packet['time_s']), actual.get('phase'), flush=True)
            if terminal_error:
                break
    finally:
        actor.close()
    recovered = list(actor.events)
    if actor.pickup is not None:
        recovered += [dict(e, time_s=float(e['time_s'])+actor.pickup_started) for e in actor.pickup.events]
    (a.output/'reconstructed_actor_events.json').write_text(json.dumps(recovered, indent=2)+'\n')
    (a.output/'balance_samples.json').write_text(json.dumps(samples, indent=2)+'\n')
    report = dict(scope=__doc__, reproduced_recorded_failure=bool(count==len(responses) and maximum<=1e-10 and terminal_error),
        responses_compared=count, expected_responses=len(responses), terminal_error=terminal_error,
        maximum_response_error=maximum if np.isfinite(maximum) else None, first_changed_time_s=failed_at,
        final_balance_sample=samples[-1] if samples else None,
        source_result_sha256=sha(a.run/'result.json'), source_sensors_sha256=result['sensors_sha256'],
        source_responses_sha256=result['responses_sha256'], recovered_events=len(recovered),
        recorded_events=len(read('events.json')), physical_continuation_executed=False, qualified_carry=False)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
