"""Authored starting stance for observing and approaching the FTIR window.

This setup does not represent executed walking or preparation.
"""
import mujoco

from ftir_hand import initialize_cover, ArmIK, mimic


def initialize_slider(model, xy=(5.95, -5.20)):
    data=initialize_cover(model,xy)
    data.joint('waist_yaw_joint').qpos[0]=-.5
    # Keep the unused hand behind the bench front during COM settling.
    # The first attempt's .2 rad pose grazed the table; .5 rad is screened
    # across retained torso states and still requires independent replay.
    data.joint('left_shoulder_pitch_joint').qpos[0]=.5
    data.qpos[ArmIK(model).qa]=[.2,-.3,0.,1.5,0.,0.,0.]
    mimic(model,data)
    mujoco.mj_forward(model,data)
    return data
