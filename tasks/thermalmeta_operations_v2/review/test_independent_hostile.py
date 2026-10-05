"""Independently authored structural/hostile tests; no source media or physics.

Run from the public package root: python3 -B -m unittest discover -s review -v
Synthetic fixtures are written here independently of the author's tests.
"""
from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runtime.symbolic_guard import (SymbolicEpisode, Held, fixture_receipt,
                                    verify_preparation, NUMERICAL_BRANCHES)

FAMILIES = ('CLOAK', 'ROTATOR45', 'CONCENTRATOR18')
CELLS = {f'COND_{family}_{axis}' for family in FAMILIES for axis in ('X', 'Y')}


def read(name):
    return json.loads((ROOT / name).read_text())


def token(identity, **fields):
    return fixture_receipt(identity, **fields)


def alter(receipt, **fields):
    values = deepcopy(receipt)
    values.update(fields)
    identity = values.pop('receipt_id')
    for key in ('evidence_class', 'issuer_role', 'valid', 'content_hash'):
        values.pop(key, None)
    return token(identity, **values)


def prep(family='CLOAK', specimen=None):
    specimen = specimen or 'AUDIT_' + family
    common = dict(paper_id='thermalmeta-2024-49630', sample_family_id=family,
                  design_id='AUDIT_DESIGN_' + family, design_revision='R0',
                  specimen_id=specimen, service_job_id='JOB_' + specimen,
                  material_lot_ids=['AUDIT_METAL', 'AUDIT_PDMS', 'AUDIT_BACKGROUND'])
    result = []
    for kind in ('design', 'materials', 'lattice', 'intermediate', 'specimen'):
        fields = dict(common, record_type=kind, object_id=specimen + '_' + kind,
                      parent_id=result[-1]['object_id'] if result else None)
        if kind == 'design':
            fields['geometry_qualification'] = True
        if kind in ('intermediate', 'specimen'):
            fields['core_assignment'] = 'PDMS' if family == 'CLOAK' else 'background_encapsulant'
        if kind == 'specimen':
            fields.update(lattice_parent_id=result[2]['object_id'],
                          intermediate_parent_id=result[3]['object_id'],
                          safe_release=True, dry_ambient=True)
        result.append(token('RECEIPT_' + specimen + '_' + kind, **fields))
    return result


def plan():
    return [dict(slot_id='SLOT_' + c, condition_id=c,
                 specimen_id='AUDIT_' + f, repeat_kind='base', approved=True)
            for f in FAMILIES for c in (f'COND_{f}_X', f'COND_{f}_Y')]


def episode():
    e = SymbolicEpisode(plan())
    for family in FAMILIES:
        e.receive(prep(family))
    e.calibrate(token('CAL_RECEIPT', calibration_id='CAL_A', reference_id='REF_A',
                      configuration_id='CAM_A', uncertainty_contract_id='UNC_A',
                      current=True, bracketing_valid=True))
    return e


def start(e, index=0, run='RUN_A'):
    slot = e.plan[index]
    e.mount(slot['slot_id'], token('MOUNT_' + run, specimen_id=slot['specimen_id'],
            condition_id=slot['condition_id'], orientation=slot['condition_id'][-1],
            calibration_id='CAL_A', mount_id='MOUNT_ID_' + run, zero_energy=True,
            dry_ambient=True, qualified_fit=True, registered_transform=True,
            supported_carrier=True))
    e.handoff(run, token('HANDOFF_' + run, run_id=run, mount_id='MOUNT_ID_' + run,
                        specimen_id=slot['specimen_id'], interlocks_valid=True,
                        acceptance='accepted'))
    return slot


def transient(run='RUN_A', **extra):
    extra.setdefault('data_origin', 'synthetic_metadata_only')
    return token('TRANSIENT_' + run, run_id=run, dataset_id='DATA_' + run,
                 timebase='synthetic_order', configuration_id='CAM_A',
                 stream_integrity=True, boundary_metadata=True, **extra)


def stable(run='RUN_A', **extra):
    extra.setdefault('data_origin', 'synthetic_metadata_only')
    return token('STABLE_' + run, run_id=run, qualified_stable=True,
                 drift_contract=True, uncertainty_valid=True, **extra)


def steady(slot, run='RUN_A', **extra):
    return token('STEADY_' + run, run_id=run, dataset_id='DATA_' + run, condition_id=slot['condition_id'],
                 calibration_id='CAL_A', profile_direction='transverse' if
                 'ROTATOR45' in slot['condition_id'] else 'parallel',
                 masks_registered=True, transform_registered=True,
                 measured_boundaries_present=True, ambient_present=True,
                 uncertainty_valid=True, data_hash_valid=True,
                 data_origin='synthetic_metadata_only', **extra)


def release(slot, run='RUN_A', **extra):
    return token('RELEASE_' + run, run_id=run, specimen_id=slot['specimen_id'],
                 zero_energy=True, cool=True, dry=True, supported_carrier=True,
                 receiver_accepts=True, condition_assessed=True, **extra)


def capture(e, slot, run='RUN_A'):
    e.observe('P12', transient(run))
    e.observe('P13', stable(run))
    e.observe('P14', steady(slot, run))


def finish_matrix(e):
    for index in range(6):
        run = 'RUN_' + str(index)
        slot = start(e, index, run)
        capture(e, slot, run)
        e.release(release(slot, run))
        e.retrieve()


def postprocess(e):
    e.reconcile_controls(token('CONTROLS', matched=True, independent_identity=True,
        data_origin='synthetic_metadata_only', denominator_safe=True,
        covers_conditions=sorted(CELLS)))
    e.assess(token('ASSESSMENT', claim_kind='synthetic_contract_pass_only',
        source_holds_preserved=True, numerical_computation_performed=False,
        uncertainty_contract_present=True))
    e.register_numerical({branch: 'unexecuted' for branch in NUMERICAL_BRANCHES})


class StaticCoverage(unittest.TestCase):
    def test_all_json_has_unique_keys(self):
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise AssertionError('duplicate JSON key: ' + key)
                result[key] = value
            return result
        for path in sorted(ROOT.rglob('*.json')):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                json.loads(path.read_text(), object_pairs_hook=unique_pairs)

    def test_twenty_unique_stages(self):
        self.assertEqual([s['id'] for s in read('operations.json')['stages']],
                         [f'P{i:02d}' for i in range(1, 21)])

    def test_all_dependencies_and_loops_resolve(self):
        operations = read('operations.json')
        stages = {s['id'] for s in operations['stages']}
        for stage in operations['stages']:
            self.assertLessEqual(set(stage['depends_on']), stages)
        for loop in operations['loops']:
            self.assertIn(loop['from'], stages)
            self.assertIn(loop['to'], stages)

    def test_all_stages_have_scene_binding(self):
        operations = read('operations.json')['stages']
        scene = read('scene_binding_contract.json')
        anchors = {a['anchor_id'] for a in scene['anchors']}
        assets = {a['asset_id'] for a in scene['assets']}
        for stage in operations:
            self.assertIn(stage['scene_anchor_id'], anchors)
            self.assertLessEqual(set(stage['scene_asset_ids']), assets)
            self.assertFalse(stage['commands_enabled'])

    def test_six_conditions_not_six_specimens(self):
        scene = read('scene_binding_contract.json')['condition_views']
        self.assertEqual({c['condition_id'] for c in scene}, CELLS)
        self.assertEqual(len({c['specimen_id'] for c in scene}), 3)
        self.assertTrue(all(c['independent_specimen_claim'] is False for c in scene))

    def test_rotator_profile_exception(self):
        for cell in read('scene_binding_contract.json')['condition_views']:
            expected = 'transverse_to_applied_reference' if cell['sample_family_id'] == 'ROTATOR45' else 'parallel_to_applied_reference'
            self.assertEqual(cell['profile_direction'], expected)

    def test_profile_number_mapping_is_not_source_claim(self):
        for cell in read('scene_binding_contract.json')['condition_views']:
            self.assertEqual(cell['profile_number_to_orientation_status'],
                             'authored_visual_selector_not_source_verified')

    def test_broad_branch_and_child_coverage(self):
        branches = read('branches.json')
        self.assertEqual({b['id'] for b in branches['families']}, {f'B{i:02d}' for i in range(1, 13)})
        expected = {'B05_FEATURE', 'B05_MATERIAL', 'B09_ROTATOR', 'B09_CONCENTRATOR',
                    'B10_THERMOTICS', 'B10_LAMINATE', 'B10_CONVERSION', 'B10_CIRCULAR',
                    'B10_MAPPING', 'B10_UNION', 'B10_HEAT', 'B10_METRICS'}
        self.assertEqual({b['id'] for b in branches['child_branches']}, expected)
        for child in branches['child_branches']:
            self.assertIn(child['parent'], {b['id'] for b in branches['families']})

    def test_every_branch_remains_unexecuted(self):
        self.assertTrue(all(v.startswith('unexecuted') for v in read('branches.json')['execution_status'].values()))

    def test_source_conflicts_and_unknowns_preserved(self):
        conflicts = read('source_conflicts.json')
        self.assertEqual({c['id'] for c in conflicts}, {f'C{i:02d}' for i in range(1, 10)})
        self.assertTrue(all(c['resolved'] is False for c in conflicts))
        self.assertEqual({u['id'] for u in read('unknown_inputs.json')}, {f'U{i:02d}' for i in range(1, 14)})

    def test_four_key_analysis_holds_present(self):
        text = json.dumps(read('analysis_contract.json'))
        for conflict in ('C01', 'C02', 'C03', 'C05'):
            self.assertIn(conflict, text)

    def test_no_hardware_or_scientific_result_claim(self):
        task = read('task.json')
        self.assertEqual(task['execution_mode'], 'offline_symbolic_only')
        self.assertFalse(task['physical_execution_enabled'])
        self.assertFalse(task['numerical_physics_enabled'])
        self.assertEqual(task['actual_experiments_performed'], 0)
        self.assertEqual(task['validated_runnable_scientific_tasks'], 0)
        self.assertFalse(task['source_reproduction_claim'])

    def test_actor_reference_separation(self):
        actor = read('agent_visible.json')
        self.assertFalse(actor['source_outcome_targets_visible'])
        text = json.dumps(actor).lower()
        for forbidden in ('source_outcomes_reference.json', 'relative temperature deviation', 'source_reported_reference', 'rtd_percent'):
            self.assertNotIn(forbidden, text)
        self.assertIn('No scientific-score', actor['scoring'])

    def test_all_powered_failure_edges_reach_release(self):
        edges = read('operations.json')['failure_edges']
        for stage in ('P11', 'P12', 'P13', 'P14'):
            self.assertTrue(any(e['from'] == stage and e['to'] == 'P15' for e in edges))
        self.assertTrue(any(e['from'] == 'P15' and e['to'] == 'SERVICE_CUSTODY_HOLD' for e in edges))

    def test_repeat_and_control_counts_are_not_invented(self):
        controls = read('controls_and_repeats.json')
        self.assertTrue(controls['no_fabricated_counts'])
        self.assertIn('Not specified', controls['reported']['independent_n'])
        self.assertIn('not replicates', controls['reported']['orientations'])


class HostileRuntime(unittest.TestCase):
    def test_normal_synthetic_six_cell_close_has_zero_experiments(self):
        e = episode()
        finish_matrix(e)
        postprocess(e)
        closed = e.close(success=True, archive_valid=True, dispositions_valid=True)
        self.assertEqual(closed['experiments_performed'], 0)
        self.assertIs(closed['scientific_success'], False)
        self.assertEqual(closed['paper_design_units'], 1)

    def test_cross_specimen_object_reuse_is_rejected(self):
        e = episode()
        original = prep()
        duplicate = prep(specimen='NEW_SPECIMEN')
        mapping = {new['object_id']: old['object_id'] for new, old in zip(duplicate, original)}
        for index, record in enumerate(duplicate):
            fields = {key: mapping.get(value, value) for key, value in record.items()
                      if key in ('object_id', 'parent_id', 'lattice_parent_id', 'intermediate_parent_id')}
            duplicate[index] = alter(record, **fields)
        with self.assertRaises(Held):
            e.receive(duplicate)

    def test_material_lot_collection_cannot_be_string(self):
        chain = prep()
        chain[2] = alter(chain[2], material_lot_ids='NOT_A_COLLECTION')
        with self.assertRaises(Held):
            verify_preparation(chain)

    def test_cross_family_relabel_is_rejected(self):
        chain = prep()
        chain[2] = alter(chain[2], sample_family_id='ROTATOR45')
        with self.assertRaises(Held):
            verify_preparation(chain)

    def test_stale_preparation_revision_is_rejected(self):
        chain = prep()
        chain[-1] = alter(chain[-1], design_revision='R99')
        with self.assertRaises(Held):
            verify_preparation(chain)

    def test_material_lots_may_be_shared_explicitly(self):
        e = episode()
        e.receive(prep(specimen='INDEPENDENT_CLOAK'))
        self.assertIn('INDEPENDENT_CLOAK', e.specimens)

    def test_duplicate_independent_specimen_condition_rejected(self):
        p = plan()
        for suffix in ('A', 'B'):
            p.append(dict(p[0], slot_id='INDEPENDENT_' + suffix,
                          repeat_kind='independent', specimen_id='SAME_INDEPENDENT',
                          replicate_of_slot_id=p[0]['slot_id']))
        with self.assertRaises(Held):
            SymbolicEpisode(p)

    def test_out_of_order_observation_routes_to_failure(self):
        e = episode()
        slot = start(e)
        with self.assertRaises(Held):
            e.observe('P14', steady(slot))
        self.assertEqual(e.state, 'P15')
        self.assertEqual(e.custody, 'service')
        self.assertEqual(len(e.failures), 1)

    def test_wrong_observation_run_routes_to_failure(self):
        e = episode()
        start(e)
        with self.assertRaises(Held):
            e.observe('P12', transient('WRONG_RUN'))
        self.assertEqual(e.state, 'P15')
        self.assertEqual(e.custody, 'service')

    def test_reference_origin_transient_rejected(self):
        e = episode()
        start(e)
        with self.assertRaises(Held):
            e.observe('P12', transient(data_origin='source_reported_reference'))

    def test_reference_origin_stability_rejected(self):
        e = episode()
        start(e)
        e.observe('P12', transient())
        with self.assertRaises(Held):
            e.observe('P13', stable(data_origin='source_reported_reference'))

    def test_transient_numerical_array_rejected(self):
        e = episode()
        start(e)
        with self.assertRaises(Held):
            e.observe('P12', transient(temperature_array=[1.0, 2.0]))

    def test_steady_numerical_array_rejected(self):
        e = episode()
        slot = start(e)
        e.observe('P12', transient())
        e.observe('P13', stable())
        with self.assertRaises(Held):
            e.observe('P14', steady(slot, heat_flux_array=[1.0, 2.0]))

    def test_foreign_camera_configuration_rejected(self):
        e = episode()
        start(e)
        with self.assertRaises(Held):
            e.observe('P12', alter(transient(), configuration_id='UNRELATED_CAMERA'))

    def test_steady_dataset_must_match_transient(self):
        e = episode()
        slot = start(e)
        e.observe('P12', transient())
        e.observe('P13', stable())
        with self.assertRaises(Held):
            e.observe('P14', alter(steady(slot), dataset_id='FOREIGN_DATASET'))
        self.assertEqual(e.state, 'P15')

    def test_false_stability_is_not_elapsed_time(self):
        e = episode()
        start(e)
        e.observe('P12', transient())
        with self.assertRaises(Held):
            e.observe('P13', alter(stable(), qualified_stable=False, elapsed_minutes=45))
        self.assertEqual(e.state, 'P15')

    def test_reference_steady_result_rejected(self):
        e = episode()
        slot = start(e)
        e.observe('P12', transient())
        e.observe('P13', stable())
        with self.assertRaises(Held):
            e.observe('P14', alter(steady(slot), data_origin='source_simulation'))

    def test_release_without_capture_or_abort_is_rejected(self):
        e = episode()
        slot = start(e)
        with self.assertRaises(Held):
            e.release(release(slot))
        self.assertEqual(e.custody, 'service')

    def test_missing_release_cannot_retrieve(self):
        e = episode()
        start(e)
        e.stop('synthetic audit fault')
        with self.assertRaises(Held):
            e.retrieve()
        self.assertEqual(e.custody, 'service')

    def test_foreign_specimen_release_retains_custody(self):
        e = episode()
        slot = start(e)
        e.stop('synthetic audit fault')
        with self.assertRaises(Held):
            e.release(alter(release(slot), specimen_id='OTHER_SPECIMEN'))
        self.assertEqual(e.state, 'SERVICE_CUSTODY_HOLD')
        self.assertEqual(e.custody, 'service')

    def test_release_and_retrieval_are_distinct(self):
        e = episode()
        slot = start(e)
        capture(e, slot)
        e.release(release(slot))
        self.assertEqual(e.custody, 'service')
        self.assertNotIn(slot['slot_id'], e.completed_slots)
        e.retrieve()
        self.assertEqual(e.custody, 'handler')
        self.assertIn(slot['slot_id'], e.completed_slots)

    def test_incomplete_closeout_preserves_open_obligation(self):
        e = episode()
        slot = start(e)
        e.stop('synthetic audit fault')
        result = e.close(success=False)
        self.assertTrue(result['open_service_obligation'])
        self.assertFalse(result['scientific_success'])
        with self.assertRaises(Held):
            e.retrieve()
        e.release(release(slot))
        e.retrieve()
        self.assertEqual(e.state, 'ADMIN_INCOMPLETE_RELEASED')

    def test_failed_attempt_not_counted_complete(self):
        e = episode()
        slot = start(e)
        e.stop('synthetic audit fault')
        e.release(release(slot))
        e.retrieve()
        self.assertEqual(e.runs['RUN_A']['status'], 'failed')
        self.assertNotIn(slot['slot_id'], e.completed_slots)
        self.assertEqual(len(e.failures), 1)

    def test_executed_numerical_branch_cannot_register(self):
        e = episode()
        finish_matrix(e)
        postprocess(e)
        ledger = {branch: 'unexecuted' for branch in NUMERICAL_BRANCHES}
        ledger['B10'] = 'executed'
        with self.assertRaises(Held):
            e.register_numerical(ledger)

    def test_missing_condition_cannot_close_success(self):
        e = episode()
        with self.assertRaises(Held):
            e.close(success=True, archive_valid=True, dispositions_valid=True)

    def test_invalid_hash_does_not_become_observation(self):
        e = episode()
        start(e)
        receipt = transient()
        receipt['timebase'] = 'TAMPERED'
        with self.assertRaises(Held):
            e.observe('P12', receipt)
        self.assertEqual(e.state, 'P15')


class ExportPathGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'tests'))
        from verify_export import names_valid
        cls.validate_names = staticmethod(names_valid)

    def test_public_relative_paths_accepted(self):
        self.validate_names(['task.json', 'review/test_independent_hostile.py'])

    def test_duplicate_archive_names_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate_names(['task.json', 'task.json'])

    def test_parent_traversal_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate_names(['folder/../escape.py'])

    def test_backslash_traversal_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate_names(['folder' + chr(92) + '..' + chr(92) + 'escape.py'])

    def test_drive_qualified_name_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate_names(['C:' + chr(92) + 'escape.py'])

    def test_hidden_path_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate_names(['folder/.hidden.json'])

    def test_publisher_media_extensions_rejected(self):
        for extension in ('.pdf', '.png', '.mp4', '.mat', '.stl'):
            with self.subTest(extension=extension), self.assertRaises(AssertionError):
                self.validate_names(['source' + extension])


if __name__ == '__main__':
    unittest.main()
