"""Observe the FTIR key row, then turn the torso into the approach posture.

This sensor-only preparation attempt does not touch or open the window. It
tests whether the new authored stance can observe the device while balancing
and return its torso to the independently screened arm-planning orientation.
"""
import argparse
import pickle
import sys

import mujoco
import numpy as np

from ftir_actor import FTIRActor
from ftir_slider_posture import initialize_slider


class SliderScanActor(FTIRActor):
    def __init__(self,model,xy):
        super().__init__(model,xy,initial_state=initialize_slider(model,xy))
        self.initial_com=self.d.subtree_com[model.body('pelvis').id].copy()
        self.centered_com=self.balance.com_target.copy()
        self.turn_started=None
        self.stable_since=None
        self.scan_observations=None
        self.state='observe'

    def update(self,obs):
        if set(obs)!=self.fields:
            raise ValueError('Non-sensor field in FTIR actor input')
        t=float(obs['time_s']);detection=None
        if t+1e-8>=self.next_control:
            self.estimate.update({k:v for k,v in obs.items() if k!='rgb'})
            if obs['rgb'] is not None and obs['depth'] is not None:
                detection=self.vision.observe(obs['rgb'],obs['depth'])
                if detection and detection['accepted']:
                    self.observations.append(detection);self.total_accepted+=1
            if self.turn_started is None and t>=2. and len(self.observations)>=8:
                recent=self.observations[-8:]
                labels=['SAMPLE','BACKGROUND','OK / ENTER','STOP']
                positions=np.array([[o['buttons'][key] for key in labels] for o in recent])
                spread=float(np.max(np.std(positions,axis=0)))
                if spread>.002:raise RuntimeError('Observed FTIR key row is not stationary')
                self.scan_observations=recent
                self.turn_started=t
                self.events.append(dict(state='observed_key_row',time_s=t,
                                        observations=recent,maximum_coordinate_std_m=spread))
            if self.turn_started is None and t>5.:
                raise RuntimeError('Four FTIR controls were not observed reliably')
            posture=self.original_posture.copy()
            if self.turn_started is not None:
                u=float(np.clip((t-self.turn_started)/3.,0,1))
                posture[self.actuator_ids['waist_yaw_joint']]=-.5+.3*u*u*(3-2*u)
                self.state='turn_to_approach' if u<1 else 'settle'
                q=float(self.d.joint('waist_yaw_joint').qpos[0])
                velocity=float(self.d.joint('waist_yaw_joint').qvel[0])
                if u>=1 and abs(q+.2)<.02 and abs(velocity)<.03:
                    if self.stable_since is None:self.stable_since=t
                    if t-self.stable_since>=1.:
                        self.finished=True;self.state='finished'
                else:self.stable_since=None
                if t-self.turn_started>9. and not self.finished:
                    raise RuntimeError('Torso did not settle at the approach orientation')
            settle=float(np.clip(t/2.,0,1));settle=settle*settle*(3-2*settle)
            self.balance.com_target=self.initial_com+settle*(self.centered_com-self.initial_com)
            self.last_torque=self.balance.torque(posture=posture,
                dt=.01 if self.last_time is None else t-self.last_time)
            self.last_time=t;self.next_control=(round(t*100)+1)/100
        return dict(torque=self.last_torque,error=None,policy_state=self.state,
                    policy_complete=self.finished,policy_failure=None,events=self.events,
                    accepted_key_observations=self.total_accepted,observation=detection,
                    estimated_root_position_m=self.d.qpos[:3].tolist(),
                    estimated_waist_yaw_rad=float(self.d.joint('waist_yaw_joint').qpos[0]),
                    scope='Sensor observation and torso preparation only; no window manipulation')


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True)
    p.add_argument('--initial-xy',nargs=2,type=float,default=[5.95,-5.20]);a=p.parse_args()
    model=mujoco.MjModel.from_xml_path(a.model);actor=SliderScanActor(model,a.initial_xy)
    while True:
        try:packet=pickle.load(sys.stdin.buffer)
        except EOFError:break
        try:response=actor.update(packet)
        except Exception as error:response=dict(torque=np.zeros(model.nu),error=str(error))
        pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
        if response['error']:break


if __name__=='__main__':main()
