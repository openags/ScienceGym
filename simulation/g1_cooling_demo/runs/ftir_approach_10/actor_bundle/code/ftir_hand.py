"""Source-hand affordance and robot-only arm IK for a panel button press."""
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from robot_state import initialize as initialize_robot


POINTING = dict(right_index_1_joint=0., right_middle_1_joint=1.25,
                right_ring_1_joint=1.25, right_little_1_joint=1.25,
                right_thumb_1_joint=1., right_thumb_2_joint=.2)


def rest_hand_pose():
    """The authored folded hand posture used by the clear stationary setup."""
    result = {}
    for side in ['left', 'right']:
        for finger in ['index', 'middle', 'ring', 'little']:
            result[side+'_'+finger+'_1_joint'] = 1.1
        result[side+'_thumb_1_joint'] = .8
        result[side+'_thumb_2_joint'] = .3
    return result


def walking_shoulder_pose():
    """Initial outward shoulder angles for the walking clearance guard."""
    return dict(left_shoulder_roll_joint=.4, right_shoulder_roll_joint=-.4)


def walking_arm_pose():
    """Authored arm hold with wrists behind the pelvis in the source model.

    These angles do not raise the wrists above the bench handles: measured
    wrist height during probe 08 is about 0.55–0.59 m. Clearance is checked
    geometrically rather than inferred from the joint-angle signs.
    """
    result = {}
    for side, sign in [('left', 1.), ('right', -1.)]:
        for joint, value in dict(shoulder_pitch=.35, shoulder_roll=sign*.3,
                                 shoulder_yaw=0., elbow=1.5, wrist_roll=0.,
                                 wrist_pitch=0., wrist_yaw=0.).items():
            result[side+'_'+joint+'_joint'] = value
    return result


def mimic(model, data):
    for i in range(model.neq):
        data.qpos[model.jnt_qposadr[model.eq_obj1id[i]]] = (model.eq_data[i, 0]
            + model.eq_data[i, 1]*data.qpos[model.jnt_qposadr[model.eq_obj2id[i]]])


def initialize(model, xy=(5.95, -5.55)):
    """Authored, collision-screened initial posture; no execution credit."""
    data = initialize_robot(model)
    data.qpos[:2] = xy
    for name, value in dict(waist_pitch_joint=-.2, left_elbow_joint=1.5, left_shoulder_roll_joint=.3,
                            right_elbow_joint=-.8, right_shoulder_roll_joint=-.4,
                            right_shoulder_yaw_joint=-.3).items():
        data.joint(name).qpos[0] = value
    for name, value in rest_hand_pose().items():
        data.joint(name).qpos[0] = value
    mimic(model, data)
    mujoco.mj_forward(model, data)
    return data


def initialize_cover(model, xy=(5.95, -5.35)):
    """Prepared cover stance: observe the controls without clipping the row."""
    data=initialize(model,xy)
    data.joint('waist_pitch_joint').qpos[0]=-.3
    data.joint('waist_yaw_joint').qpos[0]=-.2
    data.joint('left_shoulder_pitch_joint').qpos[0]=.2
    mujoco.mj_forward(model,data)
    return data


class PointingHand:
    def __init__(self, model, hand_q=None):
        data = mujoco.MjData(model)
        pose = dict(POINTING)
        pose.update(hand_q or {})
        for name, value in pose.items():
            joint = model.joint(name)
            if name not in POINTING or not np.isfinite(value):
                raise ValueError('Invalid source hand pose')
            if model.jnt_limited[joint.id] and not model.jnt_range[joint.id,0] <= value <= model.jnt_range[joint.id,1]:
                raise ValueError('Hand pose exceeds source joint bounds')
            data.joint(name).qpos[0] = value
        mimic(model, data); mujoco.mj_forward(model, data)
        geom = model.geom('right_index_force_sensor_3_collision_0').id
        mesh = model.geom_dataid[geom]
        vertices = model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]]
        world = vertices @ data.geom(geom).xmat.reshape(3,3).T + data.geom(geom).xpos
        wrist = data.site('right_wrist_reference')
        self.pad_vertices = (world-wrist.xpos) @ wrist.xmat.reshape(3,3)
        pad = data.body('right_index_force_sensor_3')
        self.pad_origin = (pad.xpos-wrist.xpos) @ wrist.xmat.reshape(3,3)
        self.pad_rotation = wrist.xmat.reshape(3,3).T @ pad.xmat.reshape(3,3)

    def at_surface(self, center, normal, row_direction):
        normal = np.asarray(normal); normal /= np.linalg.norm(normal)
        row = np.asarray(row_direction); row -= np.dot(row,normal)*normal; row /= np.linalg.norm(row)
        back = np.cross(normal, row)
        pointing = np.sin(np.deg2rad(35))*back - np.cos(np.deg2rad(35))*normal
        lateral = -row
        rotation = np.column_stack([lateral, pointing, np.cross(lateral, pointing)])
        rotation = Rotation.from_rotvec(pointing*-.2).as_matrix() @ rotation
        heights = (self.pad_vertices @ rotation.T) @ normal
        contact = self.pad_vertices[heights < heights.min()+2e-5].mean(axis=0)
        wrist = np.asarray(center)-rotation @ contact
        return wrist, rotation, contact

    def observed_contact_point(self, data, wrist_local_contact):
        local = (wrist_local_contact-self.pad_origin) @ self.pad_rotation
        pad = data.body('right_index_force_sensor_3')
        return pad.xpos + pad.xmat.reshape(3,3) @ local


class ArmIK:
    def __init__(self, model):
        self.model = model
        self.data = mujoco.MjData(model)
        names = ['right_shoulder_pitch_joint','right_shoulder_roll_joint','right_shoulder_yaw_joint',
                 'right_elbow_joint','right_wrist_roll_joint','right_wrist_pitch_joint','right_wrist_yaw_joint']
        self.joints = np.array([model.joint(n).id for n in names])
        self.qa, self.va = model.jnt_qposadr[self.joints], model.jnt_dofadr[self.joints]
        self.low = model.jnt_range[self.joints,0]+.005
        self.high = model.jnt_range[self.joints,1]-.005
        self.site = model.site('right_wrist_reference').id

    def solve(self, estimated, position, rotation, seed=None):
        m,d = self.model,self.data
        d.qpos[:] = estimated.qpos
        if seed is not None: d.qpos[self.qa] = seed
        for _ in range(100):
            mujoco.mj_kinematics(m,d); mujoco.mj_comPos(m,d)
            position_error = np.asarray(position)-d.site_xpos[self.site]
            orientation_error = Rotation.from_matrix(rotation @ d.site_xmat[self.site].reshape(3,3).T).as_rotvec()
            if np.linalg.norm(position_error)<.0002 and np.linalg.norm(orientation_error)<.004:break
            jp,jr=np.zeros((3,m.nv)),np.zeros((3,m.nv));mujoco.mj_jacSite(m,d,jp,jr,self.site)
            jac=np.vstack([jp[:,self.va],.15*jr[:,self.va]])
            error=np.r_[position_error,.15*orientation_error]
            step=np.linalg.solve(jac.T@jac+np.eye(7)*1e-5,jac.T@error)
            step*=min(1.,.15/max(np.linalg.norm(step),1e-12))
            d.qpos[self.qa]=np.clip(d.qpos[self.qa]+step,self.low,self.high)
        return d.qpos[self.qa].copy(),float(np.linalg.norm(position_error)),float(np.linalg.norm(orientation_error))
