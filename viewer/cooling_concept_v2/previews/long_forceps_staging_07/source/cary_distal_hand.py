"""Include the terminal wrist housing rigidly attached to each source hand.

The yaw-link housing has a constant transform relative to the palm. Earlier
finger-only fits omitted it and could admit impossible wrist/wrist crossings.
Upstream wrist pitch/roll housings still require whole-arm kinematics.
"""
import numpy as np
from source_geometry import hand_manager,robot_meshes,fk


def distal_hand_manager(side,body_meshes=None):
    hand=hand_manager(side);name=side+'_wrist_yaw_link'
    hand.add_object(name,(body_meshes if body_meshes is not None else robot_meshes())[name])
    a=fk({});b=fk({side+'_wrist_yaw_joint':.31,side+'_wrist_pitch_joint':-.24,
                  side+'_shoulder_pitch_joint':-.7})
    assert np.max(abs(np.linalg.inv(a[side+'_palm_force_sensor'])@a[name]-
                     np.linalg.inv(b[side+'_palm_force_sensor'])@b[name]))<1e-10
    return hand
