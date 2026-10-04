import unittest,copy,itertools
from contract import fixture,validate,PROFILES,B
class Contract(unittest.TestCase):
 def test_all_branches_profiles(self):
  for p in PROFILES:
   for b in B:
    with self.subTest(p=p,b=b):self.assertEqual(validate(*fixture([b],p)),[])
 def test_all_downstream_combinations(self):
  for n in range(1,4):
   for subset in itertools.permutations(['INTERPOLATE','REPEATABILITY','DRIFT_NOISE'],n):self.assertEqual(validate(*fixture(list(subset))),[])
 def test_default_is_safe_hold(self):
  c,e=fixture();self.assertEqual(c['terminal_status'],'safe_held');self.assertIsNone(c['service_clearance']);self.assertFalse(c['source_flow_resolved']);self.assertEqual(validate(c,e),[])
 def test_every_context_leaf_mutation(self):
  c,e=fixture(['INTERPOLATE','REPEATABILITY','DRIFT_NOISE'])
  def paths(x,p=()):
   if type(x) is dict:
    for k,v in x.items():yield from paths(v,p+(k,))
   elif type(x) is list:
    for k,v in enumerate(x):yield from paths(v,p+(k,))
   else:yield p,x
  for path,old in paths(c):
   cc=copy.deepcopy(c);node=cc
   for k in path[:-1]:node=node[k]
   node[path[-1]]=None if old is not None else 'forged'
   with self.subTest(path=path):self.assertTrue(validate(cc,e))
 def test_bool_integer_aliases(self):
  c,e=fixture(['INTERPOLATE'])
  for k in ['production_authority','whole_paper_complete','source_flow_resolved','physical_execution','fabrication_performed']:
   cc=copy.deepcopy(c);cc[k]=0;self.assertTrue(validate(cc,e))
  for eid,o in c['observations'].items():
   for k,v in o.items():
    if type(v) is bool:
     cc=copy.deepcopy(c);cc['observations'][eid][k]=int(v);self.assertTrue(validate(cc,e))
 def test_actor_injection_replay_order(self):
  c,e=fixture(['INTERPOLATE'])
  for mutation in ['inject','delete','duplicate','swap','pump','unknown']:
   ee=copy.deepcopy(e)
   if mutation=='inject':ee[0]['success']=True
   elif mutation=='delete':ee.pop()
   elif mutation=='duplicate':ee.insert(2,ee[1])
   elif mutation=='swap':ee[2],ee[3]=ee[3],ee[2]
   elif mutation=='pump':ee[0]['pump_ul_min']=50
   else:ee[0]['phase']='OPEN_LASER'
   self.assertTrue(validate(c,ee),mutation)
 def test_mutually_forged_identity_and_roles(self):
  c,e=fixture(['INTERPOLATE'])
  for o in c['observations'].values():o['binding']['profile_id']='SPP2_1064'
  self.assertTrue(validate(c,e))
  c,e=fixture(['INTERPOLATE']);c['calibration']['train_sample_ids'].append('test_a');self.assertTrue(validate(c,e))
 def test_malformed(self):
  for c,e in [(None,[]),({},{}),({},[]),([],[]),(True,[]),(dict(selected_branches=[[]]),[])]:self.assertTrue(validate(c,e))
 def test_stale_and_unsafe_receipts(self):
  c,e=fixture(['INTERPOLATE'])
  changes={'reference_fresh':False,'reference_riu':float('nan'),'clamp_observed':False,'bubbles':'unknown','enclosure':'open','drift_alarm':True,'exchange_completed':False,'calibration_invalidated':False,'cleanup_complete':False,'frame_pair_id':'stale','beam_record_id':'same_as_speckle'}
  for key,value in changes.items():
   cc=copy.deepcopy(c);target=next((o for o in cc['observations'].values() if key in o and o[key] not in [None,False,'not_observed']),None)
   if target is None:target=next(iter(cc['observations'].values()))
   target[key]=value;self.assertTrue(validate(cc,e),key)
if __name__=='__main__':unittest.main()
