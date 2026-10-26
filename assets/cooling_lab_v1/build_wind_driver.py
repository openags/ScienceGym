"""Source-sized 7/16 inch driver, with an independently built real socket."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_tripod import hex_prism
from build_nut_driver import RED,STEEL
from check_weather_assets import load_parts


def build():
    g=Geometry();axis=cq.Vector(1,0,0);af=11.1925
    blade=cq.Solid.makeCone(7.95,8.25,.3,cq.Vector(0,0,0),axis)
    blade=blade.fuse(cq.Solid.makeCylinder(8.25,28.7,cq.Vector(.3,0,0),axis))
    blade=blade.fuse(cq.Solid.makeCone(8.25,3.75,6,cq.Vector(29,0,0),axis))
    blade=blade.fuse(cq.Solid.makeCylinder(3.75,97,cq.Vector(35,0,0),axis))
    bore=hex_prism(af,25.5).rotate((0,0,0),(0,1,0),90).translate((-.1,0,0))
    mouth=(cq.Workplane('XY').polygon(6,(af+.32)/np.cos(np.pi/6)).workplane(offset=.5)
        .polygon(6,af/np.cos(np.pi/6)).loft(combine=True).val().rotate((0,0,0),(0,1,0),90))
    solid(g,'steel_shaft_and_blind_socket',blade.cut(bore).cut(mouth),STEEL,metal=.85,role='source_sized_seven_sixteenths_socket')
    family=json.loads((HERE/'mast_driver_assets.json').read_text());source=load_parts(family['geometry'])
    for n in ['red_molded_core','black_soft_grip']:
        mesh=source[n].copy();g.scene.add_geometry(mesh,node_name=n,geom_name=n)
        g.parts.append(dict(id=n,role='shared_source_sized_handle_reconstruction',bounds_m=mesh.bounds.tolist()))
    label=g.label('size_text','7/16 in',.014,.005,[0,-.24605,0],RED,[240,240,235])
    label.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]));g.parts[-1]['bounds_m']=label.bounds.tolist()
    geometry=export_review(g,'wiha_34142_wind_nut_driver')
    refs=[Path(__file__),HERE/'wind_driver_sources.json',HERE/'mast_driver_assets.json',HERE/'build_nut_driver.py',HERE/'build_tripod.py',HERE/'build_supplies.py',HERE/'check_weather_assets.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_seven_sixteenths_nut_driver_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions_m=dict(drive_AF=.0111125,blade=.125,overall=.246,grip_diameter=.041),
        selected_geometry_m=dict(socket_AF=.0111925,socket_depth=.0254,entrance_AF=.0115125,entrance_depth=.0005,
            socket_outer_diameter=.0165,outer_socket_length=.035,shaft_diameter=.0075,shaft_embedded_length=.007,overmold_radial_thickness=.0012),
        shared_handle_reference=dict(geometry=family['geometry'],parts=['red_molded_core','black_soft_grip']),
        physical_parts=3,visual_labels=1,scope='Ordinary static tool candidate; no installed fit, tightening, grasp, torque or robot-use qualification.',
        staged_in_lab=False,initial_stock_credit=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'wind_driver_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
