"""Physically dispatch paper-step bindings in a single persistent workcell.

The six step receipts are scoped to the preconstructed workcell. They cannot
qualify manufacture, film bonding or the complete BUILD_PAIR branch.
"""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import mujoco
from world import HERE
from selected_assembly_world import build
from selected_assembly_control import SelectedAssemblyRobot
from step_runtime import SceneBinding,BINDINGS,execute as execute_step,TASK
from run_integrated import SEQUENCE
from evaluate_continuous import evaluate as evaluate_layers
from evaluate_cover import evaluate as evaluate_cover
from initial_contacts import inspect


def execute(robot,targets,receipts,instance):
    occurrences=json.loads((TASK/'reference_plan.json').read_text())['occurrences']
    context=SceneBinding(robot,targets,instance)
    bindings={p['body']:step for step,p in BINDINGS.items()}
    def recheck(names):
        for name in names:
            p=targets[name]
            if name=='cover':robot.check_cover(np.array(p['assembled']),p['support'])
            else:robot.check_supported(name,p['assembled'],p['support'])
    for i,name in enumerate(SEQUENCE):
        print('ASSEMBLE',name,flush=True)
        if name in bindings:
            step=bindings[name]
            occurrence=next(o for o in occurrences if step in o['required_step_ids'] and o['payload_ids']==['white'] and o['station_id']=='WS_ASSEMBLY')
            receipts.append(execute_step(context,occurrence,step))
        else:robot.transfer(name,targets[name]['assembled'],targets[name]['support'])
        recheck(SEQUENCE[:i+1])
    assembled=float(robot.data.time)
    for i in range(len(SEQUENCE)-1,-1,-1):
        name=SEQUENCE[i];p=targets[name];print('DISASSEMBLE',name,flush=True)
        if name=='cover':robot.grip_cover();robot.put_cover(np.array(p['park']))
        else:
            if name=='emitter':robot.transfer(name,p['regrasp'],'emitter_regrasp_stand')
            robot.transfer(name,p['park'],name+'_stand')
        recheck(SEQUENCE[:i])
    layers=evaluate_layers(robot,{n:p for n,p in targets.items() if n!='cover'},[assembled])
    period=float(np.median(np.diff([s[0] for s in robot.trace])))
    for row in layers['continuity']:
        maximum=row.pop('max_translation_per_20ms_m');row.update(max_translation_per_sample_m=maximum,sample_interval_s=period,max_sampled_speed_m_s=maximum/period,passed=maximum/period<1)
    layers['passed'] &= all(r['passed'] for r in layers['continuity'])
    cover=evaluate_cover(robot,[dict(time=assembled,target=targets['cover']['assembled'],support='pe_tube'),dict(time=float(robot.data.time),target=targets['cover']['park'],support='cover_stand')])
    return dict(passed=layers['passed'] and cover['passed'] and len(receipts)==6,layers=layers,cover=cover,whole_paper_validated=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='runs/selected_assembly_debug');parser.add_argument('--seed',type=int,default=0);args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    old=[p for p in out.iterdir() if p.name!='history']
    if old:
        history=out/'history'/stamp;history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    names=['run_selected_assembly.py','selected_assembly_world.py','selected_assembly_control.py','step_runtime.py','run_integrated.py','integrated_world.py','integrated_control.py','continuous_world.py','continuous_control.py','cover_control.py','cover_world.py','membrane.py','precision_ik.py','evaluate_cover.py','evaluate_continuous.py','initial_contacts.py','support_observation.py','contact_safety.py','source_parts.py','world.py','control.py','load_model.py','robot_source.json','geometry/catalog.json']
    names+=['../../tasks/directional_cooling_operations_v3/'+n for n in ['operations.json','reference_plan.json','selected_reconstruction.json']]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={n:sha(HERE/n) for n in names}
    # Keep the archive inside this run even for task paths containing '..'.
    archive={n:'source_snapshot/'+n.replace('../','parent/') for n in names}
    for name,relative in archive.items():
        p=out/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/name,p)
    robot=None;passed=False;failure=None;targets=None;configuration=None;assessment=None;receipts=[]
    try:
        targets,configuration=build(out/'workcell.xml');pins['workcell.xml']=sha(out/'workcell.xml')
        initial=inspect(out/'workcell.xml',{n:n+'_stand' for n in targets})
        robot=SelectedAssemblyRobot(out/'workcell.xml',seed=args.seed)
        assessment=execute(robot,targets,receipts,'SELECTED_ASSEMBLY_'+stamp);passed=assessment['passed']
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Source changed during execution'
        (out/'step_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
        result=dict(status='passed' if passed else 'failed',failure=failure,configuration=configuration,targets=targets,evaluation=assessment,
            observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,seed=args.seed,
            input_sha256=pins,source_archive=archive,engine_version=mujoco.__version__,whole_paper_validated=False,
            executed_bound_steps=len(receipts),qualified_campaign_occurrences=0,
            scope='Seven layers assembled and returned using physical contacts. Six paper-step receipts, with preconstructed frame and prebonded films. Manufacturing, paired apparatus, sensors and reflector remain separate obligations.',
            artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz','step_receipts.json'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed
if __name__=='__main__':raise SystemExit(0 if main() else 1)
