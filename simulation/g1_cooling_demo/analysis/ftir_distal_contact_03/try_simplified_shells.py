"""Screen bounded simplification of intersecting source shells before TetGen.

These are collision-geometry candidates only. Source visuals are unchanged;
no candidate is attached to the physical plant by this script.
"""
import hashlib,json,sys,time,numpy as np,trimesh,manifold3d
from pathlib import Path
from meshpy.tet import MeshInfo,Options,build

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'simulation/g1_cooling_demo'))
from convex_cells import clean

rows=[]
for link in ['right_index_2','right_thumb_4']:
 source=ROOT/'assets/unitree_g1_inspire_v1/vendor/unitree_ros/meshes'/(link+'.STL')
 raw=clean(trimesh.load(source,force='mesh'));parts=raw.split(only_watertight=False)
 retained=[p for p in parts if p.is_watertight and len(p.faces)>20 and abs(p.volume)>1e-10]
 core=trimesh.util.concatenate(retained);outer=trimesh.util.concatenate([p for p in retained if p.volume>0]);holes=[]
 rng=np.random.default_rng(846)
 for p in retained:
  if p.volume>=0:continue
  points=rng.uniform(p.bounds[0],p.bounds[1],(4096,3));points=points[p.contains(points)&outer.contains(points)]
  distance=trimesh.proximity.closest_point(p,points)[1];holes.append(points[np.argmax(distance)].tolist())
 solid=manifold3d.Manifold(manifold3d.Mesh64(vert_properties=np.asarray(core.vertices),tri_verts=np.asarray(core.faces,dtype=np.uint64)))
 for tolerance in [1e-7,1e-6,1e-5,5e-5]:
  start=time.monotonic();candidate=solid.simplify(tolerance).to_mesh64()
  mesh=trimesh.Trimesh(np.asarray(candidate.vert_properties)[:,:3],np.asarray(candidate.tri_verts),process=False)
  name=link+'_'+format(tolerance,'.0e');mesh.export(HERE/(name+'.ply'))
  row=dict(link=link,tolerance_m=tolerance,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
      original_retained_volume_m3=float(core.volume),candidate_volume_m3=float(mesh.volume),
      relative_volume_change=float((mesh.volume-core.volume)/core.volume),faces=len(mesh.faces),
      candidate_path=name+'.ply',qualified=False)
  info=MeshInfo();info.set_points(mesh.vertices);info.set_facets(mesh.faces)
  if holes:info.set_holes(holes)
  try:
   tet=build(info,options=Options('pYQ'));points=np.asarray(tet.points);elements=np.asarray(tet.elements)
   volumes=abs(np.linalg.det(points[elements[:,1:]]-points[elements[:,:1]]))/6
   np.savez_compressed(HERE/(name+'_tetrahedra.npz'),points=points,elements=elements)
   row.update(status='tetrahedra_produced',tetrahedra=len(elements),tetrahedra_volume_m3=float(volumes.sum()),
       relative_tetrahedra_volume_error=float(abs(volumes.sum()-mesh.volume)/mesh.volume))
  except Exception as error:row.update(status='failed',error=str(error))
  row['seconds']=time.monotonic()-start;rows.append(row);print(json.dumps(row),flush=True)
  (HERE/'review.json').write_text(json.dumps(dict(scope=__doc__,rows=rows,plant_changed=False),indent=2)+'\n')
