"""Bind an explicit, uncalibrated fingertip/tool compliance sensitivity trial.

The steel tool's high-priority 0.9999 contact impedance otherwise overrides
the finger contact model. This candidate changes only normal/tangential solver
impedance on the declared gripping interfaces. It preserves the surfaces,
friction, time constant, contact dimension, zero margin/gap and all limits.
Neither impedance value is a measured hardware material property.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def numbers(values):
    return ' '.join(format(float(v), '.17g') for v in values)


def bind(path, contact_bodies, impedance):
    if not np.isfinite(impedance) or not .95 <= impedance <= .9999:
        raise ValueError('Contact impedance trial must lie within 0.95 to 0.9999')
    path = Path(path)
    before = mujoco.MjModel.from_xml_path(str(path))
    tool = {before.body('tweezer').id}
    for b in range(before.nbody):
        if before.body_parentid[b] in tool:
            tool.add(b)
    hands = {before.body(n).id for n in contact_bodies}
    tool_geoms = [g for g in range(before.ngeom) if before.geom_bodyid[g] in tool]
    hand_geoms = [g for g in range(before.ngeom) if before.geom_bodyid[g] in hands]
    xml = ET.parse(path)
    contact = xml.getroot().find('contact')
    if contact is None:
        contact = ET.SubElement(xml.getroot(), 'contact')
    existing = {frozenset((v.get('geom1'), v.get('geom2'))) for v in contact.findall('pair')}
    interfaces = []
    for hand in hand_geoms:
        for metal in tool_geoms:
            if not ((before.geom_contype[hand] & before.geom_conaffinity[metal]) or
                    (before.geom_contype[metal] & before.geom_conaffinity[hand])):
                continue
            names = [before.geom(hand).name, before.geom(metal).name]
            if frozenset(names) in existing:
                raise ValueError('An explicit material pair already exists: '+str(names))
            # These checks make the preserved mixing rule explicit. Do not
            # silently apply this helper to a different pair of materials.
            assert before.geom_priority[metal] > before.geom_priority[hand]
            assert before.geom_condim[metal] == 4
            assert before.geom_margin[metal] == before.geom_margin[hand] == 0.
            assert before.geom_gap[metal] == before.geom_gap[hand] == 0.
            old_impedance = before.geom_solimp[metal].copy()
            assert np.allclose(old_impedance[:2], [.9999, .9999], rtol=0, atol=1e-12)
            selected = old_impedance.copy()
            selected[:2] = impedance
            friction = before.geom_friction[metal]
            expanded = [friction[0], friction[0], friction[1], friction[2], friction[2]]
            ET.SubElement(contact, 'pair', geom1=names[0], geom2=names[1], condim='4',
                          solref=numbers(before.geom_solref[metal]), solimp=numbers(selected),
                          friction=numbers(expanded), margin='0', gap='0')
            interfaces.append(dict(parts=names, previous_solimp=old_impedance.tolist(),
                                   selected_solimp=selected.tolist(), solref=before.geom_solref[metal].tolist(),
                                   friction=expanded, margin_m=0., gap_m=0., condim=4))
    if not interfaces:
        raise ValueError('No active source fingertip/tool interfaces')
    xml.write(path, encoding='unicode')
    after = mujoco.MjModel.from_xml_path(str(path))
    fields = ['body_mass', 'body_inertia', 'body_ipos', 'body_iquat',
              'jnt_type', 'jnt_pos', 'jnt_axis', 'jnt_range', 'jnt_stiffness',
              'dof_damping', 'dof_armature', 'geom_type', 'geom_pos', 'geom_quat',
              'geom_size', 'geom_contype', 'geom_conaffinity', 'geom_friction',
              'geom_solref', 'geom_solimp', 'mesh_vert', 'mesh_face',
              'actuator_ctrlrange', 'actuator_forcerange', 'qpos0']
    assert all(np.array_equal(getattr(before, f), getattr(after, f)) for f in fields)
    assert after.npair == before.npair + len(interfaces)
    # Compiler ordering can change, so compare the original pairs by geom IDs.
    old_pairs = {(int(before.pair_geom1[i]), int(before.pair_geom2[i])): i for i in range(before.npair)}
    new_pairs = {(int(after.pair_geom1[i]), int(after.pair_geom2[i])): i for i in range(after.npair)}
    for key, i in old_pairs.items():
        j = new_pairs[key]
        for field in ['pair_dim', 'pair_solref', 'pair_solimp', 'pair_friction', 'pair_margin', 'pair_gap']:
            assert np.array_equal(getattr(before, field)[i], getattr(after, field)[j])
    return dict(scope=__doc__, selected_impedance=impedance, interfaces=interfaces,
                source_geometry_dynamics_and_actuation_exact=True, unchanged_fields=fields,
                preexisting_pairs_exact=True, contact_force_before_geometric_touch=False,
                physical_acceptance_unchanged=True, hardware_material_calibration_claimed=False,
                documentation='https://mujoco.readthedocs.io/en/latest/modeling.html#solver-parameters',
                qualified_carry=False)
