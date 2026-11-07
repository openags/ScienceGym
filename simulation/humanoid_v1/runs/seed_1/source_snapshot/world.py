"""Source-pinned H2 foundation scene; Dex5-S hands are not yet available."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
import mujoco

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSET = ROOT / 'assets/unitree_h2_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(path, *, timestep=.001, floor=True):
    source = json.loads((ASSET / 'SOURCE.json').read_text())
    for name, digest in source['files_sha256'].items():
        if sha(ASSET / name) != digest:
            raise ValueError('H2 source changed: ' + name)
    root = ET.parse(ASSET / 'vendor/h2/h2_mujoco.xml').getroot()
    root.set('model', 'ScienceGym H2 body foundation; Dex5-S absent')
    root.find('compiler').set('meshdir', 'h2_meshes')
    root.find('option').attrib.update(timestep=str(timestep), integrator='implicitfast',
                                    solver='Newton', iterations='100', tolerance='1e-10')
    ET.SubElement(root.find('asset'), 'texture', name='lab_sky', type='skybox', builtin='gradient',
                  rgb1='.72 .81 .81', rgb2='.30 .40 .43', width='512', height='3072')
    # Resolve the official MJCF's omitted pelvis inertia using the corresponding
    # official URDF, rather than letting mesh density invent a different mass.
    inertia = ET.parse(ASSET / 'vendor/H2.urdf').find("link[@name='pelvis']/inertial")
    origin, tensor = inertia.find('origin'), inertia.find('inertia')
    if origin.get('rpy') != '0 0 0':
        raise ValueError('URDF pelvis inertial orientation requires explicit conversion')
    pelvis = root.find("worldbody/body[@name='pelvis']")
    ET.SubElement(pelvis, 'inertial', pos=origin.get('xyz'),
                  mass=inertia.find('mass').get('value'),
                  fullinertia=' '.join(tensor.get(k) for k in ['ixx', 'iyy', 'izz', 'ixy', 'ixz', 'iyz']))
    for body in root.iter('body'):
        for i, geom in enumerate(body.findall('geom')):
            geom.set('name', body.get('name') + '_geom_' + str(i))
    world = root.find('worldbody')
    if floor:
        ET.SubElement(world, 'geom', name='floor', type='plane', size='3 3 .1',
                      rgba='.18 .22 .25 1', group='3', friction='.8 .005 .0001')
    ET.SubElement(world, 'geom', name='bench_top', type='box', pos='.70 0 .87',
                  size='.45 .65 .03', rgba='.62 .67 .70 1', group='2')
    for x in [.30, 1.10]:
        for y in [-.58, .58]:
            ET.SubElement(world, 'geom', name=f'bench_leg_{x}_{y}', type='box',
                          pos=f'{x} {y} .42', size='.025 .025 .42',
                          rgba='.16 .20 .23 1', group='2')
    ET.SubElement(world, 'light', pos='-1 -2 3', dir='.3 .4 -1', directional='true', diffuse='.8 .8 .8')
    ET.SubElement(world, 'light', pos='1 2 3', dir='-.3 -.3 -1', diffuse='.5 .5 .5')
    ET.SubElement(world, 'camera', name='overview', pos='2.8 -3.4 2.4',
                  xyaxes='.772 .636 0 -.245 .298 .923')
    visual = ET.SubElement(root, 'visual')
    ET.SubElement(visual, 'global', offwidth='1280', offheight='900')
    for side in ['left', 'right']:
        ankle = root.find(f".//body[@name='{side}_ankle_pitch_link']")
        ET.SubElement(ankle, 'site', name=side + '_sole',
                      pos=f'.035 {'.0365' if side == 'left' else '-.0365'} -.058', size='.003')
        wrist = root.find(f".//body[@name='{side}_wrist_yaw_link']")
        ET.SubElement(wrist, 'site', name=side + '_wrist_reference', size='.007', rgba='1 .6 .1 1')
    ET.indent(root)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding='unicode')
    return dict(source_sha256=sha(ASSET / 'SOURCE.json'), hand_model_present=False,
                pelvis_inertial_source='vendor/H2.urdf', timestep_s=timestep,
                bench_top_m=.90, floor_present=floor,
                scope='H2 body, stance and unloaded wrist motion only; no dexterous grasp or paper-step credit')


def load(path):
    assets = {p.name: p.read_bytes() for p in (ASSET / 'vendor/h2/meshes').glob('*.stl')}
    return mujoco.MjModel.from_xml_string(Path(path).read_text(), assets)


def initialize(model, *, seed=0):
    data = mujoco.MjData(model)
    for side in ['left', 'right']:
        data.joint(side + '_hip_pitch_joint').qpos[0] = -.08
        data.joint(side + '_knee_joint').qpos[0] = .16
        data.joint(side + '_ankle_pitch_joint').qpos[0] = -.08
    mujoco.mj_forward(model, data)
    # Initial placement only. The floating base is never written during rollout.
    data.qpos[2] -= min(data.site(s + '_sole').xpos[2] for s in ['left', 'right'])
    if seed:
        rng = np.random.default_rng(seed)
        data.qpos[7:] += rng.uniform(-.0001, .0001, model.nq - 7)
    mujoco.mj_forward(model, data)
    return data
