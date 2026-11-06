"""Check recorded walking-prefix compatibility and the first balance handoff.

The sensor stream comes from an earlier independent station-approach attempt.
No changed-command continuation is treated as a physical result.
"""
import argparse
import json
from pathlib import Path
import pickle

import mujoco
import numpy as np

from run_dex3_walking import sha
from station_pickup_actor import StationPickupActor
from walking_actor import SDK_JOINTS


def check(walking, source, output):
    walking, source, output = map(Path, (walking, source, output))
    output.mkdir(parents=True, exist_ok=False)
    result = json.loads((walking / 'result.json').read_text())
    assert sha(walking / 'sensors.npz') == result['sensors_sha256']
    assert sha(walking / 'responses.pkl') == result['responses_sha256']
    sensor = dict(np.load(walking / 'sensors.npz'))
    responses = pickle.loads((walking / 'responses.pkl').read_bytes())
    m = mujoco.MjModel.from_xml_path(str(walking / 'actor_bundle/model/world.xml'))
    prior = json.loads((source / 'policy_source/tool_prior.json').read_text())
    posture = np.asarray(prior.pop('initial_robot_qpos'))
    names = SDK_JOINTS[12:] + [m.joint(j).name for j in m.actuator_trnid[:, 0] if '_hand_' in m.joint(j).name]
    targets = {n: float(posture[m.joint(n).qposadr[0]]) for n in names}
    actor = StationPickupActor(m, walking / 'policy_source',
        json.loads((walking / 'walking_prior.json').read_text()), prior, targets)
    maximum = 0.
    compared = 0
    failure = None
    handoff_torque = None
    rejected_extra_field = False
    try:
        for i, expected in enumerate(responses):
            packet = {k: v[i] for k, v in sensor.items()}
            packet.update(head_rgb=None, head_depth=None)
            response = actor.update(packet)
            maximum = max(maximum, float(np.max(abs(response['torque']-expected['torque']))))
            compared += 1
            if actor.phase == 'prepare':
                handoff_torque = actor.preparation.torque(
                    {**{k: packet[k] for k in packet if k not in {'head_rgb', 'head_depth'}}, 'depth': None}, 0.)
                break
        try:
            actor.update(dict(packet, plant_position=np.zeros(3)))
        except ValueError:
            rejected_extra_field = True
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        actor.close()
    passed = failure is None and compared > 10000 and maximum == 0. and handoff_torque is not None and rejected_extra_field
    report = dict(scope=__doc__, passed=bool(passed), failure=failure,
        compared_walking_packets=compared, maximum_torque_error=maximum,
        reached_preparation=actor.phase == 'prepare', first_balance_torque_finite=
            handoff_torque is not None and bool(np.isfinite(handoff_torque).all()),
        first_balance_torque_within_source_limits=handoff_torque is not None and bool(
            np.all(handoff_torque >= m.actuator_ctrlrange[:, 0]) and np.all(handoff_torque <= m.actuator_ctrlrange[:, 1])),
        extra_plant_field_rejected=rejected_extra_field,
        source_sensors_sha256=result['sensors_sha256'], source_responses_sha256=result['responses_sha256'],
        actor_sha256=sha(Path(__file__).parent / 'station_pickup_actor.py'), script_sha256=sha(__file__),
        qualified_handoff=False, qualified_grasp=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return passed


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('walking')
    p.add_argument('source')
    p.add_argument('output')
    a = p.parse_args()
    if not check(a.walking, a.source, a.output):
        raise SystemExit(1)
