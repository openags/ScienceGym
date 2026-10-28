"""Joint-actuated contact execution. No live object pose writes or grasp welds."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import mujoco
from world import HOME
from load_model import load

DOWN=np.diag([1.,-1.,-1.])


class ExecutionFailure(RuntimeError):
    pass


class Robot:
    def __init__(self, path, record=False, seed=0):
        self.model=load(path)
        self.data=mujoco.MjData(self.model)
        self.kin=mujoco.MjData(self.model)
        self.data.qpos[:7]=HOME
        if seed:self.data.qpos[:7]+=np.random.default_rng(seed).uniform(-.012,.012,7)
        self.data.qpos[7:9]=.04
        self.data.ctrl[:7]=HOME
        self.joint_target=HOME.copy()
        self.kp=np.array([4500,4500,3500,3500,2000,2000,2000])
        self.data.ctrl[7]=255
        self.model.opt.gravity[:]=[0,0,-9.81]
        mujoco.mj_forward(self.model,self.data)
        self.record=record
        self.frames=[];self.states=[];self.timeline=[]
        self.trace=[]
        self.last_frame=-1
        self.renderer=None
        self.site=self.model.site('tcp').id
        self.left=self.model.body('left_finger').id
        self.right=self.model.body('right_finger').id
        self.max_robot_contact_force=0.
        self.arm_contacts=[]
        self.minimum_clearance=0.
        self.active_object=None
        self.peak_unintended_force=0.
        self.physics_steps=0
        self.advance(.6)

    def advance(self, duration):
        for _ in range(max(1,int(duration/self.model.opt.timestep))):
            # Gravity compensation through the same limited arm actuators.
            self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
            mujoco.mj_step(self.model,self.data)
            self.physics_steps+=1
            if not np.all(np.isfinite(self.data.qpos)):
                raise ExecutionFailure('nonfinite_physics')
            if self.physics_steps%10==0:
                self.audit_contacts()
                self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
            if self.record and self.data.time-self.last_frame>=.1-1e-8:
                self.capture()

    def audit_contacts(self):
        for i,c in enumerate(self.data.contact):
            a=self.model.body(int(self.model.geom_bodyid[c.geom1])).name
            b=self.model.body(int(self.model.geom_bodyid[c.geom2])).name
            arm={'link1','link2','link3','link4','link5','link6','link7','hand'}
            if (a in arm) == (b in arm):continue
            other=b if a in arm else a
            if other in {'link0','left_finger','right_finger'}:continue
            f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            self.peak_unintended_force=max(self.peak_unintended_force,float(f[0]))
            if f[0]>2 and c.dist<-.0005:
                raise ExecutionFailure(f'unintended arm contact {a}/{b}: {f[0]:.3f} N, {c.dist:.5f} m')

    def capture(self):
        if self.renderer is None:
            self.renderer=mujoco.Renderer(self.model,height=720,width=1120)
        camera=mujoco.MjvCamera()
        camera.lookat[:]=[.4,0,.97];camera.distance=1.85;camera.azimuth=135;camera.elevation=-30
        self.renderer.update_scene(self.data,camera)
        self.frames.append(self.renderer.render().copy())
        self.states.append(dict(t=float(self.data.time),qpos=self.data.qpos.tolist(),qvel=self.data.qvel.tolist(),ctrl=self.data.ctrl.tolist()))
        self.last_frame=float(self.data.time)

    def position(self, body):
        return self.data.body(body).xpos.copy()

    def grasp_site(self, body):
        return self.data.site(body+'_grasp').xpos.copy()

    def ik(self, xyz, rotation=DOWN):
        k=self.kin;m=self.model
        k.qpos[:]=self.data.qpos
        jp=np.zeros((3,m.nv));jr=np.zeros((3,m.nv))
        for iteration in range(220):
            mujoco.mj_kinematics(m,k);mujoco.mj_comPos(m,k)
            p=k.site_xpos[self.site];r=k.site_xmat[self.site].reshape(3,3)
            error=np.r_[np.array(xyz)-p,Rotation.from_matrix(rotation@r.T).as_rotvec()*.4]
            if np.linalg.norm(error)<.0005:return k.qpos[:7].copy()
            mujoco.mj_jacSite(m,k,jp,jr,self.site)
            j=np.vstack([jp[:,:7],jr[:,:7]*.4])
            dq=j.T@np.linalg.solve(j@j.T+np.eye(6)*.00008,error)
            k.qpos[:7]+=np.clip(dq,-.12,.12)
            k.qpos[:7]=np.clip(k.qpos[:7],m.jnt_range[:7,0]+.005,m.jnt_range[:7,1]-.005)
        if np.linalg.norm(error)<.003:return k.qpos[:7].copy()
        raise ExecutionFailure(f'IK unreachable {np.asarray(xyz).round(4).tolist()}; residual {np.linalg.norm(error):.5f}')

    def move(self, target, rotation=DOWN, duration=1.2):
        start=self.data.site_xpos[self.site].copy()
        r0=self.data.site_xmat[self.site].reshape(3,3).copy()
        delta=Rotation.from_matrix(rotation@r0.T).as_rotvec()
        steps=max(12,int(duration/.04))
        for i in range(1,steps+1):
            u=i/steps;u=u*u*(3-2*u)
            r=Rotation.from_rotvec(delta*u).as_matrix()@r0
            self.joint_target=self.ik(start+(np.asarray(target)-start)*u,r)
            self.advance(duration/steps)
        self.advance(.18)
        residual=float(np.linalg.norm(self.data.site_xpos[self.site]-target))
        if residual>.025:raise ExecutionFailure(f'tracking residual {residual:.4f} m at {target}')

    def finger(self, opening):
        self.data.ctrl[7]=np.clip(opening/.08*255,0,255)
        self.advance(.4)

    def contacts(self, body):
        bid=self.model.body(body).id
        observations=[]
        for i,c in enumerate(self.data.contact):
            b1,b2=int(self.model.geom_bodyid[c.geom1]),int(self.model.geom_bodyid[c.geom2])
            if bid not in (b1,b2):continue
            f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            observations.append(dict(other=self.model.body(b2 if b1==bid else b1).name,force_n=float(f[0]),distance_m=float(c.dist)))
        return observations

    def checkpoint(self, label, **values):
        item=dict(label=label,time_s=float(self.data.time),**values)
        self.timeline.append(item)
        return item

    def pick(self, body):
        self.active_object=body
        initial=self.position(body);grasp=self.grasp_site(body)
        self.finger(.08)
        self.move(grasp+[0,0,.16])
        self.move(grasp,duration=1.4)
        self.finger(.046 if body.startswith('foam_') else 0)
        contact=self.contacts(body)
        fingers={c['other'] for c in contact if c['force_n']>.05}
        if not {'left_finger','right_finger'}<=fingers:
            raise ExecutionFailure('bilateral grasp contact missing: '+body+' '+str(contact))
        self.move(grasp+[0,0,.14],duration=1.5)
        lifted=float(self.position(body)[2]-initial[2])
        if lifted<.09:raise ExecutionFailure(f'{body} failed lift: {lifted:.4f}')
        return self.checkpoint('lift_observed',body=body,lift_m=lifted,contacts=contact)

    def place(self, body, target, support, tolerance=.015):
        # Observe the actual object-to-hand transform after lifting. Assuming
        # a perfect nominal grasp caused angled probes to jam at the bore.
        objrot=self.data.body(body).xmat.reshape(3,3).copy()
        handrot=self.data.site_xmat[self.site].reshape(3,3).copy()
        offset=objrot.T@(self.data.site_xpos[self.site]-self.position(body))
        rotation=objrot.T@handrot
        tcp=np.array(target)+offset
        self.move(tcp+[0,0,.16],rotation)
        if body in ['probe','foam_lower','foam_upper','emitter']:
            for height in np.linspace(.12,.002,25):
                # Reobserve the grasp throughout the insertion, including
                # small slip/rotation instead of assuming a rigid grasp weld.
                objrot=self.data.body(body).xmat.reshape(3,3).copy()
                handrot=self.data.site_xmat[self.site].reshape(3,3).copy()
                offset=objrot.T@(self.data.site_xpos[self.site]-self.position(body))
                rotation=objrot.T@handrot
                tcp=np.array(target)+offset
                self.move(tcp+[0,0,height],rotation,duration=.12)
        else:
            self.move(tcp+[0,0,.002],rotation,duration=2.)
        self.finger(.08)
        self.move(tcp+[0,0,.17],rotation)
        self.advance(.6)
        actual=self.position(body);err=float(np.linalg.norm(actual-target))
        contacts=self.contacts(body)
        # Sum a support's contact manifold: a decomposed circular stand can
        # distribute the same load over hundreds of small contact forces.
        support_force=sum(c['force_n'] for c in contacts if c['other']==support)
        weight=float(self.model.body(body).mass[0])*9.81
        supported=support_force>weight*.5 and np.linalg.norm(self.data.body(body).cvel)<.03
        if err>tolerance or not supported:
            raise ExecutionFailure(f'{body} placement failed: error={err:.5f}, support={supported}, contacts={contacts}')
        return self.checkpoint('placement_observed',body=body,target=list(target),actual=actual.tolist(),error_m=err,support=support,support_force_n=support_force,contacts=contacts)

    def transfer(self,body,target,support,tolerance=.015):
        self.pick(body)
        self.place(body,target,support,tolerance)

    def access_door(self, angle):
        self.active_object='access_lid'
        joint=self.data.joint('access_hinge')
        current=float(joint.qpos[0])
        hinge=self.position('access_lid')
        grasp=self.grasp_site('access_lid')
        initial_rotation=Rotation.from_euler('x',current).as_matrix()@DOWN
        self.finger(.08)
        self.move(grasp+[0,0,.17],initial_rotation)
        self.move(grasp,initial_rotation)
        self.finger(.016)
        for theta in np.linspace(current,angle,35)[1:]:
            observed=self.data.body('access_lid').xmat.reshape(3,3).copy()
            tcp_local=observed.T@(self.data.site_xpos[self.site]-hinge)
            hand_local=observed.T@self.data.site_xmat[self.site].reshape(3,3)
            rot=Rotation.from_euler('x',theta).as_matrix()
            self.move(hinge+rot@tcp_local,rot@hand_local,duration=.12)
        self.finger(.08)
        self.move(self.grasp_site('access_lid')+[0,0,.18],initial_rotation)
        self.advance(.5)
        actual=float(joint.qpos[0])
        if abs(actual-angle)>.08:raise ExecutionFailure(f'door angle {actual:.4f} differs from {angle:.4f}')
        self.checkpoint('hinge_observed',joint='access_hinge',target_rad=float(angle),actual_rad=actual)

    def press(self):
        self.active_object='acquisition_button'
        p=self.position('acquisition_button')
        self.finger(0)
        # The closed fingers are the declared button tool, not a hidden actuator.
        self.move(p+[0,0,.12])
        self.move(p+[0,0,.008],duration=1.5)
        self.advance(.2)
        travel=float(self.data.joint('button_travel').qpos[0])
        contacts=self.contacts('acquisition_button')
        if travel<.003 or not any(c['other'] in ['left_finger','right_finger'] for c in contacts):
            raise ExecutionFailure(f'button not physically actuated: {travel}, {contacts}')
        self.checkpoint('button_observed',travel_m=travel,contacts=contacts)
        self.move(p+[0,0,.14])

    def close(self):
        if self.renderer:self.renderer.close()
