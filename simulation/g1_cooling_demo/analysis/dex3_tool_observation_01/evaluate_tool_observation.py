"""Evaluate an RGB-D tool-component proposal at an authored observing pose.

The detector receives images, robot-camera calibration and the fixed bench map.
Truth is computed separately after detection. This is a development example,
not an isolated execution actor or a localization-accuracy qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image

from tool_observation import detect


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source, observations, output, label):
    source,observations,output=[Path(p).resolve() for p in [source,observations,output]]
    output.mkdir(parents=True,exist_ok=False);public=output/'detector_inputs';public.mkdir()
    for n in [Path(__file__).name,'tool_observation.py']:
        shutil.copyfile(Path(__file__).parent/n,output/n)
    review=json.loads((observations/'review.json').read_text())
    assert sha(source/'world.xml')==review['source_model_sha256']
    pose=next(c for c in review['candidates'] if c['label']==label)
    m=mujoco.MjModel.from_xml_path(str(source/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=pose['initial_qpos'];mujoco.mj_forward(m,d)
    robot=mujoco.MjModel.from_xml_path(str(source/'robot_predictor.xml'));rd=mujoco.MjData(robot)
    for j in range(robot.njnt):rd.joint(robot.joint(j).name).qpos[:]=d.joint(robot.joint(j).name).qpos
    mujoco.mj_forward(robot,rd)
    # A fixed furniture part already present in the public architectural map.
    g=robot.geom('lab_part_1514').id;k=robot.geom_dataid[g]
    assert robot.body(robot.geom_bodyid[g]).name=='lab_architecture'
    vertices=robot.mesh_vert[robot.mesh_vertadr[k]:robot.mesh_vertadr[k]+robot.mesh_vertnum[k]]
    vertices=vertices@rd.geom_xmat[g].reshape(3,3).T+rd.geom_xpos[g]
    lo,hi=vertices.min(0),vertices.max(0);lo[2]=hi[2]+.002;hi[2]+=.18
    cameras={}
    for name in ['head_rgb','head_depth']:
        cid=robot.camera(name).id;T=np.eye(4);T[:3,:3]=rd.cam_xmat[cid].reshape(3,3);T[:3,3]=rd.cam_xpos[cid]
        cameras[name]=dict(world_from_camera=T.tolist(),fovy_deg=float(robot.cam_fovy[cid]))
    calibration=dict(scope='Own-robot cameras at an explicitly authored stationary pose and fixed bench map',
        initial_robot_qpos=rd.qpos.tolist(),cameras=cameras,workspace_bounds_m=[lo.tolist(),hi.tolist()],
        robot_model_sha256=sha(source/'robot_predictor.xml'),pose_estimation_uncertainty_evaluated=False)
    (public/'calibration.json').write_text(json.dumps(calibration,indent=2)+'\n')
    shutil.copyfile(observations/(label+'_rgb.png'),public/'rgb.png')
    shutil.copyfile(observations/(label+'_depth.npy'),public/'depth.npy')
    rgb=np.asarray(Image.open(public/'rgb.png'));depth=np.load(public/'depth.npy')
    result,cloud=detect(rgb,depth,cameras['head_depth']['world_from_camera'],cameras['head_rgb']['world_from_camera'],
        cameras['head_depth']['fovy_deg'],cameras['head_rgb']['fovy_deg'],[lo,hi])
    (output/'detector_output.json').write_text(json.dumps(result,indent=2)+'\n');np.save(output/'component_points.npy',cloud)
    # Evaluator-only data is not an input to detect(). Surface center is not COM.
    root=m.body('tweezer').id
    truth=dict(tool_com_m=d.subtree_com[root].tolist(),tool_long_axis=d.xmat[root].reshape(3,3)[:,0].tolist(),
        detector_received_truth=False)
    if result['candidate_found']:
        c=result['candidate'];axis=np.asarray(c['principal_axes'])[:,0]
        truth['unsigned_axis_error_deg']=float(np.rad2deg(np.arccos(np.clip(abs(axis@np.asarray(truth['tool_long_axis'])),0,1))))
        truth['visible_surface_center_distance_to_com_m']=float(np.linalg.norm(np.asarray(c['center_m'])-d.subtree_com[root]))
    (output/'evaluator_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    receipt=dict(scope=__doc__,source_review_sha256=sha(observations/'review.json'),
        source_model_sha256=sha(source/'world.xml'),detector_source_sha256=sha(output/'tool_observation.py'),
        evaluator_source_sha256=sha(output/Path(__file__).name),inputs={p.name:sha(p) for p in public.iterdir()},
        output_sha256=sha(output/'detector_output.json'),truth_sha256=sha(output/'evaluator_truth.json'),
        candidate_found=result['candidate_found'],qualified_perception=False)
    (output/'review.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(result=result,truth=truth)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('observations');p.add_argument('output');p.add_argument('--label',default='park_0')
    a=p.parse_args();run(a.source,a.observations,a.output,a.label)
