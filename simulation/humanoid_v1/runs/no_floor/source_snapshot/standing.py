"""Floating-base inverse-dynamics controller for two supported H2 feet.

Only source joint motors receive commands. Contact wrenches are optimization
variables used to calculate motor torques; they are never applied as forces.
"""
import numpy as np
import mujoco
import osqp
from scipy import sparse
from scipy.spatial.transform import Rotation


class StandingController:
    def __init__(self, model, data):
        self.m, self.d = model, data
        self.joints = model.actuator_trnid[:, 0]
        self.qa = model.jnt_qposadr[self.joints]
        self.va = model.jnt_dofadr[self.joints]
        self.posture = data.qpos[self.qa].copy()
        self.feet = [model.site(s + '_sole').id for s in ['left', 'right']]
        self.foot_positions = [data.site_xpos[s].copy() for s in self.feet]
        self.foot_rotations = [data.site_xmat[s].reshape(3, 3).copy() for s in self.feet]
        self.com_target = data.subtree_com[model.body('pelvis').id].copy()
        self.com_target[:2] = np.mean(self.foot_positions, axis=0)[:2]
        self.previous_com_jacobian = None
        self.previous_solution = None
        self.maximum_iterations = 0
        self.wrist_error_integral = {s: np.zeros(3) for s in ['left', 'right']}

    def jacobian(self, point, body):
        jp, jr = np.zeros((3, self.m.nv)), np.zeros((3, self.m.nv))
        mujoco.mj_jac(self.m, self.d, jp, jr, point, body)
        dp, dr = np.zeros_like(jp), np.zeros_like(jr)
        mujoco.mj_jacDot(self.m, self.d, dp, dr, point, body)
        return np.vstack([jp, jr]), np.vstack([dp, dr])

    def torque(self, target=None, dt=.005, wrist_targets=None):
        m, d = self.m, self.d
        n, total = m.nv, m.nv + 12
        target = self.posture if target is None else target
        mass = np.zeros((n, n)); mujoco.mj_fullM(m, d, mass)
        jac, accelerations = [], []
        for k, site in enumerate(self.feet):
            point = d.site_xpos[site]
            j, dj = self.jacobian(point, int(m.site_bodyid[site]))
            error = np.r_[self.foot_positions[k] - point,
                          Rotation.from_matrix(self.foot_rotations[k] @ d.site_xmat[site].reshape(3, 3).T).as_rotvec()]
            jac.append(j); accelerations.append(200 * error - 28 * (j @ d.qvel) - dj @ d.qvel)
        jfeet = np.vstack(jac)
        e = np.eye(n)
        rows, targets = [], []
        rows.append(np.c_[e[self.va], np.zeros((len(self.va), 12))])
        targets.append(40 * (target - d.qpos[self.qa]) - 12 * d.qvel[self.va])
        comj = np.zeros((3, n)); mujoco.mj_jacSubtreeCom(m, d, comj, m.body('pelvis').id)
        comdjv = np.zeros(3) if self.previous_com_jacobian is None else ((comj - self.previous_com_jacobian) / dt) @ d.qvel
        self.previous_com_jacobian = comj.copy()
        rows.append(12 * np.c_[comj, np.zeros((3, 12))])
        targets.append(12 * (70 * (self.com_target - d.subtree_com[m.body('pelvis').id]) - 18 * (comj @ d.qvel) - comdjv))
        pelvis = m.body('pelvis').id
        basej, basedj = self.jacobian(d.body(pelvis).xpos, pelvis)
        upright = Rotation.from_matrix(d.body(pelvis).xmat.reshape(3, 3).T).as_rotvec()
        rows.append(8 * np.c_[basej[3:], np.zeros((3, 12))])
        targets.append(8 * (60 * upright - 16 * (basej[3:] @ d.qvel) - basedj[3:] @ d.qvel))
        for side, reference in (wrist_targets or {}).items():
            site = m.site(side + '_wrist_reference').id
            j, dj = self.jacobian(d.site_xpos[site], int(m.site_bodyid[site]))
            error = reference['position'] - d.site_xpos[site]
            # Bounded integral feedback rejects source joint friction without
            # changing that friction or writing the wrist/object pose.
            self.wrist_error_integral[side] = np.clip(self.wrist_error_integral[side] + dt * error, -.04, .04)
            rows.append(75 * np.c_[j[:3], np.zeros((3, 12))])
            targets.append(75 * (reference['acceleration'] + 120 * error + 80 * self.wrist_error_integral[side]
                                 + 24 * (reference['velocity'] - j[:3] @ d.qvel) - dj[:3] @ d.qvel))
        rows.append(np.c_[np.zeros((12, n)), np.eye(12) * .0003]); targets.append(np.zeros(12))
        cost = np.vstack(rows); desired = np.concatenate(targets)
        p = cost.T @ cost + np.eye(total) * 1e-6
        q = -cost.T @ desired
        dynamics = np.c_[mass, -jfeet.T]
        constraints = [dynamics[:6], np.c_[jfeet, np.zeros((12, 12))], dynamics[self.va]]
        low = [-d.qfrc_bias[:6], np.concatenate(accelerations), m.actuator_ctrlrange[:, 0] - d.qfrc_bias[self.va]]
        high = [-d.qfrc_bias[:6], np.concatenate(accelerations), m.actuator_ctrlrange[:, 1] - d.qfrc_bias[self.va]]
        # World-frame friction pyramid and centre-of-pressure bounds for
        # nearly level feet, deliberately inside the source support polygon.
        wrench_rows, wrench_low, wrench_high = [], [], []
        for k in range(2):
            offset = n + 6 * k
            row = np.zeros(total); row[offset + 2] = 1
            wrench_rows.append(row); wrench_low.append(10.); wrench_high.append(1200.)
            for axis, coefficient in [(0, .6), (1, .6), (3, .025), (4, .09), (5, .015)]:
                for sign in [-1, 1]:
                    row = np.zeros(total); row[offset + axis] = sign; row[offset + 2] = -coefficient
                    wrench_rows.append(row); wrench_low.append(-np.inf); wrench_high.append(0.)
        constraints.append(np.array(wrench_rows)); low.append(wrench_low); high.append(wrench_high)
        solver = osqp.OSQP()
        solver.setup(P=sparse.csc_matrix(np.triu(p)), q=q, A=sparse.csc_matrix(np.vstack(constraints)),
                     l=np.concatenate(low), u=np.concatenate(high), verbose=False,
                     eps_abs=1e-5, eps_rel=1e-5, max_iter=10000, polishing=True)
        if self.previous_solution is not None: solver.warm_start(x=self.previous_solution)
        answer = solver.solve(raise_error=False)
        if answer.info.status_val not in (1, 2):
            raise RuntimeError('Standing inverse dynamics failed: ' + answer.info.status)
        self.maximum_iterations = max(self.maximum_iterations, answer.info.iter)
        self.previous_solution = answer.x
        torque = dynamics[self.va] @ answer.x + d.qfrc_bias[self.va]
        if np.any(torque < m.actuator_ctrlrange[:, 0] - .01) or np.any(torque > m.actuator_ctrlrange[:, 1] + .01):
            raise RuntimeError('QP motor torque exceeds source range')
        return np.clip(torque, m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1])
