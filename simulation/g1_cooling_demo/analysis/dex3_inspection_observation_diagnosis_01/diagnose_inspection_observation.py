"""Attribute a failed held-tool observation using retained frames and states.

This evaluator-only diagnostic reconstructs camera frames from recorded plant
states. Those calibration/segmentation values never enter a controller. It
tests appearance and search-window hypotheses, not online pose qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image
import trimesh

from tool_observation import detect


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def pose(obj):
    T=np.eye(4);T[:3,:3]=obj.xmat.reshape(3,3);T[:3,3]=obj.xpos
    return T


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['diagnostic','actor_run','output']:p.add_argument(name,type=Path)
    a=p.parse_args();run,actor,out=[getattr(a,k).resolve() for k in ['diagnostic','actor_run','output']]
    result=json.loads((run/'result.json').read_text());contract=json.loads((actor/'contract.json').read_text())
    assert sha(run/'trace.npz')==result['trace_sha256']
    assert sha(actor/'contract.json')==result['actor_contract_sha256']
    assert sha(actor/'world.xml')==contract['model_sha256']
    prior=json.loads((actor/'actor_bundle/model/policy/tool_prior.json').read_text())
    mesh=trimesh.load(actor/'actor_bundle/model/known_objects/tool_shape.glb',force='scene',process=False).to_geometry()
    frames=json.loads((run/'camera_index.json').read_text());trace=dict(np.load(run/'trace.npz'))
    events=json.loads((run/'events.json').read_text())
    times=[e['time_s'] for e in events if e.get('kind')=='held_tool_observation']
    selected=[min(frames,key=lambda f:abs(f['time_s']-t)) for t in [times[0],times[len(times)//2],times[-1]]]
    m=mujoco.MjModel.from_xml_path(str(actor/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:]=trace['qpos'][0];mujoco.mj_forward(m,d)
    initial_relative=np.linalg.inv(pose(d.site('right_wrist_reference')))@pose(d.body('tweezer'))
    tool={m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in tool:tool.add(b)
    geoms=np.flatnonzero(np.isin(m.geom_bodyid,list(tool)))
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    m.vis.quality.offsamples=0
    segment=mujoco.Renderer(m,height=480,width=640,max_geom=m.ngeom+1000)
    segment.enable_segmentation_rendering()
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'tool_observation.py']:shutil.copyfile(Path(__file__).with_name(name),out/name)
    rows=[]
    try:
        for f in selected:
            path=run/f['file'];assert sha(path)==f['sha256']
            with np.load(path) as data:rgb,depth=data['head_rgb'].copy(),data['head_depth'].copy()
            i=int(np.argmin(abs(trace['time']-f['time_s'])))
            d.qpos[:]=trace['qpos'][i];d.qvel[:]=trace['qvel'][i];d.time=float(trace['time'][i]);mujoco.mj_forward(m,d)
            D,C=[pose(d.camera(n)) for n in ['head_depth','head_rgb']]
            df,cf=[float(m.camera(n).fovy[0]) for n in ['head_depth','head_rgb']]
            segment.update_scene(d,camera='head_depth',scene_option=option);seg=segment.render().copy()
            mask=np.isin(seg[:,:,0],geoms)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
            h,w=depth.shape;y,x=np.mgrid[:h,:w];fy=h/(2*np.tan(np.deg2rad(df/2)))
            local=np.stack([(x+.5-w/2)*depth/fy,-(y+.5-h/2)*depth/fy,-depth],axis=-1)
            world=local@D[:3,:3].T+D[:3,3];color=(world-C[:3,3])@C[:3,:3];z=-color[:,:,2]
            rf=rgb.shape[0]/(2*np.tan(np.deg2rad(cf/2)))
            u=np.rint(rgb.shape[1]/2-.5+rf*color[:,:,0]/np.maximum(z,1e-9)).astype(int)
            v=np.rint(rgb.shape[0]/2-.5-rf*color[:,:,1]/np.maximum(z,1e-9)).astype(int)
            valid=mask&(u>=0)&(u<rgb.shape[1])&(v>=0)&(v<rgb.shape[0])&(z>.05)
            intensities=rgb[v[valid],u[valid]].mean(axis=1)
            nominal=pose(d.site('right_wrist_reference'))@np.linalg.inv(prior['grasp_geometry']['source_tool_from_wrist'])
            true=pose(d.body('tweezer'));relative=np.linalg.inv(pose(d.site('right_wrist_reference')))@true
            row=dict(time_s=f['time_s'],native_frame_sha256=f['sha256'],tool_depth_pixels=int(mask.sum()),
                tool_intensity_quantiles=np.quantile(intensities,[0,.1,.5,.9,1]).tolist() if len(intensities) else [],
                tool_wrist_translation_change_m=float(np.linalg.norm(relative[:3,3]-initial_relative[:3,3])),
                nominal_tool_center_error_m=float(np.linalg.norm(nominal[:3,3]-true[:3,3])),hypotheses=[])
            for label,T in [('nominal_grasp',nominal),('evaluator_true_tool',true)]:
                points=mesh.vertices@T[:3,:3].T+T[:3,3];bounds=[points.min(0)-.02,points.max(0)+.02]
                inside=np.all((world>=bounds[0])&(world<=bounds[1]),axis=-1)
                for threshold in [24.,42.,64.,96.,160.]:
                    proposal,cloud=detect(rgb,depth,D,C,df,cf,bounds,threshold)
                    fraction=0.
                    if len(cloud):
                        camera=(cloud-D[:3,3])@D[:3,:3];zz=-camera[:,2]
                        xx=np.rint(w/2-.5+fy*camera[:,0]/zz).astype(int);yy=np.rint(h/2-.5-fy*camera[:,1]/zz).astype(int)
                        fraction=float(mask[yy,xx].mean())
                    row['hypotheses'].append(dict(window=label,threshold=threshold,tool_pixels_in_window=int((mask&inside).sum()),
                        detected=proposal['candidate_found'],component_points=len(cloud),true_tool_fraction=fraction,
                        components=proposal['components']))
            Image.fromarray(rgb).save(out/f"{f['id']:05d}_native_rgb.png")
            Image.fromarray(mask.astype(np.uint8)*255).save(out/f"{f['id']:05d}_evaluator_tool_mask.png")
            rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='hypotheses'}),flush=True)
    finally:segment.close()
    report=dict(scope=__doc__,source_result_sha256=sha(run/'result.json'),source_trace_sha256=result['trace_sha256'],
        actor_contract_sha256=sha(actor/'contract.json'),source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        rows=rows,calibration_basis='Evaluator reconstruction at retained state; not exact native sensor replay',
        physical_execution=False,online_observation_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
