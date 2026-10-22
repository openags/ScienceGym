"""Independent static geometry checks for the Cary 5000 and legacy extension."""
import json,hashlib
from pathlib import Path
import numpy as np,trimesh
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 scene=trimesh.load(HERE/'geometry/cary_5000.glb',force='scene');meshes={}
 for name in scene.graph.nodes_geometry:
  transform,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(transform);m.vertices=np.asarray(m.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
  m.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=9);meshes[name]=m
 cfg=json.loads((HERE/'interfaces.json').read_text());parts=json.loads((HERE/'parts.json').read_text());receipt=json.loads((HERE/'build_receipt.json').read_text());checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 check('all_parts_exported',set(meshes)=={p['id'] for p in parts},parts=len(parts))
 housing=['instrument_plinth','lower_instrument_housing','left_optics_housing','right_optics_housing','rear_sample_housing']+[n for n in meshes if n.startswith('rear_lid_pocket_')];body=trimesh.util.concatenate([meshes[n] for n in housing])
 check('source_main_housing_envelope',np.max(abs(body.extents-cfg['source_envelope_m']))<2e-6,measured_m=body.extents.tolist(),source_m=cfg['source_envelope_m'],reference=cfg['source_envelope_reference'])
 complete=trimesh.util.concatenate([meshes[n] for n in cfg['main_parts']]);check('selected_projections_reported',bool(cfg['source_envelope_reference']),complete_instrument_bounds_m=complete.bounds.tolist(),complete_envelope_m=complete.extents.tolist())
 required=housing+cfg['sliding_lid_parts']+cfg['front_panel_parts'][:1]+cfg['extension_base_parts']+cfg['extension_cover_parts']
 invalid=[dict(part=n,closed=meshes[n].is_watertight,winding=meshes[n].is_winding_consistent,volume=float(meshes[n].volume)) for n in required if not(meshes[n].is_watertight and meshes[n].is_winding_consistent and meshes[n].volume>0)]
 check('closed_mechanical_solids',not invalid,invalid=invalid)
 check('source_91_kg_stationary_instrument',cfg['source_instrument_mass_kg']==91 and 'Whole 91 kg instrument transport' in cfg['exclusions'])
 origin=np.array(cfg['extension']['presentation_origin_m']);left=meshes['extension_cover_side_-0.079'].bounds;right=meshes['extension_cover_side_0.079'].bounds;front=meshes['extension_cover_front'].bounds;roof=meshes['extension_cover_roof'].bounds;base=meshes['extension_base_plate'].bounds
 measured=np.array([right[0,0]-left[1,0],origin[1]+.084-front[1,1],roof[0,2]-base[1,2]])
 check('legacy_extension_source_internal_dimensions',np.max(abs(measured-cfg['extension']['source_internal_dimensions_m']))<2e-6,measured_m=measured.tolist(),source_m=cfg['extension']['source_internal_dimensions_m'])
 check('extension_base_and_cover_independent',set(cfg['extension_base_parts']).isdisjoint(cfg['extension_cover_parts']) and len(cfg['extension_cover_parts'])>5)
 check('main_slide_front_wall_and_extension_separate',not(set(cfg['sliding_lid_parts'])&set(cfg['front_panel_parts'])) and not(set(cfg['main_parts'])&set(cfg['extension_cover_parts'])))
 # The swept lid probes are topology-aware point-in-solid checks, not a
 # contact dynamics qualification. Points on known surfaces are inset.
 fixed=[n for n in cfg['main_parts'] if n not in cfg['sliding_lid_parts'] and meshes[n].is_volume]
 collisions=[]
 for travel in np.linspace(0,.305,62):
  delta=np.array([0,travel,0])
  for n in cfg['sliding_lid_parts']:
   m=meshes[n];points=np.vstack([m.vertices,m.triangles_center]);points=points*.999999+m.center_mass*.000001+delta
   for f in fixed:
    b=meshes[f].bounds;interior=points[np.all((points>b[0]+1e-7)&(points<b[1]-1e-7),axis=1)]
    if len(interior) and meshes[f].contains(interior).any():collisions.append(dict(travel_m=float(travel),moving=n,fixed=f))
 check('rearward_lid_sweep_surface_probes_clear',not collisions,positions=62,collisions=collisions,method='Exported mesh vertices and triangle centres tested inside closed fixed solids; physical contact qualification remains separate.')
 bay=cfg['selected_bare_bay'];cx,cy=bay['center_xy_m'];floor=bay['floor_z_m'];pts=np.array([[cx+x,cy+y,floor+z] for x in [-.065,0,.065] for y in [-.18,0,.18] for z in [.020,.10,.19]])
 blocked=[n for n in housing if meshes[n].contains(pts).any()];check('sample_bay_has_usable_interior',not blocked,blocked=blocked,dimensions_inferred=bay['dimensions_are_inferred'])
 holes=[]
 for x in [.130,.240]:
  name='extension_keyhole_bracket_'+str(x);m=meshes[name];points=np.array([[x,-.354,.156],[x,-.354,.147]])
  holes.append(dict(part=name,open=bool(not m.contains(points).any()),edge_solid=bool(m.contains([[x+.008,-.354,.150]])[0])))
 check('two_open_keyhole_sockets',all(h['open'] and h['edge_solid'] for h in holes),details=holes)
 hose=[]
 for x in [-.05,.05]:
  name='extension_hose_barb_'+str(x);m=meshes[name];p=origin+[x,-.095,.015]
  hose.append(dict(part=name,open=bool(not m.contains([p])[0]),wall=bool(m.contains([p+[.003,0,0]])[0])))
 check('two_hollow_extension_hose_barbs',all(h['open'] and h['wall'] for h in hose),details=hose)
 check('documented_lift_slide_hinge_sequence',next(i for i in cfg['interfaces'] if i['id']=='extension_cover')['kind']=='lift_slide_detachable_hinge' and 'extension_hinge_bar' in cfg['extension_base_parts'])
 check('per_part_inference_records',all(p.get('geometry_basis') for p in parts) and not cfg['manufacturer_CAD'] and not cfg['contact_qualified'])
 check('builder_and_sources_pinned',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['sources_sha256']==sha(HERE/'sources.json'))
 check('artifact_hashes',all(sha(HERE/n)==digest for n,digest in receipt['artifacts_sha256'].items()))
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,glb_sha256=sha(HERE/'geometry/cary_5000.glb'),validator_sha256=sha(Path(__file__)),manufacturer_CAD=False,contact_qualified=False,scope='Static source-specific enclosure, access and legacy extension geometry; no robot or contact-dynamics qualification.')
 (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2));return report['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
