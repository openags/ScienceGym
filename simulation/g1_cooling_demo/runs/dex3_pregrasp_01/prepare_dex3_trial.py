"""Freeze an opened, full-body pregrasp before a three-finger contact attempt."""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def run(station, output, candidate=0, opening=.02):
    station=Path(station).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    review=json.loads((station/'review.json').read_text());parent=json.loads((station/'contract.json').read_text())
    assert sha(station/'contract.json')==review['contract_sha256']
    fit=json.loads((Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json').read_text())
    assert parent['fit_sha256']==sha(Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json')
    selected=review['candidates'][candidate];grasp=fit['candidates'][selected['candidate_index']]
    for n in ['world.xml','robot_predictor.xml','model_inputs.json']:shutil.copyfile(station/n,out/n)
    m=mujoco.MjModel.from_xml_path(str(out/'world.xml'));d=mujoco.MjData(m);d.qpos[:]=selected['initial_qpos']
    drivers=['right_hand_thumb_1_joint','right_hand_index_1_joint','right_hand_middle_1_joint']; signs=[-1.,1.,1.]
    for n,sign in zip(drivers,signs):d.joint(n).qpos[0]-=sign*opening
    for j in range(m.njnt):
        if m.jnt_limited[j]:assert m.jnt_range[j,0]<=d.qpos[m.jnt_qposadr[j]]<=m.jnt_range[j,1]
    mujoco.mj_forward(m,d);contacts=[];bad=[]
    root=m.body('pelvis').id;robot={root};tool={m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in robot:robot.add(b)
        if m.body_parentid[b] in tool:tool.add(b)
    tool_contact=False
    for c in d.contact:
        bs={int(m.geom_bodyid[g]) for g in c.geom};names=[m.geom(int(g)).name for g in c.geom]
        if bs&robot and bs&tool and c.dist<=0:tool_contact=True
        bound=.001 if any('ankle_roll_link_collision' in (n or '') for n in names) and 'lab_part_1515' in names else .00025 if not bs&robot else .00002
        record=dict(parts=names,distance_m=float(c.dist),bound_m=bound);contacts.append(record)
        if c.dist < -bound:bad.append(record)
    contract=dict(scope=__doc__,hand_kind='unitree_three_finger',source_station_review_sha256=sha(station/'review.json'),
        candidate_index=candidate,opening_rad=opening,plant_sha256=sha(out/'world.xml'),predictor_sha256=sha(out/'robot_predictor.xml'),
        inputs_sha256=sha(out/'model_inputs.json'),initial_qpos=d.qpos.tolist(),initial_qvel=d.qvel.tolist(),
        robot_contact_features=[dict(body=c['part'],point_local_m=c['point_hand_local_m']) for c in grasp['contacts']],
        closing_drivers=drivers,closing_signs=signs,task='pickup_hold_replace_release',
        tool_use_closure_not_part_of_this_pickup_test=True,qualified_grasp=False)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result=dict(scope=__doc__,passed_initial_scene_checks=not bad and not tool_contact,excessive_contacts=bad,
                initial_robot_tool_contact=tool_contact,contacts=contacts,contract_sha256=sha(out/'contract.json'),
                qualified_grasp=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,out/Path(__file__).name)
    print(json.dumps({k:v for k,v in result.items() if k!='contacts'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('station');p.add_argument('output');p.add_argument('--candidate',type=int,default=0)
    p.add_argument('--opening',type=float,default=.02);a=p.parse_args();run(a.station,a.output,a.candidate,a.opening)
