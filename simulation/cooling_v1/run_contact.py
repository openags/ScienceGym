"""Run observed contact operations and preserve failures as first-class results."""
import argparse
import json
import hashlib
from datetime import datetime,timezone
import mujoco
import numpy as np
from pathlib import Path
from world import HERE,TOP,assembly_scene,probe_scene,lid_scene,door_scene
from control import Robot,ExecutionFailure
from evaluate import assess


def execute(robot, scene):
    if scene=='assembly':
        robot.transfer('foam_lower',[.51,.13,TOP+.024+.0125],'assembly_base')
        robot.transfer('foam_upper',[.51,.13,TOP+.024+.025+.0125],'foam_lower')
        robot.transfer('emitter',[.51,.13,TOP+.024+.05+.00025],'foam_upper')
        robot.press()
    elif scene=='probe':
        robot.transfer('probe',[.53,.12,TOP+.064],'copper_block',.002)
        robot.transfer('probe',[.45,-.22,TOP+.064],'probe_stand',.003)
    elif scene=='lid':
        robot.transfer('baseline_lid',[.51,.13,TOP+.068],'aperture_support',.004)
        robot.transfer('baseline_lid',[.48,-.23,TOP+.012],'lid_stand',.004)
    elif scene=='door':
        robot.access_door(1.05)
        robot.access_door(.02)
    else:raise ValueError(scene)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--out',default='runs/contact');parser.add_argument('--seed',type=int,default=0);parser.add_argument('--scene',choices=['assembly','probe','lid','door'],default='assembly')
    args=parser.parse_args();out=HERE/args.out;out.mkdir(parents=True,exist_ok=True)
    attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/name for name in ['result.json','workcell.xml','physics_trace.npz','states.npz','execution.mp4','final.png'] if (out/name).exists()]
    if old:
        history=out/'history'/attempt;history.mkdir(parents=True)
        for file in old:file.replace(history/file.name)
    pending=dict(status='running',attempt_id=attempt,scene=args.scene,whole_paper_validated=False,observations=[])
    (out/'result.json').write_text(json.dumps(pending,indent=2)+'\n')
    scene=out/'workcell.xml'
    try:
        {'assembly':assembly_scene,'probe':probe_scene,'lid':lid_scene,'door':door_scene}[args.scene](scene)
        robot=Robot(scene,record=args.render,seed=args.seed)
    except Exception as error:
        pending.update(status='failed',failure=type(error).__name__+': '+str(error),physical_contact_execution=False)
        (out/'result.json').write_text(json.dumps(pending,indent=2)+'\n')
        print(pending['failure']);return False
    source_names=['world.py','control.py','load_model.py','evaluate.py','run_contact.py','robot_source.json','geometry/catalog.json','PHYSICS_SCOPE.json']
    hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in source_names}
    hashes['workcell.xml']=hashlib.sha256(scene.read_bytes()).hexdigest()
    status='failed';failure=None;evaluation=None
    try:
        execute(robot,args.scene)
        evaluation=assess(args.scene,robot)
        if not evaluation["passed"]:raise ExecutionFailure("independent goal predicates rejected execution")
        status='passed'
    except Exception as e:
        failure=type(e).__name__+': '+str(e);print(failure,flush=True)
    finally:
        if args.render:
            import imageio.v2 as imageio
            imageio.mimwrite(out/'execution.mp4',robot.frames,fps=10,codec='libx264',quality=7)
            imageio.imwrite(out/'final.png',robot.frames[-1])
            np.savez_compressed(out/'states.npz',time=[s['t'] for s in robot.states],qpos=[s['qpos'] for s in robot.states],qvel=[s['qvel'] for s in robot.states],ctrl=[s['ctrl'] for s in robot.states])
        np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
        artifacts={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['physics_trace.npz','states.npz','execution.mp4','final.png'] if (out/name).exists()}
        if not all(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==hashes[name] for name in source_names):
            status='failed';failure='Source changed during execution'
        result=dict(status=status,attempt_id=attempt,evaluation=evaluation,input_sha256=hashes,artifacts_sha256=artifacts,engine_version=mujoco.__version__,seed=args.seed,failure=failure,scene=args.scene,simulated_seconds=float(robot.data.time),physics_steps=robot.physics_steps,peak_unintended_arm_contact_n=robot.peak_unintended_force,engine='MuJoCo',physical_contact_execution=True,whole_paper_validated=False,observations=robot.timeline)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2),flush=True);robot.close()
    return status=='passed'


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
