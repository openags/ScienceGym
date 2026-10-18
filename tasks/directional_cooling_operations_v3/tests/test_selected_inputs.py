import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import selected_reconstruction
import episode_inputs

class SelectedInputs(unittest.TestCase):
    def setUp(self):self.profile=selected_reconstruction.build()
    def test_complete_selection_is_not_evidence(self):
        values=episode_inputs.validate(self.profile)
        self.assertEqual(len(values),14)
        self.assertEqual(values['allocation_card']['specimen_ids'],['white','black'])
        self.assertFalse(self.profile['whole_paper_physics_validated'])
    def test_missing_value_and_false_provenance_rejected(self):
        for mutation in ['missing','provenance','qualification']:
            p=copy.deepcopy(self.profile);row=p['cards']['scene_card']['robot_limits']
            if mutation=='missing':row['value']=None
            elif mutation=='provenance':row['origin']='source';row['source_locator']=None
            else:p['whole_paper_physics_validated']=True
            with self.subTest(mutation=mutation),self.assertRaises(episode_inputs.InputError):episode_inputs.validate(p)
    def test_port_alias_and_commercial_resizing_rejected(self):
        for mutation in ['channels','bore','heater']:
            p=copy.deepcopy(self.profile)
            if mutation=='channels':p['cards']['calibration_card']['probe_to_channel_map']['value']['TC_B']=0
            else:p['cards']['fabrication_card']['actual_dimensions']['value'][{'bore':'RTD_bore_mm','heater':'heater_diameter_mm'}[mutation]]=6 if mutation=='bore' else 50
            with self.subTest(mutation=mutation),self.assertRaises(episode_inputs.InputError):episode_inputs.validate(p)
