"""Render a Dex3 key attempt from its exact recorded plant states; no success claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import mujoco
import numpy as np
from PIL import Image


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(folder):
    folder=Path(folder).resolve()
    physical=json.loads((folder/'result.json').read_text())
    isolated=json.loads((folder/'actor_isolation.json').read_text())
    if not isolated['passed']:raise ValueError('Recorded isolated actor required')
    if physical['trace_sha256']!=sha(folder/'trace.npz') or physical['model_sha256']!=sha(folder/'world.xml'):
        raise ValueError('Reviewed trace/model changed')
    if (folder/'press.mp4').exists():raise FileExistsError('Do not overwrite a published trace movie')
    m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));d=mujoco.MjData(m)
    trace=dict(np.load(folder/'trace.npz'))
    m.mat_rgba[:,:3]=np.clip(m.mat_rgba[:,:3],0,1)**(1/2.2)
    for i in range(m.ntex):
        if not m.texture(i).name.startswith('lab_texture_'):continue
        start=m.tex_adr[i];h,w,c=m.tex_height[i],m.tex_width[i],m.tex_nchannel[i]
        pixels=m.tex_data[start:start+h*w*c].reshape(h,w,c);pixels[:]=pixels[::-1].copy()
    m.vis.headlight.ambient[:]=.5;m.vis.headlight.diffuse[:]=.5
    renderer=mujoco.Renderer(m,height=720,width=1280,max_geom=m.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    camera=mujoco.MjvCamera();camera.azimuth=45;camera.elevation=-18
    duration=float(trace['time'][-1]);count=math.ceil(duration*24);indices=[]
    encoder=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','22',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'press.rendering.mp4')],stdin=subprocess.PIPE)
    try:
        for frame in range(count):
            t=duration if frame==count-1 else frame/24
            index=min(np.searchsorted(trace['time'],t),len(trace['time'])-1);indices.append(int(index))
            d.qpos[:]=trace['qpos'][index];mujoco.mj_forward(m,d)
            u=float(np.clip(t/7,0,1))*float(np.clip((23-t)/7,0,1));u=u*u*(3-2*u)
            camera.lookat[:]=(1-u)*np.array([6.15,-5.6,.8])+u*np.array([6.34,-5.7,1.08])
            camera.distance=2.35-u
            renderer.update_scene(d,camera=camera,scene_option=option);pixels=renderer.render().copy()
            encoder.stdin.write(pixels.tobytes())
            if frame in [0,round(12.7*24),count-1]:Image.fromarray(pixels).save(folder/f'press_frame_{frame:04d}.png')
            if frame%120==0:print('render_press',frame,'/',count,flush=True)
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('Video encoder failed')
    finally:
        renderer.close()
        if encoder.poll() is None:encoder.kill();encoder.wait()
    (folder/'press.rendering.mp4').rename(folder/'press.mp4')
    receipt=dict(video_sha256=sha(folder/'press.mp4'),trace_sha256=physical['trace_sha256'],
        result_sha256=sha(folder/'result.json'),isolation_receipt_sha256=sha(folder/'actor_isolation.json'),execution_failure=physical['failure'],
        renderer_sha256=sha(__file__),frame_to_trace_index=indices,fps=24,frames=count,
        duration_s=count/24,resolution=[1280,720],overlays=False,physics_interpolation=False,
        presentation_adjustments=['Display gamma for GLTF materials','GLTF texture origin correction',
            'Headlight ambient/diffuse 0.5','Continuous camera approach and retreat'],
        scope='Recorded Dex3 BACKGROUND attempt from authored setup. Rendering does not establish physical success.')
    (folder/'press_video.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'render_dex3_ftir_press.py');print('press_video_saved',count,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();render(a.folder)
