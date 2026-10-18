"""Integrated controller with an observed load-transfer check before release."""
import numpy as np
import mujoco
import json
from world import HERE
from integrated_control import IntegratedRobot
from evaluate_cover import measure
from control import ExecutionFailure

class SelectedAssemblyRobot(IntegratedRobot):
    def __init__(self,*args,**kwargs):
        profile=json.loads((HERE.parents[1]/'tasks/directional_cooling_operations_v3/selected_reconstruction.json').read_text())
        self.shield_clamp_force=float(profile['cards']['manipulation_card']['force_torque_clearance_limits']['value']['shield_grip_N'])
        self.next_progress_time=20.
        super().__init__(*args,**kwargs)

    def advance(self,duration):
        if getattr(self,'active_object',None)=='shield' and self.clamp_force==24.:
            self.clamp_force=self.shield_clamp_force
        result=super().advance(duration)
        if self.data.time>=self.next_progress_time:
            print('PHYSICS',round(self.data.time,2),'s; active object',self.active_object,flush=True)
            self.next_progress_time=self.data.time+20.
        return result

    def grip_cover(self):
        self.active_object='cover'
        return super().grip_cover()

    def audit_contacts(self):
        super().audit_contacts()
        loads={}
        payloads={'foam_lower','foam_upper','emitter','pe_tube','cover','shield','aperture'}
        for i,c in enumerate(self.data.contact):
            names=[self.contact_body(c,j) for j in range(2)]
            if not {'left_finger','right_finger'}&set(names):continue
            for body in set(names)&payloads:
                if body==self.active_object:continue
                f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
                loads[body]=loads.get(body,0.)+max(0,float(f[0]))
        for body,force in loads.items():
            if force>.05:raise ExecutionFailure(f'Fingers loaded unintended payload {body}: {force:.5f} N while handling {self.active_object}')

    def checkpoint(self,label,**values):
        print(label,round(self.data.time,3),flush=True)
        return super().checkpoint(label,**values)

    def put_cover(self,target):
        target=np.asarray(target)
        support='pe_tube' if np.linalg.norm(target[:2]-[.48,.12])<.01 else 'cover_stand'
        def held():
            contact=self.contacts('cover')
            if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.02}:
                raise ExecutionFailure('Cover annulus grip lost')
            body=self.data.body('cover').xmat.reshape(3,3)
            return body.T@(self.data.site_xpos[self.site]-self.position('cover')),body.T@self.data.site_xmat[self.site].reshape(3,3)
        start=self.position('cover')
        for u in np.linspace(0,1,11)[1:]:
            offset,rotation=held();p=np.r_[start[:2]+u*(target[:2]-start[:2]),max(start[2],target[2]+.13)]
            self.move(p+offset,rotation,duration=.5)
        for height in np.r_[np.linspace(.10,.006,20),np.arange(.0055,.0001,-.00025)]:
            offset,rotation=held();self.move(target+offset+[0,0,height],rotation,duration=.2)
        # The gripper is the selected annular retention jig. Keep both pads
        # loaded while transferring part of the cover load to its support.
        # This does not assert full support until the subsequent open-hand
        # observation. No attachment equality is introduced.
        precheck=None
        for extra in np.arange(0,.00201,.0002):
            if extra:
                offset,rotation=held();self.move(target+offset+[0,0,.00025-extra],rotation,duration=.25)
            observation=measure(self.model,self.data,target,support)
            if observation['max_edge_strain']>.01:raise ExecutionFailure('Membrane overstretched during retained load transfer')
            if observation['vertical_support_force_n']>.5*observation['weight_n']:
                precheck=observation;break
        if precheck is None:raise ExecutionFailure('Cover never transferred load to its support while retained')
        self.checkpoint('cover_retained_load_transfer',support=support,retention_tool='PANDA_EDGE_JAWS_ANNULAR_CLAMP',observation=precheck)
        self.finger(.020)
        # The park is already at the front of the reachable workspace.
        # Its open stand needs only 60 mm of lateral clearance; reusing the
        # assembly's 130 mm retreat drove the wrist beyond its IK limits.
        retreat=.060 if support=='cover_stand' else .13
        self.move(self.data.site_xpos[self.site]+[0,-retreat,0],rotation,duration=1.5)
        self.move(self.data.site_xpos[self.site]+[0,0,.10],rotation)
        self.advance(1)
        self.check_cover(target,support)
