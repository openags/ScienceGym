"""Render two camera views from a verified execution trace, without dynamics.

State assignment here is playback only. The execution controller and original
trace remain unchanged; input/output hashes distinguish this presentation.
"""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
from load_model import load
from world import HERE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='runs/continuous');parser.add_argument('--fps',type=int,default=10);args=parser.parse_args()
    out=HERE/args.run;receipt=json.loads((out/'result.json').read_text())
    if receipt['status']!='passed':raise ValueError('Only an independently passed execution may receive a verified playback')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ['physics_trace.npz']:
        if sha(out/name)!=receipt['artifacts_sha256'][name]:raise ValueError('Trace changed after execution')
    if sha(out/'workcell.xml')!=receipt['input_sha256']['workcell.xml']:raise ValueError('Scene changed after execution')
    model=load(out/'workcell.xml');data=mujoco.MjData(model);trace=np.load(out/'physics_trace.npz')
    renderer=mujoco.Renderer(model,height=600,width=960)
    overview=mujoco.MjvCamera();overview.lookat[:]=[.42,-.09,.94];overview.distance=1.55;overview.azimuth=135;overview.elevation=-30
    detail=mujoco.MjvCamera();detail.distance=.45;detail.azimuth=110;detail.elevation=-28
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    lifts=[x for x in receipt['observations'] if x['label']=='edge_lift_observed']
    intervals=[];start=0
    for lift in lifts:
        released=next(x for x in receipt['observations'] if x['label']=='support_observed' and x.get('body')==lift['body'] and x['time_s']>lift['time_s'])
        intervals.append((start,released['time_s'],lift['body']));start=released['time_s']
    target=np.array([.48,.12,.86]);count=0
    times=np.arange(trace['time'][0],trace['time'][-1],1/args.fps)
    with imageio.get_writer(out/'detail_playback.mp4',fps=args.fps,codec='libx264',quality=7,ffmpeg_params=['-threads','8']) as writer:
        for time in times:
            index=int(np.argmin(abs(trace['time']-time)))
            data.qpos[:]=trace['qpos'][index];data.qvel[:]=trace['qvel'][index];data.ctrl[:]=trace['ctrl'][index]
            mujoco.mj_forward(model,data)
            body=next((name for a,b,name in intervals if a<=time<=b),'foam_lower')
            target=.82*target+.18*data.body(body).xpos;detail.lookat[:]=target
            renderer.update_scene(data,overview);left=renderer.render().copy()
            renderer.update_scene(data,detail);right=renderer.render().copy()
            frame=Image.new('RGB',(1920,660),(19,27,35));frame.paste(Image.fromarray(left),(0,60));frame.paste(Image.fromarray(right),(960,60))
            draw=ImageDraw.Draw(frame);draw.text((24,18),'PHYSICS TRACE | 6-layer assembly and return',font=font,fill=(230,235,239))
            draw.text((990,18),f'{time:6.1f} s | {body} | recorded state',font=font,fill=(230,235,239))
            writer.append_data(np.asarray(frame));count+=1
            if count%600==0:print('RENDER',count,len(times),flush=True)
    renderer.close()
    report=dict(presentation_only=True,source_execution_status=receipt['status'],whole_paper_validated=False,
                input_sha256={n:sha(out/n) for n in ['result.json','workcell.xml','physics_trace.npz']},
                renderer_sha256=sha(Path(__file__)),frames=count,fps=args.fps,
                output_sha256=sha(out/'detail_playback.mp4'),scope='Camera playback of the recorded six-layer physics; not new execution and not the full paper')
    (out/'playback_receipt.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
