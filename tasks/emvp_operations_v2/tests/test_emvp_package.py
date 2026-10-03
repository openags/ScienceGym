#!/usr/bin/env python3
"""Independent cross-file contracts; static design checks, never a task runner."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import test_emvp_contract as base


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def distinct_refs(values, allowed, label, nonempty=False):
    demand(isinstance(values, list), f"{label}: list required")
    demand(all(isinstance(value, str) and value for value in values), f"{label}: string IDs required")
    demand(len(values) == len(set(values)), f"{label}: duplicate IDs")
    demand(not nonempty or bool(values), f"{label}: nonempty required")
    demand(not set(values) - set(allowed), f"{label}: dangling reference")
    return set(values)


def reachable(edges, before, after):
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(a, set()).add(b)
    frontier, seen = [before], set()
    while frontier:
        current = frontier.pop()
        if current == after:
            return True
        if current not in seen:
            seen.add(current)
            frontier.extend(adjacency.get(current, ()))
    return False


def validate_branch_graph(documents, require_controls=True):
    branches = documents['branches.json']
    families = base.index_records(branches['practical_families'], 'families')
    configurations = base.index_records(branches['configurations'], 'configurations')
    operations = base.index_records(documents['operations.json']['operations'], 'operations')
    materials = base.index_records(documents['material_cards.json']['materials'], 'materials')
    unknowns = base.index_records(documents['unknown_parameters.json']['unknowns'], 'unknowns')
    controls = base.index_records(documents['control_packages.json']['packages'], 'controls') if require_controls else None
    family_claims = []
    for family in families.values():
        members = distinct_refs(family['configuration_ids'], configurations, family['id'], nonempty=True)
        family_claims.extend(members)
        for member in members:
            demand(configurations[member]['family_id'] == family['id'], 'family membership mismatch')
    demand(set(family_claims) == set(configurations) and len(family_claims) == len(configurations), 'configuration missing or multiply assigned to a family')
    dependencies = documents['dependencies.json']
    edges = dependencies['edges']
    groups = base.index_records(dependencies['conditional_edges'], 'conditional edge groups')
    for edge in edges:
        demand(isinstance(edge, list) and len(edge) == 2, 'dependency edge must have two endpoints')
    base.validate_dag(operations, edges)
    all_edges = list(edges)
    for group in groups.values():
        distinct_refs(group['configuration_ids'], configurations, group['id'], nonempty=True)
        demand(bool(group['when']), 'conditional guard missing')
        demand(bool(group['edges']), 'conditional edges empty')
        for edge in group['edges']:
            demand(isinstance(edge, list) and len(edge) == 2, 'conditional edge must have two endpoints')
        base.validate_dag(operations, group['edges'])
        all_edges += group['edges']
    base.validate_dag(operations, all_edges)
    graphs = {}
    for configuration in configurations.values():
        cid = configuration['id']
        demand(configuration['family_id'] in families, f'{cid}: unknown family')
        selected = distinct_refs(configuration['operation_ids'], operations, cid, nonempty=True)
        selected_materials = distinct_refs(configuration['material_ids'], materials, cid, nonempty=True)
        gates = distinct_refs(configuration['required_unknowns'], unknowns, cid, nonempty=True)
        if controls is not None:
            distinct_refs(configuration['control_package_ids'], controls, cid)
        required = set()
        for identifier in selected:
            required.update(operations[identifier]['required_unknowns'])
        for identifier in selected_materials:
            required.update(materials[identifier]['required_unknowns'])
        demand(required <= gates, f'{cid}: missing operation or material gate')
        applicable = list(edges)
        for group in groups.values():
            if cid in group['configuration_ids']:
                applicable += group['edges']
        applicable = [edge for edge in applicable if set(edge) <= selected]
        base.validate_dag(selected, applicable)
        graphs[cid] = applicable
        demand({'O_PLAN', 'O_SETUP', 'O_SUMMARY', 'O_CLOSE'} <= selected, f'{cid}: lifecycle obligations missing')
        if 'O_DEPOSIT_NEG' in selected:
            demand({'O_MATERIAL_RELEASE', 'O_DOCK_EMB', 'O_INSPECT_EMBED', 'O_TRANSFER_ALIGN', 'O_EXPOSE', 'O_FLUSH', 'O_POSTCURE'} <= selected, f'{cid}: negative path obligation missing')
            demand('SACRIFICIAL' in selected_materials, f'{cid}: sacrificial ink missing')
            demand(reachable(applicable, 'O_FLUSH', 'O_POSTCURE'), f'{cid}: flush not ordered before postcure')
            demand(reachable(applicable, 'O_DEPOSIT_NEG', 'O_EXPOSE'), f'{cid}: deposition/transfer/exposure ordering missing')
        if 'O_DEPOSIT_POS' in selected:
            demand({'O_MATERIAL_RELEASE', 'O_DOCK_EMB', 'O_INSPECT_EMBED'} <= selected, f'{cid}: positive path obligation missing')
            demand(reachable(applicable, 'O_MATERIAL_RELEASE', 'O_DEPOSIT_POS'), f'{cid}: material qualification bypass')
            demand(reachable(applicable, 'O_DOCK_EMB', 'O_DEPOSIT_POS'), f'{cid}: docking bypass')
        if 'O_VAM_DIRECT' in selected:
            demand({'O_MATERIAL_RELEASE', 'O_VAM_SETUP', 'O_GEOMETRY', 'O_EXPOSE'} <= selected, f'{cid}: direct VAM obligation missing')
            demand(reachable(applicable, 'O_MATERIAL_RELEASE', 'O_VAM_DIRECT'), f'{cid}: direct material qualification bypass')
            demand(reachable(applicable, 'O_VAM_DIRECT', 'O_EXPOSE'), f'{cid}: direct exposure ordering missing')
        if 'O_SHORE_PROBE' in selected:
            demand({'O_EXPOSE', 'O_POSTCURE', 'O_SHORE_MOUNT'} <= selected and 'O_CAST' not in selected, 'hardness must retain printed route')
        if 'O_TENSILE' in selected:
            demand({'O_CAST', 'O_TENSILE_MOUNT'} <= selected and 'O_EXPOSE' not in selected, 'tensile must retain cast route')
    return graphs


class BranchPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {path.name: base.read_json(path) for path in base.ROOT.glob('*.json')}

    def test_all_family_configuration_operation_control_refs_and_gates(self):
        graphs = validate_branch_graph(self.documents)
        self.assertEqual(len(graphs), 19)
        self.assertEqual(len(self.documents['branches.json']['practical_families']), 5)

    def test_branch_corruptions_fail_closed(self):
        cases = [
            lambda d: d['branches.json']['configurations'][0]['operation_ids'].append('O_ABSENT'),
            lambda d: d['branches.json']['configurations'][0]['operation_ids'].append('O_PLAN'),
            lambda d: d['branches.json']['configurations'][0]['required_unknowns'].remove('U_CQ_EDAB'),
            lambda d: d['branches.json']['configurations'][0].update(family_id='F_ABSENT'),
            lambda d: d['branches.json']['practical_families'][0]['configuration_ids'].pop(),
            lambda d: d['dependencies.json']['edges'].append(['O_CLOSE', 'O_SUMMARY']),
            lambda d: d['dependencies.json']['edges'].append(['O_ABSENT', 'O_CLOSE']),
            lambda d: d['dependencies.json']['conditional_edges'][0]['configuration_ids'].append('ABSENT'),
            lambda d: d['dependencies.json']['conditional_edges'][0]['edges'].append(['O_EXPOSE', 'O_TRANSFER_ALIGN']),
            lambda d: d['branches.json']['configurations'][0]['control_package_ids'].append('C_ABSENT'),
        ]
        for index, mutate in enumerate(cases):
            documents = copy.deepcopy(self.documents)
            mutate(documents)
            with self.subTest(index=index), self.assertRaises(ValueError):
                validate_branch_graph(documents)

    def test_negative_flush_omission_and_order_corruptions_are_rejected(self):
        for omit in ['O_FLUSH', 'O_TRANSFER_ALIGN', 'O_MATERIAL_RELEASE']:
            documents = copy.deepcopy(self.documents)
            negative = next(c for c in documents['branches.json']['configurations'] if c['id'] == 'NEGATIVE_Y_COFLOW')
            negative['operation_ids'].remove(omit)
            with self.subTest(omit=omit), self.assertRaises(ValueError):
                validate_branch_graph(documents)
        documents = copy.deepcopy(self.documents)
        for group in documents['dependencies.json']['conditional_edges']:
            group['edges'] = [edge for edge in group['edges'] if edge != ['O_FLUSH', 'O_POSTCURE']]
        with self.assertRaises(ValueError):
            validate_branch_graph(documents)

    def test_cast_printed_operation_swap_is_rejected(self):
        for cid, wrong in [('SHORE_D_PAIR', 'O_CAST'), ('CAST_TENSILE_PAIR', 'O_EXPOSE')]:
            documents = copy.deepcopy(self.documents)
            branch = next(c for c in documents['branches.json']['configurations'] if c['id'] == cid)
            branch['operation_ids'].append(wrong)
            with self.subTest(configuration=cid), self.assertRaises(ValueError):
                validate_branch_graph(documents)


def validate_actor(document, configuration_ids):
    demand(set(document) == {'schema_version', 'visibility', 'goals', 'projection_rule'}, 'unapproved actor top-level field')
    demand(document['visibility'] == 'actor_public_selected_projection_only', 'actor visibility contract changed')
    goals = base.index_records(document['goals'], 'actor goals')
    demand(set(goals) == set(configuration_ids), 'actor goal/configuration mismatch')
    allowed = {'id', 'goal', 'initial_state', 'public_inputs', 'allowed_actions', 'deliverables', 'not_given'}
    for goal in goals.values():
        demand(set(goal) == allowed, 'unapproved actor goal field')
        for key in allowed:
            demand(bool(goal[key]), 'actor field empty')
        text = json.dumps(goal)
        demand(not base.re.search(r'\b(?:O_|OUT_|COV_)[A-Z0-9_]+', text), 'hidden reference identifier in actor view')
        demand(not base.re.search(r'(?:operations|dependencies|evaluator_reference|source_outcomes)\.json', text), 'hidden document in actor view')
        # Source measured outcomes are not future readings. Source procedure inputs
        # such as site dwell and load mass remain valid public information.
        for number in ['59.8', '64.7', '27.4', '4.9', '1.28', '248', '228', '119', '335', '0.23', '0.28']:
            demand(not base.re.search(r'(?<![\d.])' + base.re.escape(number) + r'(?![\d.])', text), 'source measured outcome leaked to actor view')
    return True


def validate_coverage(documents):
    locators = base.index_records(documents['provenance.json']['locators'])
    operations = base.index_records(documents['operations.json']['operations'])
    configurations = base.index_records(documents['branches.json']['configurations'])
    nonmanual = base.index_records(documents['nonmanual_scope.json']['records'])
    rows = base.index_records(documents['coverage_matrix.json']['coverage'])
    covered = set()
    for row in rows.values():
        refs = distinct_refs(row['source_refs'], locators, row['id'], nonempty=True)
        covered.update(refs)
        distinct_refs(row['operation_ids'], operations, row['id'])
        distinct_refs(row['configuration_ids'], configurations, row['id'])
        distinct_refs(row['nonmanual_ids'], nonmanual, row['id'])
        demand(row['scope'] and row['status'], 'empty coverage claim')
        if row['status'] == 'physical_source_covered_with_explicit_input_gates':
            demand(row['operation_ids'] and row['configuration_ids'], 'physical coverage lacks operations or configuration')
        else:
            demand(row['status'] == 'nonmanual_boundary_explicit', 'unknown coverage status')
            demand(row['nonmanual_ids'] or 'S_T1' in refs, 'nonmanual coverage lacks explicit boundary')
    demand(covered == set(locators), 'source locator omitted from coverage')
    return True


def validate_source_timings(document):
    rows = base.index_records(document['timing_rows'])
    expected = [
        ('2-Arm helix (1d)', 180, 109, 289), ('3Bellow (1i)', 180, 142, 322),
        ('2Bellow (1j)', 170, 144, 314), ('Thinker (2a)', 120, 151, 271),
        ('Skeleton sphere (2b)', 180, 162, 342), ('Hollow Cylinder (2e)', 9, 122, 131),
        ('Lattice (2g)', 180, 108, 288), ('Bending Bellow (2k)', 90, 155, 245),
        ('Cylindrical chip (3c)', 12, 121, 133), ('Flat chip (3g)', 8, 148, 156),
    ]
    demand(len(rows) == len(expected), 'timing source row omitted or added')
    for index, (label, embedded, volumetric, total) in enumerate(expected, 1):
        row = rows.get(f'TIME_{index}')
        demand(row is not None, 'timing source row identity absent')
        demand((row['source_row_label'], row['EMB3D_time_s'], row['TVAM_time_s'], row['total_print_time_s']) == (label, embedded, volumetric, total), 'source timing label, units or value drift')
        demand(row['EMB3D_time_s'] + row['TVAM_time_s'] == row['total_print_time_s'], 'component timing sum mismatch')
        demand(0 < row['total_print_time_s'] < 6 * 60, 'minutes-scale print duration drift')
        if index in (9, 10):
            demand(row['physical_chip_assignment'] == 'unresolved_source_row_panel_conflict', 'unresolved chip identity silently assigned')
    return True


class FullPackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {path.name: base.read_json(path) for path in base.ROOT.glob('*.json')}

    def test_actor_projection_has_no_reference_sequence_or_measured_outcomes(self):
        configurations = base.index_records(self.documents['branches.json']['configurations'])
        self.assertTrue(validate_actor(self.documents['agent_visible.json'], configurations))
        for mutate in [lambda d: d.update(expected_outcomes={'gelation': 59.8}),
                       lambda d: d['goals'][0].update(operation_ids=['O_PLAN']),
                       lambda d: d['goals'][0]['public_inputs'].append('source_outcomes.json'),
                       lambda d: d['goals'][0]['deliverables'].append('Expect gelation 59.8 seconds')]:
            document = copy.deepcopy(self.documents['agent_visible.json'])
            mutate(document)
            with self.assertRaises(ValueError):
                validate_actor(document, configurations)

    def test_evaluator_uses_independent_observations_and_separate_outcomes(self):
        evaluator = self.documents['evaluator_reference.json']
        self.assertEqual(evaluator['visibility'], 'evaluator_only_at_runtime')
        checks = base.index_records(evaluator['checks'])
        self.assertEqual(set(checks), {'SCOPE', 'SETUP', 'LINEAGE', 'FRAME', 'PROCESS', 'RECOVERY', 'CHARACTERIZATION', 'CONTROLS', 'ANALYSIS', 'CLOSE'})
        for check in checks.values():
            self.assertTrue(check['requirement'] and check['evidence'])
        independence = evaluator['independence']
        for key in ['required', 'not_sufficient', 'alternative_orders', 'fault_observability', 'source_outcomes']:
            self.assertTrue(independence[key])
        self.assertIn('never a reward or pass threshold', independence['source_outcomes'])
        self.assertIn('Actor narration', independence['not_sufficient'])
        self.assertEqual(set(evaluator['outcomes']), {'complete', 'partial_with_valid_blocker', 'safe_abort', 'failed'})
        self.assertIn('scientific comparison reported separately', evaluator['outcomes']['complete'])
        self.assertIn('no robot task runner', evaluator['runtime_status'])

    def test_control_packages_have_nested_slots_and_no_inferred_replication(self):
        packages = base.index_records(self.documents['control_packages.json']['packages'])
        references = {identifier for configuration in self.documents['branches.json']['configurations'] for identifier in configuration['control_package_ids']}
        self.assertEqual(references, set(packages))
        for package in packages.values():
            for key in ['comparison', 'outer_loop', 'inner_loop', 'matched_factors', 'required_outputs', 'source_refs', 'interpretation']:
                self.assertTrue(package[key], (package['id'], key))
            self.assertIsNone(package['replication']['independent_specimens_per_condition'])
            self.assertEqual(package['replication']['gate'], 'U_SCHEDULE')
        dispatch = self.documents['episode_input_contract.json']['condition_dispatch']['CONTROL_SINGLE_MATERIAL_CAGE']
        self.assertEqual(set(dispatch), {'Mat1-only', 'Mat2-only', 'combined-material'})
        self.assertIn('direct VAM', dispatch['Mat1-only'])
        self.assertIn('direct VAM', dispatch['Mat2-only'])
        self.assertIn('positive embedded', dispatch['combined-material'])
        self.assertIn('not independent specimens', self.documents['control_packages.json']['coverage_rule'])

    def test_every_source_locator_has_valid_coverage_or_nonmanual_boundary(self):
        self.assertTrue(validate_coverage(self.documents))
        for mutate in [lambda d: d['coverage_matrix.json']['coverage'].pop(),
                       lambda d: d['coverage_matrix.json']['coverage'][0]['operation_ids'].append('O_ABSENT'),
                       lambda d: d['coverage_matrix.json']['coverage'][0]['configuration_ids'].clear(),
                       lambda d: d['coverage_matrix.json']['coverage'][0]['nonmanual_ids'].append('N_ABSENT')]:
            documents = copy.deepcopy(self.documents)
            mutate(documents)
            with self.assertRaises(ValueError):
                validate_coverage(documents)

    def test_lineage_contract_has_complete_entity_event_raw_and_derived_fields(self):
        document = self.documents['lineage_contract.json']
        expected = {
            'entity_fields': {'id', 'type', 'parent_ids', 'material_id', 'batch_id', 'creation_event_id', 'state_version', 'location_id', 'status'},
            'event_fields': {'id', 'ordinal', 'timestamp', 'actor_or_instrument', 'object_ids', 'source_location', 'destination_location', 'condition_id', 'attempt_id', 'instrument_id', 'calibration_id', 'before_state', 'after_state', 'evidence_record_ids'},
            'raw_record_fields': {'id', 'specimen_id', 'batch_id', 'condition_id', 'attempt_id', 'instrument_id', 'calibration_id', 'acquisition_id', 'timestamp_basis', 'units', 'actual_settings', 'validity', 'immutable_payload_hash', 'source_event_ids'},
            'derived_record_fields': {'id', 'parent_raw_ids', 'model_or_reference_ids', 'processing_version', 'processing_parameters', 'units', 'selection_rule', 'validity', 'immutable_payload_hash'},
        }
        for field, required in expected.items():
            self.assertEqual(len(document[field]), len(set(document[field])))
            self.assertTrue(required <= set(document[field]), field)
        self.assertTrue({'stock_lot', 'prepared_batch', 'aliquot', 'printed_part', 'cast_specimen', 'section', 'raw_record', 'derived_record'} <= set(document['entity_types']))
        text = json.dumps(document).lower()
        for phrase in ['exactly one current location', 'acyclic', 'append-only', 'immutable', 'every retry', 'missing data are not zero', 'four hardness sites belong to one sample']:
            self.assertIn(phrase, text)

    def test_required_episode_inputs_cannot_be_empty_success(self):
        document = self.documents['episode_input_contract.json']
        required = {'selected_configuration_ids', 'finite_condition_schedule', 'specimen_allocation', 'installed_asset_receipts', 'resolved_unknowns', 'geometry_and_process_handoffs', 'raw_acquisition_interfaces', 'analysis_handoffs'}
        self.assertTrue(required <= set(document['required_fields']))
        self.assertTrue({'origin', 'source_or_qualification_receipt', 'version', 'scope'} <= set(document['resolution_fields']))
        self.assertIn('empty condition sets', document['required_input_behavior'])
        self.assertIn('block', document['required_input_behavior'].lower())
        self.assertIn('no-op', ' '.join(document['geometry_checks']))
        self.assertIn('Not supplied', document['scientific_backend'])

    def test_source_seconds_minutes_scale_and_chip_conflict_are_preserved(self):
        document = self.documents['source_outcomes.json']
        self.assertTrue(validate_source_timings(document))
        for mutate in [lambda d: d['timing_rows'][0].update(total_print_time_s=289*60),
                       lambda d: d['timing_rows'][8].update(source_row_label='Flat chip (3c)'),
                       lambda d: d['timing_rows'][8].update(physical_chip_assignment='cylindrical'),
                       lambda d: d['timing_rows'][9].update(TVAM_time_s=121),
                       lambda d: d['timing_rows'].pop()]:
            changed = copy.deepcopy(document)
            mutate(changed)
            with self.assertRaises(ValueError):
                validate_source_timings(changed)
        conflicts = base.index_records(self.documents['source_conflicts.json']['conflicts'])
        self.assertTrue({'CF_INITIATORS', 'CF_SOLVENT', 'CF_CHIP_TIMINGS', 'CF_PHOTO_CLOCK', 'CF_DISTANCE', 'CF_CONTROL_MATERIAL'} <= set(conflicts))
        self.assertIn('do not assign', conflicts['CF_CHIP_TIMINGS']['treatment'])

    def test_clock_needle_and_cast_printed_source_comparison_semantics(self):
        document = self.documents['source_outcomes.json']
        self.assertEqual(document['visibility'], 'evaluator_context_only_never_actor_or_reward')
        outcomes = base.index_records(document['outcomes'])
        gelation = outcomes['OUT_GELATION']['reported']
        self.assertEqual(gelation, {'Mat1_elapsed_from_measurement_start_s': 59.8, 'Mat2_elapsed_from_measurement_start_s': 64.7, 'LED_on_elapsed_s': 30})
        self.assertIn('not exposure durations', outcomes['OUT_GELATION']['context'])
        fine = outcomes['OUT_FINE_CHANNELS']['reported']
        self.assertEqual((fine['needle_diameter_um'], fine['measured_helical_diameter_um'], fine['measured_vertical_diameter_um']), (150, 119, 335))
        self.assertNotEqual(fine['needle_diameter_um'], fine['measured_helical_diameter_um'])
        self.assertIn('cast-specimen', outcomes['OUT_MECHANICS']['context'])
        self.assertIn('hardness uses printed', outcomes['OUT_MECHANICS']['context'])
        self.assertIn('never a per-print pass threshold', outcomes['OUT_DISTANCE']['context'])

    def test_export_boundary_is_text_only_and_actor_allowlist_is_explicit(self):
        document = self.documents['RELEASE_BOUNDARY.json']
        allow = '\n'.join(document['actor_allowlist'])
        deny = '\n'.join(document['actor_denylist'])
        for name in ['operations.json', 'dependencies.json', 'evaluator_reference.json', 'source_outcomes.json', 'tests/']:
            self.assertIn(name, deny)
            self.assertNotIn(name, allow)
        self.assertIn('fail closed', document['loader_requirement'])
        self.assertIn('does not implement', document['loader_requirement'])
        self.assertIs(self.documents['asset_needs.json']['publisher_assets_in_export'], False)
        self.assertIs(self.documents['provenance.json']['source_bytes_in_export'], False)
        for path in base.ROOT.rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or path.name in {'build_design.py', 'export_public.py'} or path.relative_to(base.ROOT).parts[0] == 'public_export':
                continue
            relative = path.relative_to(base.ROOT).as_posix()
            base.validate_export_member(relative)
            self.assertIn(path.suffix.lower(), {'.json', '.md', '.py', '.txt'}, relative)
            payload = path.read_bytes()
            self.assertFalse(payload.startswith((b'%PDF-', b'PK\x03\x04', b'\x89PNG', b'\xff\xd8\xff')), relative)
            payload.decode('utf-8')
            if path.parent == base.ROOT:
                self.assertNotRegex(payload.decode('utf-8'), r'/(?:workspace|home|tmp|root)/')

    def test_asset_and_nonmanual_contracts_are_external_not_implemented(self):
        assets = base.index_records(self.documents['asset_needs.json']['assets'])
        self.assertTrue({'A_INSTALLED', 'A_MODELS', 'A_JOBS', 'A_INTERFACES', 'A_RECIPES'} <= set(assets))
        nonmanual = base.index_records(self.documents['nonmanual_scope.json']['records'])
        self.assertTrue({'N_HARDWARE', 'N_PROJECTION', 'N_OPTICAL_SIMULATION', 'N_ANALYSIS', 'N_UNINSPECTED_ASSETS'} <= set(nonmanual))
        self.assertIn('excluded from physical task operations', nonmanual['N_OPTICAL_SIMULATION']['status'])
        self.assertEqual(self.documents['mock_contract.json']['scope'], 'Static bookkeeping tests only')
        forbidden = '\n'.join(self.documents['mock_contract.json']['forbidden']).lower()
        for phrase in ['generated physical measurements', 'physics solver', 'robot motion/controller']:
            self.assertIn(phrase, forbidden)


class ConditionRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {path.name: base.read_json(path) for path in base.ROOT.glob('*.json')}

    def test_all_cage_condition_routes_have_independent_dags_and_scoped_gates(self):
        configurations = base.index_records(self.documents['branches.json']['configurations'])
        cage = configurations['CONTROL_SINGLE_MATERIAL_CAGE']
        routes = cage['condition_routes']
        self.assertEqual({route['condition_id'] for route in routes}, {'Mat1-only', 'Mat2-only', 'combined-material'})
        self.assertEqual(len(routes), 3)
        for route in routes:
            documents = copy.deepcopy(self.documents)
            current = next(c for c in documents['branches.json']['configurations'] if c['id'] == cage['id'])
            current.update({key: route[key] for key in ['operation_ids', 'material_ids', 'required_unknowns']})
            validate_branch_graph(documents)
            selected = set(route['operation_ids'])
            if route['condition_id'] == 'combined-material':
                self.assertIn('O_DEPOSIT_POS', selected)
                self.assertNotIn('O_VAM_DIRECT', selected)
                self.assertEqual(set(route['material_ids']), {'MAT1', 'MAT2'})
            else:
                self.assertIn('O_VAM_DIRECT', selected)
                self.assertFalse({'O_DEPOSIT_POS', 'O_DOCK_EMB', 'O_TRANSFER_ALIGN'} & selected)
                self.assertNotIn('U_TOOLPATH', route['required_unknowns'])
                self.assertEqual(route['material_ids'], ['MAT1' if route['condition_id'] == 'Mat1-only' else 'MAT2'])
                if route['condition_id'] == 'Mat2-only':
                    self.assertNotIn('U_CQ_EDAB', route['required_unknowns'])
            bad = copy.deepcopy(documents)
            current = next(c for c in bad['branches.json']['configurations'] if c['id'] == cage['id'])
            current['required_unknowns'].remove('U_MATERIAL_QUAL')
            with self.assertRaises(ValueError):
                validate_branch_graph(bad)

    def test_declared_comparison_axes_and_state_loops_are_nonempty(self):
        packages = base.index_records(self.documents['control_packages.json']['packages'])
        expected = {
            'C_LOADING': [2, 4, 8, 12],
            'C_PURE_VAM_NEGATIVE': [2, 1.5, 1, 0.5, 0.3],
            'C_PURE_VAM_POSITIVE': [10, 5, 2.5],
            'C_SINGLE_MATERIAL': ['Mat1-only', 'Mat2-only', 'combined-material'],
        }
        unknowns = base.index_records(self.documents['unknown_parameters.json']['unknowns'])
        for identifier, values in expected.items():
            axes = base.index_records(packages[identifier]['condition_axes'])
            self.assertEqual(next(iter(axes.values()))['values'], values)
            for axis in axes.values():
                if axis['values'] is None:
                    self.assertIn(axis['gate'], unknowns)
                else:
                    self.assertTrue(axis['values'])
                    self.assertEqual(len(axis['values']), len(set(axis['values'])))
        for identifier in ['C_SPHERE_STATES', 'C_BELLOW_STATES']:
            states = packages[identifier]['ordered_states']
            self.assertEqual(len(states), 3)
            self.assertEqual(len(states), len(set(states)))

    def test_sensitive_recovery_contracts_preserve_actual_observations(self):
        operations = base.index_records(self.documents['operations.json']['operations'])
        expected = {
            'O_DEPOSIT_NEG': ['path history', 'needle'],
            'O_TRANSFER_ALIGN': ['mark/transform', 'block exposure'],
            'O_EXPOSE': ['stop light', 'exposure history', 'source time'],
            'O_EXTRACT': ['fragments', 'source identity'],
            'O_FLUSH': ['block postcure', 'failed clearance'],
            'O_PHOTORHEO': ['cured aliquot', 'separately allocated', 'elapsed'],
            'O_CT_SCAN': ['partial dataset', 'new attempt', 'absent raw'],
            'O_SHORE_PROBE': ['every site', 'independent n'],
            'O_TENSILE': ['fracture', 'new qualified specimen', 'failures'],
        }
        for identifier, phrases in expected.items():
            recovery = operations[identifier]['recovery'].lower()
            for phrase in phrases:
                self.assertIn(phrase, recovery, identifier)


class ReceiptBoundaryTests(unittest.TestCase):
    def test_source_audit_is_separate_and_byte_free(self):
        access = base.read_json(base.ROOT / 'source_access_audit.json')
        self.assertIs(access['public_export_source_bytes'], False)
        self.assertIs(access['public_export_publisher_pixels'], False)
        self.assertEqual(access['supplementary_figure_coverage'], list(range(1, 13)))
        audit = base.read_json(base.ROOT / 'independent_source_audit' / 'audit.json')
        findings = base.index_records(audit['findings'])
        self.assertEqual(len(findings), 28)
        self.assertIs(audit['review_basis']['no_new_downloads'], True)
        self.assertIs(audit['review_basis']['no_third_party_code_execution'], True)
        self.assertIs(audit['review_basis']['source_raw_data_or_cad_validated'], False)
        for finding in findings.values():
            self.assertTrue(finding['source_locator'] and finding['finding'] and finding['disposition'])

    def test_public_export_manifest_when_present_has_exact_files_and_hashes(self):
        path = base.ROOT / 'EXPORT_ALLOWLIST.json'
        if not path.exists():
            return  # This is the draft package; exporter has not run here.
        manifest = base.read_json(path)
        self.assertIs(manifest['source_bytes_included'], False)
        self.assertIs(manifest['publisher_pixels_included'], False)
        self.assertIs(manifest['runtime_actor_mount_allowed'], False)
        members = manifest['files']
        names = [row['path'] for row in members]
        self.assertEqual(len(names), len(set(names)))
        actual = {p.relative_to(base.ROOT).as_posix() for p in base.ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(actual, set(names) | {'EXPORT_ALLOWLIST.json'})
        for row in members:
            base.validate_export_member(row['path'])
            payload = (base.ROOT / row['path']).read_bytes()
            self.assertEqual(len(payload), row['bytes'])
            self.assertEqual(base.hashlib.sha256(payload).hexdigest(), row['sha256'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
