"""Independent adversarial tests of finite metadata, never mechanics or hardware."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('independent_conformal_contract', ROOT/'tests'/'contract.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def context():
    return dict(specimen_id='review-specimen',fixture_id='review-foot',branch_id='B02',
                conditioning_state_id='review-state-1',configuration_epoch=4,run_id='review-run',
                carrier_id='review-carrier',cad_revision='review-cad',print_job_id='review-job')


def receipt(role, **data):
    return dict(receipt_id='review-'+role,role=role,issuer='independent_fixture_evaluator',
                status='observed',context=context(),synthetic=True,**data)


def plan():
    return dict(policy_id='review-policy',frozen_before_outcomes=True,outcomes_seen=0,
                independent_specimens=1,runs_per_condition=1,repeat_unit='specimen_and_cycle',
                condition_order=['B03','B02'],reset_policy_id='reset',stop_policy_id='stop',
                uncertainty_policy_id='uncertainty',metric_policy_id='metric',model_order_policy_id='order',
                exclusion_policy_id='exclude',repeat_until_good=False)


def mechanics():
    return receipt('mechanics_ready',calibration_id='review-mechanics',load_cell_id='review-cell',
        unloaded_reference_id='review-reference',contact_zero_id='review-contact',safe_stop_policy_id='stop',
        limit_policy_id='limits',interlock_ready=True,fixture_locked=True,source_stroke_as_safety_limit=False,
        force_limit=9,stroke_limit=4,speed_limit=3,qualified_limits=True)


def imaging():
    return receipt('imaging_ready',camera_id='camera',lens_id='lens',calibration_id='review-camera',
        reference_image_id='image',exposure_settings_id='exposure',distortion_map_id='map',
        uncertainty_policy_id='uncertainty',drift_check_id='drift',field_of_view_accepted=True,
        focus_accepted=True,visible_square_ids=['one','two','three'],source_accuracy_used_as_calibration=False)


def arming():
    return receipt('synchronized_arming',mechanics_calibration_id='review-mechanics',
        camera_calibration_id='review-camera',clock_mapping_id='review-clock',endpoint_policy_id='endpoint',
        capture_ready=True,buffer_ready=True,mechanics_ready=True,active_resources=['S05','S06'],
        foreign_leases=[],capture_ready_time=20,machine_start_time=21,clock_scale=2,clock_offset=1,
        clock_tolerance=.01,phase_policy=['loading','unloading'],qualified_program_id='review-program')


def acquisition():
    frames=[]
    for i in range(4):
        frames.append(dict(frame_id='frame-'+str(i),machine_event_id='event-'+str(i),run_id=context()['run_id'],
            raw_sha256=hashlib.sha256(('independent '+str(i)).encode()).hexdigest(),camera_time=10+i,
            machine_time=21+2*i,phase='loading' if i<2 else 'unloading',accepted=i!=1,retained_original=True))
    return receipt('cycle_acquisition',clock_mapping_id='review-clock',raw_manifest_digest='review-raw',
        expected_frame_ids=[f['frame_id'] for f in frames],frames=frames,
        machine_event_ids=[f['machine_event_id'] for f in frames],clock_scale=2,clock_offset=1,
        clock_tolerance=.01,aborted=False,drop_events_accounted=True,source_400_forced=False,
        source_playback_as_acquisition_clock=False,qualified_program_id='review-program',planned_stroke=3,planned_speed=2)


def analysis():
    return receipt('separate_analysis',modality='physical',tracking_digest='tracks',coordinate_convention_id='coords',
        registration_policy_id='register',metric_policy_id='metric',uncertainty_policy_id='uncertainty',
        model_order_policy_id='model',policy_frozen_before_outcomes=True,resolved_conflicts=['C01','C04'],
        expert_interpretation_receipt_id='expert',silent_source_correction=False,area_variable='J_area',
        linear_variable='alpha_linear',detF_min=.5,local_inversion_or_collapse=False,
        global_geometry_status='unverified',global_geometry_claim=False,boundary_closed=True,
        simply_connected_domain=True,boundary_sampling_qualified=True,boundary_alpha_min=.6,
        interior_displacements_used_for_inference_fit=False,gauge_source='frozen_independent_convention',
        fit_point_count=31,fit_coefficient_count=4,boundary_point_count=25,boundary_coefficient_count=4,
        conditioning_accepted=True,fit_squared_residual=2,fit_squared_displacement=13,
        inference_squared_residual=7,inference_squared_displacement=13,fit_result_id='fit',
        inference_result_id='infer',global_99_percent_threshold=False,ideal_alpha_as_safety_limit=False)


def repeat_records():
    return dict(policy_id='review-policy',unit='specimen_and_cycle',specimen_ids=['review-specimen'],
        runs=[dict(run_id='run-'+b,specimen_id='review-specimen',branch_id=b,status='blocked',
                   condition_state_id='state-'+b) for b in ('B03','B02')],
        failed_runs_retained=True,order_policy_followed_or_deviation_recorded=True)


def hold():
    return dict(branch_dispositions={b:'documented_unexecuted' if b in C.NONMANUAL else 'blocked' for b in C.BRANCHES},
        raw_and_failures_retained=True,scientific_success_required=False,physical_execution_claim=False,
        whole_paper_success_claim=False,actual_custody_station='S05',specimen_id='review-specimen',
        carrier_id='review-carrier',disposition='supported_hold',safe_state='unresolved',supported=True,
        robot_outside_guard=True,station_occupied=True,active_leases=['S05'],execution_complete=False,unloaded_claim=False)


class IndependentDesignTests(unittest.TestCase):
    def test_exact_scope_counts(self):
        self.assertEqual({o['id'] for o in read('operations.json')['operations']},{'R%02d'%i for i in range(1,17)})
        self.assertEqual({b['id'] for b in read('branches.json')['branches']},{'B%02d'%i for i in range(1,10)})
        self.assertEqual({s['id'] for s in read('station_contracts.json')['stations']},{'S%02d'%i for i in range(1,9)})
        self.assertEqual({x['id'] for x in read('source_parameters.json')['facts']},{'F%02d'%i for i in range(1,29)})
        self.assertEqual({x['id'] for x in read('controls_and_repeats.json')['controls']},{'K%02d'%i for i in range(1,10)})
        self.assertEqual({x['id'] for x in read('source_conflicts.json')['conflicts']},{'C%02d'%i for i in range(1,6)})
        self.assertEqual({a for o in read('operations.json')['operations'] for a in o['asset_ids']},{'A%02d'%i for i in range(1,13)})

    def test_only_two_physical_experiments_and_four_nonmanual_branches(self):
        bs=read('branches.json');rows=bs['branches']
        self.assertEqual({b['id'] for b in rows if b['classification']=='physical_experiment'},{'B02','B03'})
        self.assertEqual(set(bs['nonmanual_source_scope_ids']),{'B04','B05','B07','B08'})
        self.assertTrue(all(b['execution_status']=='DOCUMENTED_UNEXECUTED' for b in rows if b['id'] in C.NONMANUAL))

    def test_source_values_are_references_not_commands(self):
        bs={b['id']:b for b in read('branches.json')['branches']}
        for b,stroke,speed in [('B02',20,.1),('B03',40,.2)]:
            r=bs[b]['source_reference_cycle']
            self.assertEqual((r['stroke_mm'],r['speed_mm_s'],r['acquisition_fps'],r['playback_fps']),(stroke,speed,1,30))
            self.assertFalse(r['hardware_command']);self.assertFalse(r['safety_threshold'])

    def test_source_and_authored_requirement_classes(self):
        ops=read('operations.json')['operations'];facts={f['id'] for f in read('source_parameters.json')['facts']}
        self.assertTrue(all(o['classification']=='authored_robot_translation' for o in ops))
        self.assertTrue(all(o['runtime']=='unimplemented' and not o['physical_execution_qualified'] for o in ops))
        self.assertTrue(all(set(o['source_anchors'])<=facts for o in ops))
        self.assertTrue(read('evidence_map.json')['source_outcomes_are_never_observations'])
        self.assertEqual(read('RELEASE_BOUNDARY.json')['validated_runnable_whole_paper_tasks'],0)

    def test_dependency_dag_and_failure_closeout(self):
        data=read('operations.json');ops={o['id']:o for o in data['operations']};done=set();active=set()
        def visit(k):
            self.assertNotIn(k,active)
            if k in done:return
            active.add(k)
            for d in ops[k]['depends_on']:self.assertIn(d,ops);visit(d)
            active.remove(k);done.add(k)
        for k in ops:visit(k)
        self.assertTrue(read('lifecycle_contract.json')['failure_closeout_from_any_operation'])
        self.assertFalse(read('lifecycle_contract.json')['failure_requires_analysis_success'])
        self.assertTrue(all(o['failure_closeout'] for o in ops.values()))

    def test_all_unknowns_remain_execution_blocking(self):
        data=read('unknown_parameters.json');rows=data['unknowns']
        self.assertEqual({x['id'] for x in rows},{'U%02d'%i for i in range(1,17)})
        self.assertTrue(all(x['execution_blocking'] and x['physical_default'] is None and x['resolution_requires_independent_evidence'] for x in rows))
        self.assertTrue(data['null_blocks_execution'])

    def test_source_archive_and_movie_scope_is_honest(self):
        a=read('source_access_audit.json');d=a['data_code_archive_status']
        self.assertEqual(len(d['archives']),6);self.assertTrue(all(not x['contents_read'] for x in d['archives']))
        self.assertFalse(d['source_code_executed']);self.assertFalse(d['final_journal_figure_equivalence_verified'])
        self.assertEqual(len(a['media']),3)
        self.assertTrue(all(len(m['sampled_frame_numbers'])==5 and 'not continuous' in m['visual_review'] for m in a['media']))

    def test_actor_cannot_supply_observation_or_qualification_fields(self):
        a=read('agent_visible.json');e=read('evaluator_reference.json')
        self.assertEqual(set(a['permitted_actor_message_fields']),{'event_id','operation_id','evidence_id'})
        self.assertEqual(e['actor_visible_allowlist'],['agent_visible.json'])
        self.assertFalse(e['filesystem_isolation_implemented']);self.assertFalse(e['sensor_authentication_implemented'])

    def test_analysis_is_not_a_solver_or_universal_acceptance_test(self):
        a=read('analysis_contracts.json');b=a['boundary_inference']
        self.assertFalse(a['implemented_scientific_solver']);self.assertFalse(a['literature_99_percent_is_global_pass_threshold'])
        self.assertTrue(b['detF_positive_required']);self.assertTrue(b['global_injectivity_requires_separate_qualified_check'])
        self.assertTrue(b['alpha_linear_and_J_area_distinct']);self.assertTrue(a['no_silent_source_correction'])


class IndependentGuardTests(unittest.TestCase):
    def reject(self, fn, *args):
        with self.assertRaises(C.GuardError):fn(*args)

    def mutate(self, fn, baseline, changes, *args):
        for key,value in changes:
            with self.subTest(key=key,value=value):
                bad=copy.deepcopy(baseline);bad[key]=value;self.reject(fn,bad,*args)

    def test_independent_valid_policy(self):self.assertTrue(C.policy(plan()))

    def test_policy_rejects_retrospective_and_pseudoreplicated_plan(self):
        self.mutate(C.policy,plan(),[('frozen_before_outcomes',False),('outcomes_seen',1),('outcomes_seen',False),
            ('independent_specimens',0),('independent_specimens',True),('runs_per_condition',0),
            ('repeat_unit','frame'),('condition_order',['B02','B02']),('repeat_until_good',True),('metric_policy_id','')])

    def test_receipts_reject_request_actor_and_wrong_context(self):
        m=mechanics()
        self.mutate(C.mechanics,m,[('status','requested'),('issuer','actor'),('role','request'),('synthetic',False)],context())
        for key in ('specimen_id','fixture_id','conditioning_state_id','configuration_epoch','branch_id'):
            with self.subTest(key=key):
                p=mechanics();p['context'][key]='stale';self.reject(C.mechanics,p,context())

    def test_epoch_bool_is_not_integer_epoch(self):
        c=context();c['configuration_epoch']=1;p=mechanics();p['context']['configuration_epoch']=True
        self.reject(C.mechanics,p,c)

    def test_mechanics_limits_interlocks_and_zeros(self):
        self.assertTrue(C.mechanics(mechanics(),context()))
        self.mutate(C.mechanics,mechanics(),[('force_limit',0),('stroke_limit',float('nan')),('speed_limit',float('inf')),
            ('interlock_ready',False),('fixture_locked',False),('qualified_limits',False),
            ('source_stroke_as_safety_limit',True),('contact_zero_id','review-reference')],context())

    def test_imaging_requires_visibility_and_actual_qualification(self):
        self.assertTrue(C.imaging(imaging(),context()))
        self.mutate(C.imaging,imaging(),[('visible_square_ids',[]),('visible_square_ids',['one','one']),
            ('field_of_view_accepted',False),('focus_accepted',False),('source_accuracy_used_as_calibration',True),
            ('distortion_map_id',''),('uncertainty_policy_id','')],context())

    def test_arming_requires_joint_resources_and_capture_before_motion(self):
        self.assertTrue(C.arming(arming(),context()))
        self.mutate(C.arming,arming(),[('capture_ready',False),('buffer_ready',False),('mechanics_ready',False),
            ('active_resources',['S05']),('foreign_leases',['other']),('machine_start_time',19),
            ('clock_scale',0),('clock_tolerance',-.1),('phase_policy',['loading'])],context())

    def test_acquisition_requires_bijection_order_clocks_and_raw(self):
        self.assertTrue(C.acquisition(acquisition(),context()))
        p=acquisition();p['frames'].reverse();self.reject(C.acquisition,p,context())
        p=acquisition();p['frames'].pop();self.reject(C.acquisition,p,context())
        for k,v in [('machine_event_id','foreign'),('run_id','foreign'),('raw_sha256','missing'),
                    ('camera_time',50),('machine_time',100),('retained_original',False),('accepted',1)]:
            with self.subTest(key=k):
                p=acquisition();p['frames'][1][k]=v;self.reject(C.acquisition,p,context())

    def test_acquisition_keeps_both_phases_and_never_forces_source_frames(self):
        for phase in ('loading','unloading'):
            p=acquisition()
            for f in p['frames']:f['phase']=phase
            self.reject(C.acquisition,p,context())
        p=acquisition();p['frames'][0]['phase']='unloading';self.reject(C.acquisition,p,context())
        self.mutate(C.acquisition,acquisition(),[('drop_events_accounted',False),('source_400_forced',True),
            ('source_playback_as_acquisition_clock',True)],context())

    def test_aborted_cycle_requires_failure_and_partial_retention(self):
        p=acquisition();p.update(aborted=True,failure_id='failure',partial_data_retained=True)
        self.assertTrue(C.acquisition(p,context()))
        self.mutate(C.acquisition,p,[('failure_id',''),('partial_data_retained',False)],context())

    def test_composed_cycle_joins_calibration_clock_and_epoch(self):
        self.assertTrue(C.synchronized_cycle(mechanics(),imaging(),arming(),acquisition(),context()))
        for target,key,value in [('arming','mechanics_calibration_id','wrong'),('arming','camera_calibration_id','wrong'),
             ('acquisition','clock_mapping_id','wrong'),('acquisition','clock_tolerance',.02)]:
            with self.subTest(target=target,key=key):
                records=dict(mechanics=mechanics(),imaging=imaging(),arming=arming(),acquisition=acquisition())
                records[target][key]=value
                self.reject(C.synchronized_cycle,records['mechanics'],records['imaging'],records['arming'],records['acquisition'],context())
        p=imaging();p['context']['configuration_epoch']=3
        self.reject(C.synchronized_cycle,mechanics(),p,arming(),acquisition(),context())

    def test_composed_cycle_rejects_prestart_and_retimed_acquisition(self):
        p=acquisition();p['frames'][0].update(camera_time=9,machine_time=19)
        self.reject(C.synchronized_cycle,mechanics(),imaging(),arming(),p,context())
        p=acquisition();p['clock_offset']=2
        for f in p['frames']:f['machine_time']+=1
        self.reject(C.synchronized_cycle,mechanics(),imaging(),arming(),p,context())

    def test_composed_cycle_rejects_unqualified_or_mismatched_program(self):
        for key,value in [('qualified_program_id','foreign'),('planned_stroke',5),('planned_speed',4),('planned_stroke',0)]:
            with self.subTest(key=key):
                p=acquisition();p[key]=value
                self.reject(C.synchronized_cycle,mechanics(),imaging(),arming(),p,context())

    def test_preparation_is_completion_with_material_and_part_lineage(self):
        p=receipt('fabrication_completion',beam_material_lot_id='beam',pad_material_lot_id='pad',foot_material_lot_id='foot',
            pad_layout_revision='layout',foot_id='foot-part',postprocess_receipt_id='post',inspection_receipt_id='inspect',
            safe_release_receipt_id='release',dimensions_accepted=True,condition_accepted=True,closed_qualified_service=True,
            source_cad_inferred_from_figure=False)
        self.assertTrue(C.preparation(p,context()))
        self.mutate(C.preparation,p,[('status','requested'),('pad_material_lot_id',''),('inspection_receipt_id',''),
            ('closed_qualified_service',False),('source_cad_inferred_from_figure',True),('dimensions_accepted',False)],context())

    def test_contact_treatment_and_bridge_do_not_inherit_unknown_powder(self):
        p=receipt('contact_conditioning',contact_preparation_id='prep',recovery_policy_id='recover',environment_record_id='env',
            history_retained=True,condition_accepted=True,method='no_treatment_approved',unknown_powder_handling=False)
        self.assertTrue(C.contact(p,context()))
        self.mutate(C.contact,p,[('unknown_powder_handling',True),('history_retained',False),('method','source_powder')],context())
        c=context();c['branch_id']='B03';p['context']=c;self.reject(C.contact,p,c)
        p['bridge_treatment_policy_id']='bridge';self.assertTrue(C.contact(p,c))
        p['method']='qualified_service_treatment';self.reject(C.contact,p,c)
        p.update(material_identity='review-material',sds_review_id='sds',application_service_id='service',cleanup_policy_id='clean',closed_qualified_service=True)
        self.assertTrue(C.contact(p,c))

    def test_custody_requires_observed_identity_support_vacancy_and_release(self):
        p=receipt('supported_custody',source_station='S03',source_slot='rack',destination_station='S05',destination_slot='dock',
            transform_revision='transform',retention_receipt_id='retain',safe_release_receipt_id='release',custody_event_id='move',
            source_occupant=context()['specimen_id'],source_carrier=context()['carrier_id'],destination_empty=True,supported=True,
            retained=True,safe_release_observed=True,moving_or_loaded=False,grasp_surface='carrier_support_interface')
        self.assertTrue(C.custody(p,context()))
        self.mutate(C.custody,p,[('source_occupant','other'),('source_carrier','other'),('destination_empty',False),
            ('supported',False),('retained',False),('safe_release_observed',False),('moving_or_loaded',True),('grasp_surface','hinge')],context())

    def test_fixture_change_requires_fresh_ids_epoch_and_preparation_reentry(self):
        p=receipt('fixture_change',unloaded_observed=True,disarmed_observed=True,active_leases=[],new_fixture_id='bridge',
            new_configuration_epoch=5,invalidated=['docking','mechanics','imaging','synchronization'],new_run_id='new-run',
            new_specimen_id='replacement',treatment_or_conditioning_changed=False,preparation_reentry=['R02','R03','R04'],
            downstream_reentry=['R05','R06','R07','R08','R09','R10'],old_preparation_receipts_reused=False,history_retained=True)
        self.assertTrue(C.fixture_change(p,context()))
        self.mutate(C.fixture_change,p,[('new_configuration_epoch',4),('new_run_id',context()['run_id']),
            ('old_preparation_receipts_reused',True),('preparation_reentry',[]),('downstream_reentry',['R05']),
            ('active_leases',['S05']),('unloaded_observed',False),('invalidated',['mechanics'])],context())

    def test_changed_treatment_requires_repreparation_even_for_same_specimen(self):
        p=C.synthetic_registry()['R11'];p['treatment_or_conditioning_changed']=True
        self.reject(C.fixture_change,p,C.CTX)
        p['preparation_reentry']=['R03','R04'];self.assertTrue(C.fixture_change(p,C.CTX))

    def test_recovery_cannot_reset_history_or_reuse_without_acceptance(self):
        p=receipt('unload_recovery',unloaded_observed=True,disarmed_observed=True,new_conditioning_state_id='new-state',
            history_retained=True,virgin_restored_by_unload=False,damage_inspection_id='damage',residual_deformation_record_id='residual',
            adhesion_record_id='adhesion',recovery_policy_id='recover',disposition='quarantine',completed_cycle_count=1)
        self.assertTrue(C.recovery(p,context()))
        self.mutate(C.recovery,p,[('new_conditioning_state_id',context()['conditioning_state_id']),('virgin_restored_by_unload',True),
            ('history_retained',False),('completed_cycle_count',0),('disposition','reuse_qualified')],context())

    def test_tracking_requires_raw_parents_and_both_phases(self):
        p=receipt('registered_tracking',raw_manifest_digest='raw',camera_calibration_id='camera',clock_mapping_id='clock',
            tracking_revision='tracking',coordinate_convention_id='coords',quality_mask_digest='mask',uncertainty_policy_id='uncertainty',
            source_code_inspected_or_independent_validated=True,raw_immutable=True,rejected_tracks_retained=True,
            outcome_driven_filtering=False,retained_phases=['loading','unloading'])
        self.assertTrue(C.tracking(p,context()))
        self.mutate(C.tracking,p,[('raw_manifest_digest',''),('source_code_inspected_or_independent_validated',False),
            ('raw_immutable',False),('rejected_tracks_retained',False),('outcome_driven_filtering',True),('retained_phases',['unloading'])],context())

    def test_analysis_boundary_leakage_gauge_and_source_conflict_guards(self):
        self.assertTrue(C.analysis(analysis(),context()))
        self.mutate(C.analysis,analysis(),[('interior_displacements_used_for_inference_fit',True),('gauge_source','fit_to_interior'),
            ('resolved_conflicts',[]),('expert_interpretation_receipt_id',None),('silent_source_correction',True),
            ('modality','numerical'),('policy_frozen_before_outcomes',False)],context())

    def test_analysis_orientation_and_global_geometry_are_distinct(self):
        self.mutate(C.analysis,analysis(),[('detF_min',0),('detF_min',-.2),('detF_min',float('nan')),
            ('local_inversion_or_collapse',True),('global_geometry_claim',True),('global_geometry_status','assumed')],context())
        p=analysis();p['global_geometry_status']='verified_by_qualified_method';self.reject(C.analysis,p,context())
        p['global_geometry_receipt_id']='qualified-global-check';self.assertTrue(C.analysis(p,context()))

    def test_analysis_closed_domain_positive_dilation_and_model_order(self):
        self.mutate(C.analysis,analysis(),[('boundary_closed',False),('simply_connected_domain',False),('boundary_sampling_qualified',False),
            ('boundary_alpha_min',0),('area_variable','alpha_linear'),('linear_variable','J_area'),('fit_coefficient_count',31),
            ('boundary_coefficient_count',13),('conditioning_accepted',False)],context())

    def test_analysis_undefined_errors_and_universal_thresholds_rejected(self):
        self.mutate(C.analysis,analysis(),[('fit_squared_displacement',0),('inference_squared_displacement',0),
            ('fit_squared_residual',-1),('inference_squared_residual',float('inf')),('fit_result_id','infer'),
            ('global_99_percent_threshold',True),('ideal_alpha_as_safety_limit',True)],context())

    def test_nonmanual_scope_never_becomes_execution(self):
        p=dict(branch_status={b:'documented_unexecuted' for b in C.NONMANUAL},conflicts=['C01','C02','C03','C04','C05'],
            source_archives_inspected=False,source_solver_executed=False,physical_actuator_invented=False,
            source_simulation_as_measurement=False,printed_units_preserved=True,final_figure_equivalence='unverified')
        self.assertTrue(C.nonmanual(p))
        self.mutate(C.nonmanual,p,[('source_archives_inspected',True),('source_solver_executed',True),('physical_actuator_invented',True),
            ('source_simulation_as_measurement',True),('printed_units_preserved',False),('final_figure_equivalence','verified'),('conflicts',[])])
        p['branch_status']['B04']='executed';self.reject(C.nonmanual,p)

    def test_repeats_require_independent_specimens_complete_allocation_and_failures(self):
        self.assertTrue(C.repeats(repeat_records(),plan()))
        self.mutate(C.repeats,repeat_records(),[('unit','frame'),('specimen_ids',['review-specimen','review-specimen']),
            ('failed_runs_retained',False),('order_policy_followed_or_deviation_recorded',False),('policy_id','posthoc')],plan())
        p=repeat_records();p['runs'].pop();self.reject(C.repeats,p,plan())

    def test_repeats_require_nonempty_unique_run_ids_and_advancing_states(self):
        for value in (None,''):
            p=repeat_records();p['runs'][0]['run_id']=value;self.reject(C.repeats,p,plan())
        p=repeat_records();p['runs'][1]['run_id']=p['runs'][0]['run_id'];self.reject(C.repeats,p,plan())
        p=repeat_records();p['runs'][1]['condition_state_id']=p['runs'][0]['condition_state_id'];self.reject(C.repeats,p,plan())

    def test_retry_retains_failure_and_requires_fresh_identities(self):
        old=dict(attempt_id='old-attempt',run_id='old-run',raw_manifest_digest='old-raw',failure_id='failure',policy_id='policy')
        p=dict(new_attempt_id='new-attempt',new_run_id='new-run',new_raw_manifest_digest='new-raw',prior_failure_id='failure',
            current_calibration_id='current',policy_id='policy',old_raw_retained=True,authorized_by_frozen_plan=True)
        self.assertTrue(C.retry(p,old))
        self.mutate(C.retry,p,[('new_attempt_id','old-attempt'),('new_run_id','old-run'),('new_raw_manifest_digest','old-raw'),
            ('prior_failure_id','other'),('old_raw_retained',False),('authorized_by_frozen_plan',False)],old)

    def test_hold_cannot_be_claimed_complete_or_unloaded(self):
        self.assertTrue(C.closeout(hold()))
        self.mutate(C.closeout,hold(),[('execution_complete',True),('unloaded_claim',True),('supported',False),
            ('robot_outside_guard',False),('station_occupied',False),('active_leases',[]),('safe_state','safe')])

    def test_hold_lease_matches_actual_custody_station(self):
        p=hold();p['actual_custody_station']='S03';self.reject(C.closeout,p)

    def test_station_specific_holds_keep_actual_custody(self):
        for station,leases in [('S01',[]),('S02',['S02']),('S03',['S03']),('S04',['S04']),('S05',['S05']),('S08',[])]:
            with self.subTest(station=station):
                p=hold();p.update(actual_custody_station=station,active_leases=leases)
                self.assertTrue(C.closeout(p))

    def test_prephysical_failure_does_not_invent_specimen_or_safe_return(self):
        p=hold();p.update(disposition='prephysical_cancelled',specimen_id=None,carrier_id=None,
            actual_custody_station=None,station_occupied=False,active_leases=[],execution_complete=False)
        self.assertTrue(C.closeout(p))
        self.mutate(C.closeout,p,[('specimen_id','invented'),('carrier_id','invented'),('station_occupied',True),
            ('active_leases',['S05']),('execution_complete',True)])

    def test_closeout_requires_truthful_all_branch_and_failure_dispositions(self):
        self.mutate(C.closeout,hold(),[('scientific_success_required',True),('physical_execution_claim',True),
            ('whole_paper_success_claim',True),('raw_and_failures_retained',False)])
        p=hold();del p['branch_dispositions']['B01'];self.reject(C.closeout,p)
        p=hold();p['branch_dispositions']['B04']='evidence_reviewed';self.reject(C.closeout,p)

    def test_return_requires_observed_safe_release_and_confirmed_custody(self):
        p=C.synthetic_closeout();self.assertTrue(C.closeout(p))
        self.mutate(C.closeout,p,[('unloaded_observed',False),('disarmed_observed',False),('safe_release_observed',False),
            ('station_occupied',True),('active_leases',['S05']),('actual_custody_station','S04'),('destination_identity_verified',False),
            ('safe_release_receipt_id',''),('return_custody_receipt_id','')])

    def test_evaluator_pins_registry_and_rejects_actor_truth_injection(self):
        result=C.evaluate(C.synthetic_messages());self.assertEqual(result['validated_runnable_whole_paper_tasks'],0)
        self.assertFalse(result['physical_execution']);self.assertFalse(result['physical_simulation']);self.assertFalse(result['scientific_reproduction'])
        for key in ('sensor_value','safe_state','success','source_outcome','qualification','raw_frame','epoch_override'):
            with self.subTest(key=key):
                ms=C.synthetic_messages();ms[0][key]=True;self.reject(C.evaluate,ms)
        r=C.synthetic_registry();r['R13']['fit_squared_residual']=0;self.reject(C.evaluate,C.synthetic_messages(),r)

    def test_evaluator_rejects_missing_duplicate_and_out_of_order_operations(self):
        ms=C.synthetic_messages();self.reject(C.evaluate,ms[:-1])
        ms=C.synthetic_messages();ms[1]['event_id']=ms[0]['event_id'];self.reject(C.evaluate,ms)
        ms=C.synthetic_messages();ms[0],ms[1]=ms[1],ms[0];self.reject(C.evaluate,ms)


if __name__=='__main__':unittest.main()
