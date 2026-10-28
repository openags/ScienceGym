"""Independent geometry checks for the legacy internal DRA reconstruction."""
import json,hashlib
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 scene=trimesh.load(HERE/'geometry/cary_internal_dra_2500.glb',force='scene');meshes={}
 for name in scene.graph.nodes_geometry:
  transform,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(transform);m.vertices=np.asarray(m.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
  # Rejoin exact GLB normal seams without merging distinct tiny CSG edges.
  m.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=9);meshes[name]=m
 cfg=json.loads((HERE/'interfaces.json').read_text());parts=json.loads((HERE/'parts.json').read_text());receipt=json.loads((HERE/'build_receipt.json').read_text());checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 check('all_parts_exported',set(meshes)=={p['id'] for p in parts},parts=len(parts))
 module=trimesh.util.concatenate([meshes[n] for n in cfg['module_parts']+cfg['cap_parts']+cfg['clamp_parts']]);check('source_module_envelope',np.max(abs(module.extents-cfg['source_envelope_m']))<2e-6,measured_m=module.extents.tolist(),source_m=cfg['source_envelope_m'])
 required=['sphere_ptfe_body','sphere_ptfe_cap','sphere_metal_body','sphere_metal_cap','sphere_cap_carrier','sphere_housing','large_PTFE_reference']
 check('closed_interface_solids',all(meshes[n].is_watertight and meshes[n].is_winding_consistent and meshes[n].volume>0 for n in required),details={n:dict(closed=meshes[n].is_watertight,positive=bool(meshes[n].volume>0)) for n in required})
 center=np.array([0,-.058,.084]);sphere=meshes['sphere_ptfe_body'];radii=np.linalg.norm(sphere.vertices-center,axis=1);inner=radii[(radii<.05502)&(radii>.05498)];outer=radii[(radii<.05902)&(radii>.05898)]
 check('source_110_mm_inner_sphere',len(inner)>100 and np.max(abs(inner-.055))<3e-5,measured_diameter_m=float(np.median(inner)*2))
 check('source_4_mm_PTFE_coating',len(outer)>100 and abs(float(np.median(outer)-np.median(inner))-.004)<1e-5)
 directions=np.array([[1,0,0],[0,0,-1],[0,1,0]])
 check('sphere_is_hollow',not sphere.contains(center+directions*.050).any())
 cap=meshes['sphere_cap_carrier'];angles=np.arange(96)*2*np.pi/96
 circle=lambda r:np.c_[r*np.cos(angles),np.full(96,-.120),.084+r*np.sin(angles)]
 check('source_16_mm_reflectance_opening',not cap.contains(circle(.0079)).any() and cap.contains(circle(.0081)).all())
 front=[n for n in required if n.startswith('sphere_')]
 points=np.array([[x,y,.084+z] for x,z in [(0,0),(.004,0),(0,.004)] for y in [-.126,-.120,-.112,-.100,-.080]])
 blocked=[n for n in front if meshes[n].contains(points).any()]
 check('reflectance_corridor_not_blocked',not blocked,blocked=blocked)
 lens=meshes['transmission_lens_frame'];grid=np.array([[x,.009,.084+z] for x in [-.009,0,.009] for z in [-.008,0,.008]])
 check('source_transmission_aperture_open',not lens.contains(grid).any())
 check('reference_plate_source_size',np.max(abs(meshes['large_PTFE_reference'].extents-[.04445,.006,.04445]))<1e-6)
 check('removable_cap_separate_from_module',set(cfg['cap_parts']).isdisjoint(cfg['module_parts']) and len(cfg['cap_parts'])>4 and 'cap_mark_S' in cfg['cap_parts'] and 'cap_mark_D' in cfg['cap_parts'])
 check('spring_clamp_distinct',set(cfg['clamp_parts']).isdisjoint(cfg['cap_parts']) and {'sample_clamp_post','sample_clamp_slider','sample_clamp_arm','sample_clamp_contact','sample_clamp_spring'}<=set(cfg['clamp_parts']))
 check('source_rear_feet_and_front_pin',all(n in meshes for n in ['rear_lockdown_foot_-1','rear_lockdown_foot_1','front_lockdown_pin']))
 check('cover_and_optics_separated',all(n in meshes for n in cfg['cover_parts']) and not any(n.startswith('mirror_face') for n in cfg['cover_parts']))
 connector=next(i for i in cfg['interfaces'] if i['id']=='detector_connector');check('unresolved_contact_layout_not_fabricated',connector['contact_layout'] is None and connector['pinout'] is None and not connector['mating_qualified'])
 h=cfg['handling_requirements'];check('source_five_kg_payload_not_shrunk_to_fit_robot',cfg['source_mass_kg']==5 and h['source_payload_kg']==5 and h['current_Panda_payload_kg']==3 and not h['direct_Panda_lift_allowed'])
 check('per_part_inference_records',all(p.get('geometry_basis') for p in parts) and not cfg['manufacturer_CAD'] and not cfg['contact_qualified'])
 check('builder_and_sources_pinned',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['sources_sha256']==sha(HERE/'sources.json'))
 check('artifact_hashes',all(sha(HERE/n)==digest for n,digest in receipt['artifacts_sha256'].items()))
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,glb_sha256=sha(HERE/'geometry/cary_internal_dra_2500.glb'),validator_sha256=sha(Path(__file__)),manufacturer_CAD=False,contact_qualified=False,scope='Static source-specific internal DRA geometry and handling requirements; no robot, optical, connector or electrical qualification.')
 (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
