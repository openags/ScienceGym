"""Independent retained-world source-triangle check of the hypothetical path.

The full laboratory is available to this reviewer, never to the actor. Slider
travel is imposed here solely to inspect the intended geometry; it is not an
execution trace and earns no motor, walking, contact or paper-branch credit.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
sys.path.insert(0,str(BASE))
from ftir_hand import initialize_cover, ArmIK, mimic
from observations import StateEstimate,robot_joints
from robot_source_meshes import robot_source_meshes


def main():
    started=time.monotonic()
    out=HERE/'sensor_room_review.json'
    if out.exists():raise FileExistsError(out)
    run=BASE/'runs/ftir_slider_scan_02'
    report=json.loads((HERE/'sensor_plan.json').read_text());plan=report['plan']
    candidate=dict(q=plan['candidate']['hand_q'])
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    cd=mujoco.MjData(cm);cd.qpos[:]=report['estimated_initial_qpos']
    ik=ArmIK(cm);mimic(cm,cd);mujoco.mj_forward(cm,cd)
    initial=cd.qpos.copy()
    hand0={n:float(cd.joint(n).qpos[0]) for n in candidate['q']}
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    # Geometry reviewer only. Compiling contact constraints at every source
    # triangle query is redundant; no physical integration occurs here.
    m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    d=initialize_cover(m,[5.95,-5.20])
    source=robot_source_meshes(m)
    ids={n:m.body(n).id for n in source}
    robot=trimesh.collision.CollisionManager()
    for n,mesh in source.items():robot.add_object(n,mesh)
    robot_bodies=set()
    for b in range(m.nbody):
        a=b
        while a and m.body(a).name!='pelvis':a=int(m.body_parentid[a])
        if a:robot_bodies.add(b)
    environment=trimesh.collision.CollisionManager();environment_geoms={};moving=[]
    for g in range(m.ngeom):
        bid=int(m.geom_bodyid[g])
        if bid in robot_bodies or m.geom_group[g]!=2:continue
        if m.geom_type[g]!=mujoco.mjtGeom.mjGEOM_MESH:raise ValueError('Unexpected room source primitive')
        mid=m.geom_dataid[g];va,vn=m.mesh_vertadr[mid],m.mesh_vertnum[mid];fa,fn=m.mesh_faceadr[mid],m.mesh_facenum[mid]
        mesh=trimesh.Trimesh(vertices=m.mesh_vert[va:va+vn],faces=m.mesh_face[fa:fa+fn],process=False)
        n=m.geom(g).name;T=np.eye(4);T[:3,:3]=d.geom_xmat[g].reshape(3,3);T[:3,3]=d.geom_xpos[g]
        environment.add_object(n,mesh,T);environment_geoms[n]=g
        if m.body(bid).name=='nicolet_sliding_door':moving.append(n)
    slide=[j for j in range(m.njnt) if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_SLIDE]
    slide=next(j for j in slide if m.body(m.jnt_bodyid[j]).name=='nicolet_sliding_door')
    mapping={n:m.jnt_qposadr[m.joint(n).id] for n in [cm.joint(j).name for j in robot_joints(cm)]}
    def apply(q,hand,travel):
        cd.qpos[:]=initial;cd.qpos[ik.qa]=q
        for n,v in hand.items():cd.joint(n).qpos[0]=v
        mimic(cm,cd)
        d.qpos[:7]=cd.qpos[:7]
        for n,qa in mapping.items():d.qpos[qa]=cd.joint(n).qpos[0]
        d.qpos[m.jnt_qposadr[slide]]=travel;mujoco.mj_forward(m,d)
        for n,b in ids.items():
            T=np.eye(4);T[:3,:3]=d.xmat[b].reshape(3,3);T[:3,3]=d.xpos[b];robot.set_transform(n,T)
        for n in moving:
            g=environment_geoms[n];T=np.eye(4);T[:3,:3]=d.geom_xmat[g].reshape(3,3);T[:3,3]=d.geom_xpos[g];environment.set_transform(n,T)
    apply(initial[ik.qa],hand0,0.)
    _,pairs=robot.in_collision_other(environment,return_names=True)
    baseline=set(pairs)
    baseline_poses={n:(d.xpos[ids[n]].copy(),d.xmat[ids[n]].copy()) for n,_ in baseline}
    failures=[];states=[];phases=Counter()
    def check(phase,q,hand,travel):
        apply(q,hand,travel);_,pairs=robot.in_collision_other(environment,return_names=True)
        changed=[p for p in pairs if p not in baseline or p[1] in moving or
                 np.max(abs(d.xpos[ids[p[0]]]-baseline_poses[p[0]][0]))>1e-10 or
                 np.max(abs(d.xmat[ids[p[0]]]-baseline_poses[p[0]][1]))>1e-10]
        row=dict(phase=phase,arm_q=np.asarray(q).tolist(),slider_travel_m=float(travel),source_pairs=sorted(changed))
        states.append(row);phases[phase]+=1
        if changed:failures.append(row)
    for u in np.linspace(0,1,101):check('prepare_hand',initial[ik.qa],{n:hand0[n]+u*(v-hand0[n]) for n,v in candidate['q'].items()},0.)
    path=np.array(plan['entry_path'])
    for a,b in zip(path[:-1],path[1:]):
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.008))+1)):
            check('entry',a+u*(b-a),candidate['q'],0.)
    for state in plan['contact_states']:
        name,u=state['phase'],state['fraction']
        travel=0. if name=='align' else .07*(3*u*u-2*u*u*u) if name=='push' else .07
        check(name,state['arm_q'],candidate['q'],travel)
    reverse=[np.array(plan['contact_states'][-1]['arm_q']),*path[::-1]]
    for a,b in zip(reverse[:-1],reverse[1:]):
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.008))+1)):
            check('return',a+u*(b-a),candidate['q'],.07)
    for u in np.linspace(0,1,101):check('release_hand',initial[ik.qa],{n:v+u*(hand0[n]-v) for n,v in candidate['q'].items()},.07)
    print('reviewed',len(states),'states',len(failures),'failures',flush=True)
    deps=[Path(__file__),BASE/'robot_source_meshes.py',HERE/'sensor_plan.json',run/'world.xml',run/'sensor_observations.npz']
    result=dict(scope=__doc__,candidate=plan['candidate']['id'],source_environment_meshes=len(environment_geoms),
                changed_source_intersections_clear=not failures,baseline_source_intersections=sorted(baseline),
                whole_laboratory_source_clearance=not baseline and not failures,
                phases=dict(phases),checked_states=len(states),failures=failures,states=states,
                physics_qualified=False,baseline_robot_self_intersections=plan['baseline'],
                source_hashes={str(p.relative_to(BASE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                seconds=time.monotonic()-started)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['whole_laboratory_source_clearance','checked_states','source_environment_meshes','seconds']}),flush=True)


if __name__=='__main__':main()
