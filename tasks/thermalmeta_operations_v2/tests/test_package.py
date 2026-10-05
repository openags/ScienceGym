import json
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(n):return json.loads((ROOT/n).read_text())
class PackageTests(unittest.TestCase):
    def test_twenty_stages_exact(self):self.assertEqual([x['id'] for x in read('operations.json')['stages']],['P%02d'%i for i in range(1,21)])
    def test_all_required_receipts(self):self.assertTrue(all(x['required_receipt_fields'] for x in read('operations.json')['stages']))
    def test_no_commands(self):self.assertTrue(all(x['commands_enabled'] is False for x in read('operations.json')['stages']))
    def test_all_stations_defined(self):
        ids={x['id'] for x in read('station_contracts.json')['stations']};self.assertTrue(all(x['station_id'] in ids for x in read('operations.json')['stages']))
    def test_all_stages_bound(self):
        b={x['stage_id']:x for x in read('scene_binding_contract.json')['stage_bindings']}
        for s in read('operations.json')['stages']:
            self.assertEqual(s['scene_anchor_id'],b[s['id']]['anchor_id']);self.assertEqual(s['scene_asset_ids'],b[s['id']]['asset_ids'])
    def test_anchors_exist(self):
        c=read('scene_binding_contract.json');ids={x['anchor_id'] for x in c['anchors']};self.assertTrue(all(x['anchor_id'] in ids for x in c['stage_bindings']))
    def test_assets_exist(self):
        c=read('scene_binding_contract.json');ids={x['asset_id'] for x in c['assets']};self.assertTrue(all(set(x['asset_ids'])<=ids for x in c['stage_bindings']))
    def test_six_condition_ids_exact(self):self.assertEqual(set(read('task.json')['source_condition_ids']),{x['condition_id'] for x in read('scene_binding_contract.json')['condition_views']})
    def test_sample_binding_exact(self):
        samples={x['sample_family_id']:x for x in read('sample_contract.json')['families']}
        for x in read('scene_binding_contract.json')['condition_views']:
            self.assertEqual(x['specimen_id'],samples[x['sample_family_id']]['specimen_id']);self.assertEqual(x['design_id'],samples[x['sample_family_id']]['design_id']);self.assertEqual(x['design_revision'],samples[x['sample_family_id']]['design_revision'])
    def test_profile_number_mapping_authored(self):self.assertTrue(all(x.get('profile_number_to_orientation_status')=='authored_visual_selector_not_source_verified' for x in read('scene_binding_contract.json')['condition_views']))
    def test_rotator_transverse(self):self.assertTrue(all(x['profile_direction']=='transverse_to_applied_reference' for x in read('scene_binding_contract.json')['condition_views'] if x['sample_family_id']=='ROTATOR45'))
    def test_other_profiles_parallel(self):self.assertTrue(all(x['profile_direction']=='parallel_to_applied_reference' for x in read('scene_binding_contract.json')['condition_views'] if x['sample_family_id']!='ROTATOR45'))
    def test_no_physical_claim(self):
        t=read('task.json');self.assertFalse(t['physical_execution_enabled']);self.assertFalse(t['numerical_physics_enabled']);self.assertEqual(t['actual_experiments_performed'],0)
    def test_all_twelve_branches(self):self.assertEqual({x['id'] for x in read('branches.json')['families']},{'B%02d'%i for i in range(1,13)})
    def test_children_registered(self):
        b=read('branches.json');self.assertEqual(len(b['child_branches']),12);self.assertTrue(all(x['id'] in b['execution_status'] for x in b['child_branches']))
    def test_all_numerical_unexecuted(self):self.assertTrue(all('unexecuted' in x for x in read('branches.json')['execution_status'].values()))
    def test_metric_equation_feature_flux_holds(self):
        c={x['id']:x for x in read('source_conflicts.json')};self.assertTrue(all(c[x]['resolved'] is False for x in ('C01','C02','C03','C05')))
    def test_all_source_conflicts_open(self):self.assertTrue(all(x['resolved'] is False for x in read('source_conflicts.json')))
    def test_unknowns_not_invented(self):
        u=read('unknown_inputs.json');self.assertEqual(len(u),13);self.assertTrue(all(x['may_be_invented'] is False for x in u))
    def test_all_powered_failures_enter_release(self):
        edges=read('operations.json')['failure_edges'];self.assertTrue(all(any(e['from']==s and e['to']=='P15' for e in edges) for s in ('P11','P12','P13','P14')))
    def test_release_hold_present(self):self.assertEqual(read('lifecycle_contract.json')['release_failure_target'],'SERVICE_CUSTODY_HOLD')
    def test_loops_preserved(self):self.assertEqual({x['id'] for x in read('operations.json')['loops']},{'L_ORIENTATION','L_REPEAT','L_NEXT_SPECIMEN','L_CONTROL','L_REWORK','L_NEXT_PREPARATION'})
    def test_no_outcomes_actor_channel(self):
        a=read('agent_visible.json');self.assertFalse(a['source_outcome_targets_visible']);self.assertNotIn('source_outcomes_reference.json',json.dumps(a))
    def test_reading_scope_retained(self):
        a=read('provenance.json')['source_access'];self.assertEqual((a['main_pages_read'],a['si_pages_read']),(10,12));self.assertEqual(a['movies']['visual_sampling_seconds_per_movie'],[0,7,14,21,28,35]);self.assertFalse(a['matrices_acquired_or_inspected']);self.assertFalse(a['experimental_raw_data_audited'])
    def test_one_paper_count(self):self.assertEqual(read('task.json')['accepted_paper_design_units'],1);self.assertEqual(read('task.json')['validated_runnable_scientific_tasks'],0)
    def test_control_status_authored(self):self.assertTrue(read('controls_and_repeats.json')['no_fabricated_counts']);self.assertEqual(len(read('controls_and_repeats.json')['authored_proposal']),6)
if __name__=='__main__':unittest.main()
