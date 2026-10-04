"""Extract only original Apache-2.0 AFM carrier and clamp meshes, never article-derived geometry."""
import bpy,json,hashlib,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
src=root.parent/'afm_scene_assets_v1/geometry/afm_operations_lab.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
parts=[]
origin=(-.39,-.065,.315)
for parent,family in [('afm.sample_carrier','afm.sample_carrier'),('afm.retention_clamps','afm.retention_clamps')]:
 for o in bpy.data.objects[parent].children:
  assert o.type=='MESH'
  modifiers=[]
  for m in o.modifiers:
   if m.type=='BEVEL':modifiers.append({'type':'BEVEL','width':m.width,'segments':m.segments})
   elif m.type=='WEIGHTED_NORMAL':modifiers.append({'type':'WEIGHTED_NORMAL'})
   else:raise ValueError(m.type)
  parts.append({'source_part_id':o.name,'source_asset_family':family,'translation_m':[o.location[i]-origin[i] for i in range(3)],'rotation_euler_rad':list(o.rotation_euler),'scale':list(o.scale),'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'smooth_faces':[p.use_smooth for p in o.data.polygons],'source_material':o.data.materials[0].name,'modifiers':modifiers})
data={'schema':'original_mesh_reuse.v1','source_package':'afm_scene_assets_v1','source_blend':'geometry/afm_operations_lab.blend','source_blend_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'license':'Apache-2.0','source_geometry_basis':'Original authored carrier and clamp primitives; no AFM scientific microgeometry reused','reuse_family_count':2,'new_unique_asset_credit':0,'source_origin_m':list(origin),'parts':parts}
(root/'geometry/reused_carrier_components.json').write_text(json.dumps(data,indent=2))
print('EXTRACTED',len(parts),'parts from two existing families')
