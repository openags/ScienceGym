"""Floating-base constrained motor controller with Inspire mimic dynamics.

This module consumes an internal robot-state estimate. The initial diagnostic
runner may use simulator proprioception; that does not qualify sensor isolation.
No contact wrench or base force is ever written into the simulator.
"""
import numpy as np
import mujoco
import osqp
from scipy import sparse
from scipy.spatial.transform import Rotation


class Balance:
    def __init__(self,m,d):
        self.m,self.d=m,d;self.qa=m.jnt_qposadr[m.actuator_trnid[:,0]];self.va=m.jnt_dofadr[m.actuator_trnid[:,0]]
        self.posture=d.qpos[self.qa].copy();self.feet=[m.site(s+'_sole').id for s in ['left','right']]
        self.foot_positions=[d.site_xpos[s].copy() for s in self.feet];self.foot_rotations=[d.site_xmat[s].reshape(3,3).copy() for s in self.feet]
        self.com_target=d.subtree_com[m.body('pelvis').id].copy();self.com_target[:2]=np.mean(self.foot_positions,axis=0)[:2]
        self.previous=None;self.max_iter=0;self.previous_comj=None
        self.eqj=[];self.eqdata=[]
        for i in range(m.neq):
            a,b=m.eq_obj1id[i],m.eq_obj2id[i];coef=m.eq_data[i,1]
            row=np.zeros(m.nv);row[m.jnt_dofadr[a]]=1;row[m.jnt_dofadr[b]]=-coef
            self.eqj.append(row);self.eqdata.append((m.jnt_qposadr[a],m.jnt_qposadr[b],coef,m.eq_data[i,0]))
        self.eqj=np.array(self.eqj)
        self.unactuated=np.array([i for i in range(m.nv) if i not in set(self.va)])

    def jacobian(self,point,body):
        jp,jr=np.zeros((3,self.m.nv)),np.zeros((3,self.m.nv));dp,dr=np.zeros_like(jp),np.zeros_like(jr)
        mujoco.mj_jac(self.m,self.d,jp,jr,point,body);mujoco.mj_jacDot(self.m,self.d,dp,dr,point,body)
        return np.vstack([jp,jr]),np.vstack([dp,dr])

    def torque(self,targets=None,posture=None,dt=.01,forces=None,supported_mass=0.,contact_forces=None,surface_forces=None,point_targets=None,posture_weights=None,support_feet=None):
        m,d=self.m,self.d;n=m.nv;k=len(self.eqj);total=n+12+k
        support=np.ones(2,dtype=bool) if support_feet is None else np.asarray(support_feet)
        if support.shape!=(2,) or support.dtype!=bool or not support.any():
            raise ValueError('At least one explicitly declared support foot is required')
        mass=np.zeros((n,n));mujoco.mj_fullM(m,d,mass);bias=d.qfrc_bias-d.qfrc_passive
        # Desired wrist forces on a contacted object imply opposite external
        # reactions on the robot. Include their full generalized load in the
        # floating-base QP so the feet and body support it as well as the arm.
        # These are model loads only; the plant receives motor torques.
        for side,force in (contact_forces or {}).items():
            site=m.site(side+'_wrist_reference').id;j,_=self.jacobian(d.site_xpos[site],int(m.site_bodyid[site]))
            bias+=j[:3].T@np.asarray(force)
        # A fingertip load also acts on the finger joints and creates a
        # wrist moment. Applying its model reaction at the wrist omits both.
        # Points here are robot-geometry predictions from encoder estimates,
        # not simulator contacts. The physical plant still receives only
        # bounded actuator torques from the inverse-dynamics solution.
        for load in (surface_forces or []):
            point=np.asarray(load['point'],dtype=float);force=np.asarray(load['force'],dtype=float)
            if point.shape!=(3,) or force.shape!=(3,) or not np.isfinite(np.r_[point,force]).all():
                raise ValueError('Invalid predicted surface load')
            body=m.body(load['body']).id;j,_=self.jacobian(point,body)
            bias+=j[:3].T@force
        # Public work-order mass prior, expressed as the reaction on the robot.
        # Include all DOFs in inverse dynamics so foot wrench allocation also
        # accounts for the held load. Only resulting motor torques are applied.
        if supported_mass:
            for side in ['left','right']:
                site=m.site(side+'_wrist_reference').id;j,_=self.jacobian(d.site_xpos[site],int(m.site_bodyid[site]))
                bias+=j[:3].T@np.array([0.,0.,supported_mass*9.81/2])
        js=[];acc=[]
        for i,site in enumerate(self.feet):
            j,dj=self.jacobian(d.site_xpos[site],int(m.site_bodyid[site]));js.append(j)
            error=np.r_[self.foot_positions[i]-d.site_xpos[site],Rotation.from_matrix(self.foot_rotations[i]@d.site_xmat[site].reshape(3,3).T).as_rotvec()]
            acc.append(180*error-27*j@d.qvel-dj@d.qvel)
        jf=np.vstack(js);dynamics=np.c_[mass,-jf.T,-self.eqj.T]
        def pad(j):return np.c_[j,np.zeros((len(j),12+k))]
        posture=self.posture if posture is None else posture
        posture_row=pad(np.eye(n)[self.va]);posture_rhs=45*(posture-d.qpos[self.qa])-13*d.qvel[self.va]
        if posture_weights is not None:
            weights=np.asarray(posture_weights,dtype=float)
            if weights.shape!=(m.nu,) or not np.isfinite(weights).all() or np.any(weights<=0):
                raise ValueError('Invalid joint-posture task weights')
            posture_row*=weights[:,None];posture_rhs*=weights
        rows=[posture_row];ys=[posture_rhs]
        # A swing foot is a Cartesian motion task, never a fictitious support
        # wrench. Its physical motion still comes exclusively from motors.
        for foot in np.flatnonzero(~support):
            rows.append(60*pad(js[foot]));ys.append(60*acc[foot])
        cj=np.zeros((3,n));mujoco.mj_jacSubtreeCom(m,d,cj,m.body('pelvis').id)
        cd=np.zeros(3) if self.previous_comj is None else (cj-self.previous_comj)@d.qvel/dt;self.previous_comj=cj.copy()
        rows.append(12*pad(cj));ys.append(12*(70*(self.com_target-d.subtree_com[m.body('pelvis').id])-18*cj@d.qvel-cd))
        pj,pdj=self.jacobian(d.body('pelvis').xpos,m.body('pelvis').id)
        upright=Rotation.from_matrix(getattr(self,'pelvis_rotation',np.eye(3))@d.body('pelvis').xmat.reshape(3,3).T).as_rotvec()
        rows.append(8*pad(pj[3:]));ys.append(8*(60*upright-16*pj[3:]@d.qvel-pdj[3:]@d.qvel))
        for side,ref in (targets or {}).items():
            site=m.site(side+'_wrist_reference').id;j,dj=self.jacobian(d.site_xpos[site],int(m.site_bodyid[site]))
            error=np.asarray(ref)-d.site_xpos[site];rows.append(60*pad(j[:3]));ys.append(60*(100*error-22*j[:3]@d.qvel-dj[:3]@d.qvel))
            if hasattr(self,'palm_rotations'):
                rotation_error=Rotation.from_matrix(self.palm_rotations[side]@d.site_xmat[site].reshape(3,3).T).as_rotvec()
                rows.append(30*pad(j[3:]));ys.append(30*(60*rotation_error-16*j[3:]@d.qvel-dj[3:]@d.qvel))
        # Wrist tracking alone does not constrain a loaded, underactuated
        # fingertip. Track the robot's encoder-predicted surface point as an
        # additional Cartesian task; this does not attach it to an object.
        for task in (point_targets or []):
            point=np.asarray(task['point'],dtype=float);target=np.asarray(task['target'],dtype=float)
            if point.shape!=(3,) or target.shape!=(3,) or not np.isfinite(np.r_[point,target]).all():
                raise ValueError('Invalid robot surface-point target')
            j,dj=self.jacobian(point,m.body(task['body']).id)
            rows.append(60*pad(j[:3]));ys.append(60*(100*(target-point)-22*j[:3]@d.qvel-dj[:3]@d.qvel))
        rows.append(np.c_[np.zeros((12+k,n)),np.eye(12+k)*.0005]);ys.append(np.zeros(12+k))
        cost=np.vstack(rows);desired=np.concatenate(ys);P=cost.T@cost+np.eye(total)*1e-6;q=-cost.T@desired
        eqerr=np.array([d.qpos[a]-c*d.qpos[b]-offset for a,b,c,offset in self.eqdata])
        eqacc=-300*eqerr-35*self.eqj@d.qvel
        contact_rows=np.repeat(support,6)
        A=[dynamics[self.unactuated],pad(jf[contact_rows]),pad(self.eqj),dynamics[self.va]]
        lo=[-bias[self.unactuated],np.concatenate(acc)[contact_rows],eqacc,m.actuator_ctrlrange[:,0]-bias[self.va]]
        hi=[-bias[self.unactuated],np.concatenate(acc)[contact_rows],eqacc,m.actuator_ctrlrange[:,1]-bias[self.va]]
        wr=[];wl=[];wh=[]
        for foot in range(2):
            off=n+foot*6
            if not support[foot]:
                for axis in range(6):
                    row=np.zeros(total);row[off+axis]=1
                    wr.append(row);wl.append(0);wh.append(0)
                continue
            frame=self.foot_rotations[foot] if getattr(self,'rotate_foot_constraints',False) else np.eye(3)
            row=np.zeros(total);row[off:off+3]=frame[:,2];wr.append(row);wl.append(5);wh.append(800)
            for axis,mu in [(0,.6),(1,.6),(3,.025),(4,.07),(5,.012)]:
                for sign in [-1,1]:
                    row=np.zeros(total);start=off+(3 if axis>=3 else 0)
                    row[start:start+3]=sign*frame[:,axis%3];row[off:off+3]-=mu*frame[:,2]
                    wr.append(row);wl.append(-np.inf);wh.append(0)
        A.append(np.array(wr));lo.append(wl);hi.append(wh)
        solver=osqp.OSQP();solver.setup(P=sparse.csc_matrix(np.triu(P)),q=q,A=sparse.csc_matrix(np.vstack(A)),l=np.concatenate(lo),u=np.concatenate(hi),verbose=False,eps_abs=2e-5,eps_rel=2e-5,max_iter=getattr(self,'solver_max_iterations',6000),polishing=True)
        if self.previous is not None:solver.warm_start(x=self.previous)
        result=solver.solve(raise_error=False)
        self.solver_diagnostics=dict(status=result.info.status,iterations=result.info.iter,
                                     primal_residual=result.info.prim_res,dual_residual=result.info.dual_res)
        if result.info.status_val not in (1,2):raise RuntimeError('Balance QP: '+str(self.solver_diagnostics))
        self.previous=result.x;self.max_iter=max(self.max_iter,result.info.iter)
        torque=dynamics[self.va]@result.x+bias[self.va]
        for side,force in (forces or {}).items():
            site=m.site(side+'_wrist_reference').id;j,_=self.jacobian(d.site_xpos[site],int(m.site_bodyid[site]))
            torque+=j[:3,self.va].T@np.asarray(force)
        return np.clip(torque,m.actuator_ctrlrange[:,0],m.actuator_ctrlrange[:,1])
