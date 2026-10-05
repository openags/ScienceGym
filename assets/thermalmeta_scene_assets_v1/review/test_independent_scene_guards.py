"""Independent hostile checks of a static evidence-only scene; no equipment actions."""
import importlib.util,json,pathlib,subprocess,sys,unittest
P=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('independent_scene_guards',P/'scene_guards.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class IndependentGuardChecks(unittest.TestCase):
 def check_safe(self,r):
  self.assertIs(r['physical_permission'],False);self.assertEqual(r['commands_emitted'],[]);self.assertIs(r['external_state_changed'],False);self.assertIs(r['evidence_authenticity_established'],False)
 def request(self,evidence=None,**kw):
  args=dict(stage_id='P14',anchor_id='AN_REGISTER',action='inspect_geometry',evidence={} if evidence is None else evidence);args.update(kw);r=g.evaluate_request(**args);self.check_safe(r);return r
 def test_exact_stage_and_condition_counts(self):
  self.assertEqual(set(g.STAGES),{f'P{i:02d}' for i in range(1,21)});self.assertEqual(len(g.CONDITIONS),6)
 def test_wrong_stage_anchor_all_pairs(self):
  for stage,row in g.STAGES.items():
   for other in g.STAGES.values():
    if row['anchor_id']!=other['anchor_id']:
     self.assertEqual(self.request(stage_id=stage,anchor_id=other['anchor_id'])['status'],'REJECTED')
 def test_condition_identity_mismatch_each_field(self):
  for cid,c in g.CONDITIONS.items():
   for f in ['sample_family_id','orientation','specimen_id','design_id','design_revision','profile_id','profile_direction']:
    self.assertEqual(self.request({'condition_id':cid,f:'INVALID'})['status'],'REJECTED')
 def test_unbound_identity_including_revision(self):
  for f in ['sample_family_id','orientation','specimen_id','design_id','design_revision','profile_id','profile_direction']:
   self.assertEqual(self.request({f:'UNBOUND'})['status'],'REJECTED',f)
 def test_nonboolean_claims(self):
  for f,t in g.FIELDS.items():
   for invalid in ([0,1,'false','true',[],{},None] if t is bool else [0,1,True,False,[],{},None]):
    self.assertEqual(self.request({f:invalid})['status'],'REJECTED')
 def test_hardware_payloads(self):
  for a in ['HEAT','retrieve','rotate','dispose','open_guard','power_on','robot.move','exec','__import__',' simulate ', '', 'release_after_abort']:
   self.assertEqual(self.request(action=a)['status'],'REJECTED')
  for f in ['hardware_command','trajectory','motor_target','setpoint','temperature','heat_flux','measured_data','__class__','payload']:
   self.assertEqual(self.request({f:'UNTRUSTED'})['status'],'REJECTED')
 def test_safety_claims_cannot_self_certify(self):
  for f in ['geometry_qualified','use_as_measured','use_as_threshold','release_from_elapsed_time','release_from_stop','physical_actuation_enabled','profile_mapping_source_verified']:
   self.assertEqual(self.request({f:True})['status'],'REJECTED')
  for f in ['metric_convention_resolved','mapping_index_resolved','feature_label_resolved','flux_units_resolved']:
   self.assertEqual(self.request({f:True,'numeric_metric_claim':True,'absolute_flux_claim':True})['status'],'REJECTED')
 def test_conditions_share_exact_three_demo_identities(self):
  families={c['sample_family_id'] for c in g.CONDITIONS.values()};self.assertEqual(len(families),3)
  for f in families:
   rows=[c for c in g.CONDITIONS.values() if c['sample_family_id']==f];self.assertEqual(len(rows),2);self.assertEqual({c['orientation'] for c in rows},{'X','Y'});self.assertEqual(len({c['specimen_id'] for c in rows}),1)
   for c in rows:
    self.assertFalse(c['independent_specimen_claim']);self.assertIn('synthetic_demo',c['identity_status']);self.assertEqual(c['profile_number_to_orientation_status'],'authored_visual_selector_not_source_verified')
 def test_source_receipt_never_measured_or_authenticated(self):
  for cat in ['measured','simulated','qualified','safe_release','source_reported']:
   r=self.request({'evidence_id':'UNTRUSTED','category':cat},action='register_evidence');self.assertEqual(r['status'],'REJECTED')
  r=self.request({'evidence_id':'REFERENCE','category':'source_reported','source_reference_only':True},action='register_evidence');self.assertEqual(r['status'],'EVIDENCE_ONLY_ACCEPTED')
 def test_no_service_dispatch_at_any_stage(self):
  for stage,row in g.STAGES.items():
   self.assertEqual(self.request(stage_id=stage,anchor_id=row['anchor_id'],action='propose_service_request')['status'],'HOLD_UNQUALIFIED')
 def complete(self):
  r={k:{'evidence_id':'UNVERIFIED','provider_id':'UNVERIFIED_PROVIDER','independently_observed':True} for k in g.C['safe_release_requires']};r.update(specimen_id='DEMO',run_id='DEMO',provider_id='UNVERIFIED_PROVIDER',pending_service_jobs=False);return r
 def test_release_requires_every_item(self):
  for k in self.complete():
   r=self.complete();del r[k];out=g.check_release(r);self.check_safe(out);self.assertEqual(out['status'],'HOLD')
 def test_release_boolean_lookalikes(self):
  for bad in [0,1,None,'false','true',[],{}]:
   r=self.complete();r['pending_service_jobs']=bad;self.assertEqual(g.check_release(r)['status'],'HOLD')
   for k in g.C['safe_release_requires']:
    r=self.complete();r[k]['independently_observed']=bad;self.assertEqual(g.check_release(r)['status'],'HOLD')
 def test_complete_receipt_no_release_authority(self):
  r=g.check_release(self.complete());self.check_safe(r);self.assertEqual(r['status'],'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION')
 def test_malformed_cli_rejects_without_side_effects(self):
  for text in ['null','[]','{"stage_id": "P14"}','{"action":"heat"}','{"stage_id":"P14","anchor_id":"AN_REGISTER","action":"inspect_geometry","unexpected":true}','not json']:
   p=subprocess.run([sys.executable,str(P/'scene_guards.py')],input=text,text=True,capture_output=True,check=True);out=json.loads(p.stdout);self.check_safe(out);self.assertEqual(out['status'],'REJECTED')
if __name__=='__main__':unittest.main(verbosity=2)
