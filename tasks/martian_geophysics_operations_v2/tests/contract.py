"""Offline synthetic custody-contract verifier. No drivers, source data or physics."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
BRANCHES={b['id']:b for b in load('branches.json')['branches']}
DIGITAL={'measurement_analysis','numerical_analysis','data_curation'}
CONFLICTS={c['id']:c for c in load('source_conflicts.json')['conflicts']}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def same(a,b):return type(a) is type(b) and digest(a)==digest(b)
def closure(selected):
 out=set();active=set()
 def visit(b):
  if b not in BRANCHES:raise ValueError('unknown branch')
  if b in active:raise ValueError('dependency cycle')
  if b in out:return
  active.add(b)
  for d in BRANCHES[b]['required_branch_ids']:visit(d)
  active.remove(b);out.add(b)
 for b in selected:visit(b)
 return out

def policy(branch):
 """Source-preservation rules, not source-result values or model outputs."""
 return {'temperature_correction':'unresolved','sample_identity_conflict':'unresolved',
 'nominal_correction_final_separate':True,'missing_shear':'unavailable_not_zero',
 'secondary_echo':'buffer_reverberation_not_sample_shear',
 'S3631_melt_origin':'mass_balance_calculated','H6050_temperature':'no_thermocouple_method_unqualified',
 'spot_count_unit':'analytical_spots_not_runs','regions':['S3630:cold','S3630:warm','central','buffer_adjacent'],
 'mode_methods':['pixel_analysis','mass_balance'],'redox':'qualitative_at_or_below_IW_no_precise_melt_value',
 'parent_assignment':'unresolved_requires_U_PARENTMAP',
 'model_scope':'numerical_only' if BRANCHES[branch]['classification']=='numerical_analysis' else 'record_or_service_design',
 'Monte_Carlo_variants':'source_specific_not_collapsed','main_pixels':'unverified'}

def fixture(selected=None,mode='selected_branch_design'):
 selected=['SEM'] if selected is None else selected
 ids=closure(selected);jobs={};records={};lineage={};events=[];plans={};alloc={};controls={};cards={}
 for b in BRANCHES:
  if b not in ids:continue
  spec=BRANCHES[b];jid='J_'+b;sid='synthetic_'+b;digital=spec['classification'] in DIGITAL
  route='powder' if b=='GRAPHITE_FEED' or b.startswith('EXSITU_') else ('digital' if digital else 'registered_physical')
  parents=['J_'+d for d in spec['required_branch_ids']]
  plans[b]={'branch_id':b,'job_ids':[jid],'phase_order':spec['phase_order'],'instance_count':1,'count_origin':'authored_synthetic_not_source_replicates'}
  alloc[b]={'branch_id':b,'specimen_id':sid,'material_route':route,'cohort_ids':spec['cohort_ids'],'parent_assignment':'unresolved_requires_U_PARENTMAP'}
  rid='REC_'+b
  rec={'record_id':rid,'source_kind':'synthetic_fixture','job_id':jid,'specimen_id':sid,'branch_id':b,'run_ids':spec['cohort_ids'],'policy':policy(b),'physical_observation':False,'numerical_reproduction':False,'measurement_values':None,'attempt_ids':['A1_'+b],'failures':[]}
  records[rid]=rec
  j={'job_id':jid,'branch_id':b,'specimen_id':sid,'carrier_id':'C_'+b,'station_id':spec['station_id'],'input_version':1,'output_version':2,'parents':parents,'record_id':rid,'record_hash':digest(rec),'authority_id':'synthetic_evaluator','source_kind':'synthetic_fixture','card_revision':'fixture_v1','calibration_id':'CAL_'+spec['station_id'],'fixture_id':'FIX_'+spec['station_id'],'attempt_id':'A1_'+b,'receipt_status':'synthetic_only','qualified':False,'closed_service':not digital,'safe_release':'synthetic_only','damage_state':'synthetic_intact','conflict_state':'unresolved','real_execution':False}
  jobs[jid]=j
  lineage[sid]={'specimen_id':sid,'parent_ids':parents,'branch_id':b,'cohort_id':spec['cohort_ids'],'material_route':route,'carrier_id':'C_'+b,'input_version':1,'output_version':2,'section_id':'SECTION_CHILD' if b in ['SECTION','SEM','EPMA','MODES'] else None,'region_id':'distinct_registered_regions' if b in ['SEM','EPMA','MODES'] else None,'run_id':spec['cohort_ids'],'record_ids':[rid],'destructive_parent_retired':b=='SECTION'}
  for u in spec['unknown_parameter_ids']:cards[u]={'card_id':u,'authority_id':'synthetic_evaluator','revision':'fixture_v1','mode':'synthetic_placeholder','real_qualification':False,'binding':None}
  for c in spec['control_ids']:controls[c]={'control_id':c,'source_kind':'synthetic_fixture','passed_shape_check':True,'real_control_pass':False}
  for phase in spec['phase_order']:
   e={k:j[k] for k in ['job_id','branch_id','specimen_id','carrier_id','station_id','input_version','output_version','record_id','record_hash','authority_id','source_kind','card_revision','calibration_id','fixture_id','attempt_id','receipt_status','safe_release','conflict_state','real_execution']}
   e.update(event_id='EV_'+str(len(events)+1),sequence=len(events)+1,phase=phase,safe_exchange='synthetic_only',hazard_isolated='synthetic_only',guard_closed='synthetic_only',actor_values=None)
   events.append(e)
 context={'fixture_only':True,'authority_id':'synthetic_evaluator','mode':mode,'selected_branches':selected,'plans':plans,'jobs':jobs,'cards':cards,'controls':controls,'lineage':lineage,'allocations':alloc,'records':records,'conflicts':{c:'unresolved' for c in CONFLICTS},'archive':{'record_ids':sorted(records),'failed_attempt_ids':[],'cleanup_complete':'synthetic_only'},'actor_source_targets_exposed':False,'production_authentication_available':False}
 return context,events

EVENT_KEYS={'job_id','branch_id','specimen_id','carrier_id','station_id','input_version','output_version','record_id','record_hash','authority_id','source_kind','card_revision','calibration_id','fixture_id','attempt_id','receipt_status','safe_release','conflict_state','real_execution','event_id','sequence','phase','safe_exchange','hazard_isolated','guard_closed','actor_values'}
CONTEXT_KEYS={'fixture_only','authority_id','mode','selected_branches','plans','jobs','cards','controls','lineage','allocations','records','conflicts','archive','actor_source_targets_exposed','production_authentication_available'}
JOB_KEYS={'job_id','branch_id','specimen_id','carrier_id','station_id','input_version','output_version','parents','record_id','record_hash','authority_id','source_kind','card_revision','calibration_id','fixture_id','attempt_id','receipt_status','qualified','closed_service','safe_release','damage_state','conflict_state','real_execution'}

def _validate(ctx,events):
 errors=[]
 def check(ok,message):
  if not ok:errors.append(message)
 if not isinstance(ctx,dict) or not isinstance(events,list):return ['wrong container type']
 check(set(ctx)==CONTEXT_KEYS,'context schema')
 check(ctx.get('fixture_only') is True,'production execution unsupported')
 check(ctx.get('authority_id')=='synthetic_evaluator','untrusted authority')
 check(ctx.get('actor_source_targets_exposed') is False,'source targets exposed to actor')
 check(ctx.get('production_authentication_available') is False,'unimplemented production authentication')
 check(ctx.get('mode') in ['selected_branch_design','whole_physical_campaign','whole_paper_design'],'unknown mode')
 selected=ctx.get('selected_branches')
 if not isinstance(selected,list) or not selected or any(not isinstance(x,str) for x in selected):return errors+['invalid selected branches']
 check(len(set(selected))==len(selected),'duplicate selection')
 try:ids=closure(selected)
 except ValueError:return errors+['unknown branch or dependency cycle']
 if ctx['mode']=='whole_paper_design':check(ids==set(BRANCHES),'whole paper omitted branch')
 if ctx['mode']=='whole_physical_campaign':check({b for b in BRANCHES if BRANCHES[b]['classification']!='numerical_analysis'}<=ids,'whole physical campaign omitted branch')
 for key in ['plans','jobs','cards','controls','lineage','allocations','records','conflicts','archive']:
  if not isinstance(ctx.get(key),dict):return errors+['malformed '+key]
 jobs=ctx['jobs'];records=ctx['records'];lineage=ctx['lineage'];alloc=ctx['allocations']
 check(set(ctx['plans'])==ids,'plan dependency closure')
 check(set(alloc)==ids,'allocation coverage')
 check(set(jobs)=={'J_'+b for b in ids},'job coverage')
 check(set(records)=={'REC_'+b for b in ids},'record coverage')
 check(set(lineage)=={'synthetic_'+b for b in ids},'lineage coverage')
 check(ctx['conflicts']=={c:'unresolved' for c in CONFLICTS},'source conflict resolved or omitted')
 required_cards={u for b in ids for u in BRANCHES[b]['unknown_parameter_ids']}
 check(set(ctx['cards'])==required_cards,'required cards missing or extra')
 for u,c in ctx['cards'].items():check(same(c,{'card_id':u,'authority_id':'synthetic_evaluator','revision':'fixture_v1','mode':'synthetic_placeholder','real_qualification':False,'binding':None}),'card qualified, stale or forged '+str(u))
 required_controls={u for b in ids for u in BRANCHES[b]['control_ids']}
 check(set(ctx['controls'])==required_controls,'control coverage')
 for u,c in ctx['controls'].items():check(same(c,{'control_id':u,'source_kind':'synthetic_fixture','passed_shape_check':True,'real_control_pass':False}),'invalid control '+str(u))
 for b in ids:
  spec=BRANCHES[b];j=jobs.get('J_'+b,{})
  check(same(ctx['plans'].get(b),{'branch_id':b,'job_ids':['J_'+b],'phase_order':spec['phase_order'],'instance_count':1,'count_origin':'authored_synthetic_not_source_replicates'}),'invalid plan or fabricated replicates '+b)
  check(set(j)==JOB_KEYS,'job schema '+b)
  if not j:continue
  digital=spec['classification'] in DIGITAL;sid='synthetic_'+b;route='powder' if b=='GRAPHITE_FEED' or b.startswith('EXSITU_') else ('digital' if digital else 'registered_physical')
  parents=['J_'+d for d in spec['required_branch_ids']]
  check(j['job_id']=='J_'+b and j['branch_id']==b and j['specimen_id']==sid,'job identity '+b)
  check(j['carrier_id']=='C_'+b and j['station_id']==spec['station_id'],'carrier or station '+b)
  check(type(j['input_version']) is int and type(j['output_version']) is int and j['input_version']==1 and j['output_version']==2,'specimen version '+b)
  check(j['parents']==parents,'parent dependency linkage '+b)
  check(j['authority_id']=='synthetic_evaluator' and j['source_kind']=='synthetic_fixture','job evidence authority '+b)
  check(j['card_revision']=='fixture_v1' and j['fixture_id']=='FIX_'+spec['station_id'] and j['calibration_id']=='CAL_'+spec['station_id'],'job calibration '+b)
  check(j['attempt_id']=='A1_'+b and j['receipt_status']=='synthetic_only','attempt or receipt '+b)
  check(j['qualified'] is False and j['real_execution'] is False,'real qualification or actuation '+b)
  check(j['closed_service'] is (not digital),'closed service class '+b)
  check(j['safe_release']=='synthetic_only' and j['damage_state']=='synthetic_intact','unsafe release or damaged specimen '+b)
  check(j['conflict_state']=='unresolved','source gate bypass '+b)
  check(same(alloc.get(b),{'branch_id':b,'specimen_id':sid,'material_route':route,'cohort_ids':spec['cohort_ids'],'parent_assignment':'unresolved_requires_U_PARENTMAP'}),'route or cohort allocation '+b)
  expected_lineage={'specimen_id':sid,'parent_ids':parents,'branch_id':b,'cohort_id':spec['cohort_ids'],'material_route':route,'carrier_id':'C_'+b,'input_version':1,'output_version':2,'section_id':'SECTION_CHILD' if b in ['SECTION','SEM','EPMA','MODES'] else None,'region_id':'distinct_registered_regions' if b in ['SEM','EPMA','MODES'] else None,'run_id':spec['cohort_ids'],'record_ids':['REC_'+b],'destructive_parent_retired':b=='SECTION'}
  check(same(lineage.get(sid),expected_lineage),'material/section/region ancestry '+b)
  r=records.get('REC_'+b,{})
  expected_rec={'record_id':'REC_'+b,'source_kind':'synthetic_fixture','job_id':'J_'+b,'specimen_id':sid,'branch_id':b,'run_ids':spec['cohort_ids'],'policy':policy(b),'physical_observation':False,'numerical_reproduction':False,'measurement_values':None,'attempt_ids':['A1_'+b],'failures':[]}
  check(same(r,expected_rec),'record provenance, source policy or fabricated measurement '+b)
  check(j['record_id']=='REC_'+b and j['record_hash']==digest(r),'record hash '+b)
 # Trace is untrusted. It cannot add parameters, resolve conflicts or self-certify service evidence.
 expected_cells={(b,p) for b in ids for p in BRANCHES[b]['phase_order']};seen=[];seen_event_ids=set();by_branch={}
 for n,e in enumerate(events,1):
  if not isinstance(e,dict):errors.append('event not object');continue
  check(set(e)==EVENT_KEYS,'event unknown or missing field')
  check(e.get('event_id')=='EV_'+str(n) and e.get('event_id') not in seen_event_ids,'event ID replay')
  seen_event_ids.add(e.get('event_id'));check(type(e.get('sequence')) is int and e.get('sequence')==n,'sequence gap or wrong type')
  b=e.get('branch_id');phase=e.get('phase')
  if b not in ids:errors.append('unknown event branch');continue
  seen.append((b,phase));by_branch.setdefault(b,[]).append((n,phase))
  j=jobs.get(e.get('job_id'),{})
  check(bool(j) and j.get('branch_id')==b,'unknown or crossed job')
  for k in EVENT_KEYS & JOB_KEYS:check(same(e.get(k),j.get(k)),'event receipt binding '+k)
  for k in ['safe_exchange','hazard_isolated','guard_closed']:check(e.get(k)=='synthetic_only','unsafe exchange '+k)
  check(e.get('actor_values') is None,'actor injected values or source outcomes')
 check(len(seen)==len(set(seen)) and set(seen)==expected_cells,'phase missing, duplicated or extra')
 for b in ids:
  observed=by_branch.get(b,[])
  check([p for _,p in observed]==BRANCHES[b]['phase_order'],'phase order '+b)
  if not observed:continue
  for parent in BRANCHES[b]['required_branch_ids']:
   p=by_branch.get(parent,[])
   check(bool(p) and p[-1][0]<observed[0][0],'dependency event order '+b)
 check(same(ctx['archive'],{'record_ids':sorted(records),'failed_attempt_ids':[],'cleanup_complete':'synthetic_only'}),'archive omission or cleanup')
 return errors

def json_types(value):
 if type(value) in [str,bool,int,type(None)]:return True
 if type(value) is float:return math.isfinite(value)
 if type(value) is list:return all(json_types(v) for v in value)
 if type(value) is dict:return all(type(k) is str and json_types(v) for k,v in value.items())
 return False

def validate(ctx,events):
 try:
  if not json_types([ctx,events]):raise TypeError("non-JSON type")
  json.dumps([ctx,events],allow_nan=False)
  errors=_validate(ctx,events)
 except (ValueError,TypeError,KeyError,AttributeError,IndexError,RecursionError) as exc:errors=['malformed input: '+type(exc).__name__]
 return {'passed':not errors,'status':'synthetic_contract_pass' if not errors else 'rejected','errors':errors,'real_execution':False,'source_conflicts_resolved':False}
