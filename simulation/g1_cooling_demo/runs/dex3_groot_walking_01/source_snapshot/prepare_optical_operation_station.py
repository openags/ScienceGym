"""Join the visual tool-start contract to the complete passive optical scene.

This is an authored initial state for subsequent sensor-driven operations.
It preserves the original robot, tray and tweezer states, adds the scene's
free specimen/reference/cap, and retains unresolved asset qualifications.
No robot installation, sample preparation or manipulation is credited here.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from runtime_collision_plugins import load_collision_plugins


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_station', type=Path)
    p.add_argument('optical_scene', type=Path)
    p.add_argument('support_review', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--support-velocity-review',type=Path,
                   help='Independent velocity correction for the earlier support evaluator indexing defect')
    a = p.parse_args()
    source, scene, support, out = [v.resolve() for v in [
        a.source_station, a.optical_scene, a.support_review, a.output]]
    contract = json.loads((source/'contract.json').read_text())
    initial_review = json.loads((source/'review.json').read_text())
    binding = json.loads((scene/'binding.json').read_text())
    support_result = json.loads(support.read_text())
    assert contract['observed_approach'] and contract['hand_kind'] == 'unitree_three_finger'
    assert initial_review['passed_initial_scene_checks']
    assert initial_review['contract_sha256'] == sha(source/'contract.json')
    assert sha(source/'world.xml') == contract['plant_sha256'] == binding['base_model_sha256']
    assert sha(source/'robot_predictor.xml') == contract['predictor_sha256']
    assert sha(scene/'world.xml') == binding['world_sha256'] == support_result['world_sha256']
    assert sha(scene/'binding.json') == support_result['binding_sha256']
    assert sha(scene/'initial_state.json') == binding['initial_state_sha256']
    if not support_result['passed_asset_support']:
        raise ValueError('Complete-room passive support has not passed')
    assert sha(support.parent/'trace.npz') == support_result['trace_sha256']
    velocity_review=None
    affected_source='0bf415258da17e8cd3465514123f3ab963ea99ca2279d8042f583157870208db'
    if support_result.get('source_sha256')==affected_source and a.support_velocity_review is None:
        raise ValueError('This support evaluator requires the corrected specimen velocity replay')
    if a.support_velocity_review is not None:
        velocity_review=json.loads(a.support_velocity_review.read_text())
        assert velocity_review['original_review_sha256']==sha(support)
        assert velocity_review['world_sha256']==binding['world_sha256']
        assert velocity_review['retained_trace_sha256']==support_result['trace_sha256']
        assert sha(a.support_velocity_review.parent/'tail_velocities.npz')==velocity_review['tail_velocities_sha256']
        if not velocity_review['corrected_asset_support_passed']:
            raise ValueError('Corrected support velocity replay did not pass')
    inputs = {}
    for folder in [source, scene]:
        for path, digest in json.loads((folder/'model_inputs.json').read_text()).items():
            assert sha(path) == digest
            if path in inputs and inputs[path] != digest:
                raise ValueError('Source asset has conflicting identities')
            inputs[path] = digest
    plugins = binding.get('collision_plugins', [])
    load_collision_plugins(plugins)
    original = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    model = mujoco.MjModel.from_xml_path(str(scene/'world.xml'))
    for field in ['actuator_ctrlrange', 'actuator_forcerange', 'actuator_gear']:
        if not np.array_equal(getattr(original, field), getattr(model, field)):
            raise ValueError('Optical scene changes robot actuation: '+field)
    if model.nu != 43 or model.neq != original.neq:
        raise ValueError('Unexpected actuator or attachment constraint')
    initial = json.loads((scene/'initial_state.json').read_text())
    data = mujoco.MjData(model)
    data.qpos[:], data.qvel[:] = initial['qpos'], initial['qvel']
    source_data = mujoco.MjData(original)
    source_data.qpos[:], source_data.qvel[:] = contract['initial_qpos'], contract['initial_qvel']
    for j in range(original.njnt):
        name = original.joint(j).name
        data.joint(name).qpos[:] = source_data.joint(name).qpos
        data.joint(name).qvel[:] = source_data.joint(name).qvel
        if not np.array_equal(original.joint(name).range, model.joint(name).range):
            raise ValueError('Source joint limits changed: '+name)
    new_joints = {model.joint(j).name for j in range(model.njnt)} - {
        original.joint(j).name for j in range(original.njnt)}
    if new_joints != {'optical_witness_white_free', 'pike_reference_free', 'pike_reference_cap_free'}:
        raise ValueError('Unexpected added or missing passive object joints')
    for j in np.flatnonzero(model.jnt_limited):
        if not model.jnt_range[j, 0] <= data.qpos[model.jnt_qposadr[j]] <= model.jnt_range[j, 1]:
            raise ValueError('Initial joint lies outside its unchanged source range')
    mujoco.mj_forward(model, data)
    robot = {model.body('pelvis').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in robot:
            robot.add(b)
    bad = []
    for c in data.contact:
        parts = [model.geom(int(g)).name for g in c.geom]
        bodies = {int(model.geom_bodyid[g]) for g in c.geom}
        if not bodies.intersection(robot):
            continue
        bound = .001 if 'lab_part_1515' in parts and any('ankle_roll_link_collision' in n for n in parts) else .00002
        if c.dist < -bound:
            bad.append(dict(parts=parts, penetration_m=-float(c.dist), bound_m=bound))
    out.mkdir(parents=True, exist_ok=False)
    for path in [Path(__file__), Path(__file__).with_name('runtime_collision_plugins.py')]:
        shutil.copyfile(path, out/path.name)
    shutil.copyfile(scene/'world.xml', out/'world.xml')
    shutil.copyfile(source/'robot_predictor.xml', out/'robot_predictor.xml')
    for path, name in [(scene/'binding.json', 'optical_scene_binding.json'),
                       (support, 'optical_scene_support_review.json')]:
        shutil.copyfile(path, out/name)
        inputs[str(path)] = sha(path)
    if velocity_review is not None:
        shutil.copyfile(a.support_velocity_review,out/'optical_support_velocity_review.json')
        inputs[str(a.support_velocity_review.resolve())]=sha(a.support_velocity_review)
    (out/'model_inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    contract.update(scope=__doc__, source_station_contract_sha256=sha(source/'contract.json'),
        source_station_review_sha256=sha(source/'review.json'), plant_sha256=sha(out/'world.xml'),
        inputs_sha256=sha(out/'model_inputs.json'), initial_qpos=data.qpos.tolist(), initial_qvel=data.qvel.tolist(),
        collision_plugins=plugins, optical_scene_binding=dict(
            scene=str(scene), binding_sha256=sha(scene/'binding.json'),
            support_review_sha256=sha(support), source_passive_support_passed=True,
            support_velocity_review_sha256=sha(a.support_velocity_review) if velocity_review is not None else None,
            source_all_component_cases_passed=binding['passive_reference_binding']['all_component_cases_passed'],
            unresolved_asset_obligations=binding['unresolved'], actor_receives_object_truth=False,
            qualified_sample_reference_cap_handling=False), qualified_paper_branch=False)
    (out/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    review = dict(scope=__doc__, passed_initial_scene_checks=not bad, excessive_contacts=bad,
        original_robot_tool_tray_initial_states_preserved=True, original_actuation_preserved=True,
        added_free_objects=sorted(new_joints), plant_scene_unchanged=sha(out/'world.xml') == binding['world_sha256'],
        contract_sha256=sha(out/'contract.json'), physical_execution=False,
        qualified_approach=False, qualified_grasp=False, qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review), flush=True)
    if bad:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
