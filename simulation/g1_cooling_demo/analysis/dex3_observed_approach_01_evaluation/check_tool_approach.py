"""Independently inspect a proposed observed-geometry path in the full plant.

This evaluator may access plant truth; its states and errors are never actor
inputs. Kinematic samples do not prove controlled motion or carrying.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(station, observation, planning, output):
    station,observation,planning,output=map(lambda p:Path(p).resolve(),[station,observation,planning,output])
    output.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,output/Path(__file__).name)
    planned=json.loads((planning/'review.json').read_text())['result']
    assert planned['planned']
    m=mujoco.MjModel.from_xml_path(str(station/'world.xml'));d=mujoco.MjData(m)
    obs=json.loads((observation/'review.json').read_text())
    d.qpos[:]=next(c['initial_qpos'] for c in obs['candidates'] if c['label']=='park_0')
    for name,value in planned['pregrasp_hand_q'].items():d.joint(name).qpos[0]=value
    names=['right_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
    qa=np.array([m.joint(n).qposadr[0] for n in names])
    robot={m.body('pelvis').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in robot:robot.add(b)
    path=planned['entry_path']+planned['lowering_path'][1:]
    bad=[];samples=0;minimum_distance=0.
    for segment,(start,end) in enumerate(zip(path[:-1],path[1:])):
        a,b=np.asarray(start),np.asarray(end)
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(b-a)/.008))+1)):
            d.qpos[qa]=(1-u)*a+u*b;mujoco.mj_forward(m,d);samples+=1
            for c in d.contact:
                bodies={int(m.geom_bodyid[g]) for g in c.geom}
                if not bodies&robot:continue
                parts=[m.geom(int(g)).name for g in c.geom]
                bound=.001 if 'lab_part_1515' in parts and any('ankle_roll_link_collision' in n for n in parts) else .00002
                minimum_distance=min(minimum_distance,float(c.dist))
                if c.dist < -bound:
                    if len(bad)<50:bad.append(dict(segment=segment,fraction=float(u),parts=parts,penetration_m=-float(c.dist),bound_m=bound))
    pose=json.loads((planning/'public_inputs/tool_pose.json').read_text())
    R=d.body('tweezer').xmat.reshape(3,3);t=d.body('tweezer').xpos-R@np.array([.13,0.,.00575])
    error=dict(translation_error_m=float(np.linalg.norm(np.asarray(pose['position_m'])-t)),
        rotation_error_deg=float(np.linalg.norm(Rotation.from_matrix(np.asarray(pose['rotation_matrix'])@R.T).as_rotvec())*180/np.pi),
        scope='One authored observing pose; no noise, calibration or randomized perception qualification')
    report=dict(scope=__doc__,passed_sampled_geometry=not bad,samples=samples,violations=bad,
        minimum_robot_contact_distance_m=minimum_distance,pose_error=error,
        plant_model_sha256=sha(station/'world.xml'),observation_review_sha256=sha(observation/'review.json'),
        planning_review_sha256=sha(planning/'review.json'),evaluator_sha256=sha(__file__),
        physical_execution=False,qualified_approach=False,qualified_grasp=False)
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('station');p.add_argument('observation');p.add_argument('planning');p.add_argument('output')
    a=p.parse_args();run(a.station,a.observation,a.planning,a.output)
