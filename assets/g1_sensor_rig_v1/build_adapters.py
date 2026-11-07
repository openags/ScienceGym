"""Explicit G1 derivative of the Unitree camera bracket; never alter the robot.

The source half-ring contains inward tabs as well as an undersized bore. A
simple scale or bore cut cannot preserve its clamp fasteners. Retain the camera
arm above CAD Y=31 mm and replace the collar with two matched, bolted halves.
All authored dimensions below are millimetres until mesh export.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from convert_mounts import sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def cylinder(radius,height,origin,axis=(0,0,1)):
    return cq.Solid.makeCylinder(radius,height,cq.Vector(*origin),cq.Vector(*axis))


def export(shape,name,density):
    shape=shape.clean()
    assert shape.isValid() and len(shape.Solids())==1,name
    path=HERE/'geometry'/f'{name}.stl'
    cq.exporters.export(shape,str(path),tolerance=.025,angularTolerance=.10)
    mesh=trimesh.load(path,force='mesh');mesh.apply_scale(.001)
    mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_volume,name
    mesh.export(path)
    return dict(path=str(path.relative_to(ROOT)),sha256=sha(path),volume_m3=shape.Volume()*1e-9,
                mesh_volume_m3=float(mesh.volume),watertight=True,density_kg_m3=density,
                mass_kg=shape.Volume()*1e-9*density,center_of_mass_m=mesh.center_mass.tolist(),
                inertia_at_com_kg_m2=(mesh.moment_inertia*density).tolist())


def screw(length):
    # Local +Z from the bearing face towards the tip; unthreaded major envelope.
    shape=cylinder(2.75,3,(0,0,-3)).fuse(cylinder(1.5,length,(0,0,0)))
    socket=cq.Workplane('XY').polygon(6,2.5/np.cos(np.pi/6)).extrude(1.3).val().translate((0,0,-3))
    return shape.cut(socket)


def build():
    source=json.loads((HERE/'SOURCE.json').read_text());items=[]
    for side,key,z in [('left','right_wrist_D405_camera_mount',-20),('right','wrist_ring_mount',20)]:
        entry=next(e for e in source['files'] if e['path'].endswith(key+'.STEP'))
        source_path=HERE/entry['path'];assert sha(source_path)==entry['sha256']
        original=cq.importers.importStep(str(source_path)).val()
        retained=original.intersect(cq.Solid.makeBox(200,200,200,cq.Vector(-100,31,-100)))
        ring=cylinder(38.5,10,(0,0,z-5)).cut(cylinder(31.2,12,(0,0,z-6)))
        for suffix,sign in [('bracket',1),('clamp',-1)]:
            half=cq.Solid.makeBox(200,100,20,cq.Vector(-100,.5 if sign>0 else -100.5,z-10))
            shape=ring.intersect(half)
            for x in [-40,40]:
                shape=shape.fuse(cq.Solid.makeBox(11,6.5,10,cq.Vector(x-5.5,.5 if sign>0 else -7,z-5)))
                shape=shape.cut(cylinder(1.75,30,(x,-15,z),(0,1,0)))
            if suffix=='bracket':shape=shape.fuse(retained)
            geometry=export(shape,'adapter_'+side+'_'+suffix,930)
            # This is a new printable part. Source STEP files remain untouched.
            step_path=HERE/'geometry'/('adapter_'+side+'_'+suffix+'.step')
            cq.exporters.export(shape,str(step_path))
            items.append(dict(id=side+'_'+suffix,geometry=geometry,
                cad=dict(path=str(step_path.relative_to(ROOT)),sha256=sha(step_path)),
                source=dict(path=str(source_path.relative_to(ROOT)),sha256=sha(source_path)),
                frame='Source bracket STEP frame in metres',ring_center_m=[0,0,z*.001],
                retained_source_geometry='Original camera arm and camera mounting bores above CAD Y=31 mm' if suffix=='bracket' else None))
    hardware={}
    for length in [6,20]:hardware['m3x'+str(length)]=export(screw(length),'iso4762_m3x'+str(length),8000)
    washer=cylinder(3.5,.5,(0,0,0)).cut(cylinder(1.6,1,(0,0,-.25)))
    hardware['washer_m3']=export(washer,'iso7089_m3',8000)
    nut=cq.Workplane('XY').polygon(6,5.5/np.cos(np.pi/6)).extrude(2.4).val().cut(cylinder(1.5,3,(0,0,-.3)))
    hardware['nut_m3']=export(nut,'iso4032_m3',8000)
    result=dict(schema_version=1,status='authored_geometry_candidate_not_manufacturer_part',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'SOURCE.json',HERE/'hardware_sources.json']],
        design=dict(bore_radius_m=.0312,outer_radius_m=.0385,axial_width_m=.01,split_gap_m=.001,
            clamp_hole_x_m=[-.04,.04],clamp_hole_diameter_m=.0035,ear_outer_y_m=[-.007,.007],
            camera_arm_retained_above_step_y_m=.031,ring_center_wrist_x_m=.0365,
            material='Selected EOS PA 2200 PA12; full-density estimate 930 kg/m³; print tolerances and strength not certified',
            liner_reservation='Bore clearance reserves a compliant lining; liner preload, material and retention remain an explicit mechanical gate'),
        items=items,hardware=hardware,
        bom=[dict(part='authored left bracket',quantity=1),dict(part='authored right bracket',quantity=1),
             dict(part='authored clamp half',quantity=2),dict(part='ISO 4762 M3x6',quantity=4),
             dict(part='ISO 4762 M3x20',quantity=4),dict(part='ISO 4032 M3 nut',quantity=4),dict(part='ISO 7089 M3 washer',quantity=8)],
        fastener_stack=dict(camera=dict(screw_length_m=.006,plate_thickness_m=.003,engagement_m=.003,manufacturer_maximum_insertion_m=.004),
            clamp=dict(screw_length_m=.020,outer_ear_span_m=.014,washer_stack_m=.001,nut_height_m=.0024,tip_protrusion_m=.0026)),
        limitations=['New collar and fastener layout are an authored camera adaptation, not an official Unitree/Inspire installation.',
            'Threads use cylindrical major envelopes with recessed hex drives; no helical thread contact model.',
            'PA12 and steel densities are mass estimates; actual print porosity, preload, fatigue and cable loads remain unqualified.'])
    (HERE/'adapter.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(derived_parts=len(items),hardware_types=len(hardware))))


if __name__=='__main__':build()
