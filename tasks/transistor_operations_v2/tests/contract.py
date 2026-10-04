"""Offline synthetic schedule/receipt validator. No scientific model or hardware adapter.

The caller-owned context is a test fixture, not an authenticated authority. Only
actor_events are actor inputs. Never use this code to authorize real equipment.
"""
from pathlib import Path
import copy, hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
def load(name): return json.loads((ROOT/name).read_text())
BRANCHES={b['id']:b for b in load('branches.json')['branches']}
CONTROLS={c['id']:c['source_constraints'] for c in load('control_packages.json')['controls']}
CONFLICTS=[c['id'] for c in load('source_conflicts.json')['conflicts']]
ACTOR_KEYS={'event_id','job_id','phase'}
BASE_CARDS={'U_AUTHORITY','U_CUSTODY','U_ROBOT','U_CLEANUP'}
AUTH='synthetic_fixture_authority'

def digest(obj):
 return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def strict_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(strict_equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
 return a==b

def specimen_for(b,case=None):
 if b in ['PREP','STACK']:return 'synthetic_shared_substrate'
 if b=='HIGHK' and case:return 'synthetic_HIGHK_'+case+'_specimen'
 if b=='STRUCTURAL' and case:return 'synthetic_'+case+'_parent_coupon'
 return 'synthetic_'+b+'_specimen'

def material_inventory(b):
 if b=='STRUCTURAL':return [{'input_id':'synthetic_'+t+'_parent_coupon','input_disposition':'consumed_by_section_service','output_id':'synthetic_'+t+'_section','output_disposition':'retrieved_inspected_stored'} for t in ['SEM','TEM','EDX']]
 if b=='HIGHK':return [{'input_id':specimen_for(b,m),'input_disposition':'modified_by_own_dielectric_service','output_id':specimen_for(b,m),'output_disposition':'retrieved_inspected_stored'} for m in ['HfO2','Al2O3']]
 return [{'input_id':specimen_for(b),'input_disposition':'retained_with_route_history','output_id':specimen_for(b),'output_disposition':'retrieved_inspected_stored'}]

def parent_bindings(b):
 return [{'branch_id':'PREP','specimen_id':'synthetic_shared_substrate','released_specimen_version':2}] if b=='STACK' else []

def closure(selected):
 if not isinstance(selected,list) or not selected or len(set(selected))!=len(selected):raise ValueError('invalid selected branches')
 out=[]
 def add(b):
  if b not in BRANCHES:raise ValueError('unknown branch')
  for dep in BRANCHES[b]['depends_on']:add(dep)
  if b not in out:out.append(b)
 for b in selected:add(b)
 return out

def cases_for(b,buffer_variant_nm=50):
 def c(i,**x):return {'case_id':str(i),**x}
 if b=='PREP':return [c('substrate',sequence=CONTROLS[b]['sequence'],minutes_each=5)]
 if b=='STACK':
  return [c('layer_'+str(x['index']),layer_index=x['index'],role=x['role'],material=x['material'],thickness=x['source_thickness'] if x['role']!='interstack_buffer' else buffer_variant_nm,unit=x['unit'],stack=x['stack']) for x in load('layer_contract.json')['layers']]
 if b=='OVERLAP':return [c(a,architecture=a,recipe_source_complete=False) for a in ['underlap','overlap_control']]
 if b=='HIGHK':return [c(m,material=m,source_ALD_C=250 if m=='HfO2' else None) for m in ['HfO2','Al2O3']]
 if b=='CROSSBAR':return [c(str(t),thickness_nm=t,source_conditions=CONTROLS[b]['source_characterization_pairs'][i]) for i,t in enumerate([10,25,50])]
 if b=='GATE_LEAKAGE':return [c(f'{t}_{r}',gate_nm=t,region=r,terminals=ts,contacts_present=False,source_devices_per_region=50,fixture_devices=1) for t in [100,60,20] for r,ts in CONTROLS[b]['regions'].items()]
 if b=='STRUCTURAL':return [c(t,technique=t,parent_coupon='synthetic_'+t+'_parent_coupon',daughter='synthetic_'+t+'_section') for t in ['SEM','TEM','EDX']]
 if b=='SURFACE':return [c(f'S{s}_{r}',stack=s,layer_role=r,metric='RMS' if r not in ['BG_bump','TG_bump'] else 'corner_bump') for s in range(1,11) for r in ['BG','BG_dielectric','channel','TG_dielectric','TG','buffer','BG_bump','TG_bump']]
 if b=='PACKAGE':return [c(f'S{s}_{t}',stack=s,terminal=t,wire=f'wire_{s}_{t}',first_end=f'chip_S{s}_{t}',second_end=f'PCB_S{s}_{t}') for s in range(1,11) for t in ['BG','TG','source','drain']]
 if b in ['BASELINE','MOSCAP']:return [c(f'{a}_{s}',architecture=a,stack=s,cohort='baseline_12_per_stack' if b=='BASELINE' else 'MOSCAP_separate',fixture_devices=1) for a in ['BG','TG','DG'] for s in range(1,11)]
 if b in ['DUAL_TRACE','POSITIVE_STRESS']:return [c(a,architecture=a,cohort=b+'_'+a+'_100',source_devices=100,fixture_devices=1) for a in ['BG','TG','DG']]
 if b=='LONG_TERM':return [c(f'day_{d}_{a}',day=d,architecture=a,device_id='synthetic_longterm_'+a,source_devices=50,allocation='qualified_fixture_only_not_source_resolution',cohort='long_term_separate',fixture_devices=1) for d in range(0,201,10) for a in ['BG','TG','DG']]
 if b in ['NBS','NBTS']:return [c(f'S{s}',stack=s,architecture='DG',gate_V=-10,drain_V=5,temperature_C=80 if b=='NBTS' else None) for s in range(1,11)]
 if b=='THERMAL':return [c(f'S{s}',stack=s,table_temperatures_C=[25,50,75,100],hold_s=60,cooldown_s=21600) for s in range(1,11)]
 if b=='SMALL':return [c(a,architecture=a,W_um=1,Lch_nm=500,Lg_nm=100,ten_stack_claim=False) for a in ['BG','TG','DG']]
 if b=='MATERIAL':return [c(m,material=m,dielectric_nm=25) for m in ['Al2O3','parylene-C']]
 if b=='COUPLING':return [c(f'{t}_{i}',buffer_nm=t,interpretation='section7_reviewed_for_fixture_only',coupling_case=i,**v) for t in [25,50] for i,v in CONTROLS[b]['section7_cases'].items()]
 if b=='PAIRS':return [c(f'D{d}_L{l}',driver=d,loads=[l],netlist_id='ORDINARY_INVERTER_FIG4',VDD_V=15) for d in range(1,11) for l in range(1,11) if d!=l]
 if b=='PARALLEL':return [c(f'loads_{n}',driver=1,loads=list(range(2,n+2)),load_membership_origin='authored_fixture_card',netlist_id='PARALLEL_INVERTER_S30',VDD_V=15) for n in range(1,10)]
 if b=='DG_TUNE':return [c(f'S{s}_TG{v}',stack=s,TG_V=v,BG_range_V=[-10,15],VDS_V=5) for s in range(1,11) for v in [10,5,0,-5,-10]]
 if b=='INV_TUNE':return [c(f'TG1_{a}_TG2_{z}',driver=1,loads=[2],TG1_V=a,TG2_V=z,netlist_id='INDEPENDENT_INVERTER_S31',VDD_V=15) for a in [10,5,0,-5,-10] for z in [10,5,0,-5,-10]]
 raise ValueError('unhandled branch')

ACTIVE={'ACQUIRE','BASELINE_ACQUIRE','POST_ACQUIRE','TRANSFER','OUTPUT','LEAKAGE','CV_ACQUIRE','FORWARD','REVERSE','STRESS_SERVICE','TRANSIENT_READOUT','VIRGIN','PERTURB_POSITIVE','PERTURB_NEGATIVE','VTC','SUPPLY_CURRENT'}
ANALYSIS_ONLY={'COMPUTE_MOBILITY','COMPUTE_SS','COMPUTE_RATIO','COMPUTE_GAIN'}

def plan_for(b,buffer_variant_nm=50):
 """Derive explicit safe physical boundaries and source-control inventory."""
 out=[];station='storage' if b in ['HIGHK','THERMAL','LONG_TERM','STRUCTURAL'] else BRANCHES[b]['station_id'];version=2 if b=='STACK' else 1;mount=0;net=0;elapsed=0;safe=False;custody='carrier';history=[];case=None;ctrl={};specimen=specimen_for(b);parent_specimen=None
 def add(op,extra=None,seconds=0):
  nonlocal elapsed,safe,custody,version,mount,net,station,specimen,parent_specimen
  before=list(history);elapsed+=seconds
  if op=='MOUNT':mount+=1;custody='fixture';safe=False
  elif op=='VERIFY_SAFE_ZERO':safe=True
  elif op=='CONFIGURE':net+=1
  elif op in ACTIVE or op=='DEENERGIZE':safe=False
  elif op in ['DISCONNECT','REMOVE_HOTPLATE']:custody='retained_holder'
  elif op in ['RETRIEVE','RETURN_STORAGE','CLEAN_STORE']:custody='storage'
  elif op=='TRANSFER_IN':custody='carrier'
  elif op in ['CLEAN_SERVICE','LAYER_SERVICE','DIELECTRIC_SERVICE','SECTION_SERVICE','ATTACH_CHIP','BOND_SERVICE']:version+=1
  if op=='SECTION_SERVICE':parent_specimen=ctrl['parent_coupon'];specimen=ctrl['daughter']
  if op in ['STRESS_SERVICE','THERMAL_SERVICE']:
   history.append({'phase_index':len(out),'case_id':case,'operation':op,'seconds':seconds,'condition':extra or {}})
  payload={'specimen_id':specimen,'parent_specimen_id':parent_specimen,'operation':op,'case_id':case,'control':copy.deepcopy(ctrl),'detail':copy.deepcopy(extra or {}),'station':station,'specimen_version':version,'mount_revision':mount,'netlist_revision':net,'calibration_id':f'synthetic_{station}_mount{mount}_cal','elapsed_s':elapsed,'duration_s':seconds,'independent_safe_zero':safe,'custody':custody,'history_before':digest(before),'history_after':digest(history),'exposure_count':len(history),'sample_kind':'synthetic_bookkeeping_only','scientific_measurement_values':None}
  if op in ['ARCHIVE','CLEAN_STORE']:payload['material_dispositions']=material_inventory(b)
  if op in ACTIVE:payload['raw_columns']=['condition_id','synthetic_record_marker']
  out.append({'phase':f'{len(out):04d}:{op}','operation_id':op,'case_id':case,'payload':payload})
 def safe_release():
  add('DEENERGIZE');add('VERIFY_SAFE_ZERO');add('DISCONNECT')
 def acquire(op,extra=None,seconds=0):add(op,extra,seconds)
 def configure():add('CONFIGURE',{'netlist_review_current':True});add('CONTINUITY_CHECK',{'netlist_revision':net})
 for op in ['RECEIVE','VERIFY_INPUT','VERIFY_SAFE_ZERO']:add(op)
 if b not in ['HIGHK','THERMAL','LONG_TERM','STRUCTURAL']:
  for op in ['TRANSFER_IN','MOUNT','VERIFY_SAFE_ZERO']:add(op)
 if b=='PACKAGE':add('ATTACH_CHIP',{'qualified_attachment':True})
 for row in cases_for(b,buffer_variant_nm):
  case=row['case_id'];ctrl=copy.deepcopy(row)
  if b in ['HIGHK','STRUCTURAL']:specimen=specimen_for(b,case);version=1;parent_specimen=None
  if b=='PREP':add('CLEAN_SERVICE',{'qualified_recipe_only':True},900)
  elif b=='STACK':
   add('LAYER_SERVICE',{'prior_layer':row['layer_index']-1,'layer_index':row['layer_index'],'service':'certified_input' if row['layer_index']<=2 else 'closed_deposition_patterning'})
  elif b=='HIGHK':
   station='electrical';add('VERIFY_INPUT');add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');configure();acquire('BASELINE_ACQUIRE');safe_release();add('RETRIEVE')
   station='fabrication';add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');add('DIELECTRIC_SERVICE',{'material':row['material']});add('VERIFY_SAFE_ZERO');add('DISCONNECT');add('RETRIEVE')
   station='electrical';add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');configure();acquire('POST_ACQUIRE');safe_release();add('RETRIEVE');add('INSPECT')
  elif b=='STRUCTURAL':
   station='metrology';add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');add('SECTION_SERVICE',{'destructive':True,'parent_consumed':row['parent_coupon']});add('IMAGE_SERVICE',{'daughter_id':row['daughter'],'technique':row['technique']});add('VERIFY_SAFE_ZERO');add('DISCONNECT');add('RETRIEVE');add('INSPECT',{'daughter_id':row['daughter'],'parent_status':'consumed'})
  elif b=='SURFACE':add('REGISTER_REGION');add('IMAGE_SERVICE',{'metric':row['metric']})
  elif b=='PACKAGE':add('BOND_SERVICE',{'first_end':row['first_end'],'second_end':row['second_end']});add('INSPECT_BONDS',{'wire':row['wire'],'qualified_acceptance':True});add('CONTINUITY_CHECK')
  elif b=='LONG_TERM':
   station='storage_electrical'
   # The fixture's virtual clock does not claim wall-clock aging.
   delta=row['day']*86400-elapsed
   add('CUSTODY_CHECK',{'target_day':row['day'],'storage_history_complete':True},max(0,delta))
   add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');configure();acquire('TRANSFER');safe_release();add('RETURN_STORAGE',{'storage_card':'synthetic_storage_v1'})
  elif b=='THERMAL':
   station='thermal_electrical'
   add('TRANSFER_IN');add('MOUNT');add('VERIFY_SAFE_ZERO');configure()
   for temp in [25,50,75,100]:
    add('THERMAL_SERVICE',{'table_C':temp,'device_C':'qualified_separate_readback','qualified_stabilization':True},60);acquire('TRANSFER',{'table_C':temp});add('DEENERGIZE');add('VERIFY_SAFE_ZERO')
   add('DISCONNECT');add('REMOVE_HOTPLATE',{'off_hotplate':True});add('COOLDOWN',{'off_hotplate':True,'next_stack':row['stack']+1 if row['stack']<10 else None},21600)
  elif b in ['NBS','NBTS']:
   configure();acquire('TRANSFER',{'stress_elapsed_s':0});add('DEENERGIZE');add('VERIFY_SAFE_ZERO')
   if b=='NBTS':add('THERMAL_SERVICE',{'table_C':80,'qualified_stabilization':True})
   for t in range(500,4001,500):
    acquire('STRESS_SERVICE',{'stress_elapsed_s':t,'gate_V':-10,'drain_V':5},500);acquire('TRANSFER',{'stress_elapsed_s':t});add('DEENERGIZE');add('VERIFY_SAFE_ZERO')
  else:
   configure()
   ops={'OVERLAP':['ACQUIRE'],'CROSSBAR':['ACQUIRE'],'GATE_LEAKAGE':['ACQUIRE'],'BASELINE':['TRANSFER','OUTPUT','LEAKAGE'],'MOSCAP':['CV_ACQUIRE'],'DUAL_TRACE':['FORWARD','REVERSE'],'POSITIVE_STRESS':['STRESS_SERVICE','TRANSIENT_READOUT'],'SMALL':['TRANSFER','OUTPUT'],'MATERIAL':['TRANSFER'],'COUPLING':['VIRGIN','PERTURB_POSITIVE','PERTURB_NEGATIVE'],'PAIRS':['VTC','SUPPLY_CURRENT'],'PARALLEL':['VTC','SUPPLY_CURRENT'],'DG_TUNE':['TRANSFER'],'INV_TUNE':['VTC','SUPPLY_CURRENT']}[b]
   for op in ops:
    sec=10000 if b=='POSITIVE_STRESS' and op=='STRESS_SERVICE' else 0
    detail={'gate_V':5,'drain_V':5} if b=='POSITIVE_STRESS' else {}
    if b=='COUPLING':detail={'perturbation_V':{'VIRGIN':None,'PERTURB_POSITIVE':10,'PERTURB_NEGATIVE':-10}[op],'order_origin':'authored_qualified_fixture_not_source'}
    acquire(op,detail,sec)
   add('DEENERGIZE');add('VERIFY_SAFE_ZERO')
 case=None;ctrl={}
 add('READOUT')
 if custody=='fixture':safe_release()
 else:add('VERIFY_SAFE_ZERO')
 if custody!='storage':add('RETRIEVE')
 for op in ['INSPECT','ARCHIVE','CLEAN_STORE']:add(op)
 return out

def qualified_cards(ids):
 cards={}
 for b in ids:
  for u in BRANCHES[b]['unknown_parameter_ids']:
   cards[u]={'id':u,'revision':'synthetic_v1','authority':AUTH,'qualified_for_fixture_only':True,'valid':True}
 return cards

def fixture(selected_branches=None,buffer_variant_nm=50,episode_id='synthetic_episode_001'):
 selected=selected_branches or ['PAIRS'];ids=closure(selected)
 if buffer_variant_nm not in [25,50]:raise ValueError('invalid buffer variant')
 ctx={'episode_id':episode_id,'mode':'synthetic_contract_only','production_authority':False,'whole_historical_route_complete':False,'scientific_replication':False,'numerical_reproduction':False,'selected_branches':selected,'buffer_variant_nm':buffer_variant_nm,'source_conflicts_preserved':CONFLICTS[:],'cards':qualified_cards(ids),'conflict_dispositions':{},'jobs':{},'observations':{},'record_store':{}}
 for c in {c for b in ids for c in BRANCHES[b]['conflict_ids']}:
  ctx['conflict_dispositions'][c]={'id':c,'source_resolved':False,'authority':AUTH,'scope':'synthetic_fixture_only','reviewed':True,'handling':'Preserve all evidence; qualification is not author clarification or silent source correction'}
 events=[]
 for b in ids:
  plan=plan_for(b,buffer_variant_nm)
  ctx['jobs'][b]={'job_id':b,'branch_id':b,'episode_id':episode_id,'attempt_id':'synthetic_attempt_1','specimen_id':specimen_for(b),'parent_material_bindings':parent_bindings(b),'material_inventory':material_inventory(b),'carrier_id':'synthetic_'+b+'_carrier','cohort_id':'synthetic_'+b+'_cohort','parents':BRANCHES[b]['depends_on'],'control_case_ids':[c['case_id'] for c in cases_for(b,buffer_variant_nm)],'phase_ids':[p['phase'] for p in plan],'schedule_origin':'authored_synthetic_fixture','full_source_population':False,'source_conditions_claimed_executable':False}
  for p in plan:
   eid='EV'+str(len(events)+1);rid=f'synthetic://{episode_id}/{b}/{p["phase"]}'
   data={'episode_id':episode_id,'job_id':b,'attempt_id':'synthetic_attempt_1','specimen_id':p['payload']['specimen_id'],'payload':copy.deepcopy(p['payload'])}
   ctx['record_store'][rid]=data
   ctx['observations'][eid]={'event_id':eid,'episode_id':episode_id,'job_id':b,'phase':p['phase'],'operation_id':p['operation_id'],'case_id':p['case_id'],'attempt_id':'synthetic_attempt_1','specimen_id':p['payload']['specimen_id'],'carrier_id':ctx['jobs'][b]['carrier_id'],'cohort_id':ctx['jobs'][b]['cohort_id'],'authority':AUTH,'source_kind':'synthetic_fixture','record_id':rid,'record_hash':digest(data),'qualified':True,'accepted':True,'calibration_valid':True,'damage_state':'qualified_route_specific','readout_complete':p['operation_id']=='READOUT','archive_complete':p['operation_id']=='ARCHIVE','cleanup_complete':p['operation_id']=='CLEAN_STORE'}
   events.append({'event_id':eid,'job_id':b,'phase':p['phase']})
 return ctx,events

def _validate(ctx,events):
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 if not isinstance(ctx,dict) or not isinstance(events,list):return ['invalid outer shape']
 expected_ctx={'episode_id','mode','production_authority','whole_historical_route_complete','scientific_replication','numerical_reproduction','selected_branches','buffer_variant_nm','source_conflicts_preserved','cards','conflict_dispositions','jobs','observations','record_store'}
 check(set(ctx)==expected_ctx,'unknown or missing context fields')
 eid=ctx.get('episode_id');check(isinstance(eid,str) and eid.startswith('synthetic_episode_'),'invalid synthetic episode')
 check(ctx.get('mode')=='synthetic_contract_only','wrong mode')
 for flag in ['production_authority','whole_historical_route_complete','scientific_replication','numerical_reproduction']:check(ctx.get(flag) is False,'unsupported claim '+flag)
 ids=closure(ctx.get('selected_branches'));variant=ctx.get('buffer_variant_nm')
 check(type(variant) is int and variant in [25,50],'unqualified buffer variant')
 check(strict_equal(ctx.get('source_conflicts_preserved'),CONFLICTS),'omitted or corrected source conflict')
 check(strict_equal(ctx.get('cards'),qualified_cards(ids)),'missing, stale or unqualified card')
 needed={c for b in ids for c in BRANCHES[b]['conflict_ids']}
 dispositions=ctx.get('conflict_dispositions',{})
 check(set(dispositions)==needed,'missing or extra source qualification gate')
 for c in needed:
  check(strict_equal(dispositions.get(c),{'id':c,'source_resolved':False,'authority':AUTH,'scope':'synthetic_fixture_only','reviewed':True,'handling':'Preserve all evidence; qualification is not author clarification or silent source correction'}),'invalid conflict disposition '+c)
 jobs=ctx.get('jobs',{});obs=ctx.get('observations',{});records=ctx.get('record_store',{})
 check(set(jobs)==set(ids),'dependency closure mismatch')
 expected=[]
 for b in ids:
  job={'job_id':b,'branch_id':b,'episode_id':eid,'attempt_id':'synthetic_attempt_1','specimen_id':specimen_for(b),'parent_material_bindings':parent_bindings(b),'material_inventory':material_inventory(b),'carrier_id':'synthetic_'+b+'_carrier','cohort_id':'synthetic_'+b+'_cohort','parents':BRANCHES[b]['depends_on'],'control_case_ids':[c['case_id'] for c in cases_for(b,variant)],'phase_ids':[p['phase'] for p in plan_for(b,variant)],'schedule_origin':'authored_synthetic_fixture','full_source_population':False,'source_conditions_claimed_executable':False}
  check(strict_equal(jobs.get(b),job),'job schedule, cohort or lineage changed '+b)
  expected += [(b,p) for p in plan_for(b,variant)]
 check(len(events)==len(expected),'incomplete or extra actor route')
 check(len(obs)==len(expected) and len(records)==len(expected),'missing or extra independent receipts/records')
 seen=set();used_records=set();completed=set();last_state={};last_cal={};readout=set();archived=set()
 expected_obs_keys={'event_id','episode_id','job_id','phase','operation_id','case_id','attempt_id','specimen_id','carrier_id','cohort_id','authority','source_kind','record_id','record_hash','qualified','accepted','calibration_valid','damage_state','readout_complete','archive_complete','cleanup_complete'}
 for n,e in enumerate(events):
  if not isinstance(e,dict):errors.append('malformed actor event');continue
  check(set(e)==ACTOR_KEYS,'actor may not supply evidence or success')
  if n>=len(expected):continue
  b,p=expected[n];event_id=e.get('event_id');op=p['operation_id']
  check(isinstance(event_id,str) and event_id not in seen,'replayed/invalid event id');seen.add(event_id)
  check(e.get('job_id')==b and e.get('phase')==p['phase'],'wrong branch, case or operation order')
  o=obs.get(event_id)
  if not isinstance(o,dict):errors.append('missing independent observation');continue
  check(set(o)==expected_obs_keys,'unknown or missing observation fields')
  expected_binding={'event_id':event_id,'episode_id':eid,'job_id':b,'phase':p['phase'],'operation_id':op,'case_id':p['case_id'],'attempt_id':'synthetic_attempt_1','specimen_id':p['payload']['specimen_id'],'carrier_id':'synthetic_'+b+'_carrier','cohort_id':'synthetic_'+b+'_cohort','authority':AUTH,'source_kind':'synthetic_fixture'}
  for k,v in expected_binding.items():check(strict_equal(o.get(k),v),'observation binding mismatch '+k)
  for flag in ['qualified','accepted','calibration_valid']:check(o.get(flag) is True,'invalid receipt '+flag)
  check(o.get('damage_state')=='qualified_route_specific','damage/coupon status changed')
  rid=o.get('record_id');data=records.get(rid)
  check(isinstance(rid,str) and rid not in used_records,'replayed/missing raw record');used_records.add(rid)
  expected_rid=f'synthetic://{eid}/{b}/{p["phase"]}'
  check(rid==expected_rid,'record identity relabeled')
  if not isinstance(data,dict):errors.append('missing record payload');continue
  check(set(data)=={'episode_id','job_id','attempt_id','specimen_id','payload'},'unknown record fields')
  check(data.get('episode_id')==eid and data.get('job_id')==b and data.get('attempt_id')=='synthetic_attempt_1' and strict_equal(data.get('specimen_id'),p['payload']['specimen_id']),'record lineage mismatch')
  check(o.get('record_hash')==digest(data),'record payload hash mismatch')
  # Exact synthetic semantics, not just a self-consistent digest. Actual data are unsupported.
  q=data.get('payload');check(strict_equal(q,p['payload']),'operation payload, control, state, timing, history or calibration mismatch')
  if not isinstance(q,dict):continue
  prev=last_state.get(b)
  if op in ['CONFIGURE','DISCONNECT','REMOVE_HOTPLATE','RETURN_STORAGE','TRANSFER_IN','MOUNT','RETRIEVE']:
   check(prev is not None and prev.get('independent_safe_zero') is True,'unsafe causal transition before '+op)
  if prev is not None:
   if op=='TRANSFER_IN':check(prev.get('custody') in ['storage','carrier','retained_holder'],'transfer while still mounted')
   if op=='MOUNT':check(prev.get('custody')=='carrier','mount without transferred carrier')
   if op in ['CONFIGURE','DISCONNECT']:check(prev.get('custody')=='fixture','fixture operation without fixture custody')
   if op in ['REMOVE_HOTPLATE','RETURN_STORAGE']:check(prev.get('custody')=='retained_holder','transfer lacks disconnected retained holder')
   if op=='RETRIEVE':check(prev.get('custody') in ['retained_holder','carrier'],'retrieve before fixture release')
   if q.get('station')!=prev.get('station'):check(prev.get('custody') in ['carrier','retained_holder','storage'] and prev.get('independent_safe_zero') is True,'station changed without safe custody handoff')
  if op in ACTIVE:check(q.get('custody')=='fixture','electrical acquisition lacks fixture custody')
  if op=='MOUNT':last_cal[b]=q.get('calibration_id')
  if op in ACTIVE:check(q.get('calibration_id')==last_cal.get(b),'stale calibration after remount')
  if op=='READOUT':readout.add(b)
  if op=='ARCHIVE':check(b in readout,'archive before raw readout');archived.add(b)
  if op=='CLEAN_STORE':
   check(b in archived,'cleanup before archive');completed.add(b)
  for flag,phase in [('readout_complete','READOUT'),('archive_complete','ARCHIVE'),('cleanup_complete','CLEAN_STORE')]:check(o.get(flag) is (op==phase),'relabeled completion '+flag)
  if op=='RECEIVE':check(all(d in completed for d in BRANCHES[b]['depends_on']),'unfinished predecessor')
  last_state[b]=q
 check(set(obs)==seen,'unconsumed or missing observation')
 check(set(records)==used_records,'unconsumed or missing records')
 check(completed==set(ids),'missing final cleanup')
 return errors

def validate(context,actor_events):
 try:
  errors=_validate(context,actor_events)
 except (TypeError,ValueError,KeyError,IndexError,AttributeError,OverflowError) as e:
  errors=['malformed fixture: '+str(e)]
 return {'accepted':not errors,'errors':errors,'claim':'offline synthetic bookkeeping only','physical_execution':False,'scientific_replication':False}

if __name__=='__main__':
 c,e=fixture(list(BRANCHES));r=validate(c,e);print(json.dumps({'branches':len(BRANCHES),'events':len(e),**r},indent=2));raise SystemExit(0 if r['accepted'] else 1)
