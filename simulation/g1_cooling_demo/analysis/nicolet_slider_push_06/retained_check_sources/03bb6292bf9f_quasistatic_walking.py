"""Slow, motor-driven stepping with explicit level-floor support assumptions.

Only encoders and IMU update this robot state. Foot contact is not measured:
support changes require a level sole at the declared floor and small velocity.
Independent plant replay must assess actual support, slip and collisions.
"""
import mujoco
import numpy as np

from balance import Balance
from observations import robot_joints


class StanceEstimate:
    def __init__(self, model, data, initial_xy):
        self.m, self.d = model, data
        joints = robot_joints(model)
        self.qa, self.va = model.jnt_qposadr[joints], model.jnt_dofadr[joints]
        self.soles = [model.site(s+'_sole').id for s in ['left', 'right']]
        self.anchors = None
        self.initial_xy = np.asarray(initial_xy, dtype=float)
        self.support = np.ones(2, dtype=bool)
        self.last_time = None

    def update(self, obs):
        if set(obs) != {'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:
            raise ValueError('Non-sensor field in stance estimate')
        if self.last_time == obs['time_s']:
            return self.d.qpos[:3].copy()
        m, d = self.m, self.d
        d.qpos[self.qa] = obs['joint_position']
        d.qvel[self.va] = obs['joint_velocity']
        d.qpos[3:7] = obs['imu_quaternion']
        d.qvel[3:6] = obs['imu_gyro']
        d.qpos[:3] = 0.
        d.qvel[:3] = 0.
        mujoco.mj_kinematics(m, d)
        feet = d.site_xpos[self.soles].copy()
        if self.anchors is None:
            self.anchors = feet.copy()
            self.anchors[:,:2] += self.initial_xy
            self.anchors[:,2] -= min(feet[:,2])
        d.qpos[:3] = np.mean((self.anchors-feet)[self.support], axis=0)
        mujoco.mj_forward(m, d)
        velocities = []
        for index in np.flatnonzero(self.support):
            jp, jr = np.zeros((3,m.nv)), np.zeros((3,m.nv))
            mujoco.mj_jacSite(m, d, jp, jr, self.soles[index])
            velocities.append(jp@d.qvel)
        d.qvel[:3] = -np.mean(velocities, axis=0)
        mujoco.mj_forward(m, d)
        self.last_time = obs['time_s']
        return d.qpos[:3].copy()


class QuasistaticWalker:
    """Alternate short steps, moving COM over the stance sole before lifting."""
    def __init__(self, model, data, initial_xy, goal_xy, step_length=.12):
        self.m, self.d = model, data
        self.estimate = StanceEstimate(model, data, initial_xy)
        self.goal = np.asarray(goal_xy, dtype=float)
        self.step_length = float(step_length)
        if self.goal.shape!=(2,) or not np.isfinite(self.goal).all() or not 0.<self.step_length<=.15:
            raise ValueError('Invalid stepping goal')
        self.balance = None
        self.parking_time = None
        self.parking_posture_weights = None
        self.phase = 'settle'
        self.phase_started = None
        self.next_control = 0.
        self.last_torque = np.zeros(model.nu)
        self.events = []
        self.swing = 0
        self.steps = 0
        self.finished = False

    @staticmethod
    def blend(u):
        u = float(np.clip(u,0.,1.))
        return u*u*u*(10.+u*(-15.+6.*u))

    def enter(self, phase, t):
        self.phase, self.phase_started = phase, t
        self.events.append(dict(state='quasistatic_'+phase, time_s=t, completed_steps=self.steps))

    def begin_step(self, t):
        feet = np.asarray(self.balance.foot_positions)
        center = feet[:,:2].mean(axis=0)
        remaining = self.goal-center
        if np.linalg.norm(remaining)<.008 and np.linalg.norm(feet[0,:2]-feet[1,:2]-self.initial_separation)<.008:
            self.shift_from = self.balance.com_target.copy()
            self.shift_to = self.shift_from.copy()
            self.shift_to[:2] = center
            self.enter('recenter',t)
            return
        self.shift_from = self.balance.com_target.copy()
        self.shift_to = self.shift_from.copy()
        self.shift_to[:2] = feet[1-self.swing,:2]
        target = self.goal+self.foot_offsets[self.swing]
        delta = target-feet[self.swing,:2]
        delta *= min(1.,self.step_length/max(np.linalg.norm(delta),1e-12))
        self.swing_from = feet[self.swing].copy()
        self.swing_to = self.swing_from.copy()
        self.swing_to[:2] += delta
        self.enter('shift',t)

    def torque(self, obs, command_override=None):
        t = float(obs['time_s'])
        self.estimate.update(obs)
        if self.balance is None:
            self.balance = Balance(self.m,self.d)
            # Support transfer makes this constrained solve harder. Increase
            # iteration allowance without changing tolerances or accepting an
            # unfinished solve; all stationary defaults remain unchanged.
            self.balance.solver_max_iterations = 30000
            self.balance.warm_start_dual = True
            self.balance.rotate_foot_constraints = True
            feet = np.asarray(self.balance.foot_positions)
            self.foot_offsets = feet[:,:2]-feet[:,:2].mean(axis=0)
            self.initial_separation = feet[0,:2]-feet[1,:2]
            self.phase_started = t
        if t+1e-8 < self.next_control:
            return self.last_torque,np.zeros(3)
        elapsed = t-self.phase_started
        b, d = self.balance,self.d
        if self.phase == 'settle' and elapsed>=2.:
            self.begin_step(t)
        elif self.phase in {'shift','recenter'}:
            b.com_target = self.shift_from+self.blend(elapsed/3.)*(self.shift_to-self.shift_from)
            error = np.linalg.norm(d.subtree_com[self.m.body('pelvis').id,:2]-self.shift_to[:2])
            if elapsed>=3. and error<.004 and np.linalg.norm(d.qvel[:2])<.015:
                if self.phase == 'recenter':
                    self.parking_time = t
                    self.finished = True
                    self.enter('parked',t)
                else:
                    self.estimate.support[self.swing] = False
                    self.enter('swing',t)
            elif elapsed>8.:
                raise RuntimeError('COM did not settle over the declared support sole')
        elif self.phase == 'swing':
            u = min(1.,elapsed/3.)
            target = self.swing_from+self.blend(u)*(self.swing_to-self.swing_from)
            # Zero position/velocity at both ends, without ground penetration.
            target[2] += .055*64*u**3*(1-u)**3
            b.foot_positions[self.swing] = target
            if elapsed>=3.:
                self.enter('land',t)
        elif self.phase == 'land':
            site = self.estimate.soles[self.swing]
            error = np.linalg.norm(d.site_xpos[site]-self.swing_to)
            j,_ = b.jacobian(d.site_xpos[site],int(self.m.site_bodyid[site]))
            speed = np.linalg.norm(j[:3]@d.qvel)
            flat = d.site_xmat[site].reshape(3,3)[2,2]>.999
            if elapsed>=.5 and error<.003 and speed<.015 and flat:
                # Measured kinematic anchor on the known level floor; this is
                # predictor state, never a write to the physical robot pose.
                self.estimate.anchors[self.swing] = d.site_xpos[site].copy()
                b.foot_positions[self.swing] = d.site_xpos[site].copy()
                self.estimate.support[self.swing] = True
                self.steps += 1
                self.swing = 1-self.swing
                self.begin_step(t)
            elif elapsed>4.:
                raise RuntimeError('Swing sole did not settle at the declared floor')
        self.last_torque = b.torque(dt=.01,support_feet=self.estimate.support,
                                   posture_weights=self.parking_posture_weights)
        self.next_control = t+.01
        return self.last_torque,np.zeros(3)
