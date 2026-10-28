"""Clean full-laboratory views of an independently reviewed navigation probe."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def render(source,folder):
    source,folder=Path(source).resolve(),Path(folder).resolve()
    review=json.loads((folder/'physical_review.json').read_text())
    if not review['passed'] or review['trace_sha256']!=sha(folder/'trace.npz') or review['model_sha256']!=sha(source/'world.xml'):
        raise ValueError('Passing review of the unchanged trace and full laboratory required')
    out=folder/'visual_review'
    if out.exists():raise FileExistsError(out)
    out.mkdir()
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
    camera=mujoco.MjvCamera();camera.lookat[:]=[4.95,-5.08,.85]
    camera.distance=3.4;camera.azimuth=270.;camera.elevation=-20.
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    renderer=mujoco.Renderer(m,720,1280,max_geom=m.ngeom+1000);rows=[]
    try:
        for time in [0.,125.61,145.,float(trace['time'][-1])]:
            i=int(np.argmin(abs(trace['time']-time)));d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
            renderer.update_scene(d,camera=camera,scene_option=option)
            p=out/f'navigation_{time:07.2f}.png';Image.fromarray(renderer.render().copy()).save(p)
            rows.append(dict(time_s=float(trace['time'][i]),trace_index=i,file=p.name,sha256=sha(p)))
    finally:renderer.close()
    (out/'receipt.json').write_text(json.dumps(dict(frames=rows,source_sha256=sha(__file__),
        trace_sha256=review['trace_sha256'],physical_review_sha256=sha(folder/'physical_review.json'),
        scope='Still frames from a checked in-process navigation probe; no carrying or full experiment credit.'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('folder');a=p.parse_args();render(a.source,a.folder)
