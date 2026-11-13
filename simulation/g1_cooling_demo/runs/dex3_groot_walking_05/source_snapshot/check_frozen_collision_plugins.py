"""Compare legacy and frozen plugin loaders on the actual laboratory model.

Two fresh processes compile the same scene and execute ten native zero-torque
steps. This tests loading and deterministic compatibility, not support stability
or robot execution. Corrupt receipt tests must fail before library registration.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def child(scene, output, loader):
    binding = json.loads((scene/'binding.json').read_text())
    assert sha(scene/'world.xml') == binding['world_sha256']
    assert sha(scene/'initial_state.json') == binding['initial_state_sha256']
    for name, digest in json.loads((scene/'model_inputs.json').read_text()).items():
        assert sha(name) == digest
    receipts = binding['collision_plugins']
    rejected = []
    if loader == 'original':
        from runtime_collision_plugins import load_collision_plugins
        load_collision_plugins(receipts)
    else:
        import frozen_collision_plugins as module
        digest = sha(module.__file__)
        for field in ['loader', 'library_sha256', 'engine_sha256', 'source_sha256']:
            bad = copy.deepcopy(receipts)
            if field == 'source_sha256':
                key = next(iter(bad[0][field]))
                bad[0][field][key] = '0'*64
            elif field != 'loader':
                bad[0][field] = '0'*64
            try:
                module.load(bad, '0'*64 if field == 'loader' else digest)
            except ValueError:
                rejected.append(field)
            else:
                raise AssertionError('Invalid receipt was accepted: '+field)
        assert not module._loaded
        module.load(receipts, digest)
    m = mujoco.MjModel.from_xml_path(str(scene/'world.xml'))
    assert m.npluginstate == 0
    state = json.loads((scene/'initial_state.json').read_text())
    d = mujoco.MjData(m)
    d.qpos[:], d.qvel[:] = state['qpos'], state['qvel']
    mujoco.mj_forward(m, d)
    rows = []
    for _ in range(11):
        forces = []
        for i, c in enumerate(d.contact):
            force = np.zeros(6)
            mujoco.mj_contactForce(m, d, i, force)
            forces.append([*c.geom, c.dist, *force])
        rows.append((d.qpos.copy(), d.qvel.copy(), d.qacc.copy(), np.asarray(forces)))
        if len(rows) <= 10:
            mujoco.mj_step(m, d)
    arrays = {f'{k}_{i}': row[j] for i, row in enumerate(rows)
              for j, k in enumerate(['qpos', 'qvel', 'qacc', 'contacts'])}
    np.savez_compressed(output/(loader+'.npz'), **arrays)
    (output/(loader+'.json')).write_text(json.dumps(dict(
        rejected_invalid_receipts=rejected, nplugin=int(m.nplugin),
        npluginstate=int(m.npluginstate), steps=10, timestep_s=float(m.opt.timestep)), indent=2)+'\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--child-loader', choices=['original', 'frozen'])
    a = p.parse_args()
    scene, output = a.scene.resolve(), a.output.resolve()
    if a.child_loader:
        child(scene, output, a.child_loader)
        return
    output.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    sources = ['check_frozen_collision_plugins.py', 'frozen_collision_plugins.py',
               'runtime_collision_plugins.py', 'build_tool_station.py',
               'distal_contacts.py', 'partition_lab_collision.py']
    pins = {name: sha(here/name) for name in sources}
    for name in sources:
        shutil.copyfile(here/name, output/name)
    for loader in ['original', 'frozen']:
        assert all(sha(here/n) == h for n, h in pins.items())
        with (output/(loader+'.log')).open('w') as log:
            subprocess.run([sys.executable, '-B', str(__file__), str(scene), str(output),
                            '--child-loader', loader], check=True, stdout=log,
                           stderr=subprocess.STDOUT, env=dict(os.environ, OPENBLAS_NUM_THREADS='1'))
    with np.load(output/'original.npz') as original, np.load(output/'frozen.npz') as frozen:
        assert set(original.files) == set(frozen.files)
        exact = all(np.array_equal(original[k], frozen[k]) for k in original.files)
    checks = dict(exact_states_accelerations_contacts_and_forces=exact,
                  invalid_receipts_rejected=len(json.loads((output/'frozen.json').read_text())['rejected_invalid_receipts']) == 4)
    report = dict(scope=__doc__, passed=all(checks.values()), checks=checks,
                  world_sha256=sha(scene/'world.xml'), binding_sha256=sha(scene/'binding.json'),
                  source_sha256=pins, outputs_sha256={n: sha(output/n) for n in
                      ['original.npz', 'frozen.npz', 'original.json', 'frozen.json']},
                  qualified_robot_handling=False, qualified_paper_branch=False)
    (output/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
