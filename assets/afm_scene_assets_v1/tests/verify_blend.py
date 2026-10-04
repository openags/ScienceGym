"""Read actual Blender geometry and exercise authored kinematic poses."""
import bpy,json,math,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=bpy.context.scene
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise AssertionError(k)
check('metric_scale',s.unit_settings.system=='METRIC' and s.unit_settings.scale_length==1)
check('cpu_cycles',s.render.engine=='CYCLES' and s.cycles.device=='CPU')
roots=[o for o in s.objects if 'asset_id' in o]
check('stable_asset_roots',len(roots)==17 and len({o['asset_id'] for o in roots})==17)
check('no_copied_raster_resources',not any(i.filepath for i in bpy.data.images if i.name not in ['Render Result','Viewer Node']))
check('finite_meshes',all(math.isfinite(x) for o in s.objects if o.type=='MESH' for v in o.data.vertices for x in v.co))
check('nonzero_meshes',all(len(o.data.vertices)>0 for o in s.objects if o.type=='MESH'))
al=bpy.data.objects['array.reflective_film'];pd=bpy.data.objects['array.pdms'];cone=bpy.data.objects['array.microcone.00.00']
check('native_PDMS_Al_attached',abs(pd.location.z-pd.dimensions.z/2-(al.location.z+al.dimensions.z/2))<5e-8)
check('native_Al_cone_attached',abs(al.location.z-al.dimensions.z/2-(cone.location.z+cone.dimensions.z/2))<5e-8)
check('native_cone_height',abs(cone.dimensions.z-6e-6)<1e-10)
check('native_cylinder_height',abs(bpy.data.objects['coupon.micro_cylinder.0'].dimensions.z-6e-6)<1e-10)
for mode in ['docked','held','docked','held']:
 sys.argv=['verify_blend.py','--',mode];runpy.run_path(str(P/'geometry'/'apply_demo_pose.py'));bpy.context.view_layer.update()
 for o in bpy.data.objects['afm.sample_carrier_demo'].children:
  if o.name.startswith('clamp.demo.open_arm'):
   left=o.name=='clamp.demo.open_arm';px=.327 if left else .473;py=-.263
   check('clamp_orbit_'+mode+'_'+o.name,abs(math.hypot(o.location.x-px,o.location.y-py)-.021)<1e-7)
check('no_rigid_body_backend',s.rigidbody_world is None)
(P/'review'/'blend_validation.json').write_text(json.dumps({'tool':'Blender '+bpy.app.version_string,'mode':'read_geometry_and_local_demo_transforms','checks':checks,'passed':all(checks.values()),'device_IO':False},indent=2))
print('BLEND_VALIDATION_PASSED',len(checks))
