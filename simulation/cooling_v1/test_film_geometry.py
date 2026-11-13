"""Counterexamples to vertex-only cloth penetration checks."""
import unittest
import numpy as np
import mujoco
import xml.etree.ElementTree as ET
from film_geometry import triangle_box_overlap, FilmSolidAudit
from film_contact import exact_cuboid_contacts


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

    def test_multiple_flexes_use_element_data_addresses(self):
        xml='''<mujoco><worldbody>
        <geom name="solid" type="box" size=".5 .5 .5"/>
        <flexcomp name="first" type="direct" dim="2" radius=".001"
          point="2 2 2 3 2 2 2 3 2" element="0 1 2"><edge equality="true"/></flexcomp>
        <flexcomp name="second" type="direct" dim="2" radius=".001"
          point="2 2 2 3 2 2 2 3 2 0 0 0" element="0 1 3 1 2 3 2 0 3"><edge equality="true"/></flexcomp>
        </worldbody></mujoco>'''
        model=mujoco.MjModel.from_xml_string(xml)
        data=mujoco.MjData(model)
        mujoco.mj_forward(model,data)
        audit=FilmSolidAudit(model,['solid'])
        self.assertEqual(audit.triangles[1].tolist(),[[3,4,6],[4,5,6],[5,3,6]])
        result=audit.observe(data)
        self.assertFalse(result['passed'])
        self.assertEqual({p['film'] for p in result['intersecting_pairs']},{'second'})

    def test_convex_mesh_detects_crossing_missed_by_box_narrow_phase(self):
        root=ET.fromstring('''<mujoco><worldbody>
          <geom name="support_0" type="box" size=".5 .5 .5"/>
          <flexcomp name="film" type="direct" dim="2" radius=".001"
             point="-2 -2 .4 2 -2 .4 0 2 .4" element="0 1 2"><edge equality="true"/></flexcomp>
          </worldbody></mujoco>''')
        native=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
        data=mujoco.MjData(native);mujoco.mj_forward(native,data)
        self.assertFalse(FilmSolidAudit(native,['support_0']).observe(data)['passed'])
        self.assertEqual(data.ncon,0)
        exact_cuboid_contacts(root,'support_')
        mesh=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
        data=mujoco.MjData(mesh);mujoco.mj_forward(mesh,data)
        self.assertFalse(FilmSolidAudit(mesh,['support_0']).observe(data)['passed'])
        self.assertGreater(data.ncon,0)
        np.testing.assert_allclose(FilmSolidAudit(mesh,['support_0']).sizes,[[.4999]*3],atol=1e-8)


if __name__ == '__main__':
    unittest.main()
