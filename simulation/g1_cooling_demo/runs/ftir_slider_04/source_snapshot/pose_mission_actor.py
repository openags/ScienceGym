"""Sensor-only joined mission with a declared CAD shape and pose-gated grasp."""
import argparse,pickle,sys
from pathlib import Path
import mujoco,numpy as np
from scipy.spatial.transform import Rotation,Slerp
from registered_mission_actor import RegisteredMissionActor
from pose_tracking import RigidTrayTracker
from pose_policy import PoseTransportPolicy


class PoseMissionActor(RegisteredMissionActor):
    def __init__(self,model,policy_directory,initial_xy,shape):
        # The CAD-centered rim grasp requires a closer stance than the old
        # front-biased palm pinch. Fixed-base IK rejects the previous stance.
        super().__init__(model,policy_directory,initial_xy,goal_xy=(.04,0.),parking_envelope=(-.02,.18,.10));self.shape=shape
        self.walker.minimum_stop_dwell_s=.8;self.walker.parking_speed_limit=.08
        self.canonical_hand_curl=1.05
    def activate_carrier(self,obs):
        super().activate_carrier(obs)
        self.tracker.close();self.tracker=RigidTrayTracker(self.m,self.data,self.shape)
        upright=Rotation.from_euler('y',-60,degrees=True).as_matrix()
        interpolators={s:Slerp([0.,1.,2.],Rotation.from_matrix(np.stack([self.data.site(s+'_wrist_reference').xmat.reshape(3,3).copy(),upright@self.balance.palm_rotations[s],self.balance.palm_rotations[s]]))) for s in ['left','right']}
        fingers={}
        for i,j in enumerate(self.m.actuator_trnid[:,0]):
            name=self.m.joint(j).name
            if any(n in name for n in ['index','middle','ring','little']):fingers[i]='finger'
            elif 'thumb_1' in name:fingers[i]='opposition'
            elif 'thumb_2' in name:fingers[i]='thumb'
        def hands(curl,rotation):
            self.balance.palm_rotations={s:interp(rotation).as_matrix() for s,interp in interpolators.items()}
            for i,kind in fingers.items():self.balance.posture[i]=curl if kind=='finger' else min(.6,curl*1.3) if kind=='opposition' else min(.3,curl*.67)
        shape=np.load(self.shape);triangles=shape['vertices'][shape['faces']]
        # Same explicitly inferred 304-steel density as the catalog asset;
        # geometry is public. No plant body mass or contact force is read.
        volume=abs(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6.)
        hands(1.05,0.)
        self.carrier=PoseTransportPolicy({s:self.data.site(s+'_wrist_reference').xpos.copy() for s in ['left','right']},hands,carried_mass=volume*8000.)
    def update(self,obs):
        response=super().update(obs)
        if isinstance(self.tracker,RigidTrayTracker):response['pose_tracking_counts']=dict(accepted=self.tracker.accepted,rejected=self.tracker.rejected)
        return response


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--policy',default='/model/policy');p.add_argument('--initial-xy',type=float,nargs=2,default=[-.9,0.]);a=p.parse_args()
    model=mujoco.MjModel.from_xml_path(a.model);actor=PoseMissionActor(model,a.policy,a.initial_xy,Path(a.model).parent/'known_objects/tray_geometry.npz')
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
