"""The same actuated Panda and extended edge jaws handle every cooler layer."""
from continuous_control import ContinuousRobot
from cover_control import CoverRobot
from evaluate_cover import measure
from control import ExecutionFailure
from contextlib import contextmanager
import mujoco
import numpy as np
from load_model import load
from cover_world import SIDE


class IntegratedRobot(ContinuousRobot):
    contact_body=CoverRobot.contact_body
    audit_contacts=CoverRobot.audit_contacts
    put_cover=CoverRobot.put

    def __init__(self,path,**kwargs):
        self.observation_model=load(path)
        self.observation_model.opt.enableflags &= ~int(mujoco.mjtEnableBit.mjENBL_SLEEP)
        self.observation_data=mujoco.MjData(self.observation_model)
        self._observing=False;self.sleep_trace=[]
        super().__init__(path,**kwargs)

    def advance(self,duration):
        sample_steps=max(1,round(.005/self.model.opt.timestep))
        for _ in range(max(1,int(duration/self.model.opt.timestep))):
            self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
            requested=-self.clamp_force if self.clamp_force is not None else (
                2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9]))
            self.data.ctrl[7]=np.clip(requested,-40,40)
            mujoco.mj_step(self.model,self.data);self.physics_steps+=1
            iterations=int(np.max(self.data.solver_niter))
            self.maximum_solver_iterations=max(getattr(self,'maximum_solver_iterations',0),iterations)
            if iterations>=self.model.opt.iterations:
                self.solver_limit_steps=getattr(self,'solver_limit_steps',0)+1
                raise ExecutionFailure('Constraint solver reached its iteration limit')
            if any(w.number for w in self.data.warning):
                raise ExecutionFailure('MuJoCo numerical warning: '+str([int(w.number) for w in self.data.warning]))
            if not np.all(np.isfinite(self.data.qpos)):raise ExecutionFailure('nonfinite physics')
            if self.physics_steps%sample_steps==0:
                self.audit_contacts()
                self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
                self.sleep_trace.append(self.data.tree_asleep.copy())
            if self.record and self.data.time-self.last_frame>=.1-1e-8:self.capture()

    @contextmanager
    def observed(self):
        if self._observing:
            yield
            return
        model,data=self.model,self.data
        observation=self.observation_data
        observation.qpos[:]=data.qpos;observation.qvel[:]=data.qvel
        observation.ctrl[:]=data.ctrl;observation.time=data.time
        # This independent observer never steps or changes the live state.
        # It recomputes contacts omitted by the sleeping execution islands.
        mujoco.mj_forward(self.observation_model,observation)
        self.model,self.data=self.observation_model,observation;self._observing=True
        try:yield
        finally:self.model,self.data=model,data;self._observing=False

    def contacts(self,body):
        with self.observed():return CoverRobot.contacts(self,body)

    def grip_cover(self):
        self.finger(.020);p=self.grasp_site('cover')
        # The longer common edge jaws need a shorter lateral approach than
        # the stock-finger cover fixture to remain inside Panda's workspace.
        self.move(p+[0,-.08,.08],SIDE,duration=2)
        self.move(p+[0,-.06,0],SIDE,duration=1.5)
        self.move(p,SIDE,duration=2);self.finger(0)
        contact=self.contacts('cover')
        if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.05}:
            raise ExecutionFailure('Cover annulus not bilaterally held')
        initial=self.position('cover')
        self.move(self.data.site_xpos[self.site]+[0,0,.12],SIDE,duration=2)
        if self.position('cover')[2]-initial[2]<.09:raise ExecutionFailure('Cover failed lift')
        self.checkpoint('cover_lifted',contacts=contact,position=self.position('cover').tolist())

    def check_supported(self,*args,**kwargs):
        with self.observed():return super().check_supported(*args,**kwargs)

    def pick(self,body):
        super().pick(body)
        if any(c['other'] in ['left_finger','right_finger'] and c['force_n']>.05 for c in self.contacts('cover')):
            raise ExecutionFailure('Gripper also contacts unintended cover')

    def check_cover(self,target,support):
        with self.observed():result=measure(self.model,self.data,target,support)
        self.checkpoint('cover_support_observed',support=support,observation=result)
        if not result['passed']:raise ExecutionFailure('Cover support invalid: '+str(result))
        return result
