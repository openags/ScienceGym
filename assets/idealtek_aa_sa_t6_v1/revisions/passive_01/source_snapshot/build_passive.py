"""Manufacturer-sized tweezer candidate with passive elastic bending modes.

The two independent arms each use one end-load bending mode. Internal joint
couplings approximate a continuous steel beam; they do not attach the tool to
a robot or sample. Contact-driven accuracy, damping and large-deformation
behaviour remain unqualified. No selected laboratory asset is overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
import trimesh

HERE=Path(__file__).resolve().parent
LENGTH=.130
ROOT=np.array([LENGTH,0.,.00575])
FREE_LENGTH=.127
YOUNG=200e9
DENSITY=8000.
MASS=.018
KNOTS=np.array([0.,.016,.060,.105,FREE_LENGTH])


def profile(x,scale):
    width=np.interp(x,KNOTS,[.0005,.003,.0115,.011,.006])
    thickness=np.interp(x,KNOTS,[.0004,.0007*scale,.001*scale,.001*scale,.001])
    centers=[.0042,.0045,.00625-.001*scale/2,.0025,.0005]
    center=np.interp(x,KNOTS,centers)
    return float(width),float(thickness),float(center)


def segment(lo,hi,sign,scale):
    vertices=[]
    for x in [lo,hi]:
        width,thickness,center=profile(x,scale)
        for y,z in [(-thickness/2,-width/2),(thickness/2,-width/2),
                    (thickness/2,width/2),(-thickness/2,width/2)]:
            vertices.append([x,sign*(center+y),z+.00575])
    faces=[[0,3,2],[0,2,1],[4,5,6],[4,6,7]]
    for j in range(4):
        k=(j+1)%4;faces.extend([[j,k,4+k],[j,4+k,4+j]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    mesh.fix_normals()
    if not mesh.is_watertight or mesh.volume<=0:raise ValueError('Invalid beam segment')
    return mesh


def build(out,segments=20):
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise FileExistsError(out)
    out.mkdir(parents=True,exist_ok=True);(out/'meshes').mkdir()
    # Include all profile knots so no hidden shape interpolation changes at
    # a segment boundary. Additional points refine the visible bending mode.
    xs=np.array(sorted(set(np.linspace(0.,FREE_LENGTH,segments+1))|set(KNOTS),reverse=True))
    heel=trimesh.creation.box(extents=[.003,.002,.006]);heel.apply_translation([.1285,0.,.00575])
    def total_mass(scale):
        return DENSITY*(heel.volume+2*sum(segment(lo,hi,1,scale).volume for hi,lo in zip(xs[:-1],xs[1:])))
    scale=brentq(lambda s:total_mass(s)-MASS,.5,2.)
    xml=ET.Element('mujoco',model='Ideal-tek AA.SA.T.6 passive candidate')
    ET.SubElement(xml,'compiler',angle='radian',meshdir='meshes',autolimits='true')
    ET.SubElement(xml,'option',timestep='.002',integrator='implicitfast',iterations='100',tolerance='1e-10')
    default=ET.SubElement(xml,'default')
    ET.SubElement(default,'geom',type='mesh',density=str(DENSITY),friction='.225 .002 .0001',
                  priority='1',condim='4',solref='.004 1',solimp='.99 .99 .0001',rgba='.15 .17 .19 1')
    asset=ET.SubElement(xml,'asset');world=ET.SubElement(xml,'worldbody');equality=ET.SubElement(xml,'equality')
    root=ET.SubElement(world,'body',name='tweezer',pos='0 0 .15');ET.SubElement(root,'freejoint',name='tweezer_free')
    ET.SubElement(root,'geom',name='tweezer_heel',type='box',pos='-.0015 0 0',size='.0015 .001 .003')
    scene=trimesh.Scene();scene.add_geometry(heel,node_name='joined_heel',geom_name='joined_heel')
    parts=[];mode=[]
    for hi,lo in zip(xs[:-1],xs[1:]):
        def rigidity(x):
            width,thickness,_=profile(x,scale)
            return YOUNG*width*thickness**3/12.
        # Exact small-deflection compliance of this tapered span for an end
        # load. The hinge mode matches its contribution to tip deflection.
        compliance=quad(lambda x:x*x/rigidity(x),lo,hi,epsabs=1e-14)[0]
        angle_per_newton=compliance/hi
        mode.append(dict(lo_m=float(lo),hi_m=float(hi),tip_compliance_m_per_n=compliance,
                         angle_per_newton=angle_per_newton,hinge_stiffness_nm_rad=hi/angle_per_newton))
    reference=mode[0]['angle_per_newton']
    ratios=np.array([r['angle_per_newton']/reference for r in mode])
    modal_stiffness=float(sum(r['hinge_stiffness_nm_rad']*ratio**2 for r,ratio in zip(mode,ratios)))
    mode_rows=[]
    for sign,label in [(-1,'negative'),(1,'positive')]:
        parent=root;parent_anchor=ROOT.copy();anchors=[];mass_data=[]
        for index,(row,ratio) in enumerate(zip(mode,ratios)):
            hi,lo=row['hi_m'],row['lo_m'];_,_,center=profile(hi,scale)
            anchor=np.array([hi,sign*center,.00575]);anchors.append(anchor)
            body=ET.SubElement(parent,'body',name=f'{label}_beam_{index:02d}',
                               pos=' '.join(map(str,anchor-parent_anchor)))
            joint=f'{label}_bend_{index:02d}'
            ET.SubElement(body,'joint',name=joint,type='hinge',axis='0 0 1',limited='false')
            if index:
                ET.SubElement(equality,'joint',name=f'{label}_mode_{index:02d}',joint1=joint,
                              joint2=f'{label}_bend_00',polycoef=f'0 {ratio:.17g} 0 0 0',
                              solref='.004 1',solimp='.9999 .9999 .00001')
            mesh=segment(lo,hi,sign,scale);mesh.density=DENSITY
            mesh.visual.vertex_colors=[76,80,85,255]
            name=f'{label}_steel_arm_{index:02d}'
            scene.add_geometry(mesh,node_name=name,geom_name=name)
            mass_data.append((mesh.mass,mesh.center_mass.copy(),float(mesh.moment_inertia[2,2])))
            local=mesh.copy();local.apply_translation(-anchor);local.export(out/'meshes'/f'{name}.stl')
            ET.SubElement(asset,'mesh',name=name,file=name+'.stl')
            ET.SubElement(body,'geom',name=name,mesh=name)
            parts.append(dict(name=name,nominal_mass_kg=mesh.mass,source_profile_bounds_m=mesh.bounds.tolist()))
            parent,parent_anchor=body,anchor
        modal_inertia=0.
        for index,(mass,center,inertia) in enumerate(mass_data):
            jacobian=sum(ratios[j]*np.cross([0.,0.,1.],center-anchors[j]) for j in range(index+1))
            modal_inertia+=mass*float(jacobian@jacobian)+inertia*float(np.sum(ratios[:index+1]))**2
        # Damping is an explicit model assumption; material TDS supplies E,
        # not a measured assembled-tool damping ratio or force curve.
        damping_ratio=.10;damping=2*damping_ratio*np.sqrt(modal_stiffness*modal_inertia)
        master=root.find(f".//joint[@name='{label}_bend_00']")
        master.set('stiffness',str(modal_stiffness));master.set('damping',str(damping))
        mode_rows.append(dict(arm=label,hinge_ratios=ratios.tolist(),modal_stiffness_nm_rad=modal_stiffness,
                              modal_inertia_kg_m2=modal_inertia,inferred_damping_ratio=damping_ratio,
                              modal_damping_nms_rad=float(damping)))
    ET.indent(xml);ET.ElementTree(xml).write(out/'tool.xml',encoding='unicode')
    scene.export(out/'rest_geometry.glb')
    model=mujoco.MjModel.from_xml_path(str(out/'tool.xml'));data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    bounds=scene.bounds;total=float(model.body_mass.sum())
    tip_gap=2*(profile(0.,scale)[2]-profile(0.,scale)[1]/2)
    checks=dict(compiles=True,no_actuators=model.nu==0,no_runtime_attachment_equalities=all(int(v)==int(mujoco.mjtEq.mjEQ_JOINT) for v in model.eq_type),
                nominal_mass=abs(total-MASS)<1e-8,manufacturer_envelope=bool(np.allclose(np.ptp(bounds,axis=0),[.130,.0125,.0115],atol=2e-8)),
                manufacturer_tip_gap=abs(tip_gap-.008)<1e-10,
                manufacturer_tip_section=np.allclose(profile(0.,scale)[:2],[.0005,.0004],atol=1e-12))
    record=dict(schema='sciencegym.passive_tool_candidate.v1',scope=__doc__,checks={k:bool(v) for k,v in checks.items()},
                passed_geometry_and_compilation=all(checks.values()),root_in_asset_m=ROOT.tolist(),
                inferred_interior_thickness_scale=scale,compiled_mass_kg=total,rest_bounds_m=bounds.tolist(),
                unloaded_inner_tip_gap_m=tip_gap,body_material='PTFE-coated 316L steel',
                one_arm_end_load_compliance_m_per_n=float(sum(r['tip_compliance_m_per_n'] for r in mode)),
                mode_discretization=mode,arms=mode_rows,parts=parts,qualified_contact_dynamics=False,
                limitations=['One planar end-load bending mode per arm; grip-position and torsion effects need validation',
                             'Interior profile chosen to match nominal mass; coating thickness and mass not measured',
                             'Damping and pairwise friction remain assumptions; no calibrated force curve',
                             'No robot grasp, specimen retention or complete paper-task credit'],
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'sources.json']})
    (out/'model_review.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['checks','compiled_mass_kg','unloaded_inner_tip_gap_m','one_arm_end_load_compliance_m_per_n']}),flush=True)
    if not all(checks.values()):raise ValueError('Geometry or model compilation checks failed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('--segments',type=int,default=20);a=p.parse_args();build(a.out,a.segments)
