"""Source-constrained BT5M asset and finite-length inspection states.

The blade has one continuous mesh from its inner tail to the hook. Independently
constructed rest shapes do not simulate winding, brake friction or spring force.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.optimize import brentq
from PIL import Image,ImageDraw,ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,cad_mesh,export_review

RED=[190,25,35];BLACK=[27,29,30];STEEL=[177,182,180];YELLOW=[220,214,77]
TOTAL=5.30;THICK=.00012;WIDTH=.019;PITCH=.00020;CORE=.010
CENTER=np.array([-.050,0,.040]);EXIT_Z=.014


def outline(y=15):
    return (cq.Workplane('XZ',origin=(0,y,0)).moveTo(-87,8)
        .threePointArc((-84.656854,2.343146),(-79,0)).lineTo(-5,0).threePointArc((-1.464466,1.464466),(0,5))
        .lineTo(0,24).threePointArc((-1.757359,28.242641),(-6,30)).lineTo(-9,55)
        .threePointArc((-17,67),(-30,72)).threePointArc((-53,73),(-72,65))
        .threePointArc((-83,51),(-86,31)).lineTo(-87,8).close())


def housing():
    g=Geometry();outside=outline().extrude(30).edges('not |Y').fillet(1.4).val()
    cavity=outline(13).wires().toPending().offset2D(-2).extrude(26).val()
    body=outside.cut(cavity)
    # Real entry opening accommodates the curved strip and retracted hook tail.
    throat=cq.Solid.makeBox(34,21,5,cq.Vector(-30,-10.5,11.7));body=body.cut(throat)
    # An analytic arc preserves the inferred 78 mm crown and gives closed
    # fillet surfaces on export; the previous interpolated spline left holes.
    radius=(35**2+20**2)/40
    left_z=78-radius+np.sqrt(radius**2-23**2)
    button=(cq.Workplane('XZ',origin=(0,12,0)).moveTo(-67,left_z)
        .threePointArc((-44,78),(-9,58)).lineTo(-9,53.5)
        .threePointArc((-44,73.5),(-67,left_z-4.5))
        .close().extrude(24).edges('not |Y').fillet(.8).val())
    # Pivot lug is connected to the same switch, with an actual axle bore.
    button=button.fuse(cq.Solid.makeCylinder(5,24,cq.Vector(-44,-12,69),cq.Vector(0,1,0)))
    # The pivot ends remain inside blind case seats; the reference front
    # photograph has no exposed metal pin through the red outer surface.
    pivot=cq.Solid.makeCylinder(1.25,27.6,cq.Vector(-44,-13.8,69),cq.Vector(0,1,0))
    button=button.cut(pivot);body=body.cut(pivot)
    # Conservative convex pocket encloses the sampled switch shapes plus
    # 0.3 mm axial margins. It is an inferred internal clearance, not a
    # reconstruction of the transmission, stops or a continuous motion test.
    pocket=[]
    for degrees in [0,2.3,4.6]:
        b=button.rotate((-44,0,69),(-44,1,69),degrees)
        bm=cad_mesh(b)
        for x,y,z in [(0,0,0),(.3,0,0),(-.3,0,0),(0,.3,0),(0,-.3,0),(0,0,.3),(0,0,-.3)]:
            pocket.append(bm.vertices+np.array([x,y,z])*.001)
    pocket=trimesh.convex.convex_hull(np.vstack(pocket))
    # Split casing and retain ordinary rear screw access. All local fastener
    # dimensions are inferred from photographs.
    screw_sites=[(-73,57),(-78,9),(-10,25)]
    for x,z in screw_sites:
        body=body.cut(cq.Solid.makeCylinder(1.7,29,cq.Vector(x,-13,z),cq.Vector(0,1,0)))
        body=body.cut(cq.Solid.makeCylinder(3,1.8,cq.Vector(x,14,z),cq.Vector(0,1,0)))
    for x in [-14,-10.5,-7]:
        groove=cq.Solid.makeCylinder(.8,8,cq.Vector(x,-15.45,2))
        groove=groove.fuse(cq.Solid.makeSphere(.8,cq.Vector(x,-15.45,10)))
        body=body.cut(groove)
    black_mask=(cq.Workplane('XZ',origin=(0,16,0)).polyline([(-90,-2),(2,-2),(2,26),(-12,31),(-32,66),(-62,70),(-90,53)]).close().extrude(32).edges('|Y').fillet(2).val())
    red_triangle=(cq.Workplane('XZ',origin=(0,16,0)).polyline([(-83,5),(-83,39),(-38,5)]).close().extrude(32).edges('|Y').fillet(1.2).val())
    black_mask=black_mask.cut(red_triangle)
    for side,y0 in [('front',-15),('rear',.04)]:
        half=body.intersect(cq.Solid.makeBox(100,14.96,90,cq.Vector(-90,y0,-1)))
        skin=cq.Solid.makeBox(100,1,90,cq.Vector(-90,-15 if side=='front' else 14,-1))
        bumper=black_mask.intersect(skin)
        # Shared exported surfaces are cut once to avoid overlapping chord
        # approximations where independently tessellated materials meet.
        half_mesh=trimesh.boolean.difference([cad_mesh(half),pocket],engine='manifold')
        mask=cad_mesh(bumper)
        rubber=trimesh.boolean.intersection([mask,half_mesh],engine='manifold')
        plastic=trimesh.boolean.difference([half_mesh,mask],engine='manifold')
        g.add(side+'_abs_shell',plastic,RED,role='inferred_hollow_ABS_case_half')
        g.add(side+'_rubber_impact_domain',rubber,BLACK,role='photo_constrained_rubber_protection')
        rubber.visual.material.roughnessFactor=.8
    solid(g,'thumb_brake',button,BLACK,role='source_visible_pivoting_thumb_switch')
    solid(g,'thumb_brake_axle',cq.Solid.makeCylinder(1.2,27,cq.Vector(-44,-13.5,69),cq.Vector(0,1,0)),STEEL,metal=.7)
    for i,(x,z) in enumerate(screw_sites):
        shaft=cq.Solid.makeCylinder(1.5,27.2,cq.Vector(x,-13,z),cq.Vector(0,1,0))
        head=cq.Solid.makeCylinder(2.8,.8,cq.Vector(x,14.2,z),cq.Vector(0,1,0))
        cross=cq.Solid.makeBox(3,.5,.65,cq.Vector(x-1.5,14.6,z-.325)).fuse(cq.Solid.makeBox(.65,.5,3,cq.Vector(x-.325,14.6,z-1.5)))
        solid(g,'case_screw_'+str(i+1),shaft.fuse(head.cut(cross)),STEEL,metal=.85,role='inferred_housing_screw')
    # Quick-release mushroom and retaining channel follow the cited patent
    # topology; dimensions and elastic latch are unmeasured.
    button_mount=cq.Solid.makeCylinder(5.5,2.2,cq.Vector(-46,15,46),cq.Vector(0,1,0)).fuse(cq.Solid.makeCylinder(14,2,cq.Vector(-46,17.2,46),cq.Vector(0,1,0)))
    solid(g,'belt_clip_mushroom_mount',button_mount,BLACK)
    receiver=cq.Solid.makeCylinder(16.5,6,cq.Vector(-46,16.5,46),cq.Vector(0,1,0))
    receiver=receiver.cut(cq.Solid.makeCylinder(14.35,3.2,cq.Vector(-46,17.1,46),cq.Vector(0,1,0)))
    receiver=receiver.cut(cq.Solid.makeCylinder(5.9,4,cq.Vector(-46,15,46),cq.Vector(0,1,0)))
    receiver=receiver.cut(cq.Solid.makeBox(12,8,30,cq.Vector(-52,15,46)))
    frame=(cq.Workplane('XZ',origin=(0,28,0)).moveTo(-71,72).lineTo(-69,28)
        .threePointArc((-62,16),(-46,13)).threePointArc((-30,16),(-23,28))
        .lineTo(-21,72).lineTo(-27,72).lineTo(-31,43)
        .threePointArc((-46,40),(-61,43)).lineTo(-65,72).close()
        .extrude(3).edges('|Y').fillet(1.2).val())
    # Broad lower paddle, actual slot and curved top returns reproduce the
    # visible clip topology. Local dimensions are inferred, with no elastic
    # retention or belt release claim.
    window=(cq.Workplane('XZ',origin=(-46,29,31)).rect(18,7)
        .extrude(5).edges('|Y').fillet(1.2).val())
    frame=frame.cut(window)
    for x in [-71,-27]:
        returned=(cq.Workplane('YZ',origin=(x,0,0)).moveTo(28,72)
            .threePointArc((21.5,78.5),(15,72)).lineTo(15,61).lineTo(18,61)
            .lineTo(18,72).threePointArc((21.5,75.5),(25,72)).close().extrude(6).val())
        frame=frame.fuse(returned)
    # Central spring tongue is visibly connected at its lower root; a real
    # hole and recessed grip grooves replace an opaque rectangular plate.
    wires=[cq.Workplane('XY',origin=(-46,y,z)).rect(width,2.5).val() for z,y,width in [(39,25.5,16),(80,25.5,16),(86,26.5,16),(91,28,16),(94,29,14)]]
    tongue=cq.Solid.makeLoft(wires,ruled=True)
    tongue=tongue.cut(cq.Solid.makeCylinder(2.5,6,cq.Vector(-46,23,45),cq.Vector(0,1,0)))
    for z,y in [(84,27.0),(87,28.1),(90,28.7)]:tongue=tongue.cut(cq.Solid.makeBox(12,1.0,.8,cq.Vector(-52,y,z)))
    clip=receiver.fuse(frame).fuse(tongue).fuse(cq.Solid.makeBox(24,6,6,cq.Vector(-58,20,35)))
    solid(g,'belt_clip_and_release_tongue',clip,BLACK,role='inferred_retaining_channel_and_clip_no_elasticity')
    # Source-visible casing identification, independently typeset. This is
    # ordinary product labeling, not an added robot marker.
    nameplate=Image.new('RGBA',(768,768),(0,0,0,0));draw=ImageDraw.Draw(nameplate)
    draw.ellipse((5,5,763,763),fill=(22,24,25,255),outline=(60,63,63,255),width=5)
    for y,text,size in [(200,'Hultafors',84),(350,'5 m',155),(560,'BT5M',64)]:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size);draw.text((384,y),text,font=font,fill=(235,235,230,255),anchor='mm')
    m=trimesh.Trimesh(vertices=[[-.063,-.01503,.021],[-.023,-.01503,.021],[-.023,-.01503,.061],[-.063,-.01503,.061]],faces=[[0,1,2],[0,2,3]],process=False)
    g.add('case_identification_text',m,[255,255,255],role='original_identification_text')
    m.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],material=PBRMaterial(baseColorTexture=nameplate,alphaMode='BLEND',roughnessFactor=.7))
    return g


def centreline(exposed):
    k=PITCH/(2*np.pi)
    def make(turn_angle):
        angles=np.linspace(-np.pi/2-turn_angle,-np.pi/2,max(3,int(np.ceil(turn_angle/.10))+1))
        radius=CORE+k*(angles-angles[0])
        coil=CENTER+np.column_stack([radius*np.cos(angles),np.zeros(len(angles)),radius*np.sin(angles)])
        # Tangent-preserving cubic lead to a straight internal guide. End
        # shape varies with reel radius; solve its length together with coil.
        p0=coil[-1];p1=p0+[.009,0,0];p3=np.array([-.030,0,EXIT_Z]);p2=p3- [.008,0,0]
        t=np.linspace(0,1,81)[1:,None]
        lead=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t**2*p2+t**3*p3
        line=np.array([[-.027,0,EXIT_Z],[0,0,EXIT_Z],[exposed,0,EXIT_Z]])
        points=np.vstack([coil,lead,line]);return points,len(coil)
    def residual(a):return np.linalg.norm(np.diff(make(a)[0],axis=0),axis=1).sum()-TOTAL
    angle=brentq(residual,0,700,xtol=1e-11);points,n=make(angle)
    return points,dict(winding_angle_rad=angle,inner_radius_m=CORE,outer_radius_m=CORE+k*angle,
        coiled_segment_count=n-1,neutral_line_length_m=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),
        neutral_line_points_m=points.tolist())


def strip(points):
    # An arc-length transverse coordinate preserves the nominal 19 mm steel
    # strip width while the visible blade has an inferred shallow curvature.
    tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.column_stack([-tangent[:,2],np.zeros(len(points)),tangent[:,0]])
    u=np.linspace(-WIDTH/2,WIDTH/2,9);vertices=[]
    for p,n in zip(points,normal):
        curvature=np.clip((p[0]+.030)/.003,0,1)/.040
        if curvature>1e-9:y=np.sin(u*curvature)/curvature;h=(1-np.cos(u*curvature))/curvature
        else:y=u;h=np.zeros_like(u)
        cross=np.vstack([p+np.column_stack([np.zeros(9),y,np.zeros(9)])+(h+THICK/2)[:,None]*n,
                         p+np.column_stack([np.zeros(9),y[::-1],np.zeros(9)])+(h[::-1]-THICK/2)[:,None]*n])
        vertices.extend(cross)
    faces=[];count=18
    for i in range(len(points)-1):
        for j in range(count):
            a=i*count+j;b=i*count+(j+1)%count;c=b+count;d=a+count
            faces.extend([[a,b,c],[a,c,d]])
    for i in range(1,count-1):faces.extend([[0,i+1,i],[(len(points)-1)*count,(len(points)-1)*count+i,(len(points)-1)*count+i+1]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False);mesh.fix_normals();return mesh


def scale_text(g,exposed):
    # Separate <= 0.5 m textures preserve legible millimetre marks at long
    # extensions without a texture exceeding common WebGL size limits.
    fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    for tile,start in enumerate(np.arange(0,exposed,.5)):
        end=min(start+.5,exposed);span=end-start;pixels=max(64,int(np.ceil(span*8000)))
        picture=Image.new('RGBA',(pixels,152),(0,0,0,0));draw=ImageDraw.Draw(picture)
        for mm in range(int(np.ceil(start*1000)),int(np.floor(end*1000))+1):
            x=(end-mm*.001)/span*(pixels-1);major=mm%10==0;middle=mm%5==0;length=44 if major else 29 if middle else 19
            draw.line([(x,0),(x,length)],fill=(22,26,24,255),width=1)
            draw.line([(x,151),(x,151-length)],fill=(22,26,24,255),width=1)
            if major and mm:
                font=ImageFont.truetype(fontfile,38);draw.text((x,76),str(mm//10),font=font,fill=(140,22,23,255) if mm%100==0 else (22,26,24,255),anchor='mm')
        vertices=[];uv=[];faces=[]
        # Metric distance increases from the hook backwards toward the case.
        for j,s in enumerate([start,end]):
            x=exposed-s
            for i,u in enumerate(np.linspace(-WIDTH/2,WIDTH/2,9)):
                y=.040*np.sin(u/.040);z=EXIT_Z+.040*(1-np.cos(u/.040))+THICK/2+.000004
                vertices.append([x,y,z]);uv.append([1-j,i/8])
                if j==0 and i<8:faces.extend([[i,i+10,i+9],[i,i+1,i+10]])
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
        g.add('blade_graduations_'+str(tile)+'_text',mesh,[255,255,255],role='ordinary_original_metric_graduations')
        mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,alphaMode='BLEND',roughnessFactor=.7))


def blade_and_hook(g,exposed):
    points,record=centreline(exposed);blade=strip(points)
    # Actual round holes retain three rivets in the steel strip. Sliding
    # slots belong to the hook, so the entire measuring tape need not stretch.
    xs=[exposed-v for v in [.006,.014,.022]];cutters=[]
    for x in xs:
        c=trimesh.creation.cylinder(.00108,.006,sections=24);c.apply_translation([x,0,EXIT_Z]);cutters.append(c)
    blade=trimesh.boolean.difference([blade,*cutters],engine='manifold')
    g.add('continuous_steel_blade',blade,YELLOW,metal=.3,role='single_replaceable_blade_coil_lead_and_exposed_length')
    # Photo-constrained hook tail follows the same transverse curvature and
    # stays below the steel blade, rather than cutting through a flat plate.
    hook_points=np.array([[exposed-.029,0,EXIT_Z-.00040],[exposed+.0007,0,EXIT_Z-.00040]])
    hook=strip(hook_points)
    # The local helper uses the blade thickness; a scaled normal thickening
    # is explicit and does not change any external measurement datum.
    v=hook.vertices.copy();mid=EXIT_Z-.00040+.040*(1-np.cos(np.arcsin(np.clip(v[:,1]/.040,-1,1))))
    v[:,2]=mid+(v[:,2]-mid)*4;hook.vertices=v
    slot_mesh=[]
    for x in xs:
        slot=cq.Workplane('XY',origin=(x*1000,0,10)).slot2D(3.2,2.3).extrude(8).val();slot_mesh.append(cad_mesh(slot))
    hook=trimesh.boolean.difference([hook,*slot_mesh],engine='manifold')
    face=cq.Solid.makeBox(.7,18.5,13.2,cq.Vector(exposed*1000,-9.25,.2))
    hook=trimesh.boolean.union([hook,cad_mesh(face)],engine='manifold')
    g.add('sliding_steel_end_hook',hook,STEEL,metal=.8,role='inferred_slotted_three_rivet_hook')
    rubber=cq.Workplane('YZ',origin=(exposed*1000+.7,0,5.85)).rect(19.2,11.5).extrude(1.4).edges('|X').fillet(1.5).val()
    inset=cq.Workplane('YZ',origin=(exposed*1000+1.7,0,6)).rect(15,8).extrude(.4).edges('|X').fillet(.8).val()
    solid(g,'end_hook_rubber_face',rubber.cut(inset),RED,role='source_visible_end_hook_rubber')
    solid(g,'end_hook_black_impact_pad',inset,BLACK,role='source_visible_end_hook_rubber')
    for i,x in enumerate(xs):
        pin=cq.Solid.makeCylinder(1,1.0,cq.Vector(x*1000,0,13.2))
        lower=cq.Solid.makeCylinder(1.8,.25,cq.Vector(x*1000,0,12.95))
        upper=cq.Solid.makeSphere(3,cq.Vector(x*1000,0,11.8)).intersect(cq.Solid.makeBox(8,8,.6,cq.Vector(x*1000-4,-4,14.2)))
        solid(g,'end_hook_rivet_'+str(i+1),pin.fuse(lower).fuse(upper),STEEL,metal=.85,role='inferred_rivet_fixed_to_blade')
    scale_text(g,exposed)
    return record


def build():
    source=json.loads((HERE/'tape_measure_sources.json').read_text());items=[]
    base=housing()
    for identity,extension,label in [('retracted',.003,'收回参考'),('quarter_metre',.25,'250 mm 伸出参考'),('catalogue_capacity',5.,'5 m 量程参考')]:
        g=Geometry();g.scene=base.scene.copy();g.parts=list(base.parts)
        blade=blade_and_hook(g,extension)
        geometry=export_review(g,'hultafors_bt5m_'+identity)
        items.append(dict(id=identity,label=label,exposed_neutral_length_m=extension,geometry=geometry,blade=blade))
    refs=[Path(__file__),HERE/'tape_measure_sources.json',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='source_constrained_tape_measure_candidate',items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        manufacturer_facts=source['manufacturer_facts'],inferred_parameters=source['inferred_parameters'],
        blade_identity='one_replaceable_5m_metric_blade_with_inferred_hidden_tail',
        physical_identity='weather_tape_measure_bt5m',selected_required_units=1,
        limits=['Three independent inspection shapes, not a retracting mechanism or a measured force model.',
            'Case outlines, impact domains, clip, pivot, fasteners and hook details are original hypotheses constrained by manufacturer photos.',
            'Internal return spring and brake transmission are not qualified; the clip has no elastic release simulation.',
            'Internal-measurement datum and reverse CC scale remain unresolved; only external metric measurement is represented.',
            'Hook lost motion, calibration, load, blade sag, hand grasp and robot operation remain unqualified.'],
        initial_stock_credit=False,measurement_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'tape_measure_assets.json',record)
    print(json.dumps(dict(states=len(items),parts=[i['geometry']['parts'] for i in items],lengths=[i['blade']['neutral_line_length_m'] for i in items])))


if __name__=='__main__':build()
