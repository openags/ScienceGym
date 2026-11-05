"""Inspect native head observations at retained states of a completed pickup.

This uses recorded plant states to render an offline visibility diagnostic.
Segmentation is evaluator-only and is not passed to the appearance detector.
No new physical execution, online tracking, or grasp qualification is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image

from tool_cameras import ToolCameras
from tool_observation import detect


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output')
    p.add_argument('--times',type=float,nargs='+',default=[0.,10.,15.,17.,20.,23.]);a=p.parse_args()
    run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'trace.npz')==result['trace_sha256'] and sha(run/'world.xml')==contract['model_sha256']
    trace=dict(np.load(run/'trace.npz'));model=mujoco.MjModel.from_xml_path(str(run/'world.xml'));data=mujoco.MjData(model)
    data.qpos[:]=trace['qpos'][0];mujoco.mj_forward(model,data)
    g=model.geom('lab_part_1514').id
    assert model.body(model.geom_bodyid[g]).name=='lab_architecture'
    k=model.geom_dataid[g];vertices=model.mesh_vert[model.mesh_vertadr[k]:model.mesh_vertadr[k]+model.mesh_vertnum[k]]
    vertices=vertices@data.geom_xmat[g].reshape(3,3).T+data.geom_xpos[g]
    lo,hi=vertices.min(0),vertices.max(0);lo[2]=hi[2]+.002;hi[2]+=.18
    bodies={model.body('tweezer').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in bodies:bodies.add(b)
    geoms=np.flatnonzero(np.isin(model.geom_bodyid,list(bodies)))
    camera=ToolCameras(model);rows=[]
    previous_samples=int(model.vis.quality.offsamples);model.vis.quality.offsamples=0
    try:segmenter=mujoco.Renderer(model,height=480,width=640,max_geom=model.ngeom+1000)
    finally:model.vis.quality.offsamples=previous_samples
    segmenter.enable_segmentation_rendering()
    source=out/'source';source.mkdir()
    for name in ['evaluate_held_tool_visibility.py','tool_cameras.py','tool_observation.py','sensor_rendering.py']:
        shutil.copyfile(Path(__file__).parent/name,source/name)
    try:
        for requested in a.times:
            if not 0<=requested<=trace['time'][-1]:raise ValueError('Requested time outside the retained recording')
            i=int(np.searchsorted(trace['time'],requested));data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];mujoco.mj_forward(model,data)
            frame=camera.read(data);calibration={}
            for name in ['head_rgb','head_depth']:
                k=model.camera(name).id;T=np.eye(4);T[:3,:3]=data.cam_xmat[k].reshape(3,3);T[:3,3]=data.cam_xpos[k]
                calibration[name]=(T,float(model.cam_fovy[k]))
            D,df=calibration['head_depth'];C,cf=calibration['head_rgb']
            proposal,points=detect(frame['head_rgb'],frame['head_depth'],D,C,df,cf,[lo,hi],24.)
            # The diagnostic mask is generated after detector inference.
            segmenter.update_scene(data,camera='head_rgb',scene_option=camera.option);seg=segmenter.render().copy()
            mask=np.isin(seg[:,:,0],geoms)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
            prefix=f'{requested:06.3f}s'
            Image.fromarray(frame['head_rgb']).save(out/(prefix+'_rgb.png'))
            Image.fromarray((mask*255).astype(np.uint8)).save(out/(prefix+'_evaluator_tool_mask.png'))
            np.savez_compressed(out/(prefix+'_sensor_inputs.npz'),**frame,world_from_depth_camera=D,world_from_rgb_camera=C,
                                depth_fovy=df,rgb_fovy=cf,bounds=np.array([lo,hi]),detected_component=points)
            row=dict(requested_time_s=requested,recorded_time_s=float(trace['time'][i]),
                     evaluator_visible_tool_pixels=int(mask.sum()),appearance_proposal=proposal,
                     detector_used_evaluator_mask=False,files={name:sha(out/name) for name in
                         [prefix+'_rgb.png',prefix+'_evaluator_tool_mask.png',prefix+'_sensor_inputs.npz']})
            rows.append(row);print(json.dumps(dict(time_s=requested,visible_tool_pixels=row['evaluator_visible_tool_pixels'],candidate_found=proposal['candidate_found'])),flush=True)
    finally:camera.close();segmenter.close()
    report=dict(scope=__doc__,source_result_sha256=sha(run/'result.json'),source_trace_sha256=result['trace_sha256'],
                source_sha256={f.name:sha(f) for f in source.iterdir()},rows=rows,segmentation_multisampling=False,online_tool_tracking_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
