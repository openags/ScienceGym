"""Adversarial bookkeeping tests. No fabrication, physics or hardware execution."""
import copy,json,pathlib,unittest
from record_contract import load_packet,validate_design,fixture,validate_record,validate_campaign,campaign_fixture,ROOT
class DesignTests(unittest.TestCase):
 def setUp(self):self.p=load_packet()
 def test_static_design(self):self.assertTrue(validate_design(self.p))
 def test_all_18_branch_fixtures(self):
  for b in self.p['branches']['branches']:
   with self.subTest(branch=b['id']):self.assertTrue(validate_record(fixture(b['id'],self.p),self.p))
 def test_reject_source_repeat_invention(self):
  self.p['branches']['branches'][0]['repeat_count']=1
  with self.assertRaisesRegex(ValueError,'repeat'):validate_design(self.p)
 def test_reject_micro_array_merge(self):
  next(f for f in self.p['material_cards']['specimen_families'] if f['id']=='F_MICRO_TAIJI_COMP')['array_shape']=[5,6]
  with self.assertRaisesRegex(ValueError,'micro-Taiji'):validate_design(self.p)
 def test_reject_radius_repair(self):
  next(m for m in self.p['material_cards']['cards'] if m['id']=='M_MICRO_RESIN')['source_facts']['planetary']['planet_radius_mm_si_table_1_unresolved']=0.6
  with self.assertRaisesRegex(ValueError,'radii'):validate_design(self.p)
 def test_reject_full_video_claim(self):
  self.p['source_access_audit']['full_motion_videos_inspected']=True
  with self.assertRaisesRegex(ValueError,'full-motion'):validate_design(self.p)
 def test_reject_robot_impact(self):
  next(o for o in self.p['operations']['operations'] if o['id']=='IMPACT_RUN')['actor']='robot'
  with self.assertRaisesRegex(ValueError,'impact actor'):validate_design(self.p)
 def test_reject_damping_omission(self):
  self.p['nonmanual_scope']['analysis_branches']=[]
  with self.assertRaisesRegex(ValueError,'damping'):validate_design(self.p)
 def test_all_json_parse(self):
  for path in ROOT.glob('*.json'):self.assertIsInstance(json.loads(path.read_text()),dict)
class RecordTests(unittest.TestCase):
 def setUp(self):self.r=fixture('TAIJI_PLUS')
 def reject(self,pattern):
  with self.assertRaisesRegex(ValueError,pattern):validate_record(self.r)
 def test_nonempty_conditions(self):self.r['conditions']=[];self.reject('empty conditions')
 def test_boolean_count(self):self.r['independent_specimen_count']=True;self.reject('count')
 def test_unknown_cycles(self):self.r['cycles']=None;self.reject('post-initial')
 def test_zero_cycles(self):self.r['cycles']=0;self.reject('post-initial')
 def test_first_cycle_only(self):self.r['cycles']=1;self.reject('post-initial')
 def test_initial_cycle_fitted(self):self.r['analysis']['fit_cycle_ids']=[1];self.reject('cycle fitting')
 def test_empty_windows(self):self.r['analysis']['fit_intervals']=[];self.reject('slope windows')
 def test_reversed_windows(self):self.r['analysis']['fit_intervals']=[[1,0]];self.reject('slope windows')
 def test_replicate_sd(self):self.r['analysis']['error_bar_kind']='replicate_SD';self.reject('SD')
 def test_modeled_parent(self):self.r['raw']['intended_modality']='modeled';self.reject('physical parent')
 def test_mutable_raw(self):self.r['raw']['immutable']=False;self.reject('physical parent')
 def test_stale_calibration(self):self.r['calibration']['valid']=False;self.reject('calibration')
 def test_stale_version(self):self.r['events'][-1]['specimen_version']=0;self.reject('stale event')
 def test_wrong_fixture(self):self.r['mount']['fixture_mode']='tension';self.reject('fixture')
 def test_missing_phase_measurement(self):self.r['conditions'][0]['phase_measured']=False;self.reject('unmeasured phase')
 def test_missing_gate(self):self.r['gates'].pop('U_LOAD');self.reject('unresolved gate')
 def test_geometry_by_analysis_declaration(self):self.r['gates']['U_CAD']['evidence_type']='analysis_declaration';self.reject('certified geometry')
 def test_unknown_micro_geometry(self):self.r=fixture('MICRO_PLANET_COMP');self.r['gates']['U_MICRO_GEOM']['closed']=False;self.reject('U_MICRO_GEOM')
 def test_wrong_micro_family(self):self.r=fixture('MICRO_TAIJI_COMP');self.r['specimen']['family_id']='F_MICRO_TAIJI_BUILD';self.reject('family')
 def test_impact_resin_substitution(self):self.r=fixture('IMPACT');self.r['specimen']['material_card_id']='M_MACRO_RESIN';self.reject('material')
 def test_periodic_shear_substitution(self):self.r=fixture('FINITE_SHEAR');self.r['analysis']['quantity']='periodic_G';self.reject('periodic')
 def test_soft_slip_removal(self):self.r=fixture('SOFT_SHEAR');self.r['analysis']['preserve_oscillations']=False;self.reject('slips')
 def test_missing_boxing(self):self.r=fixture('MICRO_TAIJI_BUILD');self.r['events']=[e for e in self.r['events'] if e['op_id']!='MICRO_BOX'];self.reject('required operation')
 def test_missing_support_removal(self):self.r=fixture('MACRO_PLANET_COMP');self.r['events']=[e for e in self.r['events'] if e['op_id']!='SUPPORT_CLEAR'];self.reject('required operation')
 def test_duplicate_occurrence(self):self.r['events'][-1]['occurrence_id']=self.r['events'][0]['occurrence_id'];self.reject('duplicate occurrence')
 def test_wrong_actor(self):self.r=fixture('IMPACT');next(e for e in self.r['events'] if e['op_id']=='IMPACT_RUN')['actor']='robot';self.reject('actor substitution')
 def test_impact_guard(self):self.r=fixture('IMPACT');self.r['guard']['fresh_arm_token']=False;self.reject('guard')
 def test_impact_safe_token(self):self.r=fixture('IMPACT');self.r['guard'].pop('safe_release_token');self.reject('guard')
 def test_impact_reuse(self):self.r=fixture('IMPACT');self.r['impact_count']=2;self.reject('impact reuse')
 def test_terminal_reuse(self):self.r['specimen']['terminal_before']=True;self.reject('terminal')
 def test_observation_teleport(self):next(e for e in self.r['events'] if e['op_id']=='IMAGE')['location']='WS_OBSERVE';self.reject('teleport')
 def test_fabricated_person_force(self):self.r['force_magnitude_inferred_from_person']=True;self.reject('force inferred')
 def test_missing_motor_home(self):self.r=fixture('MICRO_TAIJI_ACT');self.r['events']=[e for e in self.r['events'] if e['op_id']!='MOTOR_HOME'];self.reject('required operation')
 def test_missing_raw_receipt(self):self.r['events'][-1]['receipt']=None;self.reject('receipt')
 def test_missing_cleanup(self):self.r['events']=[e for e in self.r['events'] if e['op_id']!='CLEAN'];self.reject('required operation')
 def test_no_real_execution_claim(self):self.r['record_kind']='measured';self.reject('unsupported')
 def test_selected_scope(self):self.assertTrue(validate_campaign({'kind':'synthetic_bookkeeping','scope':'selected_branch_episode','records':[self.r],'claim':'synthetic_contract_acceptance_only'}))
 def test_selected_not_whole_paper(self):
  with self.assertRaisesRegex(ValueError,'branch omission'):validate_campaign({'kind':'synthetic_bookkeeping','scope':'whole_paper_physical_execution','records':[self.r],'claim':'synthetic_contract_acceptance_only'})
class ExpandedAdversarialTests(unittest.TestCase):
 def test_valid_analysis_after_seal_before_unload(self):
  r=fixture('TAIJI_PLUS');ev=next(e for e in r['events'] if e['op_id']=='ANALYZE_Y');r['events'].remove(ev);idx=next(i for i,e in enumerate(r['events']) if e['op_id']=='ACQ_CLOSE');ev['location']='WS_TEST';r['events'].insert(idx+1,ev)
  self.assertTrue(validate_record(r))
 def test_whole_paper_positive(self):self.assertTrue(validate_campaign(campaign_fixture()))
 def test_missing_component_frame(self):
  r=fixture('TAIJI_PLUS');r['specimen']['component_material_certificates'].pop('front_and_back_frames')
  with self.assertRaisesRegex(ValueError,'component material'):validate_record(r)
 def test_wrong_component_frame(self):
  r=fixture('TAIJI_PLUS');r['specimen']['component_material_bindings']['front_and_back_frames']='M_TAIJI_METAL'
  with self.assertRaisesRegex(ValueError,'component material'):validate_record(r)
 def test_missing_micro_shafts(self):
  r=fixture('MICRO_TAIJI_COMP');r['events']=[e for e in r['events'] if e['op_id']!='MICRO_SHAFT_CAPTURE']
  with self.assertRaisesRegex(ValueError,'required operation'):validate_record(r)
 def test_missing_motor_acquisition_arm(self):
  r=fixture('MACRO_PLANET_ACT');r['events']=[e for e in r['events'] if e['op_id']!='ACT_ACQ_ARM']
  with self.assertRaisesRegex(ValueError,'required operation'):validate_record(r)
 def test_missing_motor_seal(self):
  r=fixture('MACRO_PLANET_ACT');r['events']=[e for e in r['events'] if e['op_id']!='ACT_ACQ_CLOSE']
  with self.assertRaisesRegex(ValueError,'required operation'):validate_record(r)
 def test_nonfinite_phase(self):
  r=fixture('TAIJI_PLUS');r['conditions'][0]['actual_phase_deg']=float('nan')
  with self.assertRaisesRegex(ValueError,'nonfinite'):validate_record(r)
 def test_phase_outside_tolerance(self):
  r=fixture('TAIJI_PLUS');r['conditions'][0]['actual_phase_deg']=40
  with self.assertRaisesRegex(ValueError,'tolerance'):validate_record(r)
 def test_unreported_impact_angle(self):
  r=fixture('IMPACT');r['conditions'][0].update(actual_phase_deg=40,requested_phase_deg=40)
  with self.assertRaisesRegex(ValueError,'unreported'):validate_record(r)
 def test_nonfinite_fit(self):
  r=fixture('TAIJI_PLUS');r['analysis']['fit_intervals']=[[0,float('inf')]]
  with self.assertRaisesRegex(ValueError,'slope windows'):validate_record(r)
 def test_no_impact_angle_collapse(self):
  c=campaign_fixture();c['records']=[r for r in c['records'] if r['branch_id']!='IMPACT' or r['conditions'][0]['requested_phase_deg']==0]
  with self.assertRaisesRegex(ValueError,'condition allocation'):validate_campaign(c)
 def test_missing_damping_analysis(self):
  c=campaign_fixture();c['analysis_ids'].remove('DAMPING_ANALYSIS')
  with self.assertRaisesRegex(ValueError,'damping'):validate_campaign(c)
 def test_missing_controls(self):
  c=campaign_fixture();c['control_package_ids'].remove('CP_SOFT_FRAME')
  with self.assertRaisesRegex(ValueError,'controls'):validate_campaign(c)
 def test_reused_impact_instance(self):
  c=campaign_fixture();rs=[r for r in c['records'] if r['branch_id']=='IMPACT'];old=rs[0]['specimen']['id'];rs[1]['specimen']['id']=old
  for e in rs[1]['events']:e['specimen_id']=old
  with self.assertRaisesRegex(ValueError,'reused impact'):validate_campaign(c)
 def test_fabricated_execution_claim(self):
  c=campaign_fixture();c['claim']='physically_executed'
  with self.assertRaisesRegex(ValueError,'overclaim'):validate_campaign(c)
 def test_whole_paper_allocation_required(self):
  c=campaign_fixture();c.pop('allocation')
  with self.assertRaisesRegex(ValueError,'allocation'):validate_campaign(c)
 def test_release_allowlist(self):
  p=ROOT/'EXPORT_ALLOWLIST.json'
  if not p.exists():self.skipTest('allowlist is finalized after independent review')
  allow=json.loads(p.read_text())
  for f in allow['files']:
   self.assertTrue((ROOT/f).is_file());self.assertIn(pathlib.Path(f).suffix,['.json','.md','.py'])
   self.assertFalse(pathlib.Path(f).is_absolute());self.assertNotIn('..',pathlib.Path(f).parts)
if __name__=='__main__':unittest.main()
