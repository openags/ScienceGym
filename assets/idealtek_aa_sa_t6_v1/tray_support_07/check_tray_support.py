"""Check a free tweezer leaning on an ordinary, freely resting laboratory tray.

The authored initial placement uses the existing Buerkle tray rim and bench.
Both objects remain free under gravity. This checks support only, not robot
placement, cleanliness, hand access, pickup, or a paper manipulation task.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.optimize import brentq
from scipy.spatial.transform import Rotation
import trimesh

ROOT=Path(__file__).resolve().parents[2]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def numbers(v):return ' '.join(format(float(x),'.17g') for x in v)


def run(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,output/Path(__file__).name)
    original=ROOT/'simulation/g1_cooling_demo/runs/laboratory_isolated_tool_01/world.xml'
    old=ET.parse(original).getroot()
    meshroot=(original.parent/old.find('compiler').get('meshdir')).resolve()
    tray=deepcopy(old.find(".//body[@name='carrier_tray']"))
    assert tray is not None and tray.find('freejoint') is not None
    scene=trimesh.load(source/'rest_geometry.glb',force='scene',process=False)
    vertices=[];heel=[]
    for name in scene.graph.nodes_geometry:
        tf,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(tf)
        vertices.append(mesh.vertices)
        if not name.startswith(('negative_','positive_')):heel.append(mesh.vertices)
    vertices=np.concatenate(vertices);heel=np.concatenate(heel)
    def rotation(angle):return Rotation.from_euler('y',-angle).as_matrix()@Rotation.from_euler('x',np.pi/2).as_matrix()
    def rise(a):
        r=rotation(a);return float((heel@r[2]).min()-(vertices@r[2]).min())
    angle=brentq(lambda a:rise(a)-.050001,.2,.6);rot=rotation(angle)
    tool_origin=np.array([0.,0.,.000201-(vertices@rot[2]).min()])
    heel_world=heel@rot.T+tool_origin
    lowest=heel_world[heel_world[:,2]<heel_world[:,2].min()+1e-8]
    tray_origin=np.array([lowest[:,0].mean()+.1494,heel_world[:,1].mean(),.000001])
    tray.set('pos',numbers(tray_origin));tray.set('quat','1 0 0 0')
    xml=ET.parse(source/'tool.xml').getroot()
    # Tool defaults must not become defaults of a newly imported carrier.
    # In particular, inheriting the tool's priority=1 made the tray's
    # larger friction coefficients override the tool's contact choice.
    default=xml.find('default')
    children=list(default)
    for child in children:default.remove(child)
    tool_default=ET.SubElement(default,'default',{'class':'passive_tool'})
    for child in children:tool_default.append(child)
    xml.find("worldbody/body[@name='tweezer']").set('childclass','passive_tool')
    xml.find('compiler').set('inertiafromgeom','auto');xml.find('compiler').attrib.pop('meshdir',None)
    xml.find('option').set('gravity','0 0 -9.81')
    for n in xml.find('asset'):
        if n.get('file'):n.set('file',str(source/'meshes'/n.get('file')))
    meshes={g.get('mesh') for g in tray.iter('geom')}
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [original,source/'tool.xml',source/'rest_geometry.glb',Path(__file__)]}
    for n in old.find('asset'):
        if n.get('name') in meshes:
            copied=deepcopy(n);path=(meshroot/n.get('file')).resolve();assert path.exists()
            copied.set('file',str(path));xml.find('asset').append(copied)
            source_hashes[str(path.relative_to(ROOT))]=sha(path)
    world=xml.find('worldbody');world.append(tray)
    ET.SubElement(world,'geom',name='bench',type='plane',size='.6 .4 .01',rgba='.45 .48 .50 1',
                  friction='.225 .002 .0001',solref='.001 1',solimp='.9999 .9999 .00001')
    ET.SubElement(world,'light',pos='0 -.2 .6',dir='0 .2 -1')
    ET.indent(xml);ET.ElementTree(xml).write(output/'support.xml',encoding='unicode')
    m=mujoco.MjModel.from_xml_path(str(output/'support.xml'));d=mujoco.MjData(m)
    original_model=mujoco.MjModel.from_xml_path(str(original))
    attributes=['geom_priority','geom_condim','geom_friction','geom_solref','geom_solimp',
                'geom_margin','geom_gap','geom_contype','geom_conaffinity','geom_group']
    preservation={}
    for geom in tray.iter('geom'):
        name=geom.get('name');before=original_model.geom(name).id;after=m.geom(name).id
        preservation[name]={attr:bool(np.array_equal(getattr(original_model,attr)[before],getattr(m,attr)[after]))
                            for attr in attributes}
    (output/'tray_parameter_preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    assert all(all(v.values()) for v in preservation.values()),'Imported tray contact defaults changed'
    assert m.nu==0 and m.neq==0
    tool_joint=m.joint('tweezer_free');tray_joint=m.joint('tray_free')
    tq=int(tool_joint.qposadr[0]);tv=int(tool_joint.dofadr[0]);rq=int(tray_joint.qposadr[0]);rv=int(tray_joint.dofadr[0])
    d.qpos[tq:tq+3]=tool_origin+rot@np.array([.13,0,.00575])
    q=Rotation.from_matrix(rot).as_quat();d.qpos[tq+3:tq+7]=np.r_[q[3],q[:3]]
    mujoco.mj_forward(m,d)
    bench=m.geom('bench').id;tray_body=m.body('carrier_tray').id
    tool_bodies=set(range(m.nbody))-{0,tray_body}
    initial=d.qpos.copy()
    contract=dict(scope=__doc__,duration_s=3.,settled_interval_s=[2.5,3.],
        angle_rad=angle,tool_source_origin_m=tool_origin.tolist(),tray_origin_m=tray_origin.tolist(),
        initial_qpos=initial.tolist(),timestep_s=float(m.opt.timestep),source_hashes=source_hashes,
        plant_sha256=sha(output/'support.xml'),tray_dimensions_preserved=True,tray_inertial_preserved=True,
        tray_contact_parameter_review_sha256=sha(output/'tray_parameter_preservation.json'),
        inferred_contact_parameters='Retained tool/bench/tray simulation parameters, not calibrated hardware coefficients',
        checks=dict(maximum_penetration_m=.00025,maximum_unexpected_penetration_m=.00002,
                    maximum_settled_linear_speed_m_s=.001,maximum_settled_angular_speed_rad_s=.01,
                    maximum_tool_displacement_m=.005,maximum_tray_displacement_m=.001,
                    maximum_relative_vertical_load_error=.05,
                    minimum_tool_tray_support_vertical_load_n=.005,minimum_tool_bench_support_vertical_load_n=.005))
    contract['contact_force_convention']='mj_contactForce acts on geom[1]; transform from contact axes to world, then select the sign for the tool'
    contract['contact_force_reference']='https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-geom'
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    records=[];loads=[];violations=[];penetration=0.;external=False
    def state():return (float(d.time),d.qpos.copy(),d.qvel.copy(),d.qacc_warmstart.copy())
    for step in range(round(3./m.opt.timestep)):
        before=state();records.append(before);external|=bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        mujoco.mj_step(m,d);on_tray=on_bench=0.
        for i,c in enumerate(d.contact):
            gs=list(map(int,c.geom));bs=[int(m.geom_bodyid[g]) for g in gs];tool_side=[b in tool_bodies for b in bs]
            if bench in gs or (sum(tool_side)==1 and tray_body in bs):
                penetration=max(penetration,-float(c.dist))
                f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
                if sum(tool_side)==1:
                    vertical=float((c.frame.reshape(3,3).T@f[:3])[2])*(1. if tool_side[1] else -1.)
                    if tray_body in bs:on_tray+=vertical
                    if bench in gs:on_bench+=vertical
            elif c.dist<-.00002 and len(violations)<30:
                violations.append(dict(time_s=before[0],parts=[m.geom(g).name for g in gs],distance_m=float(c.dist)))
        loads.append([before[0],on_tray,on_bench])
        if np.any(d.warning.number):break
    records.append(state());trace={k:np.asarray([r[i] for r in records]) for i,k in enumerate(['time','qpos','qvel','qacc_warmstart'])}
    np.savez_compressed(output/'trace.npz',**trace)
    replay=mujoco.MjData(m);replay.qpos[:]=initial;mujoco.mj_forward(m,replay);replay.qacc_warmstart[:]=trace['qacc_warmstart'][0]
    qe=ve=0.
    for i in range(len(records)-1):
        mujoco.mj_step(m,replay);qe=max(qe,float(np.max(abs(replay.qpos-trace['qpos'][i+1]))));ve=max(ve,float(np.max(abs(replay.qvel-trace['qvel'][i+1]))))
    mask=trace['time']>=2.5
    linear=max(float(np.max(np.linalg.norm(trace['qvel'][mask,start:start+3],axis=1))) for start in [tv,rv]) if mask.any() else float('inf')
    angular=max(float(np.max(np.linalg.norm(trace['qvel'][mask,start+3:start+6],axis=1))) for start in [tv,rv]) if mask.any() else float('inf')
    shifts=[float(np.max(np.linalg.norm(trace['qpos'][:,start:start+3]-initial[start:start+3],axis=1))) for start in [tq,rq]]
    tail=np.asarray([r for r in loads if r[0]>=2.5]);mean_loads=tail[:,1:].mean(axis=0) if len(tail) else np.array([0.,0.])
    expected_weight=float(m.body_mass[list(tool_bodies)].sum()*9.81)
    load_error=abs(float(mean_loads.sum())/expected_weight-1)
    checks=dict(duration_completed=d.time>=3.-1e-8,free_unactuated_objects=m.nu==0 and m.neq==0,
        no_numerical_warnings=not np.any(d.warning.number),finite_states=all(np.isfinite(x).all() for x in trace.values()),
        no_external_forces=not external,penetration_bounded=penetration<=.00025,no_unexpected_penetration=not violations,
        settled_linear_speed=linear<=.001,settled_angular_speed=angular<=.01,
        tool_displacement=shifts[0]<=.005,tray_displacement=shifts[1]<=.001,
        heel_still_supported_by_tray=mean_loads[0]>=.005,tips_still_supported_by_bench=mean_loads[1]>=.005,
        net_vertical_support_load=load_error<=.05,
        exact_replay=qe<=1e-9 and ve<=1e-8)
    result=dict(scope=__doc__,passed=all(checks.values()),checks={k:bool(v) for k,v in checks.items()},
        duration_s=float(d.time),maximum_penetration_m=penetration,maximum_settled_linear_speed_m_s=linear,
        maximum_settled_angular_speed_rad_s=angular,maximum_tool_displacement_m=shifts[0],maximum_tray_displacement_m=shifts[1],
        mean_settled_support_vertical_load_n=dict(tray=float(mean_loads[0]),bench=float(mean_loads[1])),
        expected_tool_weight_n=expected_weight,relative_net_vertical_support_load_error=load_error,
        maximum_replay_q_error=qe,maximum_replay_v_error=ve,unintended_contacts=violations,
        full_final_qpos=d.qpos.tolist(),tool_final_qpos=d.qpos[:rq].tolist(),tray_final_qpos=d.qpos[rq:rq+7].tolist(),
        trace_sha256=sha(output/'trace.npz'),contract_sha256=sha(output/'contract.json'),qualified_robot_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if 'qpos' not in k}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args()
    if not run(a.source,a.output)['passed']:raise SystemExit(1)
