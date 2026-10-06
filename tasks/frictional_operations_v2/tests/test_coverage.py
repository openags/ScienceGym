"""Original source-to-design coverage and disclosure checks, not science tests."""
from pathlib import Path
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from contract import load_contract,digest

def load(name):return json.loads((ROOT/name).read_text())
class CoverageTests(unittest.TestCase):
    def test_inventory(self):
        ops,sem=load_contract(ROOT);s=load('shared_binding_contract.json');self.assertEqual(len(ops),12)
        for key,n in [('branch_ids',9),('station_ids',6),('asset_ids',8),('unknown_ids',20),('anchors',32)]:self.assertEqual(len(s[key]),n)
        self.assertEqual(sem,load('semantic_core.json')['shared_binding_contract_sha256'])
    def test_all_branches(self):self.assertEqual([b['id'] for b in load('branches.json')['branches']],[f'B{i:02}' for i in range(1,10)])
    def test_all_qualification_holds(self):
        u=load('unknown_inputs.json');self.assertEqual(u['default_resolution_state'],'UNRESOLVED');self.assertEqual([x['id'] for x in u['unknowns']],[f'U{i:02}' for i in range(1,21)])
    def test_source_discrepancies_retained(self):
        cs={x['id']:x for x in load('source_conflicts.json')['conflicts_and_extraction_hazards']};self.assertEqual(set(cs),{'C01','C02','C03','C04'})
        self.assertIn('0.1',str(cs['C01']));self.assertIn('1.0',str(cs['C01']));self.assertIn('not a published correction',cs['C02']['classification']);self.assertIn('inverse',str(cs['C03']))
    def test_whole_written_coverage(self):
        r=load('read_coverage.json');self.assertEqual(len(r['main_pages']),8);self.assertEqual(len(r['main_figures']),5);self.assertEqual(len(r['main_equations']),9);self.assertFalse(r['movie_visual_scope']['continuous_playback'])
    def test_rights_are_not_flattened(self):
        p=load('provenance.json');self.assertEqual(p['source_license'],'CC BY-NC-SA 3.0 Unported');self.assertTrue(all(x['exported'] is False for x in p['source_receipts']));self.assertIn('external',p['third_party_images'])
    def test_references_are_not_measurements(self):
        r=load('evaluator_reference.json');self.assertFalse(r['actor_visibility']);self.assertFalse(r['source_outcome_is_generated_measurement']);self.assertFalse(r['source_outcome_is_success_threshold'])
    def test_anchors_are_not_robot_targets(self):
        a=load('shared_binding_contract.json')['anchors'];self.assertTrue(all(x['kind']=='evidence_only_proxy' and x['physical_motion_target'] is False and 'support_contract' not in x for x in a))
    def test_dependency_closure(self):
        ops,_=load_contract(ROOT)
        self.assertEqual(ops['R11']['depends_on'],[]);self.assertTrue(ops['R11']['repeatable_by_job']);self.assertEqual(ops['R08']['depends_on'],['R05','R06','R07'])
        for op in ops.values():self.assertTrue(set(op['unknown_refs'])<={f'U{i:02}' for i in range(1,21)});self.assertFalse(op['physical_execution_authority'])
if __name__=='__main__':unittest.main()
