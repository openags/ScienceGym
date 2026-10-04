"""Independent structural/portable/cross-package audit; standard library only.
Reads the saved files, writes review/independent_package_audit.json. Optional
argument is the paired task directory; default is sibling midinfrared_operations_v2.
"""
import ast, collections, hashlib, json, struct, sys, zlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
T=Path(sys.argv[1]) if len(sys.argv)>1 else P.parent/'midinfrared_operations_v2'
r={'audit_kind':'independent structural and cross-package review','checks':{},'errors':[],'observations':{}}
def check(n,b,detail=None):
 r['checks'][n]=bool(b)
 if not b:r['errors'].append({'check':n,'detail':detail})
def get(n):return json.loads((P/n).read_text())
def near(a,b,t=2e-6):return len(a)==len(b) and max([abs(x-y) for x,y in zip(a,b)]+[0])<t
c=get('operation_binding_contract.json');a=get('affordances.json');i=get('asset_inventory.json');m=get('asset_metadata.json');s=get('states.json');assembly=get('assembly_contract.json');stations=get('station_layout.json')
check('duplicate_operation_contracts_exact',c['operations']==get('operation_bindings.json')['operations'])
check('metadata_permanent_holds',not m['physical_geometry_validated'] and not m['physical_execution_enabled'] and not m['scientific_success'] and not m['source_pixels_or_CAD_used'] and not m['raw_data_or_author_code_read'])
check('state_permanent_holds',not s['physical_execution_enabled'] and not s['trusted_controller_implemented'] and not s['measurements_acquired'] and not s['scientific_success'])
check('state_initial_dock_empty',s['initial_state']['optical_dock']=='empty')
inv={p['scene_object']:(g['asset_id'],p) for g in i['assets'] for p in g['parts']}
for st in stations['stations']:
 check(st['station_id']+'_native_label_exists',st['scene_label'] in inv and inv[st['scene_label']][0]==st['representative_asset_id'])
for rel in assembly['relationships']:
 check(rel['child']+'_assembly_resolves',rel['child'] in inv and rel['actual_parent_object']=='ASSET.'+inv[rel['child']][0] and rel['prefix_is_logical_not_scene_object'])
for op in c['operations']:
 st=next(x for x in s['operations'] if x['id']==op['operation_id'])
 check(op['operation_id']+'_state_membership',set(op['asset_ids'])==set(st['asset_ids']) and st['primary_anchor']==op['primary_anchor'] and st['control_anchor']==op['control_anchor'])
raw=(P/'geometry/midinfrared_lab.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);check('GLB_header',magic==b'glTF' and version==2 and length==len(raw))
pos=12;chunks=[]
while pos<len(raw):
 size,kind=struct.unpack_from('<II',raw,pos);chunks.append((kind,raw[pos+8:pos+8+size]));pos+=8+size
check('GLB_chunks_self_contained',pos==len(raw) and [x[0] for x in chunks]==[0x4e4f534a,0x004e4942])
g=json.loads(chunks[0][1]);nodes=g['nodes'];names=collections.Counter(n.get('name') for n in nodes);lookup={n['name']:(idx,n) for idx,n in enumerate(nodes)};parents={child:idx for idx,n in enumerate(nodes) for child in n.get('children',[])}
check('GLB_single_scene',len(g.get('scenes',[]))==1,len(g.get('scenes',[])))
check('GLB_unique_node_names',all(v==1 for v in names.values()),{k:v for k,v in names.items() if v>1})
check('GLB_no_external_URIs',not any('uri' in x for group in ['buffers','images'] for x in g.get(group,[])))
check('GLB_no_images_textures_animation_skins',all(not g.get(k) for k in ['images','textures','animations','skins','cameras']))
check('GLB_exact_13_roots_44_anchors',sum(n.startswith('ASSET.') for n in names)==13 and sum(n.startswith('ANCHOR.') for n in names)==44)
check('GLB_render_only_transmission_extension',set(g.get('extensionsUsed',[]))<={'KHR_materials_transmission'})
for entry in a['anchors']:
 idx,n=lookup[entry['anchor_id']];ti,tn=lookup[entry['target_object']];expected=[entry['translation_m'][0],entry['translation_m'][2],-entry['translation_m'][1]]
 check(entry['anchor_id']+'_raw_glb_coordinates',near(n.get('translation',[0,0,0]),expected) and near(tn.get('translation',[0,0,0]),expected))
 check(entry['anchor_id']+'_raw_glb_owner',parents.get(idx)==parents.get(ti) and nodes[parents[idx]]['name']=='ASSET.'+entry['asset_id'])
 check(entry['anchor_id']+'_raw_glb_target_extras',n.get('extras',{}).get('target_object')==entry['target_object'] and n.get('extras',{}).get('physical_execution_enabled') is False)
for st in stations['stations']:check(st['station_id']+'_portable_label_exists',st['scene_label']+'.portable' in lookup)
r['observations']['GLB']={'node_count':len(nodes),'mesh_count':len(g['meshes']),'scene_count':len(g['scenes']),'extensions':g.get('extensionsUsed',[]),'embedded_binary_bytes':len(chunks[1][1])}
# Independent source inspection of the review-only ledger excludes hidden device/network imports.
tree=ast.parse((P/'semantic_controls.py').read_text());imports=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
 if isinstance(n,ast.ImportFrom):imports.append(n.module)
check('semantic_ledger_imports_dataclasses_only',imports==['dataclasses'],imports)
check('semantic_ledger_no_dynamic_execution_calls',not [n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec','compile','__import__','open'}])
# Source facts versus explicitly authored geometry stay differentiated.
sp=get('specimen_geometry.json');si=next(x for x in sp['specimens'] if x['id']=='SI-STAR')
check('specimen_source_vs_nominal_dimensions',si['source_nominal_thickness_m']==.0002 and si['etch_depth_m'] is None and si['etch_profile'] is None and not sp['source_pixels_or_CAD_used'] and not si['source_geometry_reproduced'] and all(x.get('source_geometry_reproduced') is False for x in sp['specimens']))
check('metadata_copper_unknown_Si_radius_authored',m['source_known_sample_dimensions']['copper_thickness_m'] is None and m['source_known_sample_dimensions']['silicon_diameter_m'] is None and m['authored_sample_dimensions']['silicon_radius_m']==.08)
# Pairing validates exact object/anchor/asset identities, not just matching ID counts.
if T.is_dir():
 taskops={x['id']:x for x in json.loads((T/'operations.json').read_text())['operations']}
 taskplan=json.loads((T/'asset_binding_plan.json').read_text())
 taskbindings={x['operation_id']:x for x in taskplan['operation_bindings']}
 check('paired_frozen_status',taskplan['status']=='frozen_nominal_pairing')
 pins=taskplan['final_asset_hashes'];expected_pins={'geometry/midinfrared_lab.blend','geometry/midinfrared_lab.glb','asset_metadata.json','asset_inventory.json','affordances.json','operation_binding_contract.json','operation_bindings.json','specimen_geometry.json','assembly_contract.json','station_layout.json','states.json','semantic_controls.py'}
 check('paired_exact_12_core_pins',len(pins)==12 and {x['path'] for x in pins}==expected_pins)
 for pin in pins:
  valid_path=pin['path'] in expected_pins
  check('paired_pin_'+pin['path'],valid_path and (P/pin['path']).is_file() and (P/pin['path']).stat().st_size==pin['bytes'] and hashlib.sha256((P/pin['path']).read_bytes()).hexdigest()==pin['sha256'])
 snap=get('task_binding_snapshot.json');check('paired_embedded_snapshot_exact',snap['binding_plan']==taskplan)
 for src in snap['source_files']:check('paired_snapshot_source_'+src['task_file'],src['task_file'] in {'operations.json','asset_binding_plan.json'} and hashlib.sha256((T/src['task_file']).read_bytes()).hexdigest()==src['sha256'])
 check('paired_exact_22_operations',set(taskops)==set(c['operation_ids']) and set(taskbindings)==set(c['operation_ids']))
 for op in c['operations']:
  k=op['operation_id'];tb=taskbindings[k]
  check(k+'_paired_asset_sets',set(op['asset_ids'])==set(taskops[k]['asset_ids'])==set(tb['asset_ids']))
  check(k+'_paired_actual_selectors',tb['primary_target']==op['primary_target'] and tb['control_target']==op['control_target'] and tb['primary_asset_id']==op['primary_asset_id'] and set(tb['anchor_ids'])=={op['primary_anchor'],op['control_anchor']} and set(tb['root_node_ids'])=={'ASSET.'+x for x in op['asset_ids']})
 check('paired_exact_5_stations',set(x['id'] for x in json.loads((T/'station_contracts.json').read_text())['stations'])==set(c['station_ids']))
 r['observations']['paired_task_sha256']={x:hashlib.sha256((T/x).read_bytes()).hexdigest() for x in ['operations.json','asset_binding_plan.json','station_contracts.json']}
else:r['observations']['paired_task']='Not present; cross-package checks not run'
# Lossless image structure and stated render hashes; actual pixels separately inspected by reviewer.
receipt=get('review/render_receipt.json')
check('receipt_CPU_nonmeasurement_labels',receipt['device']=='CPU' and receipt['renderer']=='Blender Cycles' and not receipt['source_pixels_used'])
for e in receipt['images']:
 b=(P/e['path']).read_bytes();check(e['path']+'_render_receipt_hash',hashlib.sha256(b).hexdigest()==e['sha256']);check(e['path']+'_PNG_signature',b[:8]==b'\x89PNG\r\n\x1a\n')
 pos=8;kinds=[];crc_ok=True
 while pos<len(b):
  size=struct.unpack_from('>I',b,pos)[0];kind=b[pos+4:pos+8];payload=b[pos+8:pos+8+size];crc=struct.unpack_from('>I',b,pos+8+size)[0];crc_ok &= zlib.crc32(kind+payload)&0xffffffff==crc;kinds.append(kind.decode());pos+=size+12
 check(e['path']+'_PNG_chunks_CRC',crc_ok and pos==len(b))
 check(e['path']+'_no_private_text_chunks',not set(kinds)&{'tEXt','iTXt','zTXt'})
 check(e['path']+'_1800x1200',struct.unpack_from('>II',b,16)==(1800,1200))
# Freeze the inspected payloads without pretending a report can hash itself.
files=['geometry/midinfrared_lab.blend','geometry/midinfrared_lab.glb','geometry/build_scene.py','semantic_controls.py','affordances.json','asset_inventory.json','operation_binding_contract.json','operation_bindings.json','asset_metadata.json','assembly_contract.json','station_layout.json','states.json','specimen_geometry.json','README.md']+[e['path'] for e in receipt['images']]
r['observations']['checked_sha256']={x:hashlib.sha256((P/x).read_bytes()).hexdigest() for x in files}
r['status']='PASS' if not r['errors'] else 'FAIL';(P/'review/independent_package_audit.json').write_text(json.dumps(r,indent=2)+'\n')
print('INDEPENDENT_PACKAGE_AUDIT',r['status'],len(r['checks']),'checks',len(r['errors']),'errors')
for error in r['errors']:print(error)
if r['errors']:sys.exit(1)
