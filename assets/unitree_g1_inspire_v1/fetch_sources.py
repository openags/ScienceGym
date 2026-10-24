"""Fetch the exact official G1/FTP resource bundle; never install or run upstream code."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import ssl
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROS = '15ebe53f4cd77e7d745ae83b9d7ff90e685e8998'
LAB = '3c6e67bb5c7ada942a6d1884ab69338f57596f77'  # Isaac Lab v2.3.0
SIM = 'e30c25b1dffdf92ada1d6c8c1fe9a47bdde0fecc'
MODEL = 'g1_29dof_rev_1_0_with_inspire_hand_FTP.urdf'


def fetch(spec):
    repo, revision, upstream, local = spec
    url = f'https://raw.githubusercontent.com/{repo}/{revision}/{upstream}'
    context = ssl.create_default_context(cafile='/etc/ssl/certs/ca-certificates.crt')
    data = urllib.request.urlopen(url, context=context, timeout=90).read()
    target = HERE / local
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return dict(path=local, url=url, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def main():
    model = fetch(('unitreerobotics/unitree_ros', ROS,
                   'robots/g1_description/' + MODEL, 'vendor/unitree_ros/' + MODEL))
    tree = ET.parse(HERE / model['path'])
    meshes = sorted({m.attrib['filename'] for m in tree.findall('.//mesh')})
    specs = [('unitreerobotics/unitree_ros', ROS, 'robots/g1_description/' + m,
              'vendor/unitree_ros/' + m) for m in meshes]
    specs += [('unitreerobotics/unitree_ros', ROS, p, 'vendor/unitree_ros/' + local)
              for p, local in [('LICENSE', 'LICENSE'), ('robots/g1_description/README.md', 'README.md')]]
    for p in ['LICENSE', 'source/isaaclab_assets/isaaclab_assets/robots/unitree.py',
              'source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/pick_place/__init__.py',
              'source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/pick_place/pickplace_unitree_g1_inspire_hand_env_cfg.py']:
        specs.append(('isaac-sim/IsaacLab', LAB, p, 'references/isaaclab/' + p))
    for p in ['LICENSE', 'README.md', 'fetch_assets.sh', 'robots/unitree.py', 'tasks/common_config/robot_configs.py']:
        specs.append(('unitreerobotics/unitree_sim_isaaclab', SIM, p, 'references/unitree_sim_isaaclab/' + p))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        records = [model] + list(pool.map(fetch, specs))
    source = dict(schema_version=1, retrieved_on='2026-10-24',
        selected_candidate='Unitree G1 29DoF rev 1.0 + Inspire FTP left/right',
        status='source_bundle_only_pending_scene_and_runtime_integration',
        repositories=[dict(repository='unitreerobotics/unitree_ros', commit=ROS, license='BSD-3-Clause'),
                      dict(repository='isaac-sim/IsaacLab', commit=LAB, tag='v2.3.0', license='BSD-3-Clause'),
                      dict(repository='unitreerobotics/unitree_sim_isaaclab', commit=SIM, license='Apache-2.0')],
        model_path=model['path'], mesh_count=len(meshes), files=sorted(records, key=lambda x: x['path']),
        scope=['Official URDF and referenced meshes retained byte-for-byte at source scale',
               'External NVIDIA USD and Unitree Hugging Face assets are not bundled; their terms are separate',
               'Reference simulation gains and URDF limits are source parameters, not measured hardware capabilities',
               'No scene acceptance, whole-body run, sensor-only autonomy or manipulation success is implied'])
    (HERE / 'SOURCE.json').write_text(json.dumps(source, indent=2) + '\n')
    print(json.dumps(dict(files=len(records), meshes=len(meshes), bytes=sum(r['bytes'] for r in records))))


if __name__ == '__main__':
    main()
