"""Chaptered full playback of a verified trace, with no payload interpolation."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
from device_assets import load
from trace_store import load_trace,sha


def render(directory,kind,fps=12,chapter_seconds=240):
    directory=Path(directory);result=json.loads((directory/'result.json').read_text());verification=json.loads((directory/'verification.json').read_text())
    if result['status']!='passed' or not verification['passed'] or verification['result_sha256']!=sha(directory/'result.json'):
        raise ValueError('Independent verification of this exact result is required')
    pins={n:sha(directory/n) for n in ['result.json','verification.json','workcell.xml']}
    pins['physics_trace.npz']=result['artifacts_sha256']['physics_trace.npz'];trace=load_trace(directory,pins['physics_trace.npz'])
    model=load(directory/'workcell.xml');model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    model.vis.global_.offwidth=1120;model.vis.global_.offheight=720
    model.stat.extent=1.8;model.stat.center[:]=[.4,0,1.]
    model.vis.headlight.ambient[:]=.22;model.vis.headlight.diffuse[:]=.12
    renderer=mujoco.Renderer(model,height=720,width=1120)
    camera=mujoco.MjvCamera();camera.lookat[:]=[.4,-.04,1.06];camera.distance=1.8;camera.azimuth=135;camera.elevation=-30
    detail=mujoco.MjvCamera();detail.distance=.34 if kind=='reflector' else .42;detail.azimuth=110;detail.elevation=-28
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    output=directory/'playback';output.mkdir(exist_ok=True)
    if list(output.glob('chapter_*.mp4')):raise ValueError('Preserve or move an earlier presentation before rerendering')
    rows=result['observations'];end=float(trace['time'][-1]);times=np.arange(0,end+1e-9,1/fps)
    if kind=='reflector':
        solar=json.loads((directory/'source_snapshot/selected_solar_path.json').read_text())
        locks=[e for e in rows if e['label']=='carriage_locked'];lock_times=np.array([e['time_s'] for e in locks])
        model.light_active[:]=False;model.light_active[0]=True;model.light_type[0]=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL
        model.light_diffuse[0]=[.9,.86,.8];model.light_ambient[0]=[.03,.03,.03]
    else:
        transfers=[];start=0.
        for event in rows:
            if event['label'] not in ['edge_lift_observed','cover_lifted']:continue
            body=event.get('body','cover')
            release=next(e for e in rows if e['time_s']>event['time_s'] and
                         ((e['label']=='support_observed' and e.get('body')==body) or (body=='cover' and e['label']=='cover_support_observed')))
            transfers.append((start,release['time_s'],body));start=release['time_s']
    chapters=[];writer=None;current=-1;filtered=None;total=0
    try:
        for elapsed in times:
            chapter=int(elapsed//chapter_seconds)
            if chapter!=current:
                if writer:writer.close()
                current=chapter;name=f'playback/chapter_{chapter+1:02d}.mp4'
                writer=imageio.get_writer(directory/name,fps=fps,codec='libx264',quality=None,macro_block_size=16,
                    ffmpeg_params=['-crf','23','-preset','medium','-threads','4','-movflags','+faststart'])
                chapters.append(dict(path=name,start_s=float(elapsed),frames=0))
            j=int(np.searchsorted(trace['time'],elapsed));j=min(j,len(trace['time'])-1)
            if j and abs(trace['time'][j-1]-elapsed)<abs(trace['time'][j]-elapsed):j-=1
            data.qpos[:]=trace['qpos'][j];data.qvel[:]=trace['qvel'][j];data.ctrl[:]=trace['ctrl'][j]
            if kind=='reflector':
                index=min(int(np.searchsorted(lock_times,elapsed)),len(locks)-1);command=locks[index]['command_index'];sample=solar['samples'][command]
                az,el=np.deg2rad([sample['azimuth_deg'],sample['elevation_deg']]);sun=np.array([np.cos(el)*np.sin(az),np.cos(el)*np.cos(az),np.sin(el)])
                model.light_dir[0]=-sun;model.light_pos[0]=np.array(result['configuration']['emitter_origin_m'])+2*sun
                body='carriage';title='Solar carriage | release, slide, lock';phase=f'Adjustment {command+1} / {len(locks)} | selected solar sequence'
            else:
                body=next((n for a,b,n in transfers if a<=elapsed<=b),'foam_lower');title='Seven-layer assembly and return';phase=body
            # This process only draws recorded states. It never steps physics.
            mujoco.mj_forward(model,data)
            target=data.body(body).xpos.copy()+([0,0,.015] if kind=='reflector' else [0,0,0])
            filtered=target if filtered is None else .8*filtered+.2*target;detail.lookat[:]=filtered
            renderer.update_scene(data,camera);frame=Image.new('RGB',(1120,800),(14,25,35));frame.paste(Image.fromarray(renderer.render().copy()),(0,80))
            renderer.update_scene(data,detail);close=Image.fromarray(renderer.render().copy()).resize((448,288));frame.paste(close,(656,480))
            draw=ImageDraw.Draw(frame);draw.text((20,12),title,font=font,fill=(225,239,244));draw.text((20,45),f'{elapsed:07.2f} / {end:07.2f} s | {phase}',font=small,fill=(120,219,197))
            draw.rectangle((654,452,1106,478),fill=(14,25,35));draw.text((666,455),'Recorded state / close view',font=small,fill=(225,239,244))
            writer.append_data(np.array(frame));chapters[-1]['frames']+=1;total+=1
            if total%1200==0:print('RENDER',total,'/',len(times),flush=True)
            if total==1 or total==len(times):frame.save(output/('first.png' if total==1 else 'last.png'))
    finally:
        if writer:writer.close()
        renderer.close()
    for row in chapters:
        path=directory/row['path'];row.update(duration_s=row['frames']/fps,end_s=row['start_s']+row['frames']/fps,bytes=path.stat().st_size,sha256=sha(path))
        if path.stat().st_size>95*1024*1024:raise ValueError('Chapter exceeds transport budget; rerender with shorter chapters')
    for name in ['result.json','verification.json','workcell.xml']:
        if sha(directory/name)!=pins[name]:raise ValueError('Execution evidence changed during rendering')
    manifest=dict(schema_version='sciencegym.recorded_playback.v1',presentation_only=True,kind=kind,fps=fps,
                  frames=total,trace_seconds=end,chapters=chapters,input_sha256=pins,renderer_sha256=sha(Path(__file__)),
                  payload_interpolation=False,whole_paper_validated=False,
                  lighting='Indexed solar direction plus ambient fill' if kind=='reflector' else 'Workcell lighting with ambient fill')
    (directory/'playback_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--kind',choices=['assembly','reflector'],required=True);parser.add_argument('--fps',type=int,default=12);args=parser.parse_args()
    record=render(args.directory,args.kind,args.fps);print(json.dumps(dict(frames=record['frames'],chapters=len(record['chapters']),trace_seconds=record['trace_seconds']),indent=2))
