"""Execute with Blender -b geometry/cooling_operations_lab.blend --python tests/verify_blend.py."""
import bpy,sys,json,math,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P));from semantic_controls import State,transition
spec=importlib.util.spec_from_file_location('binder',P/'geometry/apply_demo_state.py');binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
checks=[]
def ok(name,test):
    assert test,name
    checks.append({'id':name,'result':'pass'})
def close(a,b,tol=1e-7):return abs(a-b)<=tol
inv=json.loads((P/'asset_inventory.json').read_text());roots={a['asset_id'] for a in inv['assets']}
ok('exact_eight_unique_roots',len(roots)==8 and all(x in bpy.data.objects for x in roots))
ok('metric_native_units',bpy.context.scene.unit_settings.system=='METRIC' and bpy.context.scene.unit_settings.scale_length==1)
ok('cpu_render_configuration',bpy.context.scene.render.engine=='CYCLES' and bpy.context.scene.cycles.device=='CPU')
for sample in ['white','black']:
    d=bpy.data.objects[sample+'.emitter_copper'].dimensions
    ok(sample+'_copper_dimensions',all(close(x,y) for x,y in zip(d,[.05,.05,.0005])))
    for layer in ['lower','upper']:ok(sample+'_'+layer+'_16um',close(bpy.data.objects[sample+'.film.'+layer].dimensions.z,.000016,1e-8))
    o=bpy.data.objects[sample+'.reflector_disk'];ok(sample+'_height_unresolved',o['physical_target_height_m']=='UNKNOWN' and close(o['display_height_m'],.15))
ok('two_display_films_50x',all(close(bpy.data.objects['handling.film.'+k].dimensions.z,.0008) and bpy.data.objects['handling.film.'+k]['display_thickness_scale']==50 for k in ['lower','upper']))
s=State();binder.bind(s)
start=bpy.data.objects['carrier.tray'].location.copy()
s=transition(s,'open_clamp');binder.bind(s)
for k in [0,1]:
    o=bpy.data.objects[f'clamp.{k}.lever'];p=bpy.data.objects[f'clamp.{k}.pivot'].location
    # Rotated center must stay one .018 m radius from shown pivot.
    ok('pivot_correct_clamp_'+str(k),close(o.rotation_euler.z,math.pi/2) and close(o.location.x,p.x) and close(o.location.y,p.y+.018))
s=transition(s,'grasp_carrier');binder.bind(s)
ok('carrier_label_bound','HELD DEMO / CLAMPS OPEN' in bpy.data.objects['dock.nameplate.text'].data.body)
ok('bound_carrier_lift',close(bpy.data.objects['carrier.tray'].location.z,start.z+.1))
binder.bind(s);ok('pose_idempotent',close(bpy.data.objects['carrier.tray'].location.z,start.z+.1))
s=transition(s,'dock_carrier');s=transition(s,'tear_lower_film');binder.bind(s)
ok('torn_variant_bound',bpy.data.objects['handling.film.lower'].hide_render and not bpy.data.objects['handling.film.lower.torn_variant'].hide_render)
s=transition(s,'replace_lower_film');binder.bind(s)
ok('torn_variant_same_identity',bpy.data.objects['handling.film.lower.torn_variant']['component_identity']=='handling.pe.lower.rev2')
ok('replacement_identity_revision',bpy.data.objects['handling.film.lower']['component_identity']=='handling.pe.lower.rev2')
s=transition(s,'close_clamp');s=transition(s,'cover_apertures');binder.bind(s)
ok('two_lids_bound',all(all(close(a,b) for a,b in zip(bpy.data.objects[k+'.aperture_lid'].location,bpy.data.objects[k+'.aperture_lid']['closed_pose_m'])) for k in ['white','black']))
s=transition(s,'arm_logger');binder.bind(s)
ok('logger_readback_demo',bpy.data.objects['logger.readback'].data.body=='LOGGER: ARMED DEMO')
try:transition(s,'open_clamp');raise AssertionError('Guard failed')
except ValueError:ok('guard_rejects_live_demo_handling',True)
s=transition(s,'stop_logger');s=transition(s,'select_ftir_angle');s=transition(s,'mount_reference');binder.bind(s)
ok('reference_bound_to_angle_fixture',all(close(a,b) for a,b in zip(bpy.data.objects['optical.reference_disk'].location,[.283,.270,.284])))
s=transition(s,'reflector_right');binder.bind(s)
ok('reflector_bound_pose',close(bpy.data.objects['white.reflector_disk'].location.x,-.43))
ok('physical_false_after_all_events',not bpy.context.scene['physical_execution'] and not s.physical_execution and not s.geometry_qualified)
# Canonical original scene is untouched on disk. This process does not save.
out={'blender':bpy.app.version_string,'result':'pass','checks':checks,'count':len(checks),'scope':'native dimensions and bound semantic poses only','scientific_execution':False}
(P/'review'/'blend_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
