"""Regression cases for the station carry guard's sole/floor classification."""
import copy
import unittest

import mujoco
import numpy as np

from carry_tool_actor import declared_sole_support, validate_support_prior


class SupportContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = mujoco.MjModel.from_xml_string('''<mujoco><worldbody>
          <body name="lab_architecture">
            <geom name="floor" type="box" size="2 2 .05" pos="0 0 -.05"/>
            <geom name="bench" type="box" size=".2 .2 .2" pos="1 0 .7"/>
          </body>
          <body name="left_ankle_roll_link" pos="0 0 .1">
            <geom name="left_ankle_roll_link_collision_0" size=".05"/>
          </body>
          <body name="right_hand_index_1_link" pos="0 0 1">
            <geom name="finger" size=".01"/>
          </body></worldbody></mujoco>''')
        cls.prior = dict(floor_geoms=['floor'],
            sole_geoms=['left_ankle_roll_link_collision_0'], maximum_penetration_m=.001)

    def contact(self, first, second, distance=-.000013, normal=(0, 0, 1)):
        c = mujoco.MjContact()
        c.geom[:] = [self.model.geom(first).id, self.model.geom(second).id]
        c.dist = distance
        c.frame[:] = np.r_[normal, [1., 0., 0.], [0., 1., 0.]]
        return c

    def test_recorded_shallow_floor_support_in_both_geom_orders(self):
        foot = self.prior['sole_geoms'][0]
        self.assertTrue(declared_sole_support(self.model, self.contact('floor', foot), self.prior))
        self.assertTrue(declared_sole_support(self.model,
            self.contact(foot, 'floor', normal=(0, 0, -1)), self.prior))

    def test_deep_sole_contact_is_rejected(self):
        self.assertFalse(declared_sole_support(self.model,
            self.contact('floor', self.prior['sole_geoms'][0], distance=-.00101), self.prior))

    def test_sole_against_floor_side_is_not_support(self):
        self.assertFalse(declared_sole_support(self.model,
            self.contact('floor', self.prior['sole_geoms'][0], normal=(1, 0, 0)), self.prior))

    def test_finger_floor_and_sole_bench_are_not_exempted(self):
        for a, b in [('floor', 'finger'), ('bench', self.prior['sole_geoms'][0]),
                     ('finger', self.prior['sole_geoms'][0])]:
            self.assertFalse(declared_sole_support(self.model, self.contact(a, b), self.prior))

    def test_absent_prior_preserves_strict_legacy_guard(self):
        self.assertFalse(declared_sole_support(self.model,
            self.contact('floor', self.prior['sole_geoms'][0]), None))

    def test_prior_cannot_exempt_finger_or_raise_original_bound(self):
        for change in [dict(sole_geoms=['finger']), dict(maximum_penetration_m=.00101),
                       dict(maximum_penetration_m=float('nan')), dict(floor_geoms=[])]:
            prior = copy.deepcopy(self.prior)
            prior.update(change)
            with self.assertRaises(ValueError):
                validate_support_prior(self.model, prior)


if __name__ == '__main__':
    unittest.main()
