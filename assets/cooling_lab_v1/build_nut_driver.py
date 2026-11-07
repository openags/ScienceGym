"""Ordinary source-sized 7 mm nut driver with a real blind hex socket."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.interpolate import PchipInterpolator
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_tripod import hex_prism

RED=[177,25,48];BLACK=[27,30,35];STEEL=[183,193,201]
PROFILE=np.array([[125,4.5],[128,5.0],[130,8.5],[132,13.5],[136,13.0],[149,10.5],[163,11.5],
    [179,15.4],[195,18.0],[207,17.9],[219,16.3],[229,14.0],[232,13.6],[236,11.9],[238,9.5]])*.001
RADIUS=PchipInterpolator(PROFILE[:,0],PROFILE[:,1]);SKIN=.0012


def cross_section(x,radius):
    theta=np.arange(128)*2*np.pi/128
    nearest=np.max(np.cos(theta[:,None]-np.arange(8)[None,:]*np.pi/4),axis=1)
    rr=radius*np.minimum(1,.975/nearest)
    return np.column_stack([np.full(len(theta),x),rr*np.cos(theta),rr*np.sin(theta)])


def loft(sections,inner=None):
    rings=[cross_section(x,r) for x,r in sections];n=128;faces=[]
    if inner is None:
        vertices=np.vstack(rings);first=len(vertices);vertices=np.vstack([vertices,[sections[0][0],0,0],[sections[-1][0],0,0]])
        for j in range(n):faces.extend([[first,(j+1)%n,j],[first+1,(len(rings)-1)*n+j,(len(rings)-1)*n+(j+1)%n]])
        blocks=[(0,len(rings))]
    else:
        vertices=np.vstack(rings+[cross_section(x,r) for x,r in inner]);offset=len(rings)*n;blocks=[(0,len(rings)),(offset,len(inner))]
        for i in [0,len(rings)-1]:
            for j in range(n):k=(j+1)%n;faces.extend([[i*n+j,offset+i*n+j,offset+i*n+k],[i*n+j,offset+i*n+k,i*n+k]])
    for offset,count in blocks:
        for i in range(count-1):
            for j in range(n):k=(j+1)%n;a=offset+i*n;faces.extend([[a+j,a+k,a+n+k],[a+j,a+n+k,a+n+j]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces);mesh.fix_normals();assert mesh.is_volume and len(mesh.split())==1
    return mesh


def blade():
    tip=cq.Solid.makeCone(4.875,5.175,.3,cq.Vector(0,0,0),cq.Vector(1,0,0))
    body=cq.Solid.makeCylinder(5.175,28.7,cq.Vector(.3,0,0),cq.Vector(1,0,0))
    neck=cq.Solid.makeCone(5.175,2.75,3,cq.Vector(29,0,0),cq.Vector(1,0,0))
    shaft=cq.Solid.makeCylinder(2.75,100,cq.Vector(32,0,0),cq.Vector(1,0,0))
    outer=tip.fuse(body).fuse(neck).fuse(shaft)
    bore=hex_prism(7.08,19.1).rotate((0,0,0),(0,1,0),90).translate((-.1,0,0))
    # A polygonal lead-in, not a circular hole painted black.
    entrance=(cq.Workplane('XY').polygon(6,7.4/np.cos(np.pi/6)).workplane(offset=.5)
        .polygon(6,7.08/np.cos(np.pi/6)).loft(combine=True).val().rotate((0,0,0),(0,1,0),90))
    return outer.cut(bore).cut(entrance)


def build():
    g=Geometry();solid(g,'steel_shaft_and_blind_socket',blade(),STEEL,metal=.85,role='source_sized_inferred_socket')
    before=np.linspace(.125,.163,55);inside=np.linspace(.163,.229,90);after=np.linspace(.229,.238,20)
    sections=[(x,float(RADIUS(x))) for x in before]+[(x,float(RADIUS(x)-SKIN)) for x in inside]+[(x,float(RADIUS(x))) for x in after]
    core=loft(sections)
    seat=trimesh.creation.cylinder(.00277,.0072,sections=96);seat.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));seat.apply_translation([.1285,0,0])
    core=trimesh.boolean.difference([core,seat],engine='manifold')
    g.add('red_molded_core',core,RED,role='source_topology_factory_molded_core')
    outer=[(x,float(RADIUS(x))) for x in inside];inner=[(x,float(RADIUS(x)-SKIN)) for x in inside]
    g.add('black_soft_grip',loft(outer,inner),BLACK,role='source_topology_dual_material_grip')
    # Original size text on a small flat cap. The red tail belongs to the hard
    # core; it is not a precision-driver rotating end cap.
    label=g.label('size_text','7 mm',.011,.005,[0,-.23805,0],RED,[240,240,235])
    matrix=trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]);label.apply_transform(matrix)
    g.parts[-1]['bounds_m']=label.bounds.tolist()
    geometry=export_review(g,'wiha_34123_nut_driver')
    refs=[Path(__file__),HERE/'nut_driver_sources.json',HERE/'build_supplies.py',HERE/'build_tripod.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_nut_driver_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions_m=dict(drive_AF=.007,blade=.125,overall=.238,grip_diameter=.036,socket_outer_diameter=.01035),
        selected_geometry_m=dict(socket_AF=.00708,socket_depth=.019,entrance_AF=.0074,entrance_depth=.0005,
            outer_socket_length=.032,shaft_diameter=.0055,shaft_embedded_length=.007,overmold_radial_thickness=SKIN),
        alternative_literal_inch_socket_diameter_m=.427*.0254,
        physical_parts=3,visual_labels=1,
        scope='Source-sized ordinary tool and factory construction topology. No tool motion, torque, grasp or installed clamp operation.',
        factory_bond_basis='Manufacturer describes direct molding and a permanent bond; strength and internal retention geometry are unqualified.',
        staged_in_lab=False,initial_stock_credit=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'nut_driver_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
