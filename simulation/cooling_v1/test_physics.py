"""Contact regressions and deliberate physical failures, not animation checks."""
import json
import hashlib
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from control import Robot,ExecutionFailure
from evaluate import assess
from run_contact import execute
from world import HERE,TOP,assembly_scene,probe_scene,lid_scene,door_scene

BUILDERS=dict(assembly=assembly_scene,probe=probe_scene,lid=lid_scene,door=door_scene)


def main():
    source_names=['world.py','control.py','load_model.py','evaluate.py','run_contact.py','test_physics.py','PHYSICS_SCOPE.json','robot_source.json','geometry/catalog.json']
    pins={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in source_names}
    outcomes=[]
    with tempfile.TemporaryDirectory(prefix='sciencegym-contact-tests-') as directory:
        for scene,builder in BUILDERS.items():
            path=Path(directory)/(scene+'.xml');builder(path)
            for seed in [0,17,41]:
                robot=Robot(path,seed=seed)
                try:
                    execute(robot,scene);evaluation=assess(scene,robot)
                    outcomes.append(dict(case=scene+'_seed_'+str(seed),passed=evaluation['passed'],evaluation=evaluation))
                except ExecutionFailure as error:
                    outcomes.append(dict(case=scene+'_seed_'+str(seed),passed=False,reason=str(error)))
                finally:robot.close()
                print(outcomes[-1]['case'],outcomes[-1]['passed'],flush=True)

        for fault in ['unexecuted_goal','gripper_open','missing_support','blocked_button','wrong_bore','door_obstruction']:
            scene='probe' if fault=='wrong_bore' else 'door' if fault=='door_obstruction' else 'assembly'
            path=Path(directory)/(fault+'.xml');BUILDERS[scene](path)
            if fault in ['blocked_button','door_obstruction']:
                tree=ET.parse(path);world=tree.getroot().find('worldbody')
                position='.71 -.05 .777' if fault=='blocked_button' else '.55 .09 .96'
                size='.023 .023 .007' if fault=='blocked_button' else '.03 .025 .025'
                ET.SubElement(world,'geom',name='injected_obstruction',type='box',pos=position,size=size)
                tree.write(path)
            robot=Robot(path);detected=False;reason=None
            try:
                if fault=='unexecuted_goal':
                    detected=not assess(scene,robot)['passed'];reason='goal predicates reject untouched initial state'
                elif fault=='gripper_open':
                    original=robot.finger;robot.finger=lambda opening:original(.08)
                    robot.pick('foam_lower')
                elif fault=='missing_support':
                    robot.transfer('foam_lower',[.53,.30,TOP+.10],'assembly_base')
                elif fault=='blocked_button':robot.press()
                elif fault=='wrong_bore':robot.transfer('probe',[.539,.12,TOP+.064],'copper_block',.002)
                else:robot.access_door(1.05)
            except ExecutionFailure as error:
                detected=True;reason=str(error)
            finally:robot.close()
            outcomes.append(dict(case=fault,passed=detected,meaning='expected physical failure detected',reason=reason))
            print(fault,detected,flush=True)
    report=dict(scope='four isolated rigid-body contact fixtures; not whole-paper task acceptance',
                whole_paper_validated=False,passed=all(r['passed'] for r in outcomes),
                count=len(outcomes),outcomes=outcomes,input_sha256=pins)
    assert all(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest for name,digest in pins.items()),'Source changed during execution'
    (HERE/'physics_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    return report['passed']


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
