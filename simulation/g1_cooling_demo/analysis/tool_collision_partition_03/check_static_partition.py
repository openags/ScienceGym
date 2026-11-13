"""Check a static geometry partition against the unchanged full scene."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from partition_lab_collision import partition


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, output, cell):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ['check_static_partition.py', 'partition_lab_collision.py']:
        shutil.copyfile(Path(__file__).parent/name, output/name)
    tree = ET.parse(source/'world.xml').getroot()
    before = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    excluded = {n.get(k) for n in tree.findall('contact/exclude') for k in ['body1', 'body2']}
    bodies = [before.body(b).name for b in range(1, before.nbody)
              if before.body_weldid[b] == 0 and before.body_geomnum[b] > 1 and before.body(b).name not in excluded]
    groups = {before.geom(g).name: '_'.join(map(str, np.floor(before.geom_pos[g]/cell).astype(int)))
              for g in range(before.ngeom) if before.body(int(before.geom_bodyid[g])).name in bodies}
    mapping = partition(tree, bodies, groups)
    ET.indent(tree); ET.ElementTree(tree).write(output/'world.xml', encoding='unicode')
    after = mujoco.MjModel.from_xml_path(str(output/'world.xml'))
    contract = json.loads((source/'contract.json').read_text())
    models = [before, after]; datas = []
    for m in models:
        d = mujoco.MjData(m); d.qpos[:] = contract['initial_qpos']; mujoco.mj_forward(m, d); datas.append(d)
    geom_errors = []; preserved = True; meshes = True
    for g in range(before.ngeom):
        h = after.geom(before.geom(g).name).id
        geom_errors.extend([float(np.max(abs(datas[0].geom(g).xpos-datas[1].geom(h).xpos))),
                            float(np.max(abs(datas[0].geom(g).xmat-datas[1].geom(h).xmat)))])
        for attr in ['geom_contype', 'geom_conaffinity', 'geom_priority', 'geom_condim',
                     'geom_friction', 'geom_solref', 'geom_solimp', 'geom_size', 'geom_rgba', 'geom_type', 'geom_margin', 'geom_gap']:
            preserved &= np.array_equal(getattr(before, attr)[g], getattr(after, attr)[h])
        if before.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
            meshes &= before.mesh(int(before.geom_dataid[g])).name == after.mesh(int(after.geom_dataid[h])).name
        if before.body_weldid[before.geom_bodyid[g]] == 0:
            preserved &= after.body_weldid[after.geom_bodyid[h]] == 0
    times, states, contacts = [], [], []
    for m, d in zip(models, datas):
        trajectory = []; contact_series = []; started = time.monotonic()
        for _ in range(100):
            mujoco.mj_step(m, d); trajectory.append(np.r_[d.qpos, d.qvel])
            contact_series.append(sorted((tuple(sorted(m.geom(int(g)).name for g in c.geom)), float(c.dist)) for c in d.contact))
        times.append(time.monotonic()-started); states.append(np.asarray(trajectory)); contacts.append(contact_series)
    checks = dict(geom_parameters_and_weld_groups_preserved=bool(preserved),
        same_source_mesh_bindings=bool(meshes), same_initial_geom_transforms=max(geom_errors) < 1e-12,
        unchanged_contact_history=contacts[0] == contacts[1],
        unchanged_sampled_trajectory=np.array_equal(states[0], states[1]))
    result = dict(scope='Compiled geometry correspondence and 100 zero-torque steps; no grasp or general dynamics qualification',
        source_model_sha256=sha(source/'world.xml'), source_contract_sha256=sha(source/'contract.json'),
        model_sha256=sha(output/'world.xml'), checks=checks, passed=all(checks.values()),
        cell_size_m=cell, body_counts=[m.nbody for m in models], mapping=mapping,
        seconds_original_partitioned=times, maximum_state_difference=float(np.max(abs(states[0]-states[1]))),
        maximum_initial_geom_transform_error=max(geom_errors), source_scripts={n: sha(output/n) for n in ['check_static_partition.py', 'partition_lab_collision.py']})
    np.savez_compressed(output/'comparison.npz', original=states[0], partitioned=states[1])
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'mapping'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('output')
    p.add_argument('--cell', type=float, default=.2); a = p.parse_args(); run(a.source, a.output, a.cell)
