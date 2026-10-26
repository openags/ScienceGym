"""Pin a selected episode and its exact model inputs without altering evidence."""
import argparse,json,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
def package(folder):
 folder=Path(folder).resolve()
 def row(p):return dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 paths=set()
 for model in [folder/'world.xml',folder/'controller_model/world.xml']:
  tree=ET.parse(model).getroot();directory=(model.parent/tree.find('compiler').get('meshdir','')).resolve();paths.add(model)
  for item in tree.findall('asset/mesh'):paths.add((directory/item.get('file')).resolve())
 for name in ['assets/unitree_g1_inspire_v1/simulation/robot.xml','assets/unitree_g1_inspire_v1/SOURCE.json','assets/g1_sensor_rig_v1/rig.json','assets/cooling_lab_v1/ordinary_tools.json']:
  paths.add(ROOT/name)
 (folder/'model_inputs.json').write_text(json.dumps(dict(scope='Exact models and mesh dependencies for the continuous episode.',files=[row(p) for p in sorted(paths)]),indent=2)+'\n')
 files=[row(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts]
 (folder/'manifest.json').write_text(json.dumps(dict(whole_paper_validated=False,qualified_branches=0,files=files),indent=2)+'\n');print('Pinned',len(paths),'model inputs;',len(files),'episode files')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();package(a.folder)
