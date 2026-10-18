"""Actuate the actual model-specific resistance-mode button through contact."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
from datetime import datetime,timezone
import numpy as np
from world import HERE
from dmm_world import build
from hardware_control import HardwareRobot
from cover_world import SIDE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--out',default='runs/dmm_debug');args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    previous=[out/n for n in ['workcell.xml','result.json','physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()]
    if previous:
        history=out/'history'/stamp;history.mkdir(parents=True)
        for p in previous:p.replace(history/p.name)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sources=['run_dmm.py','dmm_world.py','hardware_control.py','device_assets.py','continuous_control.py','contact_safety.py','control.py','world.py','geometry/keithley_2000/catalog.json']
    pins={n:sha(HERE/n) for n in sources};robot=None;passed=False;failure=None
    try:
        interfaces=build(out/'workcell.xml');pins['workcell.xml']=sha(out/'workcell.xml')
        robot=HardwareRobot(out/'workcell.xml',record=args.render,video_path=out/'execution.mp4' if args.render else None)
        target=next(i for i in interfaces if i['id']=='Ω4')
        robot.press_button(target['physical_body'],target['axis'],SIDE,target['travel_m'])
        robot.advance(.5)
        returned=float(robot.data.joint(target['physical_body']+'_travel').qpos[0])
        if abs(returned)>.0001:raise RuntimeError('Button did not return after release')
        robot.checkpoint('button_released',body=target['physical_body'],travel_m=returned)
        passed=True
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
            if args.render:
                import imageio.v2 as imageio
                imageio.imwrite(out/'final.png',robot.frames[-1])
        if any(sha(HERE/n)!=pins[n] for n in sources):passed=False;failure='Source changed during execution'
        result=dict(status='passed' if passed else 'failed',failure=failure,input_sha256=pins,attempt_id=stamp,
                    observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
                    whole_paper_validated=False,scope='One physical front-panel key on a model-specific Keithley 2000; no complete RTD wiring or calibration credit',
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
