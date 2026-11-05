"""Build a free optical coupon and test support on the actual PIKE source panel.

Component development only: no robot handling, fabrication, accessory mounting,
instrument acquisition or paper-branch qualification. The existing annular
presentation holder is not adopted as a physically qualified fixture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import trimesh

from convex_cells import clean

ROOT=Path(__file__).resolve().parents[2]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def numbers(x):return ' '.join(format(float(v),'.17g') for v in x)


def source_part(scene,name):
    transform,key=scene.graph[name];mesh=scene.geometry[key].copy()
    mesh.apply_transform(transform)
    return clean(mesh)


def extruded_panel_cells(mesh):
    """Extrude the actual upper triangles; preserve the source aperture.

    A thin constant-thickness panel needs no tetrahedral slivers. This is a
    partition of its existing triangles, without an enlarged collision hull.
    """
    low,high=mesh.bounds[:,2]
    if np.max(np.minimum(abs(mesh.vertices[:,2]-low),abs(mesh.vertices[:,2]-high)))>1e-9:
        raise ValueError('Source panel is not a constant-thickness extrusion')
    faces=np.asarray([[0,2,1],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]])
    cells=[]
    for triangle in mesh.triangles:
        if not np.all(abs(triangle[:,2]-high)<1e-9):continue
        top=triangle.copy();bottom=triangle.copy();bottom[:,2]=low
        cell=trimesh.Trimesh(vertices=np.vstack([bottom,top]),faces=faces,process=True)
        cell.fix_normals()
        if not cell.is_volume or cell.volume<=0:raise ValueError('Degenerate source top triangle')
        cells.append(cell)
    return cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,out/Path(__file__).name)
    shutil.copyfile(Path(__file__).with_name('convex_cells.py'),out/'convex_cells.py')
    specimen_source=ROOT/'assets/cooling_optical_specimens_v1/witness_white.glb'
    panel_source=ROOT/'assets/pike_integratir_dtgs_v1/geometry/pike_integratir_dtgs.glb'
    specimen_manifest=ROOT/'assets/cooling_optical_specimens_v1/manifest.json'
    interfaces_path=ROOT/'assets/pike_integratir_dtgs_v1/interfaces.json'
    manifest=json.loads(specimen_manifest.read_text())
    expected=next(a for a in manifest['assets'] if a['id']=='optical_witness_white')['sha256']
    assert sha(specimen_source)==expected
    interfaces=json.loads(interfaces_path.read_text())
    port=next(i for i in interfaces['interfaces'] if i['id']=='sample_port')
    source=trimesh.load(specimen_source,force='scene',process=False)
    components={n:source_part(source,n) for n in ['copper_witness','paint_coat_1','paint_coat_2','paint_coat_3']}
    plate=source_part(trimesh.load(panel_source,force='scene',process=False),'top_sample_panel')
    cells=extruded_panel_cells(plate)
    if abs(sum(c.volume for c in cells)-plate.volume)>max(1e-12,plate.volume*1e-5):
        raise RuntimeError('Source panel cell volume differs')
    xml=ET.Element('mujoco',model='bare_optical_coupon_source_panel')
    ET.SubElement(xml,'compiler',angle='radian',inertiafromgeom='false')
    ET.SubElement(xml,'option',timestep='.0001',integrator='implicitfast',solver='Newton',
                  cone='elliptic',iterations='100',tolerance='1e-10')
    asset=ET.SubElement(xml,'asset');world=ET.SubElement(xml,'worldbody')
    ET.SubElement(world,'light',pos='0 -.3 .7',dir='0 0 -1',diffuse='.7 .7 .7')
    plate.export(out/'source_panel.obj');ET.SubElement(asset,'mesh',name='source_panel',file='source_panel.obj')
    ET.SubElement(world,'geom',name='source_panel_visual',type='mesh',mesh='source_panel',
                  contype='0',conaffinity='0',group='2',rgba='.45 .48 .50 1')
    for i,cell in enumerate(cells):
        name=f'panel_cell_{i}';origin=cell.vertices.mean(axis=0);local=cell.copy();local.apply_translation(-origin)
        (out/(name+'.obj')).write_text(trimesh.exchange.obj.export_obj(local,digits=17))
        ET.SubElement(asset,'mesh',name=name,file=name+'.obj')
        ET.SubElement(world,'geom',name=name,type='mesh',mesh=name,pos=numbers(origin),group='3',
                      friction='.3 .002 .0001',solref='.002 1',solimp='.9999 .9999 .0001')
    body=ET.SubElement(world,'body',name='optical_witness_white')
    ET.SubElement(body,'freejoint',name='optical_witness_white_free')
    inertia=[];parts=[]
    for name,mesh in components.items():
        if not mesh.is_volume:raise RuntimeError('Coupon component is not a closed volume: '+name)
        density=8960. if name=='copper_witness' else 1200.
        mass=mesh.volume*density;I=mesh.moment_inertia*density
        inertia.append((mass,mesh.center_mass,I));parts.append(dict(name=name,mass_kg=float(mass),
            density_kg_m3=density,volume_m3=float(mesh.volume),density_origin='Unmeasured engineering assumption'))
        mesh.export(out/(name+'.obj'));ET.SubElement(asset,'mesh',name=name,file=name+'.obj')
        ET.SubElement(body,'geom',name=name,type='mesh',mesh=name,
            rgba='.65 .30 .12 1' if name=='copper_witness' else '.76 .75 .70 1',
            friction='.3 .002 .0001',solref='.002 1',solimp='.9999 .9999 .0001')
    mass=sum(v[0] for v in inertia);com=sum(m*c for m,c,I in inertia)/mass
    moment=sum(I+m*(np.dot(c-com,c-com)*np.eye(3)-np.outer(c-com,c-com)) for m,c,I in inertia)
    ET.SubElement(body,'inertial',mass=str(mass),pos=numbers(com),fullinertia=numbers(
        [moment[0,0],moment[1,1],moment[2,2],moment[0,1],moment[0,2],moment[1,2]]))
    ET.indent(xml);ET.ElementTree(xml).write(out/'world.xml',encoding='unicode')
    m=mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    center=np.asarray(port['center_m']);bottom=min(v.bounds[0,2] for v in components.values())
    plane=float(plate.bounds[1,2]);trials=[];traces=[]
    for k,offset in enumerate([[0.,0.],[.001,0.],[-.001,0.],[0.,.001],[0.,-.001]]):
        d=mujoco.MjData(m);d.qpos[:3]=[center[0]+offset[0],center[1]+offset[1],plane-bottom+.002]
        d.qpos[3]=1.;mujoco.mj_forward(m,d)
        samples=[];peak_pen=0.;stable=0.;support_sum=0.;tail_count=0;outside_port=True
        for i in range(30000):
            mujoco.mj_step(m,d);support=0.
            for contact_index,c in enumerate(d.contact):
                f=np.zeros(6);mujoco.mj_contactForce(m,d,contact_index,f)
                support+=float(f[0]);peak_pen=max(peak_pen,max(0.,-float(c.dist)))
                outside_port=outside_port and np.linalg.norm(c.pos[:2]-center[:2])>=port['diameter_m']/2-1e-5
            if i>=25000:
                tail_count+=1;support_sum+=support
                if np.linalg.norm(d.qvel[:3])<.005 and np.linalg.norm(d.qvel[3:])<.02:stable+=1
            if i%10==0:samples.append(np.r_[d.time,d.qpos,d.qvel])
        checks=dict(no_actuators=m.nu==0,no_equalities=m.neq==0,no_external_forces=not(np.any(d.xfrc_applied) or np.any(d.qfrc_applied)),
            no_numerical_warnings=not np.any(d.warning.number),bounded_penetration=peak_pen<=.00025,
            stable_last_half_second=stable==tail_count,
            support_balances_weight=abs(support_sum/tail_count-mass*9.81)<=.05*mass*9.81,
            no_contact_inside_source_port=bool(outside_port),
            placement_retained=np.linalg.norm(d.qpos[:2]-center[:2]-offset)<.0001)
        trials.append(dict(offset_m=offset,passed=all(checks.values()),checks=checks,
            peak_penetration_m=peak_pen,final_qpos=d.qpos.tolist(),mean_final_support_n=support_sum/tail_count))
        traces.append(np.asarray(samples));print('support_trial',k,all(checks.values()),flush=True)
    np.savez_compressed(out/'support_traces.npz',**{f'trial_{i}':v for i,v in enumerate(traces)})
    result=dict(scope=__doc__,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in
        [specimen_source,panel_source,specimen_manifest,interfaces_path]},
        source_manual='https://www.piketech.com/files/user-manuals/MidIntegratIRwDTGSManual.pdf',
        source_manual_locator='PN 350-048400-01 (2012), printed pages 1 and 4: flat specimens can be supported directly on the upper port',
        reconstruction='25 mm coupon from selected 0.5 mm copper stock, three inferred paint layers; no annular holder in this candidate',
        optical_scope='Only physical support is checked. No optical response, measured paint properties or contamination qualification.',
        inferred_dynamics=dict(copper_density_kg_m3=8960.,paint_density_kg_m3=1200.,
            friction=[.3,.002,.0001],contact_solref=[.002,1.],
            note='Unmeasured development parameters, not vendor calibration; panel held stationary for this component diagnostic'),
        parts=parts,mass_kg=float(mass),source_panel_cells=len(cells),trials=trials,
        world_sha256=sha(out/'world.xml'),trace_sha256=sha(out/'support_traces.npz'),script_sha256=sha(__file__),
        passed_component_support=all(r['passed'] for r in trials),qualified_robot_handling=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed_component_support']:raise SystemExit(1)


if __name__=='__main__':main()
