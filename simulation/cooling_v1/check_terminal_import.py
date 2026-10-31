"""Compare the qualified jig and its explicitly imported terminal contact law."""
import sys,json
from pathlib import Path
from test_terminal_mechanism import build
from terminal_world import build as robot_build
from device_assets import load
from trace_store import sha
from world import HERE
import mujoco,numpy as np
directory=HERE/'runs/terminal_debug/import_check';directory.mkdir(parents=True,exist_ok=True)
p=directory/'current_jig.xml';build(p);new=mujoco.MjModel.from_xml_path(str(p));oldpath=HERE/'runs/terminal_mechanism_tests/nominal/workcell.xml';old=mujoco.MjModel.from_xml_path(str(oldpath));changed=[]
for name in dir(old):
 try:
  a,b=getattr(old,name),getattr(new,name)
  if isinstance(a,np.ndarray) and (a.shape!=b.shape or not np.array_equal(a,b)):changed.append(name)
 except (AttributeError,ValueError,TypeError):pass
q=directory/'current_robot.xml';robot_build(q);robot=load(q);differences=[];count=0
for g in range(new.ngeom):
 name=new.geom(g).name
 if not name.startswith('terminal_03_'):continue
 other=robot.geom(name).id;count+=1
 for field in ['geom_solref','geom_solimp','geom_friction','geom_condim','geom_type']:
  if not np.array_equal(getattr(new,field)[g],getattr(robot,field)[other]):differences.append([name,field])
report=dict(verifier_sha256=sha(Path(__file__)),passed=not changed and not differences,old_jig_compiled_fields_changed=changed,terminal_contact_differences=differences,terminal_geoms=count,
 previous_jig_xml_sha256=sha(oldpath),current_jig_xml_sha256=sha(p),current_robot_xml_sha256=sha(q),
 source_sha256={n:sha(HERE/n) for n in ['terminal_mechanism.py','terminal_world.py','test_terminal_mechanism.py']},
 scope='Compiled model comparison: explicit mechanism contact defaults preserve the previously verified jig and its contact parameters in the robot workcell. No robot execution credit.')
(HERE/'terminal_import_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
