"""Actuated controller for workcells with model-specific device assets.

The initialization is kept separate from the frozen layer fixture so new
device namespaces do not change the source hashes of earlier physical runs.
"""
import numpy as np
import mujoco
from world import HOME
from continuous_control import ContinuousRobot
from control import ExecutionFailure,DOWN
from device_assets import load


class HardwareRobot(ContinuousRobot):
    def audit_contacts(self):
        super().audit_contacts()
        for i,c in enumerate(self.data.contact):
            if min(c.geom)<0:continue
            names=[self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom]
            if 'button_probe' not in names:continue
            other=names[1-names.index('button_probe')]
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            if other not in {self.active_object,'hand'} and force[0]>.5:
                raise ExecutionFailure('Pusher contacted unintended body: '+other+' '+str(float(force[0])))

    def __init__(self,path,record=False,seed=0,video_path=None):
        self.model=load(path);self.data=mujoco.MjData(self.model);self.kin=mujoco.MjData(self.model)
        self.data.qpos[:7]=HOME
        if seed:self.data.qpos[:7]+=np.random.default_rng(seed).uniform(-.012,.012,7)
        self.data.qpos[7:9]=.04;self.data.ctrl[:7]=HOME;self.joint_target=HOME.copy()
        self.kp=np.array([4500,4500,3500,3500,2000,2000,2000])
        self.model.opt.gravity[:]=[0,0,-9.81];mujoco.mj_forward(self.model,self.data)
        self.record=record;self.frames=[];self.states=[];self.timeline=[];self.trace=[]
        self.last_frame=-1;self.renderer=None;self.site=self.model.site('tcp').id
        self.left=self.model.body('left_finger').id;self.right=self.model.body('right_finger').id
        self.max_robot_contact_force=0.;self.arm_contacts=[];self.minimum_clearance=0.
        self.active_object=None;self.peak_unintended_force=0.;self.physics_steps=0
        self.video_path=video_path;self.video_writer=None;self.grip_target=.04;self.clamp_force=None
        self.advance(.6)

    def checkpoint(self,label,**values):
        print(label,round(self.data.time,3),flush=True)
        return super().checkpoint(label,**values)

    def grasp(self,name,width,force,rotation=DOWN,lift=.10):
        self.active_object=name;self.finger(min(.08,width+.008))
        p=self.grasp_site(name);self.move(p+[0,0,.14],rotation,duration=1.8)
        self.move(p,rotation,duration=1.5);self.finger(max(0,width-.004))
        self.clamp_force=force;self.advance(.2)
        contact=self.contacts(name)
        if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.03}:
            raise ExecutionFailure('Missing bilateral grip: '+name+' '+str(contact))
        before=self.position(name);self.move(self.data.site_xpos[self.site]+[0,0,lift],rotation,duration=2)
        if self.position(name)[2]-before[2]<lift*.8:raise ExecutionFailure('Payload failed lift: '+name)
        self.checkpoint('grasp_and_lift_observed',body=name,contact=contact,lift_m=float(self.position(name)[2]-before[2]))

    def press_button(self,name,axis,rotation,travel):
        self.active_object=name;axis=np.asarray(axis,float)
        tools={mujoco.mj_id2name(self.model,mujoco.mjtObj.mjOBJ_BODY,i) for i in range(self.model.nbody)}
        contact_tools={'button_probe'} if 'button_probe' in tools else {'left_finger','right_finger'}
        self.finger(.08 if 'button_probe' in tools else 0)
        p=self.position(name);approach=p-axis*.10
        self.move(approach+[0,0,.10],rotation,duration=2)
        self.move(approach,rotation,duration=1.5)
        self.move(p-axis*.012,rotation,duration=1.5)
        # The TCP is at the finger-tip face; advance in bounded increments
        # and stop on observed button travel, not a fictitious UI command.
        joint=self.data.joint(name+'_travel');maximum=0.
        for distance in np.linspace(-.010,travel+.004,32):
            self.move(p+axis*distance,rotation,duration=.10)
            maximum=max(maximum,float(joint.qpos[0]))
            if maximum>.75*travel:break
        contact=self.contacts(name)
        if maximum<.75*travel or not any(c['other'] in contact_tools and c['force_n']>.01 for c in contact):
            raise ExecutionFailure('Button not physically actuated: '+name+' '+str(maximum))
        self.checkpoint('physical_button_press',body=name,travel_m=maximum,contacts=contact)
        self.move(approach,rotation);self.move(approach+[0,0,.10],rotation)
        return maximum
