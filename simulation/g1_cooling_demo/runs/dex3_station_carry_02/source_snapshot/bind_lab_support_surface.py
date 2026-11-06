"""Bind an audited exact tabletop collider while retaining its original visual.

The original support's bevels, pose and contact parameters are preserved.
This candidate still requires a new complete-room dynamic support test.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from build_tool_station import absolve_assets,sha
from runtime_collision_plugins import load_collision_plugins


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['scene','source_component','plugin','surface','gradient','output']:
        p.add_argument(name,type=Path)
    a=p.parse_args();scene=a.scene.resolve();out=a.output.resolve()
    binding=json.loads((scene/'binding.json').read_text())
    source=json.loads((a.source_component/'contract.json').read_text())
    plugin=json.loads((a.plugin/'plugin.json').read_text())
    surface=json.loads((a.surface/'review.json').read_text())
    gradient=json.loads((a.gradient/'review.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']==source['source_world_sha256']
    assert sha(scene/'binding.json')==source['source_binding_sha256']
    assert sha(a.source_component/'world.xml')==source['world_sha256']==plugin['source_world_sha256']
    assert source['geometry_conversion']['every_triangle_coordinate_identical']
    assert source['geometry_conversion']['converted_sha256']==plugin['source_mesh_sha256']
    assert surface['passed_sampled_surface'] and gradient['passed']
    assert surface['world_sha256']==gradient['world_sha256']==plugin['world_sha256']
    assert gradient['source_review_sha256']==sha(a.surface/'review.json')
    assert surface['plugin_library_sha256']==plugin['library_sha256']
    plugins=binding['collision_plugins']+[plugin];load_collision_plugins(plugins)
    old=mujoco.MjModel.from_xml_path(str(scene/'world.xml'))
    xml=ET.parse(scene/'world.xml').getroot();absolve_assets(xml,scene/'world.xml')
    name=source['source_geom'];geom=xml.find(".//geom[@name='"+name+"']")
    assert geom is not None and geom.get('type')=='mesh'
    source_mesh=xml.find("asset/mesh[@name='"+geom.get('mesh')+"']")
    assert sha(source_mesh.get('file'))==source['source_mesh_sha256']
    cx=ET.parse(a.plugin/'world.xml').getroot();absolve_assets(cx,a.plugin/'world.xml')
    cg=cx.find(".//geom[@name='source_support_surface']")
    asset=deepcopy(cx.find("asset/mesh[@name='"+cg.get('mesh')+"']"))
    asset.set('name','exact_original_bench_support_mesh')
    assert xml.find("asset/mesh[@name='"+asset.get('name')+"']") is None
    xml.find('asset').append(asset)
    parent=next(node for node in xml.iter() if geom in list(node))
    collider=deepcopy(geom);collider.set('type','sdf');collider.set('mesh',asset.get('name'))
    collider.set('group','3');collider.append(deepcopy(cg.find('plugin')))
    geom.set('name',name+'_original_visual');geom.set('contype','0');geom.set('conaffinity','0')
    parent.append(collider)
    for extension in cx.findall('extension/plugin'):xml.find('extension').append(deepcopy(extension))
    shutil.copytree(scene,out)
    for stale in ['inspection','review.json']:
        f=out/stale
        if f.is_dir():shutil.rmtree(f)
        elif f.exists():f.unlink()
    ET.indent(xml);ET.ElementTree(xml).write(out/'world.xml',encoding='unicode')
    new=mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    for field in ['body_mass','body_inertia','body_ipos','body_iquat','qpos0']:
        assert np.array_equal(getattr(old,field),getattr(new,field)),field
    oldid=old.geom(name).id;newid=new.geom(name).id
    for field in ['geom_friction','geom_solref','geom_solimp','geom_condim','geom_contype','geom_conaffinity','geom_margin','geom_gap']:
        assert np.array_equal(getattr(old,field)[oldid],getattr(new,field)[newid]),field
    visual=new.geom(name+'_original_visual').id
    assert np.array_equal(old.geom_pos[oldid],new.geom_pos[visual])
    assert np.array_equal(old.geom_quat[oldid],new.geom_quat[visual])
    # The collider uses the mesh compiler frame for the audited STL; authored
    # geom transforms are identical to the original MSH support's transforms.
    assert all(collider.get(k)==source['source_geom_attributes'].get(k) for k in ['pos','quat'])
    snapshot=out/'source_snapshot';shutil.copyfile(__file__,snapshot/Path(__file__).name)
    for src,label in [(a.source_component/'contract.json','bench_source.json'),
                      (a.surface/'review.json','bench_surface_review.json'),
                      (a.gradient/'review.json','bench_gradient_review.json')]:shutil.copyfile(src,out/label)
    inputs=json.loads((scene/'model_inputs.json').read_text())
    inputs[asset.get('file')]=sha(asset.get('file'));inputs[plugin['library']]=plugin['library_sha256']
    (out/'model_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    binding.update(upstream_scene=str(scene),upstream_binding_sha256=sha(scene/'binding.json'),
        world_sha256=sha(out/'world.xml'),model_inputs_sha256=sha(out/'model_inputs.json'),collision_plugins=plugins,
        support_surface_revision=dict(scope=__doc__,geom=name,source_mesh_sha256=source['source_mesh_sha256'],
            source_geometry_conversion=source['geometry_conversion'],plugin_library_sha256=plugin['library_sha256'],
            source_surface_review_sha256=sha(a.surface/'review.json'),gradient_review_sha256=sha(a.gradient/'review.json'),
            original_visual_preserved=True,initial_state_unchanged=sha(out/'initial_state.json')==sha(scene/'initial_state.json'),
            body_inertias_unchanged=True,contact_parameters_unchanged=True,whole_scene_support_tested=False))
    binding['source_snapshot_sha256']={f.name:sha(f) for f in snapshot.glob('*.py')}
    (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    print(json.dumps(binding['support_surface_revision']),flush=True)


if __name__=='__main__':main()
