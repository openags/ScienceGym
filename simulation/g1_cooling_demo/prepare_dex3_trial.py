"""Freeze an opened, full-body pregrasp before a three-finger contact attempt."""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def run(station, output, candidate=0, opening=.02, grouping_review=None, sleep_review=None, wake_review=None):
    station=Path(station).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    review=json.loads((station/'review.json').read_text());parent=json.loads((station/'contract.json').read_text())
    assert sha(station/'contract.json')==review['contract_sha256']
    fit=json.loads((Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json').read_text())
    assert parent['fit_sha256']==sha(Path(__file__).parent/'analysis/dex3_tweezer_fit_02/review.json')
    selected=review['candidates'][candidate];grasp=fit['candidates'][selected['candidate_index']]
    for n in ['world.xml','robot_predictor.xml','model_inputs.json']:shutil.copyfile(station/n,out/n)
    grouping = None
    if grouping_review:
        grouping_review=Path(grouping_review).resolve();grouping=json.loads(grouping_review.read_text())
        assert grouping['geometry_correspondence_passed'] and grouping['passed']
        assert grouping['source_model_sha256']==sha(station/'world.xml')
        assert grouping['model_sha256']==sha(grouping_review.parent/'world.xml')
        shutil.copyfile(grouping_review.parent/'world.xml',out/'world.xml')
    sleep_binding = None
    if sleep_review:
        assert wake_review, 'A matching contact-wake check is required'
        sleep_review=Path(sleep_review).resolve();wake_review=Path(wake_review).resolve()
        sleeping=json.loads(sleep_review.read_text());waking=json.loads(wake_review.read_text())
        assert sleeping['cover_only'] and all(sleeping['exact_compiled_preservation'].values())
        assert sleeping['active_trees_always_awake'] and sleeping['maximum_robot_tool_tray_state_difference']<=1e-10
        assert sleeping['source_model_sha256']==sha(out/'world.xml')
        assert sleeping['model_sha256']==sha(sleep_review.parent/'world.xml')
        assert waking['passed'] and waking['sleep_candidate_sha256']==sleeping['model_sha256']
        shutil.copyfile(sleep_review.parent/'world.xml',out/'world.xml')
        sleep_binding=dict(comparison_sha256=sha(sleep_review),wake_review_sha256=sha(wake_review),
            comparison_path=str(sleep_review),wake_review_path=str(wake_review),
            scope='Only native cover sleeping; robot, tool, tray and keys always awake',
            diagnostic_probe_present_in_execution=False,whole_trajectory_requires_new_qualification=True)
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
    if grouping:
        contract['static_grouping']=dict(review=str(grouping_review),review_sha256=sha(grouping_review),
            identical_bounded_sample=True,whole_trajectory_requires_new_qualification=True)
    if sleep_binding: contract['native_device_sleep']=sleep_binding
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result=dict(scope=__doc__,passed_initial_scene_checks=not bad and not tool_contact,excessive_contacts=bad,
                initial_robot_tool_contact=tool_contact,contacts=contacts,contract_sha256=sha(out/'contract.json'),
                qualified_grasp=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,out/Path(__file__).name)
    print(json.dumps({k:v for k,v in result.items() if k!='contacts'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('station');p.add_argument('output');p.add_argument('--candidate',type=int,default=0)
    p.add_argument('--opening',type=float,default=.02);p.add_argument('--grouping-review')
    p.add_argument('--sleep-review');p.add_argument('--wake-review')
    a=p.parse_args();run(a.station,a.output,a.candidate,a.opening,a.grouping_review,a.sleep_review,a.wake_review)
