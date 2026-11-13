"""Authored four-step lateral carry with grounded, planted stance feet.

Inverse kinematics only, not a balance controller or contact dynamics run.
Every stance-foot target is fixed in world coordinates; the other foot lifts
and advances 200 mm. Two such left/right pairs translate the body 400 mm.
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from source_geometry import ROOT, KIN, fk
from plan_reference_storage import HERE


def main():
    lift=json.loads((HERE/'reference_lift_path.json').read_text());q0=lift['path']['knots'][-1]['q'];base0=np.array(lift['path']['root']).reshape(4,4).T
    asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset))
    model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'};indices={n:model.joint(n).qposadr[0] for n in joints}
    legs={side:[side+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for side in ['left','right']}
    yaw=lift['path']['stance']['yaw'];data.qpos[:3]=base0[:3,3]+[0,0,KIN['root_matrix'][2][3]];data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
    for n,v in q0.items():data.qpos[indices[n]]=v
    mujoco.mj_kinematics(model,data)
    feet={s:(data.body(s+'_ankle_roll_link').xpos.copy(),data.body(s+'_ankle_roll_link').xmat.reshape(3,3).copy()) for s in legs}
    source=fk(q0);agreement=max(float(np.abs(base0@source[s+'_ankle_roll_link']-np.block([[feet[s][1],feet[s][0][:,None]],[np.array([[0,0,0,1]])]])).max()) for s in legs)
    assert agreement<1e-8
    poses=json.loads((HERE/'motion_poses.json').read_text());rows=[];q=dict(q0);duration=6.;dt=.025
    for time in np.linspace(0,duration,round(duration/dt)+1):
        phase=min(3,int(time/1.5));u=(time-phase*1.5)/1.5;smooth=u*u*(3-2*u)
        root=base0.copy();root[0,3]-=.1*(phase+smooth);root[2,3]-=.015*np.sin(np.pi*time/duration)
        data.qpos[:3]=root[:3,3]+[0,0,KIN['root_matrix'][2][3]]
        errors={}
        for side,names in legs.items():
            turn=0 if side=='left' else 1;completed=sum(1 for step in range(phase) if step%2==turn)
            flying=phase%2==turn;target=feet[side][0].copy();target[0]-=.2*(completed+(smooth if flying else 0))
            if flying:target[2]+=.04*np.sin(np.pi*u)**2
            rotation=feet[side][1];idx=[indices[n] for n in names];limits=np.array([[joints[n]['limits']['lower'],joints[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
            def objective(values):
                data.qpos[idx]=values;mujoco.mj_kinematics(model,data)
                angular=Rotation.from_matrix(rotation@body.xmat.reshape(3,3).T).as_rotvec()
                return np.r_[body.xpos-target,.20*angular]
            result=least_squares(objective,[q.get(n,0.) for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11)
            residual=objective(result.x);q.update(dict(zip(names,map(float,result.x))))
            errors[side]=dict(position_m=float(np.linalg.norm(residual[:3])),orientation_rad=float(np.linalg.norm(residual[3:])/.2),stance=not flying,target_position_m=target.tolist())
        world=fk(q);sole_min=min(float((np.array(vertices)@(root@world[name])[2,:3]+(root@world[name])[2,3]).min()) for name,vertices in poses['sole_vertices_m'].items())
        offset=np.array(lift['path']['knots'][-1]['offset'])+root[:3,3]-base0[:3,3]
        rows.append(dict(time_s=float(time),stage='reference_sidestep',root=root.tolist(),q=dict(q),offset=offset.tolist(),reference_offset=offset.tolist(),closed=1.,feet=errors,minimum_sole_z_m=sole_min,error=lift['path']['knots'][-1]['error'],rotationError=lift['path']['knots'][-1]['rotationError']))
    maximum_speed={n:max(abs(b['q'].get(n,0)-a['q'].get(n,0))/(b['time_s']-a['time_s']) for a,b in zip(rows,rows[1:])) for names in legs.values() for n in names}
    maximum_position=max(e['position_m'] for r in rows for e in r['feet'].values());minimum_sole=min(r['minimum_sole_z_m'] for r in rows)
    report=dict(scope=__doc__,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['build_reference_sidestep.py','reference_lift_path.json','motion_poses.json','source_geometry.py']},rows=rows,duration_s=duration,step_s=dt,
                source_fk_maximum_matrix_error=agreement,maximum_foot_position_error_m=maximum_position,minimum_sole_z_m=minimum_sole,maximum_leg_joint_speeds_rad_s=maximum_speed,
                endpoint_leg_joint_difference_rad=max(abs(rows[-1]['q'].get(n,0)-q0.get(n,0)) for names in legs.values() for n in names),
                passed_kinematics=maximum_position<1e-5 and minimum_sole>-.00001 and all(v<joints[n]['limits']['velocity'] for n,v in maximum_speed.items()),whole_scene_validation_pending=True)
    out=HERE/'reference_sidestep.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256','scope','maximum_leg_joint_speeds_rad_s']}),flush=True)


if __name__=='__main__':main()
