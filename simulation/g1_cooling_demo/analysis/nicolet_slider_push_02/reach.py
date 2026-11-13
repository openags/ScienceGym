"""Screen registered source-arm paths for the selected sliding-door push.

Retained encoders/IMU and RGB-D key observations supply body and instrument
estimates. No plant poses or device joints enter planning. Whole-body source
self intersections and Nicolet/PIKE intersections are checked, not the room,
contact forces, loaded deformation or successful physical execution.
"""
from collections import defaultdict
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
import trimesh

from fit_push import HERE,ROOT,VIEW,LOADER,load_environment,translate,sha,get_transform
BASE=ROOT/'simulation/g1_cooling_demo'
RUN=BASE/'runs/ftir_cover_13'
sys.path[:0]=[str(BASE),str(VIEW)]
from observations import StateEstimate
from ftir_hand import initialize_cover,ArmIK,mimic
from ftir_cover_geometry import register
from source_geometry import robot_meshes,KIN


def main():
    started=time.monotonic();out=HERE/'reach.json'
    if out.exists():raise FileExistsError(out)
    m=mujoco.MjModel.from_xml_path(str(RUN/'controller_model/world.xml'))
    d=initialize_cover(m,[5.95,-5.32]);estimate=StateEstimate(m,d)
    sensors=np.load(RUN/'sensor_observations.npz');i=int(np.argmin(abs(sensors['time_s']-2.)))
    packet={k:sensors[k][i] for k in sensors.files if k!='right_touch_n'};packet['depth']=None;estimate.update(packet)
    prior=json.loads((RUN/'policy_source/cover_grasp_prior.json').read_text())
    observations=[r['observation'] for r in json.loads((RUN/'actor_responses.json').read_text())
                  if r['time_s']<=2.001 and r.get('observation',{} ) and r['observation'].get('accepted')][-8:]
    if len(observations)!=8:raise ValueError('Need eight retained key observations')
    registrations=[register(o,prior) for o in observations]
    R=Rotation.from_matrix(np.stack([r for r,t in registrations])).mean().as_matrix()
    t=np.median([t for r,t in registrations],axis=0)
    search=json.loads((HERE/'review.json').read_text());center=np.array(search['grip_bounds_port_frame_m']).mean(0)
    source_center=np.array([-.011,-.247,.251])
    mapping=np.eye(4);mapping[:3,:3]=R;mapping[:3,3]=t+R@(source_center-center)
    env,_,_,_,paths,_=load_environment()
    slider={'nicolet::sample_access_sliding_window','nicolet::sample_access_slider_grip'}
    rest={name:mapping@(translate([0,-.104,0]) if name in slider else np.eye(4))@get_transform(obj['obj']) for name,obj in env._objs.items()}
    for name,T in rest.items():env.set_transform(name,T)
    source=robot_meshes();robot=trimesh.collision.CollisionManager();body_ids={}
    for name,mesh in source.items():
        bid=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,name)
        if bid<0:raise ValueError('Missing source body '+name)
        body_ids[name]=bid;robot.add_object(name,mesh)
    graph=defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for link in body_ids:
        todo=[(link,None,0)]
        while todo:
            n,parent,depth=todo.pop()
            if depth>1:continue
            if n in body_ids:adjacent.add(tuple(sorted([link,n])))
            todo.extend((v,n,depth+w) for v,w in graph[n] if v!=parent)
    def collision(travel):
        for name,bid in body_ids.items():
            T=np.eye(4);T[:3,:3]=d.xmat[bid].reshape(3,3);T[:3,3]=d.xpos[bid];robot.set_transform(name,T)
        for name in slider:env.set_transform(name,translate(R@np.array([0.,travel,0.]))@rest[name])
        _,pairs=robot.in_collision_internal(return_names=True)
        bad=[sorted(p) for p in pairs if tuple(sorted(p)) not in adjacent]
        _,external=robot.in_collision_other(env,return_names=True)
        return dict(self_contact=bad,instrument_contact=sorted([sorted(p) for p in external]))
    d.qpos[1]+=.12;ik=ArmIK(m)
    d.qpos[ik.qa]=np.clip([.2,-.3,0,1.5,0,0,0],ik.low,ik.high)
    mujoco.mj_forward(m,d)
    initial=d.qpos.copy();home=initial[ik.qa].copy()
    reach_seed=np.clip([-.8,-.4,0,1.4,0,0,0],ik.low,ik.high)
    initial_position=d.site('right_wrist_reference').xpos.copy();initial_R=d.site('right_wrist_reference').xmat.reshape(3,3).copy()
    rows=[];accepted=[]
    for index,c in enumerate(search['candidates']):
        if not c['passed_distal_path']:continue
        d.qpos[:]=initial;target=mapping@np.array(c['palm_in_port_frame'])
        for n,v in c['q'].items():d.joint(n).qpos[0]=v
        mimic(m,d);mujoco.mj_forward(m,d)
        seed=reach_seed.copy();failure=None;peak=[0.,0.]
        for travel in [0.,.035,.07]:
            goal=target[:3,3]+R@np.array([0.,travel,0.])
            seed,pe,re=ik.solve(d,goal,target[:3,:3],seed);peak=[max(peak[0],pe),max(peak[1],re)]
            if pe>.003 or re>.035:
                failure=dict(kind='ik',travel_m=travel,position_error_m=pe,rotation_error_rad=re);break
            d.qpos[ik.qa]=seed;mujoco.mj_forward(m,d);contacts=collision(travel)
            if any(contacts.values()):failure=dict(kind='source_collision',travel_m=travel,**contacts);break
        rows.append(dict(candidate=index,endpoint_passed=failure is None,failure=failure,peak_ik_error=peak))
        if failure is None:accepted.append((index,c,target))
        if index%40==0:print('reach',index,'endpoint_passed',len(accepted),flush=True)
    full=[]
    for index,c,target in accepted[:24]:
        d.qpos[:]=initial;seed=home.copy();finger0={n:float(d.joint(n).qpos[0]) for n in c['q']}
        raised=initial_position+[-.03,0,.07];pre=target[:3,3]+R@np.array([0.,-.025,.030]);end=target[:3,3]+R@np.array([0.,.07,0.])
        steps=[('raise',raised,initial_R,0.,0.),('approach',pre,target[:3,:3],1.,0.),
               ('align',target[:3,3],target[:3,:3],1.,0.),('push',end,target[:3,:3],1.,.07),
               ('withdraw',end+R@np.array([0.,-.01,.045]),target[:3,:3],1.,.07),
               ('clear',raised,initial_R,0.,.07),('return',initial_position,initial_R,0.,.07)]
        previous=initial_position;previous_R=initial_R;previous_curl=0.;previous_travel=0.;failure=None;states=[]
        for name,goal,rotation,curl,travel in steps:
            orientations=Slerp([0.,1.],Rotation.from_matrix([previous_R,rotation]))
            for u in np.linspace(0,1,41):
                blend=3*u*u-2*u*u*u;position=previous+blend*(goal-previous);orientation=orientations([blend]).as_matrix()[0]
                hand_u=previous_curl+blend*(curl-previous_curl)
                for n,v in c['q'].items():d.joint(n).qpos[0]=finger0[n]+hand_u*(v-finger0[n])
                mimic(m,d);seed,pe,re=ik.solve(d,position,orientation,seed)
                if pe>.003 or re>.035:failure=dict(phase=name,fraction=float(u),kind='ik',position_error_m=pe,rotation_error_rad=re);break
                d.qpos[ik.qa]=seed;mujoco.mj_forward(m,d)
                contacts=collision(previous_travel+blend*(travel-previous_travel))
                if any(contacts.values()):failure=dict(phase=name,fraction=float(u),kind='source_collision',**contacts);break
                states.append(dict(phase=name,fraction=float(u),arm_q=seed.tolist()))
            if failure:break
            previous,previous_R,previous_curl,previous_travel=goal,rotation,curl,travel
        full.append(dict(candidate=index,passed=failure is None,failure=failure,states=states))
        print('full_path',index,'passed',failure is None,'failure',failure,flush=True)
    deps=paths+[Path(__file__),HERE/'fit_push.py',HERE/'review.json',LOADER,BASE/'observations.py',BASE/'ftir_hand.py',BASE/'ftir_cover_geometry.py',VIEW/'source_geometry.py',RUN/'sensor_observations.npz',RUN/'actor_responses.json',RUN/'policy_source/cover_grasp_prior.json',RUN/'controller_model/world.xml']
    report=dict(scope=__doc__,rows=rows,full_paths=full,passed_endpoint_candidates=len(accepted),
                passed_full_paths=sum(x['passed'] for x in full),source_registration=dict(rotation=R.tolist(),translation=t.tolist()),
                source_slider_grip_center_m=source_center.tolist(),port_to_observed_mapping=mapping.tolist(),
                source_hashes={str(p.relative_to(ROOT)):sha(p) for p in deps},seconds=time.monotonic()-started,
                physical_execution=False,whole_laboratory_checked=False,prepared_stance_execution_credit=False,
                hypothetical_stance_offset_m=[0.,.12],forward_ik_seed=reach_seed.tolist(),prepared_arm_q=home.tolist())
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(endpoints=len(accepted),full=report['passed_full_paths'],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
