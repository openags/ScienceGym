"""Render a checked window-push trace in the complete laboratory, without overlays."""
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
    physical=json.loads((folder/'physical_slider_review.json').read_text())
    isolation=json.loads((folder/'isolation_verification.json').read_text())
    if not physical['passed'] or not isolation['passed']:
        raise ValueError('Passing independent window and isolation checks required')
    if physical['trace_sha256']!=sha(folder/'trace.npz') or physical['model_sha256']!=sha(folder/'world.xml'):
        raise ValueError('Reviewed trace or model has changed')
    if (folder/'slider.mp4').exists():raise FileExistsError('Do not overwrite a published trace movie')
    result=json.loads((folder/'result.json').read_text())
    if result.get('requires_visual_outcome_confirmation'):
        outcome=json.loads((folder/'visual_outcome_review.json').read_text())
        if (not outcome['passed'] or outcome['trace_sha256']!=physical['trace_sha256']
                or outcome['result_sha256']!=sha(folder/'result.json')):
            raise ValueError('Passing unchanged native-sensor outcome replay required')
    events=result['actor_last_output']['events']
    def event_time(name):
        return float(next(e['time_s'] for e in events if e['state']==name))
    contact=event_time('seek_contact_endpoint');withdraw=event_time('withdraw_endpoint')
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
    camera=mujoco.MjvCamera();camera.azimuth=45;camera.elevation=-22
    duration=float(trace['time'][-1]);fps=24;count=math.ceil(duration*fps);indices=[]
    encoder=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1280x720','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'slider.rendering.mp4')],stdin=subprocess.PIPE)
    preview_frames={0,round((contact+3)*fps),count-1}
    try:
        for frame in range(count):
            t=duration if frame==count-1 else frame/fps
            index=min(np.searchsorted(trace['time'],t),len(trace['time'])-1);indices.append(int(index))
            d.qpos[:]=trace['qpos'][index];mujoco.mj_forward(m,d)
            u=float(np.clip((t-contact+8)/6,0,1))*float(np.clip((withdraw+7-t)/6,0,1))
            u=u*u*(3-2*u)
            camera.lookat[:]=(1-u)*np.array([6.15,-5.5,.82])+u*np.array([6.25,-5.52,1.10])
            camera.distance=3.05-1.8*u
            renderer.update_scene(d,camera=camera,scene_option=option);pixels=renderer.render().copy()
            encoder.stdin.write(pixels.tobytes())
            if frame in preview_frames:Image.fromarray(pixels).save(folder/f'slider_frame_{frame:04d}.png')
            if frame%120==0:print('render_slider',frame,'/',count,flush=True)
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('Video encoder failed')
    finally:
        renderer.close()
        if encoder.poll() is None:encoder.kill();encoder.wait()
    (folder/'slider.rendering.mp4').rename(folder/'slider.mp4')
    receipt=dict(video_sha256=sha(folder/'slider.mp4'),trace_sha256=physical['trace_sha256'],
        physical_review_sha256=sha(folder/'physical_slider_review.json'),
        isolation_review_sha256=sha(folder/'isolation_verification.json'),renderer_sha256=sha(__file__),
        frame_to_trace_index=indices,fps=fps,frames=count,duration_s=count/fps,resolution=[1280,720],
        overlays=False,physics_interpolation=False,contact_begin_s=contact,withdraw_complete_s=withdraw,
        presentation_adjustments=['Display gamma for GLTF materials','GLTF texture origin correction',
                                  'Headlight ambient/diffuse 0.5','Continuous camera approach and retreat'],
        scope='One observed and tactile-controlled window push from authored standing setup in the original laboratory. No walking, full hinged-cover opening, experiment or reliability qualification.')
    if result.get('requires_visual_outcome_confirmation'):
        receipt['visual_outcome_review_sha256']=sha(folder/'visual_outcome_review.json')
    (folder/'slider_video.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'render_ftir_slider.py')
    print('slider_video_saved',count,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');render(parser.parse_args().folder)
