"""Render recorded physics states. Never create or change simulation outcomes."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import mujoco
from PIL import Image,ImageDraw,ImageFont


def render(folder, movie=False):
    folder=Path(folder);m=mujoco.MjModel.from_xml_path(str(folder/'world.xml'));d=mujoco.MjData(m)
    policy=json.loads((folder/'policy_observations.json').read_text());policy_times=np.array([x['time_s'] for x in policy])
    labels={'locate':'Locate carrier','raise':'Raise hands','approach':'Approach','lower_to_grip':'Lower hands','close':'Establish grip','settle_grip':'Settle grip','lift':'Lift','confirm_lift':'Check lift in depth','transfer':'Transport','confirm_transfer':'Check destination','place':'Place','confirm_place':'Check table support','release':'Release','verify_release':'Confirm release','retract':'Retract hands','inspect':'Inspect placement','complete':'Park / stable hold'}
    trace=np.load(folder/'trace.npz');r=mujoco.Renderer(m,height=900,width=1200)
    detail=mujoco.Renderer(m,height=270,width=360)
    cam=mujoco.MjvCamera();cam.lookat[:]=[.34,0,.85];cam.distance=2.5;cam.azimuth=130;cam.elevation=-15
    close=mujoco.MjvCamera();close.lookat[:]=[.48,.02,1.01];close.distance=.68;close.azimuth=145;close.elevation=-18
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    def frame(i):
        d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d);r.update_scene(d,camera=cam,scene_option=opt)
        image=Image.fromarray(r.render());draw=ImageDraw.Draw(image);draw.rectangle([0,0,1200,62],fill='#10262d');draw.text((20,12),'ScienceGym | Unitree G1 + Inspire FTP | continuous carrier transport',font=font,fill='white')
        record=policy[max(0,min(np.searchsorted(policy_times,trace['time'][i],side='right')-1,len(policy)-1))]
        label=('Outbound' if record['phase']==0 else 'Return')+' / '+labels[record['state']]
        draw.text((20,38),f"{trace['time'][i]:.2f} / {trace['time'][-1]:.2f} s | {label} | full paper NOT validated",font=font,fill='#d9b984')
        detail.update_scene(d,camera=close,scene_option=opt)
        image.paste(Image.fromarray(detail.render()),(820,600));draw.rectangle([820,572,1180,600],fill='#10262d');draw.text((830,576),'Recorded hand / tray contact',font=font,fill='white')
        return np.asarray(image)
    for name,t in [('first',0),('grasp',14),('lift',21),('place',30),('return_lift',57),('last',float(trace['time'][-1]))]:
        i=min(np.searchsorted(trace['time'],t),len(trace['time'])-1);Image.fromarray(frame(i)).save(folder/(name+'.png'))
    if movie:
        import imageio.v2 as imageio
        writer=imageio.get_writer(folder/'episode.mp4',fps=25,codec='libx264',quality=8,macro_block_size=4)
        for t in np.arange(0,trace['time'][-1]+.0001,.04):writer.append_data(frame(min(np.searchsorted(trace['time'],t),len(trace['time'])-1)))
        writer.close()
    (folder/'render_receipt.json').write_text(json.dumps(dict(renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),trace_sha256=hashlib.sha256((folder/'trace.npz').read_bytes()).hexdigest(),fps=25,continuous=True,scope='Recorded states in one uninterrupted simulation; no scene reset or interpolated outcome'),indent=2)+'\n')
    r.close();detail.close();print(json.dumps(dict(rendered=str(folder),movie=movie)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('--movie',action='store_true');a=p.parse_args();render(a.folder,a.movie)
