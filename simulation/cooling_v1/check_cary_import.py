"""Static import and complete lid-stroke diagnostics; no execution credit."""
import json,tempfile
from pathlib import Path
import numpy as np,mujoco
from cary_assets import load,DEVICES
from cary_world import build
from world import HERE,HOME
from trace_store import sha

def main():
 checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'workcell.xml';cfg=build(path);m=load(path);d=mujoco.MjData(m);d.qpos[:7]=HOME;d.qpos[7:9]=.04
  joint=m.joint('cary_lid_travel');check('passive_lid',joint.id not in m.actuator_trnid[:,0] and m.nu==8)
  check('no_attachment_weld',not any(v==mujoco.mjtEq.mjEQ_WELD for v in m.eq_type))
  check('positive_inferred_lid_mass',m.body('cary_lid').mass[0]>0,mass_kg=float(m.body('cary_lid').mass[0]))
  worst=0.;collisions=[]
  for travel in np.linspace(0,.305,306):
   d.joint('cary_lid_travel').qpos[0]=travel;mujoco.mj_forward(m,d)
   for c in d.contact:
    bodies=[m.body(int(m.geom_bodyid[g])).name for g in c.geom]
    if set(bodies)!={'cary','cary_lid'}:continue
    worst=min(worst,float(c.dist))
    if c.dist<-.00001 and len(collisions)<10:collisions.append(dict(travel_m=float(travel),geoms=[m.geom(g).name for g in c.geom],overlap_m=float(c.dist)))
  check('entire_lid_stroke_clear',not collisions,poses=306,maximum_overlap_m=-worst,collisions=collisions)
  explicit={tuple(sorted([int(a),int(b)])) for a,b in zip(m.pair_geom1,m.pair_geom2)}
  physical_fixed=[g for g in range(m.ngeom) if m.geom_bodyid[g]==m.body('cary').id and m.geom_contype[g]]
  physical_lid=[g for g in range(m.ngeom) if m.geom_bodyid[g]==m.body('cary_lid').id and m.geom_contype[g]]
  check('adjacent_body_contacts_explicit',all(tuple(sorted([a,b])) in explicit for a in physical_fixed for b in physical_lid),fixed_geoms=len(physical_fixed),lid_geoms=len(physical_lid))
  d.joint('cary_lid_travel').qpos[0]=0;mujoco.mj_forward(m,d);bad=[]
  arm={'link1','link2','link3','link4','link5','link6','link7','hand','left_finger','right_finger'}
  for c in d.contact:
   bodies=[m.body(int(m.geom_bodyid[g])).name for g in c.geom]
   if set(bodies)&arm and set(bodies)&{'cary','cary_lid'} and c.dist<-.00001:bad.append(dict(bodies=bodies,overlap_m=float(c.dist)))
  check('initial_robot_clear_of_instrument',not bad,collisions=bad)
  check('source_geometry_checks_pass',json.loads((DEVICES['cary_5000']/'geometry_checks.json').read_text())['passed'])
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,diagnostic_only=True,robot_execution_validated=False,input_sha256={n:sha(HERE/n) for n in ['check_cary_import.py','cary_world.py','cary_assets.py','geometry/cary_5000/catalog.json']},asset_interfaces_sha256=sha(DEVICES['cary_5000']/'interfaces.json'))
 (HERE/'cary_import_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
