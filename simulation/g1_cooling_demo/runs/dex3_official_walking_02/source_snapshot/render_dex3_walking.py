"""Render recorded walking in the full laboratory without motion edits."""
import argparse
import json
from pathlib import Path
import subprocess

import mujoco
import numpy as np
from PIL import Image

from run_dex3_walking import sha


def render(folder):
    folder = Path(folder).resolve()
    result = json.loads((folder / 'result.json').read_text())
    contract = json.loads((folder / 'contract.json').read_text())
    assert sha(folder / 'trace.npz') == result['trace_sha256']
    assert sha(folder / 'world.xml') == contract['model_sha256']
    with np.load(folder / 'trace.npz') as archive:
        times, positions = archive['time'], archive['qpos']
    m = mujoco.MjModel.from_xml_path(str(folder / 'world.xml'))
    d = mujoco.MjData(m)
    m.mat_rgba[:, :3] = np.clip(m.mat_rgba[:, :3], 0, 1)**(1 / 2.2)
    for i in range(m.ntex):
        if not m.texture(i).name.startswith('lab_texture_'):
            continue
        start, h, w, c = m.tex_adr[i], m.tex_height[i], m.tex_width[i], m.tex_nchannel[i]
        pixels = m.tex_data[start:start + h * w * c].reshape(h, w, c)
        pixels[:] = pixels[::-1].copy()
    m.vis.headlight.ambient[:] = .3
    m.vis.headlight.diffuse[:] = .3
    camera = mujoco.MjvCamera()
    camera.lookat[:] = [-.52, .1, 1.]
    camera.distance, camera.azimuth, camera.elevation = 3.4, -45., -25.
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    renderer = mujoco.Renderer(m, 720, 1280, max_geom=m.ngeom + 1000)
    fps = 24
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo',
               '-pixel_format', 'rgb24', '-video_size', '1280x720', '-framerate', str(fps),
               '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(folder / 'overview.mp4')]
    frames = []
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for k, t in enumerate(np.arange(0., times[-1], 1 / fps)):
            i = min(int(np.searchsorted(times, t)), len(times) - 1)
            d.qpos[:] = positions[i]
            mujoco.mj_forward(m, d)
            renderer.update_scene(d, camera=camera, scene_option=option)
            pixels = renderer.render().copy()
            encoder.stdin.write(pixels.tobytes())
            frames.append(dict(video_frame=k, trace_index=i, time_s=float(times[i])))
            if k == 0:
                Image.fromarray(pixels).save(folder / 'overview_initial.png')
        if frames:
            Image.fromarray(pixels).save(folder / 'overview_last.png')
    finally:
        renderer.close()
        encoder.stdin.close()
        code = encoder.wait()
    if code:
        raise RuntimeError('Video encoder failed')
    report = dict(scope=__doc__, trace_sha256=result['trace_sha256'], model_sha256=contract['model_sha256'],
                  renderer_sha256=sha(__file__), movie_sha256=sha(folder / 'overview.mp4'),
                  fps=fps, frames=frames, physics_acceptance_implied=False)
    (folder / 'render_receipt.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder')
    render(p.parse_args().folder)
