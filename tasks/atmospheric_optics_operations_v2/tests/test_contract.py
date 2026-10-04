import copy,json,unittest
from contract import fixture,validate,BRANCHES,digest
class ContractTests(unittest.TestCase):
 def assertReject(self,c,e):self.assertFalse(validate(c,e)['passed'],validate(c,e))
 def test_every_selected_branch(self):
  for b in BRANCHES:
   with self.subTest(branch=b):
    c,e=fixture([b]);r=validate(c,e);self.assertTrue(r['passed'],r);self.assertFalse(r['production_accepted'])
 def test_whole_design(self):
  c,e=fixture(whole=True);self.assertTrue(validate(c,e)['passed'],validate(c,e))
 def test_authority_and_schema_mutations(self):
  changes=[('mode','production'),('origin','measured'),('authority_id','actor'),('selected_branches',[]),('selected_branches',['PREDICT','PREDICT']),('selected_branches',['INVENTED']),('whole_design',True),('archive_complete',False),('cleanup_complete',False),('actor_targets_exposed',True),('episode_id',None),('episode_id','real')]
  for k,v in changes:
   with self.subTest(k=k,v=v):c,e=fixture(['PREDICT']);c[k]=v;self.assertReject(c,e)
  c,e=fixture();c['outcome']='success';self.assertReject(c,e)
 def test_required_registry_omissions(self):
  for registry in ['plans','cards','controls','records','datasets','calibrations','splits','conflict_resolutions']:
   with self.subTest(registry=registry):
    c,e=fixture(['PREDICT']);c[registry].pop(next(iter(c[registry])));self.assertReject(c,e)
 def test_event_binding_mutations(self):
  fields={'episode_id':'synthetic_episode_other','branch_instance_id':'wrong','job_id':'wrong','attempt_id':'attempt_2','payload_id':'wrong','payload_version':True,'instrument_id':'wrong','station_id':'wrong','port_id':'wrong','pose_card_revision':'stale','calibration_id':'stale','dataset_id':'wrong','origin':'source_reported','record_id':'wrong','record_hash':'0'*64,'authority_id':'actor','guard_closed':False,'hazard_isolated':False,'retained_support':False,'safe_release':False,'receipt_status':'failed','sequence':False,'pre_state':'finished','post_state':'verified','phase':'RUN'}
  for field,value in fields.items():
   with self.subTest(field=field):c,e=fixture(['ACQUIRE30']);e[-2][field]=value;self.assertReject(c,e)
 def test_phase_omission_duplication_reorder(self):
  for mut in [lambda e:e.pop(2),lambda e:e.append(copy.deepcopy(e[0])),lambda e:e.reverse(),lambda e:e.clear()]:
   c,e=fixture();mut(e);self.assertReject(c,e)
 def test_untrusted_readout_and_leakage(self):
  for field,val in [('payload','RMSE 109.84 nm'),('origin','physical_observation'),('dataset_id','crossed'),('record_hash','0'*64),('authority_id','actor')]:
   c,e=fixture();next(iter(c['records'].values()))[field]=val;self.assertReject(c,e)
  c,e=fixture();e[0]['future_outcome']=109.84;self.assertReject(c,e)
 def test_source_parameter_rewrite(self):
  c,e=fixture(['PREDICT']);c['plans']['PREDICT::PREDICT']['source_parameters']['selected_frames']=7000;self.assertReject(c,e)
  c,e=fixture(['COVARIANCE']);next(iter(c['conflict_resolutions'].values()))['preserved_source_conflict']=False;self.assertReject(c,e)
 def test_calibration_and_boolean_types(self):
  for registry,field in [('cards','qualified'),('calibrations','current'),('controls','passed')]:
   for val in [False,1,'true',None]:
    with self.subTest(registry=registry,val=val):
     c,e=fixture();next(iter(c[registry].values()))[field]=val;self.assertReject(c,e)
 def test_prediction_leakage_and_windows(self):
  for field,val in [('normalization_fitted_on','all_data'),('normalization_fit_ids',[]),('window_policy','concatenate_all_sets'),('training_loss_alignment','next_frame_only'),('valid_test_target_indices',list(range(5400,6000))),('valid_training_target_indices',list(range(5,5400))),('noll_modes',[1,35]),('system_aberration_removed',False),('horizon_steps',2)]:
   c,e=fixture(['PREDICT']);c['splits']['PREDICT::PREDICT'][field]=val;self.assertReject(c,e)
  c,e=fixture(['PREDICT']);s=c['splits']['PREDICT::PREDICT'];s['test_ids'][0]=s['training_ids'][0];self.assertReject(c,e)
  c,e=fixture(['PREDICT']);d=next(iter(c['datasets'].values()));d['capture_segments'][1]['start_tick']=1000;d['manifest_hash']=digest({k:v for k,v in d.items() if k!='manifest_hash'});self.assertReject(c,e)
 def test_capture_interval_boolean_rejected(self):
  c,e=fixture(['PREDICT']);d=next(iter(c['datasets'].values()));d['capture_segments'][0]['interval_ticks']=True;d['manifest_hash']=digest({k:v for k,v in d.items() if k!='manifest_hash'});self.assertReject(c,e)
 def test_finetune_day_and_count(self):
  for field,val in [('independent_day_id','synthetic_day_A'),('frame_ids',[]),('train_indices',list(range(200)))]:
   c,e=fixture(['FINETUNE']);c['splits']['FINETUNE::FINETUNE']['adaptation_dataset'][field]=val;self.assertReject(c,e)
 def test_mount_lease_and_teardown(self):
  for mutation in ['lease','generation','teardown','early','unsafe','reordered']:
   c,e=fixture(['ACQUIRE30'])
   if mutation=='lease':c['mounted_leases'].clear()
   if mutation=='generation':c['mounted_leases']['ACQUIRE30']['mount_generation']=2
   if mutation=='teardown':c['teardown_events'].pop()
   if mutation=='early':c['teardown_events'][0]['after_event_sequence']=1
   if mutation=='unsafe':c['teardown_events'][2]['safe_receipt']=False
   if mutation=='reordered':c['teardown_events'].reverse()
   self.assertReject(c,e)
 def test_cross_episode_replay(self):
  c1,e1=fixture(episode_id='synthetic_episode_1');c2,e2=fixture(episode_id='synthetic_episode_2');self.assertTrue(validate(c2,e2)['passed']);e2[0]=e1[0];self.assertReject(c2,e2)
 def test_cross_episode_authority_maps(self):
  for registry in ['cards','controls','records','datasets','calibrations','splits','conflict_resolutions','mounted_leases']:
   root='ACQUIRE30' if registry=='mounted_leases' else 'PREDICT'
   c1,e1=fixture([root],episode_id='synthetic_episode_1');c2,e2=fixture([root],episode_id='synthetic_episode_2');k=next(iter(c2[registry]));c2[registry][k]=c1[registry][k];self.assertReject(c2,e2)
 def test_malformed_inputs(self):
  for c,e in [(None,[]),({},[]),([],{}),({'selected_branches':None},[]),(fixture()[0],[None])]:self.assertReject(c,e)
if __name__=='__main__':unittest.main()
