"""Original, source-constrained tube candidate; no dispensing or robot action."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import solid, cad_mesh, export_review

GREY=[207,210,207]; CAP=[223,225,218]
# (height, half-width, half-depth), millimetres. Local geometry is inferred.
SECTIONS=[(7,10.2,10.2),(20,10.2,10.2),(30,17,16),
          (70,20.5,16),(110,24,14),(136,26,8),(151,27,.7),(153,27,.65)]


def loft(rows):
    wires=[cq.Workplane('XY',origin=(0,0,z)).ellipse(rx,ry).val() for z,rx,ry in rows]
    # Ruled intervals keep the selected envelope exact and avoid overshooting
    # a nearly flattened heat-sealed tail. The dense rendered rings smooth
    # only shading; they do not change dimensions.
    return cq.Solid.makeLoft(wires,ruled=True)


def build():
    source=json.loads((HERE/'mast_grease_sources.json').read_text());g=Geometry()
    outer=loft(SECTIONS)
    inside=[(6.9,8,8),(20,8,8),(30,16.6,15.6),(70,20.1,15.6),
            (110,23.6,13.6),(136,25.6,7.6),(150,26.5,.3)]
    cavity=loft(inside)
    body=outer.cut(cavity)
    # An open nozzle is part of the same connected tube, with a helical
    # external ridge. Its inferred female clearance is not a screw fit model.
    path=cq.Wire.makeHelix(2,6,10.4,center=cq.Vector(0,0,9))
    ridge=cq.Workplane('XZ',origin=(10.4,0,9)).circle(.6).sweep(cq.Workplane(obj=path),isFrenet=True).val()
    body=body.fuse(ridge)
    flange=cq.Solid.makeBox(54,1.3,9,cq.Vector(-27,-.65,153))
    slot=cq.Workplane('XZ',origin=(0,2,157.4)).slot2D(18,3.5).extrude(4).val()
    flange=flange.cut(slot)
    body=body.fuse(flange)
    solid(g,'tube_shell_and_sealed_tail',body,GREY,metal=.25,role='inferred_flexible_container_rigid_reference')
    cap=cq.Workplane('XY').circle(15.3).extrude(18).edges('%Circle').fillet(.7).val()
    cap=cap.cut(cq.Solid.makeCylinder(11.3,17,cq.Vector(0,0,2)))
    # Union grip ribs into one cap so their shared material is not duplicated.
    for a in np.linspace(0,2*np.pi,64,endpoint=False):
        cap=cap.fuse(cq.Solid.makeCylinder(.36,13,cq.Vector(15.3*np.cos(a),15.3*np.sin(a),2.5)))
    solid(g,'ribbed_hollow_cap',cap,CAP,role='removable_cap_with_thread_clearance_envelope')
    # Nominal sealing face is a separate annulus, inside the hollow cap. It
    # touches the nozzle lip at z=7 mm; material and preload are unmeasured.
    liner=cq.Solid.makeCylinder(11.2,5,cq.Vector(0,0,2)).cut(cq.Solid.makeCylinder(8,5.2,cq.Vector(0,0,1.9)))
    solid(g,'inferred_cap_sealing_annulus',liner,[232,231,222],role='unqualified_sealing_reference')
    # Fill volume derives from net mass, not the package's bounding box.
    # Leave finite radial clearance so tessellation cannot put stock through
    # the shell. A flat meniscus is only an inventory visualization.
    fill_rows=[(7.02,7.75,7.75)]+[(z,rx-.25,ry-.25) for z,rx,ry in inside[1:]]
    fill=loft(fill_rows);target=source['manufacturer_facts']['net_mass_g']/.89*1000
    if fill.Volume()<target:raise ValueError('Inferred tube cannot hold labelled net mass')
    lo,hi=7.02,150
    for _ in range(34):
        level=(lo+hi)/2
        cut=fill.intersect(cq.Solid.makeBox(100,100,level,cq.Vector(-50,-50,0)))
        if cut.Volume()<target:lo=level
        else:hi=level
    stock=fill.intersect(cq.Solid.makeBox(100,100,(lo+hi)/2,cq.Vector(-50,-50,0)))
    solid(g,'nominal_85g_grease_stock',stock,[228,226,205],role='nominal_material_stock_no_flow_model')
    # Original typesetting on the curved front surface; no copied logo/photo.
    picture=Image.new('RGBA',(768,1536),(0,0,0,0));draw=ImageDraw.Draw(picture)
    for y,text,size in [(140,'Super Lube',72),(290,'21030',66),(465,'MULTI-PURPOSE',51),
                        (565,'SYNTHETIC GREASE',44),(740,'NLGI 2',60),(970,'85 g',70),
                        (1150,'Silicone-free',40)]:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        draw.text((384,y),text,fill=(32,36,34,255),font=font,anchor='mm')
    vertices=[];uv=[];faces=[];angles=np.linspace(-.8,.8,33);heights=np.linspace(37,140,52)
    data=np.array(SECTIONS)
    for j,z in enumerate(heights):
        rx=np.interp(z,data[:,0],data[:,1])+.025;ry=np.interp(z,data[:,0],data[:,2])+.025
        for i,a in enumerate(angles):
            vertices.append([rx*np.sin(a)*.001,-ry*np.cos(a)*.001,z*.001]);uv.append([i/32,j/51])
            if i<32 and j<51:
                n=j*33+i;faces.extend([[n,n+1,n+34],[n,n+34,n+33]])
    label=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    g.add('tube_identification_text',label,[255,255,255],role='original_identification_text')
    label.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,alphaMode='BLEND',roughnessFactor=.65))
    geometry=export_review(g,'superlube_21030_mast_grease')
    tripod=json.loads((HERE/'tripod_assets.json').read_text())
    if sha(ROOT/tripod['geometry']['path'])!=tripod['geometry']['sha256']:raise ValueError('Tripod geometry version mismatch')
    mast_scene=trimesh.load(ROOT/tripod['geometry']['path'],force='scene')
    matrix,key=mast_scene.graph['lower_mast_with_indexing_creases']
    mast=mast_scene.geometry[key].copy();mast.apply_transform(matrix)
    length=tripod['selected_dimensions']['overlap_m'];top=float(mast.bounds[1,2])
    neck=mast.vertices[mast.vertices[:,2]>top-length+1e-5]
    radius=float(np.max(np.linalg.norm(neck[:,:2],axis=1)))
    area=2*np.pi*radius*length;film_mass=area*.0001*890*1000
    budget=dict(status='inferred_inventory_planning_allowance_not_approved_dose',
        selected_joint_envelope_area_m2=area,joint_radius_from_export_m=radius,joint_overlap_m=length,
        assumed_film_thickness_m=.0001,nominal_retained_film_g=film_mass,
        per_application_reserved_g=2.,application_and_wipe_loss_allowance_g=2.-film_mass,
        assumed_fresh_applications_for_three_campaigns=3,three_campaign_reservation_g=6.,
        nominal_remaining_after_reservation_g=79.,
        basis='Light greasing is specified; film thickness, loss and one fresh application per campaign are planning inferences. Trials and resets need additional consumption budgeting. No material has been dispensed in this state.')
    refs=[Path(__file__),HERE/'mast_grease_sources.json',HERE/'build_supplies.py',HERE/'geometry_tools.py',HERE/'tripod_assets.json']
    record=dict(schema_version=1,status='unaccepted_mast_grease_asset_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions=source['reconstruction'],net_mass_g=85,approximate_density_g_ml=.89,
        nominal_stock_volume_m3=target*1e-9,actual_cad_stock_volume_m3=stock.Volume()*1e-9,
        inferred_cavity_volume_m3=cavity.Volume()*1e-9,selected_fill_height_m=(lo+hi)*.0005,
        visualization_stock_wall_clearance_m=.00025,application_budget=budget,
        groups=dict(container=['tube_shell_and_sealed_tail','tube_identification_text'],
            cap=['ribbed_hollow_cap','inferred_cap_sealing_annulus'],stock=['nominal_85g_grease_stock']),
        inspection=dict(cap_translation_m=[0,0,-.045],scope='Separated cap inspection only; not an unscrewing path.'),
        material_allocation=dict(physical_identity='weather_mast_grease_21030',selected_containers=1,
            purpose='Lower mast creased joint only',silicone_channel_requirement_satisfied=False,
            per_application_mass_g=2.,mass_basis='inferred_planning_reservation',applicator_identity=None,cleanup_stock_identity=None,
            campaign_consumption_accepted=False,material_disposition='Contained nominal stock; application/residue/waste transfers are not yet implemented.'),
        staged_in_lab=False,initial_stock_credit=False,dispensing_qualified=False,
        sealing_qualified=False,compatibility_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'mast_grease_assets.json',record)
    print(json.dumps(dict(parts=geometry['parts'],bounds_m=geometry['bounds_m'],nominal_stock_ml=target/1000,cavity_ml=cavity.Volume()/1000)))


if __name__=='__main__':build()
