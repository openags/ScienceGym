"""Source-sized ordinary 1/2-inch nut driver for mast hardware inspection."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.interpolate import PchipInterpolator
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_tripod import hex_prism
from build_nut_driver import loft,PROFILE,RED,BLACK,STEEL


def build():
    g=Geometry();axis=cq.Vector(1,0,0)
    blade=cq.Solid.makeCone(8.95,9.25,.3,cq.Vector(0,0,0),axis)
    blade=blade.fuse(cq.Solid.makeCylinder(9.25,28.7,cq.Vector(.3,0,0),axis))
    blade=blade.fuse(cq.Solid.makeCone(9.25,3.75,6,cq.Vector(29,0,0),axis))
    blade=blade.fuse(cq.Solid.makeCylinder(3.75,97,cq.Vector(35,0,0),axis))
    bore=hex_prism(12.78,25.5).rotate((0,0,0),(0,1,0),90).translate((-.1,0,0))
    mouth=(cq.Workplane('XY').polygon(6,13.1/np.cos(np.pi/6)).workplane(offset=.5)
        .polygon(6,12.78/np.cos(np.pi/6)).loft(combine=True).val().rotate((0,0,0),(0,1,0),90))
    solid(g,'steel_shaft_and_blind_socket',blade.cut(bore).cut(mouth),STEEL,metal=.85,role='source_sized_inferred_socket')
    # The source shares the same family topology but has a distinct larger
    # catalogue envelope. Only the authored handle curve is parameterized;
    # blade length, drive bore and socket geometry are built independently.
    xp=.125+(PROFILE[:,0]-.125)*(.121/.113);rp=PROFILE[:,1]*(20.5/18)
    radius=PchipInterpolator(xp,rp);start=.125+(.163-.125)*(.121/.113);end=.125+(.229-.125)*(.121/.113)
    before=np.linspace(.125,start,55);inside=np.linspace(start,end,90);after=np.linspace(end,.246,20);skin=.0012
    sections=[(x,float(radius(x))) for x in before]+[(x,float(radius(x)-skin)) for x in inside]+[(x,float(radius(x))) for x in after]
    core=loft(sections);seat=trimesh.creation.cylinder(.00377,.0072,sections=96)
    seat.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));seat.apply_translation([.1285,0,0])
    core=trimesh.boolean.difference([core,seat],engine='manifold')
    g.add('red_molded_core',core,RED,role='source_topology_factory_molded_core')
    g.add('black_soft_grip',loft([(x,float(radius(x))) for x in inside],[(x,float(radius(x)-skin)) for x in inside]),BLACK,role='source_topology_dual_material_grip')
    label=g.label('size_text','1/2 in',.014,.005,[0,-.24605,0],RED,[240,240,235])
    label.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]));g.parts[-1]['bounds_m']=label.bounds.tolist()
    geometry=export_review(g,'wiha_34143_mast_nut_driver')
    refs=[Path(__file__),HERE/'mast_driver_sources.json',HERE/'build_nut_driver.py',HERE/'build_tripod.py',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_half_inch_nut_driver_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions_m=dict(drive_AF=.0127,blade=.125,overall=.246,grip_diameter=.041),
        selected_geometry_m=dict(socket_AF=.01278,socket_depth=.0254,entrance_AF=.0131,entrance_depth=.0005,
            socket_outer_diameter=.0185,outer_socket_length=.035,shaft_diameter=.0075,shaft_embedded_length=.007,overmold_radial_thickness=skin),
        physical_parts=3,visual_labels=1,scope='Ordinary static tool candidate; no tightening, thread movement, hand grasp or installed-use qualification.',
        staged_in_lab=False,initial_stock_credit=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'mast_driver_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
