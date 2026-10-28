"""Physical disturbance test of the selected spring brake, not a robot task.

External test forces are explicitly recorded. They probe frictional retention
and overload slip; there are no payload pose assignments or hidden holds.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from reflector_world import build
from run_reflector import ReflectorRobot
from world import HERE


def run():
    out=HERE/'runs/reflector_debug/brake_load';out.mkdir(parents=True,exist_ok=True)
    if (out/'result.json').exists():raise ValueError('Choose a new test directory rather than replacing retained evidence')
    configuration=build(out/'workcell.xml');robot=ReflectorRobot(out/'workcell.xml');bid=robot.model.body('carriage').id
    observations=[];passed=False
    try:
        initial=robot.position('carriage');robot.data.xfrc_applied[bid,0]=1.;robot.advance(1.)
        loaded=robot.position('carriage');observations.append(dict(condition='1_N_shear',force_N=[1,0,0],duration_s=1.,time_s=float(robot.data.time),
             displacement_m=float(np.linalg.norm(loaded-initial)),mechanism=robot.mechanism()))
        robot.data.xfrc_applied[bid,:]=0.;robot.advance(60.)
        settled=robot.position('carriage');observations.append(dict(condition='60_s_retained_wait',force_N=[0,0,0],duration_s=60.,time_s=float(robot.data.time),
             displacement_m=float(np.linalg.norm(settled-initial)),mechanism=robot.mechanism()))
        robot.data.xfrc_applied[bid,0]=-5.;robot.advance(.2)
        overloaded=robot.position('carriage');observations.append(dict(condition='5_N_overload_expected_slip',force_N=[-5,0,0],duration_s=.2,time_s=float(robot.data.time),
             displacement_m=float(np.linalg.norm(overloaded-settled)),mechanism=robot.mechanism()))
        passed=observations[0]['displacement_m']<.00025 and observations[1]['displacement_m']<.00025 and observations[2]['displacement_m']>.001
    finally:
        robot.data.xfrc_applied[bid,:]=0.;robot.close()
        np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        result=dict(passed=passed,configuration=configuration,observations=observations,whole_paper_validated=False,
            scope='Stationary nominal brake challenged by external loads; this is a mechanism test, not robot actuation evidence',
            input_sha256={n:sha(HERE/n) for n in ['test_reflector_brake.py','reflector_world.py','run_reflector.py','hardware_control.py','continuous_control.py','world.py','contact_safety.py']},
            artifacts_sha256={n:sha(out/n) for n in ['workcell.xml','physics_trace.npz']})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return passed


if __name__=='__main__':raise SystemExit(0 if run() else 1)
