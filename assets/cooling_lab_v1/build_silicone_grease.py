"""Build one sourced silicone-grease tube with two density/fill hypotheses."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import solid, export_review
from build_mast_grease import loft

SECTIONS=[(7,10.2,10.2),(20,10.2,10.2),(30,17,16),(65,20.5,16),
          (105,24,14),(128,26,8),(137,27,.7),(138,27,.65)]
INSIDE=[(6.9,8,8),(20,8,8),(30,16.6,15.6),(65,20.1,15.6),
        (105,23.6,13.6),(128,25.6,7.6),(135.8,26.5,.3)]


def container():
    cavity=loft(INSIDE);body=loft(SECTIONS).cut(cavity)
    helix=cq.Wire.makeHelix(2,6,10.4,center=cq.Vector(0,0,9))
    ridge=cq.Workplane('XZ',origin=(10.4,0,9)).circle(.6).sweep(cq.Workplane(obj=helix),isFrenet=True).val()
    body=body.fuse(ridge)
    seal=cq.Solid.makeBox(54,1.3,14,cq.Vector(-27,-.65,138))
    slot=cq.Workplane('XZ',origin=(0,2,143.5)).slot2D(27,5.5).extrude(4).val()
    crown=cq.Solid.makeCylinder(3.5,4,cq.Vector(0,2,145.4),cq.Vector(0,-1,0))
    body=body.fuse(seal.cut(slot.fuse(crown)))
    cap=cq.Workplane('XY').circle(15.3).extrude(16).edges('%Circle').fillet(.7).val()
    cap=cap.cut(cq.Solid.makeCylinder(11.3,15,cq.Vector(0,0,2)))
    for a in np.linspace(0,2*np.pi,64,endpoint=False):
        cap=cap.fuse(cq.Solid.makeCylinder(.36,11,cq.Vector(15.3*np.cos(a),15.3*np.sin(a),2.5)))
    liner=cq.Solid.makeCylinder(11.2,5,cq.Vector(0,0,2)).cut(cq.Solid.makeCylinder(8,5.2,cq.Vector(0,0,1.9)))
    return body,cap,liner,cavity


def label(g):
    picture=Image.new('RGBA',(768,1536),(0,0,0,0));draw=ImageDraw.Draw(picture)
    for y,text,size in [(130,'Super Lube',72),(285,'93003',66),(500,'O-RING',76),
                        (650,'SILICONE',65),(790,'GREASE',70),(1110,'85 g',70)]:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        draw.text((384,y),text,fill=(28,33,31,255),font=font,anchor='mm')
    vertices=[];uv=[];faces=[];data=np.array(SECTIONS)
    for j,z in enumerate(np.linspace(30,130,52)):
        rx=np.interp(z,data[:,0],data[:,1])+.025;ry=np.interp(z,data[:,0],data[:,2])+.025
        for i,a in enumerate(np.linspace(-.8,.8,33)):
            vertices.append([rx*np.sin(a)*.001,-ry*np.cos(a)*.001,z*.001]);uv.append([i/32,j/51])
            if i<32 and j<51:
                n=j*33+i;faces.extend([[n,n+1,n+34],[n,n+34,n+33]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    g.add('tube_identification_text',mesh,[255,255,255],role='original_identification_text')
    mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,alphaMode='BLEND',roughnessFactor=.65))


def material_mesh(shape):
    # The nominal mass is checked on the exported mesh, so use a finer
    # tessellation than the cosmetic shell's 0.03 mm / 0.12 rad defaults.
    vertices,faces=shape.tessellate(.003,.025)
    mesh=trimesh.Trimesh(vertices=np.array([[p.x,p.y,p.z] for p in vertices])*.001,faces=faces)
    mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
    mesh.fix_normals();assert mesh.is_volume
    return mesh


def build():
    source=json.loads((HERE/'silicone_grease_sources.json').read_text())
    body,cap,liner,cavity=container();items=[]
    # A 0.25 mm radial display margin left a 0.041 mm3 intersection after
    # independently tessellating the high-fill surface near z=111–115 mm.
    # The 0.5 mm visualization margin keeps both source-density scenarios
    # inside the actual exported shell; it is not a fluid meniscus model.
    fill=loft([(7.02,7.5,7.5)]+[(z,rx-.5,max(.05,ry-.5)) for z,rx,ry in INSIDE[1:]])
    for scenario in source['manufacturer_facts']['density_reports']:
        density=scenario['relative_density'];target=85/density*1000
        assert fill.Volume()>target,'Tube too small for an evidenced density scenario'
        lo,hi=7.02,135.8
        for _ in range(34):
            level=(lo+hi)/2
            cut=fill.intersect(cq.Solid.makeBox(100,100,level,cq.Vector(-50,-50,0)))
            if cut.Volume()<target:lo=level
            else:hi=level
        stock=fill.intersect(cq.Solid.makeBox(100,100,(lo+hi)/2,cq.Vector(-50,-50,0)))
        g=Geometry()
        solid(g,'tube_shell_and_sealed_tail',body,[207,210,207],metal=.25,role='inferred_flexible_container_rigid_reference')
        solid(g,'ribbed_hollow_cap',cap,[223,225,218],role='removable_cap_with_thread_clearance_envelope')
        solid(g,'inferred_cap_sealing_annulus',liner,[232,231,222],role='unqualified_sealing_reference')
        g.add('nominal_85g_silicone_stock',material_mesh(stock),[228,227,214],role='same_85g_stock_alternative_density_hypothesis')
        label(g)
        geometry=export_review(g,'superlube_93003_silicone_grease_'+scenario['id'])
        items.append(dict(**scenario,geometry=geometry,approximate_density_g_ml=density,
            nominal_volume_m3=target*1e-9,actual_cad_volume_m3=stock.Volume()*1e-9,
            selected_fill_height_m=(lo+hi)*.0005,physical_identity='weather_silicone_grease_93003'))
    refs=[Path(__file__),HERE/'silicone_grease_sources.json',HERE/'build_mast_grease.py',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_silicone_grease_candidate',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        geometry=items[0]['geometry'],items=items,default_item='tds_1_11',
        net_mass_g=85,inferred_cavity_volume_m3=cavity.Volume()*1e-9,
        visualization_stock_wall_clearance_m=.0005,
        groups=dict(container=['tube_shell_and_sealed_tail','tube_identification_text'],
            cap=['ribbed_hollow_cap','inferred_cap_sealing_annulus'],stock=['nominal_85g_silicone_stock']),
        inspection=dict(cap_translation_m=[0,0,-.045],scope='Separated cap inspection only; not an unscrewing path.'),
        application_budget=dict(status='inferred_inventory_planning_allowance_not_approved_dose',
            per_channel_g=.5,per_cable_path_g=.5,reserved_cable_paths=['temperature','wind','ground','future_external_power'],
            application_and_wipe_loss_g=.5,per_fresh_assembly_g=3.,
            three_campaign_reservation_g=9.,nominal_remaining_after_reservation_g=76.,
            dose_qualified=False,validation_trial_and_reset_budget_complete=False,
            basis='Manufacturer specifies a light coating. Pea-size description is not a calibrated dose. Four paths reserve future external power as well as three presently represented cables; its connection remains open.'),
        material_allocation=dict(physical_identity='weather_silicone_grease_93003',selected_containers=1,
            selected_for_channel=True,silicone_channel_requirement_satisfied=False,
            selected_destination='U30 EPDM cable channel',excluded_destination_parts=['u30__door_perimeter_gasket'],
            additional_exclusions=['optical_surfaces','mixing_with_mast_grease'],
            manufacturer_epdm_compatibility_rating='E',manufacturer_silicone_rubber_compatibility_rating='NC',
            actual_cable_jacket_compatibility_qualified=False,whole_assembly_compatibility_qualified=False,
            applicator_identity=None,cleanup_stock_identity=None,material_disposition='Contained stock only; no application, residue or waste transfer.'),
        staged_in_lab=False,initial_stock_credit=False,dispensing_qualified=False,sealing_qualified=False,
        compatibility_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'silicone_grease_assets.json',record)
    print(json.dumps(dict(parts=items[0]['geometry']['parts'],cavity_ml=cavity.Volume()/1000,
        scenarios=[dict(id=i['id'],stock_ml=i['nominal_volume_m3']*1e6) for i in items])))


if __name__=='__main__':build()
