"""Grounded source-leg trajectories connecting optical operation stances.

The same official leg model and planted-foot equations as the existing
delivery gait are used. This generates kinematics, not dynamic balance.
"""
import math
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from optical_choreography import JOINTS, load_json
from source_geometry import ROOT, KIN, fk


def yaw(root):
    return math.atan2(root[1,0], root[0,0])


def grounded_route(initial, goal, q0, foot_duration=.7, aisle_y=7.45):
    initial, goal = np.array(initial), np.array(goal)
    assert abs(initial[2,3]-goal[2,3]) < 1e-8
    points = [initial]
    distance = np.linalg.norm(goal[:2,3]-initial[:2,3])
    if distance > .65:
        direction = math.pi if goal[0,3] < initial[0,3] else 0.
        for x, y, angle in [(initial[0,3],aisle_y,yaw(initial)),
                             (initial[0,3],aisle_y,direction),
                             (goal[0,3],aisle_y,direction),
                             (goal[0,3],aisle_y,yaw(goal))]:
            point=initial.copy();point[:3,:3]=Rotation.from_euler('z',angle).as_matrix();point[:2,3]=[x,y]
            points.append(point)
    points.append(goal)
    targets=[]
    for a,b in zip(points,points[1:]):
        turn=math.atan2(math.sin(yaw(b)-yaw(a)),math.cos(yaw(b)-yaw(a)))
        count=max(1,math.ceil(np.linalg.norm(b[:2,3]-a[:2,3])/.20),math.ceil(abs(turn)/.20))
        for k in range(1,count+1):
            value=a.copy();value[:3,3]+=(b[:3,3]-a[:3,3])*k/count
            value[:3,:3]=Rotation.from_euler('z',yaw(a)+turn*k/count).as_matrix();targets.append(value)
    asset=ROOT/'assets/unitree_g1_inspire_v1'
    xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset))
    model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    indices={n:model.joint(n).qposadr[0] for n in JOINTS};poses=load_json('motion_poses.json')
    legs={s:[s+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for s in ['left','right']}
    q=dict(q0);world=fk(q);foot_local={s:world[s+'_ankle_roll_link'] for s in legs}
    base=initial.copy();clock=0.;rows=[]
    for target in targets:
        begin=base.copy();turn=math.atan2(math.sin(yaw(target)-yaw(begin)),math.cos(yaw(target)-yaw(begin)))
        lead='right' if turn<0 else 'left';order=[lead,'left' if lead=='right' else 'right']
        feet={s:begin@foot_local[s] for s in legs}
        for half,swing in enumerate(order):
            other='right' if swing=='left' else 'left';start_foot=feet[swing].copy();end_foot=target@foot_local[swing]
            for knot,u in enumerate(np.linspace(0,1,29)):
                if rows and knot==0:continue
                blend=u*u*(3-2*u);amount=(half+blend)/2
                base=begin.copy();base[:3,3]+=(target[:3,3]-begin[:3,3])*amount
                angle=yaw(begin)+turn*amount;base[:3,:3]=Rotation.from_euler('z',angle).as_matrix()
                base[2,3]-=.015*math.sin(math.pi*amount)
                data.qpos[:3]=base[:3,3]+np.array(KIN['root_matrix'])[:3,3]
                data.qpos[3:7]=[math.cos(angle/2),0,0,math.sin(angle/2)]
                for n,v in q.items():data.qpos[indices[n]]=v
                wanted={other:feet[other].copy(),swing:start_foot.copy()}
                wanted[swing][:3,3]=(1-blend)*start_foot[:3,3]+blend*end_foot[:3,3]
                wanted[swing][2,3]+=.04*math.sin(math.pi*u)**2
                wanted[swing][:3,:3]=Rotation.from_euler('z',yaw(begin)+turn*blend).as_matrix()@foot_local[swing][:3,:3]
                errors={}
                for side,names in legs.items():
                    desired=wanted[side];idx=[indices[n] for n in names]
                    limits=np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
                    def residual(values):
                        data.qpos[idx]=values;mujoco.mj_kinematics(model,data)
                        return np.r_[body.xpos-desired[:3,3],.20*Rotation.from_matrix(desired[:3,:3]@body.xmat.reshape(3,3).T).as_rotvec()]
                    solved=least_squares(residual,[q[n] for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),
                                         max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11)
                    error=residual(solved.x);q.update(dict(zip(names,map(float,solved.x))))
                    errors[side]=dict(position_m=float(np.linalg.norm(error[:3])),orientation_rad=float(np.linalg.norm(error[3:])/.20),stance=side==other,target=desired.tolist())
                world=fk(q)
                agreement=max(float(np.max(abs((base@world[s+'_ankle_roll_link'])[:3,3]-data.body(s+'_ankle_roll_link').xpos))) for s in legs)
                sole=min(float((np.array(v)@(base@world[n])[2,:3]+(base@world[n])[2,3]).min()) for n,v in poses['sole_vertices_m'].items())
                if agreement>1e-8 or sole<-1e-5 or any(e['position_m']>1e-5 or e['orientation_rad']>1e-5 for e in errors.values()):
                    raise RuntimeError('Source foot IK failed')
                rows.append(dict(time_s=clock+foot_duration*u,root=base.tolist(),q=dict(q),feet=errors,
                                 source_fk_position_error_m=agreement,minimum_sole_z_m=sole))
            feet[swing]=end_foot;clock+=foot_duration
        base=target.copy()
    endpoint=max(abs(q[n]-q0[n]) for names in legs.values() for n in names)
    assert endpoint<1e-6
    return dict(rows=rows,duration_s=clock,waypoints=[p.tolist() for p in points],endpoint_joint_error_rad=endpoint)
