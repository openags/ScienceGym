"""Resolve portable logical asset paths into hash-verified MuJoCo VFS entries."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
from bootstrap import CACHE,HERE


def load(path):
    xml=Path(path).read_text();root=ET.fromstring(xml)
    source=json.loads((HERE/'robot_source.json').read_text())['files_sha256']
    geometry={p['file']:p['file_sha256'] for p in json.loads((HERE/'geometry/catalog.json').read_text())['parts']}
    assets={}
    for mesh in root.findall('asset/mesh'):
        logical=mesh.get('file');prefix,filename=logical.split('/',1)
        if Path(filename).name!=filename:raise ValueError('Nonlocal asset name')
        if prefix=='robot':file=CACHE/'assets'/filename;expected=source['assets/'+filename]
        elif prefix=='equipment':file=HERE/'geometry'/filename;expected=geometry[filename]
        else:raise ValueError('Unknown asset namespace: '+prefix)
        content=file.read_bytes()
        if hashlib.sha256(content).hexdigest()!=expected:raise ValueError('Asset hash mismatch: '+logical)
        assets[logical]=content
    return mujoco.MjModel.from_xml_string(xml,assets=assets)
