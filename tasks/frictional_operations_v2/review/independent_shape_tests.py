"""Finite adversarial shape sweep; no randomness, network, or scientific values."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from contract import ContractError, EvidenceLedger
from fixtures import make_fixture

TARGETS = ('REC_R01', 'REC_R02', 'REC_R03', 'REC_R04', 'REC_R05',
           'REC_R08', 'REC_R09', 'REC_R10', 'CLOSE_RUN_JOB_CON_LOW', 'REC_R12')
REPLACEMENTS = (None, [], {}, True, 13, '')


def mutation_paths(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield path + (key,), child
            yield from mutation_paths(child, path + (key,))
    elif isinstance(value, list) and value:
        yield path + (0,), value[0]
        yield from mutation_paths(value[0], path + (0,))


def cases(receipts):
    for target in TARGETS:
        for path, prior in mutation_paths(receipts[target]):
            for replacement in REPLACEMENTS:
                if replacement != prior:
                    yield target, path, replacement


class IndependentShapeSweepTests(unittest.TestCase):
    def test_all_finite_adversarial_shape_mutations_reject_cleanly(self):
        plan, receipts, order = make_fixture()
        checked = 0
        for target, path, replacement in cases(receipts):
            checked += 1
            with self.subTest(receipt=target, field=path, replacement=repr(replacement)):
                changed = copy.deepcopy(receipts)
                obj = changed[target]
                for key in path[:-1]:
                    obj = obj[key]
                obj[path[-1]] = replacement
                with self.assertRaises(ContractError):
                    ledger = EvidenceLedger(ROOT, 'CAM_SYNTHETIC', 'EPOCH_1', plan, changed)
                    for action in order:
                        ledger.propose(action)
                        if action['evidence_id'] == target:
                            break
        self.assertGreaterEqual(checked, 3000)


if __name__ == '__main__':
    unittest.main()
