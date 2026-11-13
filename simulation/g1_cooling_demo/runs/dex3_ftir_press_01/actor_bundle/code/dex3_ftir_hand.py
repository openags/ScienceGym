"""Pointing affordance from the official Dex3 index-finger surface.

The fingertip is an existing material surface of the robot. No contact proxy,
extra pad, device pose, or simulator contact observation is introduced.
"""
import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from robot_source_meshes import robot_source_meshes


POINTING = dict(right_hand_thumb_0_joint=0., right_hand_thumb_1_joint=-.6,
    right_hand_thumb_2_joint=-1.4, right_hand_middle_0_joint=1.3,
    right_hand_middle_1_joint=1.5, right_hand_index_0_joint=.01,
    right_hand_index_1_joint=.01)


class Dex3PointingHand:
    body_name = 'right_hand_index_1_link'

    def __init__(self, model, hand_q=None):
        if model.nu != 43 or model.neq:
            raise ValueError('This affordance requires the source G1/Dex3 model')
        self.pose = dict(POINTING)
        self.pose.update(hand_q or {})
        if self.pose.keys() != POINTING.keys():
            raise ValueError('Unexpected joint in the Dex3 pointing pose')
        data = mujoco.MjData(model)
        for name, value in self.pose.items():
            joint = model.joint(name)
            lo, hi = model.jnt_range[joint.id]
            if not np.isfinite(value) or not lo+.005 <= value <= hi-.005:
                raise ValueError('Pointing posture violates the source joint margin')
            data.joint(name).qpos[0] = value
        mujoco.mj_kinematics(model, data)
        mesh = robot_source_meshes(model, visual_groups=(1, 2))[self.body_name]
        pad, wrist = data.body(self.body_name), data.site('right_wrist_reference')
        world = mesh.vertices @ pad.xmat.reshape(3, 3).T + pad.xpos
        self.pad_vertices = (world-wrist.xpos) @ wrist.xmat.reshape(3, 3)
        self.pad_origin = (pad.xpos-wrist.xpos) @ wrist.xmat.reshape(3, 3)
        self.pad_rotation = wrist.xmat.reshape(3, 3).T @ pad.xmat.reshape(3, 3)

    def at_surface(self, center, normal, row_direction, lean_rad=.35, roll_rad=0.):
        center, normal, row = [np.asarray(v, dtype=float).copy()
                               for v in [center, normal, row_direction]]
        if any(v.shape != (3,) or not np.isfinite(v).all() for v in [center, normal, row]):
            raise ValueError('Surface frame must contain finite 3-vectors')
        if np.linalg.norm(normal) < 1e-8 or not 0. <= lean_rad <= .8:
            raise ValueError('Invalid pointing approach direction')
        normal /= np.linalg.norm(normal)
        row -= np.dot(row, normal)*normal
        if np.linalg.norm(row) < 1e-8 or not np.isfinite(roll_rad):
            raise ValueError('Degenerate observed button-row direction')
        row /= np.linalg.norm(row)
        back = np.cross(normal, row)
        pointing = np.sin(lean_rad)*back - np.cos(lean_rad)*normal
        # The actual Dex3 distal finger extends along its local +X axis.
        distal_rotation = np.column_stack([pointing, np.cross(row, pointing), row])
        distal_rotation = Rotation.from_rotvec(pointing*roll_rad).as_matrix() @ distal_rotation
        rotation = distal_rotation @ self.pad_rotation.T
        heights = (self.pad_vertices @ rotation.T) @ normal
        contact = self.pad_vertices[heights <= heights.min()+2e-5].mean(axis=0)
        return center-rotation@contact, rotation, contact

    def observed_contact_point(self, data, wrist_local_contact):
        local = (np.asarray(wrist_local_contact)-self.pad_origin) @ self.pad_rotation
        pad = data.body(self.body_name)
        return pad.xpos + pad.xmat.reshape(3, 3) @ local
