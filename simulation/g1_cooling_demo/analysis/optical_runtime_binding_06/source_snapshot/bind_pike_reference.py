"""Replace static PIKE reference/cap instances with passive bodies in the lab.

Initial poses retain the previously authored installation and storage positions.
This creates a scene for subsequent physical testing, not robot execution or
approval of inferred commercial-device dimensions and dynamics.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from build_tool_station import absolve_assets, free_pose, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('base_scene', type=Path)
    p.add_argument('reference_component', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--development-initial-state', action='store_true',
                   help='Bind only passed centered initial supports while retaining every failed offset as an unresolved limitation')
    a = p.parse_args()
    base, component, out = [v.resolve() for v in [a.base_scene, a.reference_component, a.output]]
    binding = json.loads((base/'binding.json').read_text())
    review = json.loads((component/'review.json').read_text())
    contract = json.loads((component/'contract.json').read_text())
    assert len(review['trials']) == 6
    centered = {t['case']:t['passed'] for t in review['trials'] if t['case'] in ['port_center','cap_center']}
    if not review['passed_component_support']:
        if not a.development_initial_state or centered != {'port_center':True,'cap_center':True}:
            raise ValueError('Component is incomplete; development binding requires passing both actual initial support configurations')
    assert sha(component/'contract.json') == review['contract_sha256']
    assert sha(component/'world.xml') == review['world_sha256'] == contract['world_sha256']
    assert sha(component/'support_traces.npz') == review['trace_sha256']
    assert sha(base/'world.xml') == binding['world_sha256']
    assert sha(base/'initial_state.json') == binding['initial_state_sha256']
    for folder in [base, component]:
        for path, digest in json.loads((folder/'model_inputs.json').read_text()).items():
            assert sha(path) == digest
    bm = mujoco.MjModel.from_xml_path(str(base/'world.xml'))
    bd = mujoco.MjData(bm)
    initial = json.loads((base/'initial_state.json').read_text())
    bd.qpos[:], bd.qvel[:] = initial['qpos'], initial['qvel']
    mujoco.mj_forward(bm, bd)
    xml = ET.parse(base/'world.xml').getroot()
    absolve_assets(xml, base/'world.xml')
    cx = ET.parse(component/'world.xml').getroot()
    absolve_assets(cx, component/'world.xml')
    parts = ['gold_reference_holder', 'gold_reference_shoulder', 'diffuse_gold_reference_face', 'reference_protective_cap']
    old = {n: xml.find(".//body[@name='installed_pike_"+n+"']") for n in parts}
    if any(body is None for body in old.values()):
        raise ValueError('Expected static reference/cap instances are missing')
    materials = {n: old[n].find('geom').get('material') for n in parts}
    poses = {}
    for new_name, old_name, key in [
            ('pike_reference', 'gold_reference_holder', 'source_reference_origin_normalized_m'),
            ('pike_reference_cap', 'reference_protective_cap', 'source_cap_origin_normalized_m')]:
        prior = bd.body('installed_pike_'+old_name)
        T = np.eye(4)
        T[:3, :3] = prior.xmat.reshape(3, 3)
        T[:3, 3] = prior.xpos+T[:3, :3]@np.asarray(contract[key])
        if new_name == 'pike_reference':
            yaw = -np.deg2rad(contract['initial_reference_yaw_degrees'])
            cs, sn = np.cos(yaw), np.sin(yaw)
            T[:3, :3] = T[:3, :3]@np.array([[cs, -sn, 0.], [sn, cs, 0.], [0., 0., 1.]])
        poses[new_name] = free_pose(T)
    parents = {child: parent for parent in xml.iter() for child in parent}
    removed = []
    for name, body in old.items():
        removed.append(dict(source_part=name, body=body.get('name'), geoms=[g.get('name') for g in body.iter('geom')]))
        parents[body].remove(body)
    material_mapping = dict(pike_reference_holder='gold_reference_holder',
        pike_reference_shoulder_visual='gold_reference_shoulder',
        pike_reference_optical_face='diffuse_gold_reference_face',
        pike_reference_cap_visual='reference_protective_cap')
    meshes = {n.get('name'): n for n in cx.findall('asset/mesh')}
    for name in poses:
        body = deepcopy(cx.find("worldbody/body[@name='"+name+"']"))
        assert body is not None and body.find('freejoint') is not None
        # Keep newly handled passive bodies dynamically integrated. The room
        # enables sleeping, which otherwise removes their reported support
        # forces once they settle; component force validation never slept them.
        body.set('sleep','never')
        for g in body.iter('geom'):
            asset = meshes[g.get('mesh')]
            if xml.find("asset/mesh[@name='"+asset.get('name')+"']") is not None:
                raise ValueError('Component mesh name collides with laboratory asset')
            xml.find('asset').append(deepcopy(asset))
            material = materials.get(material_mapping.get(g.get('name')))
            if material:
                g.set('material', material)
                g.attrib.pop('rgba', None)
        xml.find('worldbody').append(body)
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out/'source_snapshot'
    snapshot.mkdir()
    for path, name in [(Path(__file__), Path(__file__).name),
                       (base/'binding.json', 'base_binding.json'),
                       (component/'contract.json', 'reference_contract.json'),
                       (component/'review.json', 'reference_review.json')]:
        shutil.copyfile(path, snapshot/name)
    ET.indent(xml)
    ET.ElementTree(xml).write(out/'world.xml', encoding='unicode')
    m = mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    d = mujoco.MjData(m)
    for j in range(bm.njnt):
        name = bm.joint(j).name
        d.joint(name).qpos[:] = bd.joint(name).qpos
        d.joint(name).qvel[:] = bd.joint(name).qvel
    for name, q in poses.items():
        d.joint(name+'_free').qpos[:] = q
    mujoco.mj_forward(m, d)
    cap = d.body('pike_reference_cap')
    hit = np.array([-1], dtype=np.int32)
    ray_origin = cap.xpos+np.array([0., 0., .1])
    distance = mujoco.mj_ray(m, d, ray_origin, np.array([0., 0., -1.]), None, 1,
                            m.body('pike_reference_cap').id, hit)
    if distance < 0:
        raise ValueError('Reference cap has no existing scene support')
    cap_support = dict(geom=m.geom(int(hit[0])).name, body=m.body(int(m.geom_bodyid[hit[0]])).name,
                       point_work_m=(ray_origin+np.array([0., 0., -distance])).tolist())
    if m.nu != bm.nu or m.neq != bm.neq:
        raise ValueError('Passive reference binding changed robot actuators or equalities')
    (out/'initial_state.json').write_text(json.dumps(dict(qpos=d.qpos.tolist(), qvel=d.qvel.tolist(),
        scope='Authored initial configuration; no robot placement or support qualification'), indent=2)+'\n')
    inputs = {n.get('file'): sha(n.get('file')) for n in xml.find('asset') if n.get('file')}
    (out/'model_inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    binding.update(scope=__doc__, upstream_scene=str(base), upstream_binding_sha256=sha(base/'binding.json'),
        world_sha256=sha(out/'world.xml'), initial_state_sha256=sha(out/'initial_state.json'),
        model_inputs_sha256=sha(out/'model_inputs.json'),
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.iterdir()},
        passive_reference_binding=dict(component=str(component), component_review_sha256=sha(component/'review.json'),
            component_contract_sha256=sha(component/'contract.json'), removed_static_instances=removed,
            all_component_cases_passed=review['passed_component_support'],
            failed_component_cases=[t['case'] for t in review['trials'] if not t['passed']],
            development_initial_state_only=bool(a.development_initial_state),
            passive_body_sleep_policy='never',
            sleep_policy_basis='Keep passive support forces computed during the full-scene asset diagnostic and subsequent handling',
            free_body_initial_poses={n: q.tolist() for n, q in poses.items()},
            cap_initial_support=cap_support,
            selected_source_geometry_revision=contract['geometry_revision'],
            cap_geometry_source=contract['source_hashes'],
            component_test_release_gap_m=contract['initial_reference_release_gap_m'],
            component_test_cap_release_gap_m=contract['initial_cap_release_gap_m'],
            authored_reference_yaw_degrees=contract['initial_reference_yaw_degrees'],
            numeric_limitations=contract['numeric_limitations'],
            whole_scene_support_tested=False, robot_handling_tested=False,
            selected_scene_contact_cone=int(m.opt.cone), component_contact_cone='elliptic',
            component_qualification_transferred=False),
        qualified_installation=False, qualified_robot_handling=False, qualified_paper_branch=False)
    binding['unresolved'] = [v for v in binding['unresolved'] if not v.startswith('Gold reference and cap still')]
    binding['unresolved'].extend([
        'Reference/cap support must be checked in this complete room and its contact solver',
        'Robot reference/cap handling, supported release and optical contamination remain unqualified'])
    if not review['passed_component_support']:
        binding['unresolved'].append('Offset placement remains failed in the source component; this development initial-state binding does not waive that failure')
    (out/'binding.json').write_text(json.dumps(binding, indent=2)+'\n')
    print(json.dumps(dict(output=str(out), passive_bodies=list(poses), actuators=m.nu,
                          qualified_paper_branch=False)), flush=True)


if __name__ == '__main__':
    main()
