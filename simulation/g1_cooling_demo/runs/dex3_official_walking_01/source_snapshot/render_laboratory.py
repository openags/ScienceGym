"""Render the recorded contact plant inside its complete, unchanged laboratory."""
import os
os.environ.setdefault('MUJOCO_GL', 'egl')
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import mujoco
import numpy as np
from PIL import Image


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(folder, movie=False, follow_robot=False):
    folder = Path(folder).resolve()
    result = json.loads((folder/'result.json').read_text())
    if result.get('environment') != 'existing_complete_laboratory':
        raise ValueError('Expected the complete laboratory contact plant')
    model = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    data = mujoco.MjData(model)
    trace = dict(np.load(folder/'trace.npz'))
    # Presentation-only transfer for GLTF's linear factors and image origin.
    # Geometry, camera sensor records and the physical trace stay untouched.
    model.mat_rgba[:, :3] = np.clip(model.mat_rgba[:, :3], 0, 1)**(1/2.2)
    for i in range(model.ntex):
        if not model.texture(i).name.startswith('lab_texture_'):
            continue
        start = model.tex_adr[i]
        h, w, c = model.tex_height[i], model.tex_width[i], model.tex_nchannel[i]
        pixels = model.tex_data[start:start+h*w*c].reshape(h, w, c)
        pixels[:] = pixels[::-1].copy()
    model.vis.headlight.ambient[:] = .5
    model.vis.headlight.diffuse[:] = .5
    renderer = mujoco.Renderer(model, height=720, width=1280, max_geom=max(12000, model.ngeom+1000))
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [.45, 0, .85]
    camera.azimuth = 45
    camera.elevation = -12

    def frame(t):
        i = min(np.searchsorted(trace['time'], t), len(trace['time'])-1)
        data.qpos[:] = trace['qpos'][i]
        mujoco.mj_forward(model, data)
        u = float(np.clip(t/8, 0, 1)); u = u*u*(3-2*u)
        camera.distance = 3.5-.65*u
        if follow_robot:
            camera.lookat[:] = data.body('pelvis').xpos + [.15,0,.15]
            camera.distance = 3.4
            camera.azimuth = 74
            camera.elevation = -15
        renderer.update_scene(data, camera=camera, scene_option=option)
        return renderer.render().copy()

    stills = [('first',0),('grasp',14),('lift',21),('place',30),('return_lift',57),('last',trace['time'][-1])]
    if follow_robot:
        stills = [('first',0),('start',2),('walking',4),('braking',result.get('stop_at_s',6)),('parked',9),('last',trace['time'][-1])]
    for name,t in stills:
        Image.fromarray(frame(t)).save(folder/(name+'.png'))
    times = np.arange(int(np.ceil((trace['time'][-1]-1e-8)*24)))/24
    if movie:
        temporary = folder/'episode.rendering.mp4'
        encoder = subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
            '-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','23',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(temporary)], stdin=subprocess.PIPE)
        started = time.monotonic()
        try:
            for i,t in enumerate(times):
                encoder.stdin.write(frame(t).tobytes())
                if i%240 == 0:
                    print('frame',i,'/',len(times),'wall_s',round(time.monotonic()-started,1),flush=True)
            encoder.stdin.close()
            if encoder.wait() != 0:
                raise RuntimeError('Video encoding failed')
            temporary.replace(folder/'episode.mp4')
        finally:
            if encoder.poll() is None:
                encoder.kill(); encoder.wait()
    renderer.close()
    receipt = dict(renderer_sha256=sha(__file__), trace_sha256=sha(folder/'trace.npz'),
        world_sha256=sha(folder/'world.xml'), fps=24, frame_count=len(times), continuous=True,
        sample_rule='First recorded state at or after each frame time; no invented poses or scene resets',
        movie=movie, watermarks=False, text_overlays=False,
        presentation_adjustments=['GLTF linear material factors to display gamma 2.2',
            'GLTF texture image origin correction', 'Headlight ambient/diffuse 0.5',
            'Continuous observation camera approach during first eight seconds'],
        physics_scope='Recorded laboratory carrier transport and return; other equipment fixed; no campaign qualification')
    if movie:
        receipt['video_sha256'] = sha(folder/'episode.mp4')
    if follow_robot:
        receipt['physics_scope'] = 'Recorded unloaded walking and stationary-control handoff; no carrying or campaign qualification'
        receipt['presentation_adjustments'][-1] = 'Continuous camera translation following the recorded pelvis'
    (folder/'render_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('render_complete', str(folder), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--movie', action='store_true')
    parser.add_argument('--follow-robot', action='store_true')
    args = parser.parse_args()
    render(args.folder, args.movie, args.follow_robot)
