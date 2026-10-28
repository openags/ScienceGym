"""Execute the seven-layer sequence without resetting or replacing the world."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
from datetime import datetime,timezone
import numpy as np
import mujoco
from world import HERE
from integrated_world import build
from integrated_control import IntegratedRobot
from initial_contacts import inspect
from evaluate_continuous import evaluate as evaluate_layers
from evaluate_cover import evaluate as evaluate_cover

SEQUENCE=['foam_lower','foam_upper','emitter','pe_tube','cover','shield','aperture']


def execute(robot,targets,limit):
    def recheck(names):
        for name in names:
            p=targets[name]
            if name=='cover':robot.check_cover(np.array(p['assembled']),p['support'])
            else:robot.check_supported(name,p['assembled'],p['support'])
    for i,name in enumerate(SEQUENCE):
        print('ASSEMBLE',name,float(robot.data.time),flush=True);p=targets[name]
        if name=='cover':robot.grip_cover();robot.put_cover(np.array(p['assembled']))
        else:robot.transfer(name,p['assembled'],p['support'])
        recheck(SEQUENCE[:i+1])
        if limit==name:return None
    assembled=float(robot.data.time)
    for i in range(len(SEQUENCE)-1,-1,-1):
        name=SEQUENCE[i];p=targets[name];print('DISASSEMBLE',name,float(robot.data.time),flush=True)
        if name=='cover':
            robot.grip_cover();robot.put_cover(np.array(p['park']));robot.check_cover(np.array(p['park']),'cover_stand')
        else:
            if name=='emitter':robot.transfer(name,p['regrasp'],'emitter_regrasp_stand')
            robot.transfer(name,p['park'],name+'_stand')
        recheck(SEQUENCE[:i])
    layers=evaluate_layers(robot,{n:p for n,p in targets.items() if n!='cover'},[assembled])
    period=float(np.median(np.diff([row[0] for row in robot.trace])))
    for row in layers['continuity']:
        maximum=row.pop('max_translation_per_20ms_m')
        row.update(max_translation_per_sample_m=maximum,sample_interval_s=period,
                   max_sampled_speed_m_s=maximum/period,passed=maximum/period<1.0)
    layers['passed'] &= all(row['passed'] for row in layers['continuity'])
    cover=evaluate_cover(robot,[dict(time=assembled,target=targets['cover']['assembled'],support='pe_tube'),
                                dict(time=float(robot.data.time),target=targets['cover']['park'],support='cover_stand')])
    return dict(passed=layers['passed'] and cover['passed'],layers=layers,cover=cover,whole_paper_validated=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');parser.add_argument('--limit');parser.add_argument('--seed',type=int,default=0);parser.add_argument('--out',default='runs/integrated_debug');args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True);attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[out/n for n in ['result.json','workcell.xml','physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()]
    if old:
        history=out/'history'/attempt;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    sources=['run_integrated.py','integrated_world.py','integrated_control.py','INTEGRATED_SCOPE.json','continuous_world.py','continuous_control.py','cover_control.py','cover_world.py','membrane.py','precision_ik.py','evaluate_cover.py','evaluate_continuous.py','initial_contacts.py','support_observation.py','contact_safety.py','source_parts.py','world.py','control.py','load_model.py','robot_source.json','geometry/catalog.json']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    pins={n:sha(HERE/n) for n in sources};result=dict(status='running',input_sha256=pins,attempt_id=attempt,whole_paper_validated=False,engine_version=mujoco.__version__,seed=args.seed)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    robot=None;passed=False;failure=None;assessment=None
    try:
        targets=build(out/'workcell.xml');result['targets']=targets;pins['workcell.xml']=sha(out/'workcell.xml')
        result['initial_contacts']=inspect(out/'workcell.xml',{n:n+'_stand' for n in targets})
        robot=IntegratedRobot(out/'workcell.xml',record=args.render,seed=args.seed,video_path=out/'execution.mp4' if args.render else None)
        for name,p in targets.items():
            if name=='cover':robot.check_cover(np.array(p['park']),'cover_stand')
            else:robot.check_supported(name,p['park'],name+'_stand')
        assessment=execute(robot,targets,args.limit);passed=assessment['passed'] if assessment else bool(args.limit)
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            try:
                robot.close()
                np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace],tree_asleep=robot.sleep_trace)
                if args.render:
                    import imageio.v2 as imageio
                    imageio.imwrite(out/'final.png',robot.frames[-1])
            except Exception as error:passed=False;failure='Evidence write failed: '+str(error)
        if any(sha(HERE/n)!=pins[n] for n in sources):passed=False;failure='Source changed during execution'
        result.update(status=('development_pass' if args.limit else 'passed') if passed else 'failed',failure=failure,evaluation=assessment,
                      observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
                      scope='Seven-layer assembly and return with pre-bonded membrane; no manufacture, sensors, reflector, paired apparatus or full-paper credit',
                      artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz','execution.mp4','final.png'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],result['simulated_seconds'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
