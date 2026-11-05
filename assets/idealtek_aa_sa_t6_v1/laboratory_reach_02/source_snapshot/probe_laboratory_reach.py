"""Screen a tool pregrasp in the full G1 and existing laboratory geometry.

Offline static authoring only. The free tool is proposed on the materials
bench; no tool is inserted into this scene or credited as physically placed.
Neither balance, entry/exit trajectories nor sensor localization is tested.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import time

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'simulation/g1_cooling_demo'
sys.path.insert(0,str(RUNTIME))
from ftir_hand import ArmIK,mimic
from ftir_slider_posture import initialize_slider
from laboratory import LAB_FROM_WORK


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pose(p,r):
    t=np.eye(4);t[:3,:3]=r;t[:3,3]=p;return t


def run(fit,output):
    fit,output=Path(fit).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    (output/'source_snapshot').mkdir()
    for p in [Path(__file__),RUNTIME/'ftir_hand.py',RUNTIME/'ftir_slider_posture.py',RUNTIME/'robot_state.py']:
        shutil.copyfile(p,output/'source_snapshot'/p.name)
    report=json.loads(fit.read_text());assert report['passed_local_pad_geometry']
    parent=json.loads((fit.parent/'contract.json').read_text());assert sha(fit.parent/'contract.json')==report['contract_sha256']
    candidate=report['candidates'][0]
    support_path=ROOT/parent['support_review'];assert sha(support_path)==parent['support_review_sha256']
    support=json.loads(support_path.read_text());assert support['passed']
    q=np.asarray(support['final_qpos'])
    rig_from_source=pose(q[:3],Rotation.from_quat(np.r_[q[4:7],q[3]]).as_matrix())
    rig_from_source[:3,3]-=rig_from_source[:3,:3]@np.array([.13,0,.00575])
    runpath=RUNTIME/'runs/ftir_approach_11'
    predictor=runpath/'controller_model/world.xml'
    plant_path=runpath/'world.xml'
    if not plant_path.exists():raise FileNotFoundError(plant_path)
    m=mujoco.MjModel.from_xml_path(str(predictor));plant=mujoco.MjModel.from_xml_path(str(plant_path))
    imported_path=runpath/'laboratory_import.json'
    imported=json.loads(imported_path.read_text())
    floor={plant.geom(p['geom']).id for p in imported['parts'] if p['source_part'] in
           {'indoor_floor','annex_floor','outdoor_floor','outdoor_access_path'}}
    if not floor:raise ValueError('No source laboratory floors found')
    ik=ArmIK(m);d=initialize_slider(m)
    for n,v in candidate['q'].items():d.joint(n).qpos[0]=v
    mimic(m,d);mujoco.mj_forward(m,d)
    palm_from_site=np.linalg.inv(pose(d.body('right_palm_force_sensor').xpos,d.body('right_palm_force_sensor').xmat.reshape(3,3)))@pose(d.site('right_wrist_reference').xpos,d.site('right_wrist_reference').xmat.reshape(3,3))
    root_joint=next(j for j in range(m.njnt) if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_FREE)
    robot_root=plant.body(m.body(m.jnt_bodyid[root_joint]).name).id
    robot_bodies={robot_root}
    for b in range(plant.nbody):
        if plant.body_parentid[b] in robot_bodies:robot_bodies.add(b)
    xys=list(itertools.product([5.65,5.8,5.95],[-5.9,-6.05,-6.2]))
    yaws=np.linspace(-np.pi,np.pi,9)[:-1]
    seeds=[[.2,-.3,0.,1.5,0.,0.,0.],[-.685,-.77,1.29,.449,-1.42,.239,.189]]
    contract=dict(scope=__doc__,fit_sha256=sha(fit),support_sha256=sha(support_path),
        predictor_sha256=sha(predictor),plant_sha256=sha(plant_path),script_sha256=sha(__file__),
        laboratory_import_sha256=sha(imported_path),floor_geoms=sorted(plant.geom(g).name for g in floor),
        lab_from_work=LAB_FROM_WORK.tolist(),tool_rig_lab_position_m=[9.9,8.25,.85],
        base_xy_work_m=xys,tool_lab_yaws_rad=yaws.tolist(),arm_seeds_rad=seeds,
        palm_position_tolerance_m=.0002,palm_rotation_tolerance_rad=.004,
        maximum_unintended_robot_penetration_m=.00002,maximum_sole_penetration_m=.001,
        qualified_robot_grasp=False,qualified_paper_branch=False)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    rows=[];started=time.monotonic()
    for xy,yaw,seed in itertools.product(xys,yaws,seeds):
        lab_from_rig=pose([9.9,8.25,.85],Rotation.from_euler('z',yaw).as_matrix())
        palm_target=np.linalg.inv(LAB_FROM_WORK)@lab_from_rig@rig_from_source@np.asarray(candidate['source_tool_from_palm'])
        target=palm_target@palm_from_site
        d=initialize_slider(m,xy);d.joint('waist_yaw_joint').qpos[0]=0.
        for n,v in candidate['q'].items():d.joint(n).qpos[0]=v
        mimic(m,d);mujoco.mj_forward(m,d)
        arm,pe,re=ik.solve(d,target[:3,3],target[:3,:3],seed)
        d.qpos[ik.qa]=arm;mujoco.mj_forward(m,d)
        actual=pose(d.body('right_palm_force_sensor').xpos,d.body('right_palm_force_sensor').xmat.reshape(3,3))
        pe=float(np.linalg.norm(actual[:3,3]-palm_target[:3,3]))
        re=float(Rotation.from_matrix(actual[:3,:3]@palm_target[:3,:3].T).magnitude())
        row=dict(xy=xy,tool_lab_yaw_rad=float(yaw),seed=seed,arm_q=arm.tolist(),
                 position_error_m=pe,rotation_error_rad=re,reachable=pe<=.0002 and re<=.004)
        if row['reachable']:
            pd=mujoco.MjData(plant)
            for j in range(m.njnt):
                pj=plant.joint(m.joint(j).name);w=7 if m.jnt_type[j]==mujoco.mjtJoint.mjJNT_FREE else 1
                pd.qpos[pj.qposadr[0]:pj.qposadr[0]+w]=d.qpos[m.jnt_qposadr[j]:m.jnt_qposadr[j]+w]
            mujoco.mj_forward(plant,pd);bad=[]
            for c in pd.contact:
                bodies=[int(plant.geom_bodyid[g]) for g in c.geom]
                if not any(b in robot_bodies for b in bodies):continue
                names=[plant.geom(int(g)).name for g in c.geom]
                sole=any('ankle_roll_link_collision' in n for n in names) and any(int(g) in floor for g in c.geom)
                limit=.001 if sole else .00002
                if c.dist < -limit:bad.append(dict(parts=names,distance_m=float(c.dist),sole=sole))
            row.update(full_scene_static_clear=not bad,contacts_exceeding_bounds=bad,
                       robot_qpos=d.qpos.tolist(),palm_in_work=palm_target.tolist())
        rows.append(row)
    candidates=[r for r in rows if r.get('full_scene_static_clear')]
    result=dict(scope=__doc__,contract_sha256=sha(output/'contract.json'),tested=len(rows),
        reachable=sum(r['reachable'] for r in rows),clear=len(candidates),candidates=candidates,
        trials=rows,seconds=time.monotonic()-started,qualified_robot_grasp=False,qualified_paper_branch=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['tested','reachable','clear','seconds']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fit');p.add_argument('output');a=p.parse_args();run(a.fit,a.output)
