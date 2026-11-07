"""Compare compiled contact geometry at retained failed-attempt states.

This uses evaluator states only for offline geometry review. It is not a
controller observation, motor replay or new physical execution.
"""
import hashlib,json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
import mujoco,numpy as np

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
BASE=ROOT/'simulation/g1_cooling_demo';sys.path.insert(0,str(BASE))
from distal_contacts import attach,ROBOT,MANIFEST

start=time.monotonic();reference=BASE/'runs/ftir_cover_09'
xml=ET.parse(reference/'world.xml').getroot();xml.find('compiler').set('meshdir',str(ROBOT));attach(xml,HERE)
path=HERE/'world.xml';ET.indent(xml);ET.ElementTree(xml).write(path,encoding='unicode')
print('compile',flush=True);model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model)
old=mujoco.MjModel.from_xml_path(str(reference/'world.xml'));prior=mujoco.MjData(old)
print('compiled',model.ngeom,'geoms','seconds',time.monotonic()-start,flush=True)
assert model.nq==old.nq and model.nv==old.nv
assert all(model.joint(j).name==old.joint(j).name for j in range(old.njnt))
assert np.array_equal(model.body_mass,old.body_mass) and np.array_equal(model.body_inertia,old.body_inertia)
assert np.array_equal(model.jnt_range,old.jnt_range) and np.array_equal(model.actuator_ctrlrange,old.actuator_ctrlrange)
pairs=[{'right_index_2','right_thumb_4'},{'right_index_force_sensor_3','right_thumb_4'}]
def contacts(m,d):
 rows=[]
 for c in d.contact:
  names={m.body(m.geom_bodyid[int(g)]).name for g in c.geom}
  if names in pairs and c.dist<0:rows.append(dict(parts=sorted(names),penetration_m=float(-c.dist)))
 return dict(total_contacts=d.ncon,selected_contacts=rows)
rows=[]
for run,times in [('ftir_cover_03',[14.5,15.,16.,17.4]),('ftir_cover_09',[16.5,17.5,18.,18.25,18.5,19.5,20.]),('ftir_cover_10',[15.5,16.5,17.,17.5])]:
 trace=np.load(BASE/'runs'/run/'trace.npz')
 for t in times:
  i=np.argmin(abs(trace['time']-t))
  for m,d in [(old,prior),(model,data)]:
   d.qpos[:]=trace['qpos'][i];d.qvel[:]=trace['qvel'][i];mujoco.mj_forward(m,d)
  row=dict(run=run,time_s=float(trace['time'][i]),old=contacts(old,prior),refined=contacts(model,data));rows.append(row)
  print(run,t,'old',len(row['old']['selected_contacts']),'refined',len(row['refined']['selected_contacts']),flush=True)
report=dict(scope=__doc__,manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
 rows=rows,body_inertias_unchanged=True,source_joint_and_actuator_limits_unchanged=True,
 elapsed_seconds=time.monotonic()-start,qualified=False)
(HERE/'compiled_contact_review.json').write_text(json.dumps(report,indent=2)+'\n')
