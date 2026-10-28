"""Screen registered source-arm paths for the selected sliding-door push.

Retained encoders/IMU and RGB-D key observations supply body and instrument
estimates. No plant poses or device joints enter planning. Whole-body source
self intersections and Nicolet/PIKE intersections are checked, not the room,
contact forces, loaded deformation or successful physical execution.
Unchanged baseline lower-leg visual overlaps are retained separately and do
not establish whole-robot source clearance; they do not reject arm exploration.
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
from source_proximity_room import SourceClearance
from robot_source_meshes import robot_source_meshes


def main():
    started=time.monotonic();out=HERE/'room_rrt.json'
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
    architecture_meshes={}
    # The actor's existing public map contains architecture, not equipment
    # or a precomputed motion path. Include this same map in arm planning.
    for gid in range(m.ngeom):
        bid=int(m.geom_bodyid[gid])
        if m.body(bid).name!='lab_architecture' or m.geom_group[gid]!=2:continue
        if m.geom_type[gid]!=mujoco.mjtGeom.mjGEOM_MESH:raise ValueError('Unexpected architecture geometry')
        mid=int(m.geom_dataid[gid]);va,vn=m.mesh_vertadr[mid],m.mesh_vertnum[mid];fa,fn=m.mesh_faceadr[mid],m.mesh_facenum[mid]
        mesh=trimesh.Trimesh(vertices=m.mesh_vert[va:va+vn].copy(),faces=m.mesh_face[fa:fa+fn].copy(),process=False)
        T=np.eye(4);T[:3,:3]=d.geom_xmat[gid].reshape(3,3);T[:3,3]=d.geom_xpos[gid]
        # Conservative workspace restriction: the active arm cannot extend
        # more than 1.5 m from this fixed pelvis, including the entire hand.
        points=mesh.vertices@T[:3,:3].T+T[:3,3]
        if np.any(points.max(0)<d.qpos[:3]-1.5) or np.any(points.min(0)>d.qpos[:3]+1.5):continue
        name='architecture::'+m.geom(gid).name
        architecture_meshes[name]=mesh;env.add_object(name,mesh,T)
    source=robot_source_meshes(m);robot=trimesh.collision.CollisionManager();body_ids={}
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
    # Normalize all mimic joints before freezing this hypothetical posture.
    mimic(m,d);mujoco.mj_forward(m,d)
    initial=d.qpos.copy();home=initial[ik.qa].copy()
    reach_seed=np.clip([-.8,-.4,0,1.4,0,0,0],ik.low,ik.high)
    initial_position=d.site('right_wrist_reference').xpos.copy();initial_R=d.site('right_wrist_reference').xmat.reshape(3,3).copy()
    baseline=collision(0.)
    baseline_pairs={tuple(sorted(p)) for p in baseline['self_contact']}
    baseline_transforms={n:(d.xpos[body_ids[n]].copy(),d.xmat[body_ids[n]].copy()) for pair in baseline_pairs for n in pair}
    if any(n.startswith('right_') and any(k in n for k in ['shoulder','elbow','wrist','thumb','index','middle','ring','little','palm','base_link']) for n in baseline_transforms):
        raise RuntimeError('Initial operating-arm collision requires repair')
    frozen_environment_pairs={tuple(p) for p in baseline['instrument_contact']}
    for pair in frozen_environment_pairs:
        name=next(n for n in pair if n in body_ids)
        if name.startswith('right_') and any(k in name for k in ['shoulder','elbow','wrist','thumb','index','middle','ring','little','palm','base_link']):
            raise RuntimeError('Initial operating-arm environment collision requires repair')
        baseline_transforms[name]=(d.xpos[body_ids[name]].copy(),d.xmat[body_ids[name]].copy())
    def additional_contacts(contacts):
        fixed=[];changed=[]
        for pair in contacts['self_contact']:
            if tuple(sorted(pair)) in baseline_pairs and all(np.max(abs(d.xpos[body_ids[n]]-baseline_transforms[n][0]))<1e-10 and np.max(abs(d.xmat[body_ids[n]]-baseline_transforms[n][1]))<1e-10 for n in pair):fixed.append(pair)
            else:changed.append(pair)
        external=[]
        for pair in contacts['instrument_contact']:
            name=next(n for n in pair if n in body_ids)
            if tuple(pair) in frozen_environment_pairs and np.max(abs(d.xpos[body_ids[name]]-baseline_transforms[name][0]))<1e-10 and np.max(abs(d.xmat[body_ids[name]]-baseline_transforms[name][1]))<1e-10:continue
            external.append(pair)
        return dict(self_contact=changed,instrument_contact=external),fixed
    environment_meshes=dict(architecture_meshes)
    for identity,path in [('nicolet',paths[5]),('pike',paths[6])]:
        scene=trimesh.load(path,force='scene',process=False)
        for n in scene.graph.nodes_geometry:
            full_name=identity+'::'+n
            if full_name in env._objs:
                _,key=scene.graph[n];environment_meshes[full_name]=scene.geometry[key]
    active_joints=[j for j in range(m.njnt) if m.joint(j).name.startswith('right_') and any(k in m.joint(j).name for k in ['shoulder','elbow','wrist','index','thumb','middle','ring','little'])]
    fast=SourceClearance(m,d,robot,source,env,environment_meshes,active_joints,adjacent,check_fixed_environment=False)
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
            d.qpos[ik.qa]=seed;mujoco.mj_forward(m,d);contacts,fixed=additional_contacts(collision(travel))
            if any(contacts.values()):failure=dict(kind='source_collision',travel_m=travel,**contacts);break
        rows.append(dict(candidate=index,endpoint_passed=failure is None,failure=failure,peak_ik_error=peak))
        if failure is None:accepted.append((index,c,target))
        if index%40==0:print('reach',index,'endpoint_passed',len(accepted),flush=True)
    def valid(q,hand_values,margin=.002):
        d.qpos[:]=initial;d.qpos[ik.qa]=q
        for n,v in hand_values.items():d.joint(n).qpos[0]=v
        mimic(m,d);mujoco.mj_forward(m,d)
        for n in slider:env.set_transform(n,rest[n])
        fast.update_environment()
        return fast.check(margin)['clear']
    regression=[];probe_rng=np.random.default_rng(3301)
    reference_hand=accepted[0][1]['q'] if accepted else search['candidates'][0]['q']
    probes=[home,reach_seed]+[np.clip(home+probe_rng.normal(size=7)*.8,ik.low,ik.high) for _ in range(10)]
    for q in probes:
        begin=time.monotonic();answer=valid(q,reference_hand);fast_seconds=time.monotonic()-begin
        begin=time.monotonic();contacts,fixed=additional_contacts(collision(0.))
        active_robot=trimesh.collision.CollisionManager()
        for n,g in zip(fast.names,fast.groups):
            if g:active_robot.add_object(n,source[n],get_transform(robot._objs[n]['obj']))
        expected=not any(contacts.values()) and active_robot.min_distance_other(env)>=.002
        slow_seconds=time.monotonic()-begin
        regression.append(dict(arm_q=q.tolist(),fast_clear=answer,full_source_clear=expected,fast_seconds=fast_seconds,full_source_seconds=slow_seconds))
        if answer!=expected:raise RuntimeError('Fast/source clearance disagreement')
    (HERE/'room_clearance_regression.json').write_text(json.dumps(dict(rows=regression,passed=True,scope='Bounded numerical cross-check plus conservative box containment, not dynamic qualification',baseline=baseline),indent=2)+'\n')
    print('clearance_regression',len(regression),'passed',flush=True)
    def plan_rrt(start,goal,hand_values,rng):
        checks=0;cache={}
        def free(q):
            nonlocal checks
            key=tuple(np.round(q,7))
            if key not in cache:cache[key]=valid(q,hand_values);checks+=1
            return cache[key]
        def edge(a,b,step=.035):
            return all(free(a+u*(b-a)) for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/step))+1)))
        if not free(start) or not free(goal):return None,dict(reason='endpoint',checks=checks)
        trees=[([start.copy()],[-1]),([goal.copy()],[-1])];flipped=False
        def extend(tree,q):
            nodes,parents=tree;idx=int(np.argmin([np.linalg.norm(x-q) for x in nodes]));a=nodes[idx];dist=np.linalg.norm(q-a)
            if dist<1e-9:return idx,True
            b=a+(q-a)*min(1.,.18/dist)
            if not edge(a,b):return None,False
            nodes.append(b);parents.append(idx);return len(nodes)-1,dist<=.18
        def ancestry(tree,index):
            nodes,parents=tree;path=[]
            while index>=0:path.append(nodes[index]);index=parents[index]
            return path[::-1]
        path=None
        for it in range(1400):
            if it%100==0:print("rrt_iteration",it,"checks",checks,flush=True)
            sample=(goal if not flipped else start) if rng.random()<.15 else rng.uniform(ik.low,ik.high)
            ia,_=extend(trees[0],sample)
            if ia is not None:
                target_q=trees[0][0][ia]
                for _ in range(60):
                    ib,done=extend(trees[1],target_q)
                    if ib is None:break
                    if done:
                        path=ancestry(trees[0],ia)+ancestry(trees[1],ib)[-2::-1]
                        if flipped:path=path[::-1]
                        break
                if path is not None:break
            trees.reverse();flipped=not flipped
        if path is None:return None,dict(reason='search_exhausted',checks=checks)
        for _ in range(80):
            if len(path)<3:break
            a,b=sorted(rng.choice(len(path),2,replace=False))
            if b-a>1 and edge(path[a],path[b]):path=path[:a+1]+path[b:]
        for a,b in zip(path[:-1],path[1:]):
            if not edge(a,b,.008):return None,dict(reason='dense_review',checks=checks)
        return path,dict(checks=checks,vertices=len(path),iterations=it+1)
    full=[];rng=np.random.default_rng(7349)
    ordered=sorted(accepted,key=lambda item:(abs(item[1]['q']['right_thumb_1_joint']-.8),abs(item[1]['q']['right_thumb_2_joint']-.4),item[1]['q']['right_index_1_joint']))
    for index,c,target in ordered[:18]:
        d.qpos[:]=initial;seed=reach_seed.copy();finger0={n:float(d.joint(n).qpos[0]) for n in c['q']}
        outward=R@np.array(c['outward_surface_normal']);direction=R@np.array([0.,1.,0.])
        pre=target[:3,3]+outward*.020;end=target[:3,3]+direction*.07
        for n,v in c['q'].items():d.joint(n).qpos[0]=v
        mimic(m,d);entry,pe,re=ik.solve(d,pre,target[:3,:3],seed)
        failure=None;states=[]
        if pe>.003 or re>.035:
            full.append(dict(candidate=index,passed=False,failure=dict(phase='entry_ik',position_error_m=pe,rotation_error_rad=re),states=[]));continue
        for u in np.linspace(0,1,41):
            hand_values={n:finger0[n]+u*(v-finger0[n]) for n,v in c['q'].items()}
            if not valid(home,hand_values):failure=dict(phase='prepare_hand',fraction=float(u));break
        previous=pre;previous_travel=0.;seed=entry.copy()
        steps=[('align',target[:3,3],0.),('push',end,.07),('withdraw',end+outward*.030,.07),('clear_to_entry',pre,.07)]
        if not failure:
            for name,goal,travel in steps:
                for u in np.linspace(0,1,61):
                    blend=3*u*u-2*u*u*u;position=previous+blend*(goal-previous)
                    d.qpos[:]=initial
                    for n,v in c['q'].items():d.joint(n).qpos[0]=v
                    mimic(m,d);seed,pe,re=ik.solve(d,position,target[:3,:3],seed)
                    if pe>.003 or re>.035:failure=dict(phase=name,fraction=float(u),kind='ik',position_error_m=pe,rotation_error_rad=re);break
                    d.qpos[ik.qa]=seed;mujoco.mj_forward(m,d)
                    contacts,fixed=additional_contacts(collision(previous_travel+blend*(travel-previous_travel)))
                    if any(contacts.values()):failure=dict(phase=name,fraction=float(u),kind='source_collision',**contacts);break
                    states.append(dict(phase=name,fraction=float(u),arm_q=seed.tolist()))
                if failure:break
                previous,previous_travel=goal,travel
        path=None;planning=None
        if not failure:
            path,planning=plan_rrt(home,entry,c['q'],rng)
            if path is None:failure=dict(phase='free_space_entry',planner=planning)
        full.append(dict(candidate=index,passed=failure is None,failure=failure,states=states,
                         entry_arm_q=entry.tolist(),arm_path=None if path is None else [q.tolist() for q in path],
                         planner=planning,entry_normal_offset_m=.020,withdraw_normal_offset_m=.030,
                         return_path_not_yet_checked=True))
        print('rrt_path',index,'passed',failure is None,'failure',failure,'planner',planning,flush=True)
        if path is not None:break
    deps=paths+[HERE/'source_proximity_room.py',Path(__file__),HERE/'fit_push.py',HERE/'review.json',LOADER,BASE/'robot_source_meshes.py',BASE/'observations.py',BASE/'ftir_hand.py',BASE/'ftir_cover_geometry.py',VIEW/'source_geometry.py',RUN/'sensor_observations.npz',RUN/'actor_responses.json',RUN/'policy_source/cover_grasp_prior.json',RUN/'controller_model/world.xml']
    report=dict(scope=__doc__,rows=rows,full_paths=full,passed_endpoint_candidates=len(accepted),
                passed_entry_and_contact_paths=sum(x['passed'] for x in full),source_registration=dict(rotation=R.tolist(),translation=t.tolist()),
                source_slider_grip_center_m=source_center.tolist(),port_to_observed_mapping=mapping.tolist(),
                fast_clearance_metrics=fast.metrics(),clearance_regression=regression,
                source_hashes={str(p.relative_to(ROOT)):sha(p) for p in deps},seconds=time.monotonic()-started,
                physical_execution=False,whole_laboratory_checked=False,public_architecture_meshes_checked=len(architecture_meshes),prepared_stance_execution_credit=False,
                baseline_source_intersections=baseline,whole_robot_source_clearance=not baseline["self_contact"],
                pass_scope="Forward entry and contact path only, return not checked; fixed lower-leg visual overlaps unresolved",
                hypothetical_stance_offset_m=[0.,.12],forward_ik_seed=reach_seed.tolist(),prepared_arm_q=home.tolist())
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(endpoints=len(accepted),full=report['passed_entry_and_contact_paths'],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
