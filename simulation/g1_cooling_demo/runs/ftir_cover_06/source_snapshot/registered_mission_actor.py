"""Isolated walking/transport actor with depth registration at the workbench."""
import argparse,pickle,sys
import mujoco
import numpy as np
from mission_actor import MissionActor
from observations import StateEstimate
from map_localization import MapLocalization


class RegisteredMissionActor(MissionActor):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.registration=None;self.registration_started=None;self.registration_updates=[]
        self.registration_previous_depth=None

    def start_carrier(self,obs):
        self.events[-1]['state']='stationary_before_map_registration'
        self.estimate=StateEstimate(self.m,self.data)
        self.registration=MapLocalization(self.m,self.data)
        self.registration_started=float(obs['time_s']);self.stage='localize_workstation'
        self.events.append(dict(state='begin_static_map_registration',time_s=self.registration_started))

    def activate_carrier(self,obs):
        self.registration.close();self.registration=None
        self.events.append(dict(state='stationary_control_stable',time_s=float(obs['time_s']),parking_time_s=self.walker.parking_time))
        super().start_carrier(obs)

    def update(self,obs):
        if self.stage!='localize_workstation':
            result=super().update(obs)
        else:
            if set(obs)!={'time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro','depth'}:raise ValueError('Non-sensor field in actor input')
            t=float(obs['time_s']);self.estimate.update(obs)
            self.last_torque,_=self.walker.torque(obs,command_override=np.zeros(3))
            if obs['depth'] is not None:
                self.latest_depth=obs['depth'];self.latest_depth_time=t
                fitted=self.registration.register(obs['depth'])
                if not fitted['accepted']:raise RuntimeError('Static map registration failed: '+fitted.get('reason','residual'))
                correction=np.asarray(fitted['correction_m']);self.estimate.anchors+=correction
                last=fitted['iterations'][-1]
                summary=dict(time_s=t,correction_m=correction.tolist(),position_m=fitted['position_m'],median_residual_m=last['median_residual_m'],points=last['points'])
                self.registration_updates.append(summary)
                self.events.append(dict(state='static_map_registration_update',**summary))
            if len(self.registration_updates)>=5 and t-self.registration_started>=.5:
                self.activate_carrier(obs)
            if t-self.registration_started>3:raise RuntimeError('Static map registration did not settle')
            result=super().update(obs)
        result['static_map_registration_updates']=len(self.registration_updates)
        return result

    def close(self):
        if self.registration:self.registration.close()
        super().close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--policy',default='/model/policy')
    p.add_argument('--initial-xy',type=float,nargs=2,default=[-.9,0.]);a=p.parse_args()
    model=mujoco.MjModel.from_xml_path(a.model);actor=RegisteredMissionActor(model,a.policy,a.initial_xy)
    try:
        while True:
            try:packet=pickle.load(sys.stdin.buffer)
            except EOFError:break
            try:response=actor.update(packet)
            except Exception as error:response=dict(torque=np.zeros(model.nu),error=str(error))
            pickle.dump(response,sys.stdout.buffer,protocol=5);sys.stdout.buffer.flush()
            if response['error']:break
    finally:actor.close()

if __name__=='__main__':main()
