"""Static official hand geometry inspection; fixed wrist, no task execution."""
import copy,json
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco,numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
source=ET.parse(HERE/'g1_29dof_with_hand_rev_1_0.xml').getroot()
root=ET.Element('mujoco',model='official_Dex3_geometry_inspection')
ET.SubElement(root,'compiler',angle='radian',meshdir=str(HERE/'meshes'))
visual=ET.SubElement(root,'visual');ET.SubElement(visual,'global',offwidth='900',offheight='800')
root.append(copy.deepcopy(source.find('asset')))
world=ET.SubElement(root,'worldbody')
ET.SubElement(world,'light',pos='0 -1 1',dir='0 1 -1',diffuse='.8 .8 .8')
ET.SubElement(world,'light',pos='1 1 1',dir='-1 -1 -1',diffuse='.5 .5 .5')
body=copy.deepcopy(source.find(".//body[@name='right_wrist_yaw_link']"))
body.set('pos','0 0 0');body.set('quat','1 0 0 0')
for joint in body.findall('joint'):body.remove(joint)
world.append(body)
path=HERE/'hand_inspection.xml';ET.indent(root);ET.ElementTree(root).write(path,encoding='unicode')
model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model)
renderer=mujoco.Renderer(model,height=800,width=900)
option=mujoco.MjvOption();option.geomgroup[0]=0
names=['right_hand_thumb_0_joint','right_hand_thumb_1_joint','right_hand_thumb_2_joint',
       'right_hand_index_0_joint','right_hand_index_1_joint','right_hand_middle_0_joint','right_hand_middle_1_joint']
poses={'open':[0,0,0,0,0,0,0],'curled':[.4,-.3,-.8,.8,1.,.8,1.]}
records=[]
for label,values in poses.items():
    for name,value in zip(names,values):
        j=model.joint(name)
        if not j.range[0]<=value<=j.range[1]:raise ValueError(name)
        data.joint(name).qpos[0]=value
    mujoco.mj_forward(model,data)
    visible=[]
    for geom in range(model.ngeom):
        if model.geom_group[geom]!=1:continue
        mesh=int(model.geom_dataid[geom]);start=int(model.mesh_vertadr[mesh]);count=int(model.mesh_vertnum[mesh])
        visible.append(model.mesh_vert[start:start+count]@data.geom_xmat[geom].reshape(3,3).T+data.geom_xpos[geom])
    points=np.vstack(visible);lo,hi=points.min(axis=0),points.max(axis=0)
    for azimuth in [25,150]:
        camera=mujoco.MjvCamera();camera.lookat[:]=(lo+hi)/2;camera.distance=np.linalg.norm(hi-lo)*2;camera.azimuth=azimuth;camera.elevation=-15
        renderer.update_scene(data,camera=camera,scene_option=option)
        target=HERE/f'{label}_{azimuth}.png';Image.fromarray(renderer.render()).save(target)
        records.append(dict(image=target.name,joints=dict(zip(names,values)),static_only=True))
renderer.close()
(HERE/'previews.json').write_text(json.dumps(dict(scope=__doc__,frames=records,qualified=False),indent=2)+'\n')
