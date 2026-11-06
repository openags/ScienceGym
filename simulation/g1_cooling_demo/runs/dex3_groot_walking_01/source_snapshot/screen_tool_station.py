"""Offline initial-layout search in the existing full laboratory.

Only declared initial robot/tool/tray placements change. No runtime transport,
grasp, balance or qualified branch is claimed. Every screened offset is saved.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(station, output):
    station, output = Path(station).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, output/'screen_tool_station.py')
    contract = json.loads((station/'contract.json').read_text())
    review = json.loads((station/'review.json').read_text())
    assert sha(station/'contract.json') == review['contract_sha256']
    assert sha(station/'world.xml') == contract['plant_sha256']
    model = mujoco.MjModel.from_xml_path(str(station/'world.xml'))
    data = mujoco.MjData(model)
    baseline = Path(__file__).resolve().parent/'runs/ftir_approach_11'
    base = mujoco.MjModel.from_xml_path(str(baseline/'world.xml'))
    bd = mujoco.MjData(base); mujoco.mj_forward(base, bd)
    imported = json.loads((baseline/'laboratory_import.json').read_text())
    floor = {p['geom'] for p in imported['parts'] if p['source_part'] in
             {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    source_by_geom = {p['geom']: p for p in imported['parts']}
    robot = {model.body('pelvis').id}; tool = {model.body('tweezer').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in robot: robot.add(b)
        if model.body_parentid[b] in tool: tool.add(b)
    tray_id = model.body('carrier_tray').id
    initial = np.asarray(contract['initial_qpos'])
    # Coordinate transform used by the pinned laboratory runtime.
    lab_from_work_rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    free_joints = [j for j in range(model.njnt) if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE
                   and int(model.jnt_bodyid[j]) in {model.body('pelvis').id, model.body('tweezer').id, tray_id}]
    assert len(free_joints) == 3
    offsets = list(itertools.product([-.5, -.35, -.2, 0., .2, .35, .5], [0., .03, .06]))
    rows = []
    for dx, dy in offsets:
        data.qpos[:] = initial
        delta = lab_from_work_rotation.T@np.array([dx, dy, 0.])
        for j in free_joints:
            start = int(model.jnt_qposadr[j]); data.qpos[start:start+3] += delta
        mujoco.mj_forward(model, data)
        bad = []
        for c in data.contact:
            bodies = {int(model.geom_bodyid[g]) for g in c.geom}
            if not (bodies & (robot | tool | {tray_id})): continue
            names = [model.geom(int(g)).name for g in c.geom]
            sole = any('ankle_roll_link_collision' in n for n in names) and bool(set(names)&floor)
            tool_tray = tray_id in bodies and bool(bodies&tool)
            tray_bench = tray_id in bodies and any(source_by_geom.get(n, {}).get('source_part') == 'ftir_bench_worktop' for n in names)
            limit = .001 if sole else .00025 if tool_tray or tray_bench else .00002
            if c.dist < -limit: bad.append(dict(parts=names, signed_distance_m=float(c.dist), limit_m=limit))
        points = []
        for x, y in itertools.product([-.145, 0., .145], [-.095, 0., .095]):
            tray = data.body('carrier_tray')
            origin = tray.xpos+tray.xmat.reshape(3, 3)@np.array([x, y, 0.])+[0., 0., .02]
            gid = np.array([-1], dtype=np.int32)
            dist = mujoco.mj_ray(base, bd, origin, np.array([0., 0., -1.]),
                                 np.array([0, 0, 1, 0, 0, 0], dtype=np.uint8), True, -1, gid)
            name = base.geom(int(gid[0])).name if gid[0] >= 0 else None
            height = float(origin[2]-dist) if dist >= 0 else None
            supported = source_by_geom.get(name, {}).get('source_part') == 'ftir_bench_worktop' and height is not None and abs(height-.85) < .0001
            points.append(dict(tray_xy_m=[x, y], support_geom=name, height_m=height, supported=supported))
        rows.append(dict(lab_offset_m=[dx, dy], accepted_initial_geometry=not bad and all(p['supported'] for p in points),
                         excessive_contacts=bad, footprint=points))
    result = dict(scope=__doc__, source_plant_sha256=sha(station/'world.xml'),
        source_contract_sha256=sha(station/'contract.json'), source_review_sha256=sha(station/'review.json'),
        script_sha256=sha(__file__), tested=len(rows), accepted=sum(r['accepted_initial_geometry'] for r in rows),
        trials=rows, qualified_grasp=False, qualified_paper_branch=False)
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(tested=len(rows), accepted=result['accepted'],
                         candidates=[r['lab_offset_m'] for r in rows if r['accepted_initial_geometry']])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('station'); p.add_argument('output')
    a = p.parse_args(); run(a.station, a.output)
