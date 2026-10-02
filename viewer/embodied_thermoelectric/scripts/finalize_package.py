"""Validate and freeze final visual-only deliverable, with hashes and scope."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import os,json,hashlib,subprocess,datetime,xml.etree.ElementTree as ET
def external_root(variable):
 value=os.environ.get(variable)
 if not value:
  raise SystemExit('Set '+variable+' to the existing external input directory. See EXTERNAL_INPUTS.md.')
 root=Path(value).expanduser().resolve()
 if not root.is_dir():
  raise SystemExit(variable+' must identify an existing directory. See EXTERNAL_INPUTS.md.')
 return root

OUT=Path(__file__).resolve().parents[1]
SRC=external_root('THERMO_SCENE')
TASK=external_root('THERMO_TASKS')
G1=external_root('G1_ASSETS')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((OUT/'frame_manifest.json').read_text());coverage=json.loads((OUT/'loop_coverage.json').read_text());frames=m['frames']
assert len(frames)==45 and all(f['rendered'] for f in frames)
state_audit=json.loads((OUT/'qa/state_audit.json').read_text());assert not state_audit['rigidbody_world'] and not state_audit['physics_executed']
source_integrity=json.loads((OUT/'qa/source_integrity.json').read_text());assert source_integrity['status']=='PASS'
xml=ET.parse(G1/'g1_with_hands.xml').getroot()
joint_ranges={j.get('name'):[float(x) for x in j.get('range','-3.14 3.14').split()] for j in xml.findall('.//body/joint')}
for f in frames:
 for j,q in f['robot_pose']['joint_angles_rad'].items():assert joint_ranges[j][0]-1e-8<=q<=joint_ranges[j][1]+1e-8,(f['id'],j,q)
assert len(coverage['reference_occurrences'])==66
for f in frames:
 for k in ['id','title','image','action','station','objects','sample_state_before','sample_state_after','evidence','authored_notes']:assert k in f,(f['id'],k)
 assert (OUT/f['image']).is_file()
 assert Image.open(OUT/f['image']).size==(1660,1000)
 assert not f['sample_representation']['old_PEM_module_duplicate_visible']
 assert not f['sample_representation']['other_branch_samples_visible']
start=frames[0]['sample_representation']['visible_instance_ids'];assert all(i.startswith('T00_RAW') for i in start)
assert [f['source_target_Th_K'] for f in frames if f['visual_kind']=='boundary']==[373,473,573,593]
assert [f['leg_index'] for f in frames if f['visual_kind']=='module_leg']==list(range(4))
# Bounded actual rendered visibility checks, distinct from physical correctness.
assert all(not any(i.startswith('T06') or i.startswith('T07') for i in f['sample_representation']['visible_instance_ids']) for f in frames if f['index']<=25)
module_frames=[f for f in frames if f['index']>=32]
assert all(f['physical_object_id']=='module.PAIRED_TWO.001' for f in module_frames)
m['coverage']['frames_rendered']=45;m['finalized']=True
ops={o['id']:o for o in json.loads((TASK/'operations.json').read_text())['operations']}
for f in frames:
 if f['visual_kind'] in ['module_leg','boundary']:
  opids=['MODULE_LEGS'] if f['visual_kind']=='module_leg' else ['PEM_BOUNDARY','PEM_CURRENT','PEM_ACQUIRE','PEM_NEXT']
  f['evidence']['operation_ids']=opids
  f['evidence']['source_refs']=sorted(set(e for k in opids for e in ops[k]['evidence_ids']))
  f['action']=' '.join(a for k in opids for a in ops[k]['actions'])
 if f['visual_kind']=='stack':f['aggregated_station_visits']=['WS_POWDER','WS_DIE']
 if f['visual_kind']=='mill_seat':
  f['title']=f['phase']+' · stage the jar at the mill handoff cradle';f['objects']=f['phase']+' jar / authored cradle'
  if 'The original mill cover/clamp motions are unresolved' not in f['authored_notes']:f['authored_notes']+=' The original mill cover/clamp motions are unresolved; this image depicts only a staged handoff to the separate proxy cradle.'
m['coverage']['primary_camera_stations']=len(set(f['station'] for f in frames))
m['coverage']['workstation_roles_including_aggregated_powder_visit']=13
m['coverage']['powder_station_scope']='Closed powder handling and transfer to die bench are aggregated into P_STACK / N_STACK; no separate WS_POWDER camera keyframe.'
m['material_identities']={'P':'MgAgSb + 0.625 wt% C18H36O2 (additive isomer unknown)','N':'Mg3.2In0.02Sb0.595Bi1.4Te0.005; Mg excess, In and Te retained','P_interfaces':'Sb','N_interfaces':'stainless steel'}
m['scientific_geometry']={'P_leg_mm':[3.3,3.3,6.6],'N_leg_mm':[2.9,2.9,6.6],'display_scale_linear':20,'P_cut_direction':'parallel to pressing axis','N_cut_direction':None,'AlN_dimensions':'authored source-asset proxy, not reported physical dimensions','Cu_topology':'authored detailed layout; series/thermal-parallel role supported','bonding_method':'unknown; no Ga-In claim for two-pair joining','interface_thickness':'unknown; visual partitions are authored'}
(OUT/'frame_manifest.json').write_text(json.dumps(m,indent=2))
subprocess.run(['python',str(OUT/'scripts/annotate_frames.py')],check=True)
trajectory={'kind':'authored static keyframe placements, not policy or executed trajectory','coordinate_system':'Blender meters, Z up','collision_or_reachability_validated':False,'continuous_motion_rendered':False,'poses':[{'frame':f['id'],'station':f['station'],'robot_pose':f['robot_pose'],'transport':f['transport']} for f in frames]}
(OUT/'trajectory.json').write_text(json.dumps(trajectory,indent=2))
lineage={'semantics':'One route, two independent parent batches, four leg children merged into one module. Geometry is illustrative; no material conversion executed.','P':{'raw_identity':m['material_identities']['P'],'chain':['raw.P','jar.P','powder.P','die.P','billet.P',['leg.P1','leg.P2']],'SPS_role':'SPS-322LX','interfaces':'Sb','leg_envelope_mm':[3.3,3.3,6.6],'cut_direction':'parallel to pressing axis'},'N':{'raw_identity':m['material_identities']['N'],'chain':['raw.N','jar.N','powder.N','die.N','billet.N',['leg.N1','leg.N2']],'SPS_role':'SPS-1080','interfaces':'stainless steel','leg_envelope_mm':[2.9,2.9,6.6],'cut_direction':None},'module':{'id':'module.PAIRED_TWO.001','parents':['leg.P1','leg.N1','leg.P2','leg.N2','AlN.support','Cu.electrodes'],'geometry_binding':'one reused assembly instance travels to PEM, data carrier and archive; original mounted PEM temporal copy remains hidden','measurement_boundaries':['B1','B2','B3','B4'],'current_points':None,'manufacturing_replicates':1,'replicate_count_status':'authored storyline count, not claimed paper replicate count','archive_status':'measurement-route illustration; no scientific measurements executed'},'remainders':{'quantity':'unknown','policy':'No invented yields, mass balance or duplicate full product. Leftover/offcut handling is an aggregated cleanup requirement; individual remnant geometry is not reconstructed.'}}
(OUT/'lineage.json').write_text(json.dumps(lineage,indent=2))
(OUT/'measurement_record_schema.json').write_text(json.dumps({'status':'schema only, zero acquired records','module_id':'module.PAIRED_TWO.001','run_id':None,'boundary_id':None,'point_id':None,'source_target_Th_K':None,'source_target_Tc_K':293,'actual_Th_K':None,'actual_Tc_K':None,'I_A':None,'V_V':None,'Qc_W':None,'raw_heat_flow_voltage':None,'raw_heat_flow_voltage_unit':None,'calibration':'unknown','timestamp':None,'vacuum':None,'P_W':None,'eta':None,'rules':['P=I*V only with compatible units and valid raw events','eta=P/(P+Qc) only if Qc in W is established','Raw mV must not silently become W','Missing or invalid attempts stay explicit','Four target boundaries are source labels, not achieved measurements']},indent=2))
# Review sheet contains every final frame, not a selection only.
font=ImageFont.truetype(os.environ.get('THERMO_FONT','DejaVuSans.ttf'),16)
im=Image.new('RGB',(2075,2466),'#0d1d2b');d=ImageDraw.Draw(im)
for j,f in enumerate(frames):
 x=(j%5)*415;y=(j//5)*274;im.paste(Image.open(OUT/f['image']).resize((415,250)),(x,y));d.text((x+8,y+253),f"{j+1:02d} {f['id']}",font=font,fill='#d8efee')
im.save(OUT/'keyframes_contact_sheet.jpg',quality=91)
# Keep the generic public player intact; refresh its portable data payload.
public_manifest=json.loads((OUT/'frame_manifest.json').read_text())
public_manifest['model_license']=(OUT/'licenses/Unitree_G1_BSD3.txt').read_text()
public_manifest['source_scene']='External input THERMO_SCENE: thermoelectric_scene_v3 (not distributed)'
for frame in public_manifest['frames']:
 frame.pop('detail_image',None)
 if 'detail_note' in frame:frame['detail_note']+=' The inspection inset is embedded in the published JPEG; raw detail PNGs are not distributed.'
(OUT/'frame_manifest.json').write_text(json.dumps(public_manifest,indent=2)+'\n')
(OUT/'manifest.js').write_text('window.EMBODIED_TASK='+json.dumps(public_manifest,ensure_ascii=True)+';\n')
receipt={'status':'FROZEN_FINAL','render_mode':'Blender 4.3.2 Cycles CPU, 32 primary samples / 24 inspection samples, denoising disabled','final_frames':45,'reference_operation_occurrences_mapped':66,'branch':'PAIRED_TWO only','loop_coverage':'Four thermal-boundary chapters, one same module; inner current grid deliberately symbolic and aggregated','source_stage_copies_visible_initially':False,'original_PEM_duplicate_visible_any_frame':False,'physics_executed':False,'rigidbody_world':False,'mujoco_model_loaded':False,'robot_policy_executed':False,'robot_execution':False,'contact_collision_or_reachability_validation':False,'chemical_processing':False,'thermal_processing':False,'electrical_processing':False,'scientific_readings_generated':False,'source_assets_duplicated':False,'robot_importer':'Corrected original XML pos/quat hierarchy plus authored joint rotations; no cached matrix_local joint bases','source_scene_sha256':sha(SRC/'assets/thermoelectric_lab_scene.blend'),'source_manifest_hashes':{p.name:sha(p) for p in [SRC/'sample_instances.json',SRC/'reuse_manifest.json',SRC/'provenance.json',SRC/'DELIVERY_RECEIPT.json']},'task_hashes':{p.name:sha(p) for p in sorted(TASK.glob('*.json'))},'g1_xml_sha256':sha(G1/'g1_with_hands.xml'),'g1_visual_mesh_hashes':{p.name:sha(p) for p in sorted((G1/'assets').glob('*.STL'))+sorted((G1/'assets').glob('*.stl'))},'license':'Unitree BSD-3-Clause text retained; first-party lab/equipment/sample proxies reused; no manufacturer CAD or paper photographs copied','rights_notice':'licenses/Unitree_G1_BSD3.txt','source_asset_retention':'Existing lab .blend and G1 STL/XML read in place. Only derived renders, new scripts, manifests and license notice written into this package.','remaining_limits':['No validated continuous carry path, hand contact or equipment interlock','Foreground station occluders are hidden in local interaction shots, complete 16-station layout in overview','Inspection insets hide robot/guide/cover/contact occluders and show the same active object','Recipe mass, material yield, tolerances, N cut direction and detailed joints remain unknown','No additional paper branches or recovered human microtrajectories claimed']}
receipt['source_gaps']={'material_recipe':'Real portion masses, yield and ratio not supplied; C18H36O2 additive isomer unknown','P_N_geometry':'Unequal source leg envelopes retained; displayed at 20x, so scenes do not validate grasping at real millimeter scale','cutting':'N direction, kerf and tolerances unknown; P parallel pressing-axis label retained','assembly':'AlN physical dimensions, detailed Cu topology, joining method and interface thickness unresolved/authored','equipment':'SPEX original approximately 7 mm vial/clamp gap retained; original lid/clamp motion not reconstructed; separate handoff cradle remains a proxy','measurement':'Current-grid values/count, calibration, real raw channels, vacuum plumbing, contact pressure, achieved temperatures and stability criteria unknown','rendered_scope':'WS_POWDER handling is aggregated into die-stack frames; continuous travel and recovery branches are not rendered'}
receipt['corrected_importer_reference_sha256']=json.loads((OUT/'external_inputs.json').read_text())['corrected_importer_reference_sha256']
receipt['frame_sha256']={f['image']:sha(OUT/f['image']) for f in frames};receipt['overview_sha256']=sha(OUT/'overview.jpg')
(OUT/'render_receipt.json').write_text(json.dumps(receipt,indent=2))
qa={'result':'PASS (visual-package checks only)','frame_count':45,'reference_occurrence_coverage':66,'all_required_fields':True,'images_1660x1000':True,'initial_state_raw_only':True,'P_N_distinct_envelopes':True,'four_leg_placement_keyframes':True,'four_boundary_frames':True,'same_module_identity':True,'original_PEM_copy_always_hidden':True,'other_branch_samples_always_hidden':True,'science_values_absent':True,'physical_execution_validated':False,'review_note':'Every frame included in contact sheet; representative raw/assembly/PEM/archive frames visually inspected separately.'}
qa['source_package_integrity']=source_integrity
qa['authored_joint_poses_within_XML_limits']=True
qa['G1_visual_mesh_count']=state_audit['robot_visual_meshes']
qa['robot_height_range_m']=[min(f['robot_bounds_world_m']['z'][1]-f['robot_bounds_world_m']['z'][0] for f in frames),max(f['robot_bounds_world_m']['z'][1]-f['robot_bounds_world_m']['z'][0] for f in frames)]
qa['robot_pixel_crops']=[{'id':f['id'],'bounds':f['robot_projected_bounds_px']} for f in frames if f['robot_projected_bounds_px']['y'][1]>801 or f['robot_projected_bounds_px']['y'][0]<-1 or f['robot_projected_bounds_px']['x'][0]<-1 or f['robot_projected_bounds_px']['x'][1]>1241]
qa['actor_inside_render_bounds']=not qa['robot_pixel_crops']
assert qa['actor_inside_render_bounds'],qa['robot_pixel_crops']
qa['visually_inspected_representative_frames']=['START','P_AR','P_MILL_SEAT','P_SPS_RELEASE','P_LEGS','PLACE_P2','PEM_MOUNT','BOUNDARY_573','ARCHIVE']
(OUT/'qa/validation_report.json').write_text(json.dumps(qa,indent=2))
# All publishable outputs and build scripts are frozen; bulky intermediate renders/logs are excluded.
files=[p for p in sorted(OUT.rglob('*')) if p.is_file() and 'raw' not in p.relative_to(OUT).parts and not p.name.endswith('.log') and p.name not in ['SHA256SUMS','DELIVERY_RECEIPT.json'] and '__pycache__' not in p.parts]
(OUT/'SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(OUT))+'\n' for p in files))
(OUT/'DELIVERY_RECEIPT.json').write_text(json.dumps({'status':'FROZEN_FINAL','branch':'PAIRED_TWO','frames':45,'sha256sums_file_sha256':sha(OUT/'SHA256SUMS'),'files_hashed':len(files),'publication':'No remote publication or upload performed','physics_executed':False},indent=2))
print('FROZEN_FINAL',len(files),'files hashed')
