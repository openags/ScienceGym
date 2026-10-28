"""Hash-pinned manufacturer reconstructions in portable device workcells."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import mujoco
from world import HERE,vec
from bootstrap import CACHE

ASSETS=HERE.parents[1]/'assets'
DEVICES={'keithley_2000':ASSETS/'keithley_2000_v1',
         'omega_pm_rtd':ASSETS/'omega_pm_rtd_v1'}


def export(name):
    directory=DEVICES[name];source=directory/'geometry'/f'{name}.glb'
    scene=trimesh.load(source,force='scene');cache=HERE/'geometry'/name;cache.mkdir(exist_ok=True)
    rows=[]
    for index,node in enumerate(sorted(scene.graph.nodes_geometry)):
        matrix,key=scene.graph[node];mesh=scene.geometry[key].copy();mesh.apply_transform(matrix)
        # Row-vector inverse of Blender Z-up -> glTF Y-up: (x,y,z)
        # in glTF becomes (x,-z,y). The opposite rotation inverts devices.
        mesh.vertices=np.asarray(mesh.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
        center=mesh.bounds.mean(axis=0);mesh.vertices-=center
        path=cache/f'{index:04d}.obj';mesh.export(path)
        material=mesh.visual.material;rgba=np.array(material.baseColorFactor if hasattr(material,'baseColorFactor') else [160,160,160,255],float)/255
        rows.append(dict(id=node,file=path.name,position_m=center.tolist(),rgba=rgba.tolist(),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    result=dict(model=name,glb_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),parts=rows)
    (cache/'catalog.json').write_text(json.dumps(result,indent=2)+'\n');return result


def visuals(world,parent,name,prefix=None,exclude=(),only=None,origin=(0,0,0)):
    cache=HERE/'geometry'/name;catalog=json.loads((cache/'catalog.json').read_text())
    current=hashlib.sha256((DEVICES[name]/'geometry'/f'{name}.glb').read_bytes()).hexdigest()
    if current!=catalog['glb_sha256']:raise ValueError('Device mesh cache is stale: '+name)
    prefix=prefix or name
    for part in catalog['parts']:
        if part['id'] in exclude:continue
        if only is not None and part['id'] not in only:continue
        mesh_name=prefix+'_'+part['file'].removesuffix('.obj')
        ET.SubElement(world.assets,'mesh',name=mesh_name,file=f'{name}/{part["file"]}')
        ET.SubElement(parent,'geom',name=prefix+'_'+part['id'],type='mesh',mesh=mesh_name,
                      pos=vec(np.asarray(part['position_m'])-origin),rgba=vec(part['rgba']),mass='0',contype='0',conaffinity='0',group='2')
    return catalog


def load(path):
    xml=Path(path).read_text();root=ET.fromstring(xml);assets={}
    robot=json.loads((HERE/'robot_source.json').read_text())['files_sha256']
    original={p['file']:p['file_sha256'] for p in json.loads((HERE/'geometry/catalog.json').read_text())['parts']}
    devices={n:{p['file']:p['sha256'] for p in json.loads((HERE/'geometry'/n/'catalog.json').read_text())['parts']}
             for n in DEVICES if (HERE/'geometry'/n/'catalog.json').exists()}
    for mesh in root.findall('asset/mesh'):
        logical=mesh.get('file')
        if logical is None:continue
        namespace,filename=logical.split('/',1)
        if Path(filename).name!=filename:raise ValueError('Nonlocal mesh name')
        if namespace=='robot':source=CACHE/'assets'/filename;expected=robot['assets/'+filename]
        elif namespace=='equipment':source=HERE/'geometry'/filename;expected=original[filename]
        elif namespace in DEVICES:source=HERE/'geometry'/namespace/filename;expected=devices[namespace][filename]
        else:raise ValueError('Unknown mesh namespace: '+namespace)
        content=source.read_bytes()
        if hashlib.sha256(content).hexdigest()!=expected:raise ValueError('Device asset hash mismatch: '+logical)
        assets[logical]=content
    return mujoco.MjModel.from_xml_string(xml,assets=assets)


if __name__=='__main__':
    for name in DEVICES:print(name,len(export(name)['parts']))
