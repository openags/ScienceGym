"""Inspect recorded tool contact wrenches outside the isolated controller.

Sparse states are reconstructed with mj_forward; this is a diagnostic, not a
continuous replay or grasp qualification. The rigid-tool friction-cone LP is
an optimistic static feasibility screen, not a flexible-tool controller.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.optimize import linprog


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(folder, times):
    folder = Path(folder).resolve()
    trace = dict(np.load(folder / 'trace.npz'))
    model = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    data = mujoco.MjData(model)
    root = model.body('tweezer').id
    bodies = {root}
    for b in range(model.nbody):
        if int(model.body_parentid[b]) in bodies:
            bodies.add(b)
    mass = float(sum(model.body_mass[b] for b in bodies))
    result = json.loads((folder / 'result.json').read_text())
    assert sha(folder / 'trace.npz') == result['trace_sha256']
    rows = []
    for requested in times:
        i = int(np.argmin(abs(trace['time'] - requested)))
        data.qpos[:] = trace['qpos'][i]
        data.qvel[:] = trace['qvel'][i]
        data.ctrl[:] = trace['ctrl'][i]
        data.qacc_warmstart[:] = trace['qacc_warmstart'][i]
        mujoco.mj_forward(model, data)
        com = data.subtree_com[root].copy()
        contacts = []
        for ci, c in enumerate(data.contact):
            bs = [int(model.geom_bodyid[g]) for g in c.geom]
            if sum(b in bodies for b in bs) != 1:
                continue
            other = next(b for b in bs if b not in bodies)
            name = model.body(other).name
            if not name.startswith('right_hand_'):
                continue
            f = np.zeros(6)
            mujoco.mj_contactForce(model, data, ci, f)
            if f[0] <= 1e-6:
                continue
            sign = 1. if bs[1] in bodies else -1.
            frame = sign * c.frame.reshape(3, 3)
            force = frame.T @ f[:3]
            torque = np.cross(c.pos - com, force) + frame.T @ f[3:]
            contact = dict(body=name, tool_body=model.body(next(b for b in bs if b in bodies)).name,
                point_world_m=c.pos.tolist(), normal_world=frame[0].tolist(),
                tangent1_world=frame[1].tolist(), tangent2_world=frame[2].tolist(),
                normal_force_n=float(f[0]), world_force_n=force.tolist(),
                world_torque_about_com_nm=torque.tolist(), friction=c.friction.tolist(),
                tangential_force_n=float(np.linalg.norm(f[1:3])), penetration_m=max(0., -float(c.dist)))
            contacts.append(contact)
        force = np.sum([c['world_force_n'] for c in contacts], axis=0) if contacts else np.zeros(3)
        torque = np.sum([c['world_torque_about_com_nm'] for c in contacts], axis=0) if contacts else np.zeros(3)
        fingers = ['thumb', 'index', 'middle']
        summary = {}
        for finger in fingers:
            cs = [c for c in contacts if finger in c['body']]
            load = sum(c['normal_force_n'] for c in cs)
            summary[finger] = dict(normal_force_n=load,
                center_world_m=(sum(np.asarray(c['point_world_m']) * c['normal_force_n'] for c in cs) / load).tolist() if load else None,
                world_force_n=np.sum([c['world_force_n'] for c in cs], axis=0).tolist() if cs else [0., 0., 0.])
        columns, owners = [], []
        for c in contacts:
            n, t1, t2 = [np.asarray(c[k]) for k in ['normal_world', 'tangent1_world', 'tangent2_world']]
            mu = min(c['friction'][:2])
            for a in np.arange(12) * (2*np.pi/12):
                direction = n + mu * (np.cos(a)*t1 + np.sin(a)*t2)
                columns.append(np.r_[direction, np.cross(np.asarray(c['point_world_m']) - com, direction)])
                owners.append(next(j for j, f in enumerate(fingers) if f in c['body']))
        lp_result = dict(feasible=False, explanation='No loaded hand contact')
        if columns:
            # Minimize peak per-finger load using independent contact forces.
            A = np.column_stack(columns)
            eq = np.c_[A, np.zeros(6)]
            eq[3:] *= 100.  # SI torque rows scaled for solver conditioning.
            rhs = np.r_[-mass * model.opt.gravity, np.zeros(3)]
            ub = np.zeros((3, len(columns)+1))
            for j, owner in enumerate(owners):
                ub[owner, j] = 1.
            ub[:, -1] = -1.
            lp = linprog(np.r_[np.zeros(len(columns)), 1.], A_eq=eq, b_eq=rhs,
                A_ub=ub, b_ub=np.zeros(3), bounds=[(0, None)]*len(columns)+[(0, 4.)], method='highs')
            lp_result = dict(feasible=bool(lp.success), explanation=lp.message)
            if lp.success:
                loads = ub[:, :-1] @ lp.x[:-1]
                lp_result.update(minimum_peak_finger_force_n=float(lp.x[-1]),
                    finger_normal_force_n=dict(zip(fingers, loads.tolist())),
                    unscaled_wrench_residual=(A@lp.x[:-1]-rhs).tolist())
        rows.append(dict(time_s=float(trace['time'][i]), tool_position_m=data.xpos[root].tolist(),
            tool_rotation=data.xmat[root].reshape(3, 3).tolist(), center_of_mass_m=com.tolist(),
            hand_force_n=force.tolist(), hand_torque_about_com_nm=torque.tolist(),
            force_plus_gravity_n=(force+mass*model.opt.gravity).tolist(),
            fingers=summary, optimistic_rigid_equilibrium=lp_result, contacts=contacts))
    report = dict(scope=__doc__, model_sha256=sha(folder/'world.xml'), trace_sha256=sha(folder/'trace.npz'),
        script_sha256=sha(__file__), tool_mass_kg=mass, rows=rows,
        continuous_replay=False, qualified_grasp=False)
    (folder/'contact_wrench_diagnosis.json').write_text(json.dumps(report, indent=2)+'\n')
    for r in rows:
        print(json.dumps({k:r[k] for k in ['time_s','hand_force_n','hand_torque_about_com_nm','fingers','optimistic_rigid_equilibrium']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--times', type=float, nargs='+', required=True)
    args = parser.parse_args()
    run(args.folder, args.times)
