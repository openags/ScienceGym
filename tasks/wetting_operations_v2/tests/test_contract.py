"""Author tests use only deliberately synthetic records, not scientific source outcomes."""
import unittest,copy,math
import contract as c
class ContractTests(unittest.TestCase):
 def rejects(self,fn,*args):
  with self.assertRaises(c.ContractError):fn(*args)
 def macro(self):return {'cohort':'macro','time_s':[0,1,2],'volume_nL':[70,56,50],'evidence_kind':'synthetic_observation','synthetic_only':True}
 def stack(self):return {'stack_id':'S','start_s':0,'end_s':2,'plane_time_s':[0.2,1,1.8],'z_um':[0,1,2],'side_time_s':[0.2,1,1.8],'environment_interval_s':[-1,3],'sync_tolerance_s':0.01,'synthetic_only':True}
 def angle(self):return {'theta_star_rad':1.2,'psi_rad':0.1,'theta_r_rad':1.4,'theta_r_kind':'synthetic_independent_reference','psi_fit_field':'P1_current_placement','displacement_fit_fields':['Ur','Uz'],'synthetic_only':True}
 def traction(self):return {'tractions_Pa':[[3,4,0]],'triangle_areas_m2':[2],'area_measure':'deformed_physical_area','window_policy_id':'synthetic-window','conflict_dispositions':{'C02':'synthetic_scope_choice','C03':'synthetic_dimensional_audit'},'sector_angle_rad':1,'synthetic_only':True}
 def age(self):return {'material_family':'CY','cure_utc':'2026-01-01T00:00:00Z','experiment_utc':'2026-01-15T00:00:00Z','storage_receipt_id':'synthetic-storage','custody_basis':'synthetic_dated_custody','synthetic_only':True}
 def coords(self):return [{'point_id':'p1','kind':'observed','xyz_m':[0,1e-6,2e-6],'raw_parent_id':'stack1','method_revision':'detect1','directly_measured':True},{'point_id':'p2','kind':'imputed','xyz_m':[0,2e-6,2e-6],'raw_parent_id':'stack1','method_revision':'interp1','directly_measured':False}]
 def ledger(self):return [{'sample_id':'S1','spot_id':'spot1','droplet_id':'D1','timepoint_id':'t1','cohort_id':'C1'},{'sample_id':'S1','spot_id':'spot1','droplet_id':'D1','timepoint_id':'t2','cohort_id':'C1'},{'sample_id':'S1','spot_id':'spot2','droplet_id':'D2','timepoint_id':'t1','cohort_id':'C2'}]
 def matching(self):return {'array_id':'a','pairs':[['d1','r1'],['d2','r2'],['d3','r3']],'boundary_evidence_id':'b','boundary_stationary':True,'synthetic_only':True}
 def humidity(self):return {'setpoint_percent':20,'measured_percent':21,'stability_pp':1,'sensor_accuracy_pp':3,'claimed_absolute_accuracy_pp':3,'synthetic_only':True}
 def test_all_64_fixtures(self):
  self.assertEqual(len(c.FIXTURE_IDS),64)
  for fid in c.FIXTURE_IDS:
   with self.subTest(fid=fid):
    f=c.fixture(fid);result=c.evaluate(f['events'],f['registry'],fid);self.assertTrue(result['contract_passed']);self.assertFalse(result['physical_execution']);self.assertEqual(result['validated_runnable_whole_paper_tasks'],0)
 def test_closeout_all_routes_and_outcomes(self):
  for fid in c.FIXTURE_IDS:
   f=c.fixture(fid);self.assertEqual([e['operation_id'] for e in f['events'][-4:]],['R15_O01','R15_O02','R15_O03','R15_O04'])
 def test_unknown_fixture(self):self.rejects(c.fixture,'R99:METADATA_OK')
 def test_event_extra_payload(self):
  f=c.fixture('R09:METADATA_OK');f['events'][0]['success']=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_missing_event(self):
  f=c.fixture('R09:METADATA_OK');f['events'].pop();self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_duplicate_event(self):
  f=c.fixture('R09:METADATA_OK');f['events'][1]=f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_dependency_reordering(self):
  f=c.fixture('R07:METADATA_OK');f['events'][0],f['events'][1]=f['events'][1],f['events'][0];self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_registry_forgery(self):
  f=c.fixture('R08:METADATA_OK');next(iter(f['registry'].values()))['payload']['physical_qualified']=True;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_request_role_mutation(self):
  f=c.fixture('R07:METADATA_OK');next(iter(f['registry'].values()))['role']='independent_scoped_record';self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_context_revision_mutations(self):
  for key in c.CONTEXT:
   f=c.fixture('R11:METADATA_OK');next(iter(f['registry'].values()))['context'][key]='forged';self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_isolation_hold_no_removal(self):
  f=c.fixture('R11:ISOLATION_HOLD');rows=[r for r in f['registry'].values() if r['operation_id']=='R15_O02'];self.assertEqual(rows[0]['payload']['disposition'],'held_contained');self.assertFalse(rows[0]['payload']['physical_removed'])
 def test_local_high_thickness_conflict(self):
  self.assertEqual(c.scope_holds('R10_O01',['thickness_high'])['conflicts'],['C01']);self.assertEqual(c.scope_holds('R09_O01',['thickness_high'])['conflicts'],[])
 def test_inactive_conflict_not_global(self):self.assertEqual(c.scope_holds('R14_O04',[])['conflicts'],[])
 def test_closeout_not_held_by_qualifications(self):
  for op in ('R15_O01','R15_O02','R15_O03','R15_O04'):self.assertEqual(c.scope_holds(op,['traction_integration'])['qualification'],[])
 def test_all_unknowns_retained(self):self.assertEqual(set(c.UNKNOWNS),{f'U{i:02}' for i in range(1,26)})
 def test_PDMS_ancestry_not_CY(self):self.assertIn('R01',c.route_ancestors('R09','PDMS'));self.assertNotIn('R02',c.route_ancestors('R09','PDMS'))
 def test_CY_ancestry_not_PDMS(self):self.assertIn('R02',c.route_ancestors('R11','CY'));self.assertNotIn('R01',c.route_ancestors('R11','CY'))
 def test_closeout_has_no_scientific_prerequisite(self):self.assertEqual(c.route_ancestors('R15','MULTI'),[])
 def test_macro_bracket(self):self.assertEqual(c.macro_origin(self.macro())['origin_bracket_s'],[1,2])
 def test_macro_exact_threshold(self):
  r=self.macro();r['volume_nL'][1]=55;self.assertTrue(c.macro_origin(r)['exact_origin_observed'])
 def test_micro_origin_rejected(self):r=self.macro();r['cohort']='micro';self.rejects(c.macro_origin,r)
 def test_below_origin_rejected(self):r=self.macro();r['volume_nL']=[49,45,40];self.rejects(c.macro_origin,r)
 def test_unobserved_crossing(self):r=self.macro();r['volume_nL']=[70,65,60];self.rejects(c.macro_origin,r)
 def test_origin_duplicate_time(self):r=self.macro();r['time_s']=[0,0,1];self.rejects(c.macro_origin,r)
 def test_origin_source_evidence_rejected(self):r=self.macro();r['evidence_kind']='source_reference';self.rejects(c.macro_origin,r)
 def test_stack_duration(self):self.assertEqual(c.stack_timing(self.stack())['duration_s'],2)
 def test_stack_reverse_z_supported(self):r=self.stack();r['z_um']=[2,1,0];self.assertFalse(c.stack_timing(r)['instantaneous'])
 def test_stack_duplicate_plane(self):r=self.stack();r['plane_time_s']=[0.2,0.2,1.8];self.rejects(c.stack_timing,r)
 def test_stack_partial_environment(self):r=self.stack();r['environment_interval_s']=[0.1,2];self.rejects(c.stack_timing,r)
 def test_stack_out_of_sync(self):r=self.stack();r['side_time_s']=[0.1,0.9,1.7];self.rejects(c.stack_timing,r)
 def test_stack_unmatched_planes(self):r=self.stack();r['z_um'].pop();self.rejects(c.stack_timing,r)
 def test_repeats_not_timepoints(self):r=c.repeat_ledger(self.ledger());self.assertEqual((r['distinct_droplets'],r['distinct_samples'],r['timepoints']),(2,1,3));self.assertFalse(r['statistical_independence_established'])
 def test_repeat_wrong_parentage(self):r=self.ledger();r[1]['spot_id']='other';self.rejects(c.repeat_ledger,r)
 def test_repeat_cross_cohort_duplicate(self):r=self.ledger();r.append(dict(r[0],cohort_id='different'));self.rejects(c.repeat_ledger,r)
 def test_coordinates_separate_layers(self):self.assertEqual(c.coordinate_layers(self.coords())['p2'],'imputed')
 def test_imputed_not_observed(self):r=self.coords();r[1]['directly_measured']=True;self.rejects(c.coordinate_layers,r)
 def test_inferred_not_observed(self):r=self.coords();r[0]['kind']='inferred_reference';self.rejects(c.coordinate_layers,r)
 def test_annotation_requires_raw(self):r=self.coords();r[1]['raw_parent_id']='';self.rejects(c.coordinate_layers,r)
 def test_matching_one_to_one(self):self.assertFalse(c.marker_correspondence(self.matching())['captured_reference_image'])
 def test_matching_duplicate(self):r=self.matching();r['pairs'][2][1]='r2';self.rejects(c.marker_correspondence,r)
 def test_matching_unqualified_boundary(self):r=self.matching();r['boundary_stationary']=False;self.rejects(c.marker_correspondence,r)
 def test_angle_algebra(self):r=c.angle_comparison(self.angle());self.assertAlmostEqual(r['residual_rad'],-.1);self.assertFalse(r['observed_depinning'])
 def test_source_reference_remains_model(self):r=self.angle();r['theta_r_kind']='source_reference_only';self.assertEqual(c.angle_comparison(r)['comparison_kind'],'source_reference_model')
 def test_displacement_tangent_rejected(self):r=self.angle();r['psi_fit_field']='Ur';self.rejects(c.angle_comparison,r)
 def test_traction_physical_area(self):r=c.traction_area(self.traction());self.assertEqual(r['sum_magnitude_times_area'],10);self.assertEqual(r['unit'],'N')
 def test_traction_missing_conflict(self):r=self.traction();del r['conflict_dispositions']['C02'];self.rejects(c.traction_area,r)
 def test_traction_polar_measure_rejected(self):r=self.traction();r['area_measure']='dr_dphi';self.rejects(c.traction_area,r)
 def test_traction_zero_area(self):r=self.traction();r['triangle_areas_m2']=[0];self.rejects(c.traction_area,r)
 def test_traction_bad_sector(self):r=self.traction();r['sector_angle_rad']=0;self.rejects(c.traction_area,r)
 def test_age_custody(self):self.assertTrue(c.age_eligibility(self.age())['eligible_synthetic_window'])
 def test_CY_too_young(self):r=self.age();r['experiment_utc']='2026-01-08T00:00:00Z';self.assertFalse(c.age_eligibility(r)['eligible_synthetic_window'])
 def test_PDMS_age_distinct(self):r=self.age();r['material_family']='PDMS';r['experiment_utc']='2026-01-08T00:00:00Z';self.assertTrue(c.age_eligibility(r)['eligible_synthetic_window'])
 def test_age_filesystem_is_not_evidence(self):r=self.age();r['custody_basis']='file_mtime';self.rejects(c.age_eligibility,r)
 def test_age_missing_storage(self):r=self.age();r['storage_receipt_id']='';self.rejects(c.age_eligibility,r)
 def test_age_naive_time(self):r=self.age();r['cure_utc']='2026-01-01';self.rejects(c.age_eligibility,r)
 def test_humidity_separate_accuracy(self):self.assertTrue(c.humidity_semantics(self.humidity())['stability_distinct_from_accuracy'])
 def test_humidity_overclaim(self):r=self.humidity();r['claimed_absolute_accuracy_pp']=1;self.rejects(c.humidity_semantics,r)
 def test_finite_hostile_types(self):
  for x in (True,False,'1',None,float('nan'),float('inf'),-float('inf'),10**10000):self.rejects(c.finite,x)
 def test_retry_requires_new_identity(self):
  a={k:'before-'+k for k in ('attempt_id','sample_id','spot_id','droplet_id','acquisition_id','qualified_spot_receipt','previous_failure_id')};b={k:'after-'+k for k in a};b['previous_failure_id']=a['previous_failure_id'];self.assertTrue(c.retry_lineage(a,b)['prior_failure_retained']);b['droplet_id']=a['droplet_id'];self.rejects(c.retry_lineage,a,b)
 def test_incompatible_macro_material(self):self.rejects(c.route_ancestors,'R09','CY')
 def test_material_specific_detection_lineage(self):
  f=c.fixture('R11:METADATA_OK');self.assertEqual(f['context']['material_id'],'MULTI');r=[x for x in f['registry'].values() if x['operation_id']=='R11_O06'][0];self.assertEqual([x['material_id'] for x in r['payload']['constituent_lineages']],['PDMS_30:1'])
 def test_stack_finite_extreme_duration(self):
  r=self.stack();r.update(start_s=-1e308,end_s=1e308,plane_time_s=[-1e308,1e308],z_um=[0,1],side_time_s=[-1e308,1e308],environment_interval_s=[-1e308,1e308]);self.rejects(c.stack_timing,r)
 def test_all_anchors_bound(self):
  a=c.read('asset_binding_plan.json');anchors={x['asset_id']+'.'+n for x in a['assets'] for n in x['required_anchor_ids']};self.assertEqual(anchors,set().union(*(set(x['anchor_ids']) for x in a['operation_bindings'])))
 def test_registry_huge_integer_rejected(self):
  f=c.fixture('R00:METADATA_OK');next(iter(f['registry'].values()))['payload']['extra']=10**10000;self.rejects(c.evaluate,f['events'],f['registry'],f['fixture_id'])
 def test_raw_recipe_absent(self):
  ops=[o for o in c.OPS.values() if o['route_id']=='R07'];self.assertEqual(len(ops),4);self.assertTrue(all(o['physical_implemented'] is False for o in ops));self.assertEqual(ops[0]['evidence_role'],'request_acknowledgement')
if __name__=='__main__':unittest.main()
