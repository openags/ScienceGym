"""Evaluator regression: unloaded approach cannot earn carrying distance."""
import unittest

import numpy as np

from verify_tool_grasp import carry_reference_index


class CarryReferenceTests(unittest.TestCase):
    def setUp(self):
        self.times = np.array([0., 1., 2., 3., 4.])
        self.contract = dict(actor_module='station_pickup_actor',
            carry_contract=dict(reference_state='sensor_based_pickup_handoff'))
        self.events = [dict(kind='sensor_based_pickup_handoff', time_s=2.)]

    def test_unloaded_distance_is_excluded_and_return_is_at_station(self):
        # 1.4 m empty-handed approach, then 0.1 m retreat and station return.
        # The carry reference must give 0.1 m, and a zero final return error.
        positions = np.array([0., .7, 1.4, 1.3, 1.4])
        origin = carry_reference_index(self.contract, self.events, self.times)
        self.assertAlmostEqual(positions[origin]-positions[3], .1)
        self.assertEqual(positions[-1]-positions[origin], 0.)

    def test_standalone_contract_retains_initial_reference(self):
        self.assertEqual(carry_reference_index(dict(carry_contract={}), [], self.times), 0)

    def test_missing_or_duplicate_handoff_is_not_a_reference(self):
        for events in [[], self.events*2]:
            with self.subTest(events=events):
                self.assertIsNone(carry_reference_index(self.contract, events, self.times))

    def test_outside_or_between_recorded_times_is_rejected(self):
        for t in [-1., 2.5, 5., float('nan')]:
            with self.subTest(time=t):
                self.assertIsNone(carry_reference_index(self.contract,
                    [dict(kind='sensor_based_pickup_handoff', time_s=t)], self.times))

    def test_wrong_actor_cannot_claim_station_handoff(self):
        with self.assertRaises(ValueError):
            carry_reference_index(dict(self.contract, actor_module='carry_tool_actor'), self.events, self.times)

    def test_unknown_reference_cannot_change_acceptance_origin(self):
        with self.assertRaises(ValueError):
            carry_reference_index(dict(self.contract, carry_contract=dict(reference_state='final_state')),
                                  self.events, self.times)


if __name__ == '__main__':
    unittest.main()
