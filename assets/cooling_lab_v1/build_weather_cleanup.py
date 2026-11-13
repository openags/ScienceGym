"""Ordinary separate grease applicators and individually accounted wipe stock."""
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import export_review


def ring_solid(sections, axis=0, count=96):
    """Closed superellipse sections in metres; no independent welded rings."""
    a=np.arange(count)*2*np.pi/count
    vertices=[]
    for x,ry,rz,power in sections:
        y=ry*np.sign(np.cos(a))*np.abs(np.cos(a))**(2/power)
        z=rz*np.sign(np.sin(a))*np.abs(np.sin(a))**(2/power)
        vertices.extend(np.array([np.full(count,x),y,z]).T)
    faces=[]
    for i in range(len(sections)-1):
        for j in range(count):
            n=i*count+j;k=i*count+(j+1)%count
            faces.extend([[n,k,k+count],[n,k+count,n+count]])
    for j in range(1,count-1):
        faces.extend([[0,j+1,j],[(len(sections)-1)*count,(len(sections)-1)*count+j,(len(sections)-1)*count+j+1]])
    m=trimesh.Trimesh(vertices=vertices,faces=faces);m.fix_normals()
    if axis==1:m.vertices=m.vertices[:,[1,0,2]];m.invert()
    assert m.is_volume
    return m


def spatula():
    # Both 45 mm blade lengths include the inferred neck transition.
    width=PchipInterpolator([30,32,35,39,70.5],[1.75,2,3.5,4.5,4.5])
    thickness=PchipInterpolator([30,32,35,39,70.5],[1.75,1.3,.6,.35,.35])
    sections=[]
    xs=np.unique(np.r_[np.linspace(-75,-30,181),[-30,30],np.linspace(30,70.5,163),np.linspace(70.5,75,91)])
    for x in xs:
        q=abs(x)
        if q<=30:ry=rz=1.75;power=2
        else:
            ry=float(width(min(q,70.5)));rz=float(thickness(min(q,70.5)))
            power=2+6*min(1,(q-30)/9)
            if x<-74.7:ry=4.2+np.sqrt(max(0,.3**2-(q-74.7)**2))
            if x>70.5:ry=max(.001,np.sqrt(max(0,4.5**2-(x-70.5)**2)))
        sections.append([x*.001,ry*.001,rz*.001,power])
    mesh=ring_solid(sections);mesh.apply_translation([0,0,.00175])
    g=Geometry();m=g.add('continuous_stainless_spatula',mesh,[182,188,192],metal=1,role='ordinary_reusable_spatula')
    m.visual.material.roughnessFactor=.25
    return export_review(g,'buerkle_5386_0041_spatula')


def pouch(width,half_length,half_depth,wall):
    # Closed hollow films. Each has outer and cavity surfaces; those are
    # boundaries of one material volume, not two inventory objects.
    y=np.array([-half_length,-half_length+.006,-.120,-.114,0,.114,.120,half_length-.006,half_length])
    ry=np.array([width/2-.002,width/2-.001,width/2,width/2,width/2-.002,width/2,width/2,width/2-.001,width/2-.002])
    rz=np.array([.0003,.003,half_depth-.001,half_depth,half_depth,half_depth,half_depth-.001,.003,.0003])
    outer=ring_solid(list(zip(y,ry,rz,np.full(len(y),16))),axis=1)
    inside=ring_solid(list(zip(y[1:-1],ry[1:-1]-wall,rz[1:-1]-wall,np.full(len(y)-2,16))),axis=1)
    inside.invert();mesh=trimesh.util.concatenate([outer,inside]);mesh.apply_translation([0,0,.058])
    assert mesh.is_volume
    return mesh


def wipe_material(mesh):
    # Deterministic fine nonwoven variation, not copied product artwork.
    rng=np.random.default_rng(609);noise=np.clip(rng.normal(239,4,(256,256)),224,250).astype(np.uint8)
    picture=Image.fromarray(np.repeat(noise[:,:,None],3,axis=2),'RGB')
    uv=(mesh.vertices[:,:2]+.1143)/.2286
    mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,roughnessFactor=1,metallicFactor=0))


def wipe_pack():
    g=Geometry();thickness=.00035
    for i in range(300):
        m=g.box('wipe_'+str(i+1).zfill(3),[.2286,.2286,thickness],[0,0,.0055+(i+.5)*thickness],
                [239,239,233],role='individually_identified_wipe')
        wipe_material(m)
    # Keep the inner heat-sealed margin inside the outer bag's cavity.
    # A 292 mm inner length intersected the outer sealed end by 1.43 mL.
    for name,args in [('inner_bag',(.244,.138,.056,.00008)),('outer_bag',(.252,.150,.058,.00008))]:
        m=g.add(name,pouch(*args),[227,234,236],alpha=50,role='inferred_flexible_packaging_film')
        m.visual.material.roughnessFactor=.3
    # Original multiline identification, fitted into its texture without
    # clipping the SKU/count. No copied manufacturer label or logo.
    picture=Image.new('RGB',(1024,512),(234,237,239));draw=ImageDraw.Draw(picture)
    for y,text,size in [(100,'TX609',136),(248,'300 DRY WIPES',84),(365,'9 x 9 in | 45% polyester',54),(438,'55% cellulose | non-sterile',54)]:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        bounds=draw.textbbox((512,y),text,font=font,anchor='mm')
        assert bounds[0]>=20 and bounds[2]<=1004 and bounds[1]>=10 and bounds[3]<=502
        draw.text((512,y),text,font=font,fill=(29,49,93),anchor='mm')
    m=trimesh.Trimesh(vertices=[[-.095,-.0475,.11608],[.095,-.0475,.11608],[.095,.0475,.11608],[-.095,.0475,.11608]],faces=[[0,1,2],[0,2,3]],process=False)
    g.add('pack_identification_text',m,[255,255,255],role='original_identification_text')
    m.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],material=PBRMaterial(baseColorTexture=picture,roughnessFactor=.7))
    pack=export_review(g,'texwipe_tx609_300_wipes')
    one=Geometry();m=one.box('wipe_001',[.2286,.2286,thickness],[0,0,thickness/2],[239,239,233],role='same_wipe_001_isolated_reference')
    wipe_material(m)
    return pack,export_review(one,'texwipe_tx609_one_wipe_reference')


def build():
    source=json.loads((HERE/'weather_cleanup_sources.json').read_text())
    sg=spatula();pack,one=wipe_pack()
    facts=source['manufacturer_facts'];policy=source['allocation_policy']
    mass_g=float(np.prod(facts['wipes']['selected_size_m'])*facts['wipes']['basis_weight_g_m2'])
    reservations=[];n=1
    for assembly in range(1,4):
        for role,count in policy['wipe_plan_per_fresh_assembly'].items():
            ids=['weather_wipes_tx609/wipe_'+str(i).zfill(3) for i in range(n,n+count)]
            reservations.append(dict(assembly=assembly,role=role,unit_ids=ids,quantity=count));n+=count
    used=n-1;volume_l=used*.2286**2*.00035*1000*policy['waste_loose_volume_factor']
    item=dict(id='weather_wipes_tx609',label='Texwipe TX609 · 300 张干擦拭材料',geometry=pack,
        unit_ids=['weather_wipes_tx609/wipe_'+str(i).zfill(3) for i in range(1,301)],
        packaging_parts=['inner_bag','outer_bag'],selected_packs=1,wipes_per_pack=300,
        expected_dry_mass_per_wipe_g=mass_g,expected_total_dry_wipe_mass_g=300*mass_g,
        isolated_reference=dict(geometry=one,physical_identity='weather_wipes_tx609/wipe_001',adds_stock=False),
        application_budget=dict(status='inferred_stock_plan_not_executed_consumption',per_fresh_assembly=12,
            fresh_assemblies=3,reserved_wipes=used,remaining_wipes=300-used,allocations=reservations,
            trial_reset_budget_complete=False),
        destination_scope='Dry lubricant cleanup on service components; not qualified for optical coatings, finished emitters or precision optical surfaces.')
    app=[dict(id='weather_'+family+'_applicator',label='Bürkle 5386-0041 · '+label,geometry=sg,
              assigned_grease_identity=grease,selected_required_units=1,shared_between_grease_families=False,
              rest=dict(to_support_plane=np.eye(4).tolist(),contact_basis='round_handle_tangent_line',
                        dynamic_stability_qualified=False,anti_roll_feature=False))
         for family,label,grease in [('mast','桅杆润滑脂专用','weather_mast_grease_21030'),('silicone','硅脂专用','weather_silicone_grease_93003')]]
    paths=[Path(__file__),HERE/'weather_cleanup_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py',
           HERE/'mast_grease_assets.json',HERE/'silicone_grease_assets.json',HERE/'supply_sources.json']
    record=dict(schema_version=1,status='ordinary_cleanup_candidates_pending_review',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        applicators=app,wipe_pack=item,
        waste_reservation=dict(candidate_identity='oily_waste_can',reserved_volume_l=3,
            upper_bound_grease_mass_g=15,nominal_dry_wipe_mass_g=used*mass_g,
            estimated_loose_wipe_volume_l=volume_l,loose_volume_factor=4,
            material_scope='Only the two grease families on the 36 reserved wipes; free liquids, packaging and coating/solvent waste excluded.',
            nominal_catalogue_capacity_l=23,available_capacity_qualified=False,material_compatibility_qualified=False,
            actual_transfer_complete=False),
        limitations=['Blade thickness, transition and edge radii remain inferred; metal-on-elastomer scratching and tool grip need validation.',
                    'Round handle is a neutral-roll rest reference, not an anti-roll fixture; no dynamic stability credit.',
                    'Compressed stack and pouch dimensions are inferred. Bags and all 300 wipes remain separate named parts; no cloth or opening dynamics.',
                    'TDS sorption figures are not converted into grease capacity. Wipe counts and loose waste volume are planning inferences.',
                    'Packaging collection, full trials/resets and actual waste handling remain open.'],
        owner_acceptance=None,initial_stock_credit=False,robot_use_qualified=False)
    write_json(HERE/'weather_cleanup_assets.json',record)
    print(json.dumps(dict(applicators=2,wipes=300,pack_parts=pack['parts'],reserved_wipes=used,dry_mass_g=300*mass_g)))


if __name__=='__main__':build()
