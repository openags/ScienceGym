"""Evaluate a public-input approach proposal before any physical execution.

The planner consumes only the explicitly copied public inputs. This producer
uses a selected tool-local grasp candidate as a geometric prior; it never
passes a source scene pose or previous arm trajectory to the planner.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
import trimesh

from tool_approach_planning import ToolApproachPlanner, depth_points

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(station, perception, observation, output, opening=.04):
    station,perception,observation,output=map(lambda p:Path(p).resolve(),[station,perception,observation,output])
    output.mkdir(parents=True,exist_ok=False);public=output/'public_inputs';public.mkdir()
    for name in ['tool_approach_planning.py','evaluate_tool_approach.py','ftir_hand.py','joint_rrt.py','robot_source_meshes.py','source_proximity.py']:
        shutil.copyfile(HERE/name,output/name)
    pose=json.loads((perception/'pose.json').read_text())
    if not pose['candidate_found']:raise ValueError('No observed tool pose')
    shape=ROOT/'assets/idealtek_aa_sa_t6_v1/revisions/passive_07/rest_geometry.glb'
    assert sha(shape)==json.loads((perception/'inputs.json').read_text())['shape_sha256']
    fit_path=HERE/'analysis/dex3_tweezer_fit_02/review.json'
    fit=json.loads(fit_path.read_text())['candidates'][7]
    hand=fit['q'].copy()
    for name,sign in [('right_hand_thumb_1_joint',-1),('right_hand_index_1_joint',1),('right_hand_middle_1_joint',1)]:hand[name]-=sign*opening
    prior=dict(scope='Unposed tool-local geometric grasp and robot preshape; no installed pose or arm path',
        source_tool_from_wrist=fit['source_tool_from_wrist'],pregrasp_hand_q=hand,opening_rad=opening,
        source_grasp_sha256=sha(fit_path),source_candidate=7,qualified_grasp_prior=False)
    (public/'grasp_prior.json').write_text(json.dumps(prior,indent=2)+'\n')
    (public/'tool_pose.json').write_text(json.dumps(pose['best'],indent=2)+'\n')
    for n in ['calibration.json','depth.npy','rgb.png']:
        shutil.copyfile(observation/'detector_inputs'/n,public/n)
    shutil.copyfile(perception/'component_points.npy',public/'tool_component.npy')
    shutil.copyfile(shape,public/'tool_shape.glb')
    calibration=json.loads((public/'calibration.json').read_text())
    m=mujoco.MjModel.from_xml_path(str(station/'robot_predictor.xml'))
    scene=trimesh.load(public/'tool_shape.glb',force='scene',process=False)
    mesh=scene.to_geometry()
    camera=calibration['cameras']['head_depth']
    points=depth_points(np.load(public/'depth.npy'),camera['world_from_camera'],camera['fovy_deg'])
    planner=ToolApproachPlanner(m,calibration['initial_robot_qpos'],pose['best'],prior,mesh,points,np.load(public/'tool_component.npy'))
    result=planner.build()
    receipt=dict(scope=__doc__,planner_inputs={p.name:sha(p) for p in public.iterdir()},
        robot_model_sha256=sha(station/'robot_predictor.xml'),source_model_path=str(station/'robot_predictor.xml'),
        source_files={p.name:sha(p) for p in output.glob('*.py')},result=result,
        plant_truth_given_to_planner=False,physical_execution=False,qualified_approach=False)
    (output/'review.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('station');p.add_argument('perception');p.add_argument('observation');p.add_argument('output');p.add_argument('--opening',type=float,default=.04)
    a=p.parse_args();run(a.station,a.perception,a.observation,a.output,a.opening)
