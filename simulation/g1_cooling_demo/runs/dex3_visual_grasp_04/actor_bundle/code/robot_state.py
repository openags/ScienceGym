"""Initialize the robot's own posture and nominal sole plane, without objects."""
import mujoco


def initialize(model):
    data = mujoco.MjData(model)
    for side in ['left', 'right']:
        data.joint(side+'_hip_pitch_joint').qpos[0] = -.06
        data.joint(side+'_knee_joint').qpos[0] = .12
        data.joint(side+'_ankle_pitch_joint').qpos[0] = -.06
        data.joint(side+'_elbow_joint').qpos[0] = .45
    mujoco.mj_forward(model, data)
    data.qpos[2] -= min(data.site(s+'_sole').xpos[2] for s in ['left', 'right'])
    mujoco.mj_forward(model, data)
    return data
