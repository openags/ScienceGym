"""Reach screen for encoder-based pinch centering on retained sensor packets.

Recorded motor-target metadata supplies the comparison path. No instrument
state or physical trace is read. This is a development screen, not execution.
"""
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'simulation/g1_cooling_demo'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from ftir_cover_actor import CoverActor

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

model_path = BASE/'runs/ftir_cover_10/controller_model/world.xml'
model = mujoco.MjModel.from_xml_path(str(model_path))
model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
prior = ROOT/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'
actor = CoverActor(model, [5.95,-5.32], prior)
run = BASE/'runs/ftir_cover_11'
sensors = np.load(run/'sensor_observations.npz')
monitor = [json.loads(line) for line in (run/'actor_monitor.jsonl').read_text().splitlines()]
rows = []
for record in monitor:
    pose = record['commanded_pose']
    if not pose or pose['phase']!='lift' or record['time_s']>19:
        continue
    i = int(np.argmin(abs(sensors['time_s']-record['time_s'])))
    packet = {key:sensors[key][i] for key in sensors.files if key!='right_touch_n'}
    packet['depth']=None
    actor.estimate.update(packet)
    rotation=np.array(pose['rotation'])
    offset=actor.center_offset('lift',rotation,.1,0)
    nominal=np.array(pose['target_m'])
    _,pe,re=actor.ik.solve(actor.d,nominal+offset,rotation,actor.d.qpos[actor.ik.qa])
    rows.append(dict(time_s=record['time_s'],offset_world_m=offset.tolist(),
                     centering=actor.center_status,ik_position_error_m=pe,ik_rotation_error_rad=re,
                     passed=bool(pe<=.003 and re<=.035 and np.linalg.norm(offset)<=.004+1e-12)))
if not rows:raise ValueError('No retained lifting targets to check')
report=dict(scope=__doc__,passed=all(r['passed'] for r in rows),rows=rows,
            model_sha256=sha(model_path),prior_sha256=sha(prior),sensor_sha256=sha(run/'sensor_observations.npz'),
            monitor_sha256=sha(run/'actor_monitor.jsonl'),actor_sha256=sha(BASE/'ftir_cover_actor.py'),
            builder_sha256=sha(Path(__file__)),physical_qualified=False)
(HERE/'reach_review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=report['passed'],samples=len(rows),
      maximum_offset_m=max(np.linalg.norm(r['offset_world_m']) for r in rows),
      maximum_ik_position_error_m=max(r['ik_position_error_m'] for r in rows),
      maximum_ik_rotation_error_rad=max(r['ik_rotation_error_rad'] for r in rows))),flush=True)
if not report['passed']:raise SystemExit(1)
