"""Original manufacturer-constrained 56-204 candidate; no impact simulation."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.optimize import brentq
from scipy.interpolate import PchipInterpolator
from PIL import Image,ImageDraw,ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import cad_mesh,solid,export_review

HEAD_LENGTH=135.;OVERALL=356.;STEEL_DENSITY=7850.;TARGET_HEAD_MASS=1.8
YELLOW=[237,181,16];FORGED=[45,48,47];MACHINED=[172,178,178]


def octagon(width):
    a=width/2;b=a*(np.sqrt(2)-1)
    return [(a,b),(b,a),(-b,a),(-a,b),(-a,-b),(-b,-a),(b,-a),(a,-b)]


def head_shape(width):
    # Unpublished section and face bevels are a selected hypothesis. The
    # steel section is solved against the catalogue HEAD mass, not tool mass.
    rings=[(-67.5,.90),(-65,.98),(-53,1),(-45,.93),(45,.93),(53,1),(65,.98),(67.5,.90)]
    wires=[cq.Workplane('XZ',origin=(0,y,width/2)).polyline(octagon(width*scale)).close().val() for y,scale in rings]
    outer=cq.Solid.makeLoft(wires,ruled=True)
    outer=cq.Workplane(obj=outer).edges().fillet(.6).val()
    eye=cq.Workplane('YZ',origin=(-60,0,width/2)).ellipse(14,8.5).extrude(120).val()
    return outer.cut(eye)


def handle_outer(stations,z):
    # Shape-preserving interpolation prevents the narrow waist from crossing
    # the fiberglass core between sections, which an unconstrained CAD loft
    # did even though its end sections and overall bounds looked plausible.
    p=np.asarray(stations);xs=np.unique(np.r_[np.linspace(p[0,0],p[-1,0],156),p[:,0]])
    radii=PchipInterpolator(p[:,0],p[:,1:],axis=0)(xs)
    n=96;angles=np.linspace(0,2*np.pi,n,endpoint=False)
    vertices=np.concatenate([np.column_stack([np.full(n,x),a*np.cos(angles),z+b*np.sin(angles)]) for x,(a,b) in zip(xs,radii)])*.001
    faces=[]
    for i in range(len(xs)-1):
        for j in range(n):
            k=(j+1)%n;a=i*n+j;b=i*n+k;c=(i+1)*n+k;d=(i+1)*n+j
            faces.extend([[a,b,c],[a,c,d]])
    for j in range(1,n-1):faces.extend([[0,j+1,j],[(len(xs)-1)*n,(len(xs)-1)*n+j,(len(xs)-1)*n+j+1]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces);mesh.fix_normals();assert mesh.is_volume
    return mesh


def original_label(g,jacket,centre_z):
    picture=Image.new('RGBA',(1536,256),(27,29,28,255));draw=ImageDraw.Draw(picture)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    draw.text((768,78),'STANLEY',font=ImageFont.truetype(font,100),fill=(238,185,35,255),anchor='mm')
    draw.text((768,190),'56-204',font=ImageFont.truetype(font,68),fill=(238,185,35,255),anchor='mm')
    xs=np.linspace(-.135,-.060,76);zs=np.linspace(centre_z-.004,centre_z+.004,17)
    origins=np.array([[x,-.040,z] for x in xs for z in zs]);directions=np.tile([0,1,0],(len(origins),1))
    hits,rays,_=jacket.ray.intersects_location(origins,directions)
    front=np.full(len(origins),np.inf);np.minimum.at(front,rays,hits[:,1]);assert np.isfinite(front).all()
    vertices=origins.copy();vertices[:,1]=front-.000030
    faces=[];uv=[];n=len(zs)
    for j,x in enumerate(xs):
        for i,z in enumerate(zs):
            uv.append([j/(len(xs)-1),i/(n-1)])
            if j<len(xs)-1 and i<n-1:
                a=j*n+i;faces.extend([[a,a+n,a+1],[a+1,a+n,a+n+1]])
    m=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    g.add('original_handle_identification_text',m,[255,255,255],role='ordinary_original_identification_text')
    m.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,roughnessFactor=.7))


def build():
    source=json.loads((HERE/'engineer_hammer_sources.json').read_text())
    width=brentq(lambda d:head_shape(d).Volume()*1e-9*STEEL_DENSITY-TARGET_HEAD_MASS,35,60,xtol=1e-9)
    head=head_shape(width);z=width/2;waist=.93*width/2;butt=-OVERALL+width/2
    g=Geometry()
    middle=cq.Solid.makeBox(140,128,120,cq.Vector(-70,-64,-20))
    solid(g,'forged_steel_head',head.intersect(middle),FORGED,metal=.78,role='one_head_forged_surface_domain')
    g.scene.geometry['forged_steel_head'].visual.material.roughnessFactor=.72
    for name,y0 in [('left',-80),('right',64)]:
        region=cq.Solid.makeBox(140,16,120,cq.Vector(-70,y0,-20))
        solid(g,'machined_striking_face_'+name,head.intersect(region),MACHINED,metal=.9,role='same_head_machined_surface_domain')
        g.scene.geometry['machined_striking_face_'+name].visual.material.roughnessFactor=.35
    # The unexposed fiberglass/adhesive construction is explicitly inferred;
    # no factory retention dimensions or bond strength were retrieved.
    core=cq.Workplane('YZ',origin=(butt+1.5,0,z)).ellipse(11,6.5).extrude(waist-1.2-(butt+1.5)).val()
    solid(g,'fiberglass_core',core,[180,151,93],role='inferred_continuous_fiberglass_core')
    resin=(cq.Workplane('YZ',origin=(-waist+.5,0,z)).ellipse(13.95,8.45)
        .extrude(2*waist-1.2).val())
    core_clear=cq.Workplane('YZ',origin=(-60,0,z)).ellipse(11.05,6.55).extrude(120).val()
    solid(g,'head_eye_bonding_annulus',resin.cut(core_clear),[61,55,43],role='inferred_retention_material_no_strength_claim')
    stations=[(butt,17.5,12),(butt+4,18,12.5),(butt+20,16.5,11.5),
        (butt+110,13,10),(butt+190,11.5,8),(butt+240,12.5,8.5),(-waist-6,16,10),(-waist-.3,14.2,9.2)]
    jacket=trimesh.boolean.difference([handle_outer(stations,z),cad_mesh(core)],engine='manifold')
    mesh=g.add('yellow_handle_jacket',jacket,YELLOW,role='source_visible_jacket_original_local_profile')
    mesh.visual.material.roughnessFactor=.55
    original_label(g,mesh,z*.001)
    geometry=export_review(g,'stanley_56_204_engineer_hammer')
    refs=[Path(__file__),HERE/'engineer_hammer_sources.json',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='source_constrained_engineer_hammer_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        physical_identity='weather_engineer_hammer_56_204',selected_required_units=1,
        manufacturer_constraints=dict(overall_length_m=.356,head_length_m=.135,head_mass_kg=1.8,
            source_scope='Selected cross-edition hypothesis: 2011 overall length and 2022 head length/mass. Shared family photos do not identify an exact production revision.'),
        inferred_geometry=dict(head_section_across_flats_m=width*.001,head_waist_scale=.93,
            forged_edge_radius_m=.0006,
            eye_semiaxes_m=[.014,.0085],core_semiaxes_m=[.011,.0065],bond_visual_clearance_m=.00005,
            handle_loft_sections_m=[[x*.001,a*.001,b*.001] for x,a,b in stations],
            handle_profile_interpolation='Shape-preserving cubic radii; original inferred sections, not manufacturer CAD.',
            densities_kg_m3=dict(steel=7850,fiberglass=1950,jacket=1100,bond=1200),
            section_basis='Head section is inferred from nominal head mass and selected steel density; it is not a measured dimension.'),
        source_conflicts=source['source_differences'],
        limits=['Head surface domains belong to one forged head, not detachable face caps.',
            'Jacket, continuous core, eye and bonding annulus are original local hypotheses; factory fit and retention strength are unqualified.',
            'Source head mass excludes handle and bonding material. Whole-tool mass and inertia are inferred, not manufacturer values.',
            'A four-pound engineer hammer is an ordinary candidate for the tripod manual tool requirement; stake/rod compatibility, impact energy, soil response and humanoid use remain unqualified.'],
        initial_stock_credit=False,impact_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'engineer_hammer_assets.json',record)
    print(json.dumps(dict(parts=geometry['parts'],head_width_m=width*.001,cad_head_mass_kg=head.Volume()*1e-9*STEEL_DENSITY)))


if __name__=='__main__':build()
