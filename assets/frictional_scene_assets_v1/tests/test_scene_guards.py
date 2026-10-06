"""Original static-scene hostile request tests. SPDX-License-Identifier: Apache-2.0"""
import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from scene_guards import *
class Guards(unittest.TestCase):
 def test_every_route_anchor(self):
  for r in ROUTES.values():
   for a in r['anchor_ids']:
    x=evaluate_request(r['route_id'],a,'inspect_geometry');self.assertEqual(x['status'],'EVIDENCE_ONLY_ACCEPTED');self.assertFalse(x['physical_permission']);self.assertEqual(x['commands_emitted'],[]);self.assertEqual(len(x['qualification_holds']),20)
 def test_physical_actions(self):
  for a in ['move','grasp','release','dispense','mix','open_service','set_pressure','pump','fabricate','simulate','execute_model','drill','break_glass','delete_gap','']:
   self.assertEqual(evaluate_request('R05','A04.closed_service',a)['status'],'REJECTED')
 def test_claim_bypasses(self):
  for k in BOOLS:
   for value in [True,'false',0,1,[],{}]:self.assertEqual(evaluate_request('R05','A04.closed_service','inspect_geometry',{k:value})['status'],'REJECTED')
 def test_schema(self):
  for r,a,act,e in [(None,None,None,None),([],{},3,[]),('R99','A04.closed_service','inspect_geometry',{}),('R05','A08.archive_record','inspect_geometry',{}),('R05','A04.closed_service','inspect_geometry',{'unknown':True}),('R05','A04.closed_service','inspect_geometry',{'hardware_commands':{}}),('R05','A04.closed_service','inspect_geometry',{'plate_thickness_mm':float('nan')}),('R05','A04.closed_service','inspect_geometry',{'branch_id':3})]:self.assertEqual(evaluate_request(r,a,act,e)['status'],'REJECTED')
 def test_route_branch_matrix(self):
  for r in ROUTES.values():
   for b in CONTRACT['branch_ids']:
    x=evaluate_request(r['route_id'],r['anchor_ids'][0],'select_evidence',{'branch_id':b});self.assertEqual(x['status'],'EVIDENCE_ONLY_ACCEPTED' if b in r['branch_ids'] else 'REJECTED')
 def test_route_station_matrix(self):
  for r in ROUTES.values():
   for st in CONTRACT['station_ids']:
    x=evaluate_request(r['route_id'],r['anchor_ids'][0],'select_evidence',{'station_id':st});self.assertEqual(x['status'],'EVIDENCE_ONLY_ACCEPTED' if st in r['station_ids'] else 'REJECTED')
 def test_cell_variant_identity(self):
  for a,d in [('A02.cell_10mm',19),('A02.cell_19mm',10),('A02.cell_10mm',11),('A02.cell_10mm',True),('A02.cell_10mm',10**1000),('A02.cell_19mm',float('inf'))]:self.assertEqual(evaluate_request('R02',a,'select_evidence',{'plate_thickness_mm':d})['status'],'REJECTED')
 def test_every_service_is_held(self):
  for r in ROUTES.values():
   x=evaluate_request(r['route_id'],r['anchor_ids'][0],'propose_service_request');self.assertEqual(x['status'],'HOLD_QUALIFICATION');self.assertFalse(x['physical_permission'])
 def test_returned_holds_are_defensive_copy(self):
  x=evaluate_request('R05','A04.closed_service','inspect_geometry');x['qualification_holds'].clear()
  y=evaluate_request('R05','A04.closed_service','propose_service_request');self.assertEqual(len(y['qualification_holds']),20);self.assertEqual(len(CONTRACT['unknown_ids']),20)
 def test_closeout(self):
  self.assertEqual(check_closeout({})['status'],'HOLD')
  r={k:{'evidence_id':'example-only','provider_id':'external-verification-required','independently_observed':True} for k in ['independent_safe_state','contained_material','supported_carrier','receiver_custody','inspection_disposition','archive_record']};r['no_pending_service_jobs']=True
  x=check_closeout(r);self.assertEqual(x['status'],'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION');self.assertFalse(x['physical_permission'])
  for k in r:
   bad=dict(r);bad[k]=False;self.assertEqual(check_closeout(bad)['status'],'HOLD')
if __name__=='__main__':unittest.main(verbosity=2)
