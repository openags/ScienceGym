"""Physical counterexamples for the continuous layer controller and gate."""
import hashlib
import json
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
from continuous_world import build
from continuous_control import ContinuousRobot
from initial_contacts import inspect
from control import ExecutionFailure
from load_model import load
from world import HERE,HOME,vec


def main():
    sources=['test_continuous_faults.py','continuous_world.py','continuous_control.py','initial_contacts.py','contact_safety.py','support_observation.py','source_parts.py','control.py','world.py','load_model.py']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources}
    outcomes=[]
    for case in ['payload_intersects_frame','missing_lower_foam_support','frictionless_foam_grasp','loaded_hand_obstacle']:
        with tempfile.TemporaryDirectory(prefix='sciencegym-layer-fault-') as directory:
            path=Path(directory)/'workcell.xml';targets=build(path)
            tree=ET.parse(path);root=tree.getroot();world=root.find('worldbody')
            if case=='payload_intersects_frame':world.find("body[@name='shield']").set('pos','.48 .12 .78')
            if case=='missing_lower_foam_support':
                body=world.find("body[@name='foam_lower_stand']")
                for geom in list(body.findall('geom')):body.remove(geom)
            if case=='frictionless_foam_grasp':
                for geom in root.findall('.//geom'):
                    geom.set('friction','0 0 0');geom.set('condim','1')
            if case=='loaded_hand_obstacle':
                model=load(path);data=mujoco.MjData(model);data.qpos[:7]=HOME;data.qpos[7:9]=.04;mujoco.mj_forward(model,data)
                # Intentionally intersect the hand to exercise the contact
                # audit during initial settling, not a planner name check.
                ET.SubElement(world,'geom',name='fault_obstacle',type='sphere',size='.04',pos=vec(data.body('hand').xpos),contype='1',conaffinity='1')
            tree.write(path)
            robot=None;reason=None;rejected=False
            try:
                if case=='payload_intersects_frame':inspect(path,{n:n+'_stand' for n in targets})
                else:
                    robot=ContinuousRobot(path)
                    if case=='frictionless_foam_grasp':robot.pick('foam_lower')
                    else:robot.check_supported('foam_lower',targets['foam_lower']['park'],'foam_lower_stand')
            except ExecutionFailure as error:rejected=True;reason=str(error)
            finally:
                if robot:robot.close()
            required={'payload_intersects_frame':'Invalid initial payload intersections','missing_lower_foam_support':'support invalid','frictionless_foam_grasp':'lift failed','loaded_hand_obstacle':'unintended arm contact'}[case]
            passed=rejected and required in reason
            outcomes.append(dict(case=case,passed=passed,rejected=rejected,reason=reason))
            print(case,passed,reason[:180] if reason else None,flush=True)
    result=dict(passed=all(x['passed'] for x in outcomes) and all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==v for n,v in pins.items()),
                outcomes=outcomes,input_sha256=pins,engine_version=mujoco.__version__,whole_paper_validated=False)
    (HERE/'continuous_fault_tests.json').write_text(json.dumps(result,indent=2)+'\n')
    return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
