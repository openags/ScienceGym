"""Independent source equality and hostile-mutation checks for the woven view.

The expected mappings, counts and source pins below do not import adapter
constants. These tests inspect static records, never fixtures, hardware or solvers.
"""
import collections
import copy
import hashlib
import json
import re
import unittest
import xml.etree.ElementTree as ET

from test_semantics import ROOT, TASKS, builder, get, ids
import woven_adapters as woven

PIN = 'd62daed913e2ea04f0b7b0a0f20de9f6d42b7df6'
PACKAGE = 'woven_material_operations_v2'
ALIASES = {'unknown_parameters.json': 'unknowns',
           'evaluator_reference.json': 'acceptance',
           'lineage_contract.json': 'lineage'}
KINDS = {'design_only': 'design_only',
         'closed_qualified_service': 'closed_service',
         'external_numerical_design': 'numerical',
         'conflict_hold': 'conflict_hold'}
ASSET_NAMES = {'README.md', 'evidence/overview.png',
               'evidence/measurement.png', 'evidence/package_handling.png'}


def package(): return TASKS / PACKAGE

def raw(filename): return json.loads((package() / filename).read_text())

def index(records): return {r['id']: r for r in records}

def canonical(value):
    # JSON equality is deliberately stricter than Python's False == 0 == 0.0.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def pointer(document, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class WovenBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.family = get('woven')

    def test_source_and_inspection_counts_are_separate(self):
        f = self.family
        self.assertEqual((len(f['operations']), len(f['routes']), len(f['source_files'])), (48, 25, 30))
        self.assertEqual(len(index(f['operations'])), 48)
        self.assertEqual(len(index(f['routes'])), 25)
        self.assertEqual(len(f['context']['branches']['branches']), 24)
        self.assertEqual(collections.Counter(r['route_kind'] for r in f['routes']),
                         {'design_only': 3, 'closed_service': 13, 'numerical': 7,
                          'conflict_hold': 1, 'qualification_hold': 1})
        for key, count in {'source_branches': 24, 'synthetic_configurations': 96,
                           'scene_groups': 11, 'symbolic_anchors': 43,
                           'unresolved_input_groups': 12, 'control_records': 8}.items():
            self.assertEqual(f['summary_counts'][key], count, key)
        self.assertNotIn('WHOLE_PAPER_PRACTICAL', index(f['routes']))

    def test_membership_is_exact_reverse_index_without_chronology_or_expansion(self):
        f = self.family; routes = index(f['routes'])
        for branch in f['context']['branches']['branches']:
            r = routes[branch['id']]
            expected = [o['id'] for o in f['context']['operations']['operations']
                        if branch['id'] in o['branch_ids']]
            self.assertEqual(ids(r['nodes']), expected, branch['id'])
            self.assertEqual(len(expected), len(set(expected)))
            self.assertEqual(r['route_kind'], KINDS[branch['execution_class']])
            self.assertEqual(canonical(r['detail']), canonical(branch))
        self.assertEqual({o['id'] for o in f['operations']},
                         {oid for r in f['routes'] for oid in ids(r['nodes'])})
        for r in f['routes']:
            self.assertEqual(r['metadata_only'], not bool(ids(r['nodes'])))
            for node, _ in builder.walk(r['nodes']):
                self.assertNotEqual(node['type'], 'loop')
                if node['type'] != 'op': self.assertIs(node['ordered'], False)

    def test_default_qualification_hold_is_not_a_new_scientific_branch(self):
        f = self.family; hold = index(f['routes'])['QUALIFICATION_HOLD']
        self.assertEqual(f['default_route'], 'QUALIFICATION_HOLD')
        self.assertEqual(hold['route_kind'], 'qualification_hold')
        self.assertEqual(ids(hold['nodes']), ['HOLD_QUALIFICATION'])
        self.assertEqual((hold['source_file'], hold['source_pointer']), ('lifecycle_contract.json', ''))
        self.assertEqual(canonical(hold['detail']), canonical(f['context']['lifecycle_contract']))
        self.assertNotIn('QUALIFICATION_HOLD', index(f['context']['branches']['branches']))
        self.assertEqual(f['context']['episode_input_contract']['default'], 'QUALIFICATION_HOLD')
        self.assertEqual(f['context']['lifecycle_contract']['default'], 'QUALIFICATION_HOLD')

    def test_operation_display_retains_complete_records_without_invented_commands(self):
        f = self.family
        originals = f['context']['operations']['operations']
        self.assertEqual(canonical([o['detail'] for o in f['operations']]), canonical(originals))
        for i, (op, original) in enumerate(zip(f['operations'], originals)):
            self.assertEqual((op['source_file'], op['source_pointer']), ('operations.json', '/operations/' + str(i)))
            for target, source in [('objects', 'asset_ids'), ('pre', 'precondition'),
                                   ('acceptance', 'required_output'), ('recovery', 'failure'),
                                   ('sources', 'source_evidence_ids'), ('provenance', 'origin')]:
                self.assertEqual(canonical(op[target]), canonical(original[source]), (op['id'], target))
            self.assertIsNone(op['loop'])
            self.assertEqual(op['unknowns'], [])
            self.assertEqual(len(op['actions']), 1)
            self.assertIn('No actions field supplied', op['actions'][0])
            self.assertIn('No per-operation station field supplied', op['stage'])
            self.assertIn('No post-state field supplied', op['post'])
            self.assertIs(op['detail']['device_command_implemented'], False)
            self.assertIs(op['detail']['physical_execution_authority'], False)

    def test_all_53_evidence_entries_resolve_without_asset_anchor_conflation(self):
        f = self.family
        expected = index(f['context']['evidence_map']['entries'])
        self.assertEqual(len(expected), 53)
        self.assertEqual(canonical(f['evidence']), canonical(expected))
        for record in f['operations']:
            self.assertTrue(set(record['sources']) <= set(expected), record['id'])
        for record in f['context']['branches']['branches'] + f['context']['source_conflicts']['items']:
            self.assertTrue(set(record['source_evidence_ids']) <= set(expected), record['id'])

    def test_all_11_groups_and_43_scoped_anchors_keep_static_qualification_boundary(self):
        c = self.family['context']
        stations = index(c['station_contracts']['services'])
        assets = {a['asset_id']: a for a in c['asset_binding_plan']['scene_assets']}
        self.assertEqual(set(stations), set(assets)); self.assertEqual(len(stations), 11)
        anchors = {(sid, anchor) for sid, station in stations.items() for anchor in station['anchors']}
        self.assertEqual(len(anchors), 43)
        self.assertEqual(sum(len(s['anchors']) for s in stations.values()), 43)
        bound = set()
        for sid, service in stations.items():
            self.assertIs(service['closed'], True)
            self.assertIs(service['qualification_required'], True)
            self.assertIs(service['hardware_driver'], False)
            self.assertIs(service['request_is_observation'], False)
            self.assertEqual(service['anchors'], assets[sid]['required_anchor_ids'])
            self.assertIs(assets[sid]['physical_geometry_validated'], False)
            self.assertIs(assets[sid]['asset_available'], True)
            bound.update(assets[sid]['bind_operation_ids'])
        self.assertEqual(bound, set(index(self.family['operations'])))
        for op in self.family['operations']:
            for asset_id in op['objects']:
                self.assertIn(op['id'], assets[asset_id]['bind_operation_ids'])
        self.assertEqual(c['asset_binding_plan']['binding_status'], 'STATIC_SCENE_BOUND')
        self.assertIn('no physical qualification or execution', c['asset_binding_plan']['asset_scope'])

    def test_96_synthetic_configurations_never_become_executions_or_specimens(self):
        c = self.family['context']; status = c['STATUS']; verification = c['VERIFICATION']
        self.assertEqual(status['synthetic_configuration_count'], 96)
        self.assertEqual(verification['synthetic_configurations'], 96)
        self.assertIs(status['whole_paper_design_accounted_for'], True)
        self.assertIs(status['full_paper_design_eligible'], True)
        for field in ('whole_paper_execution_complete', 'scientific_reproduction_run',
                      'full_paper_execution_eligible', 'whole_paper_complete',
                      'physical_geometry_validated'):
            self.assertIs(status[field], False, field)
        self.assertEqual(status['physical_readiness'], 'CLOSED_UNQUALIFIED_SERVICES_ONLY')
        for field in ('hardware_tests_run', 'numerical_scientific_solver_run',
                      'source_data_reproduction_run', 'physical_geometry_validated'):
            self.assertIs(verification[field], False, field)
        for branch in c['branches']['branches']:
            self.assertIs(branch['design_covered'], True)
            self.assertIs(branch['physical_executed'], False)
            self.assertIs(branch['numerical_executed'], False)
            self.assertNotIn('independent_specimen_count', branch)
        dependencies = self.family['dependencies']
        self.assertIn('No universal operation DAG supplied', dependencies['rule'])
        self.assertEqual(set(dependencies), {'rule', 'preparation_routes', 'lifecycle_contract', 'transport_routes'})
        for name in ('preparation_routes', 'lifecycle_contract', 'transport_routes'):
            self.assertEqual(canonical(dependencies[name]), canonical(c[name]))

    def test_scoped_conflicts_remain_unresolved_and_physical_model_patterns_differ(self):
        c = self.family['context']; conflicts = index(c['source_conflicts']['items'])
        self.assertEqual(len(conflicts), 11)
        self.assertTrue(all(x['status'] == 'UNRESOLVED_OR_SCOPE_CONTROLLED' for x in conflicts.values()))
        self.assertEqual(conflicts['TETRA_STRAND_COUNT']['required_handling'], 'Hold only tetra geometry; BCC/cubic unaffected')
        self.assertIn('No silent correction', conflicts['CUBIC_MODULAR_RULE']['required_handling'])
        self.assertIn('Never substitute numerical map/receipt', conflicts['PATTERN_PARAMETER_MAP']['required_handling'])
        branches = index(c['branches']['branches'])
        self.assertEqual(branches['TETRAKAIDECAHEDRON_HOLD']['execution_class'], 'conflict_hold')
        for bid in ('TENSION_BCC', 'TENSION_CUBIC'):
            self.assertEqual(branches[bid]['execution_class'], 'closed_qualified_service')
        example = c['source_outcomes']['source_reported_branch_examples']
        self.assertEqual((example['physical_high_turn'], example['numerical_high_turn']), ('8/3', '7/3'))
        self.assertEqual(example['physical_pattern_tessellations_conflicted'], [[10, 5, 2], [10, 2, 5]])
        self.assertIs(example['contexts_not_interchangeable'], True)

    def test_prepared_ancestry_and_partial_order_do_not_invent_fabrication_credit(self):
        routes = index(self.family['context']['preparation_routes']['routes'])
        self.assertEqual(len(routes), 3)
        self.assertIs(routes['PREPARED']['preparation_credit'], False)
        self.assertIn('no fabrication credit', routes['PREPARED']['note'])
        self.assertIn('no physical fabrication', routes['FULL']['note'])
        support = routes['FULL_SUPPORT']
        self.assertIs(support['requires_external_order_card'], True)
        self.assertEqual(support['source_order_between_plasma_and_coating'], 'unspecified')
        self.assertNotIn('sequence', support)
        self.assertNotIn(['coating_receipt', 'support_removal_receipt'], support['partial_order'])
        self.assertNotIn(['support_removal_receipt', 'coating_receipt'], support['partial_order'])
        self.assertIn(['cpd_receipt', 'support_removal_receipt'], support['partial_order'])
        self.assertIn(['cpd_receipt', 'coating_receipt'], support['partial_order'])

    def test_controls_lineage_safe_release_and_actor_claims_are_independent(self):
        c = self.family['context']; controls = c['control_packages']; lineage = c['lineage']
        self.assertEqual(len(controls['cards']), 8)
        self.assertIs(controls['source_reported_values_are_not_executable_controls'], True)
        self.assertIs(controls['current_revision_required'], True)
        self.assertEqual(len(c['unknowns']['required_input_gates']), 12)
        self.assertIs(c['unknowns']['missing_inputs_do_not_remove_design_routes'], True)
        self.assertEqual(len(lineage['required_keys']), 15)
        self.assertIs(lineage['context_is_evaluator_owned'], True)
        for key in ('sample_id', 'attempt_id', 'stage_revision', 'mount_revision',
                    'calibration_revision', 'control_revision', 'qualification_revision', 'raw_hash'):
            self.assertIn(key, lineage['required_keys'])
        for invariant in ('Remount invalidates calibration/control/data', 'Damage prevents reuse',
                          'Held attempt cannot resume using stale evidence'):
            self.assertIn(invariant, lineage['invalidation'])
        self.assertIn('Verified safe release before undock', c['lifecycle_contract']['stage_principles'])
        self.assertIn('Unknown isolation contained; damage quarantined', c['lifecycle_contract']['stage_principles'])
        self.assertEqual(c['lifecycle_contract']['terminal_states'],
                         ['CLOSED_SYNTHETIC', 'QUARANTINED_SYNTHETIC', 'HELD_CONTAINED'])
        self.assertIs(c['lifecycle_contract']['physical_execution'], False)
        self.assertEqual(c['episode_input_contract']['actor_fields'], ['event_id', 'operation_id', 'evidence_id'])
        self.assertIs(c['episode_input_contract']['service_requests_are_not_physical_actuation'], True)
        for field in ('measurement', 'success', 'safe', 'qualification', 'raw_hash', 'source_outcome'):
            self.assertIn(field, c['episode_input_contract']['actor_cannot_supply'])

    def test_source_outcomes_arithmetic_and_access_gaps_are_not_validation(self):
        c = self.family['context']; outcomes = c['source_outcomes']
        self.assertIs(outcomes['completion_thresholds'], False)
        self.assertIs(outcomes['not_executed'], True)
        self.assertIs(outcomes['source_reported_process_context']['nonexecuting_reference_only'], True)
        self.assertIs(outcomes['source_reported_process_context']['safety_or_executable_control_card'], False)
        self.assertIs(c['acceptance']['source_outcomes_are_reward_targets'], False)
        self.assertIs(c['acceptance']['synthetic_fixture_registry_is_production_authentication'], False)
        self.assertIn('no constitutive/deformation solver', c['analysis_contracts']['implemented_scope'])
        definitions = c['analysis_contracts']['definitions']
        self.assertNotEqual(definitions['loading_work_density_J_m3'], definitions['cycle_loss_density_J_m3'])
        self.assertIn('Signed closed-cycle', definitions['cycle_loss_density_J_m3'])
        audit = c['source_access_audit']
        self.assertIn('five videos not played', audit['video_scope'])
        self.assertIn('raw workbook values not inspected/imported/used', audit['source_data_scope'])
        self.assertIn('not read', audit['peer_review_scope'])
        self.assertIs(c['mock_contract']['hardware_network_and_solver_access'], False)

    def test_read_only_visibility_never_becomes_actor_projection(self):
        f = self.family; c = f['context']
        self.assertEqual(f['visibility'], 'author_evaluator_reference_only')
        self.assertIs(f['actor_projection_implemented'], False)
        self.assertEqual(f['family_scope'], 'paper_level_design')
        for field in ('can_declare_measurement', 'can_declare_service_qualification',
                      'can_supply_physical_observation', 'physical_implementation', 'source_outcomes_exposed'):
            self.assertIs(c['agent_visible'][field], False)
        self.assertIs(c['agent_visible']['scene_assets_are_static_placeholders'], True)
        self.assertIs(c['RELEASE_BOUNDARY']['whole_paper_execution_complete'], False)
        self.assertEqual(c['RELEASE_BOUNDARY']['numerical_execution'], 'NONE')

    def test_json_javascript_docs_and_immutable_task_and_asset_links(self):
        f = self.family
        js = (ROOT / 'data' / 'woven.js').read_text().split('["woven"]=', 1)[1].rsplit(';', 1)[0]
        self.assertEqual(canonical(json.loads(js)), canonical(json.loads((ROOT / 'data' / 'woven.json').read_text())))
        self.assertEqual(f['source_commit'], PIN)
        folder = f'https://github.com/openags/ScienceGym/blob/{PIN}/tasks/{PACKAGE}/'
        self.assertEqual(f['source_folder'], folder)
        for name, record in f['source_files'].items():
            self.assertEqual(record['url'], folder + name)
            self.assertRegex(record['sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual({a['path'].split('/', 2)[2] for a in f['asset_links']}, ASSET_NAMES)
        for asset in f['asset_links']:
            self.assertEqual(asset['url'], f'https://github.com/openags/ScienceGym/blob/{PIN}/' + asset['path'])
            self.assertRegex(asset['sha256'], r'^[0-9a-f]{64}$')
        md = (ROOT / 'docs' / 'woven.md').read_text()
        self.assertIn(f['family_scope_label'], md)
        self.assertIn(f['source_warnings'], md)
        for r in f['routes']: self.assertIn('## ' + r['id'] + ' ', md)
        for asset in f['asset_links']: self.assertIn(asset['url'], md)

    def test_all_25_svg_variants_preserve_exact_rows_without_arrows(self):
        f = self.family
        for r in f['routes']:
            candidate = copy.deepcopy(f); candidate['default_route'] = r['id']
            svg = builder.svg(candidate); root = ET.fromstring(svg)
            self.assertNotIn('marker-end=', svg)
            self.assertIn('0 executed tasks', svg)
            self.assertIn('24 scientific design routes + 1 qualification-hold view', svg)
            self.assertIn('no physical or numerical execution', svg)
            texts = [node.text or '' for node in root.findall('.//{http://www.w3.org/2000/svg}text')]
            badges = [text.split(' · ', 1)[1].split(' · ', 1)[0] for text in texts if re.match(r'^\d+ · ', text)]
            self.assertEqual([x for x in badges if x in index(f['operations'])], ids(r['nodes']), r['id'])


@unittest.skipUnless(TASKS, 'SCIENCEGYM_TASKS not set; exact source equality and mutations not run')
class WovenSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = get('woven')
        cls.adapted = woven.adapt_woven(package())

    def test_all_30_source_json_documents_are_type_exact_and_hashed(self):
        f = self.family
        names = {p.relative_to(package()).as_posix() for p in package().rglob('*.json')}
        self.assertEqual(len(names), 30)
        self.assertEqual(set(f['source_files']), names)
        self.assertEqual(set(f['context']), {ALIASES.get(name, name.removesuffix('.json')) for name in names})
        for name in sorted(names):
            self.assertEqual(canonical(f['context'][ALIASES.get(name, name.removesuffix('.json'))]), canonical(raw(name)), name)
            self.assertEqual(f['source_files'][name]['sha256'], hashlib.sha256((package() / name).read_bytes()).hexdigest(), name)

    def test_48_full_operation_records_and_24_source_routes_equal_original_json(self):
        f = self.family
        original = raw('operations.json')['operations']
        self.assertEqual(canonical([op['detail'] for op in f['operations']]), canonical(original))
        routes = [r for r in f['routes'] if r['source_file'] == 'branches.json']
        self.assertEqual(canonical([r['detail'] for r in routes]), canonical(raw('branches.json')['branches']))
        for r in f['routes']:
            self.assertEqual(canonical(r['detail']), canonical(pointer(raw(r['source_file']), r['source_pointer'])), r['id'])
            for node, _ in builder.walk(r['nodes']):
                if node['type'] == 'condition':
                    meta = node['meta']
                    self.assertEqual(canonical(meta['source_contract']), canonical(pointer(raw(meta['source_file']), meta['source_pointer'])))

    def test_all_asset_links_equal_existing_pinned_source_hashes(self):
        f = self.family
        directory = TASKS.parent / 'assets' / 'woven_scene_assets_v1'
        expected = {'README.md'} | {p.relative_to(directory).as_posix() for p in (directory / 'evidence').glob('*.png')}
        self.assertEqual(expected, ASSET_NAMES)
        for asset in f['asset_links']:
            path = TASKS.parent / asset['path']
            self.assertTrue(path.is_file())
            self.assertEqual(asset['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(asset['url'], f'https://github.com/openags/ScienceGym/blob/{PIN}/' + asset['path'])

    def reject(self, mutation):
        candidate = copy.deepcopy(self.adapted)
        mutation(candidate)
        with self.assertRaises(ValueError): woven.validate_projection(candidate, package())

    def check_mutations(self, mutations):
        for name, mutation in mutations.items():
            with self.subTest(mutation=name): self.reject(mutation)

    def test_reject_record_loss_invented_actions_and_ordered_inventories(self):
        self.check_mutations({
            'operation_loss': lambda f: f['operations'].pop(),
            'source_record_loss': lambda f: f['operations'][0]['detail'].pop('failure'),
            'source_record_extra': lambda f: f['operations'][0]['detail'].__setitem__('safe', True),
            'invented_command': lambda f: f['operations'][0].__setitem__('actions', ['activate apparatus']),
            'invented_station': lambda f: f['operations'][0].__setitem__('stage', 'A_TENSION_FIXTURE'),
            'postcondition_from_required_output': lambda f: f['operations'][0].__setitem__('post', f['operations'][0]['acceptance']),
            'source_branch_loss': lambda f: f['routes'].pop(0),
            'member_loss': lambda f: f['routes'][0]['nodes'][0]['children'].pop(),
            'member_repetition': lambda f: f['routes'][0]['nodes'][0]['children'].append(f['routes'][0]['nodes'][0]['children'][0]),
            'invented_chronology': lambda f: f['routes'][0]['nodes'][0].__setitem__('ordered', True),
            'source_sequence_changed': lambda f: f['routes'][0]['detail']['design_sequence'].reverse(),
            'expanded_cycle': lambda f: f['routes'][0]['nodes'][0].__setitem__('type', 'loop'),
            'source_pointer_changed': lambda f: f['operations'][0].__setitem__('source_pointer', '/operations/1'),
            'evidence_loss': lambda f: f['evidence'].pop(next(iter(f['evidence']))),
        })

    def test_reject_every_source_context_document_loss(self):
        for name in self.adapted['context']:
            with self.subTest(document=name): self.reject(lambda f: f['context'].pop(name))

    def test_reject_execution_visibility_numeric_type_and_count_promotions(self):
        self.check_mutations({
            'actor_projection': lambda f: f.__setitem__('actor_projection_implemented', True),
            'actor_visibility': lambda f: f.__setitem__('visibility', 'actor'),
            'physical_execution': lambda f: f['context']['STATUS'].__setitem__('whole_paper_execution_complete', True),
            'numerical_execution': lambda f: f['context']['branches']['branches'][-1].__setitem__('numerical_executed', True),
            'solver_execution': lambda f: f['context']['VERIFICATION'].__setitem__('numerical_scientific_solver_run', True),
            'physical_geometry': lambda f: f['context']['STATUS'].__setitem__('physical_geometry_validated', True),
            'synthetic_count': lambda f: f['summary_counts'].__setitem__('synthetic_configurations', 95),
            'source_route_count': lambda f: f['summary_counts'].__setitem__('source_branches', 25),
            'physical_from_numerical': lambda f: index(f['routes'])['LINEAR_HOMOGENIZATION'].__setitem__('route_kind', 'closed_service'),
            'boolean_to_zero': lambda f: f['context']['STATUS'].__setitem__('whole_paper_execution_complete', 0),
            'integer_to_float': lambda f: f['context']['STATUS'].__setitem__('synthetic_configuration_count', 96.0),
            'boolean_to_one': lambda f: f['context']['STATUS'].__setitem__('whole_paper_design_accounted_for', 1),
            'service_command_flag': lambda f: f['operations'][0]['detail'].__setitem__('device_command_implemented', True),
        })

    def test_reject_hold_resolution_claims_outcome_targets_and_replaced_controls(self):
        self.check_mutations({
            'qualification_default_removed': lambda f: f.__setitem__('default_route', 'TENSION_BCC'),
            'activation_in_default_hold': lambda f: index(f['routes'])['QUALIFICATION_HOLD']['nodes'][0]['children'].append('REQUEST_PRINT'),
            'scoped_hold_broadened': lambda f: index(f['context']['source_conflicts']['items'])['TETRA_STRAND_COUNT'].__setitem__('required_handling', 'Hold all physical branches'),
            'tetra_conflict_resolved': lambda f: index(f['context']['source_conflicts']['items'])['TETRA_STRAND_COUNT'].__setitem__('status', 'RESOLVED'),
            'modular_rule_repaired': lambda f: index(f['context']['source_conflicts']['items'])['CUBIC_MODULAR_RULE'].__setitem__('required_handling', 'Use corrected formula'),
            'physical_pattern_replaced': lambda f: f['context']['source_outcomes']['source_reported_branch_examples'].__setitem__('physical_high_turn', '7/3'),
            'outcome_threshold': lambda f: f['context']['source_outcomes'].__setitem__('completion_thresholds', True),
            'outcome_reward': lambda f: f['context']['acceptance'].__setitem__('source_outcomes_are_reward_targets', True),
            'controls_replaced': lambda f: f['context']['control_packages'].__setitem__('cards', []),
            'source_controls_enabled': lambda f: f['context']['control_packages'].__setitem__('source_reported_values_are_not_executable_controls', False),
            'unknowns_removed': lambda f: f['context']['unknowns'].__setitem__('required_input_gates', []),
            'claims_accepted': lambda f: f['context']['episode_input_contract'].__setitem__('actor_cannot_supply', []),
            'measurement_from_request': lambda f: f['context']['station_contracts']['services'][0].__setitem__('request_is_observation', True),
        })

    def test_reject_stale_lineage_invented_order_and_qualified_scene_claims(self):
        self.check_mutations({
            'lineage_identity_loss': lambda f: f['context']['lineage']['required_keys'].remove('sample_id'),
            'lineage_revision_loss': lambda f: f['context']['lineage']['required_keys'].remove('mount_revision'),
            'lineage_invalidation_loss': lambda f: f['context']['lineage'].__setitem__('invalidation', []),
            'prepared_fabrication_credit': lambda f: index(f['context']['preparation_routes']['routes'])['PREPARED'].__setitem__('preparation_credit', True),
            'source_order_invented': lambda f: index(f['context']['preparation_routes']['routes'])['FULL_SUPPORT'].__setitem__('source_order_between_plasma_and_coating', 'plasma_first'),
            'dependency_order_invented': lambda f: f['dependencies']['preparation_routes']['routes'][1].__setitem__('source_order_between_plasma_and_coating', 'plasma_first'),
            'external_order_bypassed': lambda f: index(f['context']['preparation_routes']['routes'])['FULL_SUPPORT'].__setitem__('requires_external_order_card', False),
            'safe_release_removed': lambda f: f['context']['lifecycle_contract']['stage_principles'].remove('Verified safe release before undock'),
            'scene_qualified': lambda f: f['context']['asset_binding_plan']['scene_assets'][0].__setitem__('physical_geometry_validated', True),
            'station_driver': lambda f: f['context']['station_contracts']['services'][0].__setitem__('hardware_driver', True),
            'service_qualification_bypassed': lambda f: f['context']['station_contracts']['services'][0].__setitem__('qualification_required', False),
            'anchor_loss': lambda f: f['context']['station_contracts']['services'][0]['anchors'].pop(),
            'group_loss': lambda f: f['context']['asset_binding_plan']['scene_assets'].pop(),
            'unread_workbook_promoted': lambda f: f['context']['source_access_audit'].__setitem__('source_data_scope', 'All raw workbook values read and reproduced'),
        })

    def test_reject_changed_pins_hashes_and_asset_links(self):
        self.check_mutations({
            'mutable_commit': lambda f: f.__setitem__('source_commit', 'main'),
            'mutable_folder': lambda f: f.__setitem__('source_folder', f['source_folder'].replace(PIN, 'main')),
            'task_url_changed': lambda f: f['source_files']['operations.json'].__setitem__('url', 'https://example.org/source'),
            'task_hash_changed': lambda f: f['source_files']['operations.json'].__setitem__('sha256', '0' * 64),
            'task_file_loss': lambda f: f['source_files'].pop('review/INDEPENDENT_REVIEW.json'),
            'asset_url_changed': lambda f: f['asset_links'][0].__setitem__('url', f['asset_links'][0]['url'].replace(PIN, 'main')),
            'asset_hash_changed': lambda f: f['asset_links'][0].__setitem__('sha256', '0' * 64),
            'asset_path_changed': lambda f: f['asset_links'][0].__setitem__('path', 'assets/other/README.md'),
            'asset_loss': lambda f: f['asset_links'].pop(),
        })


if __name__ == '__main__': unittest.main()
