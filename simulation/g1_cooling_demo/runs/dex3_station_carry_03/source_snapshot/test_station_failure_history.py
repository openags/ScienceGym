"""Regression: a failed child controller must preserve the continuous history."""
import json
from types import SimpleNamespace
import unittest

from station_pickup_actor import StationPickupActor


class FailureHistory(unittest.TestCase):
    def actor(self):
        actor = StationPickupActor.__new__(StationPickupActor)
        actor.m = SimpleNamespace(nu=43)
        actor.phase = 'pickup'
        actor.pickup_started = 25.4
        actor.events = [dict(time_s=13.734, kind='station_arrived'),
                        dict(time_s=25.4, kind='sensor_based_pickup_handoff')]
        actor.pickup = SimpleNamespace(events=[
            dict(time_s=2.8, phase='approach'), dict(time_s=58.222, phase='lift'),
            dict(time_s=64.52, phase='carry_walk_out')])
        return actor

    def test_recorder_retains_last_successful_history_after_nested_failure(self):
        actor = self.actor()
        previous = actor.events+[dict(e, time_s=e['time_s']+25.4) for e in actor.pickup.events]
        response = actor.error_response(RuntimeError('COM did not settle'))
        # The recorder replaces its retained events whenever the reply has
        # an events field. Its previous full history must survive this reply.
        retained = previous
        retained = response.get('events', retained)
        self.assertEqual(json.loads(json.dumps(retained)), previous)
        self.assertEqual(retained[-1]['phase'], 'carry_walk_out')
        self.assertAlmostEqual(retained[-1]['time_s'], 89.92)
        self.assertEqual(response['error'], 'RuntimeError: COM did not settle')
        self.assertNotIn('complete', response)
        self.assertEqual(response['torque'].shape, (43,))

    def test_clock_conversion_does_not_mutate_or_accumulate_on_child_events(self):
        actor = self.actor()
        before = json.dumps(actor.pickup.events)
        first = actor.error_response(RuntimeError('failure'))['events']
        second = actor.error_response(RuntimeError('failure'))['events']
        self.assertEqual(first, second)
        self.assertEqual(json.dumps(actor.pickup.events), before)

    def test_failure_before_handoff_retains_navigation_only(self):
        actor = self.actor()
        actor.pickup, actor.pickup_started, actor.phase = None, None, 'prepare'
        response = actor.error_response(RuntimeError('Preparation timed out'))
        self.assertEqual(response['events'], actor.events)
        self.assertEqual(response['phase'], 'prepare')


if __name__ == '__main__':
    unittest.main()
