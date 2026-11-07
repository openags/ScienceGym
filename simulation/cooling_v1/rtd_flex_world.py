"""Inextensible-string approximation for the RTD's complete 12 ft cable.

This alternative retains cable mass, length, gravity and contact but omits
torsional and bending stiffness. It is intended to test routing and retention,
not connector-load prediction. The serial elastic-rod model remains available
in rtd_world.py for comparison.
"""
import xml.etree.ElementTree as ET
import numpy as np
from rtd_world import build as build_rod,cable_points
from world import vec


def build(path,bore_diameter=.0066):
    configuration=build_rod(path,bore_diameter=bore_diameter);tree=ET.parse(path);root=tree.getroot()
    root.remove(root.find('extension'));probe=root.find(".//body[@name='rtd']")
    probe.remove(probe.find('composite'));points=cable_points()
    mass=1300*np.pi*.002**2*configuration['cable_centerline_length_m']
    flex=ET.SubElement(probe,'flexcomp',name='rtd_cable',type='direct',dim='1',
                       point=vec(points.flatten()),element=' '.join(f'{i} {i+1}' for i in range(len(points)-1)),
                       mass=str(mass),radius='.002',rgba='.025 .03 .035 1')
    ET.SubElement(flex,'pin',id='0')
    # Default soft equality allowed 47% local extension during transport.
    # Use a declared stiff length constraint and verify every recorded edge.
    ET.SubElement(flex,'edge',equality='true',damping='.001',solref='.002 1',solimp='.9999 .9999 .00001')
    ET.SubElement(flex,'contact',selfcollide='auto',condim='3',friction='.3 .001 .0001',solref='.0021 1',solimp='.99 .999 .0001')
    root.find('option').set('noslip_iterations','0')
    ET.indent(root);tree.write(path,encoding='unicode')
    configuration.update(cable_model='inextensible_string',cable_mass_kg=float(mass),bend_Pa=None,twist_Pa=None,
                         edge_constraint_timeconst_s=.002,edge_constraint_impedance=.9999,
                         maximum_accepted_edge_strain=.01,
                         limitations=['Cable bending and torsion are omitted; no measured connector-force prediction',
                                      'Node spacing resolves the declared initial coil but is not a cable-material calibration'])
    return configuration
