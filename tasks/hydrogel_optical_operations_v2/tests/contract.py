"""Synthetic closed-service bookkeeping checks. No device control or physical model."""
from pathlib import Path
from itertools import product
import copy, json
ROOT=Path(__file__).resolve().parents[1]
PHASES=['LOAD','VERIFY','HANDOFF','READOUT','UNLOAD','COMMIT']
def load(name): return json.loads((ROOT/name).read_text())
BRANCHES={b['id']:b for b in load('branches.json')['branches']}
SERVICES={s['id'][3:]:s for s in load('station_contracts.json')['stations'] if s.get('closed_service')}

def conditions(branch):
 axes=branch['condition_axes'];keys=list(axes)
 return [json.dumps(dict(zip(keys,values)),sort_keys=True,separators=(',',':')) for values in product(*(axes[k] for k in keys))]

def closure(selected):
 out=set()
 def visit(i):
  if i not in BRANCHES: raise ValueError('unknown branch')
  if i in out:return
  out.add(i)
  for d in BRANCHES[i]['required_branch_ids']:visit(d)
 for i in selected:visit(i)
 return out

def ordered(selected):
 done=[]
 def visit(i):
  for d in BRANCHES[i]['required_branch_ids']:visit(d) if d not in done else None
  if i not in done:done.append(i)
 for i in selected:visit(i)
 return done

def compatible_conditions(a,b):
 a=json.loads(a);b=json.loads(b)
 if not all(a[k]==b[k] for k in set(a)&set(b)):return False
 if 'material' in b and b['material']!=a.get('material','LIHAM'):return False
 if 'resist' in b and b['resist']!=a.get('resist','DEGRAD_INX_N100'):return False
 return True

def required_controls(ids):
 # Explicit controls bind to their observation branches, including source comparisons.
 controls={'CTRL_BASELINE'}
 scopes={'HYDROGEL_CONTROLS':'CTRL_MATERIAL','BEAM_POWER':'CTRL_DIRECTION','SQUARE_LATTICES':'CTRL_COMPAT','LATTICE_CYCLES':'CTRL_CYCLE','POWER_IMAGE':'CTRL_IMAGE','ANGLE_IMAGE_MAIN':'CTRL_POLAR','ANGLE_IMAGE_VIDEO':'CTRL_POLAR','DUAL_IMAGE':'CTRL_DUAL'}
 for b in ids:
  if b in scopes:controls.add(scopes[b])
 if 'BEAM_POWER' in ids:controls.add('CTRL_PLANE')
 return sorted(controls)

def fixture(selected=None,mode='selected_branch_design'):
 """Entirely authored synthetic authority and events, never measured source data."""
 selected=selected or ['BEAM_POWER']
 if mode=='whole_physical_campaign':selected=list(BRANCHES)
 ids=ordered(selected); jobs={};plans={};events=[];last={};branch_outputs={};allocations={};lineage={}
 for branch_id in ids:
  b=BRANCHES[branch_id];n=b['source_cycles'] or 1
  plans[branch_id]={'conditions':conditions(b),'cycles':list(range(1,n+1)),'count_origin':'source_cycle_count' if b['source_cycles'] else 'authored_fixture_only'}
  branch_outputs[branch_id]=[]
  for cond in conditions(b):
   for cycle in plans[branch_id]['cycles']:
    # The same planned specimen remains identified across repeated cycles.
    specimen='fixture_specimen_'+str(len([x for x in last if x.startswith(branch_id+'|')]))
    key=branch_id+'|'+cond
    if key not in last:last[key]={'id':branch_id+'_specimen_'+str(len(last)),'version':1}
    specimen=last[key]['id'];version=last[key]['version']
    allocation_key=branch_id+'|'+cond
    if allocation_key not in allocations:allocations[allocation_key]={'branch_id':branch_id,'condition_id':cond,'service_specimens':{},'material_class':json.loads(cond).get('material','LIHAM'),'condition_origin':'authored_qualified_binding','source_unit_count':27000 if branch_id=='ANGLE_IMAGE_VIDEO' else (10000 if branch_id in ['ANGLE_IMAGE_MAIN','POWER_IMAGE','IMAGE_CYCLES'] else None)}
    for s in b['service_ids']:
     if branch_id=='THREE_D':
      specimen=last[key]['id']+'_'+s;version=1
     allocations[allocation_key]['service_specimens'][s]=specimen
     if specimen not in lineage:lineage[specimen]={'specimen_id':specimen,'version':version,'parent_batch_ids':['synthetic_batch_'+allocations[allocation_key]['material_class']],'substrate_id':specimen+'_substrate','cover_id':specimen+'_cover','carrier_id':'synthetic_carrier_'+specimen,'resist_material':json.loads(cond).get('resist','DEGRAD_INX_N100'),'hydrogel_material':allocations[allocation_key]['material_class'],'geometry_hash':'synthetic_geometry_'+allocation_key,'dose_map_hash':'synthetic_dose_'+allocation_key,'orientation_map_hash':'synthetic_orientation_'+allocation_key,'development_card_revision':'synthetic_card_v1','chamber_id':specimen+'_chamber','service_job_ids':[],'thermal_history':[],'damage_state':'accepted','allocation_role':'reserved_'+s if branch_id=='THREE_D' or s=='RHEO' else 'qualified_reusable','allocation_key':allocation_key}
     jid='J'+str(len(jobs)+1)
     job={'job_id':jid,'branch_id':branch_id,'condition_id':cond,'cycle':cycle,'service_id':s,'specimen_id':specimen,'input_version':version,'output_version':version+1,'attempt_id':'accepted_attempt_1','card_revision':'synthetic_card_v1','fixture_id':'synthetic_fixture_'+s,'calibration_id':'synthetic_cal_'+s,'station_id':'WS_'+s,'carrier_id':'synthetic_carrier_'+specimen,'raw_record_id':'synthetic://record/'+jid,'record_hash':'synthetic_hash_'+jid,'authority_id':'synthetic_service_authority','source_kind':'synthetic_fixture','parents':[o for d in b['required_branch_ids'] for o in branch_outputs[d] if compatible_conditions(cond,jobs[o]['condition_id'])],'qualified':True,'closed_service':True,'safe_release':True,'accepted':True,'optical_self_peeling':s=='RELEASE','optical_free_movement':s=='RELEASE','destroyed':False,'damage_state':'accepted','optical_release_specimen_id':specimen if s=='RELEASE' else None,'optical_release_version':version+1 if s=='RELEASE' else None,'optical_release_record_id':'synthetic://record/'+jid if s=='RELEASE' else None}
     jobs[jid]=job;branch_outputs[branch_id].append(jid);lineage[specimen]['service_job_ids'].append(jid)
     if s in ['THERMAL','RELEASE','SPECTRA','RHEO','CONFOCAL','POLAR']:lineage[specimen]['thermal_history'].append({'job_id':jid,'input_version':version,'output_version':version+1,'cycle':cycle,'record_id':'synthetic://record/'+jid,'source_kind':'synthetic_fixture'})
     for phase in PHASES:
      events.append({'event_id':'EV'+str(len(events)+1),'sequence':len(events)+1,'phase':phase,**{k:v for k,v in job.items() if k not in ['parents','qualified','closed_service','safe_release','accepted','optical_self_peeling','optical_free_movement','destroyed','damage_state','optical_release_specimen_id','optical_release_version','optical_release_record_id']},'safe_exchange':True,'hazard_isolated':True,'guard_closed':True,'receipt_status':'accepted','public_note':'Authored synthetic record; no experiment occurred.'})
     version+=1
    last[key]['version']=version
 ctx={'fixture_only':True,'authority_id':'synthetic_service_authority','mode':mode,'selected_branches':selected,'plans':plans,'jobs':jobs,'cards':{u: {'qualified':True,'revision':'synthetic_card_v1','authority_id':'synthetic_service_authority'} for b in ids for u in BRANCHES[b]['unknown_parameter_ids']},'conflict_resolutions':{i:'authored_fixture_resolution_only_not_source_correction' for i in ['C1','C2','C3','C4','C5','C6','C7','C8','C9','C10']},'controls':{i:{'passed':True,'source_kind':'synthetic_fixture','record_id':'synthetic://control/'+i} for i in required_controls(ids)},'batches':{'synthetic_batch_'+a['material_class']:{'material':a['material_class'],'qualified':True,'source_kind':'synthetic_fixture'} for a in allocations.values()},'condition_allocations':allocations,'lineage':lineage,'reuse_cards':{},'archive_complete':True,'cleanup_complete':True,'actor_source_targets_exposed':False}
 return ctx,events

def _validate(context,events):
 errors=[]
 def check(condition,msg):
  if not condition:errors.append(msg)
 if not isinstance(context,dict) or not isinstance(events,list):return ['wrong outer type']
 check(context.get('fixture_only') is True,'production authority is not implemented')
 check(context.get('authority_id')=='synthetic_service_authority','invalid authority')
 check(context.get('mode') in ['selected_branch_design','whole_physical_campaign'],'invalid mode')
 selected=context.get('selected_branches',[])
 check(isinstance(selected,list) and bool(selected) and len(selected)==len(set(selected)),'empty or duplicate selected branches')
 try:ids=closure(selected)
 except (ValueError,TypeError):return errors+['invalid selected branches']
 if context.get('mode')=='whole_physical_campaign':check(ids==set(BRANCHES),'whole campaign branch omission')
 plans=context.get('plans',{});jobs=context.get('jobs',{})
 check(set(plans)==ids,'plan dependency closure mismatch')
 expected_cells=set()
 for b in ids:
  plan=plans.get(b,{})
  check(plan.get('conditions')==conditions(BRANCHES[b]),'condition omission or rewrite: '+b)
  cycles=plan.get('cycles')
  valid_cycles=isinstance(cycles,list) and len(cycles)>0 and all(type(n) is int and n>0 for n in cycles) and cycles==list(range(1,len(cycles)+1))
  check(valid_cycles,'empty, unknown, noninteger or unbounded cycle schedule: '+b)
  if BRANCHES[b]['source_cycles']:
   check(cycles==list(range(1,BRANCHES[b]['source_cycles']+1)),'source cycle lineage mismatch: '+b)
   check(plan.get('count_origin')=='source_cycle_count','source cycle attribution changed')
  else:check(plan.get('count_origin')=='authored_fixture_only','unknown source repeat count fabricated')
  if valid_cycles:
   expected_cells.update((b,c,n,s) for c in conditions(BRANCHES[b]) for n in cycles for s in BRANCHES[b]['service_ids'])
  for u in BRANCHES[b]['unknown_parameter_ids']:
   card=context.get('cards',{}).get(u,{})
   check(card.get('qualified') is True and card.get('revision')=='synthetic_card_v1' and card.get('authority_id')==context.get('authority_id'),'missing or stale qualified card '+u)
 actual_cells=[]
 allocations=context.get('condition_allocations',{});lineage=context.get('lineage',{})
 expected_allocation_keys={b+'|'+c for b in ids for c in conditions(BRANCHES[b])}
 check(set(allocations)==expected_allocation_keys,'missing or extra condition allocations')
 expected_specimens=set()
 for key,a in allocations.items():
  check(set(a)=={'branch_id','condition_id','service_specimens','material_class','condition_origin','source_unit_count'},'allocation schema mismatch')
  check(a.get('condition_origin')=='authored_qualified_binding','allocation provenance missing or misattributed')
  b=a.get('branch_id');cond=a.get('condition_id')
  if b not in ids or cond not in conditions(BRANCHES[b]):errors.append('invalid allocation condition');continue
  check(key==b+'|'+cond,'allocation identity mismatch')
  check(set(a.get('service_specimens',{}))==set(BRANCHES[b]['service_ids']),'allocation service set mismatch')
  count=27000 if b=='ANGLE_IMAGE_VIDEO' else (10000 if b in ['ANGLE_IMAGE_MAIN','POWER_IMAGE','IMAGE_CYCLES'] else None)
  check(a.get('source_unit_count')==count,'source image specimen unit-count merge')
  check(a.get('material_class')==json.loads(cond).get('material','LIHAM'),'allocation material mismatch')
  expected_specimens.update(a.get('service_specimens',{}).values())
  if b=='THREE_D':check(len(set(a.get('service_specimens',{}).values()))==len(BRANCHES[b]['service_ids']),'SEM and confocal need separate reserved siblings')
 check(set(lineage)==expected_specimens,'missing or extra specimen lineage')
 required_lineage=load('lineage_contract.json')['required_keys']+['allocation_key']
 for sid,l in lineage.items():
  check(set(l)==set(required_lineage),'incomplete or extra lineage fields')
  check(all(k in l and l[k] is not None for k in required_lineage),'incomplete lineage fields')
  for field in ['specimen_id','substrate_id','cover_id','carrier_id','resist_material','hydrogel_material','geometry_hash','dose_map_hash','orientation_map_hash','development_card_revision','chamber_id','damage_state','allocation_role','allocation_key']:
   check(isinstance(l.get(field),str) and bool(l.get(field)),'invalid lineage field '+field)
  check(type(l.get('version')) is int and l.get('version',0)>0,'invalid lineage version')
  check(l.get('development_card_revision')=='synthetic_card_v1','obsolete development card')
  expected_jobs=[jid for jid,j in jobs.items() if j.get('specimen_id')==sid]
  check(isinstance(l.get('service_job_ids'),list) and len(l.get('service_job_ids',[]))==len(set(l.get('service_job_ids',[]))) and set(l.get('service_job_ids',[]))==set(expected_jobs),'lineage job registry mismatch')
  if expected_jobs:check(l.get('version')==min(jobs[j]['input_version'] for j in expected_jobs),'lineage initial version mismatch')
  expected_thermal=[{'job_id':jid,'input_version':j['input_version'],'output_version':j['output_version'],'cycle':j['cycle'],'record_id':j['raw_record_id'],'source_kind':'synthetic_fixture'} for jid,j in jobs.items() if j.get('specimen_id')==sid and j.get('service_id') in ['THERMAL','RELEASE','SPECTRA','RHEO','CONFOCAL','POLAR']]
  check(type(l.get('thermal_history')) is list and l.get('thermal_history')==expected_thermal,'thermal exposure history missing or mismatched')
  check(type(l.get('parent_batch_ids')) is list and bool(l.get('parent_batch_ids')) and all(isinstance(x,str) and bool(x) for x in l.get('parent_batch_ids',[])),'invalid parent batch list')
  check(l.get('specimen_id')==sid,'lineage specimen mismatch')
  check(l.get('substrate_id')!=l.get('cover_id'),'cover/substrate identity collapsed')
  check(l.get('damage_state')=='accepted','damaged or destroyed lineage reused')
  a=allocations.get(l.get('allocation_key'),{})
  check(sid in a.get('service_specimens',{}).values(),'crossed allocation lineage')
  check(l.get('hydrogel_material')==a.get('material_class'),'hydrogel lineage mismatch')
  expected_resist=json.loads(a.get('condition_id','{}')).get('resist','DEGRAD_INX_N100')
  check(l.get('resist_material')==expected_resist,'resist lineage mismatch')
  for batch in l.get('parent_batch_ids',[]):
   v=context.get('batches',{}).get(batch,{})
   check(v.get('qualified') is True and v.get('material')==a.get('material_class') and v.get('source_kind')=='synthetic_fixture','unqualified or wrong material batch')
  check(bool(l.get('parent_batch_ids')) and bool(l.get('geometry_hash')) and bool(l.get('dose_map_hash')) and bool(l.get('orientation_map_hash')),'missing material/map ancestry')
 for jid,j in jobs.items():
  expected_job_keys={'job_id','branch_id','condition_id','cycle','service_id','specimen_id','input_version','output_version','attempt_id','card_revision','fixture_id','calibration_id','station_id','carrier_id','raw_record_id','record_hash','authority_id','source_kind','parents','qualified','closed_service','safe_release','accepted','optical_self_peeling','optical_free_movement','destroyed','damage_state','optical_release_specimen_id','optical_release_version','optical_release_record_id'}
  check(set(j)==expected_job_keys,'missing or unknown job field')
  for field in ['job_id','branch_id','condition_id','service_id','specimen_id','attempt_id','card_revision','fixture_id','calibration_id','station_id','carrier_id','raw_record_id','record_hash','authority_id','source_kind']:
   check(isinstance(j.get(field),str) and bool(j.get(field)),'missing or invalid job binding '+field)
  check(j.get('card_revision')=='synthetic_card_v1','stale job card revision')
  check(j.get('fixture_id')=='synthetic_fixture_'+str(j.get('service_id')),'unregistered fixture')
  check(j.get('calibration_id')=='synthetic_cal_'+str(j.get('service_id')),'unregistered calibration')
  check(j.get('raw_record_id')=='synthetic://record/'+jid and j.get('record_hash')=='synthetic_hash_'+jid,'invalid raw-record identity/hash')
  check(j.get('attempt_id')=='accepted_attempt_1','unqualified attempt')
  check(j.get('damage_state')=='accepted','quarantined service specimen')
  check(j.get('job_id')==jid,'job identity mismatch')
  cell=(j.get('branch_id'),j.get('condition_id'),j.get('cycle'),j.get('service_id'));actual_cells.append(cell)
  check(j.get('service_id') in SERVICES,'unknown service')
  check(j.get('station_id')=='WS_'+str(j.get('service_id')),'wrong station')
  check(j.get('source_kind')=='synthetic_fixture','source/future data passed as observed evidence')
  check(j.get('authority_id')==context.get('authority_id'),'job authority mismatch')
  check(j.get('qualified') is True and j.get('closed_service') is True,'unqualified or open service')
  check(j.get('safe_release') is True and j.get('accepted') is True,'unsafe or rejected service job')
  check(j.get('destroyed') is False,'destroyed specimen used')
  check(type(j.get('input_version')) is int and j.get('input_version',0)>0 and j.get('output_version')==j.get('input_version',0)+1,'invalid version transition')
  if j.get('service_id')=='RELEASE':
   check(j.get('optical_self_peeling') is True and j.get('optical_free_movement') is True,'temperature alone cannot prove release')
   check(j.get('optical_release_specimen_id')==j.get('specimen_id') and j.get('optical_release_version')==j.get('output_version') and j.get('optical_release_record_id')==j.get('raw_record_id'),'optical release evidence bound to wrong specimen/version/record')
  else:
   check(j.get('optical_self_peeling') is False and j.get('optical_free_movement') is False,'invalid non-release flags')
   check(all(j.get(k) is None for k in ['optical_release_specimen_id','optical_release_version','optical_release_record_id']),'release evidence misattributed to other service')
  b=j.get('branch_id');allocation=allocations.get(str(b)+'|'+str(j.get('condition_id')),{})
  check(allocation.get('service_specimens',{}).get(j.get('service_id'))==j.get('specimen_id'),'job not bound to allocated specimen')
  l=lineage.get(j.get('specimen_id'),{})
  check(l.get('allocation_key')==str(b)+'|'+str(j.get('condition_id')),'crossed specimen between condition allocations')
  check(jid in l.get('service_job_ids',[]),'job absent from lineage history')
  check(l.get('carrier_id')==j.get('carrier_id'),'carrier lineage mismatch')
  expected_role='reserved_'+j['service_id'] if b=='THREE_D' or j['service_id']=='RHEO' else 'qualified_reusable'
  check(l.get('allocation_role')==expected_role,'unreserved or incompatible specimen role')
  if b in ids:
   parents=j.get('parents',[])
   expected_parents={p for p,pj in jobs.items() if pj.get('branch_id') in BRANCHES[b]['required_branch_ids'] and compatible_conditions(j['condition_id'],pj['condition_id'])}
   check(set(parents)==expected_parents,'missing, mismatched or crossed parent condition lineage for '+b)
   for d in BRANCHES[b]['required_branch_ids']:
    check(any(jobs.get(p,{}).get('branch_id')==d for p in parents),'missing parent lineage for '+b)
 check(len(actual_cells)==len(set(actual_cells)),'duplicate condition service jobs')
 check(set(actual_cells)==expected_cells,'missing or extra condition/cycle/service cell')
 # No context is actor supplied in a future integration; this module merely checks authored fixtures.
 for c in ['C1','C2','C3','C4','C5','C6','C7','C8','C9','C10']:
  check(context.get('conflict_resolutions',{}).get(c)=='authored_fixture_resolution_only_not_source_correction','unresolved or silently corrected source conflict '+c)
 for c in required_controls(ids):
  v=context.get('controls',{}).get(c,{})
  check(v.get('passed') is True and v.get('source_kind')=='synthetic_fixture' and bool(v.get('record_id')),'missing control '+c)
 seen=set();progress={j:[] for j in jobs};completed=set();versions={};specimen_by_cell={}
 for index,event in enumerate(events,1):
  if not isinstance(event,dict):errors.append('invalid event');continue
  event_keys={'event_id','sequence','phase','job_id','branch_id','condition_id','cycle','service_id','specimen_id','input_version','output_version','attempt_id','card_revision','fixture_id','calibration_id','station_id','carrier_id','raw_record_id','record_hash','authority_id','source_kind','safe_exchange','hazard_isolated','guard_closed','receipt_status','public_note'}
  check(set(event)==event_keys,'missing or unknown actor event field')
  eid=event.get('event_id');check(isinstance(eid,str) and bool(eid) and eid not in seen,'missing or duplicate event ID');seen.add(eid)
  check(event.get('sequence')==index,'noncontiguous event sequence')
  jid=event.get('job_id');j=jobs.get(jid)
  if not j:errors.append('untrusted job reference');continue
  phase=event.get('phase');expected=PHASES[len(progress[jid])] if len(progress[jid])<len(PHASES) else None
  check(phase==expected,'out-of-order or duplicate phase')
  progress[jid].append(phase)
  for key in ['job_id','branch_id','condition_id','cycle','service_id','specimen_id','input_version','output_version','attempt_id','card_revision','fixture_id','calibration_id','station_id','carrier_id','raw_record_id','record_hash','authority_id','source_kind']:
   check(event.get(key)==j.get(key),'event/context binding mismatch: '+key)
  check(all(event.get(k) is True for k in ['safe_exchange','hazard_isolated','guard_closed']),'unsafe boundary readback')
  check(event.get('receipt_status')=='accepted','failed receipt is not completion')
  b=j.get('branch_id');cell=(b,j.get('condition_id'),j.get('service_id') if b=='THREE_D' else 'shared')
  if phase=='LOAD':
   for parent in j.get('parents',[]):check(parent in completed,'lineage parent not completed before load')
   if cell in specimen_by_cell:check(specimen_by_cell[cell]==j.get('specimen_id'),'cycle specimen changed without new lineage')
   else:specimen_by_cell[cell]=j.get('specimen_id')
   sid=j.get('specimen_id')
   if sid in versions:check(versions[sid]==j.get('input_version'),'stale input version')
   else:check(j.get('input_version')==1,'missing initial specimen version')
  if phase=='COMMIT':completed.add(jid);versions[j.get('specimen_id')]=j.get('output_version')
 for jid,got in progress.items():check(got==PHASES,'incomplete job '+jid)
 check(context.get('archive_complete') is True,'archive missing')
 check(context.get('cleanup_complete') is True,'cleanup missing')
 check(context.get('actor_source_targets_exposed') is False,'actor target leakage')
 return sorted(set(errors))


def validate(context,events):
 """Malformed structures fail closed rather than raising past the evaluator."""
 try:return _validate(context,events)
 except (ValueError,KeyError,TypeError,AttributeError,IndexError) as exc:return ["malformed synthetic contract: "+type(exc).__name__]
