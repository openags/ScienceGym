"""Contact-only manipulation with replaceable thin-edge jaws."""
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from control import Robot,ExecutionFailure,DOWN
from continuous_world import PARTS
from contact_safety import audit
from support_observation import support_load,designated_surfaces


class ContinuousRobot(Robot):
    def __init__(self,path,record=False,seed=0,video_path=None):
        self.video_path=video_path;self.video_writer=None
        self.grip_target=.04;self.clamp_force=None
        super().__init__(path,record=record,seed=seed)

    def advance(self,duration):
        for _ in range(max(1,int(duration/self.model.opt.timestep))):
            self.data.ctrl[:7]=self.joint_target+self.data.qfrc_bias[:7]/self.kp
            requested=-self.clamp_force if self.clamp_force is not None else (
                2000*(self.grip_target-np.mean(self.data.qpos[7:9]))-40*np.mean(self.data.qvel[7:9]))
            self.data.ctrl[7]=np.clip(requested,-40,40)
            mujoco.mj_step(self.model,self.data);self.physics_steps+=1
            if not np.all(np.isfinite(self.data.qpos)):raise ExecutionFailure('nonfinite physics')
            if self.physics_steps%10==0:
                self.audit_contacts()
                self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
            if self.record and self.data.time-self.last_frame>=.1-1e-8:self.capture()

    def finger(self,opening):
        self.clamp_force=None;self.grip_target=np.clip(opening/2,0,.04);self.advance(.4)

    def capture(self):
        super().capture()
        if self.video_path:
            if self.video_writer is None:
                import imageio.v2 as imageio
                self.video_writer=imageio.get_writer(self.video_path,fps=10,codec='libx264',quality=7)
            self.video_writer.append_data(self.frames[-1])
            # Long episodes stream frames, rather than accumulating gigabytes.
            self.frames[:]=self.frames[-1:]

    def close(self):
        if self.video_writer is not None:
            self.video_writer.close();self.video_writer=None
        super().close()

    def ik(self,xyz,rotation=DOWN):
        # The 0.5 mm stopping tolerance of the coarse fixture controller is
        # as large as the whole emitter thickness. Use 10 micrometre kinematic
        # convergence here and still verify the actual actuated contact.
        k=self.kin;m=self.model;k.qpos[:]=self.data.qpos
        jp=np.zeros((3,m.nv));jr=np.zeros((3,m.nv))
        for _ in range(300):
            mujoco.mj_kinematics(m,k);mujoco.mj_comPos(m,k)
            error=np.r_[np.asarray(xyz)-k.site_xpos[self.site],
                        Rotation.from_matrix(rotation@k.site_xmat[self.site].reshape(3,3).T).as_rotvec()*.4]
            if np.linalg.norm(error)<.00001:return k.qpos[:7].copy()
            mujoco.mj_jacSite(m,k,jp,jr,self.site)
            j=np.vstack([jp[:,:7],jr[:,:7]*.4])
            dq=j.T@np.linalg.solve(j@j.T+np.eye(6)*.00002,error)
            k.qpos[:7]=np.clip(k.qpos[:7]+np.clip(dq,-.1,.1),m.jnt_range[:7,0]+.005,m.jnt_range[:7,1]-.005)
        if np.linalg.norm(error)<.001:return k.qpos[:7].copy()
        raise ExecutionFailure('Precision IK unreachable: '+str(np.asarray(xyz).tolist()))

    def audit_contacts(self):
        audit(self)

    def pick(self,body):
        initial=self.position(body);self.active_object=body
        rim_offset=np.zeros(3)
        if body=='emitter' and any(c['other']=='foam_upper' and c['force_n']>.005 for c in self.contacts(body)):
            # On the stack, the lower edge of the 3 mm pad must stay above the
            # foam. Reusing the stand grasp also pinched and carried the foam.
            rim_offset[2]=.00145
        def observed_grasp():
            return self.grasp_site(body)+self.data.body(body).xmat.reshape(3,3)@rim_offset
        grasp=observed_grasp()
        objrot=self.data.body(body).xmat.reshape(3,3).copy()
        rotation=objrot@DOWN
        self.finger(min(.08,PARTS[body]['width']+.008))
        self.move(grasp+[0,0,.16],rotation)
        self.move(grasp,rotation,duration=1.8)
        # Reobserve the thin edge after settling; use position feedback before
        # closing, rather than assuming the commanded pose was reached.
        for _ in range(2):
            err=observed_grasp()-self.data.site_xpos[self.site]
            if np.linalg.norm(err)<.00005:break
            self.move(observed_grasp(),rotation,duration=.4)
        opening=.038 if body=='emitter' else .035 if body=='aperture' else 0 if body=='shield' else max(0,PARTS[body]['width']-.004)
        if body=='emitter':
            # Ramp closure on the 0.5 mm edge to avoid launching it from its
            # stand with an instantaneous high-force gripper command.
            for gap in np.linspace(.058,opening,12):
                self.grip_target=gap/2;self.advance(.1)
        self.finger(opening)
        contact=self.contacts(body)
        fingers={c['other'] for c in contact if c['force_n']>.03}
        if not {'left_finger','right_finger'}<=fingers:
            raise ExecutionFailure('bilateral edge contact missing: '+body+' '+str(contact))
        if body=='emitter' and sum(self.data.qpos[7:9])<.048:
            raise ExecutionFailure('Emitter sits on jaw tips instead of being pinched at its edge')
        self.clamp_force={'foam_lower':.8,'foam_upper':.8,'emitter':12.,'pe_tube':14.,'shield':24.,'aperture':18.}[body]
        self.advance(.25)
        for other in PARTS:
            if other==body:continue
            if any(c['other'] in ['left_finger','right_finger'] and c['force_n']>.05 for c in self.contacts(other)):
                raise ExecutionFailure('Gripper also contacts unintended payload: '+other)
        self.move(self.data.site_xpos[self.site]+[0,0,.17],rotation,duration=2)
        lifted=float(self.position(body)[2]-initial[2])
        if lifted<.10:raise ExecutionFailure(f'{body} edge lift failed {lifted:.5f}; actual={self.position(body).tolist()},contacts={self.contacts(body)}')
        self.checkpoint('edge_lift_observed',body=body,lift_m=lifted,contacts=contact,
                        orientation=self.data.body(body).xmat.reshape(3,3).tolist(),
                        lifted_contacts=self.contacts(body))
        self.carry_rotation=self.data.site_xmat[self.site].reshape(3,3).copy()

    def place(self,body,target,support,tolerance=.003):
        target=np.asarray(target)
        def held():
            ob=self.data.body(body).xmat.reshape(3,3).copy()
            hand=self.data.site_xmat[self.site].reshape(3,3).copy()
            contact=self.contacts(body)
            if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.01}:
                raise ExecutionFailure('grasp lost during placement: '+body)
            if body in ['emitter','aperture']:
                return self.data.site_xpos[self.site]-self.position(body),self.carry_rotation
            return ob.T@(self.data.site_xpos[self.site]-self.position(body)),ob.T@hand
        offset,rotation=held()
        # Keep height during lateral transport. A diagonal descent carrying a
        # thin eccentric plate can lose contact before its final pose check.
        # Reobserve the payload at each segment, instead of chasing it after
        # one long blind move.
        start=self.position(body)
        travel_z=max(start[2],target[2]+.17)
        if travel_z-start[2]>.001:
            self.move(np.r_[start[:2],travel_z]+offset,rotation,duration=1.5)
        delicate=body in ['emitter','aperture']
        segments=max(10,int(np.ceil(np.linalg.norm(target[:2]-start[:2])/.025))) if delicate else 10
        for u in np.linspace(0,1,segments+1)[1:]:
            offset,rotation=held()
            center=np.r_[start[:2]+(target[:2]-start[:2])*u,travel_z]
            self.move(center+offset,rotation,duration=.8 if delicate else .35)
        offset,rotation=held()
        self.move(target+offset+[0,0,.15],rotation,duration=1.5)
        for height in np.linspace(.13,.0015,23):
            offset,rotation=held()
            self.move(target+offset+[0,0,height],rotation,duration=.16)
        # Open only enough to clear this wall. A full 80 mm opening puts the
        # inner jaw through the next concentric tube and displaces the stack.
        self.finger(min(.08,PARTS[body]['width']+.008))
        self.move(self.data.site_xpos[self.site]+[0,0,.18],rotation)
        self.advance(.6)
        self.check_supported(body,target,support,tolerance)

    def check_supported(self,body,target,support,tolerance=.003):
        error=float(np.linalg.norm(self.position(body)-target))
        # Circular layers have no keyed yaw datum. Only their surface normal
        # determines seating; treating yaw as tilt rejects correct placements.
        angle=float(np.arccos(np.clip(self.data.body(body).xmat.reshape(3,3)[2,2],-1,1)))
        contacts=self.contacts(body)
        load=support_load(self.model,self.data,body,support,designated_surfaces(body,support))
        force=load['vertical_force_n'];weight=load['body_weight_n']
        speed=float(np.linalg.norm(self.data.body(body).cvel))
        enough_surfaces=body!='shield' or support!='assembly_base' or len(load['loaded_support_geoms'])>=3
        if error>tolerance or force<weight*.8 or speed>.03 or angle>.035 or not enough_surfaces:
            raise ExecutionFailure(f'{body} support invalid: error={error:.5f},angle={angle:.5f},force={force:.4f},speed={speed:.5f},support={support}')
        return self.checkpoint('support_observed',body=body,actual=self.position(body).tolist(),target=list(target),error_m=error,tilt_rad=angle,support=support,support_force_n=force,load=load)
