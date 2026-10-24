"""Continuous side grip, deformable load support and return, with pinned evidence."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
import hashlib
from datetime import datetime,timezone
import numpy as np
import mujoco
from world import HERE
from cover_world import build,PARK,TARGET
from cover_control import CoverRobot
from evaluate_cover import evaluate,measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--grip-only',action='store_true');parser.add_argument('--seed',type=int,default=0);parser.add_argument('--out',default='runs/cover_debug')
    args=parser.parse_args();out=HERE/args.out;out.mkdir(parents=True,exist_ok=True)
    attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/n for n in ['result.json','workcell.xml','physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()]
    if old:
        history=out/'history'/attempt;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    sources=['run_cover.py','cover_world.py','cover_control.py','evaluate_cover.py','precision_ik.py','membrane.py','source_parts.py','contact_safety.py','world.py','control.py','load_model.py','robot_source.json','geometry/catalog.json']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources}
    result=dict(status='running',attempt_id=attempt,input_sha256=pins,engine_version=mujoco.__version__,whole_paper_validated=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    passed=False;failure=None;robot=None;assessment=None;checkpoints=[]
    try:
        result['film_properties']=build(out/'workcell.xml')
        pins['workcell.xml']=hashlib.sha256((out/'workcell.xml').read_bytes()).hexdigest()
        robot=CoverRobot(out/'workcell.xml',record=args.render,seed=args.seed)
        robot.grip()
        if not args.grip_only:
            for target,support in [(TARGET,'tube_support'),(PARK,'cover_stand')]:
                robot.put(target)
                observation=measure(robot.model,robot.data,target,support)
                robot.checkpoint('released_support_measured',support=support,observation=observation)
                if not observation['passed']:raise RuntimeError('Cover support invalid: '+str(observation))
                checkpoints.append(dict(time=float(robot.data.time),target=target.tolist(),support=support))
                if support=='tube_support':robot.grip()
            assessment=evaluate(robot,checkpoints)
            passed=assessment['passed']
        else:passed=True
    except BaseException as error:
        failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            try:
                np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
                if args.render:
                    import imageio.v2 as imageio
                    imageio.mimwrite(out/'execution.mp4',robot.frames,fps=10,codec='libx264',quality=7)
                    imageio.imwrite(out/'final.png',robot.frames[-1])
            except Exception as error:passed=False;failure='Evidence write failed: '+str(error)
            finally:robot.close()
        if any(hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pins[n] for n in sources):passed=False;failure='Source changed during execution'
        result.update(status=('development_pass' if args.grip_only else 'passed') if passed else 'failed',failure=failure,
            observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
            evaluation=assessment,checkpoints=checkpoints,seed=args.seed,
            scope='Side gripping of a pre-bonded cover with two constrained cloth sheets; no film attachment, damage or whole-paper qualification',
            artifacts_sha256={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('RESULT',result['status'],result['simulated_seconds'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
