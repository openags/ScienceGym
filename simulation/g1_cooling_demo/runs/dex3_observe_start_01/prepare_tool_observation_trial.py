"""Author a stationary arm-clear start for sensor-derived tool approach.

Robot pose and tool-local hand preshape are declared initial conditions.
The free tool, free tray and complete laboratory retain their source states.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source,output,opening=.02):
    source,output=map(lambda p:Path(p).resolve(),[source,output])
    parent=json.loads((source/'contract.json').read_text());review=json.loads((source/'review.json').read_text())
    assert review['passed_initial_scene_checks'] and review['contract_sha256']==sha(source/'contract.json')
    assert parent['hand_kind']=='unitree_three_finger'
    output.mkdir(parents=True,exist_ok=False)
    for n in ['world.xml','robot_predictor.xml','model_inputs.json']:shutil.copyfile(source/n,output/n)
    m=mujoco.MjModel.from_xml_path(str(output/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=parent['initial_qpos'];d.qvel[:]=parent['initial_qvel']
    names=['right_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
    for n,v in zip(names,[.2,-.25,0.,1.,0.,0.,0.]):d.joint(n).qpos[0]=v
    fit_path=Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json'
    fit=json.loads(fit_path.read_text())['candidates'][7];hand=fit['q'].copy()
    for n,sign in zip(parent['closing_drivers'],parent['closing_signs']):hand[n]-=sign*opening
    for n,v in hand.items():d.joint(n).qpos[0]=v
    for j in range(m.njnt):
        if m.jnt_limited[j]:assert m.jnt_range[j,0]<=d.qpos[m.jnt_qposadr[j]]<=m.jnt_range[j,1]
    mujoco.mj_forward(m,d);robot={m.body('pelvis').id};bad=[]
    for b in range(m.nbody):
        if m.body_parentid[b] in robot:robot.add(b)
    for c in d.contact:
        bs={int(m.geom_bodyid[g]) for g in c.geom};parts=[m.geom(int(g)).name for g in c.geom]
        if not bs&robot:continue
        bound=.001 if 'lab_part_1515' in parts and any('ankle_roll_link_collision' in n for n in parts) else .00002
        if c.dist < -bound:bad.append(dict(parts=parts,penetration_m=-float(c.dist),bound_m=bound))
    geometry=dict(scope='Unposed tool-local grasp and own-hand geometry; no tool placement or arm path',
        source_tool_from_wrist=fit['source_tool_from_wrist'],pregrasp_hand_q=hand,grasp_hand_q=fit['q'],opening_rad=opening,
        robot_contact_features=parent['robot_contact_features'],source_grasp_sha256=sha(fit_path),source_candidate=7,
        qualified_grasp_prior=False)
    contract=dict(parent,scope=__doc__,source_contract_sha256=sha(source/'contract.json'),
        source_review_sha256=sha(source/'review.json'),initial_qpos=d.qpos.tolist(),initial_qvel=d.qvel.tolist(),
        observed_approach=True,grasp_geometry=geometry,qualified_approach=False)
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result=dict(scope=__doc__,passed_initial_scene_checks=not bad,excessive_contacts=bad,
        source_plant_unchanged=sha(source/'world.xml')==sha(output/'world.xml'),
        contract_sha256=sha(output/'contract.json'),qualified_approach=False,qualified_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copyfile(__file__,output/Path(__file__).name)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--opening',type=float,default=.02)
    a=p.parse_args();run(a.source,a.output,a.opening)
