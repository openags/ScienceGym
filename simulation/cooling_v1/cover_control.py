"""Side approach keeps gripper pads on the film-bonded rigid outer annulus."""
import numpy as np
import mujoco
from control import Robot,ExecutionFailure
from cover_world import SIDE
from contact_safety import audit
from precision_ik import solve


class CoverRobot(Robot):
    ik=solve
    def checkpoint(self,label,**values):
        print(label,round(self.data.time,3),flush=True)
        return super().checkpoint(label,**values)

    def contact_body(self,c,side):
        geom=int(c.geom[side])
        if geom>=0:return self.model.body(int(self.model.geom_bodyid[geom])).name
        flex=int(c.flex[side])
        name=mujoco.mj_id2name(self.model,mujoco.mjtObj.mjOBJ_FLEX,flex) if flex>=0 else ''
        return 'cover' if name and name.startswith('cover_') else 'unknown_flex'

    def audit_contacts(self):
        audit(self,self.contact_body)
        for i,c in enumerate(self.data.contact):
            a,b=[self.contact_body(c,j) for j in range(2)]
            if 'cover' in [a,b] and {'left_finger','right_finger'}&{a,b} and max(c.flex)>=0:
                f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
                local=self.data.body('cover').xmat.reshape(3,3).T@(c.pos-self.position('cover'))
                if np.linalg.norm(local[:2])<.0535 and f[0]>.02:
                    raise ExecutionFailure('Gripper contacted the unsupported optical membrane')

    def contacts(self,body):
        records=[]
        for i,c in enumerate(self.data.contact):
            a,b=[self.contact_body(c,j) for j in range(2)]
            if body not in [a,b]:continue
            f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            records.append(dict(other=b if a==body else a,force_n=float(f[0]),distance_m=float(c.dist),
                                deformable=bool(max(c.flex)>=0),point_m=c.pos.tolist()))
        return records

    def grip(self):
        self.finger(.020)
        p=self.grasp_site('cover')
        self.move(p+[0,-.13,.10],SIDE,duration=2)
        self.move(p+[0,-.10,0],SIDE,duration=1.5)
        self.move(p,SIDE,duration=2)
        self.finger(0)
        contacts=self.contacts('cover')
        if not {'left_finger','right_finger'}<={c['other'] for c in contacts if c['force_n']>.05}:
            raise ExecutionFailure('Cover annulus not bilaterally held')
        initial=self.position('cover')
        self.move(self.data.site_xpos[self.site]+[0,0,.12],SIDE,duration=2)
        if self.position('cover')[2]-initial[2]<.09:raise ExecutionFailure('Cover failed lift')
        self.checkpoint('cover_lifted',contacts=contacts,position=self.position('cover').tolist())

    def put(self,target):
        def held():
            contact=self.contacts('cover')
            if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.02}:
                raise ExecutionFailure('Cover grasp lost during transport')
            body=self.data.body('cover').xmat.reshape(3,3)
            return (body.T@(self.data.site_xpos[self.site]-self.position('cover')),
                    body.T@self.data.site_xmat[self.site].reshape(3,3))
        start=self.position('cover')
        for u in np.linspace(0,1,11)[1:]:
            offset,rotation=held()
            center=np.r_[start[:2]+(target[:2]-start[:2])*u,max(start[2],target[2]+.13)]
            self.move(center+offset,rotation,duration=.5)
        for height in np.r_[np.linspace(.10,.006,20),np.arange(.0055,.0001,-.00025)]:
            offset,rotation=held()
            self.move(target+offset+[0,0,height],rotation,duration=.2)
        self.checkpoint('cover_before_release',position=self.position('cover').tolist(),contacts=self.contacts('cover'))
        self.finger(.020)
        self.move(self.data.site_xpos[self.site]+[0,-.13,0],rotation,duration=1.5)
        self.move(self.data.site_xpos[self.site]+[0,0,.10],rotation)
        self.advance(1.0)
        self.checkpoint('cover_released',position=self.position('cover').tolist(),contacts=self.contacts('cover'))
