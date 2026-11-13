"""Counterfactual rendering without multisample anti-aliasing, for depth calibration.

Segmentation and device geometry label this diagnostic only. They are never
delivered to the controller or used to declare an experiment successful.
"""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import inspect_visible_surfaces as v
import mujoco
import numpy as np
import trimesh


def main():
    run=v.BASE/'runs/ftir_approach_09';out=Path(__file__).with_name('depth_projection_no_msaa_09.json')
    if out.exists():raise FileExistsError(out)
    time=225.5;m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    with np.load(run/'trace.npz') as a:
        i=max(0,int(np.argmin(abs(a['time']-time)))-1);d.qpos[:]=a['qpos'][i]
    mujoco.mj_forward(m,d)
    imported=json.loads((run/'laboratory_import.json').read_text())
    name=next(p['geom'] for p in imported['parts'] if p['source_part']=='sample_access_slider_grip')
    g=m.geom(name).id;mesh=int(m.geom_dataid[g]);va=m.mesh_vertadr[mesh];fa=m.mesh_faceadr[mesh]
    vertices=m.mesh_vert[va:va+m.mesh_vertnum[mesh]]@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g]
    faces=m.mesh_face[fa:fa+m.mesh_facenum[mesh]]
    surface=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    original_samples=int(m.vis.quality.offsamples)
    m.vis.quality.offsamples=0
    renderer=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000)
    try:
        renderer.enable_segmentation_rendering();renderer.update_scene(d,camera='head_depth',scene_option=option)
        segmentation=renderer.render().copy()
        renderer.disable_segmentation_rendering();renderer.enable_depth_rendering()
        renderer.update_scene(d,camera='head_depth',scene_option=option);rendered=renderer.render().copy()
    finally:renderer.close()
    original=v.frame(run,'head_depth_index.json','parts',time,True)
    native=rendered.copy()
    mask=(segmentation[:,:,0]==g)&(segmentation[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
    y,x=np.where(mask);pc=m.camera('head_depth').id;h,w=native.shape
    focal=h/(2*np.tan(np.deg2rad(m.cam_fovy[pc])/2));rows=[]
    for offset_x in [-.5,0.,.5,1.]:
        for offset_y in [-.5,0.,.5,1.]:
            z=native[mask]
            camera=np.c_[(x+offset_x-w/2)*z/focal,-(y+offset_y-h/2)*z/focal,-z]
            world=camera@d.cam_xmat[pc].reshape(3,3).T+d.cam_xpos[pc]
            distances=trimesh.proximity.closest_point(surface,world)[1]
            rows.append(dict(pixel_offset_xy=[offset_x,offset_y],points=len(x),
                             distance_quantiles_m=np.quantile(distances,[0,.25,.5,.75,.95,1]).tolist()))
    report=dict(scope=__doc__,time_s=time,trace_index=i,grip_pixels=int(mask.sum()),original_offsamples=original_samples,new_offsamples=0,physical_execution=False,maximum_change_from_native_depth_m=float(np.max(abs(rendered-original))),
                maximum_rendered_native_depth_difference_m=float(np.max(abs(rendered-native))),
                maximum_grip_depth_difference_m=float(np.max(abs(rendered[mask]-native[mask]))),
                rows=rows,source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),run/'trace.npz',run/'world.xml',run/'head_depth_index.json']})
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
