"""Counterexamples to vertex-only cloth penetration checks."""
import unittest
import numpy as np
from film_geometry import triangle_box_overlap


class TriangleBoxTests(unittest.TestCase):
    def test_interior_crosses_box_without_inside_vertices(self):
        tri = np.array([[[-2, -2, 0], [2, -2, 0], [0, 2, 0]]], dtype=float)
        self.assertFalse(np.any(np.all(abs(tri[0]) <= .5, axis=1)))
        self.assertTrue(triangle_box_overlap(tri, [.5, .5, .5])[0])

    def test_triangle_plane_separates_overlapping_bounding_boxes(self):
        tri = [[[2, 0, 0], [0, 2, 0], [0, 0, 2]]]
        self.assertFalse(triangle_box_overlap(tri, [.5, .5, .5])[0])

    def test_face_contact_and_explicit_numerical_allowance(self):
        tri = [[[0, 0, .5], [.2, 0, .5], [0, .2, .5]]]
        self.assertTrue(triangle_box_overlap(tri, [.5, .5, .5])[0])
        self.assertFalse(triangle_box_overlap(tri, [.4999, .4999, .4999])[0])

    def test_rotated_coordinate_frame(self):
        tri = np.array([[[-2, -2, 0], [2, -2, 0], [0, 2, 0]]], dtype=float)
        angle = .713
        rotation = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]])
        center = np.array([4, 5, 6])
        world = tri @ rotation.T + center
        self.assertTrue(triangle_box_overlap((world-center) @ rotation, [.5, .5, .5])[0])


if __name__ == '__main__':
    unittest.main()
