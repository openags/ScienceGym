"""Render retained poses for visual review of a checked short walking probe."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(source,folder):
    source,folder=Path(source).resolve(),Path(folder).resolve()
    report=json.loads((folder/'physical_review.json').read_text())
    if not report['passed'] or report['trace_sha256']!=sha(folder/'trace.npz') or report['model_sha256']!=sha(source/'world.xml'):
        raise ValueError('Requires the unchanged physically checked probe')
    output=folder/'visual_review_aisle';output.mkdir(exist_ok=False)
    m=mujoco.MjModel.from_xml_path(str(source/'world.xml'));d=mujoco.MjData(m)
    trace=dict(np.load(folder/'trace.npz'))
    m.mat_rgba[:,:3]=np.clip(m.mat_rgba[:,:3],0,1)**(1/2.2)
    for i in range(m.ntex):
        if not m.texture(i).name.startswith('lab_texture_'):continue
        start=m.tex_adr[i];h,w,c=m.tex_height[i],m.tex_width[i],m.tex_nchannel[i]
        pixels=m.tex_data[start:start+h*w*c].reshape(h,w,c);pixels[:]=pixels[::-1].copy()
    m.vis.headlight.ambient[:]=.3;m.vis.headlight.diffuse[:]=.3
    m.light_pos[:]=[[5.2,-4.7,2.9],[6.5,-6.5,2.8]]
    m.light_dir[:]=[[.1,-.15,-1.],[-.2,.2,-1.]]
    renderer=mujoco.Renderer(m,height=720,width=1280,max_geom=m.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    camera=mujoco.MjvCamera();camera.azimuth=270;camera.elevation=-22
    camera.lookat[:]=[5.38,-5.25,.83];camera.distance=3.2
    frames=[]
    try:
        for time in [0.,7.,14.,20.]:
            i=min(int(np.searchsorted(trace['time'],time)),len(trace['time'])-1)
            d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
            renderer.update_scene(d,camera=camera,scene_option=option)
            path=output/f'frame_{int(time):02d}.png';Image.fromarray(renderer.render()).save(path)
            frames.append(dict(file=path.name,time_s=float(trace['time'][i]),trace_index=i,sha256=sha(path)))
    finally:renderer.close()
    receipt=dict(frames=frames,model_sha256=report['model_sha256'],trace_sha256=report['trace_sha256'],
                 renderer_sha256=sha(__file__),camera=dict(lookat=camera.lookat.tolist(),distance=camera.distance,azimuth=camera.azimuth,elevation=camera.elevation),
                 adjustments=['GLTF display gamma and texture origin','headlight ambient/diffuse 0.3','Presentation spotlights over the original laboratory aisle'],
                 scope='Visual review of a physically checked short probe in the existing lab. No isolation, full workflow or reliability qualification.')
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.copyfile(__file__,output/Path(__file__).name)
    print(output,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('folder');a=p.parse_args();render(a.source,a.folder)
