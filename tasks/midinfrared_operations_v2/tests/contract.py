"""Original finite synthetic metadata contracts. No controller, physics or source oracle."""
from pathlib import Path
import json,hashlib,math,copy
ROOT=Path(__file__).resolve().parents[1]
class ContractError(ValueError):pass
def require(ok,msg):
 if not ok:raise ContractError(msg)
def exact(v,keys):require(type(v) is dict and set(v)==set(keys),'exact schema: '+','.join(keys))
def string(v):require(type(v) is str and 0<len(v)<=256,'bounded nonempty identifier');return v
def finite(v):
 require(type(v) in (int,float),'finite numeric type')
 try:require(math.isfinite(v),'finite numeric value')
 except OverflowError:raise ContractError('numeric overflow')
 return v
def positive(v):finite(v);require(v>0,'positive value');return v
def integer(v):require(type(v) is int and 0<=v<=1000000,'bounded nonnegative integer');return v
def flag(v):require(type(v) is bool,'boolean required');return v
def synth(v):require(v is True,'synthetic-only receipt')
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def canonical(v):
 try:return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 except (ValueError,TypeError,OverflowError,RecursionError) as e:raise ContractError('invalid canonical input') from e
def read(n):return json.loads((ROOT/n).read_text())
OPS={o['id']:o for o in read('operations.json')['operations']}
BRANCHES={b['id']:b for b in read('branches.json')['branches']}
FIXTURE_IDS=read('mock_contract.json')['fixture_ids']
def campaign_policy(p,first_observation):
 exact(p,('policy_id','frozen_at','specimen_count','run_count','day_count','order_digest','metrics_digest','uncertainty_digest','stopping_digest','budget_digest','role','synthetic_only'))
 synth(p['synthetic_only']);require(p['role']=='independent_policy','independent policy authority');positive(first_observation);finite(p['frozen_at']);require(p['frozen_at']<first_observation,'freeze precedes outcome')
 for k in ['specimen_count','run_count','day_count']:integer(p[k]);require(p[k]>0,'no missing or zero repeat count')
 for k in ['policy_id','order_digest','metrics_digest','uncertainty_digest','stopping_digest','budget_digest']:string(p[k])
 require(p['run_count']>=p['specimen_count'] and p['run_count']>=p['day_count'],'declared repeat hierarchy')
 return {'prospective_policy_valid_synthetic':True,'scientific_qualified':False}
def preparation(r):
 exact(r,('stock_lot_id','output_stock_lot_id','drawing_revision','output_drawing_revision','job_id','completed_job_id','sample_id','carrier_id','reference_id','completed','inspected','safe_release','role','synthetic_only'))
 synth(r['synthetic_only']);require(r['role']=='independent_fabrication','request is not completion')
 for a,b in [('stock_lot_id','output_stock_lot_id'),('drawing_revision','output_drawing_revision'),('job_id','completed_job_id')]:string(r[a]);require(r[a]==r[b],'fabrication lineage')
 for k in ['sample_id','carrier_id','reference_id']:string(r[k])
 for k in ['completed','inspected','safe_release']:require(r[k] is True,'required independent fabrication evidence')
 return {'prepared_lineage_valid_synthetic':True,'robot_performed_fabrication':False}
def custody_transfer(before,after,receipt):
 keys=('sample_id','carrier_id','stock_lot_id','drawing_revision','station_id','slot_id','revision','history','mounted','acquiring','supported','synthetic_only')
 exact(before,keys);exact(after,keys);synth(before['synthetic_only']);synth(after['synthetic_only'])
 exact(receipt,('sample_id','carrier_id','from_station','from_slot','to_station','to_slot','source_occupant','destination_empty','safe_release','retention','transform_revision','role','synthetic_only'))
 synth(receipt['synthetic_only']);require(receipt['role']=='independent_custody','independent handoff receipt')
 for k in ['sample_id','carrier_id','stock_lot_id','drawing_revision']:string(before[k]);require(before[k]==after[k],'retained immutable sample/carrier lineage')
 for k in ['station_id','slot_id']:string(before[k]);string(after[k])
 for r,k in [('from_station','station_id'),('from_slot','slot_id')]:require(receipt[r]==before[k],'actual source custody')
 for r,k in [('to_station','station_id'),('to_slot','slot_id')]:require(receipt[r]==after[k],'actual destination custody')
 for k in ['sample_id','carrier_id']:require(receipt[k]==before[k],'receipt identity')
 require(receipt['source_occupant']==before['carrier_id'],'source occupied by actual carrier')
 for k in ['destination_empty','safe_release','retention']:require(receipt[k] is True,'safe vacancy and retention evidence')
 string(receipt['transform_revision']);integer(before['revision']);integer(after['revision']);require(after['revision']==before['revision']+1,'monotonic custody revision')
 require(type(before['history']) is list and len(before['history'])>0 and type(after['history']) is list,'custody history');require(after['history'][:-1]==before['history'] and len(after['history'])==len(before['history'])+1,'append-only custody history')
 for s in [before,after]:
  require(s['mounted'] is False and s['acquiring'] is False and s['supported'] is True,'no mounted/acquiring/unsupported transfer')
 return {'custody_valid_synthetic':True,'physical_motion_verified':False}
def readiness(r,current,branch,when,branch_policy=None):
 exact(current,('epoch_id','detector_mode','controller_revision','source_revision','configuration_id','synthetic_only'));synth(current['synthetic_only'])
 exact(r,('receipt_id','epoch_id','detector_mode','controller_revision','source_revision','configuration_id','valid_interval','allowed_branches','role','interlocked','calibration_digest','uncertainty_digest','synthetic_only'))
 synth(r['synthetic_only']);require(r['role']=='independent_readiness','readiness authority');require(branch in BRANCHES,'known branch');finite(when)
 for k in ['epoch_id','detector_mode','controller_revision','source_revision','configuration_id']:string(current[k]);require(r[k]==current[k],'current configuration epoch')
 require(current['detector_mode'] in ('analog','photon','spatial_diagnostic'),'known detector mode')
 if BRANCHES[branch]['detector_mode'] is not None:require(current['detector_mode']==BRANCHES[branch]['detector_mode'],'branch-compatible detector')
 if branch=='B05':
  exact(branch_policy,('branch_id','epoch_id','readiness_id','detector_mode','exposure_policy_digest','budget_policy_digest','provenance','role','synthetic_only'));synth(branch_policy['synthetic_only'])
  require(branch_policy['role']=='independent_branch_policy' and branch_policy['branch_id']=='B05','explicit U14 resolution authority')
  require(branch_policy['epoch_id']==current['epoch_id'] and branch_policy['readiness_id']==r['receipt_id'] and branch_policy['detector_mode']==current['detector_mode'],'B05 policy tied to current qualified readiness')
  require(current['detector_mode'] in ('analog','photon'),'B05 acquisition detector, not spatial diagnostic')
  require(branch_policy['provenance'] in ('approved_authored_departure','qualified_source_specific_evidence'),'B05 resolution provenance')
  for k in ['exposure_policy_digest','budget_policy_digest']:string(branch_policy[k])
 elif branch_policy is not None:raise ContractError('unexpected branch-specific policy')
 require(type(r['allowed_branches']) is list and len(r['allowed_branches'])==len(set(r['allowed_branches'])) and branch in r['allowed_branches'] and set(r['allowed_branches'])<=set(BRANCHES),'explicit branch authorization')
 iv=r['valid_interval'];require(type(iv) is list and len(iv)==2,'validity interval');finite(iv[0]);finite(iv[1]);require(iv[0]<=when<=iv[1] and iv[0]<iv[1],'unexpired current readiness')
 for k in ['receipt_id','calibration_digest','uncertainty_digest']:string(r[k])
 require(r['interlocked'] is True,'closed interlock evidence')
 return {'ready_synthetic':True,'branch':branch,'source_equivalence_established':False,'physical_qualified':False}
def lease_transition(state,event):
 exact(event,('action','station_id','lease_id','run_id','purpose','safe_release','role','synthetic_only'));synth(event['synthetic_only']);require(type(state) is dict,'lease state');require(event['role']=='independent_lease','lease authority')
 for k in ['station_id','lease_id','run_id']:string(event[k])
 require(event['station_id']=='S03' and event['purpose'] in ('acquisition','motion','configuration_change','spatial_mapping'),'station lease purpose');flag(event['safe_release']);require(event['action'] in ('acquire','release'),'lease action')
 out=copy.deepcopy(state);key=event['station_id']
 if event['action']=='acquire':require(key not in state,'exclusive station lease');require(event['lease_id'] not in [x['lease_id'] for x in state.values()],'unique lease ID');out[key]={k:event[k] for k in ['lease_id','run_id','purpose']}
 else:
  require(key in state and state[key]=={k:event[k] for k in ['lease_id','run_id','purpose']},'matching lease owner');require(event['safe_release'] is True,'independent safe release before lease close');del out[key]
 return out
def configuration_change(old,new,receipt):
 keys=('epoch_id','detector_mode','controller_revision','source_revision','configuration_id','synthetic_only');exact(old,keys);exact(new,keys);synth(old['synthetic_only']);synth(new['synthetic_only'])
 exact(receipt,('old_epoch','new_epoch','safe_idle','active_acquisition_lease','readiness_invalidated','role','synthetic_only'));synth(receipt['synthetic_only']);require(receipt['role']=='independent_configuration_change','configuration authority')
 require(receipt['old_epoch']==old['epoch_id'] and receipt['new_epoch']==new['epoch_id'] and old['epoch_id']!=new['epoch_id'],'new epoch required')
 require(receipt['safe_idle'] is True and receipt['active_acquisition_lease'] is False and receipt['readiness_invalidated'] is True,'safe idle change invalidates readiness')
 for s in [old,new]:
  for k in keys[:-1]:string(s[k])
  require(s['detector_mode'] in ('analog','photon','spatial_diagnostic'),'known detector mode')
 require(old['configuration_id']!=new['configuration_id'],'fresh configuration identity')
 return {'new_epoch':new['epoch_id'],'ready':False,'fresh_readiness_required':True}
def pattern_ledger(manifest,rows,current_epoch):
 exact(manifest,('run_id','sample_id','epoch_id','detector_mode','encoding','matrix_digest','normalization_id','physical_display_convention','expected_displays','declared_coefficients','synthetic_only'));synth(manifest['synthetic_only']);string(current_epoch);require(manifest['epoch_id']==current_epoch,'manifest current epoch')
 for k in ['run_id','sample_id','epoch_id','matrix_digest','normalization_id']:string(manifest[k])
 require(manifest['detector_mode'] in ('analog','photon'),'acquisition detector');require(manifest['encoding'] in ('hadamard','raster','random'),'encoding');require(manifest['physical_display_convention'] in ('complementary_pairs','single_displays'),'explicit display convention')
 if manifest['encoding']=='hadamard':require(manifest['physical_display_convention']=='complementary_pairs','Hadamard paired displays')
 expected=manifest['expected_displays'];require(type(expected) is list and 0<len(expected)<=10000 and type(rows) is list and len(rows)==len(expected),'complete expected display ledger')
 seen=set();raw=set();prev=-1
 for i,(ex,r) in enumerate(zip(expected,rows)):
  exact(ex,('display_id','pattern_digest','coefficient_id','sign'));exact(r,('raw_id','run_id','sample_id','epoch_id','detector_mode','display_id','pattern_digest','coefficient_id','sign','dmd_index','controller_index','detector_index','time','exposure','value','unit','overload','missing','evidence_kind','synthetic_only'));synth(r['synthetic_only'])
  for k in ['display_id','pattern_digest','coefficient_id']:string(ex[k]);require(r[k]==ex[k],'expected display matrix binding')
  require(type(ex['sign']) is int and ex['sign'] in (-1,1) and type(r['sign']) is int and r['sign']==ex['sign'],'known sign')
  for k in ['run_id','sample_id','epoch_id','detector_mode']:require(r[k]==manifest[k],'raw manifest lineage')
  for k in ['dmd_index','controller_index','detector_index']:integer(r[k]);require(r[k]==i,'cross-device event bijection')
  string(r['raw_id']);require(r['raw_id'] not in raw and r['display_id'] not in seen,'unique raw and physical display');raw.add(r['raw_id']);seen.add(r['display_id'])
  finite(r['time']);require(r['time']>prev,'strict event time order');prev=r['time'];positive(r['exposure']);finite(r['value'])
  require(r['overload'] is False and r['missing'] is False and r['evidence_kind']=='synthetic_observation','valid synthetic raw observation only')
  if r['detector_mode']=='photon':require(type(r['value']) is int and r['value']>=0 and r['unit']=='count','nonnegative integer photon count')
  else:require(r['unit']=='ADC_unit','analog units')
 integer(manifest['declared_coefficients']);coeff=[]
 if manifest['physical_display_convention']=='complementary_pairs':
  require(len(expected)%2==0,'whole complementary pairs')
  for a,b in zip(expected[::2],expected[1::2]):require(a['coefficient_id']==b['coefficient_id'] and [a['sign'],b['sign']]==[1,-1] and a['pattern_digest']!=b['pattern_digest'],'adjacent distinct complementary pair');coeff.append(a['coefficient_id'])
 else:
  require(all(x['sign']==1 for x in expected),'single-display sign');coeff=[x['coefficient_id'] for x in expected]
 require(len(coeff)==len(set(coeff))==manifest['declared_coefficients'],'coefficient accounting')
 return {'ledger_valid_synthetic':True,'physical_displays':len(rows),'signed_coefficients':len(coeff),'independent_runs':1,'dose_equivalence_established':False}
def acquisition_bundle(branch,manifest,rows,current,receipt,lease,sample_id,when,branch_policy=None):
 """Compose previously separate symbolic guards; all evidence is evaluator-owned."""
 require(branch!='B01','spatial calibration uses diagnostic contract, not acquisition bucket ledger')
 readiness(receipt,current,branch,when,branch_policy)
 required_encoding={'B02':'hadamard','B03':'hadamard','B04':'hadamard','B07':'random'}.get(branch)
 if required_encoding is not None:require(manifest['encoding']==required_encoding,'branch-specific encoding')
 exact(lease,('lease_id','run_id','purpose'));string(lease['lease_id']);string(sample_id)
 require(lease['run_id']==manifest['run_id'],'acquisition owns current run lease')
 require(lease['purpose']==('motion' if branch=='B03' else 'acquisition'),'compatible exclusive station lease purpose')
 require(manifest['sample_id']==sample_id and manifest['detector_mode']==current['detector_mode'],'current docked sample and detector context')
 r=pattern_ledger(manifest,rows,current['epoch_id'])
 # Raw time means exposure start; validity must cover the full exposure.
 lo,hi=receipt['valid_interval']
 for row in rows:
  end=row['time']+row['exposure'];finite(end)
  require(lo<=row['time'] and end<=hi,'full raw exposure within readiness validity')
 return {**r,'branch':branch,'bundle_valid_synthetic':True,'physical_qualified':False}
def mapping_evidence(r):
 exact(r,('sensor_kind','sensor_id','registration_digest','epoch_id','empty_dock','object_removed','all_on_hash','uncorrected_pump_hash','corrected_pump_hash','representative_sfg_hash','valid_pixel_mask_hash','near_zero_excluded','coverage_policy_digest','uncertainty_digest','role','synthetic_only'));synth(r['synthetic_only']);require(r['sensor_kind']=='spatial_diagnostic' and r['role']=='independent_spatial_diagnostic','bucket-only mapping forbidden')
 for k in ['sensor_id','registration_digest','epoch_id','all_on_hash','uncorrected_pump_hash','corrected_pump_hash','representative_sfg_hash','valid_pixel_mask_hash','coverage_policy_digest','uncertainty_digest']:string(r[k])
 require(len({r[k] for k in ['all_on_hash','uncorrected_pump_hash','corrected_pump_hash','representative_sfg_hash']})==4,'distinct map evidence')
 for k in ['empty_dock','object_removed','near_zero_excluded']:require(r[k] is True,'mapping validity evidence')
 return {'mapping_contract_valid_synthetic':True,'full_set_sfg_proved':False}
def analysis_pair(base,denoised):
 keys=('result_id','raw_digest','matrix_digest','calibration_digest','correction_digest','software_digest','weights_digest','parameters_digest','reference_digest','metrics_digest','uncertainty_digest','residual_digest','role','kind','synthetic_only')
 for r in [base,denoised]:
  exact(r,keys);synth(r['synthetic_only']);require(r['role']=='independent_analysis' and r['kind']=='synthetic_analysis','independent synthetic analysis')
  for k in keys:
   if k not in ('synthetic_only','weights_digest'):string(r[k])
 require(base['weights_digest'] is None,'baseline has no denoiser weights');string(denoised['weights_digest'])
 for k in ['raw_digest','matrix_digest','calibration_digest','correction_digest','reference_digest','metrics_digest','uncertainty_digest']:require(base[k]==denoised[k],'paired analysis common provenance')
 require(base['result_id']!=denoised['result_id'],'separate derived results')
 return {'paired_provenance_valid_synthetic':True,'scientific_accuracy_proved':False}
def repeat_ledger(policy,rows):
 campaign_policy(policy,policy['frozen_at']+1);require(type(rows) is list and len(rows)==policy['run_count'],'all frozen run slots');runs=set();specimens=set();days=set()
 for r in rows:
  exact(r,('run_id','sample_id','day_id','reload_id','calibration_epoch','policy_id','independent_unit','physical_display_count','frame_count','raw_manifest_digest','status','synthetic_only'));synth(r['synthetic_only']);require(r['policy_id']==policy['policy_id'],'same frozen policy');require(r['independent_unit']=='acquisition_run','pulses/masks/frames are not independent n')
  for k in ['run_id','sample_id','day_id','reload_id','calibration_epoch','raw_manifest_digest']:string(r[k])
  require(r['run_id'] not in runs,'unique independent run');runs.add(r['run_id']);specimens.add(r['sample_id']);days.add(r['day_id']);integer(r['physical_display_count']);integer(r['frame_count']);require(r['status'] in ('accepted_synthetic','rejected_synthetic','blocked'),'every outcome retained')
 require(len(specimens)==policy['specimen_count'] and len(days)==policy['day_count'],'frozen specimen/day allocation')
 return {'independent_runs':len(runs),'specimens':len(specimens),'days':len(days),'scientific_repeatability_established':False}
def retry(old,new):
 keys=('run_id','attempt_id','sample_id','series_id','raw_ids','prior_failure_id','policy_id','synthetic_only')
 for r in [old,new]:
  exact(r,keys);synth(r['synthetic_only'])
  for k in keys:
   if k not in ('raw_ids','synthetic_only'):string(r[k])
  require(type(r['raw_ids']) is list and len(r['raw_ids'])>0 and len(r['raw_ids'])==len(set(r['raw_ids'])),'raw IDs')
  for k in r['raw_ids']:string(k)
 require(old['run_id']!=new['run_id'] and old['attempt_id']!=new['attempt_id'] and not set(old['raw_ids'])&set(new['raw_ids']),'fresh retry evidence')
 require(old['prior_failure_id']==new['prior_failure_id'] and old['policy_id']==new['policy_id'],'failure retained and policy unchanged')
 if old['sample_id']!=new['sample_id']:require(old['series_id']!=new['series_id'],'replacement starts new series')
 return {'failure_preserved':True,'physical_recovery_permitted':False}
def closeout(r):
 exact(r,('disposition','branch_status','active_leases','dock_occupied','safe_access_observed','all_samples_accounted','custody','archive_complete','failed_records_retained','robot_outside_enclosure','synthetic_only'));synth(r['synthetic_only'])
 require(type(r['branch_status']) is dict and set(r['branch_status'])==set(BRANCHES),'all eight branches accounted');require(all(v in ('complete_synthetic','blocked','rejected','unattempted') for v in r['branch_status'].values()),'branch dispositions')
 require(type(r['active_leases']) is list and len(r['active_leases'])==len(set(r['active_leases'])),'lease inventory')
 for x in r['active_leases']:string(x)
 for k in ['dock_occupied','safe_access_observed','robot_outside_enclosure']:flag(r[k])
 for k in ['all_samples_accounted','archive_complete','failed_records_retained']:require(r[k] is True,'complete custody and evidence accounting')
 require(r['disposition'] in ('closed_synthetic','supported_hold'),'bounded closeout disposition')
 if r['disposition']=='closed_synthetic':
  require(not r['active_leases'] and r['dock_occupied'] is False and r['safe_access_observed'] is True and r['custody']=='storage_or_quarantine','observed safe return and no open lease')
 else:
  require(r['custody']=='observed_supported_hold' and r['robot_outside_enclosure'] is True,'hold is actual custody, not phantom return')
  if r['dock_occupied']:require(len(r['active_leases'])>0,'occupied hold preserves station lease')
 return {'accounting_complete_synthetic':True,'fully_closed_synthetic':r['disposition']=='closed_synthetic','all_branch_metadata_complete':all(v=='complete_synthetic' for v in r['branch_status'].values()),'whole_paper_execution_complete':False}
def scope_holds(operation,claims):
 require(operation in OPS and type(claims) is list,'operation/claim scope');require(set(claims)<={'physical_execution','source_reanalysis','scientific_grading','media_exhaustiveness'},'known claim scope')
 ids=[]
 for u in read('unknown_parameters.json')['unknowns']:
  if operation in u['operation_ids'] and (('physical_execution' in claims and u['id'] not in ('U01','U10','U11')) or ('source_reanalysis' in claims and u['id']=='U01') or ('scientific_grading' in claims and u['id']=='U06') or ('media_exhaustiveness' in claims and u['id']=='U10')):ids.append(u['id'])
 return {'unresolved':ids,'can_record_safe_hold':True,'physical_execution_enabled':False}
def fixture(fid):
 require(fid in FIXTURE_IDS,'known finite fixture');events=[];registry={};last=None
 for i,op in enumerate(OPS):
  rid=f'SYNTHETIC:{fid}:{op}:receipt';eid=f'SYNTHETIC:{fid}:{i}:event';branch=next((b for b in BRANCHES if op in BRANCHES[b]['operations']),'campaign')
  payload={'branch_id':branch,'sample_id':'SYNTHETIC:silicon' if op in ('R17','R18') else 'SYNTHETIC:copper','epoch_id':'SYNTHETIC:epoch-'+str(i),'source_outcome_used':False,'physical_qualified':False,'disposition':'metadata_only' if fid.endswith('METADATA_OK') else 'held_evidence','synthetic_only':True}
  registry[rid]={'evidence_id':rid,'operation_id':op,'role':OPS[op]['evidence_role'],'depends_on':[last] if last else [],'payload':payload};events.append({'event_id':eid,'operation_id':op,'evidence_id':rid});last=rid
 return {'fixture_id':fid,'events':events,'registry':registry,'registry_digest':digest(registry)}
def evaluate(events,registry,expected_fixture_id):
 f=fixture(expected_fixture_id);require(type(events) is list and type(registry) is dict,'actor events and trusted evaluator registry');require(canonical(registry)==canonical(f['registry']),'evaluator-pinned synthetic registry only');require(len(events)==len(f['events']),'all occurrence slots required');expected={e['event_id']:e for e in f['events']};seen=set();records=set()
 for e in events:
  exact(e,('event_id','operation_id','evidence_id'))
  for v in e.values():string(v)
  require(e['event_id'] in expected and e['event_id'] not in seen and e==expected[e['event_id']],'known unique event/evidence binding');r=registry[e['evidence_id']];require(set(r['depends_on'])<=records,'dependency order');require(r['role']==OPS[e['operation_id']]['evidence_role'],'evidence role');seen.add(e['event_id']);records.add(e['evidence_id'])
 return {'contract_passed':True,'synthetic_metadata_complete':expected_fixture_id.endswith(':METADATA_OK'),'physical_execution':False,'physical_simulation':False,'scientific_reproduction':False,'source_data_reanalysis':False,'whole_paper_execution_complete':False,'validated_runnable_whole_paper_tasks':0}
