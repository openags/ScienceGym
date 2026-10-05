"""Original static guard regression tests. SPDX-License-Identifier: Apache-2.0"""
import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from scene_guards import *
class Guards(unittest.TestCase):
 def test_routes(self):
  for r in ROUTES.values():
   for a in r['target_anchor_ids']:
    with self.subTest(route=r['route_id'],anchor=a):
     x=evaluate_request(r['route_id'],a,'inspect_geometry');self.assertEqual(x['status'],'EVIDENCE_ONLY_ACCEPTED');self.assertFalse(x['physical_permission']);self.assertEqual(x['commands_emitted'],[])
 def test_actions(self):
  for a in ['move','grasp','release','dispense','dry','open_service','set_lamp','focus','acquire','start_sem','fabricate','set_vacuum','simulate','execute_model','evaluate_resolution','actuate','beam','laser','delete_gap','']:
   self.assertEqual(evaluate_request('R07','A05.optical_record',a)['status'],'REJECTED')
 def test_bypass(self):
  for k in BOOLS:self.assertEqual(evaluate_request('R07','A05.optical_record','inspect_geometry',{k:True})['status'],'REJECTED')
 def test_inputs(self):
  for route,anchor,action,e in [(None,None,None,None),([],{},3,[]),('R99','A05.optical_record','inspect_geometry',{}),('R07','A04.sil_0p5mm_identity','inspect_geometry',{}),('R07','A05.optical_record','inspect_geometry',{'unknown_flag':True}),('R07','A05.optical_record','inspect_geometry',{'actuation_enabled':'false'})]:self.assertEqual(evaluate_request(route,anchor,action,e)['status'],'REJECTED')
 def test_source_controls(self):
  cases=[('R08','A02.star_identity',{'star_sphere_diameter_um':4.74}),('R09','A04.sil_0p5mm_identity',{'sil_diameter_mm':2.5}),('R09','A04.sil_2p5mm_identity',{'sil_diameter_mm':2.5,'objective_magnification':80}),('R11','A07.virtual_frame',{'plane_id':'FRAME_OBJECT'}),('R07','A05.optical_record',{'measurement_category':'render','treated_as_new_measurement':True})]
  for r,a,e in cases:self.assertEqual(evaluate_request(r,a,'select_evidence',e)['status'],'REJECTED')
 def test_anchor_identity(self):
  for a,e in [('A02.grating_identity',{'target_family':'star_film'}),('A02.aao_identity',{'target_family':'optical_disc'}),('A04.sil_0p5mm_identity',{'objective_magnification':40}),('A04.sil_2p5mm_identity',{'objective_magnification':80})]:self.assertEqual(evaluate_request('R09',a,'select_evidence',e)['status'],'REJECTED')
 def test_branch_route(self):
  for r in ROUTES.values():
   for b in CONTRACT['branch_ids']:
    x=evaluate_request(r['route_id'],r['target_anchor_ids'][0],'select_evidence',{'branch_id':b})
    self.assertEqual(x['status'],'EVIDENCE_ONLY_ACCEPTED' if b in r['branch_ids'] else 'REJECTED')
 def test_service(self):self.assertEqual(evaluate_request('R03','A06.preparation_service_receipt','propose_service_request')['status'],'HOLD_QUALIFICATION')
 def test_closeout(self):
  self.assertEqual(check_closeout({})['status'],'HOLD')
  r={k:{'evidence_id':'example-only','provider_id':'external-verification-required','independently_observed':True} for k in ['independent_safe_state','particle_containment','supported_carrier','receiver_custody','archive_record']};r['no_pending_service_jobs']=True
  x=check_closeout(r);self.assertEqual(x['status'],'METADATA_COMPLETE_NOT_PHYSICAL_AUTHORIZATION');self.assertFalse(x['physical_permission'])
if __name__=='__main__':unittest.main(verbosity=2)
