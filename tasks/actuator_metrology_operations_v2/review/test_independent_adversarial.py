"""Independent adversarial review of the original, closed-world record verifier.

These tests are NOT physics, authentication, image processing, or actuator safety
certification.  They intentionally mutate both actor records and rehashed
synthetic evaluator records to test the documented fixture-pinned boundary.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reviewed_actuator_contract', ROOT/'tests'/'contract.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


def read(name):
    return json.loads((ROOT/name).read_text())


def first_receipt(bundle, operation, role='human_design'):
    return next(r for r in bundle['receipts'].values()
                if r['operation_id'] == operation and r['binding']['specimen_role'] == role)


def first_frame(bundle, which='after', role='human_design'):
    return next(f for f in bundle['frames'].values()
                if f['binding']['specimen_role'] == role and f['unloaded'] is (which == 'before'))


def rehash(record):
    record['raw_record_hash'] = C.digest({k:v for k,v in record.items() if k != 'raw_record_hash'})


class IndependentAdversarialReview(unittest.TestCase):
    def pair(self, branch='PHYSICAL_ORTHOGONAL', scenario='valid', variant=0, ep='synthetic_episode_independent_review'):
        return C.fixture(branch, scenario, variant, ep)

    def rejected(self, bundle, events):
        result = C.validate(bundle, events)
        self.assertIs(result['accepted'], False, result)
        self.assertEqual(result['synthetic_measurements'], [])
        self.assertIs(result['physical_validated'], False)
        self.assertIs(result['whole_paper_complete'], False)
        self.assertTrue(result['errors'])

    def test_all_authored_fixtures_remain_bounded(self):
        for branch in C.BRANCHES[:2]:
            for scenario in C.SCENARIOS:
                for variant in range(4):
                    with self.subTest(branch=branch, scenario=scenario, variant=variant):
                        bundle, events = self.pair(branch, scenario, variant)
                        result = C.validate(bundle, events)
                        self.assertTrue(result['accepted'], result)
                        self.assertFalse(result['physical_validated'])
                        self.assertFalse(result['whole_paper_complete'])
                        self.assertEqual(result['scope'], 'offline_contract_only')
                        values = result['synthetic_measurements']
                        if scenario in ('short_input', 'base_slip', 'occluded_after'):
                            self.assertEqual(values, [])
                            self.assertEqual(bundle['terminal'], 'safe_quarantined')
                        else:
                            self.assertEqual([x['specimen_role'] for x in values], list(C.ROLES))
                            sign = -1 if scenario == 'wrong_way' else 1
                            self.assertAlmostEqual(values[0]['signed_displacement_ratio'], sign*(2.0+variant*.25)/5.0)
                            self.assertAlmostEqual(values[1]['signed_displacement_ratio'], sign*(3.0+variant*.25)/5.0)
                            self.assertTrue(all(x['synthetic_only'] for x in values))

    def test_default_hold_has_no_acquisition_or_movement(self):
        bundle, events = C.fixture()
        self.assertTrue(C.validate(bundle, events)['accepted'])
        self.assertEqual([e['operation_id'] for e in events], ['HOLD_DIRECTION','ARCHIVE','CLEAN_STORE'])
        self.assertFalse(bundle['frames'])
        self.assertFalse(bundle['calibrations'])
        self.assertEqual(bundle['terminal'], 'safe_direction_hold')
        for op in ['DOCK_SPECIMEN','FIX_BASE','REQUEST_INPUT','CAPTURE_AFTER','COMPUTE_EFFICIENCY']:
            changed = copy.deepcopy(events)
            changed.insert(1, dict(event_id='INJECT', operation_id=op, specimen_id='none', evidence_id='none'))
            self.rejected(bundle, changed)

    def test_actor_has_only_declared_ids(self):
        bundle, events = self.pair()
        fields = read('episode_input_contract.json')['actor_fields']
        self.assertEqual(set(fields), {'event_id','operation_id','specimen_id','evidence_id'})
        for event in events:
            self.assertEqual(set(event), set(fields))
        for forbidden in read('episode_input_contract.json')['actor_cannot_supply']:
            for ix in (0, 8, 12, len(events)-1):
                changed = copy.deepcopy(events)
                changed[ix][forbidden] = True
                with self.subTest(field=forbidden, event=ix):
                    self.rejected(bundle, changed)

    def test_every_operation_is_required(self):
        bundle, events = self.pair()
        for ix, event in enumerate(events):
            with self.subTest(missing=event['operation_id'], index=ix):
                self.rejected(bundle, events[:ix]+events[ix+1:])

    def test_adjacent_reordering_is_rejected(self):
        bundle, events = self.pair()
        for ix in range(len(events)-1):
            changed = copy.deepcopy(events)
            changed[ix], changed[ix+1] = changed[ix+1], changed[ix]
            with self.subTest(index=ix):
                self.rejected(bundle, changed)

    def test_event_and_receipt_replay_is_rejected(self):
        bundle, events = self.pair()
        self.rejected(bundle, events+events)
        for ix in (1, 10, len(events)-1):
            changed = copy.deepcopy(events)
            changed[ix] = copy.deepcopy(events[0])
            self.rejected(bundle, changed)
        changed = copy.deepcopy(events)
        changed[10]['evidence_id'] = events[7]['evidence_id']
        self.rejected(bundle, changed)

    def test_cross_episode_replay_is_rejected(self):
        bundle, events = self.pair()
        other, other_events = self.pair(ep='synthetic_episode_other_review')
        self.rejected(bundle, other_events)
        self.rejected(other, events)
        stale = copy.deepcopy(bundle)
        stale['frames'][next(iter(stale['frames']))] = copy.deepcopy(next(iter(other['frames'].values())))
        self.rejected(stale, events)

    def test_cross_branch_and_role_swaps_are_rejected(self):
        bundle, events = self.pair()
        other, other_events = self.pair('PHYSICAL_ANTIPARALLEL')
        self.rejected(bundle, other_events)
        self.rejected(other, events)
        changed = copy.deepcopy(events)
        changed[0]['specimen_id'] = bundle['fixture_instance_id']+'_machine_design'
        self.rejected(bundle, changed)
        changed = copy.deepcopy(bundle)
        f = first_frame(changed)
        f['binding']['specimen_role'] = 'machine_design'
        rehash(f)
        self.rejected(changed, events)

    def test_same_episode_different_fixture_configuration_is_not_replayable(self):
        bundle, events = self.pair()
        for branch, scenario, variant in [('PHYSICAL_ANTIPARALLEL','valid',0),
                                          ('PHYSICAL_ORTHOGONAL','wrong_way',0),
                                          ('PHYSICAL_ORTHOGONAL','valid',1)]:
            other, other_events = self.pair(branch,scenario,variant)
            self.assertEqual(bundle['episode_id'],other['episode_id'])
            self.assertNotEqual(bundle['fixture_instance_id'],other['fixture_instance_id'])
            self.assertTrue(set(bundle['receipts']).isdisjoint(other['receipts']))
            self.assertTrue(set(bundle['frames']).isdisjoint(other['frames']))
            self.assertTrue(set(bundle['calibrations']).isdisjoint(other['calibrations']))
            self.rejected(bundle,other_events)
            self.rejected(other,events)

    def test_both_matched_control_lifecycles_required(self):
        bundle, events = self.pair()
        for role in C.ROLES:
            selected = [e for e in events if e['specimen_id'] == bundle['fixture_instance_id']+'_'+role]
            self.rejected(bundle, selected)
        receipts = list(bundle['receipts'].values())
        for role in C.ROLES:
            role_receipts = [r for r in receipts if r['binding']['specimen_role'] == role]
            self.assertEqual([r['operation_id'] for r in role_receipts], read('lifecycle_contract.json')['normal_phases'])
        before = [first_frame(bundle, 'before', role) for role in C.ROLES]
        self.assertNotEqual(before[0]['binding']['specimen_id'], before[1]['binding']['specimen_id'])
        self.assertNotEqual(before[0]['binding']['attempt_id'], before[1]['binding']['attempt_id'])
        calibrations = list(bundle['calibrations'].values())
        for key in ['input_target_mm','input_tolerance_mm','t_in','t_out','n']:
            self.assertEqual(calibrations[0][key], calibrations[1][key])

    def test_rehashed_stale_lineage_is_rejected(self):
        bundle, events = self.pair()
        for key in ['episode_id','fixture_instance_id','attempt_id','specimen_id','specimen_role','branch_id','topology_hash',
                    'material_lot','mount_revision','node_map_id','calibration_id','camera_pose_id',
                    'direction_card_id','qualification_revision']:
            changed = copy.deepcopy(bundle)
            f = first_frame(changed)
            f['binding'][key] = 'stale_or_substituted'
            rehash(f)
            with self.subTest(binding=key):
                self.rejected(changed, events)

    def test_before_after_frame_and_timestamp_freshness(self):
        bundle, events = self.pair()
        for mutation in ['same_frame','timestamp_equal','timestamp_older','camera_stale','unregistered','unloaded_after']:
            changed = copy.deepcopy(bundle)
            before, after = first_frame(changed, 'before'), first_frame(changed)
            if mutation == 'same_frame':
                after.update(copy.deepcopy(before))
            elif mutation == 'timestamp_equal':
                after['timestamp_tick'] = before['timestamp_tick']
            elif mutation == 'timestamp_older':
                after['timestamp_tick'] = before['timestamp_tick']-1
            elif mutation == 'camera_stale':
                after['camera_pose_current'] = False
            elif mutation == 'unregistered':
                after['registered'] = False
            else:
                after['unloaded'] = True
            rehash(after)
            with self.subTest(mutation=mutation):
                self.rejected(changed, events)

    def test_raw_hash_does_not_authorize_modified_measurements(self):
        bundle, events = self.pair()
        for role in C.ROLES:
            changed = copy.deepcopy(bundle)
            f = first_frame(changed, role=role)
            f['nodes']['O1'][0] -= 100.0
            rehash(f)
            result = first_receipt(changed, 'COMPUTE_EFFICIENCY', role)
            result['details']['value'] = 1.53
            rehash(result)
            self.rejected(changed, events)

    def test_node_identity_cardinality_and_numeric_type(self):
        bundle, events = self.pair()
        mutations = ['missing','extra','renamed','boolean','nan','infinity','wrong_dimension','string','extreme']
        for mutation in mutations:
            changed = copy.deepcopy(bundle)
            f = first_frame(changed)
            nodes = f['nodes']
            if mutation == 'missing': del nodes['O1']
            elif mutation == 'extra': nodes['O3'] = [1.0,1.0]
            elif mutation == 'renamed': nodes['UNQUALIFIED_NODE'] = nodes.pop('O1')
            elif mutation == 'boolean': nodes['O1'][0] = True
            elif mutation == 'nan': nodes['O1'][0] = float('nan')
            elif mutation == 'infinity': nodes['O1'][0] = float('inf')
            elif mutation == 'wrong_dimension': nodes['O1'] = [1.0,2.0,3.0]
            elif mutation == 'string': nodes['O1'][0] = '250.0'
            elif mutation == 'extreme': nodes['O1'][0] = 1e308
            if mutation not in ('nan','infinity'): rehash(f)
            with self.subTest(mutation=mutation):
                self.rejected(changed, events)

    def test_calibration_and_direction_mutation(self):
        bundle, events = self.pair()
        changes = [('matrix_mm_per_pixel', [[.1,0],[0,.1]]),
                   ('matrix_mm_per_pixel', [[0.,0.],[0.,0.]]),
                   ('matrix_mm_per_pixel', [[.1,0,0],[0,-.1,0]]),
                   ('n', 4), ('n', True), ('source_physical_n', 2),
                   ('input_target_mm', 4.), ('t_out', [1.,0.]),
                   ('t_in', [0.,1.]), ('qualified_for_real_use', True)]
        for key, value in changes:
            changed = copy.deepcopy(bundle)
            next(iter(changed['calibrations'].values()))[key] = value
            with self.subTest(key=key, value=value):
                self.rejected(changed, events)
        changed = copy.deepcopy(bundle)
        c = next(iter(changed['calibrations'].values()))
        c['node_groups']['output'] = ['O1','O1']
        self.rejected(changed, events)

    def test_request_acknowledgements_do_not_prove_state(self):
        bundle, events = self.pair()
        for command, observation in [('FIX_BASE','VERIFY_BASE'),('REQUEST_INPUT','VERIFY_INPUT'),('RELEASE_INPUT','VERIFY_UNLOADED')]:
            for role in C.ROLES:
                command_r = first_receipt(bundle, command, role)
                observed_r = first_receipt(bundle, observation, role)
                self.assertIs(command_r['details']['state_observed'], False)
                self.assertIs(observed_r['details']['independent_observation'], True)
                changed = copy.deepcopy(bundle)
                target = first_receipt(changed, observation, role)
                target['details'] = copy.deepcopy(command_r['details'])
                rehash(target)
                with self.subTest(command=command, role=role):
                    self.rejected(changed, events)

    def test_qualified_receipts_cannot_be_actor_promoted(self):
        bundle, events = self.pair()
        for key, value in [('current',False), ('production_authority',True), ('authority','actor'), ('card_ids',[])]:
            changed = copy.deepcopy(bundle)
            r = first_receipt(changed, 'VERIFY_CARDS')
            r['details'][key] = value
            rehash(r)
            self.rejected(changed, events)

    def test_unsafe_state_claims_fail_closed(self):
        bundle, events = self.pair()
        cases = [('VERIFY_BASE','base_fixed',False), ('VERIFY_BASE','output_free',False),
                 ('VERIFY_INPUT','base_fixed',False), ('VERIFY_INPUT','input_pass',False),
                 ('VERIFY_INPUT','independent_observation',False),
                 ('VERIFY_UNLOADED','unloaded',False), ('VERIFY_UNLOADED','supported',False),
                 ('UNFIX_BASE','supported',False), ('UNFIX_BASE','base_released',False),
                 ('RETRIEVE_SPECIMEN','custody_complete',False),
                 ('INSPECT_SPECIMEN','condition','damaged'),
                 ('ARCHIVE','raw_records_preserved',False), ('ARCHIVE','failed_attempts_preserved',False),
                 ('CLEAN_STORE','cleanup_observed',False)]
        for operation, key, value in cases:
            changed = copy.deepcopy(bundle)
            r = first_receipt(changed, operation)
            r['details'][key] = value
            rehash(r)
            with self.subTest(operation=operation, key=key):
                self.rejected(changed, events)

    def test_failed_metrology_quarantines_without_efficiency(self):
        for scenario in ['short_input','base_slip','occluded_after']:
            bundle, events = self.pair(scenario=scenario)
            result = C.validate(bundle, events)
            self.assertTrue(result['accepted'])
            self.assertEqual(result['synthetic_measurements'], [])
            for role in C.ROLES:
                ops = [r['operation_id'] for r in bundle['receipts'].values() if r['binding']['specimen_role'] == role]
                self.assertIn('QUARANTINE', ops)
                self.assertNotIn('COMPUTE_EFFICIENCY', ops)
                self.assertIn('VERIFY_UNLOADED', ops)
                self.assertIn('RETRIEVE_SPECIMEN', ops)
                self.assertIn('CLEAN_STORE', ops)
            changed = [e for e in events if e['operation_id'] != 'QUARANTINE']
            self.rejected(bundle, changed)

    def test_damage_preserves_measurement_but_blocks_reuse(self):
        bundle, events = self.pair(scenario='damage')
        self.assertTrue(C.validate(bundle, events)['accepted'])
        self.assertEqual(bundle['terminal'], 'safe_quarantined')
        for role in C.ROLES:
            self.assertIs(first_receipt(bundle,'INSPECT_SPECIMEN',role)['details']['reuse_permitted'], False)
            self.assertIs(first_receipt(bundle,'QUARANTINE',role)['details']['reuse_permitted'], False)
            self.assertEqual(first_receipt(bundle,'CLEAN_STORE',role)['details']['custody'], 'quarantined_storage')
        self.rejected(bundle, [e for e in events if e['operation_id'] != 'QUARANTINE'])

    def test_positive_signed_projection_not_norm_or_source_outcome(self):
        self.assertAlmostEqual(C.project_ratio([0.,-5.],[-2.,37.],[0.,-1.],[-1.,0.]), .4)
        self.assertAlmostEqual(C.project_ratio([0.,-5.],[2.,37.],[0.,-1.],[-1.,0.]), -.4)
        self.assertAlmostEqual(C.project_ratio([0.,-5.],[37.,3.],[0.,-1.],[0.,1.]), .6)
        self.assertAlmostEqual(C.project_ratio([0.,-5.],[37.,-3.],[0.,-1.],[0.,1.]), -.6)
        for branch in C.BRANCHES[:2]:
            bundle, events = self.pair(branch)
            for role, outcome in [('human_design', 1.0), ('machine_design', 1.53)]:
                changed = copy.deepcopy(bundle)
                r = first_receipt(changed, 'COMPUTE_EFFICIENCY', role)
                r['details']['value'] = outcome
                r['details']['source_outcome_used'] = True
                rehash(r)
                self.rejected(changed, events)

    def test_group_means_pixel_y_flip_and_calibrated_transform(self):
        before = {'A':[10.,10.], 'B':[30.,10.]}
        after = {'A':[10.,40.], 'B':[30.,80.]}
        self.assertEqual(C.mean_delta(before,after,['A','B'],[[.1,0.],[0.,-.1]]), [0.,-5.])
        self.assertEqual(C.mean_delta(before,after,['A','B'],[[0.,-.1],[.1,0.]]), [-5.,0.])
        for ids in ([], ['A','A']):
            with self.assertRaises(ValueError):
                C.mean_delta(before,after,ids,[[.1,0.],[0.,-.1]])
        with self.assertRaises(ValueError):
            C.mean_delta(before,after,['A'],[[1.,0.],[0.,0.]])

    def test_denominator_and_unit_vector_guards(self):
        for input_delta in ([0.,0.],[0.,5.],[0.,-1e-13]):
            with self.assertRaises(ValueError):
                C.project_ratio(input_delta,[-2.,0.],[0.,-1.],[-1.,0.])
        for t in ([0.,-2.],[0.,0.],[True,0.],[float('nan'),0.]):
            with self.assertRaises(ValueError):
                C.project_ratio([0.,-5.],[-2.,0.],t,[-1.,0.])

    def test_schema_type_and_unknown_fields(self):
        bundle, events = self.pair()
        for bad in (None, False, [], 'fixture'):
            self.rejected(bad, events)
            self.rejected(bundle, bad)
        for field, bad in [('variant',True),('variant',.0),('variant',99),('scenario','unknown'),
                           ('branch_id','FABRICATE'),('episode_id',None),('production_authority',True),
                           ('whole_paper_complete',True),('physical_execution',True),('numerical_reproduction',True)]:
            changed = copy.deepcopy(bundle)
            changed[field] = bad
            self.rejected(changed, events)
        changed = copy.deepcopy(bundle)
        changed['actor_supplied_success'] = True
        self.rejected(changed, events)
        for field in ['event_id','operation_id','specimen_id','evidence_id']:
            changed = copy.deepcopy(events)
            changed[0][field] = 1
            self.rejected(bundle, changed)

    def test_release_scope_and_route_coverage(self):
        boundary = read('RELEASE_BOUNDARY.json')
        self.assertIs(boundary['whole_paper_complete'], False)
        self.assertIs(boundary['qualifies_for_full_paper_target_count'], False)
        self.assertIs(boundary['real_actuation_implemented'], False)
        self.assertIs(boundary['physical_simulation_run'], False)
        self.assertIs(boundary['numerical_reproduction_run'], False)
        self.assertIs(boundary['author_code_included'], False)
        self.assertIs(boundary['publisher_assets_included'], False)
        branches = read('branches.json')['branches']
        self.assertEqual(len(branches), 15)
        self.assertEqual({b['id'] for b in branches if b['synthetic_lifecycle_verified']}, set(C.BRANCHES))
        self.assertTrue(all(not b['physical_execution_implemented'] and not b['numerical_execution_implemented'] for b in branches))
        self.assertFalse(read('branches.json')['source_fabrication_completion_credited'])
        self.assertEqual(set(read('source_conflicts.json')['conflicts'][i]['id'] for i in range(4)),set(C.CONFLICTS))
        self.assertTrue(all(x['resolved'] is False for x in read('source_conflicts.json')['conflicts']))

    def test_public_fixture_boundary_does_not_claim_global_authentication(self):
        # Re-validating an identical offline fixture is deterministic and accepted.
        # Replay protection means replay within a trace or across bound episodes,
        # not an authenticated persistent registry across validate() invocations.
        bundle, events = self.pair()
        self.assertEqual(C.validate(bundle,events),C.validate(bundle,events))
        self.assertFalse(bundle['production_authority'])
        self.assertIn('physical authentication',read('mock_contract.json')['not_implemented'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
