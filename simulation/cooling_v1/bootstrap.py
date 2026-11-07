"""Fetch a pinned, separately licensed robot model into a local cache."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import requests
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
COMMIT = '62ab00f2bc44f6f20c1c9b7a13f3fb1dd41a4e35'
BASE = f'https://raw.githubusercontent.com/google-deepmind/mujoco_menagerie/{COMMIT}/franka_emika_panda/'
CACHE = Path(os.environ.get('SCIENCEGYM_ROBOT_CACHE','/tmp/sciencegym-robot-cache'))
EXPECTED = json.loads((HERE/'robot_source.json').read_text()).get('files_sha256',{}) if (HERE/'robot_source.json').exists() else {}


def fetch(name):
    if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError(name)
    p = CACHE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        response = requests.get(BASE + name, timeout=90)
        response.raise_for_status()
        p.write_bytes(response.content)
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if name in EXPECTED and digest!=EXPECTED[name]:raise ValueError('Pinned robot source mismatch: '+name)
    return name, digest


def main():
    fetch('panda.xml')
    root = ET.parse(CACHE / 'panda.xml').getroot()
    names = ['LICENSE', 'README.md'] + ['assets/' + e.attrib['file'] for e in root.findall('asset/mesh')]
    with ThreadPoolExecutor(max_workers=6) as pool:
        hashes = dict(pool.map(fetch, names))
    hashes['panda.xml'] = fetch('panda.xml')[1]
    record = dict(repository='https://github.com/google-deepmind/mujoco_menagerie',
                  commit=COMMIT, model='franka_emika_panda', license='Apache-2.0',
                  files_sha256=hashes)
    (HERE / 'robot_source.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Pinned Panda files:', len(hashes), flush=True)


if __name__ == '__main__':
    main()
