"""Extract one unchanged laboratory support mesh for a source-surface audit."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import struct
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

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
    out.mkdir(parents=True,exist_ok=False)
    component_mesh=deepcopy(mesh);conversion=None
    if Path(mesh.get('file')).suffix=='.msh':
        raw=Path(mesh.get('file')).read_bytes();nv,nn,nt,nf=struct.unpack('<4i',raw[:16])
        assert nv>=4 and nf>0 and nn in [0,nv] and nt in [0,nv]
        assert len(raw)==16+12*(nv+nn+nf)+8*nt
        vertices=np.frombuffer(raw,dtype='<f4',count=nv*3,offset=16).reshape(-1,3)
        faces=np.frombuffer(raw,dtype='<i4',count=nf*3,offset=16+12*(nv+nn)+8*nt).reshape(-1,3)
        assert faces.min()>=0 and faces.max()<nv
        shape=trimesh.Trimesh(vertices,faces,process=False)
        target=out/'source_geometry.stl';shape.export(target)
        roundtrip=trimesh.load(target,force='mesh',process=False)
        assert np.array_equal(shape.triangles,roundtrip.triangles)
        component_mesh.set('file',str(target));component_mesh.attrib.pop('content_type',None)
        conversion=dict(format_reference='https://mujoco.readthedocs.io/en/3.4.0/XMLreference.html#asset-mesh',
            source_sha256=sha(mesh.get('file')),converted_sha256=sha(target),triangles=nf,
            every_triangle_coordinate_identical=True,maximum_triangle_coordinate_error_m=0.)
    world=ET.Element('mujoco',model='source_support_geometry')
    ET.SubElement(world,'compiler',angle='radian')
    ET.SubElement(world,'option',timestep='.0001',gravity='0 0 -9.81')
    asset=ET.SubElement(world,'asset');asset.append(component_mesh)
    body=ET.SubElement(world,'worldbody')
    ET.SubElement(body,'geom',name='source_support_surface',type='mesh',mesh=mesh.get('name'),
        contype='1',conaffinity='1',pos='0 0 0',quat='1 0 0 0')
    ET.indent(world);ET.ElementTree(world).write(out/'world.xml',encoding='unicode')
    contract=dict(scope=__doc__,source_scene=str(scene),source_geom=a.geom,
        source_binding_sha256=sha(scene/'binding.json'),source_world_sha256=sha(scene/'world.xml'),
        source_mesh_path=mesh.get('file'),source_mesh_sha256=sha(mesh.get('file')),
        source_geom_attributes=geom.attrib,geometry_conversion=conversion,collision_plugins=[],
        world_sha256=sha(out/'world.xml'),qualified_support=False)
    (out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    shutil.copyfile(__file__,out/Path(__file__).name)
    print(json.dumps(contract),flush=True)


if __name__=='__main__':main()
