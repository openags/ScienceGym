"""Render hypothetical arm-search states in the retained full laboratory.

These images are geometry review, not physics execution or a demo video.
"""
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_hand import initialize_cover, ArmIK, mimic
from observations import StateEstimate


def main():
    run = BASE / 'runs/ftir_cover_13'
    report = json.loads((HERE/'rrt_fast.json').read_text())
    plan = next(p for p in report['full_paths'] if p['passed'])
    candidate = json.loads((HERE/'review.json').read_text())['candidates'][plan['candidate']]
    cm = mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'))
    cd = initialize_cover(cm, [5.95, -5.32])
    estimate = StateEstimate(cm, cd)
    sensors = np.load(run/'sensor_observations.npz')
    i = int(np.argmin(abs(sensors['time_s']-2.)))
    packet = {k:sensors[k][i] for k in sensors.files if k != 'right_touch_n'}
    packet['depth'] = None
    estimate.update(packet)
    cd.qpos[1] += .12
    ik = ArmIK(cm)
    initial = cd.qpos.copy()
    m = mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    d = initialize_cover(m, [5.95, -5.20])
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    option.sitegroup[:] = 0
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [6.12, -5.35, 1.02]
    camera.distance = 1.90
    camera.azimuth = 135
    camera.elevation = -20
    states = [('entry_'+str(i), q) for i,q in enumerate(plan['arm_path'])]
    states += [('contact', next(s['arm_q'] for s in plan['states']
                               if s['phase']=='align' and s['fraction']==1.))]
    out = HERE/'path_images'
    out.mkdir(exist_ok=True)
    renderer = mujoco.Renderer(m, height=720, width=960, max_geom=m.ngeom+1000)
    for name,q in states:
        cd.qpos[:] = initial
        cd.qpos[ik.qa] = q
        for n,v in candidate['q'].items():cd.joint(n).qpos[0] = v
        mimic(cm, cd)
        d.qpos[:7] = cd.qpos[:7]
        for j in range(cm.njnt):
            if cm.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE:
                d.joint(cm.joint(j).name).qpos[0] = cd.qpos[cm.jnt_qposadr[j]]
        mujoco.mj_forward(m,d)
        renderer.update_scene(d,camera=camera,scene_option=option)
        Image.fromarray(renderer.render()).save(out/(name+'.png'))
    renderer.close()
    (out/'scope.json').write_text(json.dumps(dict(
        source='rrt_fast.json', candidate=plan['candidate'],
        physical_execution=False, hypothetical_prepared_posture=True,
        images=[name+'.png' for name,_ in states]),indent=2)+'\n')


if __name__=='__main__':main()
