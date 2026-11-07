"""Presentation-only rendering of a verified contact trace; never execution."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont
from device_assets import load


def render(directory,body='rtd'):
    directory=Path(directory);receipt=json.loads((directory/'verification.json').read_text())
    if not receipt['passed']:raise ValueError('Refusing to present a failed trace as accepted execution')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    pins={name:sha(directory/name) for name in ['result.json','verification.json','workcell.xml','physics_trace.npz']}
    with np.load(directory/'physics_trace.npz') as compressed:trace={k:compressed[k] for k in compressed.files}
    m=load(directory/'workcell.xml');d=mujoco.MjData(m);renderer=mujoco.Renderer(m,720,1120)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    overview=mujoco.MjvCamera();overview.lookat[:]=[.35,0,1.10];overview.distance=1.95;overview.azimuth=135;overview.elevation=-30
    detail=mujoco.MjvCamera();detail.distance=.34;detail.azimuth=140;detail.elevation=-20
    out=directory/'detail_playback.mp4';writer=imageio.get_writer(out,fps=20,codec='libx264',quality=8,macro_block_size=16)
    rows=json.loads((directory/'result.json').read_text())['observations'];end=float(trace['time'][-1]);frames=0
    releases=[r['time_s'] for r in rows if r['label']=='rtd_released_support'];lifts=[r['time_s'] for r in rows if r['label']=='grasp_and_lift_observed']
    try:
        for time in np.arange(0,end+1e-8,.05):
            index=int(np.argmin(abs(trace['time']-time)))
            # State writes belong only to this separate presentation process.
            # They are never used by the control/acceptance simulation.
            d.qpos[:]=trace['qpos'][index];d.qvel[:]=trace['qvel'][index];d.ctrl[:]=trace['ctrl'][index];mujoco.mj_forward(m,d)
            renderer.update_scene(d,overview);frame=Image.fromarray(renderer.render().copy())
            detail.lookat[:]=d.body(body).xpos+[0,0,.075]
            renderer.update_scene(d,detail);close=Image.fromarray(renderer.render().copy()).resize((448,288))
            frame.paste(close,(656,410));draw=ImageDraw.Draw(frame)
            draw.rectangle((0,0,1120,76),fill=(14,25,35));draw.text((20,12),'Cabled RTD: insert, release, retrieve',font=font,fill=(225,239,244))
            phase='Approach and grasp' if time<lifts[0] else 'Transport and insert' if time<releases[0] else 'Regrasp with cable clearance' if time<lifts[1] else 'Retrieve and return'
            draw.text((20,44),f'{time:05.2f} / {end:05.2f} s  |  {phase}',font=small,fill=(120,219,197))
            draw.rectangle((654,382,1106,408),fill=(14,25,35));draw.text((666,385),'Recorded contact simulation / detail',font=small,fill=(225,239,244))
            writer.append_data(np.array(frame));frames+=1
        frame.save(directory/'playback_preview.png')
    finally:writer.close();renderer.close()
    if any(sha(directory/name)!=digest for name,digest in pins.items()):raise RuntimeError('Trace changed during rendering')
    record=dict(presentation_only=True,source='verified recorded MuJoCo states',interpolated_payload_trajectory=False,
                input_sha256=pins,renderer_sha256=sha(Path(__file__)),frames=frames,fps=20,
                trace_seconds=end,video_sha256=sha(out),whole_paper_validated=False)
    (directory/'playback_receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args();render(args.directory)
