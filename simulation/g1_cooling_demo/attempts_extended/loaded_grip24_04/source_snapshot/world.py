"""Current G1/Inspire contact runtime; source models are never modified."""
from pathlib import Path
import json,os
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import trimesh
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ROBOT=ROOT/'assets/unitree_g1_inspire_v1'


def build(out, *, timestep=.002, tray=True, tray_offset=(0.,0.), payload=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    xml=ET.parse(ROBOT/'simulation/robot.xml').getroot()
    xml.set('model','ScienceGym G1 Inspire contact development')
    xml.find('compiler').set('meshdir',os.path.relpath(ROBOT,out))
    xml.find('option').attrib.update(timestep=str(timestep),iterations='100',tolerance='1e-9',solver='Newton')
    world=xml.find('worldbody');world.find("geom[@name='review_floor']").set('rgba','.25 .30 .32 1')
    for side in ['left','right']:
        body=xml.find(f".//body[@name='{side}_ankle_roll_link']")
        ET.SubElement(body,'site',name=side+'_sole',pos='.025 0 -.0354',size='.002')
        body=xml.find(f".//body[@name='{side}_palm_force_sensor']")
        ET.SubElement(body,'site',name=side+'_wrist_reference',size='.002',rgba='0 0 0 0')
    imu=xml.find(".//body[@name='pelvis']");ET.SubElement(imu,'site',name='pelvis_imu',size='.002',rgba='0 0 0 0')
    ET.SubElement(xml.find('sensor'),'framequat',name='imu_orientation',objtype='site',objname='pelvis_imu')
    ET.SubElement(xml.find('sensor'),'gyro',name='imu_angular_velocity',site='pelvis_imu')
    rig=json.loads((ROOT/'assets/g1_sensor_rig_v1/rig.json').read_text())
    optical=next(c for c in rig['optics'] if c['id']=='head_depth');t=np.asarray(optical['parent_from_optical'])
    camera_body=xml.find(".//body[@name='d435_link']")
    q=Rotation.from_matrix(t[:3,:3]@np.diag([1,-1,-1])).as_quat();q=np.r_[q[3],q[:3]]
    ET.SubElement(camera_body,'camera',name='head_depth',pos=' '.join(map(str,t[:3,3])),quat=' '.join(map(str,q)),fovy='58')
    for name,position,size,color in [('bench_top',[.83,0,.875],[.45,.70,.025],[.39,.44,.45,1]),
            ('bench_leg_a',[.43,-.65,.425],[.025,.025,.425],[.65,.67,.66,1]),
            ('bench_leg_b',[1.29,-.65,.425],[.025,.025,.425],[.65,.67,.66,1]),
            ('bench_leg_c',[.43,.65,.425],[.025,.025,.425],[.65,.67,.66,1]),
            ('bench_leg_d',[1.29,.65,.425],[.025,.025,.425],[.65,.67,.66,1])]:
        ET.SubElement(world,'geom',name=name,type='box',pos=' '.join(map(str,position)),size=' '.join(map(str,size)),rgba=' '.join(map(str,color)),group='2',friction='.7 .005 .0001')
    # The exact catalog tray visual is retained. Its contact surface uses a
    # convex decomposition of the same formed shell, not a filled bounding box.
    if tray:
        src=json.loads((ROOT/'assets/cooling_lab_v1/ordinary_tools.json').read_text())
        item=next(x for x in src['items'] if x['id']=='buerkle_4208_0022')
        mesh=trimesh.load(ROOT/item['geometry']['path'],force='scene').to_geometry()
        mesh.export(out/'tray_visual.stl')
        ET.SubElement(xml.find('asset'),'mesh',name='tray_visual',file=os.path.relpath(out/'tray_visual.stl',ROBOT))
        body=ET.SubElement(world,'body',name='carrier_tray',pos=f'{.51+tray_offset[0]} {tray_offset[1]} .9005',quat='.7071067811865476 0 0 .7071067811865476')
        ET.SubElement(body,'freejoint',name='tray_free')
        # Selected 1.2 mm sheet and 304 steel density from existing asset
        # reconstruction; inertia follows the actual mesh and is not measured.
        mass=float(mesh.volume*8000);inertia=mesh.moment_inertia*8000
        ET.SubElement(body,'inertial',pos=' '.join(map(str,mesh.center_mass)),mass=str(mass),fullinertia=' '.join(map(str,[inertia[0,0],inertia[1,1],inertia[2,2],inertia[0,1],inertia[0,2],inertia[1,2]])))
        ET.SubElement(body,'geom',name='tray_visual',type='mesh',mesh='tray_visual',contype='0',conaffinity='0',group='2',rgba='.68 .71 .72 1')
        # Faceted wall pieces preserve a cavity and the source tapered sides.
        # Decomposition is computed once and cached with this runtime input.
        import coacd
        coacd.set_log_level('error')
        pieces=coacd.run_coacd(coacd.Mesh(np.asarray(mesh.vertices),np.asarray(mesh.faces)),threshold=.035,max_convex_hull=32,resolution=1000,mcts_iterations=40,mcts_max_depth=3,seed=0)
        for i,(v,f) in enumerate(pieces):
            fn=out/f'tray_collision_{i}.stl';trimesh.Trimesh(v,f,process=False).export(fn)
            ET.SubElement(xml.find('asset'),'mesh',name=f'tray_collision_{i}',file=os.path.relpath(fn,ROBOT))
            ET.SubElement(body,'geom',name=f'tray_contact_{i}',type='mesh',mesh=f'tray_collision_{i}',group='3',rgba='.3 .7 .3 .2',friction='.7 .005 .0001',solref='.01 1')
        if payload:
            stock=json.loads((ROOT/'assets/cooling_lab_v1/supplies.json').read_text())
            item=next(x for x in stock['items'] if x['id']=='calibration_copper_stock')
            copper=trimesh.load(ROOT/item['geometry']['path'],force='scene').to_geometry()
            fn=out/'calibration_copper_stock.stl';copper.export(fn)
            ET.SubElement(xml.find('asset'),'mesh',name='calibration_copper_stock',file=os.path.relpath(fn,ROBOT))
            block=ET.SubElement(world,'body',name='calibration_copper_stock',pos=f'{.51+tray_offset[0]} {tray_offset[1]} .9021')
            ET.SubElement(block,'freejoint',name='copper_stock_free')
            mass=float(copper.volume*8960);inertia=copper.moment_inertia*8960
            ET.SubElement(block,'inertial',pos=' '.join(map(str,copper.center_mass)),mass=str(mass),fullinertia=' '.join(map(str,[inertia[0,0],inertia[1,1],inertia[2,2],inertia[0,1],inertia[0,2],inertia[1,2]])))
            # Source-defined 60 x 50 x 30 mm design stock, with inferred copper
            # density. It starts in the carrier; loading is not robot credit.
            ET.SubElement(block,'geom',name='copper_stock_contact',type='mesh',mesh='calibration_copper_stock',density='8960',rgba='.65 .31 .15 1',friction='.5 .005 .0001',group='2')
    ET.SubElement(xml.find('asset'),'texture',name='sky',type='skybox',builtin='gradient',rgb1='.18 .25 .30',rgb2='.52 .59 .62',width='512',height='3072')
    ET.SubElement(world,'light',name='key',pos='0 -2 3',dir='.2 .5 -1',directional='true',diffuse='.8 .8 .8')
    ET.SubElement(world,'light',name='fill',pos='1 2 3',dir='-.2 -.5 -1',diffuse='.6 .6 .6')
    visual=ET.SubElement(xml,'visual');ET.SubElement(visual,'global',offwidth='1280',offheight='960')
    path=out/'world.xml';ET.indent(xml);ET.ElementTree(xml).write(path,encoding='unicode')
    return path


def initialize(m):
    d=mujoco.MjData(m)
    for side in ['left','right']:
        d.joint(side+'_hip_pitch_joint').qpos[0]=-.06
        d.joint(side+'_knee_joint').qpos[0]=.12
        d.joint(side+'_ankle_pitch_joint').qpos[0]=-.06
        d.joint(side+'_elbow_joint').qpos[0]=.45
    mujoco.mj_forward(m,d)
    d.qpos[2]-=min(d.site(s+'_sole').xpos[2] for s in ['left','right'])
    mujoco.mj_forward(m,d)
    return d
