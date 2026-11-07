"""Compile a distinct collision implementation with unchanged source geometry.

The original plugin remains intact. Copy its exact geometry arrays, changing
only the registered name, and compile the selected implementation into a new
library. This is a candidate; it requires independent numerical comparison.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from frozen_collision_plugins import load, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    original,out=a.original.resolve(),a.output.resolve()
    prior=json.loads((original/'plugin.json').read_text())
    here=Path(__file__).resolve().parent
    parents=prior.get('parent_collision_plugins',[])
    load([*parents,prior],sha(here/'frozen_collision_plugins.py'))
    assert sha(original/'world.xml')==prior['world_sha256']
    implementation=here/'pike_surface_sdf.cc'
    name=prior['plugin_name']+'_'+sha(implementation)[:8]
    assert name!=prior['plugin_name']
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),implementation,here/'frozen_collision_plugins.py']:
        shutil.copyfile(path,out/path.name)
    shutil.copyfile(original/'plugin.json',out/'original_plugin.json')
    old_header=(original/'pike_surface_geometry.h').read_text()
    old_name='static constexpr char kPluginName[]="'+prior['plugin_name']+'";'
    assert old_header.count(old_name)==1
    header=old_header.replace(old_name,'static constexpr char kPluginName[]="'+name+'";')
    (out/'pike_surface_geometry.h').write_text(header)
    package=Path(mujoco.__file__).parent
    engines=list(package.glob('libmujoco.so.*'));assert len(engines)==1
    assert sha(engines[0])==prior['engine_sha256']
    library=out/'libsciencegym_pike_surface.so'
    command=['g++','-std=c++17','-O3','-shared','-fPIC','-Wall','-Wextra',
        '-I'+str(package/'include'),str(out/implementation.name),str(engines[0]),
        '-Wl,-rpath,'+str(package),'-o',str(library)]
    # Older through-bore headers have no floor. Preserve their original
    # occupancy function exactly rather than inventing a recess floor.
    through_bore = 'kBoreFloor' not in old_header
    if through_bore:
        assert 'kBoreFloor' not in (original/'pike_surface_sdf.cc').read_text()
        command.insert(1, '-DSCIENCEGYM_THROUGH_BORE')
    compiled=subprocess.run(command,capture_output=True,text=True)
    (out/'build.log').write_text(compiled.stdout+compiled.stderr);compiled.check_returncode()
    mujoco.mj_loadPluginLibrary(str(library))
    xml=ET.parse(original/'world.xml')
    nodes=xml.getroot().findall("extension/plugin[@plugin='"+prior['plugin_name']+"']")
    assert len(nodes)==1
    nodes[0].set('plugin',name)
    xml.write(out/'world.xml',encoding='unicode')
    before=mujoco.MjModel.from_xml_path(str(original/'world.xml'))
    after=mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    fields=['body_mass','body_inertia','body_ipos','body_iquat','geom_type','geom_size',
            'geom_pos','geom_quat','mesh_vert','mesh_face','qpos0']
    assert all(np.array_equal(getattr(before,f),getattr(after,f)) for f in fields)
    receipt=dict(prior)
    receipt.update(scope=__doc__,plugin_name=name,library=str(library),library_sha256=sha(library),
        world_sha256=sha(out/'world.xml'),source_world_sha256=prior['world_sha256'],
        original_receipt_sha256=sha(original/'plugin.json'),geometry_header_arrays_unchanged=True,
        original_through_bore_occupancy_preserved=through_bore,
        unchanged_compiled_fields=fields,build_command=command,
        source_sha256={p.name:sha(p) for p in [out/implementation.name,out/'pike_surface_geometry.h',
            out/Path(__file__).name,out/'frozen_collision_plugins.py']},
        qualified_surface_accuracy=False,qualified_support=False,qualified_robot_handling=False)
    (out/'plugin.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(plugin_name=name,geometry_header_arrays_unchanged=True)),flush=True)


if __name__=='__main__':main()
