"""Inspect a frozen visual actor's planning state from its recorded inputs.

This host-side debugging replay supplies the same public model and sensor
packets. It is not the separate namespace-isolated controller acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import shutil
import sys

import mujoco
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(folder,output,retry_planner=False):
    folder,output=map(lambda p:Path(p).resolve(),[folder,output]);output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,output/Path(__file__).name)
    result=json.loads((folder/'result.json').read_text());receipt=json.loads((folder/'actor_isolation.json').read_text())
    for n,h in receipt['source_modules'].items():assert sha(folder/'actor_bundle/code'/n)==h
    assert sha(folder/'sensors.npz')==result['sensors_sha256']
    assert sha(folder/'responses.pkl')==result['responses_sha256']
    assert sha(folder/'camera_index.json')==result['camera_index_sha256']
    code=folder/'actor_bundle/code';sys.path.insert(0,str(code))
    spec=importlib.util.spec_from_file_location('frozen_visual_actor',code/'visual_tool_actor.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    prior=json.loads((folder/'actor_bundle/model/policy/tool_prior.json').read_text())
    prior['tool_shape_path']=str(folder/'actor_bundle/model/known_objects/tool_shape.glb')
    actor=module.ToolActor(mujoco.MjModel.from_xml_path(str(folder/'actor_bundle/model/world.xml')),prior)
    sensors=dict(np.load(folder/'sensors.npz'));frames=json.loads((folder/'camera_index.json').read_text())
    expected=pickle.loads((folder/'responses.pkl').read_bytes());maximum_torque_error=0.;phases_match=True;observations=[]
    for i in range(len(expected)):
        packet={k:v[i] for k,v in sensors.items()};frame=int(packet.pop('camera_frame_id'))
        if frame>=0:
            entry=frames[frame];assert sha(folder/entry['file'])==entry['sha256']
            with np.load(folder/entry['file']) as image:packet.update({k:image[k] for k in image.files})
        else:packet.update(head_rgb=None,head_depth=None)
        response=actor.update(packet)
        maximum_torque_error=max(maximum_torque_error,float(np.max(abs(response['torque']-expected[i]['torque']))))
        phases_match=phases_match and response['phase']==expected[i]['phase']
        if frame>=0 and actor.poses:observations.append(dict(time_s=float(packet['time_s']),pose=actor.poses[-1]))
    report=dict(scope=__doc__,source_result_sha256=sha(folder/'result.json'),producer_sha256=sha(__file__),
        maximum_torque_error_nm=maximum_torque_error,phases_match=phases_match,observations=observations,
        plan=actor.plan,qualified_approach=False)
    if retry_planner and actor.planner is not None:
        current=Path(__file__).parent/'tool_approach_planning.py'
        spec=importlib.util.spec_from_file_location('current_tool_planner',current);new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
        D,df=actor.camera('head_depth');C,cf=actor.camera('head_rgb')
        from tool_observation import detect
        _,component=detect(packet['head_rgb'],packet['head_depth'],D,C,df,cf,actor.bounds,actor.threshold)
        surface=new.depth_surface(packet['head_depth'],D,df)
        pose=dict(position_m=actor.planner.registration[:3,3].tolist(),rotation_matrix=actor.planner.registration[:3,:3].tolist())
        planner=new.ToolApproachPlanner(actor.m,actor.planner.initial,pose,actor.geometry,actor.mesh,surface,component)
        report['retry_plan']=planner.build();report['retry_planner_sha256']=sha(current)
        shutil.copyfile(current,output/'retry_tool_approach_planning.py')
        report['retry_executed']=False
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='observations'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('output');p.add_argument('--retry-planner',action='store_true')
    a=p.parse_args();run(a.folder,a.output,a.retry_planner)
