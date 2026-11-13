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
from scipy.spatial import ConvexHull,HalfspaceIntersection
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[2]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def numbers(x):return ' '.join(format(float(v),'.17g') for v in x)


def source_part(scene,name):
    transform,key=scene.graph[name];mesh=scene.geometry[key].copy()
    mesh.apply_transform(transform)
    return clean(mesh)


def panel_cells(mesh,center,radius):
    """Partition a convex beveled source panel around its polygonal bore.

    Each cell is the source outer hull clipped by two radial planes and one
    source bore edge. The sectors do not overlap or fill the aperture. This
    avoids the near-zero-thickness tetrahedral cells at the original bevels.
    """
    center=np.asarray(center)[:2];xy=mesh.vertices[:,:2]
    bore_points=xy[abs(np.linalg.norm(xy-center,axis=1)-radius)<1e-7]
    bore_hull=ConvexHull(bore_points);polygon=bore_points[bore_hull.vertices]
    outer=ConvexHull(mesh.vertices)
    expected=outer.volume-bore_hull.volume*np.ptp(mesh.vertices[:,2])
    if abs(expected-mesh.volume)>max(1e-14,mesh.volume*1e-6):
        raise ValueError('Source is not the declared convex panel with a through bore')
    cells=[]
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        ra,rb=a-center,b-center;edge=b-a
        planes=[]
        for normal,point in [(np.r_[ra[1],-ra[0],0.],center),
                             (np.r_[-rb[1],rb[0],0.],center),
                             (np.r_[-edge[1],edge[0],0.],a)]:
            normal/=np.linalg.norm(normal);planes.append(np.r_[normal,-normal[:2]@point])
        constraints=np.vstack([outer.equations,planes])
        opt=linprog([0.,0.,0.,-1.],A_ub=np.c_[constraints[:,:3],np.linalg.norm(constraints[:,:3],axis=1)],
                    b_ub=-constraints[:,3],bounds=[(None,None)]*3+[(0.,None)],method='highs')
        if not opt.success or opt.x[-1]<1e-7:raise ValueError('Source panel sector has no robust interior')
        vertices=HalfspaceIntersection(constraints,opt.x[:3]).intersections
        cells.append(trimesh.convex.convex_hull(vertices))
    return cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    parser.add_argument('--ccd-tolerance',type=float,default=1e-6)
    parser.add_argument('--ccd-iterations',type=int,default=35)
    args=parser.parse_args()
    if not 1e-12<=args.ccd_tolerance<=1e-6 or not 35<=args.ccd_iterations<=1000:
        parser.error('CCD settings must retain or tighten the default convergence limits')
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
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
    # Blender's GLB export is Y-up; the published device interfaces are Z-up.
    # The specimen GLB is exported directly by trimesh and already uses Z-up.
    source_from_glb=np.array([[1.,0.,0.,0.],[0.,0.,-1.,0.],[0.,1.,0.,0.],[0.,0.,0.,1.]])
    plate.apply_transform(source_from_glb)
    cells=panel_cells(plate,port['center_m'],port['diameter_m']/2)
    if abs(sum(c.volume for c in cells)-plate.volume)>max(1e-12,plate.volume*1e-5):
        raise RuntimeError('Source panel cell volume differs')
    xml=ET.Element('mujoco',model='bare_optical_coupon_source_panel')
    ET.SubElement(xml,'compiler',angle='radian',inertiafromgeom='false')
    ET.SubElement(xml,'option',timestep='.0001',integrator='implicitfast',solver='Newton',
                  cone='elliptic',iterations='100',tolerance='1e-10',
                  ccd_tolerance=str(args.ccd_tolerance),ccd_iterations=str(args.ccd_iterations))
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
        samples=[];peak_pen=0.;peak_normal=0.;stable=0.;support_sum=0.;tail_count=0;outside_port=True
        tail_speed=0.;tail_angular_speed=0.
        for i in range(30000):
            mujoco.mj_step(m,d);support=0.;total_normal=0.
            for contact_index,c in enumerate(d.contact):
                f=np.zeros(6);mujoco.mj_contactForce(m,d,contact_index,f)
                sign=1. if m.geom_bodyid[c.geom[1]]==m.body('optical_witness_white').id else -1.
                support+=float(sign*(c.frame.reshape(3,3).T@f[:3])[2]);total_normal+=float(f[0])
                peak_pen=max(peak_pen,max(0.,-float(c.dist)))
                outside_port=outside_port and np.linalg.norm(c.pos[:2]-center[:2])>=port['diameter_m']/2-1e-5
            peak_normal=max(peak_normal,total_normal)
            if i>=25000:
                tail_count+=1;support_sum+=support
                speed=float(np.linalg.norm(d.qvel[:3]));angular_speed=float(np.linalg.norm(d.qvel[3:]))
                tail_speed=max(tail_speed,speed);tail_angular_speed=max(tail_angular_speed,angular_speed)
                if speed<.005 and angular_speed<.02:stable+=1
            if i%10==0:samples.append(np.r_[d.time,d.qpos,d.qvel])
        checks=dict(no_actuators=m.nu==0,no_equalities=m.neq==0,no_external_forces=not(np.any(d.xfrc_applied) or np.any(d.qfrc_applied)),
            no_numerical_warnings=not np.any(d.warning.number),bounded_penetration=peak_pen<=.00025,
            stable_last_half_second=stable==tail_count,
            bounded_total_contact_load=peak_normal<=1.,
            support_balances_weight=abs(support_sum/tail_count-mass*9.81)<=.05*mass*9.81,
            no_contact_inside_source_port=bool(outside_port),
            placement_retained=np.linalg.norm(d.qpos[:2]-center[:2]-offset)<.0001)
        checks={k:bool(v) for k,v in checks.items()}
        trials.append(dict(offset_m=offset,passed=all(checks.values()),checks=checks,
            peak_penetration_m=peak_pen,peak_total_contact_load_n=peak_normal,
            last_half_second_peak_speed_m_s=tail_speed,
            last_half_second_peak_angular_speed_rad_s=tail_angular_speed,
            last_half_second_stable_steps=stable,last_half_second_total_steps=tail_count,
            final_qpos=d.qpos.tolist(),mean_final_support_n=support_sum/tail_count))
        (out/f'trial_{k}.json').write_text(json.dumps(trials[-1],indent=2)+'\n')
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
        collision_solver=dict(ccd_tolerance_m=float(m.opt.ccd_tolerance),ccd_iterations=int(m.opt.ccd_iterations),
            documentation='https://mujoco.readthedocs.io/en/stable/computation/#convex-collisions',
            reason='Thin source paint layers require a numerical convergence check; geometry, friction, contact compliance and physical acceptance bounds are unchanged'),
        source_device_from_glb=source_from_glb.tolist(),
        partition='Nonoverlapping radial sectors of the actual beveled outer hull and source polygonal bore',
        actual_support_plane_m=plane,declared_interface_center_m=center.tolist(),
        interface_to_upper_surface_offset_m=float(plane-center[2]),
        parts=parts,mass_kg=float(mass),source_panel_cells=len(cells),trials=trials,
        world_sha256=sha(out/'world.xml'),trace_sha256=sha(out/'support_traces.npz'),script_sha256=sha(__file__),
        passed_component_support=all(r['passed'] for r in trials),qualified_robot_handling=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    if not result['passed_component_support']:raise SystemExit(1)


if __name__=='__main__':main()
