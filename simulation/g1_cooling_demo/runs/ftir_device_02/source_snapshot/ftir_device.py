"""Passive Nicolet cover, sliding door and scan keys for the laboratory plant.

The instrument stays at its authored laboratory placement. Its reconstruction
is not vendor CAD. All mechanical parameters here are declared engineering
inferences and do not qualify the device or a robot operation.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

from convex_cells import clean, decompose

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/nicolet_6700_mechanism_v1/build_receipt.json'
INTERFACES = ROOT / 'assets/nicolet_6700_v1/interfaces.json'
RECESSED_PARTS = {'sample_bay_lid', 'sample_bay_rear_wall',
                  'rear_optics_housing', 'scan_panel', 'right_source_housing'}


def numbers(v):
    return ' '.join(format(float(x), '.12g') for x in v)


def source_override():
    receipt = json.loads(SOURCE.read_text())
    if not receipt['passed']:
        raise ValueError('Operating-clearance source review failed')
    return receipt['geometry_override']


def prepare(xml, body, scene, asset):
    """Return exact part-to-body bindings, source-relative origins and cells."""
    interfaces = json.loads(INTERFACES.read_text())
    normal = np.asarray(asset['normalization_matrix'])
    cover = next(i for i in interfaces['interfaces'] if i['id'] == 'sample_cover')
    slider = next(i for i in interfaces['interfaces'] if i['id'] == 'sample_access_slider')
    pivot = (normal @ np.r_[cover['pivot_m'], 1.])[:3]
    lid = ET.SubElement(body, 'body', name='nicolet_cover', pos=numbers(pivot))
    ET.SubElement(lid, 'joint', name='nicolet_cover_hinge', type='hinge',
                  axis=numbers(cover['axis']), range=numbers([-np.pi/2, 0]),
                  damping='.15', frictionloss='.65', solreflimit='.004 1')
    door = ET.SubElement(lid, 'body', name='nicolet_sliding_door')
    ET.SubElement(door, 'joint', name='nicolet_door_slide', type='slide',
                  axis=numbers(slider['axis']), range=numbers([0, slider['travel_m']]),
                  damping='2', frictionloss='.8', solreflimit='.004 1')
    ET.SubElement(lid, 'site', name='nicolet_cover_handle',
                  pos=numbers((normal @ np.r_[cover['grasp_center_m'], 1.])[:3] - pivot),
                  size='.001', rgba='0 0 0 0')
    bindings = {}
    for name in cover['parts']:
        bindings[name] = (door if name in slider['parts'] else lid, pivot)
    key_specs = []
    for control in interfaces['interfaces']:
        if control['kind'] != 'push_button':
            continue
        index = control['id'].split('_')[-1]
        origin = (normal @ np.r_[control['center_m'], 1.])[:3]
        key = ET.SubElement(body, 'body', name='nicolet_key_' + index, pos=numbers(origin))
        ET.SubElement(key, 'joint', name='nicolet_key_slide_' + index, type='slide',
                      axis=numbers(control['axis']), range='0 .0003', stiffness='1000',
                      springref='0', damping='1', frictionloss='.05', solreflimit='.004 1')
        bindings['scan_key_' + index] = (key, origin)
        key_specs.append(dict(id=control['id'], label=control['label'],
                              travel_m=.0003, spring_n_per_m=1000, damping_ns_per_m=1,
                              friction_n=.05, moving_mass_kg=.002))
    meshes, cells, inertia = {}, {}, []
    for name in sorted(scene.graph.nodes_geometry):
        transform, geometry = scene.graph[name]
        mesh = scene.geometry[geometry].copy()
        mesh.apply_transform(transform)
        meshes[name] = mesh
        if name in RECESSED_PARTS:
            cells[name] = decompose(mesh)
    for target in [lid, door] + [b for b in body.findall('body') if b.get('name', '').startswith('nicolet_key_')]:
        components = []
        for name, (parent, origin) in bindings.items():
            if parent is not target:
                continue
            m = clean(meshes[name])
            if not m.is_volume:
                raise ValueError('Moving source mesh is not a closed solid: ' + name)
            density = 8000 if name.startswith('lid_hinge_') else 1050
            mass = .002 if name.startswith('scan_key_') else m.volume * density
            components.append((mass, m.center_mass - origin, m.moment_inertia * (mass / m.volume)))
        mass = sum(p[0] for p in components)
        center = sum(m * c for m, c, _ in components) / mass
        moment = np.zeros((3, 3))
        for m, c, I in components:
            offset = c - center
            moment += I + m * (np.dot(offset, offset) * np.eye(3) - np.outer(offset, offset))
        ET.SubElement(target, 'inertial', mass=str(mass), pos=numbers(center),
                      fullinertia=numbers([moment[0, 0], moment[1, 1], moment[2, 2],
                                          moment[0, 1], moment[0, 2], moment[1, 2]]))
        inertia.append(dict(body=target.get('name'), mass_kg=float(mass),
                            local_center_m=center.tolist(), inertia_kg_m2=moment.tolist()))
    report = dict(schema_version='sciencegym.passive_ftir_device.v1',
        interfaces_sha256=hashlib.sha256(INTERFACES.read_bytes()).hexdigest(),
        source_revision_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        geometry=source_override(), placement_m=asset['position_m'],
        hinge=dict(range_rad=[-float(np.pi/2), 0], damping_nms_per_rad=.15,
                   friction_nm=.65, pivot_in_normalized_asset_m=pivot.tolist()),
        door=dict(travel_m=slider['travel_m'], damping_ns_per_m=2, friction_n=.8),
        keys=key_specs, inertias=inertia,
        decomposition={name: dict(cells=len(parts), source_volume_m3=float(clean(meshes[name]).volume),
                                  cell_volume_m3=float(sum(p.volume for p in parts)))
                       for name, parts in cells.items()},
        dynamics_parameters_inferred=True, manufacturer_mechanism_qualified=False,
        device_actuators=[], actor_state_channels=[],
        assumptions=['Shell density 1050 kg/m3; hinge cylinders 8000 kg/m3.',
                     'Each scan key includes an inferred 2 g moving plunger.',
                     'Friction, damping, spring, travel and stops are unmeasured development values.',
                     'Other fixed parts retain convex hull obstacles; connectors remain unqualified.'])
    return bindings, cells, report
