"""Render a complete independently verified device episode from saved states."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json
from pathlib import Path
import numpy as np,mujoco,imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
from bath_assets import load
from trace_store import load_trace,sha


def render(directory,kind,fps=12):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());verification=json.loads((directory/'verification.json').read_text())
    if result['status']!='passed' or not verification['passed'] or verification['result_sha256']!=sha(directory/'result.json'):
        raise ValueError('Exact complete episode must pass independent verification first')
    pins={n:sha(directory/n) for n in ['result.json','verification.json','workcell.xml']};pins['physics_trace.npz']=result['artifacts_sha256']['physics_trace.npz']
    trace=load_trace(directory,pins['physics_trace.npz']);model=load(directory/'workcell.xml');data=mujoco.MjData(model)
    model.vis.global_.offwidth=1120;model.vis.global_.offheight=720;model.vis.headlight.ambient[:]=.22;model.vis.headlight.diffuse[:]=.16
    renderer=mujoco.Renderer(model,720,1120);overview=mujoco.MjvCamera();detail=mujoco.MjvCamera()
    if kind=='bath':
        overview.lookat[:]=[.43,.0,.96];overview.distance=1.85;overview.azimuth=135;overview.elevation=-24
        detail.distance=.40;detail.azimuth=115;detail.elevation=-28
        title='A25: remove lid, park, press keys, retrieve and close'
        scope='Recorded contact execution; filling and thermal calibration remain separate'
    elif kind=='terminal':
        overview.lookat[:]=[.39,.0,.95];overview.distance=1.55;overview.azimuth=135;overview.elevation=-32
        detail.distance=.18;detail.azimuth=65;detail.elevation=-35
        title='USB-TC: insert, tighten, pull-check, loosen and withdraw'
        scope='One 24 AWG extension end; complete circuit and fine-wire transition remain separate'
    else:raise ValueError(kind)
    output=directory/'playback';output.mkdir(exist_ok=True)
    if any(output.glob('chapter_*.mp4')):raise ValueError('Existing presentation must be preserved')
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    end=float(trace['time'][-1]);events=result['observations'];frames=0;writer=None;chapters=[];chapter_frames=0
    def close_chapter():
        nonlocal writer,chapter_frames
        if writer is None:return
        writer.close();writer=None;path=output/f'chapter_{len(chapters)+1:02d}.mp4';start=sum(r['frames'] for r in chapters)/fps
        chapters.append(dict(path=str(path.relative_to(directory)),start_s=start,end_s=start+chapter_frames/fps,duration_s=chapter_frames/fps,
            frames=chapter_frames,bytes=path.stat().st_size,sha256=sha(path)));chapter_frames=0
    try:
        presentation_times=np.arange(0,end+1e-9,1/fps);presentation_times[-1]=end
        for at in presentation_times:
            if writer is None:
                writer=imageio.get_writer(output/f'chapter_{len(chapters)+1:02d}.mp4',fps=fps,codec='libx264',quality=None,macro_block_size=16,
                    ffmpeg_params=['-crf','22','-preset','medium','-threads','4','-movflags','+faststart'])
            i=min(int(np.searchsorted(trace['time'],at)),len(trace['time'])-1)
            if i and abs(trace['time'][i-1]-at)<abs(trace['time'][i]-at):i-=1
            data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i]
            mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data);mujoco.mj_flex(model,data);mujoco.mj_camlight(model,data);mujoco.mj_tendon(model,data)
            renderer.update_scene(data,overview);frame=Image.new('RGB',(1120,800),(14,25,35));frame.paste(Image.fromarray(renderer.render().copy()),(0,80))
            event=next((e for e in reversed(events) if e['time_s']<=at),{'label':'approach'});site='tcp'
            if kind=='bath':
                opened=next(e['time_s'] for e in events if e['label']=='bath_lid_supported')
                last_key=max(e['time_s'] for e in events if e['label']=='bath_key_released')
                if opened<=at<last_key:site='bath_pusher_tcp'
            else:
                if event['label'] in {'wire_retained_by_fixture','driver_seated','terminal_tightened','terminal_opened'}:site='driver_tcp'
            detail.lookat[:]=data.site(site).xpos;renderer.update_scene(data,detail)
            frame.paste(Image.fromarray(renderer.render().copy()).resize((448,288)),(656,480));draw=ImageDraw.Draw(frame)
            draw.text((20,10),title,font=font,fill=(225,239,244))
            draw.text((20,40),f"{at:06.2f} / {end:06.2f} s | "+event['label'].replace('_',' '),font=small,fill=(120,219,197))
            draw.text((20,62),scope,font=small,fill=(177,191,198));draw.rectangle((654,452,1106,478),fill=(14,25,35))
            draw.text((666,455),'Recorded tool and contact geometry',font=small,fill=(225,239,244))
            writer.append_data(np.asarray(frame));frames+=1;chapter_frames+=1
            if frames==1:frame.save(output/'first.png')
            for fraction,label in [(.25,'quarter'),(.5,'middle'),(.75,'three_quarters')]:
                if abs(at-end*fraction)<1/(2*fps):frame.save(output/(label+'.png'))
            if frames%(fps*30)==0:print('PRESENTATION',round(at,2),'/',round(end,2),flush=True)
            if chapter_frames>=fps*120:close_chapter()
        frame.save(output/'last.png');close_chapter()
    finally:
        if writer is not None:writer.close()
        renderer.close()
    if any(sha(directory/n)!=pins[n] for n in ['result.json','verification.json','workcell.xml']):raise ValueError('Inputs changed during rendering')
    manifest=dict(schema_version='sciencegym.recorded_playback.v1',presentation_only=True,kind=kind,fps=fps,frames=frames,trace_seconds=end,
        chapters=chapters,input_sha256=pins,renderer_sha256=sha(Path(__file__)),payload_interpolation=False,last_frame_exact_terminal_state=True,whole_paper_validated=False)
    (directory/'playback_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Rendered',frames,'frames',len(chapters),'chapters',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--kind',choices=['bath','terminal'],required=True);p.add_argument('--fps',type=int,default=12);a=p.parse_args();render(a.directory,a.kind,a.fps)
