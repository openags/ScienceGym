"""Stage the source free tweezer/tray with the full G1 in the existing lab.

This is an authored initial condition for arm/finger coordination development.
It grants no placement, approach, grasp, standing or paper-branch execution.
The original room remains; the two explicitly replaced static stock instances
are removed to avoid displaying duplicate white-tray/tweezer identities.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numbers(values): return ' '.join(format(float(v), '.17g') for v in values)


def pose(q):
    result = np.eye(4)
    result[:3, :3] = Rotation.from_quat(np.r_[q[4:7], q[3]]).as_matrix()
    result[:3, 3] = q[:3]
    return result


def free_pose(matrix):
    q = Rotation.from_matrix(matrix[:3, :3]).as_quat()
    return np.r_[matrix[:3, 3], q[3], q[:3]]


def absolve_assets(xml, path):
    compiler = xml.find('compiler')
    for kind, attribute in [('mesh', 'meshdir'), ('texture', 'texturedir'), ('hfield', None)]:
        directory = path.parent/compiler.get(attribute, '') if attribute else path.parent
        for node in xml.findall('asset/'+kind):
            if node.get('file'):
                target = (directory/node.get('file')).resolve()
                if not target.is_file(): raise FileNotFoundError(target)
                node.set('file', str(target))
    for attribute in ['meshdir', 'texturedir']:
        compiler.attrib.pop(attribute, None)


def build(reach_path, fit_path, output):
    reach_path, fit_path, output = [Path(p).resolve() for p in (reach_path, fit_path, output)]
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output/'source_snapshot'; snapshot.mkdir()
    shutil.copyfile(__file__, snapshot/Path(__file__).name)
    reach = json.loads(reach_path.read_text())
    reach_contract_path = reach_path.parent/'contract.json'
    assert sha(reach_contract_path) == reach['contract_sha256']
    reach_contract = json.loads(reach_contract_path.read_text())
    assert sha(fit_path) == reach_contract['fit_sha256']
    fit = json.loads(fit_path.read_text())
    fit_contract_path = fit_path.parent/'contract.json'
    assert sha(fit_contract_path) == fit['contract_sha256']
    fit_contract = json.loads(fit_contract_path.read_text())
    support_path = ROOT/fit_contract['support_review']
    assert sha(support_path) == fit_contract['support_review_sha256']
    support = json.loads(support_path.read_text()); assert support['passed']
    support_contract_path = support_path.parent/'contract.json'
    assert sha(support_contract_path) == support['contract_sha256']
    support_contract = json.loads(support_contract_path.read_text())
    assert 'tray_final_qpos' in support
    support_xml_path = support_path.parent/'support.xml'
    assert sha(support_xml_path) == support_contract['plant_sha256']
    for name, digest in support_contract['source_hashes'].items(): assert sha(ROOT/name) == digest
    candidate = min(reach['candidates'], key=lambda c: c['position_error_m'])
    assert candidate['full_scene_static_clear']
    pregrasp_index = reach_contract.get('pregrasp_index')
    hand = fit['candidates'][0] if pregrasp_index is None else fit['nearest_candidates'][pregrasp_index]
    baseline = HERE/'runs/ftir_approach_11'
    plant_path = baseline/'world.xml'; predictor_path = baseline/'controller_model/world.xml'
    assert sha(plant_path) == reach_contract['plant_sha256']
    assert sha(predictor_path) == reach_contract['predictor_sha256']
    imported_path = baseline/'laboratory_import.json'
    assert sha(imported_path) == reach_contract['laboratory_import_sha256']
    imported = json.loads(imported_path.read_text())
    xml = ET.parse(plant_path).getroot(); absolve_assets(xml, plant_path)
    support_xml = ET.parse(support_xml_path).getroot(); absolve_assets(support_xml, support_xml_path)
    # Remove precisely these two static initial-stock instances. All other
    # source room and equipment bodies remain in the baseline tree.
    parents = {child: parent for parent in xml.iter() for child in parent}
    replaced = []
    for name in ['lab_tray_white', 'lab_tweezers_white']:
        body = xml.find(f".//body[@name='{name}']")
        if body is None: raise ValueError('Expected initial-stock instance missing: '+name)
        replaced.append(dict(body=name, source_xml_sha256=hashlib.sha256(ET.tostring(body)).hexdigest(),
                             geoms=[g.get('name') for g in body.iter('geom')]))
        parents[body].remove(body)
    defaults = xml.find('default')
    if defaults is None: defaults = ET.SubElement(xml, 'default')
    for node in support_xml.findall('default/default'):
        assert node.get('class') and xml.find(f".//default[@class='{node.get('class')}']") is None
        defaults.append(deepcopy(node))
    # This changes the full plant's integration profile and must therefore be
    # requalified. No earlier standing/walking result is transferred.
    before_option = dict(xml.find('option').attrib)
    xml.find('option').attrib.update(support_xml.find('option').attrib)
    lab_from_work = np.asarray(reach_contract['lab_from_work'])
    lab_from_rig = np.eye(4)
    lab_from_rig[:3, 3] = reach_contract['tool_rig_lab_position_m']
    lab_from_rig[:3, :3] = Rotation.from_euler('z', candidate['tool_lab_yaw_rad']).as_matrix()
    work_from_rig = np.linalg.inv(lab_from_work)@lab_from_rig
    free_states = {'tweezer': support['tool_final_qpos'], 'carrier_tray': support['tray_final_qpos']}
    imported_meshes = set()
    for name, state in free_states.items():
        body = deepcopy(support_xml.find(f"worldbody/body[@name='{name}']"))
        assert body is not None and body.find('freejoint') is not None
        q = free_pose(work_from_rig@pose(np.asarray(state[:7])))
        body.set('pos', numbers(q[:3])); body.set('quat', numbers(q[3:7]))
        imported_meshes.update(g.get('mesh') for g in body.iter('geom') if g.get('mesh'))
        xml.find('worldbody').append(body)
    for node in support_xml.find('asset'):
        if node.get('name') in imported_meshes:
            assert xml.find(f"asset/*[@name='{node.get('name')}']") is None
            xml.find('asset').append(deepcopy(node))
    model_path = output/'world.xml'
    ET.indent(xml); ET.ElementTree(xml).write(model_path, encoding='unicode')
    predictor = ET.parse(predictor_path).getroot(); absolve_assets(predictor, predictor_path)
    ET.indent(predictor); ET.ElementTree(predictor).write(output/'robot_predictor.xml', encoding='unicode')
    model = mujoco.MjModel.from_xml_path(str(model_path)); data = mujoco.MjData(model)
    robot = mujoco.MjModel.from_xml_path(str(output/'robot_predictor.xml'))
    assert len(candidate['robot_qpos']) == robot.nq
    for j in range(robot.njnt):
        name = robot.joint(j).name; width = 7 if robot.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE else 1
        start = int(robot.jnt_qposadr[j]); data.joint(name).qpos[:] = candidate['robot_qpos'][start:start+width]
    reference = mujoco.MjModel.from_xml_path(str(support_xml_path))
    original = mujoco.MjData(reference); original.qpos[:] = support['full_final_qpos']
    mujoco.mj_forward(reference, original)
    for j in range(reference.njnt):
        name = reference.joint(j).name; values = original.joint(name).qpos.copy()
        if reference.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE: values = free_pose(work_from_rig@pose(values))
        data.joint(name).qpos[:] = values
    mujoco.mj_forward(model, data)
    expected_palm = work_from_rig@pose(np.asarray(support['tool_final_qpos'][:7]))
    offset = np.eye(4); offset[:3, 3] = [-.13, 0, -.00575]
    expected_palm = expected_palm@offset@np.asarray(hand['source_tool_from_palm'])
    actual_palm = np.eye(4); actual_palm[:3, 3] = data.body('right_palm_force_sensor').xpos
    actual_palm[:3, :3] = data.body('right_palm_force_sensor').xmat.reshape(3, 3)
    placement_errors = []; preserved = {}
    for g in range(reference.ngeom):
        name = reference.geom(g).name
        if name == 'support_plane': continue
        current = model.geom(name).id
        expected = work_from_rig[:3, :3]@original.geom(g).xpos+work_from_rig[:3, 3]
        placement_errors.append(float(np.linalg.norm(expected-data.geom(current).xpos)))
        preserved[name] = {attr: bool(np.array_equal(getattr(reference, attr)[g], getattr(model, attr)[current]))
                           for attr in ['geom_priority', 'geom_condim', 'geom_friction', 'geom_solref', 'geom_solimp', 'geom_contype', 'geom_conaffinity']}
    # Find the actual existing horizontal support under the proposed tray.
    ray_origin = work_from_rig[:3, 3].copy(); ray_origin[2] += .4
    base_model = mujoco.MjModel.from_xml_path(str(plant_path)); base_data = mujoco.MjData(base_model)
    mujoco.mj_forward(base_model, base_data)
    geom_id = np.array([-1], dtype=np.int32)
    distance = mujoco.mj_ray(base_model, base_data, ray_origin, np.array([0., 0., -1.]),
                            np.array([0, 0, 1, 0, 0, 0], dtype=np.uint8), True, -1, geom_id)
    support_geom_name = base_model.geom(int(geom_id[0])).name if geom_id[0] >= 0 else None
    support_z = float(ray_origin[2]-distance) if distance >= 0 else None
    source_part = next((p for p in imported['parts'] if p['geom'] == support_geom_name), None)
    floor_names = set(reach_contract['floor_geoms'])
    robot_bodies = {model.body('pelvis').id}; tool_bodies = {model.body('tweezer').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in robot_bodies: robot_bodies.add(b)
        if model.body_parentid[b] in tool_bodies: tool_bodies.add(b)
    tray_body = model.body('carrier_tray').id
    contacts = []; bad = []
    for c in data.contact:
        bodies = [int(model.geom_bodyid[g]) for g in c.geom]
        if not any(b in robot_bodies or b in tool_bodies or b == tray_body for b in bodies): continue
        names = [model.geom(int(g)).name for g in c.geom]
        sole = any('ankle_roll_link_collision' in n for n in names) and bool(set(names)&floor_names)
        tool_tray = tray_body in bodies and bool(set(bodies)&tool_bodies)
        tray_bench = tray_body in bodies and support_geom_name in names
        limit = .001 if sole else .00025 if tool_tray or tray_bench else .00002
        row = dict(parts=names, signed_distance_m=float(c.dist), limit_m=limit,
                   kind='sole_floor' if sole else 'tool_tray' if tool_tray else 'tray_bench' if tray_bench else 'other')
        contacts.append(row)
        if c.dist < -limit: bad.append(row)
    inputs = {}
    for tree in [xml, predictor]:
        for node in tree.findall('asset/*'):
            if node.get('file'): inputs[node.get('file')] = sha(node.get('file'))
    (output/'model_inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    contract = dict(scope=__doc__, reach_review_sha256=sha(reach_path), fit_review_sha256=sha(fit_path),
        support_review_sha256=sha(support_path), baseline_model_sha256=sha(plant_path),
        baseline_predictor_sha256=sha(predictor_path), laboratory_import_sha256=sha(imported_path),
        script_sha256=sha(snapshot/Path(__file__).name), plant_sha256=sha(model_path),
        predictor_sha256=sha(output/'robot_predictor.xml'), inputs_sha256=sha(output/'model_inputs.json'),
        source_support_options=support_xml.find('option').attrib, previous_plant_options=before_option,
        work_from_rig=work_from_rig.tolist(), replaced_static_instances=replaced,
        instance_mapping={'tray_white': 'carrier_tray', 'tweezers_white': 'tweezer'},
        initial_qpos=data.qpos.tolist(), initial_qvel=data.qvel.tolist(),
        initial_stock_staging_is_not_executed_transport=True,
        full_body_integration_changed_and_requires_requalification=True)
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    checks = dict(source_contact_parameters_preserved=all(all(v.values()) for v in preserved.values()),
        free_tool_and_tray=True, only_robot_actuators=model.nu == robot.nu == 41,
        only_robot_equalities=model.neq == robot.neq,
        geometry_transform=max(placement_errors) < 1e-8,
        palm_target=np.max(abs(expected_palm-actual_palm)) < .0002,
        actual_bench_at_declared_height=support_z is not None and abs(support_z-work_from_rig[2, 3]) < .0001,
        initial_contact_bounds=not bad)
    report = dict(scope=__doc__, passed_initial_scene_checks=bool(all(checks.values())),
        checks={k: bool(v) for k, v in checks.items()}, support_geom=support_geom_name,
        support_source_part=source_part, measured_support_height_m=support_z,
        maximum_passive_geometry_transform_error_m=max(placement_errors),
        maximum_palm_transform_error=float(np.max(abs(expected_palm-actual_palm))),
        source_contact_preservation=preserved, contacts=contacts, excessive_contacts=bad,
        contract_sha256=sha(output/'contract.json'), qualified_grasp=False, qualified_paper_branch=False)
    (output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['passed_initial_scene_checks', 'checks', 'measured_support_height_m', 'support_geom', 'excessive_contacts']}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('reach'); parser.add_argument('fit'); parser.add_argument('output')
    args = parser.parse_args(); build(args.reach, args.fit, args.output)
