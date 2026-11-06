"""Pin delivered evidence and external mesh inputs without changing results."""
import json,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];FOLDER=ROOT/'simulation/g1_cooling_demo/runs/delivery'
def row(p):return dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
paths=set()
for model in [FOLDER/'world.xml',FOLDER/'controller_model/world.xml']:
 tree=ET.parse(model).getroot();directory=(model.parent/tree.find('compiler').get('meshdir','')).resolve()
 paths.add(model)
 for item in tree.findall('asset/mesh'):paths.add((directory/item.get('file')).resolve())
for p in ['assets/unitree_g1_inspire_v1/simulation/robot.xml','assets/unitree_g1_inspire_v1/SOURCE.json','assets/g1_sensor_rig_v1/rig.json','assets/cooling_lab_v1/ordinary_tools.json']:
 paths.add(ROOT/p)
inputs=dict(scope='Exact XML and mesh inputs used by delivery plant and actor models.',files=[row(p) for p in sorted(paths)])
(FOLDER/'model_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
manifest=dict(whole_paper_validated=False,files=[row(p) for p in sorted(FOLDER.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts])
(FOLDER/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Pinned',len(inputs['files']),'model inputs and',len(manifest['files']),'delivery files')
