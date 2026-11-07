"""Inspect exported commercial dimensions and physically separate lead paths."""
from pathlib import Path
import json
import hashlib
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent

def main():
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 scene=trimesh.load(HERE/'geometry/omega_khr_2_2_p.glb',force='scene');meshes={}
 for name in scene.graph.nodes_geometry:
  transform,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(transform)
  mesh.vertices=np.asarray(mesh.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]]);meshes[name]=mesh
 checks=[]
 def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
 parts=json.loads((HERE/'parts.json').read_text());interfaces=json.loads((HERE/'interfaces.json').read_text())
 check('all_parts_exported',set(meshes)=={p['id'] for p in parts},meshes=len(meshes))
 ext=meshes['heater_laminate'].extents
 check('commercial_2_inch_outline',np.max(np.abs(ext[:2]-.0508))<2e-6,diameter_xy_m=ext[:2].tolist())
 low=min(meshes[n].bounds[0,2] for n in ['heater_laminate','PSA_layer']);high=max(meshes[n].bounds[1,2] for n in ['heater_laminate','PSA_layer'])
 check('selected_thickness_below_source_maximum',abs(high-low-.0002)<1e-6 and high-low<.000254,measured_m=float(high-low),source_max_m=.000254)
 check('radial_overhang_preserved',abs(interfaces['mounting_face']['radial_overhang_m']-.0004)<1e-9)
 paths=[]
 for terminal in interfaces['terminals']:
  points=np.array(terminal['centerline_m']);paths.append(points);length=np.linalg.norm(np.diff(points,axis=0),axis=1).sum()
  check(terminal['id']+'_305mm_lead',abs(length-.305)<1e-5,length_m=float(length))
  # Exclude neighbours within 5 mm along the centreline, not a fixed index
  # count, because the first straight segment is much longer than the mesh.
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
  distance=np.linalg.norm(points[:,None,:]-points[None,:,:],axis=-1)
  distance[np.abs(arc[:,None]-arc[None,:])<.005]=np.inf
  clearance=float(distance.min());check(terminal['id']+'_no_self_overlap',clearance>.001,nonlocal_centerline_clearance_m=clearance)
 separation=float(np.linalg.norm(paths[0][:,None,:]-paths[1][None,:,:],axis=-1).min())
 check('two_separate_conductors',separation>.001,minimum_centerline_separation_m=separation)
 check('two_actual_heater_nodes',len(interfaces['terminals'])==2 and {'stripped_1','stripped_2'}<=set(meshes))
 receipt=json.loads((HERE/'build_receipt.json').read_text())
 check('builder_and_source_pins',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['source_sha256']==sha(HERE/'sources.json'))
 check('artifact_pins',all(sha(HERE/n)==digest for n,digest in receipt['artifacts_sha256'].items()))
 result=dict(passed=all(x['passed'] for x in checks),checks=checks,validator_sha256=sha(Path(__file__)),
             geometry_sha256=sha(HERE/'geometry/omega_khr_2_2_p.glb'),contact_qualified=False,electrical_qualified=False,
             scope='Commercial outline, lead length/topology, exported geometry and declared reconstruction dimensions; no adhesion, bending or circuit validation')
 (HERE/'geometry_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result['passed']
if __name__=='__main__':raise SystemExit(0 if main() else 1)
