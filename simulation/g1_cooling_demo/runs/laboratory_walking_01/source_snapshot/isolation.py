"""Create a read-only actor bundle and enforce filesystem/PID/network isolation."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACTOR_MODULES = ['actor.py','actor_feedback.py','robot_state.py','balance.py',
                 'observations.py','tracking.py','policy.py','isolation_probe.py']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def namespace_prefix(code, model_dir):
    """Build the same access policy using this workstation's Python paths."""
    bwrap = shutil.which('bwrap')
    if not bwrap:
        raise RuntimeError('bubblewrap is required for the isolated sensor actor')
    command = [bwrap,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL',
               '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
               '--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache',
               '--proc','/proc','--dev','/dev','--tmpfs','/tmp']
    for prefix in sorted({sys.base_prefix, sys.prefix}):
        command += ['--ro-bind', prefix, prefix]
    for path in sorted(Path('/dev').glob('nvidia*')):
        command += ['--dev-bind', str(path), str(path)]
    if Path('/dev/dri').exists():
        command += ['--dev-bind','/dev/dri','/dev/dri']
    command += ['--ro-bind',str(Path(code).resolve()),'/actor',
                '--ro-bind',str(Path(model_dir).resolve()),'/model','--chdir','/actor']
    return command


def prepare(out, control_model, actor_command, *, extra_modules=(), policy_files=()):
    """Fail closed if the namespace or its active denial probes fail.

    The bundle deliberately excludes world construction, source task plans,
    simulation state, evaluators and recorded evidence. Its model is the
    caller's existing robot plus authored architectural prior only.
    """
    out, control_model = Path(out).resolve(), Path(control_model).resolve()
    bwrap = shutil.which('bwrap')
    if not bwrap:
        raise RuntimeError('bubblewrap is required for the isolated sensor actor')
    bundle = out/'actor_bundle'
    code, model_dir = bundle/'code', bundle/'model'
    code.mkdir(parents=True)
    model_dir.mkdir()
    modules = list(ACTOR_MODULES) + list(extra_modules)
    if any(Path(name).name != name or not name.endswith('.py') for name in modules):
        raise ValueError('Actor modules must be local Python module names')
    for name in modules:
        shutil.copyfile(HERE/name, code/name)
    xml = ET.parse(control_model).getroot()
    compiler = xml.find('compiler')
    files = []
    for kind, attribute, subdir in [('mesh','meshdir','meshes'), ('texture','texturedir','textures')]:
        directory = (control_model.parent/compiler.get(attribute,'')).resolve()
        destination = model_dir/subdir
        destination.mkdir()
        for item in xml.findall('asset/'+kind):
            filename = item.get('file')
            if not filename:
                continue
            source = (directory/filename).resolve()
            digest = sha(source)
            name = digest+source.suffix.lower()
            target = destination/name
            if not target.exists():
                shutil.copyfile(source, target)
            item.set('file', name)
            files.append(dict(path=str(target.relative_to(out)), sha256=digest))
        compiler.set(attribute, subdir)
    for source in map(Path, policy_files):
        target = model_dir/'policy'/source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        files.append(dict(path=str(target.relative_to(out)), sha256=sha(source)))
    ET.indent(xml)
    ET.ElementTree(xml).write(model_dir/'world.xml', encoding='unicode')
    # This engine-side audit happens before the bundle is exposed to the actor.
    import mujoco
    model = mujoco.MjModel.from_xml_path(str(model_dir/'world.xml'))
    names = {model.body(i).name for i in range(model.nbody)}
    prohibited = {'carrier_tray','calibration_copper_stock','buerkle_spatula'}
    if names & prohibited:
        raise RuntimeError('Handled object leaked into the actor model')
    if any(name.startswith('lab_') and name!='lab_architecture' for name in names):
        raise RuntimeError('Loose laboratory assets leaked into the actor model')
    if sum(model.jnt_type == mujoco.mjtJoint.mjJNT_FREE) != 1:
        raise RuntimeError('Actor model must contain only one floating robot')
    command = namespace_prefix(code, model_dir)
    environment = dict(PATH='/usr/bin:/bin', MUJOCO_GL='egl', OPENBLAS_NUM_THREADS='1', PYTHONNOUSERSITE='1')
    sentinel = out/'plant_only_sentinel'
    sentinel.write_bytes(os.urandom(32))
    forbidden = [str(sentinel), str(out/'world.xml'), str(out/'source_snapshot'),
                 str(ROOT/'tasks/directional_cooling_operations_v3/operations.json'),
                 str(ROOT/'simulation/g1_cooling_demo/verify_transport.py'),
                 f'/proc/{os.getpid()}']
    host_namespaces = {name:os.readlink('/proc/self/ns/'+name) for name in ['mnt','pid','net']}
    probe_command = command + [sys.executable, '/actor/isolation_probe.py', json.dumps(forbidden)]
    probe = subprocess.run(probe_command, env=environment, text=True, capture_output=True, timeout=90)
    try:
        result = json.loads(probe.stdout)
    except json.JSONDecodeError:
        result = dict(passed=False, stdout=probe.stdout)
    result['namespace_separation'] = {name: result.get('namespaces',{}).get(name) != value
                                      for name,value in host_namespaces.items()}
    result['passed'] = bool(result.get('passed') and probe.returncode==0 and all(result['namespace_separation'].values()))
    result.update(returncode=probe.returncode, stderr=probe.stderr,
                  source_model_sha256=sha(control_model), bundled_model_sha256=sha(model_dir/'world.xml'),
                  source_modules={name:sha(code/name) for name in modules},
                  input_files=sorted({r['path']:r for r in files}.values(),key=lambda r:r['path']),
                  isolation_source_sha256=sha(__file__), probe_source_sha256=sha(HERE/'isolation_probe.py'),
                  command_prefix=command, environment=environment,
                  scope='Filesystem, process and network namespace access restriction; not sensor calibration or task qualification')
    (out/'actor_isolation.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed']:
        raise RuntimeError('Actor isolation probe failed; see actor_isolation.json')
    args = list(actor_command[2:])
    args[args.index('--model')+1] = '/model/world.xml'
    executable = Path(actor_command[1]).name
    return command + [sys.executable, '/actor/'+executable] + args, environment, result


def restore_inputs(folder):
    """Recreate ignored bundle inputs without changing recorded code or models."""
    folder = Path(folder).resolve()
    receipt = json.loads((folder/'actor_isolation.json').read_text())
    xml_path = folder/'controller_model/world.xml'
    xml = ET.parse(xml_path).getroot()
    if sha(xml_path) != receipt['source_model_sha256']:
        raise ValueError('Recorded controller model changed')
    available = {}
    for kind, attribute in [('mesh','meshdir'), ('texture','texturedir')]:
        directory = (xml_path.parent/xml.find('compiler').get(attribute,'')).resolve()
        for node in xml.findall('asset/'+kind):
            if node.get('file'):
                source = (directory/node.get('file')).resolve()
                available[sha(source)] = source
    model_dir = folder/'actor_bundle/model'
    if (folder/'policy_source').is_dir():
        for source in (folder/'policy_source').rglob('*'):
            if source.is_file(): available[sha(source)] = source
    for row in receipt['input_files']:
        target = (folder/row['path']).resolve()
        if not target.is_relative_to(model_dir) or target.parent.name not in {'meshes','textures','policy'}:
            raise ValueError('Unexpected bundle target')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            shutil.copyfile(available[row['sha256']], target)
        if sha(target) != row['sha256']:
            raise ValueError('Bundle input changed: '+str(target))
    print('Restored', len(receipt['input_files']), 'actor input files')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--restore-inputs',required=True)
    restore_inputs(parser.parse_args().restore_inputs)
