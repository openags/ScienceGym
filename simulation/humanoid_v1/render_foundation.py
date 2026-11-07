"""Export the exact accepted body-only recording and its source-mesh preview."""
import os
os.environ.setdefault('MUJOCO_GL', 'egl')
import argparse
import json
from pathlib import Path
import numpy as np
import mujoco
import trimesh
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
from world import load, sha, ASSET


def render(directory):
    directory = Path(directory)
    result = json.loads((directory / 'result.json').read_text())
    verification = json.loads((directory / 'verification.json').read_text())
    if not verification['passed'] or verification['result_sha256'] != sha(directory / 'result.json'):
        raise ValueError('Render only independently verified exact recordings')
    if sha(directory / 'physics_trace.npz') != result['artifacts_sha256']['physics_trace.npz']:
        raise ValueError('Trace changed')
    with np.load(directory / 'physics_trace.npz') as archive: trace = {k: archive[k] for k in archive.files}
    model = load(directory / 'workcell.xml'); data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=900, width=1280)
    options = mujoco.MjvOption(); options.geomgroup[0] = 0; options.geomgroup[3] = 1
    fps = 20; times = np.arange(round(result['simulated_seconds'] * fps) + 1) / fps
    output = directory / 'playback'; output.mkdir(exist_ok=True)
    if (output / 'episode.mp4').exists(): raise ValueError('Playback already exists')
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
    indices = []
    with imageio.get_writer(output / 'episode.mp4', fps=fps, codec='libx264', quality=8, macro_block_size=1) as writer:
        for i, at in enumerate(times):
            k = int(np.argmin(abs(trace['time'] - at))); indices.append(k)
            data.qpos[:] = trace['qpos'][k]; data.qvel[:] = trace['qvel'][k]
            data.ctrl[:] = trace['ctrl'][k]; mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera='overview', scene_option=options)
            frame = Image.fromarray(renderer.render()); draw = ImageDraw.Draw(frame)
            draw.rectangle((0, 0, 1280, 78), fill=(14, 35, 44))
            draw.text((22, 10), 'UNITREE H2 | Recorded whole-body foundation', fill='white', font=font)
            draw.text((22, 44), 'Dex5-S Pro hands NOT integrated | No grasp or paper-task acceptance', fill=(255, 210, 130), font=small)
            phase = 'Settle standing' if at < 3 else 'Bilateral wrist reach' if at < 8 else 'Hold reach' if at < 11 else 'Return wrists' if at < 16 else 'Hold final stance'
            draw.rectangle((0, 850, 1280, 900), fill=(14, 35, 44))
            draw.text((22, 861), f'{at:05.2f} / {times[-1]:.2f} s  |  {phase}', fill='white', font=font)
            writer.append_data(np.asarray(frame))
            if i in [0, 200, len(times) - 1]:
                frame.save(output / ('first.png' if i == 0 else 'reach.png' if i == 200 else 'last.png'))
    renderer.close()
    manifest = dict(fps=fps, frames=len(times), simulated_seconds=result['simulated_seconds'],
                    source_frame_indices=indices, terminal_state_included=indices[-1] == len(trace['time']) - 1,
                    video='playback/episode.mp4', video_sha256=sha(output / 'episode.mp4'),
                    result_sha256=sha(directory / 'result.json'), verification_sha256=sha(directory / 'verification.json'),
                    renderer_sha256=sha(Path(__file__)), manipulation_accepted=False)
    (directory / 'playback_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Export the compiled original visual meshes in the recorded settled pose.
    k = int(np.argmin(abs(trace['time'] - 3.)))
    data.qpos[:] = trace['qpos'][k]; mujoco.mj_forward(model, data)
    scene = trimesh.Scene()
    for g in range(model.ngeom):
        if model.geom_group[g] != 1 or model.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH: continue
        mesh_id = int(model.geom_dataid[g]); va = int(model.mesh_vertadr[mesh_id]); fa = int(model.mesh_faceadr[mesh_id])
        mesh = trimesh.Trimesh(vertices=model.mesh_vert[va:va + model.mesh_vertnum[mesh_id]],
                               faces=model.mesh_face[fa:fa + model.mesh_facenum[mesh_id]], process=False)
        mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=(model.geom_rgba[g] * 255).astype(np.uint8))
        transform = np.eye(4); transform[:3, :3] = data.geom_xmat[g].reshape(3, 3); transform[:3, 3] = data.geom_xpos[g]
        scene.add_geometry(mesh, geom_name=model.geom(g).name, node_name=model.geom(g).name, transform=transform)
    dest = ASSET / 'geometry'; dest.mkdir(exist_ok=True)
    preview = dest / 'h2_settled.glb'; preview.write_bytes(scene.export(file_type='glb'))
    receipt = dict(source_sha256=sha(ASSET / 'SOURCE.json'), result_sha256=sha(directory / 'result.json'),
                   trace_sha256=sha(directory / 'physics_trace.npz'), recorded_time_s=float(trace['time'][k]),
                   glb_sha256=sha(preview), visual_meshes=len(scene.geometry), bounds_m=scene.bounds.tolist(),
                   hand_model_present=False, scope='Source H2 body meshes at a recorded stance; rigid wrist geometry is not an articulated Dex5-S hand')
    (ASSET / 'preview_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(frames=len(times), glb_meshes=len(scene.geometry)), indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('directory', type=Path)
    render(p.parse_args().directory)
