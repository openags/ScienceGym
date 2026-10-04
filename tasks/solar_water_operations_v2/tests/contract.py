"""Offline design/receipt fixture. No hardware, scientific values or authenticated authority.
Actor input is events only. The caller-owned fixture context is not a secure boundary.
"""
from pathlib import Path
import copy, hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_text())
BRANCHES={b['id']:b for b in load('branches.json')['branches']}
CONTROLS={x['id']:x['cases'] for x in load('control_packages.json')['controls']}
CONFLICTS=[c['id'] for c in load('source_conflicts.json')['conflicts']]
AUTH='synthetic_fixture_authority'
WET={'WET_FRONT','TRANSFER','DARK','HORIZONTAL','VERTICAL','ANGLE','BIFACIAL','OUTDOOR','CONDENSATE'}
LIGHT={'HORIZONTAL','THERMAL_DRY','VERTICAL','ANGLE','BIFACIAL','CONDENSATE'}
ACTOR_KEYS={'event_id','job_id','phase'}
RAW_CHANNELS={
'OPTICAL_ACQUIRE':['acquisition_time_s','wavelength_um','incidence_angle_deg','measured_reflectance','measurement_convention','reference_id','uncertainty'],
'METROLOGY_SERVICE':['region_id','coordinate_frame','length_unit','instrument_record_id','surface_revision','uncertainty'],
'WET_FRONT_ACQUIRE':['acquisition_time_s','frame_id','position_mm','scale_calibration_id','initial_wetness','position_uncertainty_mm'],
'CONTACT_ACQUIRE':['acquisition_time_s','balance_mass_g','contact_phase','coupon_position_mm','reservoir_id','force_component_annotation','mass_uncertainty_g'],
'DARK_ACQUIRE':['acquisition_time_s','balance_mass_g','absorber_temperature_C','water_temperature_C','ambient_temperature_C','RH_percent','airflow_metadata','area_definition'],
'LIGHT_ACQUIRE':['acquisition_time_s','balance_mass_g','absorber_temperature_C','water_temperature_C','front_irradiance_W_m2','rear_irradiance_W_m2_if_applicable','area_definition','ambient_metadata'],
'THERMAL_ACQUIRE':['acquisition_time_s','front_temperature_C','back_temperature_C','irradiance_W_m2','placement_record','uncertainty'],
'REAR_FLUX_ACQUIRE':['acquisition_time_s','front_irradiance_W_m2','rear_irradiance_W_m2','sensor_plane','reflector_id','uncertainty'],
'WEATHER_ACQUIRE':['acquisition_time_s','ambient_temperature_C','RH_percent','wind_metadata','shading','sensor_plane','irradiance_W_m2'],
'CONDENSATE_ACQUIRE':['acquisition_time_s','reservoir_mass_g','collector_mass_g','holdup_estimate_g','leakage_annotation','separate_balance_id','uncertainty']}

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def strict_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(strict_equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
 return a==b

def closure(selected):
 if not isinstance(selected,list) or not selected or any(type(b) is not str for b in selected) or len(set(selected))!=len(selected):raise ValueError('invalid selection')
 out=[]
 def add(b):
  if b not in BRANCHES:raise ValueError('unknown or excluded branch')
  for p in BRANCHES[b]['depends_on']:add(p)
  if b not in out:out.append(b)
 for b in selected:add(b)
 return out

def identity(b,c):
 key=b+'_'+c['case_id'];bulk=c['source_constraints'].get('material')=='bulk_water' or b=='ASSEMBLE'
 return {'coupon_id':None if bulk else 'synthetic_coupon_'+key,'coupon_version':0 if bulk else 1,'parent_coupon_id':None,'fabrication_lot_id':None if bulk else 'synthetic_lot_'+key,'surface_state_revision':0 if bulk else 1,'assembly_id':'synthetic_assembly_'+key,'support_id':'synthetic_support_'+key,'aperture_id':'synthetic_aperture_'+key,'reservoir_id':'synthetic_reservoir_'+key if b in WET else None,'water_lot_id':None,'collector_id':'synthetic_collector_'+key if b=='CONDENSATE' else None}

def plan_for(b,release_inventory=None):
 out=[]
 release_inventory=release_inventory or []
 for case in CONTROLS[b]:
  ident=identity(b,case);mount=0;setup=0;cal=None;safe=False;custody='carrier';light=False;surface=ident['surface_state_revision'];history=[];water_rev=0;interlocks=False
  def add(op,detail=None):
   nonlocal mount,setup,cal,safe,custody,light,surface,water_rev,interlocks
   before=digest(history)
   if op=='VERIFY_SAFE':safe=True
   elif op=='TRANSFER_IN':
    if not safe:raise ValueError('unsafe transfer')
    custody='carrier'
   elif op=='MOUNT':
    if not safe:raise ValueError('unsafe mounting')
    mount+=1;setup+=1;cal=None;custody='fixture';safe=False
   elif op in ['REGISTER_GEOMETRY','ORIENT']:
    if not safe:raise ValueError('unsafe geometry operation')
    setup+=1;cal=None;interlocks=False
   elif op=='CALIBRATE':cal=f'synthetic_{b}_{case["case_id"]}_mount{mount}_setup{setup}'
   elif op=='CHECK_INTERLOCKS':interlocks=True
   elif op=='CONFIGURE_LIGHT':
    if not safe or cal is None:raise ValueError('unqualified light configuration')
   elif op in ['LIGHT_ACQUIRE','THERMAL_ACQUIRE','REAR_FLUX_ACQUIRE']:
    if cal is None or not interlocks:raise ValueError('unqualified illuminated acquisition')
    light=True;safe=False
   elif op=='DEENERGIZE':light=False;safe=False;interlocks=False
   elif op=='COOLDOWN':safe=False
   elif op in ['DISCONNECT','RETRIEVE']:
    if not safe or light:raise ValueError('unsafe release')
    custody='retained_carrier' if op=='DISCONNECT' else 'storage'
   elif op in ['PREPARE_CLEAN_WATER','RESET_WATER']:
    if not safe:raise ValueError('unsafe fluid handling')
    water_rev+=1;ident['water_lot_id']=f'synthetic_water_{b}_{case["case_id"]}_{water_rev}'
    history.append({'operation':op,'water_lot_id':ident['water_lot_id'],'prior_fluid_disposition':'approved_fixture_bookkeeping_only'})
   elif op=='ASSEMBLY_SERVICE':
    if not safe:raise ValueError('unsafe assembly service handoff')
    setup+=1;cal=None;history.append({'operation':op,'service_batch_received':True})
   elif op=='CLEANING_SERVICE':
    if not safe:raise ValueError('unsafe service handoff')
    ident['coupon_version']+=1;surface+=1;ident['surface_state_revision']=surface;cal=None;history.append({'operation':op,'surface_state_revision':surface})
   elif op in ['WET_FRONT_ACQUIRE','CONTACT_ACQUIRE','DARK_ACQUIRE','OPTICAL_ACQUIRE','METROLOGY_SERVICE','REAR_FLUX_ACQUIRE','WEATHER_ACQUIRE','CONDENSATE_ACQUIRE']:
    if cal is None:raise ValueError('uncalibrated acquisition')
   if op in ['LIGHT_ACQUIRE','THERMAL_ACQUIRE','WET_FRONT_ACQUIRE','CONTACT_ACQUIRE','DARK_ACQUIRE']:
    history.append({'operation':op,'setup_revision':setup,'water_lot_id':ident['water_lot_id'],'surface_state_revision':surface})
   payload={'branch_id':b,'case_id':case['case_id'],'operation_id':op,**copy.deepcopy(ident),'station_id':BRANCHES[b]['station_id'],'mount_revision':mount,'setup_revision':setup,'calibration_id':cal,'independent_safe_state':safe,'light_active':light,'interlocks_current':interlocks,'custody':custody,'control':copy.deepcopy(case['source_constraints']),'control_provenance':copy.deepcopy(case['field_provenance']),'history_before':before,'history_after':digest(history),'ordinal_time':len(out),'elapsed_physical_seconds':None,'scientific_measurement_values':None,'sample_kind':'synthetic_bookkeeping_only','detail':detail or {}}
   if op in RAW_CHANNELS:payload['raw_columns']=RAW_CHANNELS[op][:]
   if op in ['ARCHIVE','CLEAN_STORE']:payload['material_disposition']={'coupon':ident['coupon_id'],'coupon_version':ident['coupon_version'],'assembly':ident['assembly_id'],'final_water':ident['water_lot_id'],'history_preserved':True,'destination':'qualified_storage_or_approved_waste'}
   if op in ['ARCHIVE','CLEAN_STORE'] and b in {'RECEIPT','ASSEMBLE'}:payload['service_material_dispositions']=[{'coupon_id':x['coupon_id'],'coupon_version':x['coupon_version'],'assembly_id':x['assembly_id'],'target_job_id':x['target_job_id'],'disposition':'registered_service_release_for_named_target'} for x in release_inventory if b=='RECEIPT' or x['assembly_form']==case['case_id']]
   out.append({'phase':f'{len(out):04d}:{case["case_id"]}:{op}','operation_id':op,'payload':payload})
  for op in ['RECEIVE','CHECK_INPUT','VERIFY_SAFE','TRANSFER_IN','MOUNT','VERIFY_SAFE','REGISTER_GEOMETRY','CALIBRATE']:add(op)
  if b=='RECEIPT':add('SERVICE_RECEIPT',{'fabrication_details':'closed_service_only','chemical_or_biological_operations':False,'released_input_inventory':copy.deepcopy(release_inventory)})
  elif b=='ASSEMBLE':
   add('ASSEMBLY_SERVICE',{'mounted_object_role':'independent_batch_carrier_not_downstream_device','qualified_geometry_receipt':True,'input_coupon_ids':[x['coupon_id'] for x in release_inventory if x['assembly_form']==case['case_id']],'released_assemblies':[copy.deepcopy(x) for x in release_inventory if x['assembly_form']==case['case_id']]});add('REGISTER_GEOMETRY');add('CALIBRATE')
  elif b=='OPTICAL':add('OPTICAL_ACQUIRE')
  elif b=='TOPOGRAPHY':add('METROLOGY_SERVICE')
  elif b=='REUSE':
   add('CLEANING_SERVICE',{'known_benign_material':True,'biological_material':False,'open_recipe_supplied':False});add('REGISTER_GEOMETRY');add('CALIBRATE');add('METROLOGY_SERVICE',{'post_cleaning_state_check':True,'decontamination_claim':False})
  else:
   if b in WET:add('PREPARE_CLEAN_WATER');add('REGISTER_INITIAL_WETNESS')
   if b=='WET_FRONT':add('WET_FRONT_ACQUIRE')
   elif b=='TRANSFER':add('CONTACT_ACQUIRE',{'force_components_separate':True})
   elif b=='DARK':add('DARK_ACQUIRE')
   elif b=='OUTDOOR':
    add('ORIENT');add('REGISTER_GEOMETRY');add('CALIBRATE');add('DARK_ACQUIRE');add('RESET_WATER');add('CHECK_INTERLOCKS');add('WEATHER_ACQUIRE');add('LIGHT_ACQUIRE',{'illumination':'natural sunlight; qualified shield and station boundaries'})
   else:
    if b=='ANGLE':add('ORIENT');add('REGISTER_GEOMETRY');add('CALIBRATE')
    if b in WET:add('DARK_ACQUIRE');add('RESET_WATER')
    add('CONFIGURE_LIGHT');add('CHECK_INTERLOCKS');add('THERMAL_ACQUIRE' if b=='THERMAL_DRY' else 'LIGHT_ACQUIRE')
    if b=='BIFACIAL':add('REAR_FLUX_ACQUIRE',{'binding':'current illumination, mount and setup; not a dark reading'})
    if b=='CONDENSATE':add('CONDENSATE_ACQUIRE',{'mass_loss_is_not_collection':True})
  for op in ['DEENERGIZE','COOLDOWN','VERIFY_SAFE','READOUT','DISCONNECT','RETRIEVE','INSPECT','ARCHIVE','CLEAN_STORE']:add(op)
 return out

def fixture(selected_branches=None,episode_id='synthetic_solar_001'):
 if type(episode_id) is not str or not episode_id:raise ValueError('invalid episode identity')
 episode_token=digest(episode_id)[:16]
 selected=selected_branches if selected_branches is not None else list(BRANCHES)
 ids=closure(selected)
 ctx={'episode_id':episode_id,'mode':'synthetic_contract_only','production_authority':False,'full_paper_complete':False,'scientific_replication':False,'biological_operations_included':False,'selected_branches':copy.deepcopy(selected),'source_conflicts_preserved':CONFLICTS[:],'conflict_dispositions':{},'cards':{},'jobs':{},'observations':{},'record_store':{},'input_inventory':{},'service_scope':'bounded_nonbiological'}
 events=[]
 inventories={b:[identity(b,c) for c in CONTROLS[b]] for b in ids}
 assembly_release=[{'target_job_id':'job_'+b,'assembly_form':'vertical' if b in {'VERTICAL','ANGLE','BIFACIAL'} or (b=='OUTDOOR' and 'tilted' in x['assembly_id']) else 'horizontal',**copy.deepcopy(x)} for b in ids if 'ASSEMBLE' in BRANCHES[b]['depends_on'] for x in inventories[b]]
 if 'ASSEMBLE' in ids:
  inventories['ASSEMBLE']=[{k:copy.deepcopy(v) for k,v in x.items() if k not in {'target_job_id','assembly_form'}} for x in assembly_release]
  if not inventories['ASSEMBLE']:
   inventories['ASSEMBLE']=[{**identity('ASSEMBLE',c),'coupon_id':'synthetic_standalone_assembly_input_'+c['case_id'],'coupon_version':1,'surface_state_revision':1,'fabrication_lot_id':'synthetic_standalone_lot_'+c['case_id']} for c in CONTROLS['ASSEMBLE']]
   assembly_release=[{'target_job_id':'job_ASSEMBLE','assembly_form':c['case_id'],**copy.deepcopy(x)} for c,x in zip(CONTROLS['ASSEMBLE'],inventories['ASSEMBLE'])]
 receipt_release=[{'target_job_id':'job_'+b,**copy.deepcopy(x)} for b in ids if 'RECEIPT' in BRANCHES[b]['depends_on'] for x in inventories[b]]
 releases={'RECEIPT':receipt_release,'ASSEMBLE':assembly_release}
 ctx['release_inventories']={'job_'+b:copy.deepcopy(releases.get(b,[])) for b in ids}
 for b in ids:
  for u in BRANCHES[b]['unknown_parameter_ids']:ctx['cards'][u]={'id':u,'authority':AUTH,'revision':'synthetic_v1','valid_for':'synthetic_fixture_only','production_qualified':False}
  for c in BRANCHES[b]['conflict_ids']:ctx['conflict_dispositions'][c]={'id':c,'source_resolved':False,'qualification':'synthetic_fixture_only','decision':'Preserve conflict; no source correction or production interpretation'}
  plan=plan_for(b,releases.get(b,[]));job='job_'+b
  inventory=inventories[b]
  ctx['input_inventory'][job]=inventory
  parents=[{'job_id':'job_'+p,'release_id':'release_'+p,'inventory_binding':digest(inventory),'parent_release_inventory_hash':digest(releases.get(p,[])),'released_target_records':[copy.deepcopy(x) for x in releases.get(p,[]) if x['target_job_id']==job],'scope':'qualified_input_handoff_not_historical_reproduction'} for p in BRANCHES[b]['depends_on']]
  ctx['jobs'][job]={'branch_id':b,'phase_count':len(plan),'parents':parents,'release_id':'release_'+b,'input_inventory_hash':digest(inventory),'release_covers_registered_inputs':True}
  for phase in plan:
   n=len(events);eid=f'event_{episode_token}_{n:06d}';rid='record_'+eid
   phase['payload']['episode_id']=episode_id
   phase['payload']['attempt_id']='synthetic_attempt_1'
   ctx['record_store'][rid]=copy.deepcopy(phase['payload'])
   ctx['observations'][eid]={'event_id':eid,'episode_id':episode_id,'job_id':job,'phase':phase['phase'],'authority':AUTH,'raw_record_id':rid,'record_hash':digest(phase['payload']),'sample_kind':'synthetic_bookkeeping_only'}
   events.append({'event_id':eid,'job_id':job,'phase':phase['phase']})
 return ctx,events

def validate(context,actor_events):
 if not isinstance(context,dict) or not isinstance(actor_events,list):raise ValueError('wrong input types')
 if context.get('mode')!='synthetic_contract_only' or context.get('production_authority') is not False:raise ValueError('not production authority')
 try:canonical,expected=fixture(context['selected_branches'],context['episode_id'])
 except (KeyError,TypeError,ValueError) as e:raise ValueError('invalid fixture context') from e
 if not strict_equal(context,canonical):raise ValueError('untrusted, stale, changed or noncanonical fixture evidence')
 if len(actor_events)!=len(expected):raise ValueError('missing or extra event')
 seen=set();completed=set()
 for e,want in zip(actor_events,expected):
  if not isinstance(e,dict) or set(e)!=ACTOR_KEYS:raise ValueError('actor cannot supply evidence or results')
  if not strict_equal(e,want):raise ValueError('wrong event, replay, ordering or phase')
  if e['event_id'] in seen:raise ValueError('replay')
  seen.add(e['event_id']);job=context['jobs'][e['job_id']]
  for parent in job['parents']:
   if parent['job_id'] not in completed:raise ValueError('unreleased parent')
  obs=context['observations'][e['event_id']];payload=context['record_store'][obs['raw_record_id']]
  if obs['record_hash']!=digest(payload):raise ValueError('record integrity failure')
  if payload['scientific_measurement_values'] is not None:raise ValueError('invented scientific data')
  if payload['operation_id']=='CLEAN_STORE' and e['phase']==expected[[x['job_id'] for x in expected].index(e['job_id'])+job['phase_count']-1]['phase']:completed.add(e['job_id'])
 return {'status':'passed','scope':'synthetic_contract_only','jobs':len(context['jobs']),'events':len(actor_events),'full_paper_complete':False,'physical_execution_performed':False,'physics_simulation_performed':False,'scientific_replication':False}
