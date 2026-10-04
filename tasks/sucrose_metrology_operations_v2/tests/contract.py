"""Offline authored synthetic record contract. No hardware, PCA, optics or production trust."""
from pathlib import Path
import json, hashlib, math
R=Path(__file__).resolve().parents[1]
B={b['id']:b for b in json.loads((R/'branches.json').read_text())['branches']}
PROFILES={'SPP2_1064':('SPP2',1064),'SPP5_1064':('SPP5',1064),'SPP5_532':('SPP5',532)}
SAMPLES=['cal_low','cal_mid','cal_high','test_a','test_b']
TRAIN=SAMPLES[:3];TEST=SAMPLES[3:]
VALUES=dict(zip(SAMPLES,[1.3328,1.3365,1.3403,1.3343,1.3388]))
CONFLICTS=[c['id'] for c in json.loads((R/'source_conflicts.json').read_text())]
TAIL=['SAFE_ISOLATE','INVALIDATE_CALIBRATION','UNDOCK','INSPECT','ARCHIVE','CLEAN_STORE']

def same(a,b):
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b

def closure(selected):
 if type(selected) is not list or not selected or any(type(b) is not str or b not in B for b in selected) or len(set(selected))!=len(selected):raise ValueError('invalid branches')
 if 'FLOW_HOLD' in selected and selected!=['FLOW_HOLD']:raise ValueError('hold cannot be mixed with measurement')
 result=[]
 def add(b):
  for d in B[b]['depends_on']:add(d)
  if b not in result:result.append(b)
 for b in selected:add(b)
 return result

def sample_phases(kinds,s):return [k+':'+s for k in kinds]
def exchange(s):return sample_phases(['CLAMP','VERIFY_CLAMP','SWITCH_SAMPLE','SERVICE_EXCHANGE','OBSERVE_BUBBLES','REQUEST_ACQUISITION','READ_PAIR'],s)
def phases(b):
 if b=='PREPARE':return sum([sample_phases(['VERIFY_MATERIAL','TARE','WEIGH','MIX','LABEL_CAP','FILTER','RECORD_CUSTODY'],s) for s in SAMPLES],[])+['ARCHIVE','CLEAN_STORE']
 if b=='REFERENCE':return sum([sample_phases(['CHECK_REFERENCE','PRESENT_REFERENCE','READ_REFERENCE','CLEAN_REFERENCE','RECORD_CUSTODY'],s) for s in SAMPLES],[])+['ARCHIVE','CLEAN_STORE']
 if b=='CALIBRATE':return ['VERIFY_CARTRIDGE','DOCK_CARTRIDGE','VERIFY_ENCLOSURE']+sum([exchange(s) for s in TRAIN],[])+['FREEZE_CALIBRATION','ARCHIVE']
 if b=='INTERPOLATE':return sum([exchange(s) for s in TEST],[])+['BIND_RECORDS','ARCHIVE']
 if b=='REPEATABILITY':return exchange('test_a')+sample_phases(['REQUEST_ACQUISITION','READ_PAIR','REQUEST_ACQUISITION','READ_PAIR'],'test_a')+['BIND_RECORDS','ARCHIVE']
 if b=='DRIFT_NOISE':return ['LOG_TEMPERATURE','REQUEST_DARK','READ_DARK','LOG_TEMPERATURE','BIND_RECORDS','ARCHIVE']
 return ['HOLD_FLOW_CONFLICT','SAFE_ISOLATE','ARCHIVE','CLEAN_STORE']

def sequence(selected):
 ids=closure(selected);opt=[b for b in ids if b in ['CALIBRATE','INTERPOLATE','REPEATABILITY','DRIFT_NOISE']]
 return [(b,p) for b in ids for p in phases(b)+(TAIL if opt and b==opt[-1] else [])]

def binding(ep,profile,sample):
 return dict(episode_id=ep,run_id=ep+'_run_1',sample_id=sample,aliquot_id=sample+'_aliquot' if sample else None,parent_bottle_id=sample+'_bottle' if sample else None,reference_id=ep+'_'+sample+'_reference' if sample else None,reference_session=ep if sample else None,setup_version='synthetic_setup_v1',profile_id=profile,plate_id=PROFILES[profile][0],cartridge_id='synthetic_cartridge',mount_version='synthetic_mount_v1',calibration_id=ep+'_calibration',attempt_id='synthetic_attempt_1')

def phase_receipt(kind,s,record,branch):
 """Opaque qualified work receipts, not invented physical parameter values."""
 common={'record_origin':'authored_fixture_only','raw_receipt_id':record+'_phase'}
 details={
  'VERIFY_MATERIAL':{'materials':['water','sucrose'],'lot_identity_checked':True,'recipe_id':'synthetic_recipe_'+str(s)},
  'TARE':{'balance_id':'synthetic_balance','zero_observed':True,'container_id':str(s)+'_bottle'},
  'WEIGH':{'recipe_id':'synthetic_recipe_'+str(s),'mass_record_ids':[record+'_sucrose_mass',record+'_water_mass'],'mass_basis':'qualified_recipe_not_source_guessed','mass_transfer_accepted':True},
  'MIX':{'recipe_endpoint_id':'synthetic_mixing_endpoint','endpoint_observed':True},
  'LABEL_CAP':{'label_sample_id':s,'cap_closed_observed':True},
  'FILTER':{'filter_card_id':'U_FILTER','parent_bottle_id':str(s)+'_bottle','receiver_aliquot_id':str(s)+'_aliquot','compatibility_checked':True,'recovery_checked':True},
  'PRESENT_REFERENCE':{'aliquot_id':str(s)+'_aliquot','carryover_clearance_id':'synthetic_reference_clean'},
  'READ_REFERENCE':{'reference_instrument_id':'synthetic_refractometer','instrument_calibration_card':'U_REFERENCE','uncertainty_record_id':record+'_reference_uncertainty','wavelength_basis':'sodium_D_reference_equivalent'},
  'CLEAN_REFERENCE':{'qualified_cleanup_card':'U_CLEANUP','cleaning_observed':True,'sample_retained':True},
  'SERVICE_EXCHANGE':{'logical_service_job_id':record+'_exchange','numeric_pump_command_issued':False,'source_flow_disagreement_resolved':False,'carryover_clearance_id':record+'_carryover'},
  'FREEZE_CALIBRATION':{'fit_record_id':record+'_locked_fit','training_samples':TRAIN[:],'test_data_used':False,'numerical_fit_implemented':False},
  'REQUEST_DARK':{'closed_service_job_id':record+'_dark','laser_off_confirmation':True},
  'READ_DARK':{'channel_role':'dark_camera_record','sample_ri_estimate':None},
  'LOG_TEMPERATURE':{'temperature_observation_id':record+'_temperature','timestamp_record_id':record+'_timestamp','unit':'kelvin','numeric_tolerance_inferred':False},
  'INSPECT':{'cartridge_condition':'fixture_accepted','inspection_current':True},
  'ARCHIVE':{'immutable_attempt_preserved':True,'raw_records_retained':True},
  'CLEAN_STORE':{'qualified_cleanup_card':'U_CLEANUP','stock_and_aliquot_custody':'retained_for_downstream' if branch in ['PREPARE','REFERENCE'] else 'archived_and_stored','cleanup_observed':True},
 }
 common.update(details.get(kind,{'phase_observation':kind}));return common

def fixture(selected=None,profile='SPP5_532',episode_id='synthetic_episode_001'):
 selected=['FLOW_HOLD'] if selected is None else selected
 ids=closure(selected)
 if profile not in PROFILES:raise ValueError('unknown profile')
 seq=sequence(selected);opt=any(b in ids for b in ['CALIBRATE','INTERPOLATE','REPEATABILITY','DRIFT_NOISE']);events=[];obs={}
 cards={u:{'id':u,'revision':'synthetic_v1','authority':'fixture_author','qualified_for_fixture_only':True} for b in ids for u in B[b]['unknown_parameter_ids']}
 for n,(b,p) in enumerate(seq):
  eid='EV'+str(n+1);kind,_,s=p.partition(':');s=s or None;record='synthetic://'+episode_id+'/'+eid
  pair=kind=='READ_PAIR';dark=kind=='READ_DARK'
  obs[eid]=dict(phase_receipt=phase_receipt(kind,s,record,b),event_id=eid,job_id=b,phase=p,binding=binding(episode_id,profile,s),source_kind='synthetic_fixture',authority='fixture_author',accepted=True,qualified=True,stationary=True,custody_supported=True,clamp_closed=kind in ['VERIFY_CLAMP','SWITCH_SAMPLE'],clamp_observed=kind=='VERIFY_CLAMP',exchange_completed=kind=='SERVICE_EXCHANGE',bubbles='absent' if kind=='OBSERVE_BUBBLES' else 'not_observed',enclosure='closed',drift_alarm=False,reference_fresh=True,reference_riu=VALUES[s] if s else None,reference_wavelength_nm=589.29,frame_pair_id=record+'_pair' if pair else None,speckle_record_id=record+'_speckle' if pair else None,beam_record_id=record+'_beam' if pair else None,dark_record_id=record+'_dark' if dark else None,temperature_record_id=record+'_temperature',raw_record_id=record,record_hash=hashlib.sha256(record.encode()).hexdigest(),sequence_number=n+1,isolated=kind=='SAFE_ISOLATE',inspection_complete=kind=='INSPECT',archive_complete=kind=='ARCHIVE',cleanup_complete=kind=='CLEAN_STORE',calibration_invalidated=kind=='INVALIDATE_CALIBRATION')
  events.append(dict(event_id=eid,job_id=b,phase=p))
 ctx=dict(episode_id=episode_id,mode='synthetic_contract_only',production_authority=False,physical_execution=False,whole_paper_complete=False,fabrication_performed=False,selected_branches=selected,profile_id=profile,cards=cards,source_conflicts_preserved=CONFLICTS[:],source_flow_resolved=False,service_clearance='authored_fixture_only' if opt else None,calibration=dict(train_sample_ids=TRAIN[:],test_sample_ids=TEST[:],preprocessing='authored_locked_fixture_v1',fit_uses_test_data=False,domain_riu=[1.3328,1.3403],absolute_accuracy_claim=False,precision_pass_threshold=None,technical_repeats_are_independent=False,schedule_origin='authored_reduced_fixture',source_schedule_reproduced=False),observations=obs,terminal_status='safe_held' if ids==['FLOW_HOLD'] else 'synthetic_design_trace_complete')
 return ctx,events

def _validate(ctx,events):
 errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 if type(ctx) is not dict or type(events) is not list:return ['wrong outer types']
 selected=ctx.get('selected_branches');ids=closure(selected);profile=ctx.get('profile_id');ep=ctx.get('episode_id')
 if type(ep) is not str or not ep.startswith('synthetic_episode_') or profile not in PROFILES:return ['invalid episode/profile']
 canonical,_=fixture(selected,profile,ep)
 check(set(ctx)==set(canonical),'context schema drift')
 # Context contains no measurements: all control claims must be exactly typed and bounded.
 for k in canonical:
  if k not in ['observations']:check(same(ctx.get(k),canonical[k]),'invalid context '+k)
 observations=ctx.get('observations');seq=sequence(selected)
 if type(observations) is not dict:return ['observation registry type']
 check(len(events)==len(seq),'missing/extra events');check(set(observations)=={'EV'+str(n+1) for n in range(len(seq))},'observation registry mismatch')
 completed=set();reference_seen=set();pair_seen=set();prepared=set();clamp_state='unknown';switched=None;flow_sample=None;bubble_sample=None;pending=None;cal_active=False;docked=False;isolated=False;invalidated=False;closed=False;seen=set()
 for n,e in enumerate(events):
  if type(e) is not dict:errors.append('malformed actor event');continue
  check(set(e)=={'event_id','job_id','phase'},'actor observation/setting injection')
  eid=e.get('event_id');b=e.get('job_id');p=e.get('phase')
  if type(eid) is not str or type(b) is not str or type(p) is not str:errors.append('invalid actor types');continue
  check(eid=='EV'+str(n+1) and eid not in seen,'event replay/order');seen.add(eid)
  check(n<len(seq) and (b,p)==seq[n],'phase or branch order')
  o=observations.get(eid)
  if type(o) is not dict:errors.append('missing observation');continue
  expected=canonical['observations'].get(eid)
  if not expected:errors.append('extra observation');continue
  check(set(o)==set(expected),'observation schema drift')
  # Synthetic fixture identity, receipt labels and typed safe statuses are closed-world.
  for k in expected:
   check(same(o.get(k),expected[k]),'receipt mismatch '+k)
  kind,_,s=p.partition(':');s=s or None
  if b not in ids:errors.append('unknown job');continue
  if n==0 or seq[n-1][0]!=b:check(set(B[b]['depends_on'])<=completed,'dependency incomplete')
  if kind=='RECORD_CUSTODY' and b=='PREPARE':prepared.add(s)
  if kind=='READ_REFERENCE':
   check(s in prepared and o.get('reference_fresh') is True,'reference before prepared/fresh sample');reference_seen.add(s)
  if kind=='DOCK_CARTRIDGE':docked=True
  if kind=='CLAMP':clamp_state='awaiting_observation'
  if kind=='VERIFY_CLAMP':
   check(clamp_state=='awaiting_observation' and o.get('clamp_observed') is True and o.get('clamp_closed') is True,'clamp command is not observation');clamp_state='clamped'
  if kind=='SWITCH_SAMPLE':
   check(clamp_state=='clamped' and docked and o.get('clamp_closed') is True,'switch without verified clamp or dock');switched=s;flow_sample=None;bubble_sample=None
  if kind=='SERVICE_EXCHANGE':
   check(switched==s and clamp_state=='clamped' and ctx.get('service_clearance')=='authored_fixture_only' and 'U_FLOW' in ctx.get('cards',{}) and o.get('exchange_completed') is True,'exchange without qualified bounded service');flow_sample=s;clamp_state='open'
  if kind=='OBSERVE_BUBBLES':
   check(flow_sample==s and o.get('bubbles')=='absent','bubble/stable-flow guard');bubble_sample=s
  if kind=='REQUEST_ACQUISITION':
   check(docked and not closed and not isolated and bubble_sample==s and flow_sample==s and s in reference_seen and o.get('enclosure')=='closed' and o.get('drift_alarm') is False,'acquisition safety/reference guard')
   check(b=='CALIBRATE' or cal_active,'acquisition without active calibration')
   check(s in (TRAIN if b=='CALIBRATE' else TEST),'train/test role leak')
   v=o.get('reference_riu');check(type(v) is float and math.isfinite(v) and 1.3328<=v<=1.3403,'range/nonfinite guard');pending=s
  if kind=='READ_PAIR':
   check(pending==s,'read without requested acquisition');pending=None;pair_seen.add(s)
  if kind=='FREEZE_CALIBRATION':
   check(set(TRAIN)<=pair_seen and not cal_active,'incomplete or repeated fit');cal_active=True
  if kind=='REQUEST_DARK':check(cal_active and docked and not isolated,'dark service without current station')
  if kind=='SAFE_ISOLATE':isolated=True;flow_sample=None;bubble_sample=None
  if kind=='INVALIDATE_CALIBRATION':check(isolated and cal_active,'invalidation before isolation');cal_active=False;invalidated=True
  if kind=='UNDOCK':check(isolated and invalidated and docked,'unsafe retrieval or active calibration');docked=False
  if kind=='CLEAN_STORE' and (b=='FLOW_HOLD' or 'CALIBRATE' in ids and n==len(seq)-1):
   check(isolated and not docked and not cal_active,'unsafe closure');closed=True
  if n<len(seq) and (n==len(seq)-1 or seq[n+1][0]!=b):completed.add(b)
 check(completed==set(ids),'incomplete branch set')
 if 'CALIBRATE' in ids:check(closed and invalidated and not docked and not cal_active,'session not closed')
 if ids==['FLOW_HOLD']:check(closed and not pair_seen and not ctx.get('service_clearance'),'hold activated measurement')
 return sorted(set(errors))

def validate(ctx,events):
 try:return _validate(ctx,events)
 except (ValueError,TypeError,KeyError,AttributeError,IndexError,OverflowError,RecursionError):return ['malformed synthetic contract fails closed']
