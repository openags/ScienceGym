"""Prepare closed drilled sphere segments using robust solid booleans.

The mesh stage is separate from Blender so its Python packages need not be
installed into Blender's bundled interpreter. No manufacturer mesh is used.
"""
import json,hashlib,importlib.metadata
from pathlib import Path
import numpy as np,trimesh,manifold3d
HERE=Path(__file__).resolve().parent
CENTER=np.array([0,-.058,.084])

def box(size,position):
 m=trimesh.creation.box(size);m.apply_translation(position);return m

def cylinder(radius,height,position,axis='Z'):
 m=trimesh.creation.cylinder(radius,height,sections=96)
 if axis=='Y':m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
 m.apply_translation(position);return m

def main():
 cuts=[cylinder(.008,.040,[0,-.119,.084],'Y'),box([.019,.030,.017],[0,-.002,.084]),box([.030,.011,.013],[-.056,-.058,.084]),cylinder(.0055,.040,[-.022,-.055,.137]),box([.016,.014,.040],[.018,-.055,.137]),cylinder(.007,.040,[.010,-.055,.137]),cylinder(.007,.040,[.026,-.055,.137])]
 records={}
 for material,inner,outer in [('ptfe',.055,.059),('metal',.059,.061)]:
  a=trimesh.creation.uv_sphere(radius=outer,count=[64,96]);a.apply_translation(CENTER)
  b=trimesh.creation.uv_sphere(radius=inner,count=[64,96]);b.apply_translation(CENTER)
  shell=trimesh.boolean.difference([a,b,*cuts],engine='manifold')
  for name,position in [('body',[0,-.001,.084]),('cap',[0,-.201,.084])]:
   m=trimesh.boolean.intersection([shell,box([.20,.20,.20],position)],engine='manifold')
   # Remove sub-micrometre boolean slivers before float32 GLB export.
   # The solid simplifier preserves topology and bounds surface motion to
   # 1 micrometre; welding those slivers after export merged distinct edges.
   solid=manifold3d.Manifold(manifold3d.Mesh(np.asarray(m.vertices,dtype=np.float32),np.asarray(m.faces,dtype=np.uint32))).simplify(.000001)
   mesh=solid.to_mesh();m=trimesh.Trimesh(mesh.vert_properties[:,:3],mesh.tri_verts,process=False)
   assert m.is_watertight and m.is_winding_consistent and m.volume>0,(material,name)
   records['sphere_'+material+'_'+name]=dict(vertices=m.vertices.tolist(),faces=m.faces.tolist())
 receipt=dict(generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),surface_simplification_bound_m=.000001,versions={n:importlib.metadata.version(n) for n in ['trimesh','numpy','manifold3d']},meshes=records,source='Original source-dimensioned sphere and selected port positions; no vendor mesh')
 out=HERE/'geometry';out.mkdir(exist_ok=True);(out/'sphere_parts.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n');print('Prepared four closed sphere segments')
if __name__=='__main__':main()
