"""Independent read-only reopen/reimport audit of the original static scene."""
import bpy,json,pathlib,math,hashlib,struct
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1]
C=json.loads((P/'scene_binding_contract.json').read_text())
R={'review_scope':'Static authored geometry only; no physics or physical-interface qualification','checks':[],'native':{},'glb':{}}
def check(name,condition,detail=None):
 R['checks'].append({'name':name,'passed':bool(condition),'detail':detail})
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [(min(q[i] for q in p),max(q[i] for q in p)) for i in range(3)]
def gap(a,b):return bounds(a)[2][0]-bounds(b)[2][1]
def contains_xy(base,top):
 a,b=bounds(base),bounds(top)
 return all(a[i][0]-1e-6<=b[i][0] and a[i][1]+1e-6>=b[i][1] for i in range(2))
def source_objects():return [o for o in bpy.context.scene.objects if o.name.endswith('.source_envelope')]
blend=P/'geometry/thermalmeta_lab.blend';glb=P/'geometry/thermalmeta_lab.glb'
magic=blend.read_bytes()[:4]
check('native_file_is_compressed',magic in [bytes.fromhex('28b52ffd'),bytes.fromhex('1f8b0800')],magic.hex())
bpy.ops.wm.open_mainfile(filepath=str(blend));s=bpy.context.scene;bpy.context.view_layer.update()
check('native_is_metre_scale',s.unit_settings.system=='METRIC' and abs(s.unit_settings.scale_length-1)<1e-9)
check('native_cpu_cycles',s.render.engine=='CYCLES' and s.cycles.device=='CPU')
check('native_default_no_actuation_or_physics',s.get('physical_actuation_enabled') is False and s.get('physics_simulation_performed') is False and s.get('geometry_interface_qualified') is False)
check('no_native_embedded_scripts',len(bpy.data.texts)==0)
check('no_external_image_assets',len([i for i in bpy.data.images if i.source not in {'GENERATED','VIEWER'}])==0)
check('no_external_linked_libraries',len(bpy.data.libraries)==0)
check('native_no_animation_or_dynamics',not any(o.animation_data or o.rigid_body or o.rigid_body_constraint for o in s.objects) and len(bpy.data.actions)==0 and len(s.timeline_markers)==0)
assets=[o for o in s.objects if o.name in {f'A{i:02d}' for i in range(1,11)}]
check('exact_ten_asset_roots',len(assets)==10 and all(o.type=='EMPTY' and o.get('asset_id')==o.name for o in assets))
anchors=[o for o in s.objects if o.get('anchor_id')]
check('exact_25_unique_anchors',len(anchors)==25 and {o.get('anchor_id') for o in anchors}=={a['anchor_id'] for a in C['anchors']})
check('exact_six_source_envelopes',len(source_objects())==6)
expected={};native_records=[]
for a in C['anchors']:
 o=bpy.data.objects.get(a['object_name']);ok=o is not None and o.type=='EMPTY' and o.get('anchor_id')==a['anchor_id'] and o.get('asset_id')==a['asset_id'] and (o.matrix_world.translation-Vector(a['position_m'])).length<1e-6
 check('native_anchor_'+a['anchor_id'],ok);expected[a['object_name']]=list(o.matrix_world.translation)
for c in C['condition_views']:
 cid=c['condition_id'];root=bpy.data.objects[c['root_object']];o=bpy.data.objects[c['envelope_object']];pad=bpy.data.objects[c['support_object']];base=bpy.data.objects[c['carrier_object']];cover=bpy.data.objects[c['cover_object']];table=bpy.data.objects['A02.condition_display_top'];d=list(o.dimensions)
 check('native_nominal_envelope_'+cid,all(abs(x-y)<1e-6 for x,y in zip(d,[.12,.12,.0045])),d)
 check('native_identity_'+cid,root.get('specimen_id')==c['specimen_id'] and o.get('specimen_id')==c['specimen_id'] and o.get('qualified_geometry') is False)
 check('native_support_chain_'+cid,all(abs(x)<1e-6 for x in [gap(o,pad),gap(pad,base),gap(base,table)]) and contains_xy(pad,o) and contains_xy(base,pad) and contains_xy(table,base),{'specimen_to_pad_m':gap(o,pad),'pad_to_carrier_m':gap(pad,base),'carrier_to_table_m':gap(base,table)})
 check('native_cover_clearance_'+cid,gap(cover,o)>.01,{'vertical_clearance_m':gap(cover,o)})
 arrow=bpy.data.objects[cid+'.orientation_shaft'];profile=bpy.data.objects[c['profile_object']]
 av=(arrow.matrix_world.to_3x3()@Vector((0,0,1))).normalized();pv=(profile.matrix_world.to_3x3()@Vector((0,0,1))).normalized();dot=abs(av.dot(pv));target=0 if c['sample_family_id']=='ROTATOR45' else 1
 check('native_profile_relation_'+cid,abs(dot-target)<1e-5,{'absolute_direction_dot':dot,'authored_number_mapping':c['profile_number_to_orientation_status']})
 check('native_orientation_reference_'+cid,abs(av.dot(Vector((1,0,0) if c['orientation']=='X' else (0,1,0))))>1-1e-5)
 native_records.append({'condition_id':cid,'dimensions_m':d,'specimen_id':o.get('specimen_id'),'static_contact_gap_m':gap(o,pad)})
contact_rows=json.loads((P/'contact_contract.json').read_text())['contacts']
check('exact_20_declared_static_contacts',len(contact_rows)==20)
for i,c in enumerate(contact_rows):
 a=bpy.data.objects[c['supported_object']];b=bpy.data.objects[c['support_object']];ab,bb=bounds(a),bounds(b)
 overlap=all(min(ab[j][1],bb[j][1])-max(ab[j][0],bb[j][0])>0 for j in range(2))
 check('native_declared_contact_'+str(i+1),abs(gap(a,b)-c['expected_vertical_gap_m'])<c['tolerance_m'] and overlap and c['physical_fit_qualified'] is False,{'supported_object':a.name,'support_object':b.name,'vertical_gap_m':gap(a,b),'xy_overlap':overlap})
for n in ['A03.closed_front','A06.closed_glass_front','A06.closed_lid','A06.guard_back','A06.guard_side','A06.bath_lid','A06.side_foam','A09.QUARANTINE_bin','A09.STORAGE_bin','A10.parking_support']:
 check('service_geometry_'+n,n in bpy.data.objects)
labels='\n'.join(o.data.body for o in s.objects if o.type=='FONT')
for key in ['QUALIFICATION HELD','NO HARDWARE CONTROL','NO THERMAL DATA','NOT SOURCE-VERIFIED','NOT HEAT FLOW','CUSTODY HELD','STABILITY: NONE','RELEASE: NONE','PHYSICAL UNITS: HOLD']:
 check('native_label_'+key,key in labels)
R['native']={'object_count':len(s.objects),'font_object_count':len([o for o in s.objects if o.type=='FONT']),'condition_geometry':native_records,'sha256':hashlib.sha256(blend.read_bytes()).hexdigest()}
b=glb.read_bytes();raw_glb=b;magic,version,size=struct.unpack_from('<4sII',b,0);check('glb_header',magic==b'glTF' and version==2 and size==len(b));l,t=struct.unpack_from('<II',b,12);doc=json.loads(b[20:20+l]);check('glb_embedded_geometry_only',not doc.get('images') and not doc.get('animations') and not doc.get('skins') and not any('uri' in q for q in doc.get('buffers',[])));check('glb_no_external_resource_uris','"uri"' not in json.dumps(doc))
glass_materials=[m for m in doc.get('materials',[]) if m.get('name')=='glass']
check('glb_transparent_panes_use_standard_alpha',len(glass_materials)==1 and glass_materials[0].get('alphaMode')=='BLEND' and abs(glass_materials[0].get('pbrMetallicRoughness',{}).get('baseColorFactor',[0,0,0,1])[3]-.07)<1e-9)
check('glb_transparency_approximation_labeled',len(glass_materials)==1 and glass_materials[0].get('extras',{}).get('rendering_boundary')=='illustrative_alpha_approximation_not_optical_physics')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb));bpy.context.view_layer.update()
gm=bpy.data.materials.get('glass');principled=[n for n in gm.node_tree.nodes if n.type=='BSDF_PRINCIPLED'] if gm and gm.use_nodes else []
check('glb_reimport_preserves_transparent_pane_alpha',len(principled)==1 and abs(principled[0].inputs['Alpha'].default_value-.07)<1e-6)
check('glb_preserves_exact_six_envelopes',len(source_objects())==6)
for a in C['anchors']:
 o=bpy.data.objects.get(a['object_name']);check('glb_anchor_'+a['anchor_id'],o is not None and (o.matrix_world.translation-Vector(expected[a['object_name']])).length<2e-5 and o.get('anchor_id')==a['anchor_id'] and o.get('asset_id')==a['asset_id'])
for c in C['condition_views']:
 cid=c['condition_id'];o=bpy.data.objects[c['envelope_object']];pad=bpy.data.objects[c['support_object']];root=bpy.data.objects[c['root_object']]
 check('glb_nominal_envelope_'+cid,all(abs(x-y)<2e-5 for x,y in zip(o.dimensions,[.12,.12,.0045])))
 check('glb_identity_'+cid,o.get('specimen_id')==c['specimen_id'] and root.get('specimen_id')==c['specimen_id'] and o.get('qualified_geometry') is False)
 check('glb_contact_'+cid,abs(gap(o,pad))<2e-5)
for i,c in enumerate(contact_rows):
 a=bpy.data.objects[c['supported_object']];b=bpy.data.objects[c['support_object']]
 check('glb_declared_contact_'+str(i+1),abs(gap(a,b)-c['expected_vertical_gap_m'])<2e-5,{'vertical_gap_m':gap(a,b)})
check('glb_labels_converted_to_geometry',len([o for o in bpy.context.scene.objects if o.type=='FONT'])==0)
R['glb']={'object_count':len(bpy.context.scene.objects),'sha256':hashlib.sha256(raw_glb).hexdigest(),'bytes':len(raw_glb),'embedded_buffer_bytes':sum(x.get('byteLength',0) for x in doc.get('buffers',[]))}
R['passed']=all(c['passed'] for c in R['checks']);R['passed_check_count']=sum(c['passed'] for c in R['checks']);R['total_check_count']=len(R['checks'])
(P/'review/independent_geometry_audit.json').write_text(json.dumps(R,indent=2)+'\n')
print('INDEPENDENT_GEOMETRY_RESULT',json.dumps({'passed':R['passed'],'checks':len(R['checks']),'failures':[x['name'] for x in R['checks'] if not x['passed']]}))
if not R['passed']:raise SystemExit(1)
