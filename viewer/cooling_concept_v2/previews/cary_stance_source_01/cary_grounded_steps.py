"""Source-leg IK for short, fixed-heading steps between Cary operation poses.

The planted foot stays at its world target. This is a kinematic path generator;
callers must check carried geometry and the complete room, then validate balance
and contacts separately. It supplies no dynamics qualification.
"""
import math,xml.etree.ElementTree as ET
import mujoco,numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from optical_choreography import JOINTS,load_json
from source_geometry import ROOT,KIN,fk


def translation_steps(initial,goal,q0,foot_duration=.85):
    initial=np.array(initial);goal=np.array(goal);delta=goal[:3,3]-initial[:3,3]
    assert np.max(abs(initial[:3,:3]-goal[:3,:3]))<1e-10 and abs(delta[2])<1e-9
    asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset));model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    indices={n:model.joint(n).qposadr[0] for n in JOINTS};poses=load_json('motion_poses.json')
    legs={s:[s+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for s in ['left','right']}
    q=dict(q0);world=fk(q);foot_local={s:world[s+'_ankle_roll_link'] for s in legs};base=initial.copy();count=max(1,math.ceil(np.linalg.norm(delta[:2])/.20));clock=0.;rows=[]
    yaw=math.atan2(initial[1,0],initial[0,0]);lead='left' if delta[:2]@np.array([-math.sin(yaw),math.cos(yaw)])>0 else 'right';order=[lead,'right' if lead=='left' else 'left']
    for pair in range(count):
        begin=base.copy();end=initial.copy();end[:3,3]+=delta*(pair+1)/count;feet={s:begin@foot_local[s] for s in legs}
        for half,swing in enumerate(order):
            other='right' if swing=='left' else 'left';start_foot=feet[swing].copy();end_foot=end@foot_local[swing]
            for knot,u in enumerate(np.linspace(0,1,35)):
                if rows and knot==0:continue
                blend=u*u*(3-2*u);amount=(half+blend)/2;base=begin.copy();base[:3,3]+=(end[:3,3]-begin[:3,3])*amount;base[2,3]-=.015*math.sin(math.pi*amount)
                data.qpos[:3]=base[:3,3]+np.array(KIN['root_matrix'])[:3,3];data.qpos[3:7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
                for n,v in q.items():data.qpos[indices[n]]=v
                targets={other:feet[other].copy(),swing:start_foot.copy()};targets[swing][:3,3]=(1-blend)*start_foot[:3,3]+blend*end_foot[:3,3];targets[swing][2,3]+=.04*math.sin(math.pi*u)**2;errors={}
                for side,names in legs.items():
                    target=targets[side];idx=[indices[n] for n in names];limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
                    def residual(values):
                        data.qpos[idx]=values;mujoco.mj_kinematics(model,data);return np.r_[body.xpos-target[:3,3],.20*Rotation.from_matrix(target[:3,:3]@body.xmat.reshape(3,3).T).as_rotvec()]
                    result=least_squares(residual,[q[n] for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11);error=residual(result.x);q.update(dict(zip(names,map(float,result.x))))
                    errors[side]=dict(position_m=float(np.linalg.norm(error[:3])),orientation_rad=float(np.linalg.norm(error[3:])/.20),stance=side==other,target=target.tolist())
                world=fk(q);agreement=max(float(np.max(abs((base@world[s+'_ankle_roll_link'])[:3,3]-data.body(s+'_ankle_roll_link').xpos))) for s in legs)
                sole=min(float((np.array(v)@(base@world[n])[2,:3]+(base@world[n])[2,3]).min()) for n,v in poses['sole_vertices_m'].items())
                if agreement>1e-8 or sole< -1e-5 or any(e['position_m']>1e-5 or e['orientation_rad']>1e-5 for e in errors.values()):raise RuntimeError('Source foot IK failed')
                rows.append(dict(time_s=clock+foot_duration*u,root=base.tolist(),q=dict(q),feet=errors,source_fk_position_error_m=agreement,minimum_sole_z_m=sole))
            feet[swing]=end_foot;clock+=foot_duration
        base=end.copy()
    assert max(abs(q[n]-q0[n]) for names in legs.values() for n in names)<1e-6
    return rows
