"""Extract one unchanged laboratory support mesh for a source-surface audit."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from build_tool_station import absolve_assets,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('geom');p.add_argument('output',type=Path)
    a=p.parse_args();scene=a.scene.resolve();out=a.output.resolve()
    binding=json.loads((scene/'binding.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    source=ET.parse(scene/'world.xml').getroot();absolve_assets(source,scene/'world.xml')
    geom=source.find(".//geom[@name='"+a.geom+"']")
    if geom is None or geom.get('type')!='mesh':raise ValueError('Expected original support mesh')
    mesh=source.find("asset/mesh[@name='"+geom.get('mesh')+"']")
    if mesh is None or mesh.get('scale','1 1 1')!='1 1 1':raise ValueError('Unexpected scaled support asset')
    world=ET.Element('mujoco',model='source_support_geometry')
    ET.SubElement(world,'compiler',angle='radian')
    ET.SubElement(world,'option',timestep='.0001',gravity='0 0 -9.81')
    asset=ET.SubElement(world,'asset');asset.append(deepcopy(mesh))
    body=ET.SubElement(world,'worldbody')
    ET.SubElement(body,'geom',name='source_support_surface',type='mesh',mesh=mesh.get('name'),
        contype='1',conaffinity='1',pos='0 0 0',quat='1 0 0 0')
    out.mkdir(parents=True,exist_ok=False)
    ET.indent(world);ET.ElementTree(world).write(out/'world.xml',encoding='unicode')
    contract=dict(scope=__doc__,source_scene=str(scene),source_geom=a.geom,
        source_binding_sha256=sha(scene/'binding.json'),source_world_sha256=sha(scene/'world.xml'),
        source_mesh_path=mesh.get('file'),source_mesh_sha256=sha(mesh.get('file')),
        source_geom_attributes=geom.attrib,collision_plugins=[],
        world_sha256=sha(out/'world.xml'),qualified_support=False)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    shutil.copyfile(__file__,out/Path(__file__).name)
    print(json.dumps(contract),flush=True)


if __name__=='__main__':main()
