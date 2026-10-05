import json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import scene_guards as g
class GuardTests(unittest.TestCase):
 def safe(self,out):
  self.assertIs(out['physical_permission'],False);self.assertEqual(out['commands_emitted'],[]);self.assertIs(out['external_state_changed'],False)
 def reject(self,**kw):
  args=dict(stage_id='P10',anchor_id='AN_MOUNT',action='inspect_geometry',evidence={});args.update(kw);out=g.evaluate_request(**args);self.safe(out);self.assertEqual(out['status'],'REJECTED')
 def test_all_20_stage_bindings(self):
  self.assertEqual(len(g.STAGES),20)
  for k,v in g.STAGES.items():
   o=g.evaluate_request(k,v['anchor_id'],'inspect_geometry');self.safe(o);self.assertEqual(o['status'],'EVIDENCE_ONLY_ACCEPTED')
 def test_all_conditions(self):
  self.assertEqual(len(g.CONDITIONS),6)
  for k,c in g.CONDITIONS.items():
   e={f:c[f] for f in ['condition_id','sample_family_id','orientation','specimen_id','design_id','design_revision','profile_id','profile_direction']};o=g.evaluate_request('P14','AN_REGISTER','inspect_condition',e);self.safe(o);self.assertEqual(o['status'],'EVIDENCE_ONLY_ACCEPTED')
 def test_unknown_stage(self):self.reject(stage_id='P21')
 def test_wrong_anchor(self):self.reject(anchor_id='AN_SAFE_RELEASE')
 def test_bad_types(self):
  for bad in [[],False,42,'payload']:
   self.reject(evidence=bad)
 def test_actuations(self):
  for a in ['heat','cast','pump','move','grasp','release','rotate','start','stop','open_service','execute_path','simulate','set_temperature','dispose','__import__("os")']:
   self.reject(action=a)
 def test_schema_cannot_be_truthy(self):
  for k in ['physical_actuation_enabled','geometry_qualified','use_as_measured']:
   for v in ['false','true',1,[],{}]:self.reject(evidence={k:v})
 def test_nested_hardware(self):self.reject(evidence={'hardware':{'command':'heat'}})
 def test_unknown_keys(self):self.reject(evidence={'temperature_c':37})
 def test_unsafe_claims(self):
  for k in ['geometry_qualified','use_as_measured','use_as_threshold','release_from_elapsed_time','release_from_stop','physical_actuation_enabled','profile_mapping_source_verified']:self.reject(evidence={k:True})
 def test_missing_condition(self):self.reject(action='inspect_condition')
 def test_unknown_condition(self):self.reject(evidence={'condition_id':'COND_CLOAK_Z'})
 def test_identity_mismatch(self):
  for k,v in [('orientation','Y'),('sample_family_id','ROTATOR45'),('specimen_id','SPEC_OTHER'),('design_revision','R1'),('profile_id','R1'),('profile_direction','transverse_to_applied_reference')]:self.reject(evidence={'condition_id':'COND_CLOAK_X',k:v})
 def test_unbound_identity(self):self.reject(evidence={'orientation':'X'})
 def test_unbound_design_revision(self):self.reject(evidence={'design_revision':'arbitrary'})
 def test_real_claim(self):self.reject(evidence={'condition_id':'COND_CLOAK_X','synthetic_demo':False})
 def test_source_as_measurement(self):self.reject(evidence={'category':'source_reported'})
 def test_unsupported_category(self):self.reject(evidence={'category':'measured'})
 def test_evidence_requires_id(self):self.reject(action='register_evidence',evidence={'category':'external_unverified_receipt'})
 def test_metric_hold(self):self.reject(evidence={'numeric_metric_claim':True,'metric_convention_resolved':False})
 def test_even_resolved_not_certified(self):self.reject(evidence={'numeric_metric_claim':True,'metric_convention_resolved':True})
 def test_flux_hold(self):self.reject(evidence={'absolute_flux_claim':True,'flux_units_resolved':True})
 def test_source_reference(self):
  o=g.evaluate_request('P01','AN_REVIEW','register_evidence',{'evidence_id':'SYNTHETIC_SOURCE_TOKEN','category':'source_reported','source_reference_only':True});self.safe(o);self.assertEqual(o['status'],'EVIDENCE_ONLY_ACCEPTED')
 def test_service_does_not_dispatch(self):
  o=g.evaluate_request('P11','AN_SERVICE_HANDOFF','propose_service_request');self.safe(o);self.assertEqual(o['status'],'HOLD_UNQUALIFIED')
 def complete(self):
  d={k:{'evidence_id':'DEMO_ONLY','provider_id':'DEMO_PROVIDER','independently_observed':True} for k in g.C['safe_release_requires']};d.update(pending_service_jobs=False,specimen_id='DEMO_SPEC',run_id='DEMO_RUN',provider_id='DEMO_PROVIDER');return d
 def test_missing_release(self):
  for bad in [{},[],False,'stop']:
   o=g.check_release(bad);self.safe(o);self.assertEqual(o['status'],'HOLD')
 def test_missing_each_release(self):
  for k in g.C['safe_release_requires']:
   d=self.complete();del d[k];self.assertEqual(g.check_release(d)['status'],'HOLD')
 def test_release_lookalike(self):
  d=self.complete();d['zero_energy_evidence']['independently_observed']='true';self.assertEqual(g.check_release(d)['status'],'HOLD')
 def test_pending_service(self):
  d=self.complete();d['pending_service_jobs']=True;self.assertEqual(g.check_release(d)['status'],'HOLD')
 def test_unknown_release_field(self):
  d=self.complete();d['elapsed_minutes']=45;self.assertEqual(g.check_release(d)['status'],'HOLD')
 def test_complete_never_physical_authority(self):
  o=g.check_release(self.complete());self.safe(o);self.assertEqual(o['status'],'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION')
if __name__=='__main__':unittest.main(verbosity=2)
