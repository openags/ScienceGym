"""Screen the existing D405 rig on recorded G1/three-finger poses.

The added rig is render geometry only. Robot/tool states are retained samples,
not a simulation with added camera mass, cables or clamp forces. Original room,
hand, camera housing, brackets and fasteners all occlude the candidate view.
Source-triangle intersections with the robot are a rejection screen, not full
containment, environment-clearance, mount-retention or motion qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
import trimesh

from robot_source_meshes import robot_source_meshes

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def numbers(v):return ' '.join(format(float(x),'.17g') for x in np.asarray(v).ravel())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output')
    p.add_argument('--times',type=float,nargs='+',default=[0.,15.,23.]);a=p.parse_args()
    run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'trace.npz')==result['trace_sha256'] and sha(run/'world.xml')==contract['model_sha256']
    trace=dict(np.load(run/'trace.npz'));source_model=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    source_meshes=robot_source_meshes(source_model,visual_groups=(1,2))
    assert 'right_hand_palm_link' in source_meshes
    rig_path=ROOT/'assets/g1_sensor_rig_v1/rig.json';adapter_path=rig_path.with_name('adapter.json')
    rig=json.loads(rig_path.read_text());adapter=json.loads(adapter_path.read_text())
    root=ET.parse(run/'world.xml').getroot();asset=root.find('asset');geometry=out/'geometry';geometry.mkdir()
    # Preserve all original file references after relocating the review XML.
    for node in root.iter():
        file=node.get('file')
        if file and not Path(file).is_absolute():node.set('file',str((run/file).resolve()))
    parts=[]
    for attachment in rig['attachments']:
        if not attachment['id'].startswith('right_'):continue
        assert sha(ROOT/attachment['geometry_path'])==attachment['geometry_sha256']
        parts.append(dict(id=attachment['id'],parent=attachment['parent_link'],
                          path=attachment['geometry_path'],sha256=attachment['geometry_sha256'],
                          transform=attachment['parent_from_geometry']))
        for hardware in attachment.get('hardware',[]):
            source=adapter['hardware'][hardware['kind']]
            assert sha(ROOT/source['path'])==source['sha256']
            parts.append(dict(id=hardware['id'],parent=attachment['parent_link'],path=source['path'],sha256=source['sha256'],
                              transform=(np.array(attachment['parent_from_geometry'])@hardware['step_from_hardware']).tolist()))
    meshes={}
    for part in parts:
        mesh=trimesh.load(ROOT/part['path'],force='scene',process=False).to_geometry();meshes[part['id']]=mesh
        path=geometry/(part['id']+'.stl');mesh.export(path)
        name='review_rig_'+part['id'];T=np.array(part['transform']);q=Rotation.from_matrix(T[:3,:3]).as_quat()[[3,0,1,2]]
        ET.SubElement(asset,'mesh',name=name,file=str(path))
        parent=root.find(".//body[@name='"+part['parent']+"']");assert parent is not None
        ET.SubElement(parent,'geom',name=name,type='mesh',mesh=name,pos=numbers(T[:3,3]),quat=numbers(q),
                      rgba='0.25 0.25 0.25 1',group='2',contype='0',conaffinity='0',density='0')
        part.update(render_mesh_sha256=sha(path),render_faces=len(mesh.faces))
    optical=next(c for c in rig['optics'] if c['id']=='right_wrist_rgb');T=np.array(optical['parent_from_optical'])
    R=T[:3,:3]@np.diag([1.,-1.,-1.]);q=Rotation.from_matrix(R).as_quat()[[3,0,1,2]]
    profile=optical['profile'];parent=root.find(".//body[@name='"+optical['parent_link']+"']")
    ET.SubElement(parent,'camera',name='review_right_wrist_rgb',pos=numbers(T[:3,3]),quat=numbers(q),
                  resolution=f"{profile['width']} {profile['height']}",sensorsize='1 1',
                  focalpixel=numbers([profile['fx_px'],profile['fy_px']]),principalpixel='0 0')
    path=out/'view_model.xml';ET.ElementTree(root).write(path,encoding='unicode')
    model=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(model)
    assert model.nq==source_model.nq and model.nv==source_model.nv
    assert [model.joint(j).name for j in range(model.njnt)]==[source_model.joint(j).name for j in range(source_model.njnt)]
    manager=trimesh.collision.CollisionManager()
    for name,mesh in source_meshes.items():manager.add_object(name,mesh)
    tool={model.body('tweezer').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in tool:tool.add(b)
    tool_geoms=np.flatnonzero(np.isin(model.geom_bodyid,list(tool)))
    renderer=mujoco.Renderer(model,height=profile['height'],width=profile['width'],max_geom=model.ngeom+1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0;rows=[]
    try:
        for requested in a.times:
            if not 0<=requested<=trace['time'][-1]:raise ValueError('Requested pose outside recording')
            i=int(np.searchsorted(trace['time'],requested));data.qpos[:]=trace['qpos'][i];mujoco.mj_forward(model,data)
            for name in source_meshes:
                body=data.body(name);world=np.eye(4);world[:3,:3]=body.xmat.reshape(3,3);world[:3,3]=body.xpos
                manager.set_transform(name,world)
            collisions=[]
            for part in parts:
                body=data.body(part['parent']);world=np.eye(4);world[:3,:3]=body.xmat.reshape(3,3);world[:3,3]=body.xpos
                hit,names=manager.in_collision_single(meshes[part['id']],world@part['transform'],return_names=True)
                if hit:collisions.append(dict(part=part['id'],robot_links=sorted(names)))
            renderer.update_scene(data,camera='review_right_wrist_rgb',scene_option=option);rgb=renderer.render().copy()
            renderer.enable_segmentation_rendering();seg=renderer.render().copy();renderer.disable_segmentation_rendering()
            mask=np.isin(seg[:,:,0],tool_geoms)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
            prefix=f'{requested:06.3f}s';Image.fromarray(rgb).save(out/(prefix+'_rgb.png'))
            Image.fromarray((mask*255).astype(np.uint8)).save(out/(prefix+'_evaluator_tool_mask.png'))
            row=dict(recorded_time_s=float(trace['time'][i]),evaluator_visible_tool_pixels=int(mask.sum()),
                     robot_surface_intersections=collisions,
                     files={n:sha(out/n) for n in [prefix+'_rgb.png',prefix+'_evaluator_tool_mask.png']})
            rows.append(row);print(json.dumps(row),flush=True)
    finally:renderer.close()
    shutil.copyfile(__file__,out/'screen_dex3_wrist_camera.py')
    report=dict(scope=__doc__,source_trace_sha256=result['trace_sha256'],rig_sha256=sha(rig_path),
                adapter_sha256=sha(adapter_path),source_sha256=sha(__file__),parts=parts,optical=optical,rows=rows,
                camera_intrinsics_reference='https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-camera',
                rig_mass_or_retention_simulated=False,active_installation=False,sensor_runtime_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
