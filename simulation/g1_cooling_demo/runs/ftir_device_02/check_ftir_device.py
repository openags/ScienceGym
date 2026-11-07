"""Independent plant-only checks, without awarding robot execution credit.

Sweep the compiled collision geometry and physically press each key with a
separate diagnostic probe. Device joints have no actuator. Truth is read only
by this evaluator; none of these probe inputs are a robot policy observation.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def values(v):
    return ' '.join(format(float(x), '.12g') for x in v)


def inspect(folder, probes=True):
    folder = Path(folder).resolve()
    source = folder / 'world.xml'
    model = mujoco.MjModel.from_xml_path(str(source))
    data = mujoco.MjData(model)
    imported = json.loads((folder/'laboratory_import.json').read_text())
    mechanism = json.loads((folder/'ftir_device.json').read_text())
    labels = {model.geom(g).id: part['source_part'] for part in imported['parts']
              if part['instance'] == 'nicolet'
              for g in [part['geom']] + part.get('contact_geoms', [])}
    dynamic = {i for i in labels if model.body_weldid[model.geom_bodyid[i]] != 0}
    sweeps, failures = [], []
    conditions = [(dict(nicolet_cover_hinge=float(q)), 'cover') for q in np.linspace(0, -np.pi/2, 181)]
    conditions += [(dict(nicolet_cover_hinge=-np.deg2rad(65), nicolet_door_slide=float(q)), 'door')
                   for q in np.linspace(0, .104, 105)]
    conditions += [(dict(**{'nicolet_key_slide_'+str(k):float(q)}), 'key_'+str(k))
                   for k in range(4) for q in np.linspace(0, .0003, 31)]
    for state, kind in conditions:
        mujoco.mj_resetData(model, data)
        for name, q in state.items():
            data.joint(name).qpos[0] = q
        mujoco.mj_forward(model, data)
        collisions = {}
        for contact in data.contact:
            a, b = map(int, contact.geom)
            if (a in dynamic or b in dynamic) and contact.dist < -2e-6:
                pair = tuple(sorted([labels.get(a, model.geom(a).name), labels.get(b, model.geom(b).name)]))
                collisions[pair] = min(collisions.get(pair, 0), float(contact.dist))
        row = dict(kind=kind, state=state, contacts=[dict(parts=list(p), distance_m=d) for p,d in collisions.items()])
        sweeps.append(row)
        if collisions: failures.append(row)
    (folder/'mechanism_sweep.json').write_text(json.dumps(sweeps, indent=2)+'\n')
    print('sweep', len(sweeps), 'failed_states', len(failures), flush=True)
    mujoco.mj_resetData(model, data); mujoco.mj_forward(model, data)
    device_joints = {model.joint(i).id for i in range(model.njnt) if model.joint(i).name.startswith('nicolet_')}
    no_actuator = not any(int(model.actuator_trnid[i,0]) in device_joints for i in range(model.nu))
    probe_results = []
    if probes:
        for index in range(4):
            probe_results.append(press_key(folder, index, model, data))
    checks = dict(compiled_device_has_six_passive_joints=len(device_joints)==6 and no_actuator,
                  sweep_has_no_unintended_penetration=not failures,
                  four_contact_presses_and_returns=len(probe_results)==4 and all(r['passed'] for r in probe_results))
    report = dict(scope='Full-laboratory passive-device engineering checks; diagnostic probes are not robot execution.',
                  passed=all(checks.values()), checks=checks, source_world_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  state_count=len(sweeps), failed_states=len(failures), first_failures=failures[:12],
                  key_probes=probe_results, inferred_dynamics=True, qualified_robot_skills=0,
                  qualified_paper_branches=0)
    (folder/'device_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    shutil.copyfile(__file__, folder/'check_ftir_device.py')
    print(json.dumps(report, indent=2), flush=True)
    return report


def probe_xml(folder):
    tree = ET.parse(folder/'world.xml')
    xml = tree.getroot()
    # Device diagnostics have no controlled robot. The complete laboratory
    # and instrument collision meshes are retained unchanged.
    world = xml.find('worldbody')
    world.remove(world.find("body[@name='pelvis']"))
    for tag in ['actuator', 'sensor', 'equality', 'keyframe']:
        node = xml.find(tag)
        if node is not None: xml.remove(node)
    contact = xml.find('contact')
    if contact is not None:
        for node in list(contact):
            if not all(node.get(k,'').startswith('lab_') for k in ['geom1','geom2']):
                contact.remove(node)
    xml.find('option').set('timestep', '.0005')
    return xml


def press_key(folder, index, full_model, full_data):
    xml = probe_xml(folder)
    key = 'nicolet_key_slide_' + str(index)
    jid = full_model.joint(key).id
    bodyid = full_model.jnt_bodyid[jid]
    frame = full_data.body(bodyid).xmat.reshape(3,3)
    axis = frame @ full_model.jnt_axis[jid]
    center = full_data.body(bodyid).xpos.copy()
    # Source key is 1.5 mm thick. Place a 4 mm radius probe 2 mm off its face.
    position = center - axis*(.00075+.004+.002)
    probe = ET.SubElement(xml.find('worldbody'), 'body', name='diagnostic_probe', pos=values(position))
    ET.SubElement(probe, 'joint', name='diagnostic_probe_slide', type='slide', axis=values(axis), damping='1')
    ET.SubElement(probe, 'inertial', pos='0 0 0', mass='.02', diaginertia='1e-6 1e-6 1e-6')
    ET.SubElement(probe, 'geom', name='diagnostic_probe_contact', type='sphere', size='.004',
                  rgba='.9 .4 .1 1', friction='.6 .005 .0001', solref='.004 1', solimp='.99 .99 .0005')
    actuator = ET.SubElement(xml, 'actuator')
    ET.SubElement(actuator, 'position', name='diagnostic_probe_motor', joint='diagnostic_probe_slide',
                  kp='2000', kv='10', forcerange='-3 3')
    path = folder/f'key_probe_{index}.xml'
    ET.indent(xml); ET.ElementTree(xml).write(path, encoding='unicode')
    model = mujoco.MjModel.from_xml_path(str(path)); data = mujoco.MjData(model)
    key_geom = model.geom(next(p['geom'] for p in json.loads((folder/'laboratory_import.json').read_text())['parts']
                               if p['instance']=='nicolet' and p['source_part']=='scan_key_'+str(index))).id
    probe_geom = model.geom('diagnostic_probe_contact').id
    trace, target_contacts, wrong_contacts, worst_depth = [], 0, set(), 0.
    for _ in range(2400):
        t = float(data.time)
        command = 0. if t < .1 or t > .8 else .0033 * min(1., (t-.1)/.2)
        data.ctrl[0] = command
        mujoco.mj_step(model, data)
        trace.append([t, float(data.joint(key).qpos[0]), float(data.joint('diagnostic_probe_slide').qpos[0]), float(data.actuator_force[0])])
        for c in data.contact:
            geoms = set(map(int, c.geom))
            if probe_geom in geoms:
                if key_geom in geoms:
                    target_contacts += 1
                    worst_depth = min(worst_depth, float(c.dist))
                else: wrong_contacts.add(tuple(model.geom(i).name for i in sorted(geoms)))
    trace = np.asarray(trace)
    np.savez_compressed(folder/f'key_probe_{index}_trace.npz', columns=np.array(['time_s','key_travel_m','probe_travel_m','probe_force_n']), values=trace)
    maximum, final = float(trace[:,1].max()), float(trace[-1,1])
    passed = (target_contacts>0 and maximum >= .00024 and maximum <= .00035 and abs(final)<.00005
              and not wrong_contacts and np.isfinite(trace).all() and not np.any(data.warning.number))
    result = dict(index=index, passed=bool(passed), maximum_travel_m=maximum, final_travel_m=final,
                  target_contact_samples=target_contacts, unintended_probe_pairs=sorted(wrong_contacts),
                  maximum_contact_penetration_m=-worst_depth, max_probe_force_n=float(abs(trace[:,3]).max()),
                  device_joint_forces_applied=False, external_probe_is_diagnostic=True)
    print('key_probe',json.dumps(result),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('--scan-only', action='store_true')
    args = parser.parse_args()
    if not inspect(args.folder, not args.scan_only)['passed']:
        raise SystemExit(1)
