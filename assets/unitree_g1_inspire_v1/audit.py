"""Audit the vendored URDF and export its zero-pose geometry for asset review.

This does not import an actuator model or execute a manipulation controller.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def origin(element):
    out = np.eye(4)
    if element is not None:
        out = trimesh.transformations.euler_matrix(*map(float, element.get('rpy', '0 0 0').split()))
        out[:3, 3] = list(map(float, element.get('xyz', '0 0 0').split()))
    return out


def audit():
    source = json.loads((HERE / 'SOURCE.json').read_text())
    for entry in source['files']:
        assert sha(HERE / entry['path']) == entry['sha256'], entry['path']
    path = HERE / source['model_path']
    robot = ET.parse(path).getroot()
    links = {l.get('name'): l for l in robot.findall('link')}
    joints = {j.get('name'): j for j in robot.findall('joint')}
    assert len(links) == len(robot.findall('link'))
    children = {j.find('child').get('link'): j for j in joints.values()}
    assert len(children) == len(joints)
    roots = set(links) - set(children)
    assert len(roots) == 1 and set(children) <= set(links)
    root = next(iter(roots))
    transforms = {root: np.eye(4)}

    def transform(name, visited=()):
        assert name not in visited, 'Cyclic link tree'
        if name not in transforms:
            joint = children[name]
            parent = joint.find('parent').get('link')
            assert parent in links
            transforms[name] = transform(parent, visited + (name,)) @ origin(joint.find('origin'))
        return transforms[name]

    movable = [j for j in joints.values() if j.get('type') != 'fixed']
    mimic = {j.get('name'): j.find('mimic').attrib for j in movable if j.find('mimic') is not None}
    for name in mimic:
        visited = set()
        while name in mimic:
            assert name not in visited, 'Cyclic mimic tree'
            visited.add(name)
            name = mimic[name]['joint']
            assert name in joints
    for j in movable:
        limit = j.find('limit')
        assert limit is not None
        values = {k: float(limit.get(k)) for k in ['lower', 'upper', 'effort', 'velocity']}
        assert np.isfinite(list(values.values())).all()
        assert values['lower'] <= values['upper'] and values['effort'] > 0 and values['velocity'] > 0
    inertial_findings = []
    for name, link in links.items():
        inertia = link.find('inertial/inertia')
        if inertia is None:
            inertial_findings.append(dict(link=name, issue='no_inertial_element'))
            continue
        a = {k: float(v) for k, v in inertia.attrib.items()}
        matrix = np.array([[a['ixx'], a['ixy'], a['ixz']], [a['ixy'], a['iyy'], a['iyz']], [a['ixz'], a['iyz'], a['izz']]])
        mass = float(link.find('inertial/mass').get('value'))
        eigen = np.linalg.eigvalsh(matrix)
        if mass <= 0 or eigen[0] <= 0 or eigen[2] > eigen[:2].sum() + 1e-10:
            inertial_findings.append(dict(link=name, issue='mass_or_inertia_requires_review', mass=mass, principal_inertias=eigen.tolist()))
    materials = {m.get('name'): m.find('color').get('rgba') for m in robot.findall('material') if m.find('color') is not None}
    scene = trimesh.Scene()
    for name, link in links.items():
        transform(name)
        for index, visual in enumerate(link.findall('visual')):
            mesh_node = visual.find('geometry/mesh')
            assert mesh_node is not None, 'Unexpected primitive: ' + name
            mesh_path = path.parent / mesh_node.get('filename')
            mesh = trimesh.load(mesh_path, force='mesh', process=False)
            assert len(mesh.faces) and np.isfinite(mesh.vertices).all(), str(mesh_path)
            mesh.apply_scale(list(map(float, mesh_node.get('scale', '1 1 1').split())))
            mat = visual.find('material')
            rgba = '0.7 0.7 0.7 1'
            if mat is not None:
                rgba = mat.find('color').get('rgba') if mat.find('color') is not None else materials.get(mat.get('name'), rgba)
            mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
                baseColorFactor=np.array(list(map(float, rgba.split()))), metallicFactor=0, roughnessFactor=.65))
            scene.add_geometry(mesh, node_name=f'{name}_visual_{index}', geom_name=f'{name}_visual_{index}',
                               transform=transforms[name] @ origin(visual.find('origin')))
    source_bounds = scene.bounds.copy()
    floor_translation = -source_bounds[0, 2]
    scene.apply_translation([0, 0, floor_translation])
    (HERE / 'geometry').mkdir(exist_ok=True)
    preview = HERE / 'geometry/g1_inspire_ftp_zero.glb'
    preview.write_bytes(scene.export(file_type='glb'))
    # Export/reload is checked independently of the source traversal.
    reloaded = trimesh.load(preview, force='scene')
    assert np.allclose(reloaded.bounds, scene.bounds, atol=1e-6)
    mounts = [dict(name=j.get('name'), parent=j.find('parent').get('link'), child=j.find('child').get('link'),
                   origin=dict(j.find('origin').attrib)) for j in joints.values()
              if j.find('parent').get('link') in ['left_wrist_yaw_link', 'right_wrist_yaw_link']]
    assert len(mounts) == 2 and all(joints[m['name']].get('type') == 'fixed' for m in mounts)
    report = dict(schema_version=1, status='source_structure_audited_not_runtime_qualified',
        source_sha256=sha(HERE / 'SOURCE.json'), auditor_sha256=sha(__file__),
        checked_source_files=len(source['files']), mesh_files=source['mesh_count'],
        links=len(links), joints=len(joints), movable_joints=len(movable), mimic_joints=len(mimic),
        independent_joint_coordinates=len(movable)-len(mimic), mimic_relations=mimic, wrist_mounts=mounts,
        inertial_findings=inertial_findings,
        preview=dict(path=str(preview.relative_to(HERE)), sha256=sha(preview), bounds_m=scene.bounds.tolist(),
                     source_bounds_m=source_bounds.tolist(), source_to_preview_translation_m=[0, 0, float(floor_translation)],
                     units='metres', up_axis='Z', pose='all_joint_coordinates_zero_not_a_balance_solution',
                     material_scope='URDF colours; roughness 0.65 and zero metallic are display defaults'),
        limitations=['URDF mimic relations require explicit simulator mapping; 53 movable joints are not 53 independent commands',
                     'Source inertial values, collision geometry, friction, actuator response and force/tactile sensing are not calibrated',
                     'NVIDIA and Unitree example variants/joint namespaces require explicit mapping before reuse',
                     'No contact, balance, reachability, payload, camera or task qualification performed'])
    (HERE / 'VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['checked_source_files', 'mesh_files', 'links', 'movable_joints', 'mimic_joints', 'independent_joint_coordinates', 'inertial_findings']}))


if __name__ == '__main__':
    audit()
