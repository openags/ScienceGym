"""Actively check the actor namespace before allowing any plant steps."""
import json
import os
from pathlib import Path
import sys


def main():
    forbidden = json.loads(sys.argv[1])
    blocked = {}
    for name in forbidden:
        try:
            with open(name, 'rb') as stream:
                stream.read(1)
            blocked[name] = False
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            blocked[name] = not Path(name).exists()
    readonly = {}
    for name in ['/actor/actor_feedback.py', '/model/world.xml']:
        try:
            with open(name, 'ab'):
                pass
            readonly[name] = False
        except OSError:
            readonly[name] = True
    scratch = Path('/tmp/actor_probe')
    scratch.write_text('private scratch')
    scratch_ok = scratch.read_text() == 'private scratch'
    scratch.unlink()
    namespaces = {name:os.readlink('/proc/self/ns/'+name) for name in ['mnt','pid','net']}
    status = dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    caps = int(status['CapEff'].strip(), 16)
    # Exercise the same graphics backend needed for the actor's depth residual.
    import mujoco
    model = mujoco.MjModel.from_xml_path('/model/world.xml')
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    renderer = mujoco.Renderer(model, height=32, width=32)
    renderer.update_scene(data, camera='head_depth')
    shape = list(renderer.render().shape)
    renderer.close()
    result = dict(forbidden_paths_blocked=blocked, inputs_readonly=readonly,
                  private_scratch_writable=scratch_ok, namespaces=namespaces,
                  effective_capabilities=caps, gpu_render_shape=shape,
                  model_nq=model.nq,
                  passed=all(blocked.values()) and all(readonly.values()) and scratch_ok and caps==0 and shape==[32,32,3])
    print(json.dumps(result))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
