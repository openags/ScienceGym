"""Negative regression tests for the owner's high-impact scope choices."""
import json
import unittest
from geometry_tools import HERE
from build_readiness import validate_policy

class PilotPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads((HERE/'pilot_contract.json').read_text())
        self.scene=json.loads((HERE/'scene.json').read_text())
    def test_current_candidate_is_within_asset_phase(self):validate_policy(self.policy,self.scene)
    def test_actor_truth_channel_rejected(self):
        self.policy['observations']['allowed_channels'].append('simulator object poses')
        with self.assertRaisesRegex(ValueError,'privileged'):validate_policy(self.policy,self.scene)
    def test_hidden_robot_fixture_rejected(self):
        self.scene['architecture']['part_records'].append({'id':'cheat_dock','role':'custom_fixture'})
        with self.assertRaisesRegex(ValueError,'fixture'):validate_policy(self.policy,self.scene)
    def test_fiducial_permission_cannot_be_inferred(self):
        self.policy['adaptations']['added_fiducials_allowed']=True
        with self.assertRaisesRegex(ValueError,'fiducial'):validate_policy(self.policy,self.scene)
    def test_green_checks_cannot_authorize_manipulation(self):
        self.policy['new_manipulation_development_allowed']=True
        with self.assertRaisesRegex(ValueError,'acceptance'):validate_policy(self.policy,self.scene)
    def test_owner_authorized_hand_selection_allowed(self):
        self.policy['robot']['alternate_hand_substitution_allowed']=True
        validate_policy(self.policy,self.scene)
    def test_non_unitree_body_rejected(self):
        self.policy['robot']['body_manufacturer']='Other'
        with self.assertRaisesRegex(ValueError,'Unitree'):validate_policy(self.policy,self.scene)
    def test_different_hand_cannot_reuse_provenance(self):
        self.policy['robot']['hands']=['Inspire DFQ left','Inspire DFQ right']
        with self.assertRaisesRegex(ValueError,'provenance'):validate_policy(self.policy,self.scene)
    def test_silent_model_relabeling_rejected(self):
        self.policy['robot']['silent_model_relabeling_allowed']=True
        with self.assertRaisesRegex(ValueError,'relabeling'):validate_policy(self.policy,self.scene)

if __name__=='__main__':unittest.main()
