"""Pick a cabled RTD, insert its sheath and retrieve it without pose writes."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
from datetime import datetime,timezone
import numpy as np
import mujoco
from world import HERE
from hardware_control import HardwareRobot
from rtd_world import build,PARK,TARGET
from control import ExecutionFailure
from support_observation import support_load


def put(robot,target,support):
    def held():
        contacts=robot.contacts('rtd')
        if not {'left_finger','right_finger'}<={x['other'] for x in contacts if x['force_n']>.02}:raise ExecutionFailure('RTD grip lost')
        body=robot.data.body('rtd').xmat.reshape(3,3)
        return body.T@(robot.data.site_xpos[robot.site]-robot.position('rtd')),body.T@robot.data.site_xmat[robot.site].reshape(3,3)
    start=robot.position('rtd')
    for u in np.linspace(0,1,11)[1:]:
        offset,rotation=held();p=np.r_[start[:2]+u*(target[:2]-start[:2]),max(start[2],target[2]+.13)]
        robot.move(p+offset,rotation,duration=.5)
    for h in np.r_[np.linspace(.10,.010,20),np.arange(.0095,.0001,-.0005)]:
        offset,rotation=held();robot.move(target+offset+[0,0,h],rotation,duration=.18)
    robot.finger(.034);robot.move(robot.data.site_xpos[robot.site]+[0,0,.15],rotation,duration=2);robot.advance(1)
    # Native sleep can omit support contacts: recompute in a separate awake
    # observer, without modifying the execution world's state.
    from device_assets import load
    m=load(robot.source_path);m.opt.enableflags &= ~int(mujoco.mjtEnableBit.mjENBL_SLEEP)
    d=mujoco.MjData(m);d.qpos[:]=robot.data.qpos;d.qvel[:]=robot.data.qvel;d.ctrl[:]=robot.data.ctrl;mujoco.mj_forward(m,d)
    actual=d.body('rtd').xpos;error=float(np.linalg.norm(actual-target));tilt=float(np.arccos(np.clip(d.body('rtd').xmat[8],-1,1)))
    load_obs=support_load(m,d,'rtd',support)
    result=dict(position_m=actual.tolist(),error_m=error,tilt_rad=tilt,support=support,support_observation=load_obs)
    robot.checkpoint('rtd_released_support',**result)
    if error>.001 or tilt>.02 or load_obs['vertical_force_n']<.2:raise ExecutionFailure('RTD insertion support invalid: '+str(result))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--out',default='runs/rtd_debug');args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/n for n in ['workcell.xml','result.json','physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()]
    if old:
        history=out/'history'/stamp;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sources=['run_rtd.py','rtd_world.py','hardware_control.py','device_assets.py','continuous_control.py','control.py','world.py','contact_safety.py','support_observation.py','geometry/omega_pm_rtd/catalog.json']
    pins={n:sha(HERE/n) for n in sources};robot=None;passed=False;failure=None;configuration=None
    try:
        configuration=build(out/'workcell.xml');pins['workcell.xml']=sha(out/'workcell.xml')
        robot=HardwareRobot(out/'workcell.xml',record=args.render,video_path=out/'execution.mp4' if args.render else None);robot.source_path=out/'workcell.xml'
        for target,support in [(TARGET,'calibration_block'),(PARK,'rtd_stand')]:
            robot.grasp('rtd',.0254,8.,lift=.14);put(robot,target,support)
        passed=True
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
            if args.render:
                import imageio.v2 as imageio
                imageio.imwrite(out/'final.png',robot.frames[-1])
        if any(sha(HERE/n)!=pins[n] for n in sources):passed=False;failure='Source changed during execution'
        result=dict(status='passed' if passed else 'failed',failure=failure,configuration=configuration,input_sha256=pins,
                    simulated_seconds=float(robot.data.time) if robot else 0,observations=robot.timeline if robot else [],
                    whole_paper_validated=False,scope='Manufacturer-sized RTD with attached cable inserted into a selected copper bore and retrieved; no bath, four-wire circuit or calibrated temperature data',
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
