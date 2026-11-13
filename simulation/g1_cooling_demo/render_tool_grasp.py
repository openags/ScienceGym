"""Render authored initial setup or recorded states without changing geometry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

os.environ.setdefault('MUJOCO_GL', 'egl')
import mujoco
import numpy as np
from PIL import Image


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render(folder, movie=False, sample_times=(), model_run=None):
    folder = Path(folder).resolve()
    model_folder = folder if model_run is None else Path(model_run).resolve()
    model = mujoco.MjModel.from_xml_path(str(model_folder/'world.xml')); data = mujoco.MjData(model)
    contract = json.loads((model_folder/'contract.json').read_text())
    trace = dict(np.load(folder/'trace.npz')) if (folder/'trace.npz').exists() else None
    if movie and trace is None: raise ValueError('A movie requires an actual recorded trajectory')
    data.qpos[:] = contract['initial_qpos']; mujoco.mj_forward(model, data)
    if model_run is not None:
        result = json.loads((folder/'result.json').read_text())
        assert trace is not None and result['actor_contract_sha256'] == sha(model_folder/'contract.json')
        assert result['trace_sha256'] == sha(folder/'trace.npz')
        assert contract['model_sha256'] == sha(model_folder/'world.xml')
        data.qpos[:] = trace['qpos'][0]; mujoco.mj_forward(model, data)
    start_time = 0. if trace is None else float(trace['time'][0])
    model.mat_rgba[:, :3] = np.clip(model.mat_rgba[:, :3], 0, 1)**(1/2.2)
    for i in range(model.ntex):
        if not model.texture(i).name.startswith('lab_texture_'): continue
        start = model.tex_adr[i]; h, w, c = model.tex_height[i], model.tex_width[i], model.tex_nchannel[i]
        pixels = model.tex_data[start:start+h*w*c].reshape(h, w, c); pixels[:] = pixels[::-1].copy()
    model.vis.headlight.ambient[:] = .5; model.vis.headlight.diffuse[:] = .5
    renderer = mujoco.Renderer(model, height=720, width=1280, max_geom=model.ngeom+1000)
    option = mujoco.MjvOption(); option.geomgroup[3] = 0; option.sitegroup[:] = 0
    camera = mujoco.MjvCamera(); cameras = {}
    pelvis = data.body('pelvis').xpos.copy(); tool = data.body('tweezer').xpos.copy()
    cameras['overview'] = dict(lookat=(pelvis+[.12, 0., .15]).tolist(), distance=2.5, azimuth=135., elevation=-18.)
    cameras['contact'] = dict(lookat=(tool+[-.05, 0., .015]).tolist(), distance=.42, azimuth=135., elevation=-33.)

    def frame(t, view):
        if trace is not None:
            i = min(int(np.searchsorted(trace['time'], t)), len(trace['time'])-1)
            data.qpos[:] = trace['qpos'][i]; mujoco.mj_forward(model, data)
        for key, value in cameras[view].items():
            if key == 'lookat': camera.lookat[:] = value
            else: setattr(camera, key, value)
        renderer.update_scene(data, camera=camera, scene_option=option)
        return renderer.render().copy()

    outputs = []
    for view in cameras:
        name = view+'_initial.png'; Image.fromarray(frame(start_time, view)).save(folder/name); outputs.append(name)
        if trace is not None:
            name = view+'_last.png'; Image.fromarray(frame(float(trace['time'][-1]), view)).save(folder/name); outputs.append(name)
    if sample_times and trace is None: raise ValueError('Timed frames require an actual recorded trajectory')
    for t in sample_times:
        if not start_time <= t <= float(trace['time'][-1]): raise ValueError('Requested frame is outside the trace')
        name = f'contact_{t:.3f}s.png'; Image.fromarray(frame(t, 'contact')).save(folder/name); outputs.append(name)
    if movie:
        times = start_time + np.arange(int(np.ceil((float(trace['time'][-1])-start_time)*24)))/24
        for view in cameras:
            name = view+'.mp4'
            encoder = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                '-s', '1280x720', '-r', '24', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(folder/name)], stdin=subprocess.PIPE)
            try:
                for t in times: encoder.stdin.write(frame(float(t), view).tobytes())
                encoder.stdin.close()
                if encoder.wait() != 0: raise RuntimeError('ffmpeg failed')
            finally:
                if encoder.poll() is None: encoder.kill(); encoder.wait()
            outputs.append(name)
    renderer.close()
    receipt = dict(scope='Authored initial setup only' if trace is None else 'Recorded attempted execution; consult independent verdict',
        world_sha256=sha(model_folder/'world.xml'), trace_sha256=None if trace is None else sha(folder/'trace.npz'),
        renderer_sha256=sha(__file__), cameras=cameras, movie=movie, fps=24, sample_times_s=list(sample_times),
        sample_rule='First recorded state at or after the frame time; no invented states',
        presentation_adjustments=['Material gamma and texture origin correction', 'Headlight ambient/diffuse 0.5'],
        outputs={name: sha(folder/name) for name in outputs}, qualified_grasp=False, qualified_paper_branch=False)
    if model_run is not None:
        receipt.update(scope='Restored-checkpoint physical diagnostic only; not a continuous pickup recording',
                       actor_contract_sha256=sha(model_folder/'contract.json'),
                       trace_time_origin_s=start_time, continuous_pickup_carry=False)
    (folder/'render_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(outputs=outputs)), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('--movie', action='store_true')
    p.add_argument('--sample-times', type=float, nargs='*', default=[])
    p.add_argument('--model-run', help='Frozen model for a restored-checkpoint diagnostic')
    a = p.parse_args(); render(a.folder, a.movie, a.sample_times, a.model_run)
