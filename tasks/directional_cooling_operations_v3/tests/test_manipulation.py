import copy
import json
import sys
import unittest
from pathlib import Path
import jsonschema

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import planner
from validate_manipulation import validate_contract, validate_terminal_connection


class ManipulationTests(unittest.TestCase):
    def setUp(self):
        self.ops=planner.read('operations')['operations']
        self.interfaces=planner.read('interaction_contracts')
        self.bindings=planner.read('asset_bindings')
        self.terminals=planner.read('daq_terminal_contract')
        self.sensors=planner.read('sensor_installation')
        self.parts=json.loads((HERE.parents[1]/'assets/cooling_scene_assets_v2/parts.json').read_text())['parts']
        self.coverage=planner.read('manipulation_coverage')
    def validate(self):
        return validate_contract(self.ops,self.interfaces,self.bindings,self.terminals,self.sensors,self.parts,self.coverage)
    def rejects(self):
        with self.assertRaises(ValueError):self.validate()
    def test_complete_contract(self):
        result=self.validate()
        self.assertGreater(result['manipulation_steps'],0)
        self.assertGreater(result['interfaces_without_geometry'],0)
    def test_manual_action_requires_support_and_observation(self):
        s=next(s for o in self.ops for s in o['reference_steps'] if 'interaction' in s)
        s['interaction'].pop('support_transition');self.rejects()
    def test_schema_rejects_missing_interaction(self):
        d=planner.read('operations')
        s=next(s for o in d['operations'] for s in o['reference_steps'] if 'interaction' in s)
        s.pop('interaction')
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,planner.read('operations.schema'))
    def test_wrong_interface_rejected(self):
        s=next(s for o in self.ops for s in o['reference_steps'] if 'interaction' in s)
        s['interaction']['interface_id']='unregistered_gripper';self.rejects()
    def test_duplicate_operation_binding_rejected(self):
        self.bindings['bindings'].append(copy.deepcopy(self.bindings['bindings'][0]));self.rejects()
    def test_suffix_is_not_exact_part_binding(self):
        b=next(b for b in self.bindings['bindings'] if b['part_selection'])
        b['part_selection'][0]=b['part_selection'][0].split('__')[-1];self.rejects()
    def test_exploded_pose_not_executable_variant(self):
        i=next(i for i in self.interfaces['interfaces'] if i['asset_variants'])
        i['asset_variants'][0]['root_id']='COOLER_EXPLODED';self.rejects()
    def test_missing_wire_entry_rejected(self):
        pid=self.terminals['terminals'][2]['wire_entry_part_id']
        self.parts=[p for p in self.parts if p['id']!=pid];self.rejects()
    def test_reversed_channel_four_pin_order(self):
        c=self.terminals['channels'][4];c['positive_pin'],c['negative_pin']=c['negative_pin'],c['positive_pin'];self.rejects()
    def test_map_probe_cannot_be_assigned_to_unrelated_part(self):
        self.sensors['sensors'][1]['target_part_id']='COOLER_THERMAL_MAP__PE_support';self.rejects()
    def test_map_coordinate_differs_from_model(self):
        self.sensors['sensors'][1]['position_in_asset_root_m'][0]+=.01;self.rejects()
    def test_duplicate_probe_identity_rejected(self):
        self.sensors['sensors'][1]['probe_role']=self.sensors['sensors'][0]['probe_role'];self.rejects()
    def connection(self):
        return dict(channel=4,positive_pin=44,negative_pin=43,probe_wire_AWG=36,terminal_wire_AWG=24,
            transition_id='synthetic_adapter',transition_qualification_id='synthetic_qualification',calibrated_connection_path_id='synthetic_calibration')
    def test_terminal_connection_contract(self):
        self.assertTrue(validate_terminal_connection(self.connection(),self.terminals))
    def test_direct_36awg_clamp_rejected(self):
        c=self.connection();c['terminal_wire_AWG']=36
        with self.assertRaises(ValueError):validate_terminal_connection(c,self.terminals)
    def test_unqualified_fine_wire_transition_rejected(self):
        c=self.connection();c.pop('transition_qualification_id')
        with self.assertRaises(ValueError):validate_terminal_connection(c,self.terminals)
    def test_wrong_pin_polarity_card_rejected(self):
        c=self.connection();c['positive_pin']=43
        with self.assertRaises(ValueError):validate_terminal_connection(c,self.terminals)
    def test_angle_reference_cannot_precede_angle_configuration(self):
        plan=planner.compile_reference(planner.fixture())
        e=next(e for e in plan['occurrences'] if e['operation_id']=='ANGLE_REFERENCE');e['angle_deg']=80
        with self.assertRaises(planner.PlanError):planner.verify_plan(plan)
    def test_missing_manual_step_cannot_pass_symbolic_plan(self):
        plan=planner.compile_reference(planner.fixture())
        e=next(e for e in plan['occurrences'] if e['operation_id']=='CAL_MOUNT');e['required_step_ids'].pop()
        with self.assertRaises(planner.PlanError):planner.verify_plan(plan)
    def test_missing_calibration_block_producer_rejected(self):
        plan=planner.compile_reference(planner.fixture())
        plan['occurrences']=[e for e in plan['occurrences'] if e['operation_id']!='CAL_BLOCK_PREP']
        with self.assertRaises(planner.PlanError):planner.verify_plan(plan)
    def test_reference_artifacts_removed_from_actor_nested_inputs(self):
        d=planner.actor_projection({'current_observations':{'interaction_contracts':self.interfaces,'sensor_installation':self.sensors,'observed_temperature':20}})
        self.assertEqual(d,{'current_observations':{'observed_temperature':20}})


if __name__=='__main__':unittest.main()
