"""Check unactuated support after an explicitly authored tool translation.

Copies the existing passive tool/tray plant byte for byte. The selected initial
placement has zero velocity; it is not a robot action or a continuation of the
old trajectory. Original corner-span support acceptance is retained, including
separate rim loads, contact bounds, settled speeds and exact trajectory replay.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np

from fit_dex3_tweezer import ROOT, TOOL, digest, load_support


def run(placement_path, output, selection=0):
    started = time.monotonic()
    placement_path, output = Path(placement_path).resolve(), Path(output).resolve()
    placement = json.loads(placement_path.read_text())
    assert placement['contract_sha256'] == digest(placement_path.parent / 'contract.json')
    placement_contract = json.loads((placement_path.parent / 'contract.json').read_text())
    for name, expected in placement_contract['source_hashes'].items():
        assert digest(ROOT / name) == expected, name
    chosen = placement['candidates'][selection]
    assert chosen['passed_static']
    original = TOOL / 'tray_support_12'
    support = json.loads((original / 'review.json').read_text())
    source_contract = json.loads((original / 'contract.json').read_text())
    load_support(original / 'review.json', ROOT)
    assert source_contract['arrangement'] == 'corner_span'
    output.mkdir(parents=True, exist_ok=False)
    for name in ['support.xml', 'tray_parameter_preservation.json']:
        shutil.copyfile(original / name, output / name)
    shutil.copyfile(__file__, output / Path(__file__).name)
    model = mujoco.MjModel.from_xml_path(str(output / 'support.xml'))
    data = mujoco.MjData(model)
    assert model.nu == 0 and model.neq == 0
    data.qpos[:] = support['full_final_qpos']
    data.joint('tweezer_free').qpos[:3] += chosen['world_translation_m']
    data.qvel[:] = 0
    mujoco.mj_forward(model, data)
    data.qacc_warmstart[:] = 0
    tq = int(model.joint('tweezer_free').qposadr[0])
    tv = int(model.joint('tweezer_free').dofadr[0])
    rq = int(model.joint('tray_free').qposadr[0])
    rv = int(model.joint('tray_free').dofadr[0])
    tray = model.body('carrier_tray').id
    bench = model.geom('bench').id
    tool_bodies = {model.body('tweezer').id}
    for b in range(model.nbody):
        if int(model.body_parentid[b]) in tool_bodies:
            tool_bodies.add(b)
    files = [placement_path, placement_path.parent / 'contract.json', original / 'review.json',
             original / 'contract.json', output / Path(__file__).name]
    source_hashes = dict(source_contract['source_hashes'])
    source_hashes.update({str(p.relative_to(ROOT)): digest(p) for p in files})
    contract = dict(scope=__doc__, source_hashes=source_hashes,
                    plant_sha256=digest(output / 'support.xml'),
                    tray_contact_parameter_review_sha256=digest(output / 'tray_parameter_preservation.json'),
                    source_support_contract_sha256=digest(original / 'contract.json'),
                    arrangement='corner_span', authored_placement=chosen,
                    initial_placement_is_not_robot_execution=True,
                    initial_qpos=data.qpos.tolist(), initial_qvel=data.qvel.tolist(),
                    initial_qacc_warmstart=data.qacc_warmstart.tolist(),
                    duration_s=3., settled_interval_s=[2.5,3.], timestep_s=float(model.opt.timestep),
                    checks=source_contract['checks'], rim_regions_in_tray_frame_m=source_contract['rim_regions_in_tray_frame_m'],
                    inferred_contact_parameters=source_contract['inferred_contact_parameters'],
                    contact_force_convention=source_contract['contact_force_convention'],
                    geometry_and_materials_unchanged=digest(output / 'support.xml') == source_contract['plant_sha256'])
    assert contract['geometry_and_materials_unchanged']
    (output / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    initial = data.qpos.copy()
    records, loads, violations = [], [], []
    maximum_penetration = 0.
    external = False
    def state():
        return (float(data.time), data.qpos.copy(), data.qvel.copy(), data.qacc_warmstart.copy())
    for step in range(round(3. / model.opt.timestep)):
        records.append(state())
        external |= bool(np.any(data.xfrc_applied) or np.any(data.qfrc_applied))
        mujoco.mj_step(model, data)
        vertical_load = np.zeros(4)  # tray, bench, left rim, front rim
        for i, c in enumerate(data.contact):
            gs = list(map(int,c.geom))
            bs = [int(model.geom_bodyid[g]) for g in gs]
            tool_side = [b in tool_bodies for b in bs]
            if bench in gs or (sum(tool_side) == 1 and tray in bs):
                maximum_penetration = max(maximum_penetration, -float(c.dist))
                if sum(tool_side) == 1:
                    force = np.zeros(6)
                    mujoco.mj_contactForce(model, data, i, force)
                    z = float((c.frame.reshape(3,3).T @ force[:3])[2]) * (1. if tool_side[1] else -1.)
                    if tray in bs:
                        vertical_load[0] += z
                        local = data.xmat[tray].reshape(3,3).T @ (c.pos-data.xpos[tray])
                        if local[0] < -.145 and local[1] > -.085: vertical_load[2] += z
                        if local[1] < -.095 and local[0] > -.135: vertical_load[3] += z
                    if bench in gs: vertical_load[1] += z
            elif c.dist < -.00002 and len(violations) < 30:
                violations.append(dict(time_s=records[-1][0], parts=[model.geom(g).name for g in gs], distance_m=float(c.dist)))
        loads.append([records[-1][0], *vertical_load])
        if np.any(data.warning.number): break
    records.append(state())
    trace = {k: np.asarray([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','qacc_warmstart'])}
    np.savez_compressed(output / 'trace.npz', **trace)
    np.savez_compressed(output / 'support_loads.npz', values=np.asarray(loads))
    replay = mujoco.MjData(model)
    replay.qpos[:] = trace['qpos'][0]; replay.qvel[:] = trace['qvel'][0]
    mujoco.mj_forward(model,replay); replay.qacc_warmstart[:] = trace['qacc_warmstart'][0]
    qe = ve = 0.
    for i in range(len(records)-1):
        mujoco.mj_step(model, replay)
        qe = max(qe, float(np.max(abs(replay.qpos-trace['qpos'][i+1]))))
        ve = max(ve, float(np.max(abs(replay.qvel-trace['qvel'][i+1]))))
    mask = trace['time'] >= 2.5
    linear = max(float(np.max(np.linalg.norm(trace['qvel'][mask,s:s+3],axis=1))) for s in [tv,rv]) if mask.any() else float('inf')
    angular = max(float(np.max(np.linalg.norm(trace['qvel'][mask,s+3:s+6],axis=1))) for s in [tv,rv]) if mask.any() else float('inf')
    shifts = [float(np.max(np.linalg.norm(trace['qpos'][:,s:s+3]-initial[s:s+3],axis=1))) for s in [tq,rq]]
    tail = np.asarray([r for r in loads if r[0] >= 2.5])
    mean = tail[:,1:].mean(axis=0) if len(tail) else np.zeros(4)
    weight = float(model.body_mass[list(tool_bodies)].sum()*9.81)
    load_error = abs(float(mean[:2].sum())/weight-1)
    checks = dict(duration_completed=data.time >= 3.-1e-8,
                  free_unactuated_objects=model.nu == 0 and model.neq == 0,
                  geometry_and_materials_unchanged=contract['geometry_and_materials_unchanged'],
                  no_numerical_warnings=not np.any(data.warning.number),
                  finite_states=all(np.isfinite(x).all() for x in trace.values()),
                  no_external_forces=not external, penetration_bounded=maximum_penetration <= .00025,
                  no_unexpected_penetration=not violations, settled_linear_speed=linear <= .001,
                  settled_angular_speed=angular <= .01, tool_displacement=shifts[0] <= .005,
                  tray_displacement=shifts[1] <= .001, net_vertical_support_load=load_error <= .05,
                  left_rim_support=mean[2] >= .005, front_rim_support=mean[3] >= .005,
                  no_tool_bench_support=abs(mean[1]) <= .001, exact_replay=qe <= 1e-9 and ve <= 1e-8)
    result = dict(scope=__doc__, passed=all(checks.values()), checks={k: bool(v) for k,v in checks.items()},
                  duration_s=float(data.time), maximum_penetration_m=maximum_penetration,
                  maximum_settled_linear_speed_m_s=linear, maximum_settled_angular_speed_rad_s=angular,
                  maximum_tool_displacement_m=shifts[0], maximum_tray_displacement_m=shifts[1],
                  mean_settled_support_vertical_load_n=dict(tray=float(mean[0]),bench=float(mean[1])),
                  mean_separate_rim_vertical_load_n=dict(left=float(mean[2]),front=float(mean[3])),
                  expected_tool_weight_n=weight, relative_net_vertical_support_load_error=load_error,
                  maximum_replay_q_error=qe, maximum_replay_v_error=ve, unintended_contacts=violations,
                  full_final_qpos=data.qpos.tolist(), tool_final_qpos=data.qpos[tq:rq].tolist(),
                  tray_final_qpos=data.qpos[rq:rq+7].tolist(), trace_sha256=digest(output / 'trace.npz'),
                  contract_sha256=digest(output / 'contract.json'), seconds=time.monotonic()-started,
                  qualified_robot_grasp=False, qualified_paper_branch=False)
    (output / 'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if 'qpos' not in k}),flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('placement'); p.add_argument('output')
    p.add_argument('--selection',type=int,default=0)
    a = p.parse_args()
    if not run(a.placement,a.output,a.selection)['passed']: raise SystemExit(1)
