"""Screen Dex3 cover opening reach using retained robot sensors and source CAD.

The laboratory placement is registered from saved RGB-D feature observations.
The body posture is estimated from encoders/IMU and the authored foot anchors.
No recorded instrument pose or hinge state enters this hypothetical 0..60 deg
path. This excludes approach, dynamic balance, closed-loop grip and room checks.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from fit_cover_grasp import HERE, ROOT, NAMES, SourceHand, digest, handle_mesh

BASE=ROOT/'simulation/g1_cooling_demo'
RUN=BASE/'runs/ftir_cover_13'
sys.path.insert(0,str(RUN/'source_snapshot'))
from observations import StateEstimate
from ftir_hand import initialize_cover,ArmIK


def run(seed,out,dx,dy,forward_arm,fold_left,fixed_wrist):
    started=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    old=mujoco.MjModel.from_xml_path(str(RUN/'controller_model/world.xml'))
    old.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
    estimated=initialize_cover(old,[5.95,-5.32]);estimator=StateEstimate(old,estimated)
    sensors=np.load(RUN/'sensor_observations.npz');i=int(np.argmin(abs(sensors['time_s']-2)))
    packet={k:sensors[k][i] for k in sensors.files if k!='right_touch_n'};packet['depth']=None;estimator.update(packet)
    responses=json.loads((RUN/'actor_responses.json').read_text())
    observations=[r['observation'] for r in responses if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
    if len(observations)<8:raise ValueError('Not enough retained accepted RGB-D observations')
    prior_path=RUN/'policy_source/cover_grasp_prior.json';prior=json.loads(prior_path.read_text())
    observed=np.median([[o['buttons'][k['label']] for k in prior['keys']] for o in observations],axis=0)
    normal=np.mean([o['outward_normal'] for o in observations],axis=0);normal/=np.linalg.norm(normal)
    row=observed[-1]-observed[0];row-=row.dot(normal)*normal;row/=np.linalg.norm(row)
    known_normal=-np.array(prior['keys'][0]['inward_axis'])
    basis=lambda r,n:np.column_stack([r,np.cross(n,r),n])
    rotation=basis(row,normal)@basis(np.array([1.,0,0]),known_normal).T
    handle=np.median([o['handle_fit']['handle_m'] for o in observations],axis=0)
    _,device_path,source_handle=handle_mesh();registration=np.eye(4);registration[:3,:3]=rotation;registration[:3,3]=handle-rotation@source_handle
    source_pivot=np.array(prior['hinge_pivot_m']);source_axis=np.array(prior['hinge_axis'])
    xml=ET.parse(HERE/'g1_29dof_with_hand_rev_1_0.xml').getroot()
    xml.find('compiler').set('meshdir',str(HERE/'meshes'))
    urdf=ET.parse(HERE/'g1_29dof_with_hand_rev_1_0.urdf').getroot();bounds=[]
    for joint in xml.findall('.//joint[@range]'):
        spec=urdf.find(f"joint[@name='{joint.get('name')}']/limit")
        if spec is None:continue
        lo,hi=np.fromstring(joint.get('range'),sep=' ');lo=max(lo,float(spec.get('lower')));hi=min(hi,float(spec.get('upper')))
        joint.set('range',f'{lo:.12g} {hi:.12g}');bounds.append(joint.get('name'))
    ET.SubElement(xml.find(".//body[@name='right_wrist_yaw_link']"),'site',name='right_wrist_reference',pos='0 0 0',size='.003')
    path=out/'robot.xml';ET.indent(xml);ET.ElementTree(xml).write(path,encoding='unicode')
    model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model);data.qpos[:7]=estimated.qpos[:7]
    copied=[]
    for j in range(model.njnt):
        if model.jnt_type[j]!=mujoco.mjtJoint.mjJNT_HINGE:continue
        name=model.joint(j).name;old_id=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_JOINT,name)
        if old_id>=0:data.qpos[model.jnt_qposadr[j]]=estimated.qpos[old.jnt_qposadr[old_id]];copied.append(name)
    data.qpos[:2]+=[dx,dy]
    left_posture={}
    if fold_left:
        left_posture=dict(left_shoulder_roll_joint=.45,left_hand_thumb_0_joint=0.,
                          left_hand_thumb_1_joint=.3,left_hand_thumb_2_joint=1.,
                          left_hand_index_0_joint=-1.,left_hand_index_1_joint=-1.2,
                          left_hand_middle_0_joint=-1.,left_hand_middle_1_joint=-1.2)
        for n,v in left_posture.items():
            if not model.joint(n).range[0]<=v<=model.joint(n).range[1]:raise ValueError(n)
            data.joint(n).qpos[0]=v
    mujoco.mj_forward(model,data);ik=ArmIK(model);home_arm=data.qpos[ik.qa].copy()
    if forward_arm:home_arm=np.clip([-.8,-.4,0,1.4,0,0,0],ik.low,ik.high)
    # Inspect each native hull collision against the actual source triangles.
    # A native false positive remains a runtime model defect, not physics credit.
    source_objects=trimesh.collision.CollisionManager();source_transforms={}
    for body in xml.findall('.//body'):
        for geom in body.findall("geom[@group='1'][@mesh]"):
            name=geom.get('mesh');mesh=trimesh.load(HERE/'meshes'/xml.find(f"asset/mesh[@name='{name}']").get('file'),force='mesh')
            local=np.eye(4);local[:3,3]=np.fromstring(geom.get('pos','0 0 0'),sep=' ')
            values=np.zeros(9);mujoco.mju_quat2Mat(values,np.fromstring(geom.get('quat','1 0 0 0'),sep=' '));local[:3,:3]=values.reshape(3,3)
            source_transforms[name]=(int(model.body(body.get('name')).id),local);source_objects.add_object(name,mesh)
    def raw_collision(ga,gb):
        names=[]
        for geom in [ga,gb]:
            if model.geom_type[geom]!=mujoco.mjtGeom.mjGEOM_MESH:return None
            name=model.mesh(model.geom_dataid[geom]).name
            if name not in source_transforms:return None
            bid,local=source_transforms[name];T=np.eye(4);T[:3,:3]=data.xmat[bid].reshape(3,3);T[:3,3]=data.xpos[bid]
            source_objects.set_transform(name,T@local);names.append(name)
        import fcl
        result=fcl.CollisionResult();fcl.collide(source_objects._objs[names[0]]['obj'],source_objects._objs[names[1]]['obj'],fcl.CollisionRequest(),result)
        return bool(result.is_collision)
    hand=SourceHand();scene=trimesh.load(device_path,force='scene',process=False)
    instrument=trimesh.collision.CollisionManager();rest={}
    for name in scene.graph.nodes_geometry:
        T,key=scene.graph[name];rest[name]=T;instrument.add_object(name,scene.geometry[key],T)
    interfaces=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    moving=set(next(r for r in interfaces['interfaces'] if r['id']=='sample_cover')['parts'])
    candidates=json.loads(Path(seed).read_text())['candidates'];rows=[];paths={}
    for index,candidate in enumerate(candidates):
        wrist=np.array(candidate['instrument_frame_from_wrist']);q=[candidate['q'][n] for n in NAMES]
        poses=hand.forward(q)
        for n,v in candidate['q'].items():data.joint(n).qpos[0]=v
        arm_seed=home_arm.copy();peaks=[0.,0.];failure=None;states=[];false_contacts=[]
        for degrees in np.linspace(0,60,31):
            rot=Rotation.from_rotvec(-source_axis*np.deg2rad(degrees)).as_matrix()
            hinge=np.eye(4);hinge[:3,:3]=rot;hinge[:3,3]=source_pivot-rot@source_pivot
            wrist_moved=hinge@wrist
            if fixed_wrist:
                wrist_moved=wrist.copy()
                wrist_moved[:3,3]=source_pivot+rot@(source_handle-source_pivot)+(wrist[:3,3]-source_handle)
            target=registration@wrist_moved
            arm_seed,pe,re=ik.solve(data,target[:3,3],target[:3,:3],arm_seed);peaks=[max(peaks[0],pe),max(peaks[1],re)]
            if pe>.003 or re>.035:failure=dict(kind='arm_ik',degrees=float(degrees),position_error_m=pe,rotation_error_rad=re);break
            data.qpos[ik.qa]=arm_seed;mujoco.mj_forward(model,data)
            bad=[];checked=set()
            for c in data.contact:
                if c.dist < -2e-5:
                    pair=tuple(sorted(map(int,c.geom)))
                    if pair in checked:continue
                    checked.add(pair);raw=raw_collision(*pair)
                    record=dict(parts=[model.geom(int(g)).name or model.body(model.geom_bodyid[int(g)]).name for g in c.geom],distance_m=float(c.dist),raw_source_intersection=raw)
                    if raw is False:false_contacts.append(dict(degrees=float(degrees),**record))
                    else:bad.append(record)
            if bad:failure=dict(kind='native_robot_collision',degrees=float(degrees),contacts=bad);break
            for name in moving:instrument.set_transform(name,hinge@rest[name])
            for name,pose in poses.items():hand.manager.set_transform(name,wrist_moved@pose)
            _,pairs=hand.manager.in_collision_other(instrument,return_names=True)
            if pairs:failure=dict(kind='hand_instrument_collision',degrees=float(degrees),pairs=[list(p) for p in sorted(pairs)]);break
            states.append(dict(degrees=float(degrees),arm_q=arm_seed.tolist(),target_world=target.tolist()))
        rows.append(dict(candidate_index=index,source_trial=candidate['source_trial'],roll_deg=candidate['roll_deg'],
                         passed=failure is None,failure=failure,max_position_error_m=peaks[0],max_rotation_error_rad=peaks[1]))
        rows[-1]['native_false_contacts']=false_contacts
        rows[-1]['native_model_path_passed']=failure is None and not false_contacts
        if failure is None:paths[str(index)]=states
        if index%25==0:print('candidate',index,'passed',len(paths),flush=True)
    report=dict(scope=__doc__,rows=rows,paths=paths,passed_candidates=len(paths),
                sensor_time_s=float(sensors['time_s'][i]),registration_from_observations=registration.tolist(),
                estimated_initial_root_qpos=estimated.qpos[:7].tolist(),copied_encoder_joints=copied,
                hypothetical_stance_offset_m=[dx,dy],authored_left_posture=left_posture,
                wrist_orientation_policy='fixed_world_orientation_round_bar_rolls' if fixed_wrist else 'rigidly_follow_cover_rotation',
                initial_arm_solver_seed=home_arm.tolist(),stance_or_posture_execution_credit=False,
                source_limit_intersections=bounds,source_sensor_sha256=digest(RUN/'sensor_observations.npz'),
                source_observations_sha256=digest(RUN/'actor_responses.json'),prior_sha256=digest(prior_path),
                candidate_sha256=digest(seed),builder_sha256=digest(__file__),robot_sha256=digest(path),
                dependency_sha256={p.name:digest(p) for p in [HERE/'fit_cover_grasp.py',RUN/'source_snapshot/observations.py',RUN/'source_snapshot/ftir_hand.py']},
                seconds=time.monotonic()-started,physics_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(rows),passed_candidates=len(paths),seconds=report['seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',required=True);p.add_argument('--out',required=True)
    p.add_argument('--dx',type=float,default=0);p.add_argument('--dy',type=float,default=0)
    p.add_argument('--forward-arm',action='store_true');p.add_argument('--fold-left',action='store_true')
    p.add_argument('--fixed-wrist',action='store_true')
    a=p.parse_args();run(a.seed,a.out,a.dx,a.dy,a.forward_arm,a.fold_left,a.fixed_wrist)
