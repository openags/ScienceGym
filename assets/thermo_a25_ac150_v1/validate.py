"""Inspect exported A25 dimensions, open work area, lid and source separation."""
import json,hashlib
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 scene=trimesh.load(HERE/'geometry/thermo_a25_ac150.glb',force='scene');meshes={}
 for name in scene.graph.nodes_geometry:
  transform,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(transform);m.vertices=np.asarray(m.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]]);meshes[name]=m
 parts=json.loads((HERE/'parts.json').read_text());cfg=json.loads((HERE/'interfaces.json').read_text());sources=json.loads((HERE/'sources.json').read_text());checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 check('all_parts_exported',set(meshes)=={p['id'] for p in parts},count=len(meshes))
 shell=trimesh.util.concatenate([meshes[p['id']] for p in parts if p['role'] in ['housing','support','controller_housing']])
 check('manufacturer_case_envelope',np.max(abs(shell.extents-np.array([.273,.483,.749])))<2e-6,measured_m=shell.extents.tolist(),excludes='projecting drain, rocker and rear fittings')
 check('floor_datum',abs(shell.bounds[0,2])<1e-7)
 opening=np.array([[x,y,z] for x in [-.084,0,.084] for y in [-.202,-.112,-.022] for z in [.317,.400,.513]])
 excluded=set(cfg['lid_parts']);blocked=[]
 for p in parts:
  if p['id'] in excluded or p['role']=='identification_legend':continue
  m=meshes[p['id']]
  if np.any(m.bounds[1]<opening.min(axis=0)) or np.any(m.bounds[0]>opening.max(axis=0)):continue
  if m.is_watertight and m.contains(opening).any():blocked.append(p['id'])
 check('full_working_region_is_open_with_lid_removed',not blocked,blocked=blocked,source_dimensions_m=[.173,.184,.200])
 walls=trimesh.util.concatenate([meshes[p['id']] for p in parts if p['role'].startswith('reservoir_')])
 check('real_reservoir_floor_and_walls',walls.contains([[0,-.112,.314],[-.0875,-.112,.4],[.0875,-.112,.4],[0,-.205,.4],[0,.162,.4]]).all())
 lid=meshes['bath_lid'];head=meshes['controller_case'];bridge=meshes['controller_bridge']
 check('lid_closes_working_opening',lid.bounds[0,0]<-.0865 and lid.bounds[1,0]>.0865 and lid.bounds[0,1]<-.204 and lid.bounds[1,1]>=-.020001)
 check('lid_has_clear_vertical_removal',lid.bounds[1,1]<head.bounds[0,1]-.0001 and lid.bounds[1,1]<=bridge.bounds[0,1]+1e-6,
  lid_rear_y_m=float(lid.bounds[1,1]),controller_front_y_m=float(head.bounds[0,1]),bridge_front_y_m=float(bridge.bounds[0,1]))
 check('folded_lid_has_open_underside',not lid.contains([[0,-.115,.516]])[0] and lid.contains([[0,-.115,.5185]])[0],selected_sheet_m=.001)
 handle=meshes['lid_handle'];points=np.array([[x,-.108,z] for x in [-.015,0,.015] for z in [.527,.537,.545]])
 check('lid_handle_has_grip_clearance',not handle.contains(points).any())
 handle_recess=np.array([[x,-.235,z] for x in [-.025,0,.025] for z in [.347,.355,.363]])
 check('front_carry_handle_is_recessed',not meshes['front_shell'].contains(handle_recess).any())
 drain=meshes['drain_body'];r=np.array([[0,y,.302] for y in np.linspace(-.258,-.241,10)])
 check('real_drain_bore',not drain.contains(r).any() and drain.contains([[.007,-.2475,.302]])[0])
 front=meshes['front_shell'];grillepoints=np.array([[x,-.2415,z] for x in [-.05,0,.05] for z in [.06,.16,.25]])
 check('front_vent_opening',not front.contains(grillepoints).any() and len([p for p in parts if p['role']=='vent_grille'])>100)
 buttons=[i for i in cfg['interfaces'] if i['kind']=='push_button'];check('seven_separate_AC150_keys',len(buttons)==7 and all('key_'+i['id'].removeprefix('AC150_') in meshes for i in buttons))
 check('AC200_only_ports_omitted',not any('usb' in n.lower() or 'multifunction' in n.lower() for n in meshes))
 check('source_controller_identity_not_fabricated',cfg['historical_controller_known'] is False and 'selected' in sources['historical_identity']['controller'])
 check('source_dimension_conflicts_preserved',len(sources['source_conflicts'])>=3)
 check('manual_fill_level_reference',cfg['fill_below_rim_m']==[.022,.057] and cfg['work_area']['depth_m']==.200,
   resulting_water_depth_m=[.200-.057,.200-.022])
 receipt=json.loads((HERE/'build_receipt.json').read_text())
 check('source_and_builder_pins',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['sources_sha256']==sha(HERE/'sources.json'))
 check('geometry_hashes',all(sha(HERE/n)==h for n,h in receipt['artifacts_sha256'].items()))
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,validator_sha256=sha(Path(__file__)),glb_sha256=sha(HERE/'geometry/thermo_a25_ac150.glb'),vendor_cad=False,contact_qualified=False,
 scope='Static original manufacturer-informed A25/selected-AC150 geometry. No liquid, thermal/electrical function, robot manipulation or historical-controller qualification.')
 (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
