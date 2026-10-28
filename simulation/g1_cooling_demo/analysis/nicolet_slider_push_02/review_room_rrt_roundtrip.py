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
    started=time.monotonic();out=HERE/'room_rrt_roundtrip.json'
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
    report=json.loads((HERE/'room_rrt.json').read_text())
    for path,expected in report['source_hashes'].items():
        if sha(ROOT/path)!=expected:raise ValueError('Planning dependency changed: '+path)
    plan=next(p for p in report['full_paths'] if p['passed'])
    candidate=search['candidates'][plan['candidate']]
    qhand=candidate['q'];initial_hand={n:float(d.joint(n).qpos[0]) for n in qhand}
    rows=[]
    def check(phase,q,hand,travel):
        d.qpos[:]=initial;d.qpos[ik.qa]=q
        for n,v in hand.items():d.joint(n).qpos[0]=v
        mimic(m,d);mujoco.mj_forward(m,d)
        contacts,fixed=additional_contacts(collision(travel))
        # Free-space retreat retains the same 2 mm instrument clearance.
        fast.update_environment();answer=fast.check(.002)
        passed=not any(contacts.values()) and answer['clear']
        rows.append(dict(phase=phase,arm_q=q.tolist(),passed=passed,source_contacts=contacts,proximity=answer))
        return passed
    path=[np.array(plan['states'][-1]['arm_q']), *[np.array(q) for q in plan['arm_path'][::-1]]]
    for edge,(a,b) in enumerate(zip(path[:-1],path[1:])):
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.008))+1)):
            check('return_edge_'+str(edge),a+u*(b-a),qhand,.07)
    for u in np.linspace(0,1,101):
        check('release_hand_at_home',home,{n:qhand[n]+u*(initial_hand[n]-qhand[n]) for n in qhand},.07)
    result=dict(candidate=plan['candidate'],passed=all(r['passed'] for r in rows),checked_states=len(rows),
                rows=rows,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'room_rrt.json',HERE/'source_proximity_room.py']},
                baseline_source_intersections=baseline,whole_robot_source_clearance=False,whole_laboratory_checked=False,
                physical_execution=False,prepared_stance_execution_credit=False,
                scope='Reverse arm path and hand release with slider geometrically moved 70 mm. No force or actual slider motion is assumed proven.',
                seconds=time.monotonic()-started)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','candidate','checked_states','seconds']}),flush=True)

if __name__=='__main__':main()
