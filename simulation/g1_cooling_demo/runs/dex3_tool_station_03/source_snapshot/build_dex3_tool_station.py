"""Place official Unitree three-finger hands in the existing G1 tool station.

Only source wrist/hand subtrees change. The full room, passive tool and free tray
are retained. All poses are authored initial conditions, with no execution credit.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from build_tool_station import sha, numbers, pose
from ftir_hand import ArmIK

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = HERE / 'analysis/g1_dex3_comparison_01'


def replace_hands(xml):
    official = ET.parse(SOURCE/'g1_29dof_with_hand_rev_1_0.xml').getroot()
    urdf = ET.parse(SOURCE/'g1_29dof_with_hand_rev_1_0.urdf').getroot()
    before_bodies = {b.get('name'): ET.tostring(b.find('inertial')) for b in xml.iter('body') if b.find('inertial') is not None}
    removed = set(); mesh_names = set(); limits = {}
    for side in ['left','right']:
        name = side+'_wrist_yaw_link'
        old = xml.find(f".//body[@name='{name}']")
        parents = {c:p for p in xml.iter() for c in p}
        removed.update(b.get('name') for b in old.iter('body'))
        new = deepcopy(official.find(f".//body[@name='{name}']"))
        assert np.max(abs(np.fromstring(old.get('pos'),sep=' ')-np.fromstring(new.get('pos'),sep=' ')))<1e-12
        ET.SubElement(new,'site',name=side+'_wrist_reference',size='.002',rgba='0 0 0 0')
        for i,g in enumerate(new.iter('geom')):
            if g.get('mesh'):
                mesh_names.add(g.get('mesh'));g.set('mesh','dex3_'+g.get('mesh'))
            g.set('name',f'dex3_{side}_geom_{i}')
        for j in new.iter('joint'):
            n=j.get('name'); lim=urdf.find(f"joint[@name='{n}']/limit")
            low,high=np.fromstring(j.get('range'),sep=' ')
            low=max(low,float(lim.get('lower'))); high=min(high,float(lim.get('upper')))
            j.set('range',numbers([low,high])); limits[n]=dict(range=[low,high],effort_nm=float(lim.get('effort')),velocity_rad_s=float(lim.get('velocity')))
        parents[old].remove(old);parents[old].append(new)
    for name in sorted(mesh_names):
        m=deepcopy(official.find(f"asset/mesh[@name='{name}']")); m.set('name','dex3_'+name)
        m.set('file',str(SOURCE/'meshes'/m.get('file')));xml.find('asset').append(m)
    joints={j.get('name') for j in xml.iter('joint') if j.get('name')}
    sites={j.get('name') for j in xml.iter('site')}
    for section in ['actuator','equality','sensor']:
        node=xml.find(section)
        if node is None:continue
        for item in list(node):
            if any(item.get(k) and item.get(k) not in joints for k in ['joint','joint1','joint2']) or (item.get('site') and item.get('site') not in sites):
                node.remove(item)
    for name,lim in limits.items():
        if '_hand_' not in name:continue
        ET.SubElement(xml.find('actuator'),'motor',name=name+'_torque',joint=name,gear='1',ctrlrange=numbers([-lim['effort_nm'],lim['effort_nm']]))
        ET.SubElement(xml.find('sensor'),'jointpos',name=name+'_encoder',joint=name)
        ET.SubElement(xml.find('sensor'),'jointvel',name=name+'_velocity',joint=name)
    used={g.get('mesh') for g in xml.iter('geom') if g.get('mesh')}
    for mesh in list(xml.find('asset')):
        if mesh.tag=='mesh' and mesh.get('name') not in used:xml.find('asset').remove(mesh)
    after_bodies={b.get('name'):ET.tostring(b.find('inertial')) for b in xml.iter('body') if b.find('inertial') is not None}
    preserved={n:after_bodies.get(n)==value for n,value in before_bodies.items() if n not in removed}
    assert all(preserved.values())
    return dict(source_joint_limits=limits,unchanged_body_inertias=len(preserved),replaced_bodies=sorted(removed),
                source_wrist_hand_inertias_preserved=True,official_collision_geometry_preserved=True,
                contact_defaults='Official unspecified hand friction/compliance inherit MuJoCo defaults; not hardware calibrated')


def run(station, fit, output, yaw_offsets=(0.,), candidate_indices=None, multistart=False):
    started=time.monotonic();station=Path(station).resolve();fit=Path(fit).resolve();out=Path(output).resolve()
    out.mkdir(parents=True,exist_ok=False);snapshot=out/'source_snapshot';snapshot.mkdir()
    for p in [Path(__file__),HERE/'build_tool_station.py',HERE/'ftir_hand.py']:
        shutil.copyfile(p,snapshot/p.name)
    original=json.loads((station/'contract.json').read_text());review=json.loads((station/'review.json').read_text())
    assert review['passed_initial_scene_checks'] and sha(station/'contract.json')==review['contract_sha256']
    assert sha(station/'world.xml')==original['plant_sha256']
    fits=json.loads(fit.read_text());assert sha(fit.parent/'contract.json')==fits['contract_sha256']
    parent=ET.parse(station/'world.xml').getroot()
    old_model=mujoco.MjModel.from_xml_path(str(station/'world.xml'));old_data=mujoco.MjData(old_model)
    old_data.qpos[:]=original['initial_qpos']
    unaffected=[b for b in list(parent.find('worldbody')) if b.get('name')!='pelvis']
    room_hashes={b.get('name',str(i)):sha_bytes(ET.tostring(b)) for i,b in enumerate(unaffected)}
    graft=replace_hands(parent)
    ET.indent(parent);ET.ElementTree(parent).write(out/'world.xml',encoding='unicode')
    predictor=ET.parse(station/'robot_predictor.xml').getroot();replace_hands(predictor)
    ET.indent(predictor);ET.ElementTree(predictor).write(out/'robot_predictor.xml',encoding='unicode')
    m=mujoco.MjModel.from_xml_path(str(out/'world.xml'));d=mujoco.MjData(m)
    rm=mujoco.MjModel.from_xml_path(str(out/'robot_predictor.xml'));rd=mujoco.MjData(rm)
    assert m.nu==rm.nu==43 and rm.neq==0
    for j in range(m.njnt):
        n=m.joint(j).name;old=mujoco.mj_name2id(old_model,mujoco.mjtObj.mjOBJ_JOINT,n)
        if old>=0:d.joint(n).qpos[:]=old_data.joint(n).qpos
    for n,v in dict(left_hand_thumb_0_joint=0.,left_hand_thumb_1_joint=.3,left_hand_thumb_2_joint=1.,
                    left_hand_index_0_joint=-1.,left_hand_index_1_joint=-1.2,
                    left_hand_middle_0_joint=-1.,left_hand_middle_1_joint=-1.2).items(): d.joint(n).qpos[0]=v
    initial=d.qpos.copy()
    world_from_source=pose(d.joint('tweezer_free').qpos)
    world_from_source[:3,3]-=world_from_source[:3,:3]@np.array([.13,0,.00575])
    ik=ArmIK(rm);rows=[];accepted=[]
    for index,candidate in enumerate(fits['candidates']):
        if candidate_indices is not None and index not in candidate_indices:continue
        target=world_from_source@np.asarray(candidate['source_tool_from_wrist'])
        for dx,dy,yaw in [(dx,dy,yaw) for dx,dy in [(0.,0.),(-.15,0.),(.15,0.),(0.,-.15),(0.,.15)] for yaw in yaw_offsets]:
            d.qpos[:]=initial;d.qpos[:2]+=[dx,dy]
            orientation=(Rotation.from_euler('z',yaw,degrees=True)*Rotation.from_quat(np.r_[initial[4:7],initial[3]])).as_quat()
            d.qpos[3:7]=np.r_[orientation[3],orientation[:3]]
            for n,v in candidate['q'].items():d.joint(n).qpos[0]=v
            for j in range(rm.njnt):rd.joint(rm.joint(j).name).qpos[:]=d.joint(rm.joint(j).name).qpos
            seeds=[rd.qpos[ik.qa].copy()]
            if multistart:seeds += [np.clip(q,ik.low,ik.high) for q in
                [[-.6,-.4,-1.5,1.2,1.5,0,0],[-.6,-.5,0,1.2,-1.5,0,0],[-1.,-.3,1.5,1.5,1.,0,0]]]
            solutions=[ik.solve(rd,target[:3,3],target[:3,:3],seed) for seed in seeds]
            arm,pe,re=min(solutions,key=lambda r:r[1]+.15*r[2])
            d.qpos[[m.jnt_qposadr[m.joint(rm.joint(j).name).id] for j in ik.joints]]=arm
            bad=[]
            if pe<.0003 and re<.005:
                mujoco.mj_forward(m,d)
                for c in d.contact:
                    names=[m.geom(int(g)).name for g in c.geom]
                    bound=.001 if any('ankle_roll_link_collision' in (n or '') for n in names) else .00025 if any('tray_contact' in (n or '') or 'steel_arm' in (n or '') for n in names) else .00002
                    if c.dist < -bound:bad.append(dict(parts=names,distance_m=float(c.dist),bound_m=bound))
            passed=pe<.0003 and re<.005 and not bad
            row=dict(candidate_index=index,base_offset_m=[dx,dy],base_yaw_offset_deg=yaw,position_error_m=pe,rotation_error_rad=re,
                     excessive_contacts=bad,passed_static=passed,arm_q=arm.tolist())
            rows.append(row)
            if passed: accepted.append(dict(**row,initial_qpos=d.qpos.tolist(),target_world_wrist=target.tolist()))
        if index%5==0:print('candidate',index,'static candidates',len(accepted),flush=True)
    inputs={str(Path(n.get('file')).resolve()):sha(n.get('file')) for tag in ['mesh','texture','hfield'] for n in parent.findall('asset/'+tag) if n.get('file')}
    (out/'model_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    contract=dict(scope=__doc__,station_contract_sha256=sha(station/'contract.json'),fit_sha256=sha(fit),
                  source_model_sha256=sha(SOURCE/'g1_29dof_with_hand_rev_1_0.xml'),source_urdf_sha256=sha(SOURCE/'g1_29dof_with_hand_rev_1_0.urdf'),
                  source_snapshot_sha256={p.name:sha(p) for p in snapshot.iterdir()},graft=graft,
                  unchanged_room_body_hashes=room_hashes,plant_sha256=sha(out/'world.xml'),predictor_sha256=sha(out/'robot_predictor.xml'),
                  model_inputs_sha256=sha(out/'model_inputs.json'),authored_original_initial_qpos=initial.tolist(),
                  tool_source_frame_world=world_from_source.tolist(),selected_initial_condition_is_not_execution=True,
                  yaw_offsets_deg=list(yaw_offsets),candidate_indices=candidate_indices,multistart=multistart,
                  actuators=m.nu,robot_nq=rm.nq,robot_nv=rm.nv,source_visual_joint_overlap_disclosed_in_fit=True)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    (out/'review.json').write_text(json.dumps(dict(scope=__doc__,tested=len(rows),rows=rows,candidates=accepted,
        passed_static_candidates=len(accepted),contract_sha256=sha(out/'contract.json'),seconds=time.monotonic()-started,
        qualified_grasp=False,qualified_branch=False),indent=2)+'\n')
    print(json.dumps(dict(tested=len(rows),accepted=len(accepted),seconds=time.monotonic()-started)),flush=True)


def sha_bytes(value):
    import hashlib
    return hashlib.sha256(value).hexdigest()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--station',required=True);p.add_argument('--fit',required=True);p.add_argument('--out',required=True)
    p.add_argument('--yaw-offsets',type=float,nargs='+',default=[0.]);p.add_argument('--candidate-indices',type=int,nargs='+')
    p.add_argument('--multistart',action='store_true')
    a=p.parse_args();run(a.station,a.fit,a.out,a.yaw_offsets,a.candidate_indices,a.multistart)
