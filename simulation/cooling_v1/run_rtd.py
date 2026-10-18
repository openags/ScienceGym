"""Pick a cabled RTD, insert its sheath and retrieve it without pose writes."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
import numpy as np
import mujoco
from world import HERE
from hardware_control import HardwareRobot
from rtd_world import build,PARK,TARGET
from control import ExecutionFailure
from support_observation import support_load
from control import DOWN
from scipy.spatial.transform import Rotation


class RTDRobot(HardwareRobot):
    def contacts(self,body):
        records=[]
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'rtd_cable' for g in c.geom]
            if body not in names:continue
            f=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,f)
            records.append(dict(other=names[1-names.index(body)],force_n=float(f[0]),distance_m=float(c.dist)))
        return records


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
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--out',default='runs/rtd_debug');parser.add_argument('--flex-cable',action='store_true')
    parser.add_argument('--seed',type=int,default=0);parser.add_argument('--bore-diameter',type=float,default=.0066);args=parser.parse_args()
    if args.flex_cable and args.out=='runs/rtd_debug':args.out='runs/rtd_debug/flex'
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/n for n in ['workcell.xml','result.json','physics_trace.npz','execution.mp4','final.png','source_snapshot'] if (out/n).exists()]
    if old:
        history=out/'history'/stamp;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sources=['run_rtd.py','rtd_world.py','hardware_control.py','device_assets.py','continuous_control.py','control.py','world.py','contact_safety.py','support_observation.py','geometry/omega_pm_rtd/catalog.json']
    if args.flex_cable:sources.append('rtd_flex_world.py')
    pins={n:sha(HERE/n) for n in sources};robot=None;passed=False;failure=None;configuration=None
    for name in sources:
        target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/name,target)
    try:
        builder=build
        if args.flex_cable:
            from rtd_flex_world import build as builder
        configuration=builder(out/'workcell.xml',bore_diameter=args.bore_diameter);pins['workcell.xml']=sha(out/'workcell.xml')
        robot=RTDRobot(out/'workcell.xml',record=args.render,seed=args.seed,video_path=out/'execution.mp4' if args.render else None);robot.source_path=out/'workcell.xml'
        # The length-constrained string folds toward -Y during insertion;
        # the elastic rod retains its +X exit direction. The observed cable
        # routing determines the selected clear-side approach for each model.
        retrieval_yaw=np.pi/2 if args.flex_cable else 0.
        configuration['retrieval_grasp_yaw_rad']=retrieval_yaw
        configuration['retrieval_frame_basis']='Selected station frame for the observed cable route; not a source-reported robot trajectory'
        for target,support,yaw in [(TARGET,'calibration_block',0.),(PARK,'rtd_stand',retrieval_yaw)]:
            robot.grasp('rtd',.0254,8.,rotation=Rotation.from_euler('z',yaw).as_matrix()@DOWN,lift=.14)
            put(robot,target,support)
        passed=True
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
            if args.render:
                import imageio.v2 as imageio
                imageio.imwrite(out/'final.png',robot.frames[-1])
        if any(sha(HERE/n)!=pins[n] for n in sources):passed=False;failure='Source changed during execution'
        result=dict(status='passed' if passed else 'failed',failure=failure,configuration=configuration,input_sha256=pins,source_archive='source_snapshot',seed=args.seed,
                    simulated_seconds=float(robot.data.time) if robot else 0,observations=robot.timeline if robot else [],
                    whole_paper_validated=False,scope='Manufacturer-sized RTD with attached cable inserted into a selected copper bore and retrieved; no bath, four-wire circuit or calibrated temperature data',
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
