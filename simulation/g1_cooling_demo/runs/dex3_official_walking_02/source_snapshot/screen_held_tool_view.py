"""Offline inspection-pose screen using an explicitly retained held state.

Tool motion is a rigid-grasp hypothesis in a kinematic diagnostic only. This
does not execute a robot, establish grasp retention, or supply plant poses to
an actor. A selected pose still needs sensor-based planning and physical tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

from ftir_hand import ArmIK


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def pose(obj):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = obj.xmat.reshape(3, 3), obj.xpos
    return T


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--time', type=float, default=50.)
    a = p.parse_args()
    run, out = a.recording.resolve(), a.output.resolve()
    result, contract = [json.loads((run/n).read_text()) for n in ['result.json', 'contract.json']]
    assert sha(run/'trace.npz') == result['trace_sha256']
    assert sha(run/'world.xml') == contract['model_sha256']
    with np.load(run/'trace.npz') as trace:
        k = int(np.searchsorted(trace['time'], a.time))
        initial, recorded_time = trace['qpos'][k].copy(), float(trace['time'][k])
    m = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    d = mujoco.MjData(m)
    d.qpos[:] = initial
    mujoco.mj_forward(m, d)
    wrist = pose(d.site('right_wrist_reference'))
    relative = np.linalg.inv(wrist) @ pose(d.body('tweezer'))
    base_rotation = d.body('pelvis').xmat.reshape(3, 3).copy()
    address = m.joint('tweezer_free').qposadr[0]
    robot, tool = {m.body('pelvis').id}, {m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in robot:
            robot.add(b)
        if m.body_parentid[b] in tool:
            tool.add(b)
    allowed = {m.body(n).id for n in contract['allowed_tool_contact_bodies']}
    tray = m.body('carrier_tray').id
    imported = json.loads((run/'laboratory_import.json').read_text())
    floor = {p['geom'] for p in imported['parts'] if p['source_part'] in
             {'indoor_floor', 'annex_floor', 'outdoor_floor', 'outdoor_access_path'}}
    bench = {p['geom'] for p in imported['parts'] if p['source_part'] == 'ftir_bench_worktop'}
    limits = contract['physical_acceptance']
    ik = ArmIK(m)
    tool_geoms = np.flatnonzero(np.isin(m.geom_bodyid, list(tool)))
    tip_bodies = [max((b for b in tool if m.body(b).name.startswith(label+'_beam_')),
                      key=lambda b: m.body(b).name) for label in ['negative', 'positive']]
    tip_geoms = np.flatnonzero(np.isin(m.geom_bodyid, tip_bodies))
    out.mkdir(parents=True, exist_ok=False)
    for name in ['screen_held_tool_view.py', 'ftir_hand.py']:
        shutil.copyfile(Path(__file__).with_name(name), out/name)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    old = m.vis.quality.offsamples
    m.vis.quality.offsamples = 0
    segment = mujoco.Renderer(m, height=480, width=640, max_geom=m.ngeom+1000)
    m.vis.quality.offsamples = old
    rgb = mujoco.Renderer(m, height=480, width=640, max_geom=m.ngeom+1000)
    segment.enable_segmentation_rendering()

    def screen(q):
        d.qpos[:] = q
        mujoco.mj_kinematics(m, d)
        T = pose(d.site('right_wrist_reference')) @ relative
        d.qpos[address:address+3] = T[:3, 3]
        d.qpos[address+3:address+7] = Rotation.from_matrix(T[:3, :3]).as_quat()[[3, 0, 1, 2]]
        mujoco.mj_forward(m, d)
        failures = []
        for c in d.contact:
            bs = {int(m.geom_bodyid[g]) for g in c.geom}
            names = [m.geom(int(g)).name for g in c.geom]
            if not bs & (robot | tool | {tray}):
                continue
            if len(bs & tool) == 1 and bs & allowed:
                bound = limits['maximum_hand_tool_penetration_m']
            elif (bs & tool and (tray in bs or set(names) & bench)) or (tray in bs and set(names) & bench):
                bound = limits['maximum_passive_support_penetration_m']
            elif any('ankle_roll_link_collision' in n for n in names) and set(names) & floor:
                bound = limits['maximum_sole_penetration_m']
            else:
                bound = limits['maximum_other_penetration_m']
            if c.dist < -bound:
                failures.append(dict(parts=names, penetration_m=-float(c.dist), bound_m=bound))
        return failures

    def visible():
        segment.update_scene(d, camera='head_rgb', scene_option=option)
        seg = segment.render().copy()
        valid = seg[:, :, 1] == int(mujoco.mjtObj.mjOBJ_GEOM)
        return (int((valid & np.isin(seg[:, :, 0], tool_geoms)).sum()),
                int((valid & np.isin(seg[:, :, 0], tip_geoms)).sum()))

    rows, best = [], None
    try:
        initial_contacts = screen(initial)
        baseline_pixels = visible()
        rgb.update_scene(d, camera='head_rgb', scene_option=option)
        Image.fromarray(rgb.render()).save(out/'initial.png')
        offsets = [np.zeros(3), np.array([0., .08, 0.]), np.array([0., -.08, 0.]),
                   np.array([0., 0., .06]), np.array([-.08, 0., .04])]
        for offset in offsets:
            for angle in [0., -.5, .5, -1., 1., -1.5, 1.5]:
                q = initial.copy()
                bad = None
                samples = []
                for u in np.linspace(0., 1., 41):
                    d.qpos[:] = q
                    goal = wrist[:3, 3] + base_rotation @ offset * u
                    rotation = wrist[:3, :3] @ Rotation.from_rotvec([0., 0., angle*u]).as_matrix()
                    joints, pe, re = ik.solve(d, goal, rotation, q[ik.qa])
                    q[ik.qa] = joints
                    if pe > .001 or re > .025:
                        bad = dict(kind='ik', fraction=float(u), position_error_m=pe, rotation_error_rad=re)
                        break
                    contacts = screen(q)
                    if contacts:
                        bad = dict(kind='contact_bounds', fraction=float(u), contacts=contacts[:8])
                        break
                    samples.append(q[ik.qa].tolist())
                row = dict(base_frame_offset_m=offset.tolist(), wrist_roll_about_tool_axis_rad=angle,
                           sampled_path_clear=bad is None, failure=bad, samples=len(samples))
                if bad is None:
                    pixels, tips = visible()
                    row.update(tool_pixels=pixels, tip_pixels=tips)
                    if best is None or (tips, pixels) > (best['tip_pixels'], best['tool_pixels']):
                        best = dict(row, arm_joint_path=samples)
                        rgb.update_scene(d, camera='head_rgb', scene_option=option)
                        Image.fromarray(rgb.render()).save(out/'best.png')
                rows.append(row)
                print(json.dumps(row), flush=True)
    finally:
        rgb.close()
        segment.close()
    report = dict(scope=__doc__, source_result_sha256=sha(run/'result.json'),
        source_trace_sha256=result['trace_sha256'], model_sha256=contract['model_sha256'],
        recorded_time_s=recorded_time, initial_contacts=initial_contacts,
        initial_tool_pixels=baseline_pixels[0], initial_tip_pixels=baseline_pixels[1],
        candidates=rows, best=best, source_sha256=sha(__file__),
        evaluator_segmentation_only=True, physical_execution=False,
        online_tool_tracking_qualified=False, qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
