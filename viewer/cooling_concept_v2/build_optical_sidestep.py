"""Grounded lateral foot placements between FTIR port and optical staging.

Authored leg inverse kinematics with planted stance-foot targets. This does
not implement dynamic balance. The full carried-tool/room trajectory needs
its own independent review after composition with the manipulation episode.
"""
import hashlib,json,math,xml.etree.ElementTree as ET
import mujoco,numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,KIN,fk
from optical_choreography import HERE,load_json,Scene,canonical


def main():
    pickup=load_json('previews/optical_tool_pickup_path.json');port=load_json('previews/specimen_port_refined.json')['candidates'][0]
    base0=np.array(port['root']).reshape(4,4).T;base1=np.array(pickup['root']);delta=base1[:3,3]-base0[:3,3];assert abs(delta[2])<1e-8 and np.max(abs(base0[:3,:3]-base1[:3,:3]))<1e-10
    q0=canonical(port['rows'][-1]['q']);scene=Scene();q=dict(q0);poses=load_json('motion_poses.json')
    asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset));model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'};indices={n:model.joint(n).qposadr[0] for n in joints};yaw=port['stance']['yaw']
    data.qpos[:3]=base0[:3,3]+[0,0,KIN['root_matrix'][2][3]];data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
    for n,v in q0.items():data.qpos[indices[n]]=v
    mujoco.mj_kinematics(model,data);legs={s:[s+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for s in ['left','right']}
    feet={s:(data.body(s+'_ankle_roll_link').xpos.copy(),data.body(s+'_ankle_roll_link').xmat.reshape(3,3).copy()) for s in legs}
    source=fk(q0);agreement=max(float(np.abs(base0@source[s+'_ankle_roll_link']-np.block([[feet[s][1],feet[s][0][:,None]],[np.array([[0,0,0,1]])]])).max()) for s in legs);assert agreement<1e-8
    pairs=math.ceil(np.linalg.norm(delta[:2])/.20);steps=2*pairs;duration=steps*1.5;lead='left' if delta[:2]@np.array([-np.sin(yaw),np.cos(yaw)])>0 else 'right';rows=[]
    for t in np.linspace(0,duration,round(duration/.025)+1):
        phase=min(steps-1,int(t/1.5));u=(t-phase*1.5)/1.5;s=u*u*(3-2*u);root=base0.copy();root[:3,3]+=delta*(phase+s)/steps;root[2,3]-=.015*np.sin(np.pi*t/duration)
        data.qpos[:3]=root[:3,3]+[0,0,KIN['root_matrix'][2][3]];errors={}
        for side,names in legs.items():
            turn=0 if side==lead else 1;completed=sum(1 for step in range(phase) if step%2==turn);flying=phase%2==turn
            target=feet[side][0]+delta*(completed+(s if flying else 0))/pairs
            if flying:target[2]+=.04*np.sin(np.pi*u)**2
            rotation=feet[side][1];idx=[indices[n] for n in names];limits=np.array([[joints[n]['limits']['lower'],joints[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
            def objective(values):
                data.qpos[idx]=values;mujoco.mj_kinematics(model,data);return np.r_[body.xpos-target,.20*Rotation.from_matrix(rotation@body.xmat.reshape(3,3).T).as_rotvec()]
            solved=least_squares(objective,[q[n] for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11);error=objective(solved.x);q.update(dict(zip(names,map(float,solved.x))))
            errors[side]=dict(position_m=float(np.linalg.norm(error[:3])),orientation_rad=float(np.linalg.norm(error[3:])/.2),stance=not flying,target_position_m=target.tolist())
        world=fk(q);sole=min(float((np.array(v)@(root@world[n])[2,:3]+(root@world[n])[2,3]).min()) for n,v in poses['sole_vertices_m'].items())
        failure=scene.check(root,q,tool_held=True,closure=scene.fit['carrier_grip_closure'],held_specimen='white')
        rows.append(dict(time_s=float(t),root=root.tolist(),q=dict(q),feet=errors,minimum_sole_z_m=sole,failure=failure))
    speeds={n:max(abs(b['q'][n]-a['q'][n])/(b['time_s']-a['time_s']) for a,b in zip(rows,rows[1:])) for names in legs.values() for n in names}
    result=dict(scope=__doc__,rows=rows,duration_s=duration,source_fk_maximum_matrix_error=agreement,foot_placements=steps,lead_foot=lead,body_translation_m=delta.tolist(),maximum_leg_joint_speeds_rad_s=speeds,passed=all(not r['failure'] and r['minimum_sole_z_m']>-.00001 and all(e['position_m']<1e-5 for e in r['feet'].values()) for r in rows) and all(v<joints[n]['limits']['velocity'] for n,v in speeds.items()),source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['build_optical_sidestep.py','optical_choreography.py','previews/optical_tool_pickup_path.json','previews/specimen_port_refined.json']})
    (HERE/'previews/optical_sidestep.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],states=len(rows),foot_placements=steps,duration_s=duration,failures=[dict(time_s=r['time_s'],failure=r['failure']) for r in rows if r['failure']][:5])),flush=True)


if __name__=='__main__':main()
