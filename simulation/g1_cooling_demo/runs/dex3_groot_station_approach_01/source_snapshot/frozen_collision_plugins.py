"""Load pinned, stateless collision geometry for a frozen tool execution.

This plant/evaluator helper deliberately has no scene-builder dependencies.
It is excluded from the isolated actor bundle. Receipts bind the native library,
its source files and the MuJoCo binary; no object state is supplied to the actor.
"""
import hashlib
from pathlib import Path

import mujoco


_loaded = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(receipts, expected_loader_sha256):
    if sha(__file__) != expected_loader_sha256:
        raise ValueError('Collision plugin loader differs from the frozen contract')
    engines = list(Path(mujoco.__file__).parent.glob('libmujoco.so.*'))
    if len(engines) != 1:
        raise ValueError('Cannot identify the MuJoCo engine binary')
    engine_digest = sha(engines[0])
    # Validate the entire set before registering any native library.
    checked = {}
    for receipt in receipts:
        library = Path(receipt['library'])
        digest = sha(library)
        if digest != receipt['library_sha256']:
            raise ValueError('Collision plugin library changed: '+str(library))
        if receipt['mujoco_version'] != mujoco.__version__ or receipt['engine_sha256'] != engine_digest:
            raise ValueError('Collision plugin engine differs')
        for name, expected in receipt['source_sha256'].items():
            if Path(name).name != name or sha(library.parent/name) != expected:
                raise ValueError('Collision plugin source changed: '+name)
        name = receipt['plugin_name']
        if name in checked or (name in _loaded and _loaded[name] != digest):
            raise ValueError('Conflicting collision plugin identity: '+name)
        checked[name] = (library, digest)
    for name, (library, digest) in checked.items():
        if name not in _loaded:
            mujoco.mj_loadPluginLibrary(str(library))
            _loaded[name] = digest


def require_stateless(model):
    if model.npluginstate != 0:
        raise ValueError('Tool replay requires stateless collision geometry plugins')
