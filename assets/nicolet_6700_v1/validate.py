"""Independent exported geometry checks for the bare Nicolet reconstruction."""
import json,hashlib
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 scene=trimesh.load(HERE/'geometry/nicolet_6700.glb',force='scene');meshes={}
 for name in scene.graph.nodes_geometry:
  transform,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(transform);m.vertices=np.asarray(m.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]]);meshes[name]=m
 parts=json.loads((HERE/'parts.json').read_text());cfg=json.loads((HERE/'interfaces.json').read_text());receipt=json.loads((HERE/'build_receipt.json').read_text());checks=[]
 def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
 check('all_parts_exported',set(meshes)=={p['id'] for p in parts},parts=len(parts))
 case=trimesh.util.concatenate([meshes[p['id']] for p in parts if p['role'] in ['housing','support','cover_rib']])
 check('manufacturer_case_envelope',np.max(abs(case.extents-cfg['source_envelope_m']))<2e-6,measured_m=case.extents.tolist(),excludes='projecting handles, legends and service fittings')
 check('floor_datum',abs(case.bounds[0,2])<1e-7)
 bay=cfg['sample_bay'];cx,cy=bay['center_xy_m'];points=np.array([[cx+x,cy+y,z] for x in [-.103,0,.103] for y in [-.128,0,.128] for z in [.060,.150,.248]])
 blocked=[]
 for p in parts:
  if p['id'] in cfg['cover_parts'] or p['role']=='identification_legend':continue
  m=meshes[p['id']]
  if np.any(m.bounds[1]<points.min(axis=0)) or np.any(m.bounds[0]>points.max(axis=0)):continue
  if m.is_watertight and m.contains(points).any():blocked.append(p['id'])
 check('source_sample_bay_is_open',not blocked,blocked=blocked,usable_dimensions_m=[.210,.260,.200])
 floor=meshes['sample_compartment_floor'];check('defined_accessory_support_plane',abs(floor.bounds[1,2]-.050)<1e-6 and np.max(abs(floor.extents[:2]-[.210,.260]))<1e-6)
 check('separate_hinged_cover_and_fixed_front',len(cfg['cover_parts'])==18 and all(n in meshes for n in cfg['cover_parts']) and meshes['sample_bay_lid'].bounds[0,2]>.24999 and 'sample_bay_front' not in cfg['cover_parts'])
 check('front_cover_seam_without_overlap',abs(meshes['sample_cover_front_lip'].bounds[0,2]-meshes['sample_bay_front'].bounds[1,2])<1e-6 and all(meshes[n].bounds[0,2]>=meshes['sample_bay_front'].bounds[1,2]-1e-7 for n in cfg['cover_parts'] if n.startswith('lid_handle_')))
 check('front_lip_clear_of_bay_liners',all(meshes[n].bounds[0,1]-meshes['sample_cover_front_lip'].bounds[1,1]>.00099 for n in meshes if n.startswith('sample_compartment_wall_')))
 handle=meshes['lid_handle_bar'];gap=np.array([[cx+x,-.300,z] for x in [-.02,0,.02] for z in [.243,.247,.251]])
 check('handle_grip_gap',not any(meshes[n].contains(gap).any() for n in cfg['cover_parts'] if meshes[n].is_watertight))
 opening=np.array([[cx+x,-.208+y,.251] for x in [-.070,0,.070] for y in [-.045,0,.045]])
 check('sample_access_is_an_open_cover_aperture',not meshes['sample_bay_lid'].contains(opening).any())
 slider=next(i for i in cfg['interfaces'] if i['id']=='sample_access_slider');pane=meshes['sample_access_sliding_window'];at_pane=opening.copy();at_pane[:,2]=.248
 moved=pane.copy();moved.apply_translation(np.array(slider['axis'])*slider['travel_m'])
 check('separate_sliding_window_opens_access',pane.contains(at_pane).all() and not moved.contains(at_pane).any() and set(slider['parts'])<=set(cfg['cover_parts']))
 for name in ['detector_motors','auxiliary']:
  port=next(i for i in cfg['interfaces'] if i['id']==name);points=np.array(port['contact_centers_m']);points[:,1]+=.001
  check('fifteen_open_female_contacts_'+name,port['contacts']==15 and len(points)==15 and not meshes[name+'_insulator'].contains(points).any() and not meshes[name+'_keyed_shell'].contains(points).any())
 check('detector_connection_is_inside_bay',not any(n.startswith('rear_external_detector') for n in meshes) and -.050<meshes['detector_motors_flange'].bounds[0,1]<-.030)
 check('purge_outlet_is_hollow',not meshes['sample_bay_purge_outlet'].contains([[cx+.045,-.038,.110]])[0])
 keys=[i for i in cfg['interfaces'] if i['kind']=='push_button'];check('four_separate_scan_keys',len(keys)==4 and all('scan_key_'+str(i) in meshes for i in range(4)))
 exposed=[]
 for i in range(4):
  key=meshes['scan_key_'+str(i)];center=key.centroid
  exposed.append(not meshes['right_source_housing'].contains([center])[0])
 check('keys_not_buried_in_housing',all(exposed),exposed=exposed)
 for side,name in [(-1,'left_detector_housing'),(1,'right_source_housing')]:
  points=np.array([[side*(.346-.002),.035+i*.012,.095] for i in range(20)])
  check('recessed_side_vent_'+str(side),not meshes[name].contains(points).any())
 sockets=[p['id'] for p in parts if p['role']=='accessory_socket'];check('open_mount_sockets',len(sockets)==4 and all(not meshes[n].contains([meshes[n].centroid])[0] for n in sockets))
 check('accessory_identity_separated',not any('IntegratIR' in n or 'Smart_Orbit' in n for n in meshes) and len(cfg['exclusions'])==3)
 check('inference_record_per_part',all(p.get('geometry_basis') for p in parts) and all(i.get('qualified') is False for i in cfg['interfaces'] if i['kind'] in ['hinge','slide','female_detector_connector','female_auxiliary_connector','purge_outlet']))
 check('source_builder_pins',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['sources_sha256']==sha(HERE/'sources.json'))
 check('geometry_hashes',all(sha(HERE/n)==h for n,h in receipt['artifacts_sha256'].items()))
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,glb_sha256=sha(HERE/'geometry/nicolet_6700.glb'),validator_sha256=sha(Path(__file__)),manufacturer_CAD=False,contact_qualified=False,scope='Static bare instrument envelope, open bay, exposed controls and separate inferred cover; no robot, optical or electronic qualification.')
 (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']

if __name__=='__main__':raise SystemExit(0 if main() else 1)
