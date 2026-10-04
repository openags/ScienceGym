"""Offline synthetic contract only. No robot, physics, source data or production authority."""
from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parents[1]
B={b['id']:b for b in json.loads((R/'branches.json').read_text())['branches']}
ACTOR_KEYS={'event_id','job_id','phase'}
PHASES=['VERIFY_INPUT','DOCK','MOUNT','SETUP_CHECK']
TAIL=['READOUT','SAFE_RELEASE','RETRIEVE','INSPECT','ARCHIVE','CLEAN_STORE']
FINAL=['FINAL_SAFE_RELEASE','FINAL_PROBE_RETRIEVE','FINAL_PROBE_INSPECT','FINAL_CAL_INVALIDATE','FINAL_SESSION_ARCHIVE','FINAL_SESSION_CLEAN_STORE']
CONTACT=['MOVE','APPROACH','ACQUIRE','WITHDRAW','VERIFY_RELEASE']

def same(a,b):
 """JSON type-strict equality: bool is not an integer and lists are not tuples."""
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b

def closure(selected):
 out=[]
 def add(b):
  if b not in B:raise ValueError('unknown branch')
  for d in B[b]['depends_on']:add(d)
  if b not in out:out.append(b)
 for b in selected:add(b)
 return out

def point_ids(b):
 # Deliberately reduced authored coverage, never a complete source experiment.
 if b=='ARRAY_CAL':return ['cal_0','cal_1','cal_2']
 if b=='LEVER_CAL':return ['glass_ref']
 if b in ('ARROW_RASTER','COMPLEX_RASTER'):return ['tile_0','tile_1','tile_2','tile_3']
 if b=='ARROW_LINE':return ['line_0','line_1','line_2']
 if b=='CYLINDER_MECHANICS':return ['radius_A','radius_B']
 if b=='SINGLE_OPTICS':return ['indent_A','indent_B']
 return ['center','offset_A','offset_B']

def plan_for(b):
 ps=PHASES[:]
 if b=='ARRAY_CAL':ps+=['LEVEL','BASELINE']
 elif b=='LEVER_CAL':ps+=['THERMAL_PSD']
 elif b in ('SINGLE_OPTICS','OFF_CENTER'):ps+=['REGISTER','BASELINE']
 else:ps+=['REGISTER']
 for p in point_ids(b):ps += [x+':'+p for x in CONTACT]
 if b in ('ARRAY_CAL','LEVER_CAL'):ps+=['CAL_FIT']
 return ps+TAIL

def phases_for(b,ids):
 last=[x for x in ids if B[x]['setup_id']==B[b]['setup_id']][-1]
 return plan_for(b)+(FINAL if b==last else [])

def binding(b):
 setup=B[b]['setup_id'];parallel=setup=='parallel'
 return {'specimen_id':'synthetic_'+B[b]['target_role'],
 'specimen_version':1,'carrier_id':'synthetic_'+B[b]['target_role']+'_carrier',
 'probe_id':'synthetic_array' if parallel else 'synthetic_lever',
 'probe_carrier_id':'synthetic_array_carrier' if parallel else 'synthetic_lever_carrier',
 'probe_mount_version':'synthetic_'+setup+'_probe_mount_v1',
 'setup_id':setup,'setup_version':'synthetic_'+setup+'_v1','mount_version':'synthetic_'+setup+'_probe_mount_v1',
 'target_mount_version':'synthetic_'+b+'_target_mount_v1',
 'calibration_id':'synthetic_array_cal_v1' if parallel else 'synthetic_lever_cal_v1',
 'target_id':B[b]['target_role'],'region_id':b.lower()+'_region','schedule_id':b+'_reduced_fixture',
 'metric':'main_normalized_brightness' if parallel else ('si_baseline_subtracted_darkening' if b in ('SINGLE_OPTICS','OFF_CENTER') else 'force_distance')}

def fixture(selected=None,episode_id='synthetic_episode_001'):
 selected=selected or ['ARROW_RASTER'];ids=closure(selected)
 cards={u:{'id':u,'revision':'synthetic_v1','qualified_for_fixture_only':True,'authority':'synthetic_fixture_authority'} for b in ids for u in B[b]['unknown_parameter_ids']}
 jobs={};observations={};events=[]
 for b in ids:
  job={'episode_id':episode_id,'job_id':b,'branch_id':b,'binding':binding(b),'parents':B[b]['depends_on'],
       'schedule':{'origin':'authored_reduced_fixture','point_ids':point_ids(b),'full_source_scan':False},
       'phases':phases_for(b,ids),'attempt_id':'synthetic_attempt_1','source_kind':'synthetic_fixture'}
  jobs[b]=job
  for phase in job['phases']:
   eid='EV'+str(len(events)+1);kind,_,point=phase.partition(':')
   contact='contact' if kind in ['APPROACH','ACQUIRE','WITHDRAW'] else 'released'
   # WITHDRAW is only a command acknowledgment; it never proves release.
   record='synthetic://'+episode_id+'/'+b+'/'+phase
   observations[eid]={'episode_id':episode_id,'event_id':eid,'job_id':b,'phase':phase,'binding':binding(b),
    'point_id':point or None,'custody_asset_role':'retained_probe' if kind.startswith('FINAL_') else 'exchange_specimen','attempt_id':job['attempt_id'],'source_kind':'synthetic_fixture',
    'authority':'synthetic_fixture_authority','contact_state':contact,'stationary':True,
    'support_retained':True,'safe_exchange':True,'qualified':True,'accepted':True,'damage_state':'accepted',
    'raw_record_id':record,'record_hash':hashlib.sha256(record.encode()).hexdigest(),
    'source_metric_used':binding(b)['metric'],'baseline_current':True,'force_release_measured':kind=='VERIFY_RELEASE',
    'inspection_current':kind in ['INSPECT','FINAL_PROBE_INSPECT'],'archive_complete':kind in ['ARCHIVE','FINAL_SESSION_ARCHIVE'],'cleanup_complete':kind in ['CLEAN_STORE','FINAL_SESSION_CLEAN_STORE'],'calibration_invalidated':kind=='FINAL_CAL_INVALIDATE'}
   events.append({'event_id':eid,'job_id':b,'phase':phase})
 ctx={'episode_id':episode_id,'mode':'synthetic_contract_only','production_authority':False,'whole_historical_route_complete':False,
 'scientific_replication':False,'selected_branches':selected,'cards':cards,'jobs':jobs,'observations':observations,
 'input_qualification':{'prefabricated_array':True,'cylinder_coupon':True,'configured_instruments':True,'fabrication_performed':False},
 'source_conflicts_preserved':['C_SCALE','C_PRECISION','C_CROSSTALK','C_OPTICS','C_REPEAT_SOURCE','C_INTENSITY','C_MODULUS','C_SERIES_FORMULA']}
 return ctx,events

def _validate(ctx,events):
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 if not isinstance(ctx,dict) or not isinstance(events,list):return ['wrong outer types']
 check(set(ctx)=={'episode_id','mode','production_authority','whole_historical_route_complete','scientific_replication','selected_branches','cards','jobs','observations','input_qualification','source_conflicts_preserved'},'unknown or missing context fields')
 episode_id=ctx.get('episode_id')
 check(isinstance(episode_id,str) and episode_id.startswith('synthetic_episode_'),'missing or invalid episode identity')
 check(ctx.get('mode')=='synthetic_contract_only' and ctx.get('production_authority') is False,'production execution unsupported')
 check(ctx.get('whole_historical_route_complete') is False and ctx.get('scientific_replication') is False,'invalid completion claim')
 selected=ctx.get('selected_branches')
 check(isinstance(selected,list) and bool(selected) and len(selected)==len(set(selected)),'invalid selected branch set')
 ids=closure(selected);jobs=ctx.get('jobs',{});obs=ctx.get('observations',{})
 check(set(jobs)==set(ids),'dependency closure mismatch')
 check(set(ctx.get('source_conflicts_preserved',[]))==set(fixture(['ARRAY_CAL'])[0]['source_conflicts_preserved']),'source conflict omitted')
 check(same(ctx.get('input_qualification'),{'prefabricated_array':True,'cylinder_coupon':True,'configured_instruments':True,'fabrication_performed':False}),'qualified initial inputs missing or fabrication completion invented')
 expected_cards={u for b in ids for u in B[b]['unknown_parameter_ids']}
 check(set(ctx.get('cards',{}))==expected_cards,'missing/extra qualified input cards')
 for u in expected_cards:
  check(same(ctx.get('cards',{}).get(u),{'id':u,'revision':'synthetic_v1','qualified_for_fixture_only':True,'authority':'synthetic_fixture_authority'}),'stale or unqualified card '+u)
 for b,j in jobs.items():
  if b not in ids:continue
  check(set(j)=={'episode_id','job_id','branch_id','binding','parents','schedule','phases','attempt_id','source_kind'},'unknown or missing job fields')
  check(j.get('episode_id')==episode_id,'cross-episode job replay')
  check(j.get('job_id')==b and j.get('branch_id')==b,'job identity mismatch')
  check(j.get('parents')==B[b]['depends_on'],'dependency parent mismatch')
  check(same(j.get('binding'),binding(b)),'stale/mismatched specimen, target, setup, mount, calibration or metric')
  check(same(j.get('schedule'),{'origin':'authored_reduced_fixture','point_ids':point_ids(b),'full_source_scan':False}),'invalid or source-misattributed schedule')
  check(j.get('phases')==phases_for(b,ids),'incomplete/altered planned route')
  check(j.get('attempt_id')=='synthetic_attempt_1' and j.get('source_kind')=='synthetic_fixture','unrecognized attempt/source')
 expected_keys=set(fixture(['ARRAY_CAL'])[0]['observations']['EV1'])
 check(len(events)==sum(len(phases_for(b,ids)) for b in ids),'wrong event count')
 check(len(obs)==len(events),'missing or extra observations')
 seen=set();progress={b:[] for b in ids};completed=set();states={b:'released' for b in ids};last_release={b:None for b in ids};baselines=set();closed_setups=set();invalidated_setups=set()
 sequence=[(b,p) for b in ids for p in phases_for(b,ids)]
 for n,e in enumerate(events):
  if not isinstance(e,dict):errors.append('malformed actor event');continue
  check(set(e)==ACTOR_KEYS,'actor may not supply observations or success flags')
  eid=e.get('event_id');b=e.get('job_id');phase=e.get('phase')
  check(isinstance(eid,str) and eid not in seen,'duplicate/missing event id');seen.add(eid)
  if b not in jobs:errors.append('unknown job');continue
  check(n<len(sequence) and (b,phase)==sequence[n],'wrong phase, point order or branch order')
  o=obs.get(eid)
  if not isinstance(o,dict):errors.append('missing environment observation');continue
  check(set(o)==expected_keys,'unknown or missing observation fields')
  for k,v in [('episode_id',episode_id),('event_id',eid),('job_id',b),('phase',phase),('binding',jobs[b].get('binding')),('attempt_id',jobs[b].get('attempt_id')),('source_kind','synthetic_fixture'),('authority','synthetic_fixture_authority')]:check(same(o.get(k),v),'observation binding mismatch '+k)
  check(o.get('qualified') is True and o.get('accepted') is True,'unqualified/rejected observation')
  check(o.get('support_retained') is True,'unsupported specimen custody')
  check(o.get('stationary') is True,'moving readback not settled')
  check(o.get('damage_state')=='accepted','damaged or unknown specimen state')
  check(o.get('source_metric_used')==binding(b)['metric'],'wrong intensity metric')
  check(o.get('baseline_current') is True,'stale optical baseline')
  record='synthetic://'+episode_id+'/'+b+'/'+str(phase)
  check(o.get('raw_record_id')==record and o.get('record_hash')==hashlib.sha256(record.encode()).hexdigest(),'record identity/hash mismatch')
  kind,_,point=str(phase).partition(':')
  check(o.get('contact_state')==('contact' if kind in ['APPROACH','ACQUIRE','WITHDRAW'] else 'released'),'contradictory or unknown phase-end contact state')
  check(o.get('custody_asset_role')==('retained_probe' if kind.startswith('FINAL_') else 'exchange_specimen'),'probe/target custody conflated')
  check(o.get('calibration_invalidated') is (kind=='FINAL_CAL_INVALIDATE'),'calibration invalidation receipt relabeled')
  if kind=='FINAL_CAL_INVALIDATE':invalidated_setups.add(B[b]['setup_id'])
  if kind=='FINAL_SESSION_CLEAN_STORE':
   check(B[b]['setup_id'] in invalidated_setups,'session closed with active calibration');closed_setups.add(B[b]['setup_id'])
  if kind=='VERIFY_INPUT':check(B[b]['setup_id'] not in closed_setups,'closed session reused')
  check(o.get('point_id')==(point or None),'point identity mismatch')
  if kind=='VERIFY_INPUT':check(all(d in completed for d in B[b]['depends_on']),'uncompleted calibration dependency')
  if kind=='BASELINE':
   check(states[b]=='released' and o.get('contact_state')=='released','baseline in contact');baselines.add(b)
  if kind=='MOVE':check(states[b]=='released' and o.get('contact_state')=='released','lateral motion before verified release')
  if kind=='APPROACH':
   check(states[b]=='released' and o.get('contact_state')=='contact','invalid approach transition');states[b]='contact'
  if kind=='ACQUIRE':
   check(states[b]=='contact' and o.get('contact_state')=='contact' and o.get('stationary') is True,'acquisition without stationary contact')
   if b in ['ARRAY_CAL','SINGLE_OPTICS','OFF_CENTER']:check(b in baselines,'missing optical baseline')
  if kind=='WITHDRAW':
   check(states[b]=='contact','withdraw without contact');states[b]='awaiting_release'
  if kind=='VERIFY_RELEASE':
   check(states[b]=='awaiting_release' and o.get('contact_state')=='released' and o.get('force_release_measured') is True,'withdrawal command is not verified release');states[b]='released';last_release[b]=eid
  if kind in ['READOUT','SAFE_RELEASE','RETRIEVE','INSPECT','ARCHIVE','CLEAN_STORE']+FINAL:
   check(states[b]=='released' and last_release[b] is not None and o.get('contact_state')=='released','terminal handoff before measured release')
  if kind in ['DOCK','MOUNT','SAFE_RELEASE','RETRIEVE','CLEAN_STORE']+FINAL:check(o.get('safe_exchange') is True,'unsafe exchange')
  check(o.get('force_release_measured') is (kind=='VERIFY_RELEASE'),'release receipt relabeled')
  check(o.get('inspection_current') is (kind in ['INSPECT','FINAL_PROBE_INSPECT']),'inspection receipt relabeled')
  check(o.get('archive_complete') is (kind in ['ARCHIVE','FINAL_SESSION_ARCHIVE']),'archive receipt relabeled')
  check(o.get('cleanup_complete') is (kind in ['CLEAN_STORE','FINAL_SESSION_CLEAN_STORE']),'cleanup receipt relabeled')
  progress[b].append(phase)
  if kind=='CLEAN_STORE':completed.add(b)
 for b in ids:check(progress[b]==phases_for(b,ids),'incomplete branch '+b)
 check(completed==set(ids),'branches not safely closed')
 check(closed_setups=={B[b]['setup_id'] for b in ids},'instrument sessions not safely closed')
 check(set(obs)==seen,'observation/event registry mismatch')
 return sorted(set(errors))

def validate(ctx,events):
 try:return _validate(ctx,events)
 except (ValueError,TypeError,KeyError,AttributeError,IndexError):return ['malformed synthetic contract fails closed']
