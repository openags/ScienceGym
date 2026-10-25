"""Source-scale jack, actual mounting holes and ordinary hardware candidates."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from geometry_tools import HERE, ROOT, sha, write_json

JACK = ROOT / 'assets/thorlabs_l200_v1'
HOLES = [(x, y) for x in [-37.4904, 37.4904] for y in [-12.4968, 12.4968]]


def cad_mesh(shape):
    assert shape.isValid()
    vertices, faces = shape.tessellate(.015, .10)
    mesh = trimesh.Trimesh(vertices=[v.toTuple() for v in vertices], faces=faces)
    mesh.merge_vertices(digits_vertex=5)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight
    mesh.apply_scale(.001)
    return mesh


def cap_screw():
    # Head sits in Z=0..3 mm, shank in Z=3..13 mm. Socket opens at Z=0.
    body = cq.Solid.makeCylinder(2.75, 3).fuse(cq.Solid.makeCylinder(1.5, 10, cq.Vector(0, 0, 3)))
    socket = cq.Workplane('XY').polygon(6, 2.5 / np.cos(np.pi / 6)).extrude(1.3).val()
    return cad_mesh(body.cut(socket))


def countersunk_screw():
    # Flat head in Z=0, tip in +Z=8 mm; cone and socket remain actual voids.
    body = cq.Solid.makeCone(3.36, 1.5, 1.86).fuse(cq.Solid.makeCylinder(1.5, 6.14, cq.Vector(0, 0, 1.86)))
    socket = cq.Workplane('XY').polygon(6, 2 / np.cos(np.pi / 6)).extrude(1.1).val()
    return cad_mesh(body.cut(socket))


def washer():
    return trimesh.creation.annulus(.0016, .0045, .0008, sections=96)


def display(mesh, color=(.52, .57, .62, 1), metal=.78):
    out = trimesh.graph.smooth_shade(mesh, angle=np.radians(25), facet_minarea=100)
    out.metadata.pop('original_components', None)
    out.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(baseColorFactor=color, metallicFactor=metal, roughnessFactor=.38))
    return out


def replace(scene, name, mesh):
    old = scene.geometry.get(name)
    # Keep planar plate normals separate from bore/edge normals; otherwise
    # the CAD triangulation renders a flat plate like a dented metal sheet.
    mesh = display(mesh)
    if old is not None and hasattr(old.visual, 'material'):
        mesh.visual = trimesh.visual.TextureVisuals(material=old.visual.material.copy())
    scene.geometry[name] = mesh


def apply_mount(scene, prefix):
    ledger = json.loads((HERE / 'apparatus_mount_sources.json').read_text())
    model = json.loads((JACK / 'model.json').read_text())
    assert sha(ROOT / model['geometry']['path']) == model['geometry']['sha256']
    base = scene.geometry[prefix + 'acrylic_base']
    center = base.bounds.mean(axis=0)[:2]
    bottom, base_top = base.bounds[:, 2]
    foil = scene.geometry[prefix + 'mylar_base']
    jack_bottom = float(foil.bounds[1, 2])
    jack_top = jack_bottom + model['source_pose_height_m']
    old_platform_bottom = scene.geometry[prefix + 'lift_plate'].bounds[0, 2]
    dz = float(jack_top - old_platform_bottom)
    translated, removed, rebuilt, added = [], [], [], []
    for name in list(scene.geometry):
        suffix = name.removeprefix(prefix)
        if suffix in ['lift_foot', 'lift_thread'] or suffix.startswith(('sensor_lead_', 'probe_contact_')):
            scene.delete_geometry(name)
            removed.append(name)
        elif suffix.startswith(('foam_', 'emitter_', 'cover_')) or suffix in ['PE_support', 'PE_support_mylar', 'film_spacer', 'radiation_shield', 'aperture_plate', 'solar_reflector', 'reflector_track', 'reflector_carriage', 'fixed_reflector_band']:
            scene.geometry[name].apply_translation([0, 0, dz])
            translated.append(name)
    # Original authored envelopes, now with actual through-holes.
    for suffix, size, z, countersink in [
        ('acrylic_base', base.extents * 1000, bottom * 1000, False),
        ('mylar_base', foil.extents * 1000, base_top * 1000, False),
        ('lift_plate', np.array([170., 170., 5.]), jack_top * 1000, True)]:
        shape = cq.Solid.makeBox(*size, cq.Vector(-size[0] / 2, -size[1] / 2, z))
        for x, y in HOLES:
            shape = shape.cut(cq.Solid.makeCylinder(1.7, size[2] + 2, cq.Vector(x, y, z - 1)))
            if countersink:
                shape = shape.cut(cq.Solid.makeCone(1.7, 3.36, 1.66, cq.Vector(x, y, z + size[2] - 1.66)))
        mesh = cad_mesh(shape)
        mesh.apply_translation([*center, 0])
        replace(scene, prefix + suffix, mesh)
        rebuilt.append(prefix + suffix)
    jack = trimesh.load(ROOT / model['geometry']['path'], force='scene')
    translation = [*center, jack_bottom]
    for node in jack.graph.nodes_geometry:
        matrix, key = jack.graph[node]
        mesh = jack.geometry[key].copy()
        mesh.apply_transform(matrix)
        mesh.apply_translation(translation)
        name = prefix + node
        scene.add_geometry(mesh, node_name=name, geom_name=name)
        added.append(name)
    interfaces = []
    for i, (x, y) in enumerate(HOLES, 1):
        xy = center + np.array([x, y]) * .001
        cap = cap_screw()
        cap.apply_translation([*xy, bottom - .0008 - .003])
        ring = washer()
        ring.apply_translation([*xy, bottom - .0004])
        top = countersunk_screw()
        top.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        top.apply_translation([*xy, jack_top + .005])
        for suffix, mesh in [('base_screw_' + str(i), cap), ('base_washer_' + str(i), ring), ('platform_screw_' + str(i), top)]:
            name = prefix + suffix
            scene.add_geometry(display(mesh), node_name=name, geom_name=name)
            added.append(name)
        interfaces.append(dict(id=str(i), center_xy_m=xy.tolist(),
                               bottom_screw_tip_z_m=float(bottom - .0008 + .010),
                               bottom_engagement_m=float(bottom - .0008 + .010 - jack_bottom),
                               top_screw_tip_z_m=float(jack_top + .005 - .008),
                               top_engagement_m=.003,
                               bottom_screw=prefix + 'base_screw_' + str(i),
                               bottom_washer=prefix + 'base_washer_' + str(i),
                               top_screw=prefix + 'platform_screw_' + str(i)))
    return dict(source_jack_geometry=model['geometry'], jack_translation_m=translation,
                base_bottom_m=float(bottom), base_top_m=float(base_top), jack_bottom_m=jack_bottom,
                jack_top_m=float(jack_top), platform_top_m=float(jack_top + .005),
                thermal_and_reflector_translation_m=[0, 0, dz], translated_parts=translated,
                removed_legacy_parts=removed, rebuilt_parts=rebuilt, added_parts=added,
                interfaces=interfaces, physical_installation_qualified=False,
                core_inspection_parts=rebuilt + added, limitations=ledger['limits'])


def build_stock():
    scene = trimesh.Scene()
    units = []
    for row, (kind, maker) in enumerate([('cap_m3x10', cap_screw), ('csk_m3x8', countersunk_screw), ('washer_m3', washer)]):
        for i in range(8):
            mesh = maker()
            if kind == 'washer_m3':
                mesh.apply_translation([0, 0, .0004])
            mesh.apply_translation([i * .014, row * .020, 0])
            name = f'{kind}_{i + 1:02d}'
            scene.add_geometry(display(mesh), node_name=name, geom_name=name)
            units.append(dict(id=name, kind=kind, parts=[name]))
    path = HERE / 'geometry' / 'lift_mount_hardware.glb'
    path.write_bytes(scene.export(file_type='glb', include_normals=True))
    record = dict(id='lift_mount_hardware', label='升降台安装紧固件 · 8 螺钉 + 8 沉头螺钉 + 8 垫圈',
                  geometry=dict(path=str(path.relative_to(ROOT)), sha256=sha(path), parts=len(scene.geometry), bounds_m=scene.bounds.tolist()),
                  units=units, resource_id='consumables:consumable_12', component_label='height-adjuster mount fasteners',
                  selected_required_units=24, accepted=False,
                  source_artifacts=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in [Path(__file__), HERE / 'apparatus_mount_sources.json']])
    write_json(HERE / 'lift_mount_stock.json', record)
    return record


if __name__ == '__main__':
    build_stock()
