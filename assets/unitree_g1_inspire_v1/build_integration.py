"""Build source-derived articulation and a gravity-enabled floating-base MJCF.

Actuators and contact parameters are explicitly provisional. No task/controller
or hardware qualification is granted by compilation and static checks.
"""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import trimesh
from audit import sha,origin
from kinematics import HERE,Robot

ROOT=HERE.parents[1]


def nums(values):return ' '.join(format(float(v),'.12g') for v in values)


def transform_attributes(t):
    return dict(pos=nums(t[:3,3]),quat=nums(trimesh.transformations.quaternion_from_matrix(t)))


def build():
    robot=Robot();q=robot.inspection()
    kin=dict(schema_version=1,root_link=robot.root,root_matrix=robot.root_matrix.tolist(),
      joints=[dict(j,inspection_angle_rad=q[j['name']]) for j in robot.joints],
      bind_world={k:v.tolist() for k,v in robot.bind.items()},
      part_links={n:n.rsplit('_visual_',1)[0] for n in robot.preview.graph.nodes_geometry},
      scope='Official URDF frames and mimic relations. Slider is a geometric inspection, not a motor command or grasp.')
    (HERE/'kinematics.json').write_text(json.dumps(kin,indent=2)+'\n')
    xml=ET.Element('mujoco',model='sciencegym_g1_inspire_ftp_asset')
    ET.SubElement(xml,'compiler',angle='radian',autolimits='true',inertiafromgeom='false',fusestatic='false',meshdir='..')
    ET.SubElement(xml,'option',gravity='0 0 -9.81',timestep='.001',integrator='implicitfast',iterations='100')
    assets=ET.SubElement(xml,'asset');mesh_names={}
    for e in robot.xml.findall('.//mesh'):
        key=(e.get('filename'),e.get('scale','1 1 1'))
        if key not in mesh_names:
            name='source_mesh_'+str(len(mesh_names));mesh_names[key]=name
            ET.SubElement(assets,'mesh',name=name,file='vendor/unitree_ros/'+key[0],scale=key[1])
    collision=json.loads((HERE/'collision.json').read_text());palm_pieces={}
    for item in collision['items']:
        assert sha(HERE/item['source_path'])==item['source_sha256']
        palm_pieces[item['link']]=[]
        for i,piece in enumerate(item['pieces']):
            assert sha(HERE/piece['path'])==piece['sha256']
            name=item['link']+'_convex_'+str(i);palm_pieces[item['link']].append(name)
            ET.SubElement(assets,'mesh',name=name,file=piece['path'])
    world=ET.SubElement(xml,'worldbody');ET.SubElement(world,'geom',name='review_floor',type='plane',size='3 3 .05',rgba='.7 .75 .7 1',friction='.8 .005 .0001')
    bodies={robot.root:ET.SubElement(world,'body',name=robot.root,**transform_attributes(robot.root_matrix))}
    ET.SubElement(bodies[robot.root],'freejoint',name='floating_base')
    for j in robot.joints:
        body=ET.SubElement(bodies[j['parent']],'body',name=j['id'],**transform_attributes(np.array(j['origin_matrix'])))
        bodies[j['id']]=body
        if j['type']=='revolute':
            limit=j['limits'];ET.SubElement(body,'joint',name=j['name'],type='hinge',axis=nums(j['axis']),range=nums([limit['lower'],limit['upper']]),damping='.05',armature='.001')
    materials={m.get('name'):m.find('color').get('rgba') for m in robot.xml.findall('material') if m.find('color') is not None}
    for name,link in robot.links.items():
        body=bodies[name];inertial=link.find('inertial')
        if inertial is not None:
            tr=origin(inertial.find('origin'));a={k:float(v) for k,v in inertial.find('inertia').attrib.items()}
            I=np.array([[a['ixx'],a['ixy'],a['ixz']],[a['ixy'],a['iyy'],a['iyz']],[a['ixz'],a['iyz'],a['izz']]])
            I=tr[:3,:3]@I@tr[:3,:3].T
            ET.SubElement(body,'inertial',pos=nums(tr[:3,3]),mass=inertial.find('mass').get('value'),fullinertia=nums([I[0,0],I[1,1],I[2,2],I[0,1],I[0,2],I[1,2]]))
        for kind in ['visual','collision']:
            for index,e in enumerate(link.findall(kind)):
                shape=list(e.find('geometry'))[0];attrs=transform_attributes(origin(e.find('origin')))
                attrs.update(name=name+'_'+kind+'_'+str(index),density='0',group='2' if kind=='visual' else '3')
                if kind=='visual':
                    mat=e.find('material');color=mat.find('color') if mat is not None else None
                    attrs.update(contype='0',conaffinity='0',rgba=color.get('rgba') if color is not None else materials.get(mat.get('name') if mat is not None else '', '.7 .7 .7 1'))
                else:attrs.update(friction='.8 .005 .0001',rgba='.3 .7 .3 .2')
                if shape.tag=='mesh':attrs.update(type='mesh',mesh=mesh_names[(shape.get('filename'),shape.get('scale','1 1 1'))])
                elif shape.tag=='sphere':attrs.update(type='sphere',size=shape.get('radius'))
                elif shape.tag=='cylinder':attrs.update(type='cylinder',size=nums([shape.get('radius'),float(shape.get('length'))/2]))
                else:raise ValueError(shape.tag)
                if kind=='collision' and name in palm_pieces:
                    for i,piece in enumerate(palm_pieces[name]):ET.SubElement(body,'geom',**{**attrs,'mesh':piece,'name':name+'_collision_piece_'+str(i)})
                else:ET.SubElement(body,'geom',**attrs)
    eq=ET.SubElement(xml,'equality');act=ET.SubElement(xml,'actuator');drivers=[]
    for j in robot.joints:
        if j['type']=='fixed':continue
        if j['mimic']:
            m=j['mimic'];ET.SubElement(eq,'joint',name='mimic_'+j['name'],joint1=j['name'],joint2=m['joint'],polycoef=nums([float(m.get('offset',0)),float(m.get('multiplier',1)),0,0,0]))
        else:
            effort=j['limits']['effort'];ET.SubElement(act,'motor',name=j['name']+'_torque',joint=j['name'],gear='1',ctrlrange=nums([-effort,effort]))
            drivers.append(dict(joint=j['name'],effort_limit_from_urdf=effort,velocity_limit_from_urdf=j['limits']['velocity'],hardware_calibrated=False))
    for side in ['left','right']:
        ET.SubElement(bodies[side+'_base_link'],'site',name=side+'_palm_review',pos='0 0 .12',size='.006',rgba='1 .4 0 1')
    sensor=ET.SubElement(xml,'sensor')
    for j in robot.joints:
        if j['type']=='revolute':
            ET.SubElement(sensor,'jointpos',name=j['name']+'_encoder',joint=j['name'])
            ET.SubElement(sensor,'jointvel',name=j['name']+'_velocity',joint=j['name'])
    out=HERE/'simulation';out.mkdir(exist_ok=True);target=out/'robot.xml'
    ET.indent(xml);ET.ElementTree(xml).write(target,encoding='unicode')
    model=mujoco.MjModel.from_xml_path(str(target));data=mujoco.MjData(model)
    mujoco.mj_forward(model,data)
    checks=[]
    def check(name,value,**extra):
        checks.append(dict(name=name,passed=bool(value),**extra))
        if not value:raise AssertionError(name)
    check('free_root_gravity_and_contacts',model.jnt_type[0]==mujoco.mjtJoint.mjJNT_FREE and np.allclose(model.opt.gravity,[0,0,-9.81]) and model.ngeom>90)
    check('independent_actuators_and_mimics',model.nu==41 and model.neq==12 and model.nv==59)
    for fraction in [0,.25,.5,.75,1]:
        pose={k:fraction*v for k,v in q.items()};expected=robot.fk(pose)
        data.qpos[:]=model.qpos0
        for j in robot.joints:
            if j['type']=='revolute':data.qpos[model.joint(j['name']).qposadr[0]]=pose[j['name']]
        mujoco.mj_forward(model,data)
        error=max(np.linalg.norm(data.body(name).xpos-t[:3,3]) for name,t in expected.items())
        rotation=max(np.max(np.abs(data.body(name).xmat.reshape(3,3)-t[:3,:3])) for name,t in expected.items())
        check('urdf_mjcf_frames_'+str(fraction),error<1e-8 and rotation<1e-8,maximum_position_error_m=float(error),maximum_rotation_error=float(rotation))
        check('mimic_residual_'+str(fraction),np.max(np.abs(data.efc_pos[:model.neq]))<1e-8)
    # Falling is expected without a controller: only numerical/contact loading
    # is tested, never reported as a standing qualification.
    data=mujoco.MjData(model);initial_height=float(data.qpos[2])
    for _ in range(100):mujoco.mj_step(model,data)
    check('unactuated_100ms_numeric_smoke',np.isfinite(data.qpos).all() and np.isfinite(data.qvel).all() and np.isfinite(data.qacc).all() and not np.any(data.warning.number) and abs(data.time-.1)<1e-10)
    collisions=[];static=mujoco.MjData(model);mujoco.mj_forward(model,static)
    for contact in static.contact:
        if contact.dist < -.0005:collisions.append(dict(geoms=[model.geom(i).name for i in contact.geom],penetration_m=float(-contact.dist)))
    check('zero_pose_no_penetration_over_0_5mm',not collisions)
    report=dict(schema_version=1,status='compiled_asset_model_not_controller_qualified',mujoco_version=mujoco.__version__,checks=checks,
      model=dict(path=str(target.relative_to(ROOT)),sha256=sha(target),nq=model.nq,nv=model.nv,nu=model.nu,equality_constraints=model.neq),
      source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [HERE/'SOURCE.json',HERE/'VERIFICATION.json',HERE/'kinematics.json',HERE/'kinematics.py',HERE/'collision.json',HERE/'collision_baseline.json',Path(__file__)]],
      hand_independent_actuators_per_side=6,actuators=drivers,zero_pose_penetrations_over_0_5mm=collisions,
      passive_smoke=dict(duration_s=.1,controls='zero torque',initial_base_height_m=initial_height,final_base_height_m=float(data.qpos[2]),standing_qualified=False),
      assumptions=['Source URDF motor effort and speed limits are uncalibrated; speed is recorded but not enforced by the torque-only interface',
       'Joint damping .05 and armature .001 are authored numerical defaults, not measured dynamics',
       'Contact friction .8/.005/.0001 and default solver softness are provisional',
       'Palms use source-component CoACD decomposition for large shells and convex hulls for small parts. Other meshes use convex hulls; all contact surfaces remain subject to review',
       'Palm review sites at source-hand (0,0,.12) are authored reach references, not a validated grasp frame',
       'No tactile response, camera streams, process isolation, gait or manipulation controller is implemented'],
      full_physics_qualified=False,owner_acceptance=None)
    (HERE/'integration.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(checks=len(checks),passed=all(c['passed'] for c in checks),actuators=model.nu,mimics=model.neq,zero_pose_penetrations=collisions)))


if __name__=='__main__':build()
