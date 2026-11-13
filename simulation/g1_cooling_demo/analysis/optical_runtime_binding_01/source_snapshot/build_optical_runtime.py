"""Bind an installed FTIR accessory and a free specimen into the existing lab.

This constructs an explicit initial configuration, not an installation or robot
execution receipt. The reference remains a named, unimplemented dynamic binding.
The full room, G1, ordinary tray and passive tweezer are retained. No state is
written after simulation starts by this builder.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh

from build_tool_station import absolve_assets, free_pose, numbers, pose, sha

ROOT=Path(__file__).resolve().parents[2]


def transform_body(parent,name,T):
    q=free_pose(T)
    return ET.SubElement(parent,'body',name=name,pos=numbers(q[:3]),quat=numbers(q[3:]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('base_run',type=Path);p.add_argument('component_run',type=Path)
    p.add_argument('output',type=Path);a=p.parse_args()
    base,component,out=[v.resolve() for v in [a.base_run,a.component_run,a.output]]
    bc=json.loads((base/'contract.json').read_text())
    cr=json.loads((component/'review.json').read_text())
    assert sha(base/'world.xml')==bc['model_sha256']
    assert cr['passed_component_support'] and len(cr['trials'])==5
    assert sha(component/'world.xml')==cr['world_sha256']
    assert sha(component/'support_traces.npz')==cr['trace_sha256']
    for path,digest in cr['source_hashes'].items():assert sha(ROOT/path)==digest
    imported=json.loads((base/'laboratory_import.json').read_text())
    assert sha(base/'laboratory_import.json')==bc['laboratory_import_sha256']
    scene_path=ROOT/'assets/cooling_lab_v1/scene.json'
    setup_path=ROOT/'viewer/cooling_concept_v2/optical_setup.json'
    scene=json.loads(scene_path.read_text());setup=json.loads(setup_path.read_text())
    pike=next(v for v in scene['assets'] if v['id']=='pike')
    assert sha(ROOT/pike['geometry'])==pike['geometry_sha256']==setup['source_geometry_sha256']['pike']
    assert imported['source_inputs'][pike['geometry']]==pike['geometry_sha256']
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for source in [Path(__file__),Path(__file__).with_name('build_tool_station.py'),setup_path,
                   component/'review.json',base/'contract.json']:
        name=('component_review.json' if source==component/'review.json' else
              'base_contract.json' if source==base/'contract.json' else source.name)
        shutil.copyfile(source,snapshot/name)
    xml=ET.parse(base/'world.xml').getroot();absolve_assets(xml,base/'world.xml')
    cx=ET.parse(component/'world.xml').getroot();absolve_assets(cx,component/'world.xml')
    parent=xml.find(".//body[@name='lab_pike']");assert parent is not None
    parts=[v for v in imported['parts'] if v['instance']=='pike']
    assert {v['source_part'] for v in parts}==set(setup['parts']['pike'])
    transformations=[];part_bodies={}
    # The authored installed transform applies to source geometry within the
    # existing lab_pike frame. Preserve each mesh and apply a rigid transform.
    for record in parts:
        name=record['source_part'];geom=parent.find(f"geom[@name='{record['geom']}']")
        if geom is None:raise ValueError('Source part is missing or already rebound: '+name)
        T=np.asarray(setup['parts']['pike'][name]['matrix'],dtype=float)
        if not np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-12):
            raise ValueError('Installed transform scales the source asset')
        b=transform_body(parent,'installed_pike_'+name,T);parent.remove(geom);b.append(geom)
        part_bodies[name]=b
        transformations.append(dict(source_part=name,geom=record['geom'],matrix=T.tolist(),
            reason=setup['parts']['pike'][name]['reason']))
    # Replace the filled convex hull of the sample-port panel by the exact
    # radial source partition tested by the component diagnostic.
    panel=part_bodies['top_sample_panel'];panel.find('geom').set('contype','0')
    panel.find('geom').set('conaffinity','0')
    N=np.asarray(pike['normalization_matrix'])
    normalized=transform_body(panel,'installed_pike_panel_source_frame',N)
    meshes={v.get('name'):v for v in cx.findall('asset/mesh')}
    copied=set()
    def copy_mesh(name):
        if name in copied:return
        mesh=deepcopy(meshes[name]);mesh.set('name','optical_'+name)
        xml.find('asset').append(mesh);copied.add(name)
    for geom in cx.findall('worldbody/geom'):
        if not geom.get('name','').startswith('panel_cell_'):continue
        g=deepcopy(geom);copy_mesh(g.get('mesh'));g.set('mesh','optical_'+g.get('mesh'))
        g.set('name','optical_'+g.get('name'));normalized.append(g)
    # Preserve the real alignment-pin opening of the inferred mount. A single
    # convex hull around all four pieces would incorrectly close the opening.
    plate=setup['mount_plate'];mesh=trimesh.Trimesh(vertices=plate['vertices'],faces=plate['faces'],process=False)
    lab=xml.find(".//body[@name='laboratory_map']");assert lab is not None
    pieces=mesh.split(only_watertight=False)
    if len(pieces)!=4 or any(not v.is_volume for v in pieces):
        raise ValueError('Expected four closed pieces around the mount opening')
    for i,v in enumerate(pieces):
        name=f'optical_mount_plate_{i}';path=out/(name+'.obj')
        path.write_text(trimesh.exchange.obj.export_obj(v,digits=17))
        ET.SubElement(xml.find('asset'),'mesh',name=name,file=str(path))
        ET.SubElement(lab,'geom',name=name,type='mesh',mesh=name,
            rgba='.08 .10 .12 1',friction='.3 .002 .0001',solref='.002 1',solimp='.99 .99 .0001')
    # This is a declared pre-existing optical specimen for a handling episode.
    # Its fabrication/coating remains an outstanding full-paper obligation.
    coupon=deepcopy(cx.find("worldbody/body[@name='optical_witness_white']"))
    for g in coupon.iter('geom'):
        copy_mesh(g.get('mesh'));g.set('mesh','optical_'+g.get('mesh'))
        g.set('name','optical_'+g.get('name'))
    xml.find('worldbody').append(coupon)
    xml.find('option').set('ccd_tolerance',str(cr['collision_solver']['ccd_tolerance_m']))
    xml.find('option').set('ccd_iterations',str(cr['collision_solver']['ccd_iterations']))
    if xml.find('keyframe') is not None:
        raise ValueError('Keyframe lengths require explicit remapping before adding a free body')
    ET.indent(xml);ET.ElementTree(xml).write(out/'world.xml',encoding='unicode')
    m=mujoco.MjModel.from_xml_path(str(out/'world.xml'));d=mujoco.MjData(m)
    bm=mujoco.MjModel.from_xml_path(str(base/'world.xml'));bd=mujoco.MjData(bm)
    bd.qpos[:]=bc['initial_qpos'];bd.qvel[:]=bc['initial_qvel']
    for j in range(bm.njnt):
        name=bm.joint(j).name;d.joint(name).qpos[:]=bd.joint(name).qpos;d.joint(name).qvel[:]=bd.joint(name).qvel
    mujoco.mj_forward(m,d)
    tray=d.body('carrier_tray');R=tray.xmat.reshape(3,3)
    ray_origin=tray.xpos+R@np.array([-.06,.04,.2]);direction=-R[:,2]
    # Inspect only the existing tray surface to select an authored initial
    # position. Restore geom groups before writing the scene or simulating it.
    groups=m.geom_group.copy();m.geom_group[:]=0
    m.geom_group[m.geom_bodyid==m.body('carrier_tray').id]=5
    hit=np.array([-1],dtype=np.int32)
    distance=mujoco.mj_ray(m,d,ray_origin,direction,np.array([0,0,0,0,0,1],dtype=np.uint8),1,-1,hit)
    m.geom_group[:]=groups
    if distance<0:raise ValueError('Selected specimen position has no tray support')
    support=ray_origin+distance*direction
    bottom=min(trimesh.load(component/(name+'.obj'),process=False).bounds[0,2]
               for name in ['copper_witness','paint_coat_1','paint_coat_2','paint_coat_3'])
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=support+R[:,2]*(.002-bottom)
    d.joint('optical_witness_white_free').qpos[:]=free_pose(T)
    mujoco.mj_forward(m,d)
    cid=m.body('optical_witness_white').id
    bad=[dict(geoms=[m.geom(g).name for g in c.geom],distance_m=float(c.dist))
         for c in d.contact if cid in m.geom_bodyid[c.geom] and c.dist<0]
    if bad:raise ValueError('Initial specimen intersects existing geometry: '+str(bad))
    initial=dict(qpos=d.qpos.tolist(),qvel=d.qvel.tolist(),scope='Authored initial configuration, not a robot placement')
    (out/'initial_state.json').write_text(json.dumps(initial,indent=2)+'\n')
    inputs={str(Path(n.get('file'))):sha(n.get('file')) for n in xml.find('asset') if n.get('file')}
    (out/'model_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    work_from_lab=np.linalg.inv(np.asarray(imported['lab_from_work']))
    port=np.r_[setup['ports']['ftir_sample']['position_m'],1.]
    report=dict(scope=__doc__,environment='existing_complete_laboratory',
        base_model_sha256=bc['model_sha256'],base_contract_sha256=sha(base/'contract.json'),
        component_review_sha256=sha(component/'review.json'),optical_setup_sha256=sha(setup_path),
        scene_sha256=sha(scene_path),world_sha256=sha(out/'world.xml'),
        initial_state_sha256=sha(out/'initial_state.json'),model_inputs_sha256=sha(out/'model_inputs.json'),
        source_snapshot_sha256={v.name:sha(v) for v in snapshot.iterdir()},
        installed_part_transforms=transformations,installed_source_panel_cells=cr['source_panel_cells'],
        ftir_sample_port_work_m=(work_from_lab@port)[:3].tolist(),
        specimen_initial_support=dict(body='carrier_tray',geom=m.geom(int(hit[0])).name,
            point_work_m=support.tolist(),initial_release_gap_m=.002),
        actuator_count=int(m.nu),base_actuator_count=int(bm.nu),
        initial_specimen_penetrations=bad,installation_assumptions=setup['assumptions'],
        unresolved=['Gold reference and cap still require passive dynamic models and manipulation',
            'Accessory mounting, detector cable mating and optical alignment unqualified',
            'Full-scene specimen settling and robot handling not executed',
            'Initial specimen does not discharge full-paper fabrication/coating obligations',
            'Other paper branches retain their complete existing scope'],
        qualified_installation=False,qualified_robot_handling=False,qualified_paper_branch=False)
    assert m.nu==bm.nu==43
    (out/'binding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),actuators=int(m.nu),free_specimen=True,
        installed_panel_cells=cr['source_panel_cells'],qualified_paper_branch=False)),flush=True)


if __name__=='__main__':main()
