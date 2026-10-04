"""Original finite synthetic metadata guards. No hardware or scientific solver.
Receipt roles here are test metadata, not real-world authentication. The evaluator
must own fixtures and actor/evaluator isolation in any future implementation.
"""
from copy import deepcopy
import hashlib,json,math
OPERATIONS=tuple('R%02d'%i for i in range(1,17))
BRANCHES=tuple('B%02d'%i for i in range(1,10))
PHYSICAL=('B02','B03');NONMANUAL=('B04','B05','B07','B08')
class GuardError(ValueError):pass
def need(ok,message):
 if not ok:raise GuardError(message)
def text(v):return type(v) is str and bool(v.strip())
def ident(v):need(text(v),'nonempty identifier required');return v
def integer(v,minimum=0):need(type(v) is int and v>=minimum,'bounded integer required');return v
def number(v,positive=False):
 need(type(v) in (int,float) and math.isfinite(v),'finite number required')
 if positive:need(v>0,'positive number required')
 return v
def digest(v):ident(v);need(len(v)==64 and all(c in '0123456789abcdef' for c in v),'SHA256 required');return v
def unique(xs):need(type(xs) is list and len(xs)==len(set(xs)),'unique list required');return xs
def exact_keys(d,keys):need(type(d) is dict and set(d)==set(keys),'exact fields required')
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def hashof(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def context_equal(a,b,keys):
 for k in keys:
  need(k in a and k in b and type(a[k]) is type(b[k]) and a[k]==b[k] and a[k] is not None,'context mismatch: '+k)
  if k=='configuration_epoch':integer(a[k],1)
  else:ident(a[k])
def receipt(r,role,context,keys):
 need(type(r) is dict,'receipt object');need(r.get('role')==role and r.get('issuer')=='independent_fixture_evaluator','independent receipt role')
 ident(r.get('receipt_id'));need(r.get('status')=='observed','request is not completion');context_equal(r.get('context',{}),context,keys)
 need(r.get('synthetic') is True,'only synthetic receipt model implemented');return r

def policy(p):
 ident(p.get('policy_id'));need(p.get('frozen_before_outcomes') is True,'prospective policy freeze required')
 need(p.get('outcomes_seen')==0 and type(p.get('outcomes_seen')) is int,'no outcomes before freeze')
 for k in ['independent_specimens','runs_per_condition']:integer(p.get(k),1)
 need(p.get('repeat_unit')=='specimen_and_cycle','frames are not independent specimens')
 need(set(p.get('condition_order',[]))==set(PHYSICAL) and len(p['condition_order'])==2,'both conditions planned once in order template')
 for k in ['reset_policy_id','stop_policy_id','uncertainty_policy_id','metric_policy_id','model_order_policy_id','exclusion_policy_id']:ident(p.get(k))
 need(p.get('repeat_until_good') is False,'no outcome-conditioned retries');return True

def preparation(p,c):
 receipt(p,'fabrication_completion',c,['specimen_id','cad_revision','print_job_id'])
 for k in ['beam_material_lot_id','pad_material_lot_id','foot_material_lot_id','pad_layout_revision','foot_id','postprocess_receipt_id','inspection_receipt_id','safe_release_receipt_id']:ident(p.get(k))
 need(p.get('dimensions_accepted') is True and p.get('condition_accepted') is True,'independent part inspection required')
 need(p.get('closed_qualified_service') is True,'qualified closed fabrication service required')
 need(p.get('source_cad_inferred_from_figure') is False,'figure is not CAD');return True

def fixture(p,c):
 receipt(p,'fixture_inspection',c,['fixture_id','branch_id'])
 need(c.get('branch_id') in PHYSICAL,'physical fixture branch')
 for k in ['drawing_revision','contact_registry_id','mount_inspection_id']:ident(p.get(k))
 need(p.get('locked') is True and p.get('geometry_verified') is True,'fixture geometry and lock required');return True

def contact(p,c):
 receipt(p,'contact_conditioning',c,['specimen_id','fixture_id','conditioning_state_id','branch_id'])
 ident(p.get('contact_preparation_id'));ident(p.get('recovery_policy_id'));ident(p.get('environment_record_id'))
 need(p.get('history_retained') is True and p.get('condition_accepted') is True,'condition history and acceptance required')
 method=p.get('method');need(method in ('no_treatment_approved','qualified_service_treatment'),'declared method required')
 if method=='qualified_service_treatment':
  for k in ['material_identity','sds_review_id','application_service_id','cleanup_policy_id']:ident(p.get(k))
  need(p.get('closed_qualified_service') is True,'closed treatment service required')
 if c['branch_id']=='B03':need(p.get('bridge_treatment_policy_id') is not None and text(p['bridge_treatment_policy_id']),'bridge cannot inherit foot treatment policy')
 need(p.get('unknown_powder_handling') is False,'unidentified powder blocked');return True

def custody(p,c):
 receipt(p,'supported_custody',c,['specimen_id','carrier_id','conditioning_state_id'])
 for k in ['source_station','source_slot','destination_station','destination_slot','transform_revision','retention_receipt_id','safe_release_receipt_id','custody_event_id']:ident(p.get(k))
 need((p['source_station'],p['source_slot'])!=(p['destination_station'],p['destination_slot']),'distinct custody endpoints')
 need(p.get('source_occupant')==c['specimen_id'] and p.get('source_carrier')==c['carrier_id'],'source observed identity')
 need(p.get('destination_empty') is True and p.get('supported') is True and p.get('retained') is True,'supported transfer and vacant destination')
 need(p.get('safe_release_observed') is True and p.get('moving_or_loaded') is False,'safe released state required')
 need(p.get('grasp_surface')=='carrier_support_interface','no fragile hinge or pad grasp');return True

def mechanics(p,c):
 receipt(p,'mechanics_ready',c,['specimen_id','fixture_id','conditioning_state_id','configuration_epoch','branch_id'])
 for k in ['calibration_id','load_cell_id','unloaded_reference_id','contact_zero_id','safe_stop_policy_id','limit_policy_id']:ident(p.get(k))
 need(p['unloaded_reference_id']!=p['contact_zero_id'],'unloaded reference and contact zero distinct')
 need(p.get('interlock_ready') is True and p.get('fixture_locked') is True and p.get('source_stroke_as_safety_limit') is False,'independent mechanics safety required')
 for k in ['force_limit','stroke_limit','speed_limit']:number(p.get(k),True)
 need(p.get('qualified_limits') is True,'limits need independent qualification');return True

def imaging(p,c):
 receipt(p,'imaging_ready',c,['specimen_id','conditioning_state_id','configuration_epoch'])
 for k in ['camera_id','lens_id','calibration_id','reference_image_id','exposure_settings_id','distortion_map_id','uncertainty_policy_id','drift_check_id']:ident(p.get(k))
 need(p.get('field_of_view_accepted') is True and p.get('focus_accepted') is True,'image geometry required')
 unique(p.get('visible_square_ids'));need(len(p['visible_square_ids'])>=1,'nonempty tracking visibility')
 need(p.get('source_accuracy_used_as_calibration') is False,'source tracking accuracy not calibration');return True

def arming(p,c):
 receipt(p,'synchronized_arming',c,['run_id','specimen_id','fixture_id','conditioning_state_id','configuration_epoch','branch_id'])
 for k in ['mechanics_calibration_id','camera_calibration_id','clock_mapping_id','endpoint_policy_id']:ident(p.get(k))
 need(p.get('capture_ready') is True and p.get('buffer_ready') is True and p.get('mechanics_ready') is True,'both instruments ready')
 need(p.get('active_resources')==['S05','S06'] and p.get('foreign_leases')==[],'exclusive tester-camera lease')
 number(p.get('capture_ready_time'));number(p.get('machine_start_time'));need(p['machine_start_time']>=p['capture_ready_time'],'motion before capture ready')
 number(p.get('clock_scale'),True);number(p.get('clock_offset'));number(p.get('clock_tolerance'));need(p['clock_tolerance']>=0,'nonnegative clock tolerance')
 need(p.get('phase_policy')==['loading','unloading'],'both phases planned');return True

def acquisition(p,c):
 receipt(p,'cycle_acquisition',c,['run_id','specimen_id','fixture_id','conditioning_state_id','configuration_epoch','branch_id'])
 need(c.get('branch_id') in PHYSICAL,'physical branch required');ident(p.get('clock_mapping_id'));ident(p.get('raw_manifest_digest'))
 expected=unique(p.get('expected_frame_ids'));frames=p.get('frames');need(type(frames) is list and len(expected)>0,'frame ledger required')
 need([f.get('frame_id') for f in frames]==expected,'frame ledger missing duplicate or reordered')
 machine=unique(p.get('machine_event_ids'));need([f.get('machine_event_id') for f in frames]==machine,'cross-device event bijection')
 scale=number(p.get('clock_scale'),True);offset=number(p.get('clock_offset'));tol=number(p.get('clock_tolerance'));need(tol>=0,'nonnegative clock tolerance')
 prev=None;phases=[]
 for f in frames:
  need(f.get('run_id')==c['run_id'],'frame run mismatch');digest(f.get('raw_sha256'));number(f.get('camera_time'));number(f.get('machine_time'))
  need(abs(f['camera_time']*scale+offset-f['machine_time'])<=tol,'clock mapping mismatch')
  need(prev is None or f['camera_time']>prev,'nonincreasing camera clock');prev=f['camera_time']
  need(f.get('phase') in ('loading','unloading'),'phase label');phases.append(f['phase'])
  need(f.get('accepted') in (True,False) and type(f.get('accepted')) is bool,'explicit acceptance flag')
  need(f.get('retained_original') is True,'raw record retained')
 need(p.get('aborted') in (True,False) and type(p['aborted']) is bool,'abort flag')
 if not p['aborted']:
  need(set(phases)=={'loading','unloading'},'complete cycle retains both phases')
  need(phases==sorted(phases,key=lambda x:0 if x=='loading' else 1),'loading before unloading')
 else:ident(p.get('failure_id'));need(p.get('partial_data_retained') is True,'aborted data retained')
 need(p.get('drop_events_accounted') is True and p.get('source_400_forced') is False,'drops cannot be hidden or frames manufactured')
 need(p.get('source_playback_as_acquisition_clock') is False,'playback is not acquisition');return True

def synchronized_cycle(mech,img,arm,acq,c):
 mechanics(mech,c);imaging(img,c);arming(arm,c);acquisition(acq,c)
 need(arm['mechanics_calibration_id']==mech['calibration_id'],'current mechanics calibration join')
 need(arm['camera_calibration_id']==img['calibration_id'],'current camera calibration join')
 for k in ['clock_mapping_id','clock_scale','clock_offset','clock_tolerance']:
  need(type(arm[k]) is type(acq[k]) and arm[k]==acq[k],'current synchronized clock join: '+k)
 for f in acq['frames']:need(f['machine_time']>=arm['machine_start_time'],'no acquisition frame before current machine start')
 need(acq.get('planned_stroke') is not None and acq.get('planned_speed') is not None,'qualified program envelope required')
 number(acq['planned_stroke'],True);number(acq['planned_speed'],True)
 need(acq['planned_stroke']<=mech['stroke_limit'] and acq['planned_speed']<=mech['speed_limit'],'qualified program exceeds commissioned limits')
 need(acq.get('qualified_program_id')==arm.get('qualified_program_id') and text(acq.get('qualified_program_id')),'current branch program join')
 return True

def recovery(p,c):
 receipt(p,'unload_recovery',c,['run_id','specimen_id','fixture_id','conditioning_state_id','configuration_epoch'])
 need(p.get('unloaded_observed') is True and p.get('disarmed_observed') is True,'observed unload and disarm required')
 ident(p.get('new_conditioning_state_id'));need(p['new_conditioning_state_id']!=c['conditioning_state_id'],'advance specimen state')
 need(p.get('history_retained') is True and p.get('virgin_restored_by_unload') is False,'unloading not virgin reset')
 for k in ['damage_inspection_id','residual_deformation_record_id','adhesion_record_id','recovery_policy_id']:ident(p.get(k))
 need(p.get('disposition') in ('reuse_qualified','quarantine','retire','hold'),'explicit recovery disposition')
 if p['disposition']=='reuse_qualified':ident(p.get('recovery_acceptance_receipt_id'));need(p.get('recovery_criteria_passed') is True,'qualified recovery before reuse')
 integer(p.get('completed_cycle_count'),1);return True

def fixture_change(p,c):
 receipt(p,'fixture_change',c,['specimen_id','fixture_id','conditioning_state_id','configuration_epoch'])
 need(p.get('unloaded_observed') is True and p.get('disarmed_observed') is True and p.get('active_leases')==[],'isolated change required')
 ident(p.get('new_fixture_id'));need(p['new_fixture_id']!=c['fixture_id'],'new fixture identity')
 integer(p.get('new_configuration_epoch'),1);need(type(c['configuration_epoch']) is int and p['new_configuration_epoch']>c['configuration_epoch'],'epoch advances')
 need(p.get('invalidated')==['docking','mechanics','imaging','synchronization'],'all affected readiness invalidated')
 ident(p.get('new_run_id'));need(p['new_run_id']!=c.get('run_id'),'new run identity')
 new=p.get('new_specimen_id');ident(new);replace=new!=c['specimen_id'];changed=p.get('treatment_or_conditioning_changed');need(type(changed) is bool,'explicit preparation change')
 required=['R02','R03','R04'] if replace else (['R03','R04'] if changed else [])
 need(p.get('preparation_reentry')==required,'applicable preparation reentry required')
 need(p.get('downstream_reentry')==['R05','R06','R07','R08','R09','R10'],'full new branch reentry')
 need(p.get('old_preparation_receipts_reused') is False if replace else True,'replacement cannot inherit preparation')
 need(p.get('history_retained') is True,'cross-fixture history retained');return True

def tracking(p,c):
 receipt(p,'registered_tracking',c,['run_id','specimen_id','conditioning_state_id'])
 for k in ['raw_manifest_digest','camera_calibration_id','clock_mapping_id','tracking_revision','coordinate_convention_id','quality_mask_digest','uncertainty_policy_id']:ident(p.get(k))
 need(p.get('source_code_inspected_or_independent_validated') is True,'unread source code not executable qualification')
 need(p.get('raw_immutable') is True and p.get('rejected_tracks_retained') is True and p.get('outcome_driven_filtering') is False,'tracking provenance retained')
 need(p.get('retained_phases')==['loading','unloading'],'both phases survive tracking');return True

def analysis(p,c):
 receipt(p,'separate_analysis',c,['run_id','specimen_id','conditioning_state_id'])
 need(p.get('modality')=='physical','physical analysis separate from source numerical scope')
 for k in ['tracking_digest','coordinate_convention_id','registration_policy_id','metric_policy_id','uncertainty_policy_id','model_order_policy_id']:ident(p.get(k))
 need(p.get('policy_frozen_before_outcomes') is True,'no post-hoc analysis policy')
 need(p.get('resolved_conflicts')==['C01','C04'] and p.get('expert_interpretation_receipt_id') is not None,'affected conflicts need interpretation')
 ident(p['expert_interpretation_receipt_id']);need(p.get('silent_source_correction') is False,'no silent scientific correction')
 need(p.get('area_variable')=='J_area' and p.get('linear_variable')=='alpha_linear','linear dilation distinct from area')
 number(p.get('detF_min'),True);need(p.get('local_inversion_or_collapse') is False,'orientation preserving local geometry required')
 need(p.get('global_geometry_status') in ('verified_by_qualified_method','unverified'),'explicit global validity')
 if p['global_geometry_status']=='verified_by_qualified_method':ident(p.get('global_geometry_receipt_id'))
 else:need(p.get('global_geometry_claim') is False,'unverified global geometry cannot be certified')
 need(p.get('boundary_closed') is True and p.get('simply_connected_domain') is True and p.get('boundary_sampling_qualified') is True,'closed qualified boundary required')
 number(p.get('boundary_alpha_min'),True);need(p.get('interior_displacements_used_for_inference_fit') is False,'boundary-only leakage')
 need(p.get('gauge_source')=='frozen_independent_convention','no interior post-hoc gauge fit')
 n=integer(p.get('fit_point_count'),1);m=integer(p.get('fit_coefficient_count'),1);nb=integer(p.get('boundary_point_count'),1);mb=integer(p.get('boundary_coefficient_count'),1)
 need(m<n and 2*mb<nb,'model order below point count')
 need(p.get('conditioning_accepted') is True,'conditioning required')
 for kind in ['fit','inference']:
  num=number(p.get(kind+'_squared_residual'));den=number(p.get(kind+'_squared_displacement'));need(num>=0 and den>0,'undefined normalized residual')
  ident(p.get(kind+'_result_id'))
 need(p['fit_result_id']!=p['inference_result_id'],'distinct analyses required')
 need(p.get('global_99_percent_threshold') is False and p.get('ideal_alpha_as_safety_limit') is False,'literature not universal acceptance/safety')
 return True

def nonmanual(p):
 need(set(p.get('branch_status',{}))==set(NONMANUAL),'all nonmanual branches accounted')
 need(all(v=='documented_unexecuted' for v in p['branch_status'].values()),'no numerical execution implied')
 need(p.get('conflicts')==['C01','C02','C03','C04','C05'],'all source conflicts preserved')
 for k in ['source_archives_inspected','source_solver_executed','physical_actuator_invented','source_simulation_as_measurement']:need(p.get(k) is False,'nonmanual scope: '+k)
 need(p.get('printed_units_preserved') is True and p.get('final_figure_equivalence')=='unverified','source version and units boundary');return True

def repeats(p,plan):
 policy(plan);need(p.get('policy_id')==plan['policy_id'],'frozen repeat policy identity');need(p.get('unit')=='specimen_and_cycle','frames not independent n')
 ids=unique(p.get('specimen_ids'));need(len(ids)==plan['independent_specimens'],'independent specimen count')
 runs=p.get('runs');need(type(runs) is list and len({r.get('run_id') for r in runs})==len(runs),'distinct run IDs')
 expected={(s,b) for s in ids for b in PHYSICAL};counts={key:0 for key in expected}
 states=set()
 for r in runs:
  ident(r.get('run_id'));ident(r.get('condition_state_id'));state=(r.get('specimen_id'),r['condition_state_id']);need(state not in states,'every same-specimen cycle advances state');states.add(state)
  need((r.get('specimen_id'),r.get('branch_id')) in counts,'declared specimen and branch');counts[(r['specimen_id'],r['branch_id'])]+=1
  need(r.get('status') in ('accepted','failed','blocked'),'all result dispositions explicit');ident(r.get('condition_state_id'))
 need(all(n==plan['runs_per_condition'] for n in counts.values()),'complete frozen repeat allocation')
 need(p.get('failed_runs_retained') is True and p.get('order_policy_followed_or_deviation_recorded') is True,'failures and order history retained');return True

def retry(p,old):
 for k in ['new_attempt_id','new_run_id','new_raw_manifest_digest','prior_failure_id','current_calibration_id']:ident(p.get(k))
 need(p['new_attempt_id']!=old.get('attempt_id') and p['new_run_id']!=old.get('run_id') and p['new_raw_manifest_digest']!=old.get('raw_manifest_digest'),'fresh retry identities')
 need(p['prior_failure_id']==old.get('failure_id') and p.get('policy_id')==old.get('policy_id'),'failure and prospective policy preserved')
 need(p.get('old_raw_retained') is True and p.get('authorized_by_frozen_plan') is True,'retry scope and retained raw');return True

def closeout(p):
 need(set(p.get('branch_dispositions',{}))==set(BRANCHES),'all nine branches accounted')
 allowed={'documented_unexecuted','evidence_reviewed','failed','blocked','not_started'}
 need(all(v in allowed for v in p['branch_dispositions'].values()),'truthful branch disposition')
 need(all(p['branch_dispositions'][b]=='documented_unexecuted' for b in NONMANUAL),'nonmanual source remains unexecuted')
 need(p.get('raw_and_failures_retained') is True and p.get('scientific_success_required') is False,'failure closeout independent of analysis')
 need(p.get('physical_execution_claim') is False and p.get('whole_paper_success_claim') is False,'metadata not physical success')
 if p.get('disposition')=='prephysical_cancelled':
  need(p.get('specimen_id') is None and p.get('carrier_id') is None and p.get('actual_custody_station') is None,'no invented prephysical custody')
  need(p.get('station_occupied') is False and p.get('active_leases')==[] and p.get('execution_complete') is False,'cancelled before acquisition')
  need(all(p['branch_dispositions'][b] in ('not_started','blocked','failed') for b in BRANCHES if b not in NONMANUAL),'prephysical branches not completed');return True
 ident(p.get('actual_custody_station'));ident(p.get('specimen_id'));ident(p.get('carrier_id'))
 if p.get('disposition')=='supported_hold':
  need(p.get('safe_state')=='unresolved' and p.get('supported') is True and p.get('robot_outside_guard') is True,'guarded supported hold')
  hold_leases={'S01':[],'S02':['S02'],'S03':['S03'],'S04':['S04'],'S05':['S05'],'S08':[]}
  need(p['actual_custody_station'] in hold_leases and p.get('station_occupied') is True and p.get('active_leases')==hold_leases[p['actual_custody_station']],'unresolved custody and station-specific lease retained')
  need(p.get('execution_complete') is False and p.get('unloaded_claim') is False,'hold not completed safe return')
 elif p.get('disposition')=='safe_returned':
  need(p.get('unloaded_observed') is True and p.get('disarmed_observed') is True and p.get('safe_release_observed') is True,'independent safe return evidence')
  need(p.get('station_occupied') is False and p.get('active_leases')==[],'reconcile leases and occupancy')
  need(p.get('actual_custody_station')=='S08' and p.get('destination_identity_verified') is True,'confirmed destination custody')
  for k in ['safe_release_receipt_id','return_custody_receipt_id','disposition_receipt_id']:ident(p.get(k))
 else:need(False,'explicit closeout disposition')
 return True

# Canonical finite fixtures use arbitrary values unrelated to source conditions.
CTX={'specimen_id':'synthetic-specimen-a','fixture_id':'synthetic-foot','branch_id':'B02','conditioning_state_id':'synthetic-state-1','configuration_epoch':1,'run_id':'synthetic-run-1','carrier_id':'synthetic-carrier-a','cad_revision':'synthetic-cad','print_job_id':'synthetic-print'}
def observed(role,**fields):return {'receipt_id':'synthetic-'+role,'role':role,'issuer':'independent_fixture_evaluator','status':'observed','context':deepcopy(CTX),'synthetic':True,**fields}
def synthetic_plan():return {'policy_id':'synthetic-policy','frozen_before_outcomes':True,'outcomes_seen':0,'independent_specimens':1,'runs_per_condition':1,'repeat_unit':'specimen_and_cycle','condition_order':['B02','B03'],'reset_policy_id':'r','stop_policy_id':'s','uncertainty_policy_id':'u','metric_policy_id':'m','model_order_policy_id':'o','exclusion_policy_id':'e','repeat_until_good':False}
def synthetic_closeout(hold=False):
 x={'branch_dispositions':{b:('documented_unexecuted' if b in NONMANUAL else 'blocked') for b in BRANCHES},'raw_and_failures_retained':True,'scientific_success_required':False,'physical_execution_claim':False,'whole_paper_success_claim':False,'specimen_id':CTX['specimen_id'],'carrier_id':CTX['carrier_id'],'execution_complete':False}
 if hold:x.update(disposition='supported_hold',safe_state='unresolved',supported=True,robot_outside_guard=True,station_occupied=True,active_leases=['S05'],actual_custody_station='S05',unloaded_claim=False)
 else:x.update(disposition='safe_returned',unloaded_observed=True,disarmed_observed=True,safe_release_observed=True,station_occupied=False,active_leases=[],actual_custody_station='S08',destination_identity_verified=True,safe_release_receipt_id='release',return_custody_receipt_id='return',disposition_receipt_id='disp')
 return x

def synthetic_registry():
 r={}
 r['R01']=synthetic_plan()
 r['R02']=observed('fabrication_completion',beam_material_lot_id='b',pad_material_lot_id='p',foot_material_lot_id='f',pad_layout_revision='pads',foot_id='foot',postprocess_receipt_id='post',inspection_receipt_id='inspect',safe_release_receipt_id='release',dimensions_accepted=True,condition_accepted=True,closed_qualified_service=True,source_cad_inferred_from_figure=False)
 r['R03']=observed('fixture_inspection',drawing_revision='draw',contact_registry_id='contact',mount_inspection_id='mount',locked=True,geometry_verified=True)
 r['R04']=observed('contact_conditioning',contact_preparation_id='prep',recovery_policy_id='recover',environment_record_id='env',history_retained=True,condition_accepted=True,method='no_treatment_approved',unknown_powder_handling=False)
 r['R05']=observed('supported_custody',source_station='S03',source_slot='a',destination_station='S05',destination_slot='dock',transform_revision='transform',retention_receipt_id='retain',safe_release_receipt_id='release',custody_event_id='move',source_occupant=CTX['specimen_id'],source_carrier=CTX['carrier_id'],destination_empty=True,supported=True,retained=True,safe_release_observed=True,moving_or_loaded=False,grasp_surface='carrier_support_interface')
 r['R06']=observed('mechanics_ready',calibration_id='mech',load_cell_id='cell',unloaded_reference_id='ref',contact_zero_id='zero',safe_stop_policy_id='stop',limit_policy_id='limits',interlock_ready=True,fixture_locked=True,source_stroke_as_safety_limit=False,force_limit=7,stroke_limit=3,speed_limit=2,qualified_limits=True)
 r['R07']=observed('imaging_ready',camera_id='camera',lens_id='lens',calibration_id='image',reference_image_id='reference',exposure_settings_id='exposure',distortion_map_id='distortion',uncertainty_policy_id='uncertainty',drift_check_id='drift',field_of_view_accepted=True,focus_accepted=True,visible_square_ids=['sq-a','sq-b'],source_accuracy_used_as_calibration=False)
 r['R08']=observed('synchronized_arming',mechanics_calibration_id='mech',camera_calibration_id='image',clock_mapping_id='clock',endpoint_policy_id='endpoint',capture_ready=True,buffer_ready=True,mechanics_ready=True,active_resources=['S05','S06'],foreign_leases=[],capture_ready_time=5,machine_start_time=6,clock_scale=1,clock_offset=4,clock_tolerance=0.001,phase_policy=['loading','unloading'],qualified_program_id='program-a')
 frames=[{'frame_id':'f'+str(i),'machine_event_id':'m'+str(i),'run_id':CTX['run_id'],'raw_sha256':str(i)*64,'camera_time':i+2,'machine_time':i+6,'phase':'loading' if i==0 else 'unloading','accepted':True,'retained_original':True} for i in range(2)]
 r['R09']=observed('cycle_acquisition',clock_mapping_id='clock',raw_manifest_digest='raw-a',expected_frame_ids=['f0','f1'],frames=frames,machine_event_ids=['m0','m1'],clock_scale=1,clock_offset=4,clock_tolerance=.001,aborted=False,drop_events_accounted=True,source_400_forced=False,source_playback_as_acquisition_clock=False,planned_stroke=2,planned_speed=1,qualified_program_id='program-a')
 r['R10']=observed('unload_recovery',unloaded_observed=True,disarmed_observed=True,new_conditioning_state_id='synthetic-state-2',history_retained=True,virgin_restored_by_unload=False,damage_inspection_id='damage',residual_deformation_record_id='residual',adhesion_record_id='adhesion',recovery_policy_id='recover',disposition='hold',completed_cycle_count=1)
 r['R11']=observed('fixture_change',unloaded_observed=True,disarmed_observed=True,active_leases=[],new_fixture_id='synthetic-bridge',new_configuration_epoch=2,invalidated=['docking','mechanics','imaging','synchronization'],new_run_id='synthetic-run-2',new_specimen_id=CTX['specimen_id'],treatment_or_conditioning_changed=False,preparation_reentry=[],downstream_reentry=['R05','R06','R07','R08','R09','R10'],old_preparation_receipts_reused=True,history_retained=True)
 r['R12']=observed('registered_tracking',raw_manifest_digest='raw-a',camera_calibration_id='image',clock_mapping_id='clock',tracking_revision='track',coordinate_convention_id='coordinate',quality_mask_digest='mask',uncertainty_policy_id='uncertainty',source_code_inspected_or_independent_validated=True,raw_immutable=True,rejected_tracks_retained=True,outcome_driven_filtering=False,retained_phases=['loading','unloading'])
 r['R13']=observed('separate_analysis',modality='physical',tracking_digest='track',coordinate_convention_id='coordinate',registration_policy_id='registration',metric_policy_id='metric',uncertainty_policy_id='uncertainty',model_order_policy_id='order',policy_frozen_before_outcomes=True,resolved_conflicts=['C01','C04'],expert_interpretation_receipt_id='expert',silent_source_correction=False,area_variable='J_area',linear_variable='alpha_linear',detF_min=.7,local_inversion_or_collapse=False,global_geometry_status='unverified',global_geometry_claim=False,boundary_closed=True,simply_connected_domain=True,boundary_sampling_qualified=True,boundary_alpha_min=.8,interior_displacements_used_for_inference_fit=False,gauge_source='frozen_independent_convention',fit_point_count=30,fit_coefficient_count=3,boundary_point_count=20,boundary_coefficient_count=3,conditioning_accepted=True,fit_squared_residual=3,fit_squared_displacement=10,inference_squared_residual=5,inference_squared_displacement=10,fit_result_id='fit',inference_result_id='inference',global_99_percent_threshold=False,ideal_alpha_as_safety_limit=False)
 r['R14']={'branch_status':{b:'documented_unexecuted' for b in NONMANUAL},'conflicts':['C01','C02','C03','C04','C05'],'source_archives_inspected':False,'source_solver_executed':False,'physical_actuator_invented':False,'source_simulation_as_measurement':False,'printed_units_preserved':True,'final_figure_equivalence':'unverified'}
 r['R15']={'policy_id':'synthetic-policy','unit':'specimen_and_cycle','specimen_ids':[CTX['specimen_id']],'runs':[{'run_id':'rep-'+b,'specimen_id':CTX['specimen_id'],'branch_id':b,'status':'blocked','condition_state_id':'state-'+b} for b in PHYSICAL],'failed_runs_retained':True,'order_policy_followed_or_deviation_recorded':True}
 r['R16']=synthetic_closeout()
 return r

_CANONICAL=synthetic_registry();_PIN=hashof(_CANONICAL)
def synthetic_messages():return [{'event_id':'event-'+op,'operation_id':op,'evidence_id':'evidence-'+op} for op in OPERATIONS]
def evaluate(messages,registry=None):
 registry=deepcopy(_CANONICAL) if registry is None else registry
 need(hashof(registry)==_PIN,'evaluator fixture registry changed')
 need(type(messages) is list and len(messages)==len(OPERATIONS),'complete finite replay')
 seen=set()
 validators=[lambda p:policy(p),lambda p:preparation(p,CTX),lambda p:fixture(p,CTX),lambda p:contact(p,CTX),lambda p:custody(p,CTX),lambda p:mechanics(p,CTX),lambda p:imaging(p,CTX),lambda p:arming(p,CTX),lambda p:acquisition(p,CTX),lambda p:recovery(p,CTX),lambda p:fixture_change(p,CTX),lambda p:tracking(p,CTX),lambda p:analysis(p,CTX),lambda p:nonmanual(p),lambda p:repeats(p,registry['R01']),lambda p:closeout(p)]
 for op,m,fn in zip(OPERATIONS,messages,validators):
  exact_keys(m,['event_id','operation_id','evidence_id']);ident(m['event_id']);need(m['event_id'] not in seen,'duplicate actor event');seen.add(m['event_id'])
  need(m['operation_id']==op and m['evidence_id']=='evidence-'+op,'pinned operation evidence order');fn(registry[op])
 synchronized_cycle(registry['R06'],registry['R07'],registry['R08'],registry['R09'],CTX)
 return {'status':'SYNTHETIC_METADATA_ACCEPTED','operation_templates_checked':16,'paper_designs':1,'physical_execution':False,'physical_simulation':False,'scientific_reproduction':False,'validated_runnable_whole_paper_tasks':0,'production_actor_isolation':False}
