"""Full recorded-state presentation of the independently verified plug cycle."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
import extended_device_assets
from device_assets import load
from trace_store import load_trace,sha


def render(directory):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());verification=json.loads((directory/'verification.json').read_text())
    if result['status']!='passed' or not verification['passed'] or verification['result_sha256']!=sha(directory/'result.json'):
        raise ValueError('Independent verification of this exact execution required')
    pins={n:sha(directory/n) for n in ['result.json','verification.json','workcell.xml']};pins['physics_trace.npz']=result['artifacts_sha256']['physics_trace.npz']
    trace=load_trace(directory,pins['physics_trace.npz']);model=load(directory/'workcell.xml');model.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    model.vis.global_.offwidth=1120;model.vis.global_.offheight=720
    model.stat.extent=1.8;model.vis.headlight.ambient[:]=.24;model.vis.headlight.diffuse[:]=.12
    renderer=mujoco.Renderer(model,720,1120)
    overview=mujoco.MjvCamera();overview.lookat[:]=[.4,0,1.06];overview.distance=1.75;overview.azimuth=55;overview.elevation=-27
    detail=mujoco.MjvCamera();detail.distance=.23;detail.azimuth=70;detail.elevation=-16
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    output=directory/'playback';output.mkdir(exist_ok=True);video=output/'chapter_01.mp4'
    if video.exists():raise ValueError('Preserve earlier presentation before rendering')
    writer=imageio.get_writer(video,fps=12,codec='libx264',quality=None,macro_block_size=16,
        ffmpeg_params=['-crf','23','-preset','medium','-threads','4','-movflags','+faststart'])
    end=float(trace['time'][-1]);events=result['observations'];frames=0
    try:
        for at in np.arange(0,end+1e-9,1/12):
            i=int(np.searchsorted(trace['time'],at));i=min(i,len(trace['time'])-1)
            if i and abs(trace['time'][i-1]-at)<abs(trace['time'][i]-at):i-=1
            data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i];mujoco.mj_forward(model,data)
            renderer.update_scene(data,overview);frame=Image.new('RGB',(1120,800),(14,25,35));frame.paste(Image.fromarray(renderer.render().copy()),(0,80))
            detail.lookat[:]=data.site('plug_tip').xpos+[0,-.015,0];renderer.update_scene(data,detail)
            frame.paste(Image.fromarray(renderer.render().copy()).resize((448,288)),(656,480));draw=ImageDraw.Draw(frame)
            event=next((e['label'] for e in reversed(events) if e['time_s']<=at),'approach_and_grasp')
            draw.text((20,12),'Cabled plug: insert, release, withdraw, return',font=font,fill=(225,239,244));draw.text((20,45),f'{at:06.2f} / {end:06.2f} s | {event.replace("_"," ")}',font=small,fill=(120,219,197))
            draw.rectangle((654,452,1106,478),fill=(14,25,35));draw.text((666,455),'Recorded contact state / socket detail',font=small,fill=(225,239,244))
            writer.append_data(np.array(frame));frames+=1
            if frames==1:frame.save(output/'first.png')
            if abs(at-38.75)<.04:frame.save(output/'released.png')
        frame.save(output/'last.png')
    finally:writer.close();renderer.close()
    if any(sha(directory/n)!=pins[n] for n in ['result.json','verification.json','workcell.xml']):raise ValueError('Inputs changed during presentation')
    row=dict(path='playback/chapter_01.mp4',start_s=0.,end_s=frames/12,duration_s=frames/12,frames=frames,bytes=video.stat().st_size,sha256=sha(video))
    manifest=dict(schema_version='sciencegym.recorded_playback.v1',presentation_only=True,kind='connector',fps=12,frames=frames,trace_seconds=end,
        chapters=[row],input_sha256=pins,renderer_sha256=sha(Path(__file__)),payload_interpolation=False,whole_paper_validated=False)
    (directory/'playback_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Rendered',frames,'frames',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args();render(args.directory)
