"""Load locally built, hash-pinned collision geometry plugins before MJCF.

No model state or controller is modified. The receipt must identify the exact
engine binary and build sources used for each geometry-only plugin.
"""
from pathlib import Path

import mujoco

from build_tool_station import sha

_loaded = {}


def load_collision_plugins(receipts):
    for receipt in receipts:
        library = Path(receipt['library'])
        digest = sha(library)
        if digest != receipt['library_sha256']:
            raise ValueError('Collision plugin library changed: '+str(library))
        if receipt['mujoco_version'] != mujoco.__version__:
            raise ValueError('Collision plugin engine version differs')
        engines = list(Path(mujoco.__file__).parent.glob('libmujoco.so.*'))
        if len(engines) != 1 or sha(engines[0]) != receipt['engine_sha256']:
            raise ValueError('Collision plugin engine binary differs')
        for name, expected in receipt['source_sha256'].items():
            if Path(name).name != name or sha(library.parent/name) != expected:
                raise ValueError('Collision plugin source changed: '+name)
        name = receipt['plugin_name']
        if name in _loaded and _loaded[name] != digest:
            raise ValueError('Cannot replace an already registered collision plugin')
        if name not in _loaded:
            mujoco.mj_loadPluginLibrary(str(library))
            _loaded[name] = digest
