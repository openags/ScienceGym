"""Add inferred running clearances to the existing Nicolet reconstruction.

Preserve external moving parts, interfaces, sizes and all other scene meshes.
Cut hinge seats, a front/rear closure seam and shallow key wells into four
stationary parts. These local clearances are inferred, not manufacturer CAD.
"""
import copy,hashlib,json,math
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=ROOT/'assets/cooling_lab_v1/geometry/prepared_nicolet.glb'
scene=trimesh.load(source,force='scene',process=False)
interfaces=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
manifest=json.loads((ROOT/'viewer/cooling_concept_v2/runtime_scene.json').read_text())
asset=next(a for a in manifest['assets'] if a['id']=='nicolet');normal=np.array(asset['normalization_matrix'])
def shift(xyz):
 m=np.eye(4);m[:3,3]=xyz;return m
def world(name):
 t,k=scene.graph[name];m=scene.geometry[k].copy();m.apply_transform(t);return m
cover=next(i for i in interfaces['interfaces'] if i['id']=='sample_cover')
pivot=(normal@np.r_[cover['pivot_m'],1.])[:3]
cuts={n:[] for n in ['sample_bay_rear_wall','rear_optics_housing','sample_bay_front','scan_panel']}
for x in [-.095,.073]:
 cutter=trimesh.creation.cylinder(radius=.0045,height=.026,sections=96)
 tr=np.eye(4);tr[:3,:3]=Rotation.from_euler('y',math.pi/2).as_matrix();tr[:3,3]=[x,pivot[1],pivot[2]];cutter.apply_transform(tr)
 for n in ['sample_bay_rear_wall','rear_optics_housing']:cuts[n].append(cutter)
for name,lower in [('sample_bay_rear_wall',.249),('sample_bay_front',.23725)]:
 m=world(name);box=trimesh.creation.box(extents=[.25,.012,.020]);box.apply_translation([m.centroid[0],m.centroid[1],lower+.010]);cuts[name].append(box)
for control in [i for i in interfaces['interfaces'] if i['kind']=='push_button']:
 axis=np.array(control['axis']);center=(normal@np.r_[control['center_m'],1.])[:3]
 cutter=trimesh.creation.cylinder(radius=.0062,height=.0015,sections=96)
 tr=trimesh.geometry.align_vectors([0,0,1],axis);tr[:3,3]=center+axis*.0012;cutter.apply_transform(tr);cuts['scan_panel'].append(cutter)
changes=[]
for name,cutters in cuts.items():
 transform,key=scene.graph[name];original=scene.geometry[key];mesh=world(name)
 mesh.merge_vertices(merge_tex=True,merge_norm=True);mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals();assert mesh.is_volume,name
 result=trimesh.boolean.difference([mesh,*cutters],engine='manifold');assert result.is_volume,name
 result.apply_transform(np.linalg.inv(transform))
 result.visual=trimesh.visual.texture.TextureVisuals(material=copy.deepcopy(original.visual.material))
 scene.geometry[key]=result
 changes.append(dict(name=name,removed_volume_m3=float(mesh.volume-result.volume),triangles_before=len(original.faces),triangles_after=len(result.faces)))
(HERE/'geometry').mkdir(exist_ok=True);out=HERE/'geometry/nicolet_6700_mechanism.glb';out.write_bytes(scene.export(file_type='glb'))
# Validate the serialized artifact with every cover part against stationary parts.
actual=trimesh.load(out,force='scene',process=False);moving=trimesh.collision.CollisionManager();fixed=trimesh.collision.CollisionManager();rest={}
cover_names=set(interfaces['cover_parts']);keys={'scan_key_'+str(i) for i in range(4)}
for name in actual.graph.nodes_geometry:
 t,k=actual.graph[name];rest[name]=t
 (moving if name in cover_names|keys else fixed).add_object(name,actual.geometry[k],t)
failures=[]
for angle in np.linspace(0,-math.radians(65),521):
 r=np.eye(4);r[:3,:3]=Rotation.from_euler('x',angle).as_matrix();delta=shift(pivot)@r@shift(-pivot)
 for n in cover_names:moving.set_transform(n,delta@rest[n])
 hit,pairs,data=moving.in_collision_other(fixed,return_names=True,return_data=True)
 bad=[dict(pair=sorted(d.names),depth=float(d.depth)) for d in data if abs(d.depth)>1e-7]
 if bad:failures.append(dict(angle=float(angle),pairs=bad))
for control in [i for i in interfaces['interfaces'] if i['kind']=='push_button']:
 name='scan_key_'+control['id'].split('_')[-1]
 for distance in np.linspace(0,.0003,31):
  moving.set_transform(name,shift(np.array(control['axis'])*distance)@rest[name])
  hit,pairs,data=moving.in_collision_other(fixed,return_names=True,return_data=True)
  bad=[dict(pair=sorted(d.names),depth=float(d.depth)) for d in data if abs(d.depth)>1e-7]
  if bad:failures.append(dict(button=name,travel=float(distance),pairs=bad))
 moving.set_transform(name,rest[name])
unchanged=[]
old=trimesh.load(source,force='scene',process=False)
for name in old.graph.nodes_geometry:
 if name in cuts:continue
 ta,ka=old.graph[name];tb,kb=actual.graph[name]
 assert np.max(abs(ta-tb))<1e-12 and np.array_equal(old.geometry[ka].vertices,actual.geometry[kb].vertices) and np.array_equal(old.geometry[ka].faces,actual.geometry[kb].faces),name
 unchanged.append(name)
report=dict(scope=__doc__,passed=not failures,source_path=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometry_override=dict(asset='nicolet',path=str(out.relative_to(ROOT)),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),changes=changes,unchanged_parts=unchanged,cover_states=521,button_states=124,failures=failures,inferred_dimensions=True)
(HERE/'build_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],unchanged_parts=len(unchanged),failed_states=len(failures))),flush=True)
