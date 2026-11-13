"""Offline pad/handle drift in failed cover attempt 11; never an actor input.

Source pad centers approximate a contact region, not its pressure centroid.
This describes recorded geometry; it does not prove the cause of slipping.
"""
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RUN = ROOT / 'simulation/g1_cooling_demo/runs/ftir_cover_11'
trace = np.load(RUN / 'trace.npz')
model = mujoco.MjModel.from_xml_path(str(RUN / 'world.xml'))
data = mujoco.MjData(model)
monitor = [json.loads(s) for s in (RUN / 'actor_monitor.jsonl').read_text().splitlines()]
source = json.loads((ROOT / 'simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_06/pad_grasps.json').read_text())
centers = source['central_source_points_m']
parts = json.loads((RUN / 'laboratory_import.json').read_text())['parts']
bar = model.geom(next(p['geom'] for p in parts if p['instance'] == 'nicolet' and p['source_part'] == 'lid_handle_bar')).id
hinge = model.joint('nicolet_cover_hinge').id
rows = []
baseline = None
for t in np.arange(14.5, 20.01, .25):
    i = int(np.argmin(abs(trace['time'] - t)))
    data.qpos[:] = trace['qpos'][i]
    mujoco.mj_kinematics(model, data)
    record = min(monitor, key=lambda row: abs(row['time_s'] - t))
    wrist = data.site('right_wrist_reference')
    rotation = wrist.xmat.reshape(3, 3)
    axis = data.body(int(model.jnt_bodyid[hinge])).xmat.reshape(3, 3) @ model.jnt_axis[hinge]
    handle = data.geom_xpos[bar]
    pads = {}
    wrist_points = []
    for name, local in centers.items():
        body = data.body(name)
        point = body.xpos + body.xmat.reshape(3, 3) @ local
        vector = point - handle
        radial = vector - axis * (axis @ vector)
        wrist_points.append(rotation.T @ (point - wrist.xpos))
        pads[name] = dict(center_axis_distance_m=float(np.linalg.norm(radial)),
                          source_front_normal_world=body.xmat.reshape(3, 3)[:, 2].tolist(),
                          wrist_relative_center_m=wrist_points[-1].tolist())
    midpoint = np.mean(wrist_points, axis=0)
    if baseline is None:
        baseline = midpoint.copy()
    rows.append(dict(time_s=float(trace['time'][i]), phase=record['policy_state'],
                     lid_angle_deg=float(-np.degrees(data.qpos[model.jnt_qposadr[hinge]])),
                     sensor_load_n=record['touch'], pads=pads,
                     pad_midpoint_shift_since_14_5_s_m=(midpoint-baseline).tolist(),
                     wrist_tracking=record['wrist_load_compensation']))
report = dict(scope=__doc__, rows=rows, trace_sha256=hashlib.sha256((RUN/'trace.npz').read_bytes()).hexdigest(),
              source_center_receipt_sha256=hashlib.sha256((ROOT/'simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_06/pad_grasps.json').read_bytes()).hexdigest(),
              builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), qualified=False)
(HERE / 'review.json').write_text(json.dumps(report, indent=2)+'\n')
for row in rows[::2]:
    print(row['time_s'], row['phase'], round(row['lid_angle_deg'], 3),
          {k:round(v, 3) for k,v in row['sensor_load_n'].items()},
          'midpoint_shift_mm', np.round(np.array(row['pad_midpoint_shift_since_14_5_s_m'])*1000, 3).tolist(), flush=True)
