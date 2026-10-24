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
    def test_substitute_hand_rejected(self):
        self.policy['robot']['alternate_hand_substitution_allowed']=True
        with self.assertRaisesRegex(ValueError,'substitution'):validate_policy(self.policy,self.scene)

if __name__=='__main__':unittest.main()
