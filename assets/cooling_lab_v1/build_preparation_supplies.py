"""Ordinary preparation tools and disconnected meter leads, in SI units.

Catalogue dimensions constrain these reconstructions. Local profiles, resting
poses and unreported dimensions are explicit in supply_sources.json. No source
photographs, logos, ratings or approvals are baked into the exported models.
"""
import numpy as np
import cadquery as cq
import trimesh
from PIL import Image, ImageDraw
from trimesh.visual.material import PBRMaterial
from scipy.optimize import brentq
from geometry_tools import Geometry
from build_supplies import solid, curved_tube, cad_mesh, STEEL


def copy_parts(dest, source, prefix, translation):
    for node in source.scene.graph.nodes_geometry:
        t, key = source.scene.graph[node]
        m = source.scene.geometry[key].copy()
        m.apply_transform(t); m.apply_translation(translation)
        visual = m.visual.copy()
        dest.add(prefix + node, m, STEEL, role='separate_catalog_component')
        m.visual = visual


def holding_arm(length):
    g = Geometry(); L = length * 1000
    # Side profile follows the shallow bow visible in the manufacturer photo.
    # Length is sourced; width, bow, post bore and thickness are inferred.
    profile = [(0, 2), (22, 4), (L*.40, 10), (L-34, 7),
               (L-29, 11), (L, 11), (L, 0), (L-29, 0),
               (L-34, 3), (L*.40, 6), (22, 0), (0, 0)]
    arm = cq.Workplane('XZ').polyline(profile).close().extrude(6, both=True).val()
    head = cq.Workplane('XY').box(29, 20, 11, centered=(False, True, False)).val().translate((L-29, 0, 0))
    arm = arm.fuse(head).cut(cq.Solid.makeCylinder(5.3, 15, cq.Vector(L-18, 0, -2)))
    solid(g, 'bowed_arm_with_post_bore', arm, [49, 53, 59])
    pad = cq.Workplane('XY').box(27, 15, 3, centered=(False, True, False)).edges('|Z').fillet(2).val()
    pad = pad.translate((0, 0, -1.3))
    solid(g, 'red_contact_pad', pad, [220, 65, 42])
    return g


def workholding_kit():
    g = Geometry(); units = []
    for i, L in enumerate([.2032]*3 + [.1524]*2):
        prefix = f'arm_{i+1}_'; copy_parts(g, holding_arm(L), prefix, [0, i*.032, .0013])
        units.append(dict(id=f'arm_{i+1}', kind='long_arm' if i<3 else 'medium_arm', nominal_length_m=L))
    # Four post assemblies lie on the table. Knurl and unengaged threaded
    # envelopes are visible; thread fit and table-channel dimensions are open.
    for i in range(4):
        y=i*.032; x=.230; z=.010
        prefix=f'post_{i+1}_'
        g.cylinder(prefix+'shaft', .005, .110, [x+.055,y,z], STEEL, axis=(1,0,0), metal=.9)
        g.cylinder(prefix+'knurled_grip', .010, .012, [x+.006,y,z], STEEL, axis=(1,0,0), metal=.85)
        for j in range(40):
            a=j*np.pi/20
            # Tessellate in mm before converting to SI: trimesh's absolute
            # revolve tolerance otherwise omits the tiny cylinder end caps.
            rib=trimesh.creation.cylinder(.25,11,sections=24);rib.apply_scale(.001)
            rib.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]))
            rib.apply_translation([x+.006,y+.0098*np.cos(a),z+.0098*np.sin(a)])
            g.add(prefix+f'knurl_{j}',rib,STEEL,metal=.85)
        g.cylinder(prefix+'thread_major_envelope', .003, .010, [x-.005,y,z], STEEL, axis=(1,0,0), metal=.9)
        nut=cq.Workplane('XY').box(24,12,5,centered=(True,True,False)).edges('|Z').fillet(2).val()
        nut=nut.cut(cq.Solid.makeCylinder(3,7,cq.Vector(0,0,-1))).translate((359,y*1000,0))
        solid(g,f'tnut_{i+1}',nut,STEEL,.85)
        units.append(dict(id=f'post_{i+1}',kind='post_assembly',dimensions_inferred=True))
        units.append(dict(id=f'tnut_{i+1}',kind='separate_t_nut',dimensions_inferred=True))
    return g, dict(units=units, installed=False, clamp_force_qualified=False,
                   source_arm_lengths_m=[.2032,.1524], post_diameter_m=.010,
                   bore_diameter_m=.0106, unreported_dimensions_inferred=True)


def fine_cutter():
    g=Geometry(); red=[191,38,47]; blue=[40,67,124]
    # Selected nearly closed review pose. Two independent metal levers and
    # overmoulds remain separate; this is not a simulated cutting joint.
    for sign in [-1,1]:
        # Pointed 9 mm cutting section, 13.5 mm maximum head width.
        outline=[(0,0),(0,sign*.45),(9,sign*6.75),(20,sign*6.75),
                 (29,sign*4.7),(70,sign*20),(116,sign*21),
                 (119,sign*17),(70,sign*14),(28,sign*.7),(9,0)]
        body=cq.Workplane('XY').polyline(outline).close().extrude(3.7).val().translate((0,0,2.75 if sign==1 else 6.45))
        body=body.cut(cq.Workplane('XY').box(9.1,30,20,centered=(False,True,False)).val().translate((-.1,0,0)))
        jaw=cq.Workplane('XY').polyline([(0,sign*.15),(0,sign*.6),(9,sign*6.75),(11,sign*6.75),(11,sign*.15)]).close().extrude(3.7).val().translate((0,0,4.5))
        body=body.fuse(jaw)
        body=body.cut(cq.Solid.makeCylinder(1.5,15,cq.Vector(27,sign*2.8,0)))
        solid(g,f'lever_{sign}',body,STEEL,.85)
        # Rounded moulded grips, following the photographed curved handle.
        # Successive elliptical sections preserve separate red/blue materials
        # without flat sticker-like rectangles or angular slab handles.
        sections=[(34,8.7,.8,.8),(35.5,8.7,3.8,5.3),(40,10,4.8,6.2),
                  (50,13,5.8,6.2),(70,18,6,6.2),(90,20,6,6.2),
                  (110,20,5.4,6.2),(120,20,4.3,5.6),(123,20,2.7,3.8),(125,20,.2,.2)]
        wires=[cq.Workplane('YZ',origin=(x,sign*y,6.5)).ellipse(ry,rz).val() for x,y,ry,rz in sections]
        grip=cq.Solid.makeLoft(wires,False)
        # One watertight exterior per grip; the original colour texture follows
        # the photographed material boundary. Internal overmould layers are
        # not reconstructed, and overlapping shells must not cause z-fighting.
        patch=[(36,3),(36,10),(50,16),(90,23),(119,23),
               (124,20),(119,16),(90,14),(50,7)]
        surface=cad_mesh(grip);g.add(f'moulded_grip_{sign}',surface,blue)
        picture=Image.new('RGB',(2048,512),tuple(blue));draw=ImageDraw.Draw(picture)
        draw.polygon([(x/125*2047,(1-y/30)*511) for x,y in patch],fill=tuple(red))
        uv=np.column_stack([surface.vertices[:,0]/.125,sign*surface.vertices[:,1]/.030])
        surface.visual=trimesh.visual.TextureVisuals(uv=uv,material=PBRMaterial(baseColorTexture=picture,metallicFactor=0,roughnessFactor=.65))
    g.cylinder('rivet',.0034,.0078,[.019,0,.0066],STEEL,metal=.9)
    # Separate spring crossing the open handle gap; no force curve asserted.
    pts=[[.041,-.006,.0065],[.047,-.003,.0065],[.051,0,.0065],[.047,.003,.0065],[.041,.006,.0065]]
    curved_tube(g,'opening_spring',pts,.0005,STEEL,.85)
    return g, dict(review_state='nearly_closed', articulated=False, cutting_qualified=False,
        length_m=.125, head_width_m=.0135, jaw_length_m=.009,
        width_scope='Selected handle pose; manufacturer regional overall-width specifications conflict')


def deburring_tool():
    g=Geometry()
    # Catalogue identifies 12 mm hexagonal aluminum holder, unlike the 8 mm
    # disposable EO1000. Holder length and detailed blade curvature inferred.
    radius=.012/np.sqrt(3)
    handle=trimesh.creation.cylinder(radius,.120,sections=6)
    handle.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]))
    handle.apply_translation([.086,0,radius]);g.add('hexagonal_holder',handle,[43,45,52],role='ordinary_deburring_holder',metal=.2)
    for name,r,l,x in [('release_collar',.005,.006,.023),('tapered_nose',.0038,.010,.015),('blade_socket',.0024,.004,.008)]:
        g.cylinder(name,r,l,[x,0,radius],[52,54,61],axis=(1,0,0),metal=.35)
    points=np.array([[.008,0,radius],[.003,0,radius],[-.002,0,radius+.001],[-.008,0,radius+.006],[-.014,0,radius+.009],[-.019,0,radius+.009]])
    curved_tube(g,'S10_blade_3_2mm',points,.0016,STEEL,.9)
    # Oblique ground end is an explicit visual approximation, not a cutting
    # coefficient or a gauged 40-degree rake surface.
    g.label('model_text','RB1000',.038,.004,[.113,-.006001,radius],(43,45,52),(215,216,219))
    return g, dict(handle_across_flats_m=.012, selected_handle_length_m=.120,
        shank_diameter_m=.0032, blade='S10 / BS1010', blade_change_qualified=False,
        cutting_edge_geometry_inferred=True)


def straight_plug(color):
    g=Geometry()
    # 2.7 in overall / .925 in nose from manufacturer drawing. Nose has
    # an actual annular opening around the recessed 4 mm male contact.
    g.ring('insulating_shroud',.0031,.004,.023495,[.0117475,0,0],color,axis=(1,0,0))
    g.cylinder('banana_core',.00172,.018,[.012,0,0],STEEL,axis=(1,0,0),metal=.9)
    for i in range(6):
        angle=i*np.pi/3
        p=[]
        for x in np.linspace(.003,.021,35):
            r=.00172+.00016*np.sin(np.pi*(x-.003)/.018)
            p.append([x,r*np.cos(angle),r*np.sin(angle)])
        curved_tube(g,f'banana_leaf_{i}',p,.00012,STEEL,.9)
    g.cylinder('finger_guard',.0066,.0025,[.024745,0,0],color,axis=(1,0,0))
    g.profile('moulded_grip',[(0,0),(.0053,0),(.0053,.014),(.0042,.026),(.0036,.029),(0,.029)],color,axis=(1,0,0),position=(.026,0,0))
    for x in [.030,.034,.038,.042]:g.ring('grip_ridge_'+str(x),.0047,.0057,.001,[x,0,0],color,axis=(1,0,0))
    g.profile('strain_relief',[(0,0),(.0036,0),(.0034,.003),(.0023,.01358),(0,.01358)],color,axis=(1,0,0),position=(.055,0,0))
    for x in np.linspace(.057,.066,5):
        r=.0036-(x-.055)/.01358*.0013
        g.ring('relief_ridge_'+str(x),r-.0004,r+.0002,.0006,[x,0,0],color,axis=(1,0,0))
    return g


def meter_leads():
    g=Geometry(); records=[]
    # Four separately counted leads (two 5908A sets) for a future four-wire
    # connection. These are loose, disconnected cables, not an installed route.
    for i in range(4):
        color=[189,37,43] if i%2==0 else [28,29,32]
        x=(i%2)*.240; y=(i//2)*.150; rise=.0055
        def path(radius):
            t=np.linspace(0,3,721); a=2*np.pi*t-np.pi/2
            helix=np.column_stack([x+radius*np.cos(a),y+radius+radius*np.sin(a),.0066+rise*t])
            return np.vstack([[x-.040,y,.0066],helix,[x+.040,y,.0066+3*rise]])
        radius=brentq(lambda r:np.linalg.norm(np.diff(path(r),axis=0),axis=1).sum()-1.2192,.05,.07)
        points=path(radius); curved_tube(g,f'lead_{i+1}_silicone_cable',points,.0036576/2,color)
        for end,origin,tangent in [('A',points[0],points[1]-points[0]),('B',points[-1],points[-2]-points[-1])]:
            # Positive connector X runs from nose toward cable entry.
            direction=tangent/np.linalg.norm(tangent)
            plug=straight_plug(color);R=trimesh.geometry.align_vectors([1,0,0],direction)
            R[:3,3]=origin-direction*.06858
            for node in plug.scene.graph.nodes_geometry:
                t,key=plug.scene.graph[node];m=plug.scene.geometry[key].copy();m.apply_transform(R@t);visual=m.visual.copy()
                g.add(f'lead_{i+1}_{end}_'+node,m,color,role='disconnected_meter_plug');m.visual=visual
        records.append(dict(id=f'lead_{i+1}',set_number=i//2+1,color='red' if i%2==0 else 'black',
            wire_awg=18,cable_outer_diameter_m=.0036576,nominal_cable_length_m=1.2192,
            rest_points_m=points.tolist(),connected=False))
    return g, dict(leads=records, sets=2, electrical_qualified=False,
        cable_length_scope='48 inches between moulded cable entries; connector bodies are additional',
        bend_shape='Authored separated helices for inspection; no flexible-body or gravity-settled cable claim')


def models():
    return [('omax_317864',workholding_kit,{}),('knipex_7803125',fine_cutter,{}),
            ('noga_rb1000',deburring_tool,{}),('pomona_5908a',meter_leads,{})]
