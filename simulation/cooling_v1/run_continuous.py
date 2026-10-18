"""Develop a continuous cooler assembly/disassembly, preserving physical state."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import mujoco
from world import HERE
from continuous_world import build
from continuous_control import ContinuousRobot
from evaluate_continuous import evaluate
from initial_contacts import inspect as initial_contacts


def execute(robot,targets,limit=None):
    sequence=['foam_lower','foam_upper','emitter','pe_tube','shield','aperture']
    for name in sequence:
        target=targets[name]
        print('ASSEMBLE',name,flush=True)
        robot.transfer(name,target['assembled'],target['support'])
        # Every retained component remains checked after every later placement.
        for previous in sequence[:sequence.index(name)+1]:
            p=targets[previous]
            robot.check_supported(previous,p['assembled'],p['support'])
        if name==limit:return []
    assembled_times=[float(robot.data.time)]
    robot.checkpoint('assembled_layers_observed',bodies=sequence.copy())
    for name in reversed(sequence):
        print('DISASSEMBLE',name,flush=True)
        if name=='emitter':
            robot.transfer(name,targets[name]['regrasp'],'emitter_regrasp_stand')
        robot.transfer(name,targets[name]['park'],name+'_stand')
        # Removing one layer must not silently disturb retained lower layers.
        for previous in sequence[:sequence.index(name)]:
            p=targets[previous];robot.check_supported(previous,p['assembled'],p['support'])
    for name in sequence:
        robot.check_supported(name,targets[name]['park'],name+'_stand')
    return assembled_times


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--limit');parser.add_argument('--cycle');parser.add_argument('--seed',type=int,default=0);parser.add_argument('--out',default='runs/continuous_debug')
    args=parser.parse_args();out=HERE/args.out;out.mkdir(parents=True,exist_ok=True)
    attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/n for n in ['result.json','workcell.xml','physics_trace.npz','states.npz','execution.mp4','final.png'] if (out/n).exists()]
    if old:
        history=out/'history'/attempt;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    source_names=['continuous_world.py','continuous_control.py','run_continuous.py','evaluate_continuous.py','source_parts.py','contact_safety.py','support_observation.py','initial_contacts.py','CONTINUOUS_SCOPE.json','world.py','control.py','load_model.py','robot_source.json','geometry/catalog.json']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in source_names}
    result=dict(status='running',attempt_id=attempt,seed=args.seed,whole_paper_validated=False,
                input_sha256=pins,engine='MuJoCo',engine_version=mujoco.__version__)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    passed=False;failure=None;robot=None;assessment=None;targets=None
    try:
        targets=build(out/'workcell.xml')
        pins['workcell.xml']=hashlib.sha256((out/'workcell.xml').read_bytes()).hexdigest()
        result['initial_contacts']=initial_contacts(out/'workcell.xml',{name:name+'_stand' for name in targets})
        robot=ContinuousRobot(out/'workcell.xml',record=args.render,seed=args.seed,
                              video_path=out/'execution.mp4' if args.render else None)
        for name,target in targets.items():robot.check_supported(name,target['park'],name+'_stand')
        if args.cycle:robot.transfer(args.cycle,targets[args.cycle]['park'],args.cycle+'_stand')
        else:
            times=execute(robot,targets,args.limit)
            if not args.limit:assessment=evaluate(robot,targets,times)
        passed=assessment['passed'] if assessment else bool(args.cycle or args.limit)
        if not passed:failure='Independent evaluator rejected the continuous run'
    except BaseException as error:
        failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            try:
                robot.close()
                np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
                if args.render:
                    import imageio.v2 as imageio
                    imageio.imwrite(out/'final.png',robot.frames[-1])
                    np.savez_compressed(out/'states.npz',time=[s['t'] for s in robot.states],qpos=[s['qpos'] for s in robot.states],qvel=[s['qvel'] for s in robot.states],ctrl=[s['ctrl'] for s in robot.states])
            except Exception as error:
                passed=False;failure='Evidence write failed: '+str(error)
        if any(hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pins[n] for n in source_names):
            passed=False;failure='Source changed during execution'
        result.update(status=('development_pass' if args.cycle or args.limit else 'passed') if passed else 'failed',
            failure=failure,evaluation=assessment,targets=targets,
            observations=robot.timeline if robot else [],physics_steps=robot.physics_steps if robot else 0,
            simulated_seconds=float(robot.data.time) if robot else 0,
            physical_scope='one persistent rigid-layer scene; material preparation, film manufacture, sensors and campaign branches remain separate obligations',
            artifacts_sha256={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['physics_trace.npz','states.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print('RESULT',result['status'],result['simulated_seconds'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
