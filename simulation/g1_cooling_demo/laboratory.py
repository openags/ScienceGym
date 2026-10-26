"""Import the reviewed laboratory into the contact plant without scaling assets.

The importer keeps exact source triangles for rendering and a separate named
geom for each source part. MuJoCo mesh contacts use each part's convex hull;
unopened equipment is therefore a fixed obstacle, not a qualified device model.
The handled tray keeps the existing decomposed, free-body contact model.
"""
from pathlib import Path
import hashlib
import io
import json
import os
import struct
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
ROBOT = ROOT / 'assets/unitree_g1_inspire_v1'
CACHE = Path(__file__).resolve().parent / 'lab_cache'
SCENE = ROOT / 'assets/cooling_lab_v1/scene.json'
# The robot's work frame faces the existing white assembly bench (+lab Y).
# This is an initial placement, never an update to the floating base at runtime.
LAB_FROM_WORK = np.array([[0., -1., 0., 3.7],
                          [1., 0., 0., 2.02],
                          [0., 0., 1., 0.],
                          [0., 0., 0., 1.]])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numbers(values):
    return ' '.join(format(float(v), '.12g') for v in values)


def cached(data, suffix):
    key = hashlib.sha256(data).hexdigest()
    path = CACHE / (key + suffix)
    if not path.exists():
        path.write_bytes(data)
    elif digest(path) != key:
        raise ValueError('Corrupted laboratory mesh cache: ' + str(path))
    return path


def mesh_bytes(mesh):
    """MuJoCo MSH preserves source vertices, normals, UVs and triangle indices."""
    vertices = np.asarray(mesh.vertices, dtype='<f4')
    normals = np.asarray(mesh.vertex_normals, dtype='<f4')
    uv = getattr(mesh.visual, 'uv', None)
    uv = np.asarray(uv, dtype='<f4') if uv is not None else np.empty((0, 2), '<f4')
    if len(uv) not in (0, len(vertices)):
        raise ValueError('Source UV count differs from vertex count')
    faces = np.asarray(mesh.faces, dtype='<i4')
    return (struct.pack('<4i', len(vertices), len(normals), len(uv), len(faces))
            + vertices.tobytes() + normals.tobytes() + uv.tobytes() + faces.tobytes())


def attach(xml, out, *, map_only=False):
    """Replace the standalone table/floor with the original laboratory.

    The actor receives only the authored architectural map, not loose equipment
    or live object state. Both models share the same coordinate transform.
    """
    out = Path(out)
    CACHE.mkdir(exist_ok=True)
    source = json.loads(SCENE.read_text())
    world, assets = xml.find('worldbody'), xml.find('asset')
    for node in list(world):
        if node.tag == 'geom' and (node.get('name', '').startswith('bench_')
                                  or node.get('name') == 'review_floor'):
            world.remove(node)
    origin = np.linalg.inv(LAB_FROM_WORK)[:3, 3]
    lab = ET.SubElement(world, 'body', name='laboratory_map', pos=numbers(origin),
                        quat=numbers([2**-.5, 0, 0, -2**-.5]))
    mesh_names, material_names, texture_names = {}, {}, {}
    parts, inputs, instances = [], {}, []

    def material(mesh):
        mat = getattr(mesh.visual, 'material', None)
        rgba = getattr(mat, 'baseColorFactor', None)
        rgba = np.asarray(rgba if rgba is not None else [170, 175, 175, 255]) / 255.
        image = getattr(mat, 'baseColorTexture', None)
        texture_path = None
        if image is not None:
            stream = io.BytesIO()
            image.convert('RGBA').save(stream, format='PNG')
            texture_path = cached(stream.getvalue(), '.png')
            if texture_path not in texture_names:
                name = 'lab_texture_' + str(len(texture_names))
                ET.SubElement(assets, 'texture', name=name, type='2d',
                              file=os.path.relpath(texture_path, out))
                texture_names[texture_path] = name
        key = (tuple(rgba), str(texture_path))
        if key not in material_names:
            name = 'lab_material_' + str(len(material_names))
            values = dict(name=name, rgba=numbers(rgba), specular='.2', shininess='.15')
            if texture_path:
                values['texture'] = texture_names[texture_path]
            ET.SubElement(assets, 'material', **values)
            material_names[key] = name
        return material_names[key]

    def include(identifier, path, expected, position, yaw):
        path = ROOT / path
        if digest(path) != expected:
            raise ValueError('Source geometry hash changed: ' + str(path))
        inputs[str(path.relative_to(ROOT))] = expected
        model = trimesh.load(path, force='scene', process=False)
        body = ET.SubElement(lab, 'body', name='lab_' + identifier,
                             pos=numbers(position),
                             quat=numbers([np.cos(yaw/2), 0, 0, np.sin(yaw/2)]))
        count = 0
        for node in sorted(model.graph.nodes_geometry):
            transform, geometry = model.graph[node]
            mesh = model.geometry[geometry].copy()
            mesh.apply_transform(transform)
            singular = np.linalg.svd(mesh.vertices-mesh.vertices.mean(axis=0), compute_uv=False)
            planar = bool(singular[-1] < max(1e-10, singular[0]*1e-9))
            filename = cached(mesh_bytes(mesh), '.msh')
            if filename not in mesh_names:
                name = 'lab_mesh_' + str(len(mesh_names))
                ET.SubElement(assets, 'mesh', name=name,
                              file=os.path.relpath(filename, ROBOT), inertia='shell')
                mesh_names[filename] = name
            name = 'lab_part_' + str(len(parts))
            ET.SubElement(body, 'geom', name=name, type='mesh', mesh=mesh_names[filename],
                          material=material(mesh), group='2',
                          contype='0' if planar else '1', conaffinity='0' if planar else '1', friction='.7 .005 .0001')
            parts.append(dict(geom=name, instance=identifier, source_part=node,
                              source_bounds_m=mesh.bounds.tolist(), vertices=len(mesh.vertices),
                              triangles=len(mesh.faces), mesh_sha256=filename.stem,
                              contact='none_zero_thickness_source_surface' if planar else 'source_part_convex_hull'))
            count += 1
        instances.append(dict(id=identifier, parts=count, position_m=position, yaw_rad=yaw,
                              state='fixed_initial_obstacle'))

    arch = source['architecture']
    include('architecture', arch['path'], arch['sha256'], [0, 0, 0], 0)
    dynamic_ids = {'g1'}
    if world.find("body[@name='carrier_tray']") is not None:
        dynamic_ids.add('tray_white')
    if not map_only:
        for item in source['assets']:
            if item['id'] in dynamic_ids:
                continue
            include(item['id'], item['geometry'], item['geometry_sha256'],
                    item['position_m'], item['yaw_rad'])
    statistic = xml.find('statistic')
    if statistic is None:
        statistic = ET.SubElement(xml, 'statistic')
    statistic.attrib.update(center='0.3 0 1', extent='4')
    visual = xml.find('visual')
    visual_map = visual.find('map')
    if visual_map is None:
        visual_map = ET.SubElement(visual, 'map')
    visual_map.attrib.update(znear='.002', zfar='30')
    # Local lights stay in the room; no cuts or visibility masks remove walls.
    for light in world.findall('light'):
        light.set('directional', 'false')
    manifest = dict(schema_version='sciencegym.laboratory_runtime_import.v1',
        scene_sha256=digest(SCENE), importer_sha256=digest(__file__),
        lab_from_work=LAB_FROM_WORK.tolist(), architecture_only=map_only,
        source_inputs=inputs, imported_instances=instances, parts=parts,
        dynamic_bindings=[] if map_only else [dict(instance='g1', body='pelvis')]+(
            [dict(instance='tray_white', body='carrier_tray')] if 'tray_white' in dynamic_ids else []),
        initial_staging=[] if map_only else [
            dict(instance='g1', laboratory_xy_m=[3.7, 2.02], yaw_rad=float(np.pi/2))]+([
            dict(instance='tray_white', original_m=[3.4, 2.8, .9],
                 laboratory_m=[3.7, 2.53, .9005], yaw_rad=float(np.pi),
                 basis='Authored initial staging on the existing white bench; not an executed preparation step')] if 'tray_white' in dynamic_ids else []),
        collision_scope='Per-part convex mesh obstacles; non-convex equipment cavities and device articulation are not qualified',
        source_documentation='https://mujoco.readthedocs.io/en/stable/XMLreference.html#asset-mesh',
        assets_accepted=False, physical_campaign_qualified=False)
    (out/'laboratory_import.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('laboratory_import', len(instances), 'instances', len(parts), 'parts', flush=True)
    return manifest
