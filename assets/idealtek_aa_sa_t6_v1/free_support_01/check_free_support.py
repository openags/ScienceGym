"""Check a free passive tool settling on a support plane under gravity.

This is an asset-support check before robot pickup, not a grasp trial. The tool
keeps its six free-body coordinates, passive arm joints and manufacturer-sized
geometry. No heel mount, actuator, attachment equality or external force is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, output, orientation):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    asset = json.loads((source / 'model_review.json').read_text())
    assert asset['passed_geometry_and_compilation']
    tree = ET.parse(source / 'tool.xml')
    root = tree.getroot()
    root.find('compiler').set('meshdir', str(source / 'meshes'))
    root.find('option').set('gravity', '0 0 -9.81')
    world = root.find('worldbody')
    ET.SubElement(world, 'geom', name='support', type='plane', size='.3 .3 .01',
                  friction='.225 .002 .0001', solref='.001 1',
                  solimp='.9999 .9999 .00001', rgba='.6 .65 .68 1')
    ET.indent(tree)
    tree.write(output / 'support.xml', encoding='unicode')
    shutil.copyfile(__file__, output / Path(__file__).name)
    model = mujoco.MjModel.from_xml_path(str(output / 'support.xml'))
    data = mujoco.MjData(model)
    support = model.geom('support').id
    tool_geoms = [i for i in range(model.ngeom) if i != support]
    assert model.nu == 0 and model.neq == 0
    assert np.count_nonzero(model.jnt_type == mujoco.mjtJoint.mjJNT_FREE) == 1
    if orientation == 'broadside':
        data.qpos[3:7] = [2**-.5, 2**-.5, 0, 0]
    elif orientation != 'edge':
        raise ValueError(orientation)
    mujoco.mj_forward(model, data)
    minimum = np.inf
    for geom in tool_geoms:
        if model.geom_type[geom] == mujoco.mjtGeom.mjGEOM_MESH:
            mesh = model.geom_dataid[geom]
            vertices = model.mesh_vert[model.mesh_vertadr[mesh]:
                                       model.mesh_vertadr[mesh]+model.mesh_vertnum[mesh]]
            transformed = vertices @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]
            minimum = min(minimum, float(transformed[:, 2].min()))
        else:
            # The only non-mesh tool part is the rectangular joined heel.
            assert model.geom_type[geom] == mujoco.mjtGeom.mjGEOM_BOX
            dz = float(np.abs(data.geom_xmat[geom].reshape(3, 3)[2]) @ model.geom_size[geom])
            minimum = min(minimum, float(data.geom_xpos[geom, 2] - dz))
    # Authored initial condition only: a 0.2 mm settling gap above the plane.
    data.qpos[2] += .0002 - minimum
    mujoco.mj_forward(model, data)
    contract = dict(scope=__doc__, orientation=orientation, duration_s=2.,
                    settled_interval_s=[1.5, 2.], initial_drop_m=.0002,
                    initial_qpos=data.qpos.tolist(), timestep_s=float(model.opt.timestep),
                    gravity_m_s2=model.opt.gravity.tolist(),
                    acceptance=dict(maximum_support_penetration_m=.00025,
                        maximum_self_penetration_m=.00002,
                        maximum_settled_linear_speed_m_s=.001,
                        maximum_settled_angular_speed_rad_s=.01,
                        maximum_relative_mean_support_load_error=.05,
                        maximum_replay_position_error=1e-9,
                        maximum_replay_velocity_error=1e-8),
                    limitations=['Ideal flat support, not a complete instrument bench or tray',
                                 'The source tool has planar arm bending only; spatial torsion is not qualified'],
                    source_hashes={str(p):sha(p) for p in
                        [Path(__file__), source/'tool.xml', source/'model_review.json', output/'support.xml']})
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    recorded, contacts, violations = [], [], []
    penetration = 0.
    external = False
    def state():
        return (float(data.time), data.qpos.copy(), data.qvel.copy(), data.qacc_warmstart.copy())
    for i in range(round(contract['duration_s']/model.opt.timestep)):
        before = state()
        recorded.append(before)
        external |= bool(np.any(data.xfrc_applied) or np.any(data.qfrc_applied))
        mujoco.mj_step(model, data)
        # Contacts returned by mj_step are evaluated at the pre-integration
        # configuration; label these forces with that state's timestamp.
        load = 0.
        for index, contact in enumerate(data.contact):
            pair = list(map(int, contact.geom))
            if support in pair:
                force = np.zeros(6)
                mujoco.mj_contactForce(model, data, index, force)
                load += abs(float(force[0]))
                penetration = max(penetration, -float(contact.dist))
            elif contact.dist < -.00002 and len(violations) < 30:
                violations.append(dict(time_s=before[0], parts=[model.geom(g).name for g in pair],
                                       distance_m=float(contact.dist)))
        contacts.append(dict(time_s=before[0], normal_load_n=load))
        if np.any(data.warning.number):
            break
    recorded.append(state())
    trace = {key:np.asarray([r[j] for r in recorded]) for j,key in
             enumerate(['time','qpos','qvel','qacc_warmstart'])}
    np.savez_compressed(output/'trace.npz', **trace)
    replay = mujoco.MjData(model)
    replay.qpos[:] = trace['qpos'][0]
    replay.qvel[:] = trace['qvel'][0]
    mujoco.mj_forward(model, replay)
    replay.qacc_warmstart[:] = trace['qacc_warmstart'][0]
    q_error = v_error = 0.
    for i in range(len(recorded)-1):
        mujoco.mj_step(model, replay)
        q_error = max(q_error, float(np.max(abs(replay.qpos-trace['qpos'][i+1]))))
        v_error = max(v_error, float(np.max(abs(replay.qvel-trace['qvel'][i+1]))))
    selected = trace['time'] >= 1.5
    linear = float(np.max(np.linalg.norm(trace['qvel'][selected,:3], axis=1))) if selected.any() else float('inf')
    angular = float(np.max(np.linalg.norm(trace['qvel'][selected,3:6], axis=1))) if selected.any() else float('inf')
    loads = [r['normal_load_n'] for r in contacts if r['time_s'] >= 1.5]
    expected = float(model.body_mass.sum()*9.81)
    load_error = abs(float(np.mean(loads))/expected-1) if loads else float('inf')
    checks = dict(duration_completed=data.time >= 2.-1e-8,
                  no_numerical_warnings=not np.any(data.warning.number),
                  free_unactuated_tool=model.nu == 0 and model.neq == 0,
                  no_external_forces=not external,
                  support_penetration_bounded=penetration <= .00025,
                  no_unintended_self_penetration=not violations,
                  settled_linear_speed=linear <= .001, settled_angular_speed=angular <= .01,
                  settled_support_load=load_error <= .05,
                  exact_replay=q_error <= 1e-9 and v_error <= 1e-8)
    result = dict(passed=all(checks.values()), checks={k:bool(v) for k,v in checks.items()},
                  orientation=orientation, states=len(recorded), simulated_seconds=float(data.time),
                  maximum_support_penetration_m=penetration,
                  maximum_settled_linear_speed_m_s=linear, maximum_settled_angular_speed_rad_s=angular,
                  expected_weight_n=expected, relative_settled_support_load_error=load_error,
                  maximum_replay_q_error=q_error, maximum_replay_v_error=v_error,
                  final_qpos=data.qpos.tolist(), unintended_contacts=violations,
                  trace_sha256=sha(output/'trace.npz'), contract_sha256=sha(output/'contract.json'),
                  qualified_robot_grasp=False, qualified_paper_branch=False,
                  scope='Free tool support under gravity only; no pickup or source-force calibration credit')
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'final_qpos'}), flush=True)
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source');p.add_argument('output');p.add_argument('--orientation', choices=['edge','broadside'], default='edge')
    a=p.parse_args()
    if not run(a.source,a.output,a.orientation)['passed']:
        raise SystemExit(1)
