"""Capture native RGB-D at explicitly authored FTIR component starting poses.

These are setup candidates, not executed navigation or robot observations from
a completed trial. Only the root XY/yaw changes; equipment state is retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np
from PIL import Image

from ftir_vision import KeyRowObservation
from sensor_rendering import depth_renderer


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_run', type=Path)
    p.add_argument('base_frame', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--pose', nargs=3, type=float, action='append', required=True,
                   metavar=('X', 'Y', 'YAW'))
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    m = mujoco.MjModel.from_xml_path(str(a.source_run/'world.xml'))
    d = mujoco.MjData(m)
    with np.load(a.base_frame) as f:
        initial = f['authored_qpos'].copy()
    color = mujoco.Renderer(m, height=360, width=640, max_geom=m.ngeom+1000)
    depth = depth_renderer(m, 360, 640)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    rows = []
    try:
        for index, (x, y, yaw) in enumerate(a.pose):
            if not np.isfinite([x, y, yaw]).all():
                raise ValueError('Nonfinite authored initial pose')
            d.qpos[:] = initial
            d.qpos[:2] = [x, y]
            d.qpos[3:7] = [np.cos(yaw/2), 0., 0., np.sin(yaw/2)]
            mujoco.mj_forward(m, d)
            color.update_scene(d, camera='head_rgb', scene_option=option)
            rgb = color.render().copy()
            depth.update_scene(d, camera='head_depth', scene_option=option)
            z = depth.render().copy()
            detection = KeyRowObservation(m, d).observe(rgb, z)
            stem = 'view_%02d' % index
            np.savez_compressed(a.output/(stem+'.npz'), rgb=rgb, depth=z, authored_qpos=d.qpos)
            Image.fromarray(rgb).save(a.output/(stem+'.png'))
            rows.append(dict(xy=[x, y], yaw=yaw, detection=detection,
                frame=stem+'.npz', frame_sha256=sha(a.output/(stem+'.npz'))))
            print(json.dumps(dict(index=index, xy=[x, y], yaw=yaw,
                observed=bool(detection and detection['accepted']))), flush=True)
    finally:
        color.close()
        depth.close()
    pins = {}
    for name in [Path(__file__).name, 'ftir_vision.py', 'sensor_rendering.py']:
        src = Path(__file__).with_name(name)
        shutil.copyfile(src, a.output/name)
        pins[name] = sha(src)
    report = dict(scope=__doc__, source_model_sha256=sha(a.source_run/'world.xml'),
        base_frame_sha256=sha(a.base_frame), source_sha256=pins, samples=rows,
        physical_execution=False, qualified_navigation=False, qualified_ftir_press=False)
    (a.output/'review.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
