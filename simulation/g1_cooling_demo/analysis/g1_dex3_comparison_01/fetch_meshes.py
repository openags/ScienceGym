"""Fetch the pinned official comparison model; leaves the selected robot intact."""
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
from pathlib import Path
import shutil,urllib.request
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CURRENT=ROOT/'assets/unitree_g1_inspire_v1'
source=json.loads((HERE/'source.json').read_text())
existing=json.loads((CURRENT/'SOURCE.json').read_text())
known={row['path']:row for row in existing['files']}
xml=ET.parse(HERE/'g1_29dof_with_hand_rev_1_0.xml').getroot()
base=f"https://raw.githubusercontent.com/unitreerobotics/unitree_ros/{source['commit']}/robots/g1_description/meshes/"
(HERE/'meshes').mkdir(exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def fetch(name):
    target=HERE/'meshes'/name;old=CURRENT/'vendor/unitree_ros/meshes'/name
    key=str(old.relative_to(CURRENT));url=base+name
    if old.exists() and key in known and sha(old.read_bytes())==known[key]['sha256']:
        data=old.read_bytes();method='Reuse verified bytes from the same pinned official repository'
    else:
        data=urllib.request.urlopen(url,timeout=30).read();method='HTTPS with system certificate validation'
    target.write_bytes(data)
    return dict(path='meshes/'+name,url=url,sha256=sha(data),bytes=len(data),method=method)
names=sorted({Path(m.get('file')).name for m in xml.findall('asset/mesh')})
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(fetch,names):rows.append(row)
license_row=next(r for r in existing['files'] if 'unitree_ros' in r['url'] and r['url'].endswith('/LICENSE'))
license_data=(CURRENT/license_row['path']).read_bytes()
if sha(license_data)!=license_row['sha256']:raise ValueError('Source license changed')
(HERE/'LICENSE').write_bytes(license_data)
source['mesh_files']=rows
source['license_file']=dict(path='LICENSE',url=license_row['url'],sha256=sha(license_data))
source['geometry_adopted']=False
(HERE/'source.json').write_text(json.dumps(source,indent=2)+'\n')
print(json.dumps(dict(meshes=len(rows),downloaded=sum(r['method'].startswith('HTTPS') for r in rows),bytes=sum(r['bytes'] for r in rows))),flush=True)
