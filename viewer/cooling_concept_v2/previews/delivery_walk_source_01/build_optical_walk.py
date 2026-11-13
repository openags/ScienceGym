"""Authored grounded foot placements and turns for optical witness delivery.

Uses official source leg FK/limits and planted stance-foot targets. This is
kinematic choreography, not a balance controller or a physical walking trial.
The complete laboratory and held tool/witness are screened at each knot;
independent composed-scene sampling remains required.
"""
import argparse,hashlib,json,math,time,xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,canonical,load_json
from optical_delivery import DeliveryScene
from source_geometry import ROOT,KIN,fk


def heading(root):return math.atan2(root[1,0],root[0,0])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['white','black'],required=True);args=parser.parse_args();kind=args.kind;began=time.monotonic()
    scene=DeliveryScene();pickup=load_json('previews/optical_tool_pickup_path.json');collection=load_json('previews/cary_'+kind+'_collection.json');port=load_json('previews/specimen_port_refined.json')['candidates'][0]
    start=np.array(pickup['root']);goal=np.array(collection['root']);q0=canonical(port['rows'][-1]['q']);poses=load_json('motion_poses.json');stored=dict(scene.cary_staging)
    if kind=='black':stored['white']=np.array(load_json('previews/optical_white_exchange.json')['initial_holder'])
    waypoints=[start.copy()]
    for x,y,yaw in [(start[0,3],7.25,heading(start)),(start[0,3],7.25,math.pi),(goal[0,3],7.25,math.pi),(goal[0,3],7.25,heading(goal)),(goal[0,3],goal[1,3],heading(goal))]:
        root=start.copy();root[:3,:3]=Rotation.from_euler('z',yaw).as_matrix();root[:2,3]=[x,y];waypoints.append(root)
    pair_targets=[]
    for a,b in zip(waypoints,waypoints[1:]):
        dyaw=math.atan2(math.sin(heading(b)-heading(a)),math.cos(heading(b)-heading(a)));distance=np.linalg.norm(b[:2,3]-a[:2,3]);count=max(1,math.ceil(distance/.28),math.ceil(abs(dyaw)/.24))
        for i in range(1,count+1):
            root=a.copy();root[:3,3]=a[:3,3]+(b[:3,3]-a[:3,3])*i/count;root[:3,:3]=Rotation.from_euler('z',heading(a)+dyaw*i/count).as_matrix();pair_targets.append(root)
    asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset));model=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));data=mujoco.MjData(model)
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'};indices={n:model.joint(n).qposadr[0] for n in joints}
    legs={s:[s+'_'+n+'_joint' for n in ['hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll']] for s in ['left','right']}
    foot_local={s:fk(q0)[s+'_ankle_roll_link'] for s in legs};q=dict(q0);rows=[];base=start.copy();duration_per_foot=.7;clock=0.;failure_count=0
    for pair_number,target in enumerate(pair_targets):
        initial=base.copy();delta_yaw=math.atan2(math.sin(heading(target)-heading(initial)),math.cos(heading(target)-heading(initial)));lead='right' if delta_yaw<0 else 'left';order=[lead,'left' if lead=='right' else 'right']
        feet={s:initial@foot_local[s] for s in legs}
        for half,swing in enumerate(order):
            planted='left' if swing=='right' else 'right';foot_start=feet[swing].copy();foot_end=target@foot_local[swing]
            for knot,u in enumerate(np.linspace(0,1,29)):
                if rows and knot==0:continue
                blend=u*u*(3-2*u);amount=(half+blend)/2;root=initial.copy();root[:3,3]+=amount*(target[:3,3]-initial[:3,3]);yaw=heading(initial)+amount*delta_yaw;root[:3,:3]=Rotation.from_euler('z',yaw).as_matrix();root[2,3]-=.015*math.sin(math.pi*amount)
                data.qpos[:3]=root[:3,3]+np.array(KIN['root_matrix'])[:3,3];data.qpos[3:7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
                for name,value in q.items():data.qpos[indices[name]]=value
                targets={planted:feet[planted].copy(),swing:foot_start.copy()};targets[swing][:3,3]=(1-blend)*foot_start[:3,3]+blend*foot_end[:3,3];targets[swing][2,3]+=.045*math.sin(math.pi*u)**2
                targets[swing][:3,:3]=Rotation.from_euler('z',heading(initial)+blend*delta_yaw).as_matrix()@foot_local[swing][:3,:3]
                errors={}
                for side,names in legs.items():
                    desired=targets[side];idx=[indices[n] for n in names];limits=np.array([[joints[n]['limits']['lower'],joints[n]['limits']['upper']] for n in names]);body=data.body(side+'_ankle_roll_link')
                    def residual(values):
                        data.qpos[idx]=values;mujoco.mj_kinematics(model,data);return np.r_[body.xpos-desired[:3,3],.20*Rotation.from_matrix(desired[:3,:3]@body.xmat.reshape(3,3).T).as_rotvec()]
                    result=least_squares(residual,[q[n] for n in names],bounds=(limits[:,0]+1e-6,limits[:,1]-1e-6),max_nfev=80,ftol=1e-11,xtol=1e-11,gtol=1e-11);error=residual(result.x);q.update(dict(zip(names,map(float,result.x))))
                    errors[side]=dict(position_m=float(np.linalg.norm(error[:3])),orientation_rad=float(np.linalg.norm(error[3:])/.20),stance=side==planted,target=desired.tolist())
                world=fk(q);sole=min(float((np.array(vertices)@(root@world[name])[2,:3]+(root@world[name])[2,3]).min()) for name,vertices in poses['sole_vertices_m'].items());agreement=max(float(np.max(abs((root@world[side+'_ankle_roll_link'])[:3,3]-data.body(side+'_ankle_roll_link').xpos))) for side in legs)
                full=scene.check(root,q,tool_held=True,closure=scene.fit['carrier_grip_closure'],held_specimen=kind,stored=stored)
                empty=scene.check(root,{**q,**scene.hand_q(0.)},tool_held=True,stored=stored) if not full else {}
                failures={k:v for k,v in [('held',full),('empty',empty)] if v};failure_count+=bool(failures)
                rows.append(dict(time_s=clock+duration_per_foot*u,root=root.tolist(),q=dict(q),feet=errors,minimum_sole_z_m=sole,source_fk_position_error_m=agreement,failures=failures))
            feet[swing]=foot_end;clock+=duration_per_foot
        base=target.copy();print(kind,'walk pair',pair_number+1,'/',len(pair_targets),'failures',failure_count,flush=True)
    speed={n:max(abs(b['q'][n]-a['q'][n])/(b['time_s']-a['time_s']) for a,b in zip(rows,rows[1:])) for names in legs.values() for n in names}
    endpoint_error=max(max(abs(rows[0]['q'][n]-q0[n]) for n in q0),max(abs(rows[-1]['q'][n]-q0[n]) for n in q0))
    result=dict(scope=__doc__,kind=kind,waypoints=[m.tolist() for m in waypoints],rows=rows,duration_s=clock,foot_placements=len(pair_targets)*2,source_speed_max_rad_s=speed,endpoint_joint_error_rad=endpoint_error,passed=not failure_count and endpoint_error<1e-6 and all(r['minimum_sole_z_m']>=-1e-5 and r['source_fk_position_error_m']<1e-8 and all(e['position_m']<1e-5 and e['orientation_rad']<1e-5 for e in r['feet'].values()) for r in rows) and all(speed[n]<joints[n]['limits']['velocity'] for n in speed),independent_composed_review_pending=True,wall_seconds=time.monotonic()-began,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['build_optical_walk.py','optical_delivery.py','previews/cary_'+kind+'_collection.json','previews/optical_tool_pickup_path.json','previews/specimen_port_refined.json']})
    (HERE/'previews'/('optical_'+kind+'_delivery_walk.json')).write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256','waypoints','scope','source_speed_max_rad_s']}),flush=True)


if __name__=='__main__':main()
