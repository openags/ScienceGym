"""Sensor-only actor with depth-observed transport stage transitions."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,pickle,sys
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from world import initialize
from balance import Balance
from observations import StateEstimate
from tracking import TrayTracker
from policy import FeedbackPolicy

def main(path,return_to_source=False,grip_force=15,finger_curl=0.,com_align=False,carried_mass=0.):
    model=mujoco.MjModel.from_xml_path(path);data=initialize(model);estimate=StateEstimate(model,data);controller=Balance(model,data);tracker=TrayTracker(model,data)
    zero=mujoco.MjData(model);mujoco.mj_forward(model,zero)
    controller.palm_rotations={s:Rotation.from_euler('x',-45 if s=='left' else 45,degrees=True).as_matrix()@zero.site(s+'_wrist_reference').xmat.reshape(3,3) for s in ['left','right']}
    policy=FeedbackPolicy({s:data.site(s+'_wrist_reference').xpos.copy() for s in ['left','right']},return_to_source,grip_force)
    initial_com=controller.com_target.copy();com_y=float(initial_com[1])
    try:
        while True:
            try:obs=pickle.load(sys.stdin.buffer)
            except EOFError:break
            try:
                estimate.update(obs);detection=tracker.observe(obs['depth']);targets,forces=policy.update(obs['time_s'],detection,obs['depth'] is not None)
                fraction=float(np.clip((obs['time_s']-policy.started)/max(policy.duration,.001),0,1));fraction=fraction*fraction*(3-2*fraction)
                support=fraction if policy.state=='lift' else 1-fraction if policy.state=='place' else 1. if policy.state in ['confirm_lift','transfer','confirm_transfer'] else 0.
                controller.com_target[0]=initial_com[0]-.025*support*min(carried_mass/1.76,1)
                if com_align:
                    requested=initial_com[1]+(np.clip(policy.y*.65,-.05,.05) if hasattr(policy,'y') and not policy.complete else 0)
                    com_y+=float(np.clip(requested-com_y,-.00015,.00015));controller.com_target[1]=com_y
                posture=controller.posture.copy()
                for i,j in enumerate(model.actuator_trnid[:,0]):
                    if any(name in model.joint(j).name for name in ['index','middle','ring','little']):posture[i]=finger_curl*policy.current_force/policy.grip_force
                torque=controller.torque(targets=targets,forces=forces,posture=posture,supported_mass=carried_mass*support)
                result=dict(torque=torque,observed_target=None if policy.target is None else policy.target.tolist(),depth_detections=len(policy.observations),maximum_qp_iterations=controller.max_iter,policy_state=policy.state,policy_phase=policy.phase,policy_complete=policy.complete,policy_events=policy.events,depth_observation=detection,error=None)
            except Exception as e:result=dict(torque=np.zeros(model.nu),policy_state=policy.state,policy_events=policy.events,maximum_qp_iterations=controller.max_iter,error=str(e))
            pickle.dump(result,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
            if result['error']:break
    finally:tracker.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--return-to-source',action='store_true');p.add_argument('--grip-force',type=float,default=15);p.add_argument('--finger-curl',type=float,default=0.);p.add_argument('--com-align',action='store_true');p.add_argument('--carried-mass',type=float,default=0.);a=p.parse_args();main(a.model,a.return_to_source,a.grip_force,a.finger_curl,a.com_align,a.carried_mass)
