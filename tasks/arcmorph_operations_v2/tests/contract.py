"""Original finite synthetic contract model. No hardware, image, physics or source-model code."""
from pathlib import Path
import json,hashlib,math,re
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[1]
def read(n):return json.loads((ROOT/n).read_text())
OPS={x['id']:x for x in read('operations.json')['operations']}
BRANCHES={x['id']:x for x in read('branches.json')['physical_routes']}
CONFLICTS={x['id']:x for x in read('source_conflicts.json')['conflicts']}
UNKNOWNS={x['id']:x for x in read('unknown_parameters.json')['unknowns']}
CONTEXT=read('lineage_contract.json')['context_keys']
OUTCOMES=('METADATA_OK','QUALIFICATION_HOLD','DATA_HOLD','SAFE_RELEASE_HOLD')
FIXTURE_IDS=tuple(r+':'+o for r in (*BRANCHES,'PHOTO_ANALYSIS','CLOSEOUT') for o in OUTCOMES)
class ContractError(ValueError):pass
def require(ok,msg):
 if not ok:raise ContractError(msg)
def exact(d,keys):require(type(d) is dict and set(d)==set(keys),'exact fields required')
def string(s):require(type(s) is str and 0<len(s)<=256,'bounded nonempty string');return s
def finite(x):
 require(type(x) in (int,float),'real scalar, not boolean or string')
 try:y=float(x)
 except (OverflowError,ValueError):raise ContractError('bounded scalar')
 require(math.isfinite(y),'finite scalar');return y
def canonical(x):
 try:return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
 except (ValueError,TypeError,OverflowError):raise ContractError('canonical bounded JSON')
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def sha(s):require(type(s) is str and re.fullmatch('[0-9a-f]{64}',s) is not None,'SHA-256 identity');return s
def synthetic(r):require(r.get('synthetic_only') is True,'synthetic fixture required')
def scope_holds(op,family,claims,unresolved=None):
 require(op in OPS,'known operation');require(family in ('CS1','CS2','CS3','CS4','PP'),'known physical family');require(type(claims) is list and all(type(v) is str for v in claims),'claim list')
 ids=set(UNKNOWNS) if unresolved is None else set(unresolved);require(ids<=set(UNKNOWNS),'known unresolved inputs')
 c=[x['id'] for x in CONFLICTS.values() if op in x['operation_ids'] and ('ALL' in x['family_scope'] or family in x['family_scope']) and set(claims)&set(x['claim_scope'])]
 u=sorted(ids&set(OPS[op]['unknown_ids']))
 claim_specific={'U11':{'model_comparison','quantitative_shear_oracle','source_matched_geometry'},'U14':{'source_raw_correspondence'}}
 u=[key for key in u if key not in claim_specific or set(claims)&claim_specific[key]]
 return {'conflicts':c,'unknowns':u,'can_record_supported_hold':True,'can_perform_physical_action':False}
def custody_transition(before,after):
 keys=('stock_id','specimen_id','family_id','drawing_revision','carrier_id','station_id','revision','history','mounted','loaded','supported','synthetic_only')
 for r in (before,after):
  exact(r,keys);synthetic(r)
  for k in ('stock_id','specimen_id','family_id','drawing_revision','carrier_id','station_id'):string(r[k])
  require(type(r['revision']) is int and r['revision']>=0,'nonnegative revision')
  require(type(r['history']) is list and all(type(x) is str and x for x in r['history']),'history list')
  for k in ('mounted','loaded','supported'):require(type(r[k]) is bool,'exact boolean state')
 for k in ('stock_id','specimen_id','family_id','drawing_revision'):require(before[k]==after[k],'immutable parentage '+k)
 require(after['revision']==before['revision']+1,'one appended revision')
 require(after['history'][:len(before['history'])]==before['history'] and len(after['history'])>len(before['history']),'append-only conditioning history')
 require(before['supported'] and after['supported'],'supported custody')
 if before['station_id']!=after['station_id']:
  require(not any(r[k] for r in (before,after) for k in ('mounted','loaded')),'no loaded/mounted transport');require(before['carrier_id']==after['carrier_id'],'retained carrier')
 return {'custody_valid_synthetic':True,'physical_transport':False}
def service_handoff(r):
 exact(r,('stock_id','output_parent_stock_id','job_id','completed_job_id','drawing_revision','output_drawing_revision','receipt_role','completed','safe_release','supported','synthetic_only'));synthetic(r)
 for a,b in [('stock_id','output_parent_stock_id'),('job_id','completed_job_id'),('drawing_revision','output_drawing_revision')]:string(r[a]);require(r[a]==r[b],'service lineage mismatch')
 require(r['receipt_role']=='independent_completion','request is not completion')
 require(all(r[k] is True for k in ('completed','safe_release','supported')),'service output remains held')
 return {'synthetic_handoff_valid':True,'fabrication_executed':False}
def fold_ledger(plan,records):
 exact(plan,('plan_id','family_id','drawing_revision','edges','depends_on','synthetic_only'));synthetic(plan)
 for k in ('plan_id','family_id','drawing_revision'):string(plan[k])
 e=plan['edges'];require(type(e) is list and len(e)>0 and len(e)==len(set(e)),'unique nonempty edge plan')
 require(type(plan['depends_on']) is dict and set(plan['depends_on'])==set(e),'dependency coverage')
 for edge in e:
  string(edge);d=plan['depends_on'][edge];require(type(d) is list and len(d)==len(set(d)) and set(d)<=set(e) and edge not in d,'valid edge predecessors')
 require(type(records) is list and len(records)==len(e),'complete edge records, not service-only fold')
 seen=set()
 for r in records:
  exact(r,('edge_id','plan_id','drawing_revision','actions','inspection','receipt_id','synthetic_only'));synthetic(r)
  edge=r['edge_id'];require(edge in e and edge not in seen,'edge exactly once');require(set(plan['depends_on'][edge])<=seen,'dependency ordered folds')
  require(r['plan_id']==plan['plan_id'] and r['drawing_revision']==plan['drawing_revision'],'fold plan revision')
  require(r['actions']==['support','engage','bounded_fold','release','inspect'],'complete manual edge sequence');require(r['inspection']=='accepted_synthetic','edge inspection accepted');string(r['receipt_id']);seen.add(edge)
 require(len({x['receipt_id'] for x in records})==len(records),'distinct fold receipts')
 return {'fold_ledger_complete':True,'physical_folding':False}
def lease_transition(leases,r):
 exact(r,('action','device_id','lease_id','specimen_id','job_id','safe_release','supported','synthetic_only'));synthetic(r)
 require(type(leases) is dict,'lease ledger');state=deepcopy(leases)
 for k in ('device_id','lease_id','specimen_id','job_id'):string(r[k])
 d=r['device_id']
 if r['action']=='acquire':
  require(d not in state,'exclusive device lease');require(all(x['lease_id']!=r['lease_id'] for x in state.values()),'unique live lease ID');require(r['supported'] is True,'supported acquisition')
  state[d]={k:r[k] for k in ('lease_id','specimen_id','job_id')}
 elif r['action']=='release':
  require(d in state and state[d]=={k:r[k] for k in ('lease_id','specimen_id','job_id')},'matching live lease required');require(r['safe_release'] is True and r['supported'] is True,'supported safe release evidence');del state[d]
 else:raise ContractError('known lease action')
 return state
def calibration(r,current):
 exact(r,('calibration_id','revisions','reference_ids','valid_interval','role','synthetic_only'));synthetic(r);string(r['calibration_id'])
 required={'front_camera','front_lens','front_mount','side_camera','side_lens','side_mount','fixture','height_reference','scale_reference'}
 require(type(current) is dict and set(current)==required and all(type(v) is str and v for v in current.values()),'full current device revisions')
 require(current['front_camera']!=current['side_camera'] and current['front_lens']!=current['side_lens'],'distinct camera and lens identities');require(current['height_reference']!=current['scale_reference'],'distinct reference identities');require(r['revisions']==current,'stale calibration revision');require(r['role']=='independent_calibration','calibration authority')
 require(type(r['reference_ids']) is list and len(r['reference_ids'])==2 and len(set(r['reference_ids']))==2 and all(type(x) is str and x for x in r['reference_ids']),'two distinct references')
 require(set(r['reference_ids'])=={current['height_reference'],current['scale_reference']},'calibration reference identity binding')
 interval=r['valid_interval'];require(type(interval) is list and len(interval)==2,'calibration interval');a,b=map(finite,interval);require(a<b,'positive calibration interval')
 return True
def capture_pair(rows,token,cal,current):
 exact(token,('token_id','specimen_id','configuration_revision','calibration_id','lock_interval','active','all_locks','stable','synthetic_only'));synthetic(token)
 for k in ('token_id','specimen_id','configuration_revision','calibration_id'):string(token[k])
 require(all(token[k] is True for k in ('active','all_locks','stable')),'live locked stable token')
 require(type(token['lock_interval']) is list and len(token['lock_interval'])==2,'lock interval');lo,hi=map(finite,token['lock_interval']);require(lo<hi,'positive lock interval')
 calibration(cal,current);require(token['calibration_id']==cal['calibration_id'],'token calibration')
 require(type(rows) is list and len(rows)==2,'two complete views');require({r.get('view_role') for r in rows}=={'front','side'},'orthogonal view roles')
 for r in rows:
  exact(r,('capture_id','camera_id','lens_id','view_role','specimen_id','configuration_revision','token_id','calibration_id','file_hash','time','quality_ok','evidence_kind','synthetic_only'));synthetic(r)
  for k in ('capture_id','camera_id','lens_id'):string(r[k])
  for k in ('specimen_id','configuration_revision','token_id','calibration_id'):require(r[k]==token[k],'pair identity or revision mismatch '+k)
  require(r['camera_id']==current[r['view_role']+'_camera'] and r['lens_id']==current[r['view_role']+'_lens'],'capture camera/lens bound to calibration');sha(r['file_hash']);t=finite(r['time']);require(lo<=t<=hi and cal['valid_interval'][0]<=t<=cal['valid_interval'][1],'time outside lock or calibration')
  require(r['quality_ok'] is True and r['evidence_kind']=='synthetic_observation','valid independent raw observation required')
 require(len({r['capture_id'] for r in rows})==len({r['camera_id'] for r in rows})==len({r['file_hash'] for r in rows})==2,'independent capture/device/file identities')
 return {'pair_valid_synthetic':True,'actual_images_observed':False}
def unmount(r,current_mount):
 exact(current_mount,('fixture_kind','fixture_id','specimen_id','lease_id','mounted'));require(current_mount['mounted'] is True,'independent live mount required')
 exact(r,('fixture_kind','fixture_id','specimen_id','operation_id','lease_id','load_removed','safe_release','supported','mounts_detached','fixture_empty','carrier_occupied','token_invalidated','synthetic_only'));synthetic(r);string(r['lease_id'])
 for k in ('fixture_kind','fixture_id','specimen_id','lease_id'):string(current_mount[k]);require(r[k]==current_mount[k],'unmount must match actual live fixture and lease '+k)
 require(r['fixture_kind'] in ('corner','rigid'),'known mount type');require(r['operation_id']==('R22' if r['fixture_kind']=='corner' else 'R30'),'wrong unmount operation')
 require(all(r[k] is True for k in ('load_removed','safe_release','supported','mounts_detached','fixture_empty','carrier_occupied','token_invalidated')),'unmount evidence incomplete')
 return {'lease_may_close_synthetic':True,'physical_unload':False}
def repeat_ledger(rows):
 require(type(rows) is list and len(rows)>0,'nonempty series ledger');seen=set();parents={};series={}
 for r in rows:
  exact(r,('series_id','specimen_id','stock_id','configuration_id','attempt_id','pair_id','kind','synthetic_only'));synthetic(r)
  for k in ('series_id','specimen_id','stock_id','configuration_id','attempt_id','pair_id'):string(r[k])
  require(r['kind'] in ('source_aligned_slot','authored_technical_repeat'),'declared repetition kind');require(r['pair_id'] not in seen,'pair not reused');seen.add(r['pair_id'])
  require(r['specimen_id'] not in parents or parents[r['specimen_id']]==r['stock_id'],'specimen stock cannot change');parents[r['specimen_id']]=r['stock_id']
  require(r['series_id'] not in series or series[r['series_id']]==r['specimen_id'],'replacement specimen starts new series');series[r['series_id']]=r['specimen_id']
 require(len({(r['series_id'],r['configuration_id'],r['attempt_id']) for r in rows})==len(rows),'duplicate attempt')
 return {'distinct_specimens':len(parents),'configuration_slots':len({(r['series_id'],r['configuration_id']) for r in rows}),'accepted_pairs':len(rows),'statistical_independence_established':False,'source_repeats_established':False}
def observables(r):
 exact(r,('pair_id','raw_hashes','height','interior_radius','exterior_radius','uncertainties','units','method_id','kind','synthetic_only'));synthetic(r);string(r['pair_id']);string(r['method_id'])
 require(r['kind']=='synthetic_observation' and r['units']=='m','new measurement class and units')
 require(type(r['raw_hashes']) is list and len(r['raw_hashes'])==2 and len(set(r['raw_hashes']))==2,'two raw parents')
 for x in r['raw_hashes']:sha(x)
 exact(r['uncertainties'],('height','interior_radius','exterior_radius'))
 for k in ('height','interior_radius','exterior_radius'):require(finite(r[k])>0 and finite(r['uncertainties'][k])>0,'positive observation and declared uncertainty')
 require(r['interior_radius']<=r['exterior_radius'],'named inner/outer ordering')
 return {'observables_separated':True,'curve_agreement_tested':False,'scientific_reproduction':False}
def retry(before,after):
 keys=('attempt_id','specimen_id','series_id','token_id','capture_ids','raw_hashes','previous_failure_id','synthetic_only')
 for r in (before,after):
  exact(r,keys);synthetic(r)
  for k in ('attempt_id','specimen_id','series_id','token_id','previous_failure_id'):string(r[k])
  require(type(r['capture_ids']) is list and type(r['raw_hashes']) is list and len(r['capture_ids'])==len(r['raw_hashes'])==2,'two retry view records')
  require(len(set(r['capture_ids']))==len(set(r['raw_hashes']))==2,'distinct retry view identities')
  for h in r['raw_hashes']:sha(h)
 require(before['previous_failure_id']==after['previous_failure_id'],'failure retained')
 for k in ('attempt_id','token_id'):require(before[k]!=after[k],'new retry '+k)
 for k in ('capture_ids','raw_hashes'):require(not set(before[k])&set(after[k]),'retry cannot reuse '+k)
 if before['specimen_id']!=after['specimen_id']:require(before['series_id']!=after['series_id'],'replacement requires separate series')
 return {'failure_preserved':True,'physical_retry':False}
def closeout(r):
 exact(r,('disposition','loaded','mounted','open_leases','supported','transported_to_storage','station_inventory_complete','evidence_archive_complete','selected_route_status','synthetic_only'));synthetic(r)
 require(type(r['open_leases']) is list and type(r['selected_route_status']) is dict and r['selected_route_status'],'explicit lease and route status ledger')
 for k in ('loaded','mounted','supported','transported_to_storage','station_inventory_complete','evidence_archive_complete'):require(type(r[k]) is bool,'explicit closeout state')
 require(r['supported'] and r['evidence_archive_complete'],'supported state and preserved evidence')
 require(all(v in ('complete_synthetic','held','failed','unattempted') for v in r['selected_route_status'].values()),'every selected route terminally accounted')
 if r['disposition']=='closed_synthetic':require(not r['loaded'] and not r['mounted'] and not r['open_leases'] and r['station_inventory_complete'] and all(v=='complete_synthetic' for v in r['selected_route_status'].values()),'no incomplete physical/scientific branch may claim closed')
 elif r['disposition']=='supported_hold':require(not r['transported_to_storage'],'held specimen cannot teleport to storage')
 else:raise ContractError('explicit supported-hold or closed disposition')
 return {'accounted_for':True,'fully_closed_synthetic':r['disposition']=='closed_synthetic','physical_complete':False}
def sequence(route):
 require(route in (*BRANCHES,'PHOTO_ANALYSIS','CLOSEOUT'),'known route')
 if route=='CLOSEOUT':return [('CLOSEOUT','R24','closeout')]
 if route=='PHOTO_ANALYSIS':return sequence('PP_RIGID')+[('PHOTO_ANALYSIS','R25','analysis')]
 r=BRANCHES[route];out=[]
 if route in ('PP_RIGID','PP_SHEAR'):out=sequence('PP_PREP')[:-2]
 else:out=[(route,'R00','allocation'),(route,'R01','qualification')]
 if route.startswith('CS'):
  for group,ops in r['operation_groups'].items():out += [(route,op,group) for op in ops]
 elif route=='PP_PREP':out += [(route,op,'preparation') for op in r['operation_sequence']]+[(route,'R23','closeout'),(route,'R24','closeout')]
 elif route=='PP_RIGID':
  out += [(route,op,'setup') for op in r['setup']]
  for h in r['state_loop']['instances']:out += [(route,op,h['id']) for op in r['state_loop']['per_instance']]
  out += [(route,op,'closeout') for op in r['closeout']]
 else:out += [(route,op,'qualitative') for op in r['operation_sequence']]
 return out
def fixture(fid):
 require(type(fid) is str and fid in FIXTURE_IDS,'known evaluator-selected fixture');route,outcome=fid.split(':');seq=sequence(route)
 if outcome=='QUALIFICATION_HOLD':seq=seq[:2]
 elif outcome in ('DATA_HOLD','SAFE_RELEASE_HOLD'):seq=seq[:max(1,len(seq)//2)]
 if outcome!='METADATA_OK':seq += [('CLOSEOUT','R24','supported_hold_accounting')]
 events=[];registry={};last=None;transfer_counts={}
 family=route if route.startswith('CS') else 'PP'
 for i,(owner,op,slot) in enumerate(seq,1):
  eid=fid+':E'+str(i);rid=fid+':REC'+str(i);ctx={k:'synthetic:'+k for k in CONTEXT};ctx.update(route_id=owner,family_id=family,attempt_id=fid+':attempt',specimen_id=fid+':one-specimen',stock_id=fid+':one-stock',configuration_revision=slot)
  payload={'record_type':OPS[op]['required_record_type'],'slot':slot,'synthetic_only':True,'physical_qualified':False,'physical_execution':False,'source_outcome_used':False,'disposition':outcome,'supported_hold':outcome=='SAFE_RELEASE_HOLD' and op=='R24','transported':False,'full_route_execution_claim':False}
  if op=='R03':
   catalog=[x for x in read('transport_routes.json')['transfers'] if x['route_id']==owner];ix=transfer_counts.get(owner,0);require(ix<len(catalog),'expanded transport binding required');payload['transport_binding']={**catalog[ix],'object_id':ctx['specimen_id'] if catalog[ix]['object_role']=='folded_specimen' else ctx['stock_id'] if catalog[ix]['object_role']=='stock_sheet' else ctx['prepared_sheet_id'],'carrier_id':ctx['carrier_id']};transfer_counts[owner]=ix+1
  record={'evidence_id':rid,'operation_id':op,'context':ctx,'role':OPS[op]['evidence_role'],'depends_on':[last] if last else [],'payload':payload};registry[rid]=record;events.append({'event_id':eid,'operation_id':op,'evidence_id':rid});last=rid
 return {'fixture_id':fid,'events':events,'registry':registry,'registry_digest':digest(registry)}
def evaluate(events,registry,expected_fixture_id):
 f=fixture(expected_fixture_id);require(type(events) is list and type(registry) is dict,'actor events and evaluator registry')
 require(canonical(registry)==canonical(f['registry']),'registry must equal evaluator-pinned finite evidence');require(len(events)==len(f['events']),'all occurrence slots required')
 targets={e['event_id']:e for e in f['events']};seen=set();records=set()
 for e in events:
  exact(e,('event_id','operation_id','evidence_id'))
  for x in e.values():string(x)
  require(e['event_id'] in targets and e['event_id'] not in seen,'known unique event occurrence');require(e==targets[e['event_id']],'operation/evidence/occurrence binding')
  r=registry[e['evidence_id']];require(set(r['depends_on'])<=records,'state dependency order');require(r['role']==OPS[e['operation_id']]['evidence_role'],'correct evidence role');seen.add(e['event_id']);records.add(e['evidence_id'])
 return {'contract_passed':True,'synthetic_metadata_complete':expected_fixture_id.endswith(':METADATA_OK'),'physical_execution':False,'physical_simulation':False,'scientific_reproduction':False,'source_data_reanalysis':False,'whole_paper_execution_complete':False,'validated_runnable_whole_paper_tasks':0}
