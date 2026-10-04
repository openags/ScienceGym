"""Synthetic contract checks only. This module never authenticates production evidence or runs physics."""
from pathlib import Path
import copy, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
BRANCHES={b['id']:b for b in load('branches.json')['branches']}
STATIONS={s['id']:s for s in load('station_contracts.json')['stations']}
PHASES=['PREPARE','LOAD','VERIFY','RUN','READOUT','RETRIEVE','CLEANUP']
STATES=['allocated','prepared','loaded','verified','finished','readout_bound','retrieved','archived_safe']
AUTH='synthetic_authority_only'
def same(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'))==json.dumps(b,sort_keys=True,separators=(',',':'))
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def closure(root):
 out=[]
 def visit(i):
  if i not in BRANCHES:raise ValueError('unknown branch')
  for dep in BRANCHES[i]['required_branch_ids']:
   if dep not in out:visit(dep)
  if i not in out:out.append(i)
 visit(root);return out

def expected_dataset(root):
 if root.startswith('SIM_'):return {'capture_kind':'synthetic_model_fixture','profile':'numerical','frame_count':50,'frame_rate_hz':None,'exposure_ms':None,'timebase':'not_applicable'}
 if root in ['ACQUIRE15','TIS','CORRECTED']:return {'capture_kind':'synthetic_observation_fixture','profile':'lunar_15','frame_count':900,'frame_rate_hz':15,'exposure_ms':5,'timebase':'synthetic_UTC'}
 if root=='ACQUIRE_SHORT':return {'capture_kind':'synthetic_observation_fixture','profile':'short_30','frame_count':200,'frame_rate_hz':30,'exposure_ms':2,'timebase':'synthetic_UTC'}
 if root=='DAYTIME25':return {'capture_kind':'synthetic_observation_fixture','profile':'daytime_25','frame_count':3,'frame_rate_hz':25,'exposure_ms':'synthetic_qualified_unknown','timebase':'synthetic_UTC'}
 return {'capture_kind':'synthetic_observation_fixture','profile':'long_30','frame_count':7000 if root in ['PREDICT','FINETUNE','ABLATIONS','COVARIANCE'] else 1000,'frame_rate_hz':30,'exposure_ms':2,'timebase':'synthetic_UTC'}

def fixture(selected=None,whole=False,episode_id='synthetic_episode_1'):
 """Manufactured records for software tests. No real sensor/sample data is returned."""
 selected=list(BRANCHES) if whole else (selected or ['CORRECTED'])
 ctx={'episode_id':episode_id,'mode':'synthetic_bookkeeping_only','origin':'synthetic_fixture','authority_id':AUTH,'selected_branches':selected,'whole_design':whole,'plans':{},'cards':{},'controls':{},'records':{},'datasets':{},'calibrations':{},'splits':{},'conflict_resolutions':{},'archive_complete':True,'cleanup_complete':True,'actor_targets_exposed':False,'mounted_leases':{},'teardown_events':[]}
 events=[]
 for root in selected:
  dataset_id='fixture_dataset_'+root
  ds={'episode_id':episode_id,'dataset_id':dataset_id,'origin':'synthetic_fixture','independent_day_id':'synthetic_day_A',**expected_dataset(root)}
  ds['frame_ids']=[dataset_id+'/'+str(i) for i in range(ds['frame_count'])]
  ds['capture_segments']=[{'capture_id':dataset_id+'/capture_'+str(k),'first_index':k*1000,'last_exclusive':min((k+1)*1000,ds['frame_count']),'start_tick':k*2000,'interval_ticks':1} for k in range((ds['frame_count']+999)//1000)]
  ds['manifest_hash']=digest(ds);ctx['datasets'][dataset_id]=ds
  if 'MOUNT' in closure(root):ctx['mounted_leases'][root]={'episode_id':episode_id,'lease_id':'lease_'+root,'sensor_id':'payload_'+root,'mount_generation':1,'authority_id':AUTH,'origin':'synthetic_fixture','calibration_id':'cal_'+root+'::MOUNT','initial_state':'not_mounted'}
  for b_id in closure(root):
   b=BRANCHES[b_id];iid=root+'::'+b_id;cal='cal_'+iid
   ctx['calibrations'][cal]={'episode_id':episode_id,'authority_id':AUTH,'revision':'synthetic_v1','current':True,'dataset_id':dataset_id,'station_id':b['station_id']}
   plan={'episode_id':episode_id,'branch_instance_id':iid,'branch_id':b_id,'root_id':root,'dataset_id':dataset_id,'job_id':'job_'+iid,'attempt_id':'attempt_1','payload_id':'payload_'+root,'payload_version':1,'instrument_id':'instrument_'+b['station_id'],'station_id':b['station_id'],'port_id':STATIONS[b['station_id']]['port'],'pose_card_revision':'synthetic_pose_v1','calibration_id':cal,'algorithm_version':'synthetic_algorithm_v1','source_parameters':copy.deepcopy(b['source_parameters']),'parent_record_ids':['record_'+root+'::'+dep for dep in b['required_branch_ids']],'record_id':'record_'+iid,'origin':'synthetic_fixture'}
   ctx['plans'][iid]=plan
   for u in b['unknown_parameter_ids']:
    ctx['cards'][iid+'/'+u]={'episode_id':episode_id,'authority_id':AUTH,'revision':'synthetic_v1','qualified':True,'origin':'synthetic_fixture','branch_instance_id':iid,'parameter_id':u}
   for c in b['control_ids']:
    ctx['controls'][iid+'/'+c]={'episode_id':episode_id,'authority_id':AUTH,'passed':True,'origin':'synthetic_fixture','branch_instance_id':iid,'control_id':c}
   record={'episode_id':episode_id,'record_id':plan['record_id'],'branch_instance_id':iid,'dataset_id':dataset_id,'output_kind':b['output_kind'],'origin':'synthetic_fixture','authority_id':AUTH,'calibration_id':cal,'parent_record_ids':plan['parent_record_ids'],'payload':'Synthetic placeholder only; no measurement or simulation occurred.'}
   record['record_hash']=digest(record);ctx['records'][record['record_id']]=record
   if b_id in ['PREDICT','FINETUNE','ABLATIONS']:
    frames=ds['frame_ids']; split={'episode_id':episode_id,'selected_frame_ids':frames[:6000],'training_ids':frames[:5400],'test_ids':frames[5400:6000],'excluded_ids':frames[6000:],'input_length':5,'horizon_steps':1,'normalization_fit_ids':frames[:5400],'normalization_fitted_on':'training_only','window_policy':'within_capture_and_split_only','valid_test_target_indices':[i for i in range(5405,6000) if i%1000>=5],'valid_training_target_indices':[i for i in range(5,5400) if i%1000>=5],'training_loss_alignment':'shifted_sequence_[t-L+1,t]','system_aberration_removed':True,'noll_modes':[4,35],'origin':'synthetic_fixture'}
    if b_id=='FINETUNE':
     split['adaptation_dataset']={'episode_id':episode_id,'origin':'synthetic_fixture','dataset_id':'fixture_other_day','independent_day_id':'synthetic_day_B','frame_ids':['fixture_other_day/'+str(n) for n in range(600)],'train_indices':list(range(540)),'test_indices':list(range(540,600))}
    ctx['splits'][iid]=split
   for cf in load('source_conflicts.json')['conflicts']:
    if b_id in cf['affected_branch_ids']:ctx['conflict_resolutions'][iid+'/'+cf['id']]={'episode_id':episode_id,'status':'synthetic_test_scope_only','preserved_source_conflict':True,'authority_id':AUTH}
   for n,p in enumerate(PHASES):
    events.append({'episode_id':episode_id,'event_id':'event_'+str(len(events)+1),'sequence':len(events)+1,'phase':p,'pre_state':STATES[n],'post_state':STATES[n+1],**{k:plan[k] for k in ['episode_id','branch_instance_id','job_id','attempt_id','payload_id','payload_version','instrument_id','station_id','port_id','pose_card_revision','calibration_id','dataset_id','origin']},'record_id':record['record_id'],'record_hash':record['record_hash'],'authority_id':AUTH,'guard_closed':True,'hazard_isolated':True,'retained_support':True,'safe_release':True,'receipt_status':'accepted'})
  if 'MOUNT' in closure(root):
   for phase in ['CLOSE_JOBS','PARK_ISOLATE','DETACH_SUPPORTED','STORE_SAFE']:
    ctx['teardown_events'].append({'episode_id':episode_id,'root_id':root,'phase':phase,'lease_id':'lease_'+root,'mount_generation':1,'after_event_sequence':len(events),'authority_id':AUTH,'origin':'synthetic_fixture','all_jobs_closed':True,'safe_receipt':True})
 return ctx,events

def _validate(ctx,events):
 errors=[]
 def check(v,m):
  if not v:errors.append(m)
 if not isinstance(ctx,dict) or not isinstance(events,list):return ['invalid outer type']
 context_fields={'episode_id','mode','origin','authority_id','selected_branches','whole_design','plans','cards','controls','records','datasets','calibrations','splits','conflict_resolutions','archive_complete','cleanup_complete','actor_targets_exposed','mounted_leases','teardown_events'}
 episode_id=ctx.get('episode_id')
 check(isinstance(episode_id,str) and episode_id.startswith('synthetic_episode_') and len(episode_id)>18,'invalid synthetic episode identity')
 check(set(ctx)==context_fields,'context schema mismatch')
 check(ctx.get('mode')=='synthetic_bookkeeping_only' and ctx.get('origin')=='synthetic_fixture' and ctx.get('authority_id')==AUTH,'production evidence unsupported')
 roots=ctx.get('selected_branches',[])
 if not isinstance(roots,list) or not roots or len(set(roots))!=len(roots) or any(x not in BRANCHES for x in roots):return errors+['invalid selected branches']
 check(type(ctx.get('whole_design')) is bool,'whole flag type')
 if ctx.get('whole_design'):check(set(roots)==set(BRANCHES),'whole-design omission')
 expected={r+'::'+b for r in roots for b in closure(r)}
 plans=ctx.get('plans',{});datasets=ctx.get('datasets',{});records=ctx.get('records',{});cals=ctx.get('calibrations',{})
 check(set(plans)==expected,'dependency closure or branch-instance omission')
 check(set(datasets)=={'fixture_dataset_'+r for r in roots},'dataset registry mismatch')
 for root in roots:
  did='fixture_dataset_'+root;d=datasets.get(did,{})
  fields={'episode_id','dataset_id','origin','independent_day_id','capture_kind','profile','frame_count','frame_rate_hz','exposure_ms','timebase','frame_ids','capture_segments','manifest_hash'}
  check(set(d)==fields,'dataset fields mismatch')
  check(d.get('episode_id')==episode_id and d.get('dataset_id')==did and d.get('origin')=='synthetic_fixture' and d.get('independent_day_id')=='synthetic_day_A','dataset identity/origin mismatch')
  for k,v in expected_dataset(root).items():check(same(d.get(k),v),'dataset profile mismatch: '+k)
  check(d.get('frame_ids')==[did+'/'+str(i) for i in range(expected_dataset(root)['frame_count'])],'frame order/count/identity mismatch')
  check(same(d.get('capture_segments'),[{'capture_id':did+'/capture_'+str(k),'first_index':k*1000,'last_exclusive':min((k+1)*1000,expected_dataset(root)['frame_count']),'start_tick':k*2000,'interval_ticks':1} for k in range((expected_dataset(root)['frame_count']+999)//1000)]),'capture continuity metadata altered')
  check(d.get('manifest_hash')==digest({k:v for k,v in d.items() if k!='manifest_hash'}),'dataset hash mismatch')
 expected_cards=set();expected_controls=set();expected_splits=set();expected_conflicts=set();expected_cals=set();expected_records=set()
 plan_fields={'episode_id','branch_instance_id','branch_id','root_id','dataset_id','job_id','attempt_id','payload_id','payload_version','instrument_id','station_id','port_id','pose_card_revision','calibration_id','algorithm_version','source_parameters','parent_record_ids','record_id','origin'}
 for iid,p in plans.items():
  check(set(p)==plan_fields,'plan schema mismatch')
  if iid not in expected:continue
  root,bid=iid.split('::');b=BRANCHES[bid];did='fixture_dataset_'+root;cal='cal_'+iid;rid='record_'+iid
  truth={'episode_id':episode_id,'branch_instance_id':iid,'branch_id':bid,'root_id':root,'dataset_id':did,'job_id':'job_'+iid,'attempt_id':'attempt_1','payload_id':'payload_'+root,'payload_version':1,'instrument_id':'instrument_'+b['station_id'],'station_id':b['station_id'],'port_id':STATIONS[b['station_id']]['port'],'pose_card_revision':'synthetic_pose_v1','calibration_id':cal,'algorithm_version':'synthetic_algorithm_v1','source_parameters':b['source_parameters'],'parent_record_ids':['record_'+root+'::'+dep for dep in b['required_branch_ids']],'record_id':rid,'origin':'synthetic_fixture'}
  for k,v in truth.items():check(same(p.get(k),v),'plan binding mismatch: '+k)
  expected_cals.add(cal);expected_records.add(rid)
  check(same(cals.get(cal),{'episode_id':episode_id,'authority_id':AUTH,'revision':'synthetic_v1','current':True,'dataset_id':did,'station_id':b['station_id']}),'stale or crossed calibration')
  for u in b['unknown_parameter_ids']:
   key=iid+'/'+u;expected_cards.add(key)
   check(same(ctx['cards'].get(key),{'episode_id':episode_id,'authority_id':AUTH,'revision':'synthetic_v1','qualified':True,'origin':'synthetic_fixture','branch_instance_id':iid,'parameter_id':u}),'missing/stale/crossed unknown card')
  for c in b['control_ids']:
   key=iid+'/'+c;expected_controls.add(key)
   check(same(ctx['controls'].get(key),{'episode_id':episode_id,'authority_id':AUTH,'passed':True,'origin':'synthetic_fixture','branch_instance_id':iid,'control_id':c}),'missing or failed control')
  rec=records.get(rid,{})
  expected_rec={'episode_id':episode_id,'record_id':rid,'branch_instance_id':iid,'dataset_id':did,'output_kind':b['output_kind'],'origin':'synthetic_fixture','authority_id':AUTH,'calibration_id':cal,'parent_record_ids':truth['parent_record_ids'],'payload':'Synthetic placeholder only; no measurement or simulation occurred.'}
  expected_rec['record_hash']=digest(expected_rec)
  check(same(rec,expected_rec),'readout authority/hash/lineage/type mismatch or injected outcome')
  if bid in ['PREDICT','FINETUNE','ABLATIONS']:
   expected_splits.add(iid);s=ctx['splits'].get(iid,{})
   d=datasets.get(did,{});frames=d.get('frame_ids',[])
   st={'episode_id':episode_id,'selected_frame_ids':frames[:6000],'training_ids':frames[:5400],'test_ids':frames[5400:6000],'excluded_ids':frames[6000:],'input_length':5,'horizon_steps':1,'normalization_fit_ids':frames[:5400],'normalization_fitted_on':'training_only','window_policy':'within_capture_and_split_only','valid_test_target_indices':[i for i in range(5405,6000) if i%1000>=5],'valid_training_target_indices':[i for i in range(5,5400) if i%1000>=5],'training_loss_alignment':'shifted_sequence_[t-L+1,t]','system_aberration_removed':True,'noll_modes':[4,35],'origin':'synthetic_fixture'}
   if bid=='FINETUNE':st['adaptation_dataset']={'episode_id':episode_id,'origin':'synthetic_fixture','dataset_id':'fixture_other_day','independent_day_id':'synthetic_day_B','frame_ids':['fixture_other_day/'+str(n) for n in range(600)],'train_indices':list(range(540)),'test_indices':list(range(540,600))}
   check(same(s,st),'prediction split/leakage/mode/day mismatch')
   check(not (set(s.get('training_ids',[]))&set(s.get('test_ids',[]))),'prediction leakage')
  for cf in load('source_conflicts.json')['conflicts']:
   if bid in cf['affected_branch_ids']:
    key=iid+'/'+cf['id'];expected_conflicts.add(key)
    check(same(ctx['conflict_resolutions'].get(key),{'episode_id':episode_id,'status':'synthetic_test_scope_only','preserved_source_conflict':True,'authority_id':AUTH}),'source conflict silently resolved')
 for key,ex in [('cards',expected_cards),('controls',expected_controls),('splits',expected_splits),('conflict_resolutions',expected_conflicts),('calibrations',expected_cals),('records',expected_records)]:check(set(ctx.get(key,{}))==ex,'missing or extra registry: '+key)
 lease_roots={r for r in roots if 'MOUNT' in closure(r)}
 check(set(ctx['mounted_leases'])==lease_roots,'mounted lease omission')
 for r in lease_roots:check(same(ctx['mounted_leases'][r],{'episode_id':episode_id,'lease_id':'lease_'+r,'sensor_id':'payload_'+r,'mount_generation':1,'authority_id':AUTH,'origin':'synthetic_fixture','calibration_id':'cal_'+r+'::MOUNT','initial_state':'not_mounted'}),'mount lease/calibration identity mismatch')
 seen=set();progress={i:[] for i in expected};completed=set();live_leases=set();last_sequences={}
 event_fields={'episode_id','event_id','sequence','phase','pre_state','post_state','branch_instance_id','job_id','attempt_id','payload_id','payload_version','instrument_id','station_id','port_id','pose_card_revision','calibration_id','dataset_id','origin','record_id','record_hash','authority_id','guard_closed','hazard_isolated','retained_support','safe_release','receipt_status'}
 for seq,e in enumerate(events,1):
  if not isinstance(e,dict):errors.append('event not object');continue
  check(set(e)==event_fields,'event schema mismatch or injected result')
  eid=e.get('event_id');check(isinstance(eid,str) and bool(eid) and eid not in seen,'duplicate or missing event identity');seen.add(eid)
  check(type(e.get('sequence')) is int and e.get('sequence')==seq,'sequence gap or reorder')
  iid=e.get('branch_instance_id');p=plans.get(iid)
  if iid not in expected or p is None:errors.append('unregistered event plan');continue
  n=len(progress[iid]);check(n<7,'duplicate phase');
  if n>=7:continue
  check(e.get('phase')==PHASES[n] and e.get('pre_state')==STATES[n] and e.get('post_state')==STATES[n+1],'phase/state order mismatch')
  for k in ['episode_id','branch_instance_id','job_id','attempt_id','payload_id','payload_version','instrument_id','station_id','port_id','pose_card_revision','calibration_id','dataset_id','origin','record_id']:check(same(e.get(k),p.get(k)),'event plan mismatch: '+k)
  rec=records.get(p.get('record_id'),{})
  check(e.get('record_hash')==rec.get('record_hash') and e.get('authority_id')==AUTH,'untrusted readout')
  check(all(e.get(k) is True for k in ['guard_closed','hazard_isolated','retained_support','safe_release']),'unsafe service/custody state')
  check(e.get('receipt_status')=='accepted','failed attempt cannot advance')
  for par in p.get('parent_record_ids',[]):check(par.removeprefix('record_') in completed,'parent used before completion')
  if p['branch_id']=='MOUNT' and e.get('phase')=='RUN':live_leases.add(p['root_id'])
  if p['branch_id'].startswith('ACQUIRE'):check(p['root_id'] in live_leases,'acquisition without mounted lease')
  last_sequences[p['root_id']]=seq
  progress[iid].append(e.get('phase'))
  if n==6:completed.add(iid)
 for iid in expected:check(progress[iid]==PHASES,'missing phase: '+iid)
 teardown=[]
 for r in roots:
  if r in lease_roots:
   for phase in ['CLOSE_JOBS','PARK_ISOLATE','DETACH_SUPPORTED','STORE_SAFE']:teardown.append({'episode_id':episode_id,'root_id':r,'phase':phase,'lease_id':'lease_'+r,'mount_generation':1,'after_event_sequence':last_sequences.get(r),'authority_id':AUTH,'origin':'synthetic_fixture','all_jobs_closed':True,'safe_receipt':True})
 check(same(ctx['teardown_events'],teardown),'early/missing/unsafe/unbound teardown')
 check(ctx.get('archive_complete') is True and ctx.get('cleanup_complete') is True,'archive/cleanup incomplete')
 check(ctx.get('actor_targets_exposed') is False,'actor target leakage')
 return errors

def validate(context,events):
 try:errors=_validate(context,events)
 except (KeyError,TypeError,ValueError,IndexError,AttributeError) as exc:errors=['malformed fixture: '+type(exc).__name__]
 return {'passed':not errors,'errors':errors,'validation_kind':'synthetic_bookkeeping_only','production_accepted':False,'physics_or_instrument_run':False}
