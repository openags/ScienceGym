import unittest,sys,dataclasses,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from semantic_controls import *
BASE=dict(sample_id='S1',sample_version=1,carrier_id='C1',holder_id='H1',configuration_id='K1',configuration_version=1,topology='BCC')
def record(action,cycle='1'):
 r=dict(BASE);r.update({k:k+'_'+cycle for k in ACTION_FIELDS[action]})
 if action in SYMBOLS:r[SYMBOLS[action][0]]=SYMBOLS[action][1]
 if action=='bind_services':r.update(plasma_route='not_required',plasma_receipt_id='NOT_APPLICABLE')
 return r
def act(f,a,r=None):
 r=r or record(a);c=f.claim(a,r[TARGET_FIELDS[a]],r);return f.apply(a,r,c)
def ready(f):
 for a in ['register_custody','dock','bind_services','mount_fixture']:act(f,a)
class Guards(unittest.TestCase):
 def assert_atomic(self,f,fn):
  before=f.snapshot()
  with self.assertRaises(GuardError):fn()
  self.assertEqual(f.snapshot(),before)
 def test_complete_cycle_and_invariants(self):
  f=WovenFixture('S1');ready(f);act(f,'bind_records');self.assertEqual(f.record_manifest()['scope'],'unverified_external_identifiers_only');act(f,'disconnect');s=act(f,'retrieve');self.assertEqual(s['state'],'CUSTODY');self.assertEqual(set(s['records']),{'register_custody','retrieve'})
  for k,v in s.items():
   if k.endswith('_enabled') or k in ['physical_execution','geometry_coupling','claims_are_evidence']:self.assertFalse(v)
  self.assertIsNone(s['scientific_outputs'])
 def test_constructor_strict(self):
  for a,b in [('',1),('S',True),('S',0),(False,1),('S',1.0)]:
   with self.assertRaises(GuardError):WovenFixture(a,b)
 def test_exact_fields_and_types(self):
  for key,value in [('sample_version',True),('sample_id',''),('configuration_version',1.0),('topology','TETRAKAIDECAHEDRON')]:
   f=WovenFixture('S1');r=record('register_custody');r[key]=value;self.assert_atomic(f,lambda:f.claim('register_custody','C1',r))
  for mode in ['missing','extra']:
   f=WovenFixture('S1');r=record('register_custody');r.pop('carrier_id') if mode=='missing' else r.update(extra='x');self.assert_atomic(f,lambda:f.claim('register_custody','C1',r))
 def test_target_identity_and_config(self):
  f=WovenFixture('S1');act(f,'register_custody')
  for k,v in [('sample_id','S2'),('sample_version',2),('carrier_id','C2'),('holder_id','H2'),('configuration_id','K2'),('configuration_version',2),('topology','CUBIC')]:
   r=record('dock');r[k]=v;self.assert_atomic(f,lambda:f.claim('dock',r['holder_id'],r))
  r=record('dock');self.assert_atomic(f,lambda:f.claim('dock','OTHER',r))
 def test_sequence(self):
  f=WovenFixture('S1');act(f,'register_custody');r=record('bind_services');c=f.claim('bind_services','H1',r);self.assert_atomic(f,lambda:f.apply('bind_services',r,c))
 def test_claim_replay(self):
  f=WovenFixture('S1');r=record('register_custody');c=f.claim('register_custody','C1',r);f.apply('register_custody',r,c);self.assert_atomic(f,lambda:f.apply('register_custody',r,c))
 def test_forged_cross_instance_stale_changed_payload(self):
  f=WovenFixture('S1');g=WovenFixture('S1');r=record('register_custody');c=f.claim('register_custody','C1',r)
  for bad in [dataclasses.replace(c,claim_id='forged'),dataclasses.replace(c,revision=True),dataclasses.replace(c,sample_version=True),dataclasses.replace(c,target_id='X')]:self.assert_atomic(f,lambda:f.apply('register_custody',r,bad))
  self.assert_atomic(g,lambda:g.apply('register_custody',r,c));changed=dict(r,custody_record_id='changed');self.assert_atomic(f,lambda:f.apply('register_custody',changed,c))
 def test_plasma_branch(self):
  f=WovenFixture('S1');act(f,'register_custody');act(f,'dock');r=record('bind_services');r['plasma_route']='required_external';self.assert_atomic(f,lambda:f.claim('bind_services','H1',r));r['plasma_receipt_id']='PLASMA_1';act(f,'bind_services',r)
 def test_receipt_collision(self):
  f=WovenFixture('S1');act(f,'register_custody');act(f,'dock');r=record('bind_services');r['cpd_receipt_id']=r['coating_receipt_id'];self.assert_atomic(f,lambda:f.claim('bind_services','H1',r))
 def test_symbolic_disposition(self):
  f=WovenFixture('S1');act(f,'register_custody');act(f,'dock');r=record('bind_services');r['service_status']='physically_complete';self.assert_atomic(f,lambda:f.claim('bind_services','H1',r))
 def test_fresh_records_across_cycles(self):
  f=WovenFixture('S1');ready(f);act(f,'bind_records');act(f,'disconnect');act(f,'retrieve');act(f,'dock');act(f,'bind_services');act(f,'mount_fixture');r=record('bind_records');self.assert_atomic(f,lambda:f.claim('bind_records',r['record_set_id'],r));act(f,'bind_records',record('bind_records','2'))
 def test_duplicate_acquisition_ids(self):
  f=WovenFixture('S1');ready(f);r=record('bind_records');r['sem_image_record_id']=r['force_displacement_record_id'];self.assert_atomic(f,lambda:f.claim('bind_records',r['record_set_id'],r))
 def test_detached_input_output(self):
  f=WovenFixture('S1');r=record('register_custody');act(f,'register_custody',r);r['carrier_id']='MUTATED';s=f.snapshot();s['records'].clear();self.assertEqual(f.snapshot()['records']['register_custody']['carrier_id'],'C1')
 def test_quarantine_terminal_idempotent(self):
  f=WovenFixture('S1');a=f.quarantine();self.assertEqual(a,f.quarantine());self.assert_atomic(f,lambda:f.claim('register_custody','C1',record('register_custody')))
 def test_service_unconditional_rejection(self):
  f=WovenFixture('S1')
  for op in ['fabricate','develop','cpd','plasma','coat','load','sem','simulate','measure','unknown']:self.assert_atomic(f,lambda:f.request_physical_service(op,callback=lambda:self.fail('callback executed')))
 def test_no_manifest_before_or_after_records(self):
  f=WovenFixture('S1');self.assert_atomic(f,f.record_manifest);ready(f);act(f,'bind_records');m=f.record_manifest();m['records'].clear();self.assertTrue(f.record_manifest()['records']);act(f,'disconnect');self.assert_atomic(f,f.record_manifest)
if __name__=='__main__':unittest.main()
