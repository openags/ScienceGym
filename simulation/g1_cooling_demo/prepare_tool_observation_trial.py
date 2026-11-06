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


def run(source,output,opening=.02,base_offset=(0.,0.),grasp_candidate=None):
    source,output=map(lambda p:Path(p).resolve(),[source,output])
    parent=json.loads((source/'contract.json').read_text());review=json.loads((source/'review.json').read_text())
    assert review['passed_initial_scene_checks'] and review['contract_sha256']==sha(source/'contract.json')
    assert parent['hand_kind']=='unitree_three_finger'
    output.mkdir(parents=True,exist_ok=False)
    for n in ['world.xml','robot_predictor.xml','model_inputs.json']:shutil.copyfile(source/n,output/n)
    m=mujoco.MjModel.from_xml_path(str(output/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=parent['initial_qpos'];d.qvel[:]=parent['initial_qvel']
    base_offset=np.asarray(base_offset,dtype=float)
    if base_offset.shape!=(2,) or not np.isfinite(base_offset).all() or np.linalg.norm(base_offset)>.1:
        raise ValueError('Authored initial stance offset must be finite and at most 0.1 m')
    d.qpos[:2]+=base_offset
    names=['right_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
    for n,v in zip(names,[.2,-.25,0.,1.,0.,0.,0.]):d.joint(n).qpos[0]=v
    fit_path=Path(parent['source_grasp_review']) if 'source_grasp_review' in parent else Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json'
    candidate_index=parent.get('source_grasp_candidate',7) if grasp_candidate is None else grasp_candidate
    if 'source_grasp_sha256' in parent:assert sha(fit_path)==parent['source_grasp_sha256']
    fit=json.loads(fit_path.read_text())['candidates'][candidate_index]
    if not all(fit['checks'].values()):raise ValueError('Selected grasp fails its source geometry screen')
    hand=fit['q'].copy()
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
    features=[dict(body=c['part'],point_local_m=c['point_hand_local_m']) for c in fit['contacts']]
    geometry=dict(scope='Unposed tool-local grasp and own-hand geometry; no tool placement or arm path',
        source_tool_from_wrist=fit['source_tool_from_wrist'],pregrasp_hand_q=hand,grasp_hand_q=fit['q'],opening_rad=opening,
        robot_contact_features=features,source_grasp_sha256=sha(fit_path),source_candidate=candidate_index,
        qualified_grasp_prior=False)
    contract=dict(parent,scope=__doc__,source_contract_sha256=sha(source/'contract.json'),
        source_review_sha256=sha(source/'review.json'),initial_qpos=d.qpos.tolist(),initial_qvel=d.qvel.tolist(),
        authored_initial_base_offset_m=base_offset.tolist(),initial_stance_offset_is_not_robot_motion=True,
        observed_approach=True,grasp_geometry=geometry,qualified_approach=False)
    if grasp_candidate is not None:
        contract.update(source_grasp_review=str(fit_path),source_grasp_candidate=candidate_index,
            source_grasp_sha256=sha(fit_path),robot_contact_features=features,
            grasp_selection_revision=dict(previous_candidate=parent.get('source_grasp_candidate',7),
                selected_candidate=candidate_index,geometry_masses_and_tool_states_changed=False,
                scope='Authored initial hand preshape and unposed grasp geometry; approach must be planned from native vision and executed anew',
                qualification_transferred=False))
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result=dict(scope=__doc__,passed_initial_scene_checks=not bad,excessive_contacts=bad,
        source_plant_unchanged=sha(source/'world.xml')==sha(output/'world.xml'),
        contract_sha256=sha(output/'contract.json'),qualified_approach=False,qualified_grasp=False)
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copyfile(__file__,output/Path(__file__).name)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--opening',type=float,default=.02)
    p.add_argument('--base-offset',type=float,nargs=2,default=[0.,0.],metavar=('X','Y'))
    p.add_argument('--grasp-candidate',type=int)
    a=p.parse_args();run(a.source,a.output,a.opening,a.base_offset,a.grasp_candidate)
