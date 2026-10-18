"""Present the complete independently checked seven-layer state recording."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
from load_model import load
from trace_store import load_trace,sha


def render(directory,fps=12):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text())
    verification=json.loads((directory/'verification.json').read_text())
    if result['status']!='passed' or not verification['passed'] or verification['result_sha256']!=sha(directory/'result.json'):
        raise ValueError('Independent verification of this exact complete episode required')
    pins={n:sha(directory/n) for n in ['result.json','verification.json','workcell.xml','step_receipts.json']}
    pins['physics_trace.npz']=result['artifacts_sha256']['physics_trace.npz']
    trace=load_trace(directory,pins['physics_trace.npz']);model=load(directory/'workcell.xml');data=mujoco.MjData(model)
    model.vis.global_.offwidth=1120;model.vis.global_.offheight=720
    model.vis.headlight.ambient[:]=.22;model.vis.headlight.diffuse[:]=.16
    renderer=mujoco.Renderer(model,720,1120)
    overview=mujoco.MjvCamera();overview.lookat[:]=[.44,-.05,1.02];overview.distance=1.8;overview.azimuth=135;overview.elevation=-32
    detail=mujoco.MjvCamera();detail.distance=.29;detail.azimuth=65;detail.elevation=-29
    output=directory/'playback';output.mkdir(exist_ok=True)
    if any(output.glob('chapter_*.mp4')):raise ValueError('Preserve existing presentation before rendering again')
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    end=float(trace['time'][-1]);events=result['observations'];frames=0;writer=None;chapters=[];chapter_frames=0
    def close_chapter():
        nonlocal writer,chapter_frames
        if writer is None:return
        writer.close();writer=None
        path=output/f'chapter_{len(chapters)+1:02d}.mp4';start=sum(r['frames'] for r in chapters)/fps
        chapters.append(dict(path=str(path.relative_to(directory)),start_s=start,end_s=start+chapter_frames/fps,
            duration_s=chapter_frames/fps,frames=chapter_frames,bytes=path.stat().st_size,sha256=sha(path)))
        chapter_frames=0
    try:
        for at in np.arange(0,end+1e-9,1/fps):
            if writer is None:
                path=output/f'chapter_{len(chapters)+1:02d}.mp4'
                writer=imageio.get_writer(path,fps=fps,codec='libx264',quality=None,macro_block_size=16,
                    ffmpeg_params=['-crf','22','-preset','medium','-threads','4','-movflags','+faststart'])
            i=min(int(np.searchsorted(trace['time'],at)),len(trace['time'])-1)
            if i and abs(trace['time'][i-1]-at)<abs(trace['time'][i]-at):i-=1
            data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i]
            # Presentation only: recompute the recorded geometry without a
            # physics step or interpolation of rigid/flexible payload poses.
            mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data);mujoco.mj_flex(model,data);mujoco.mj_camlight(model,data);mujoco.mj_tendon(model,data)
            renderer.update_scene(data,overview)
            frame=Image.new('RGB',(1120,800),(14,25,35));frame.paste(Image.fromarray(renderer.render().copy()),(0,80))
            detail.lookat[:]=data.site('tcp').xpos+[0,0,-.025];renderer.update_scene(data,detail)
            frame.paste(Image.fromarray(renderer.render().copy()).resize((448,288)),(656,480))
            draw=ImageDraw.Draw(frame);event=next((e for e in reversed(events) if e['time_s']<=at),{'label':'approach'})
            label=(event['label']+' '+event.get('body','')).replace('_',' ')
            draw.text((20,10),'Seven layers: assemble, release, disassemble, return',font=font,fill=(225,239,244))
            draw.text((20,40),f'{at:06.2f} / {end:06.2f} s | {label}',font=small,fill=(120,219,197))
            draw.text((20,62),'Preconstructed frame and prebonded films; one recorded robot episode',font=small,fill=(177,191,198))
            draw.rectangle((654,452,1106,478),fill=(14,25,35));draw.text((666,455),'Recorded tool and contact geometry',font=small,fill=(225,239,244))
            writer.append_data(np.asarray(frame));frames+=1;chapter_frames+=1
            if frames==1:frame.save(output/'first.png')
            if abs(at-150)<1/(2*fps):frame.save(output/'cover_released.png')
            if frames%(fps*30)==0:print('PRESENTATION',round(at,2),'/',round(end,2),flush=True)
            if chapter_frames>=fps*120:close_chapter()
        frame.save(output/'last.png');close_chapter()
    finally:
        if writer is not None:writer.close()
        renderer.close()
    if any(sha(directory/n)!=pins[n] for n in ['result.json','verification.json','workcell.xml','step_receipts.json']):raise ValueError('Inputs changed during presentation')
    manifest=dict(schema_version='sciencegym.recorded_playback.v1',presentation_only=True,kind='selected_assembly',fps=fps,frames=frames,
        trace_seconds=end,chapters=chapters,input_sha256=pins,renderer_sha256=sha(Path(__file__)),payload_interpolation=False,whole_paper_validated=False)
    (directory/'playback_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Rendered',frames,'frames',len(chapters),'chapters',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--fps',type=int,default=12);a=p.parse_args();render(a.directory,a.fps)
