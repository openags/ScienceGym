"""Source-photo constrained coating packages with explicit dimensional hypotheses.

These closed stock units and removable-cap inspection views are not dispensing
or curing simulations. Manufacturer artwork is not copied into the textures.
"""
import math
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry
from build_supplies import solid, curved_tube, STEEL


def sleeve(g, name, radius, bottom, top, lines, dark=False):
    """Original typeset identification on an actual cylindrical label surface."""
    bg = (239, 240, 235)
    fg = (30, 33, 37)
    picture = Image.new('RGB', (1536, 1024), bg)
    draw = ImageDraw.Draw(picture)
    if dark:
        # The inspected black can retains a white upper label; only the lower
        # colour panel is dark. Do not turn the entire container into black.
        draw.rectangle((0,580,1536,1024),fill=(35,37,40))
    for y, text, size in lines:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
        ink=(234,236,233) if dark and y>=580 else fg
        draw.text((768, y), text, fill=ink, font=font, anchor='mm')
    # Rear text makes clear this is authored identification, not original art.
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
    for x in [220, 1316]:
        draw.text((x, 410), 'RECONSTRUCTION', fill=fg, font=font, anchor='mm')
        draw.text((x, 465), 'Scale inferred', fill=fg, font=font, anchor='mm')
    angles = np.linspace(-np.pi, np.pi, 129)
    vertices = [[radius*np.sin(a), -radius*np.cos(a), z] for z in [bottom, top] for a in angles]
    faces = []
    for j in range(128):
        faces.extend([[j, j+1, 129+j+1], [j, 129+j+1, 129+j]])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    g.add(name, mesh, [255, 255, 255], role='original_identification_text')
    uv = [[i/128, v] for v in [0, 1] for i in range(129)]
    mesh.visual = trimesh.visual.TextureVisuals(uv=uv, material=PBRMaterial(
        baseColorTexture=picture, roughnessFactor=.63, metallicFactor=0,
        baseColorFactor=[255,255,255,255], doubleSided=False))


def aerosol(white=True):
    g = Geometry()
    color = [233, 235, 230] if white else [28, 30, 33]
    # Overall Ø66 x 208 mm is a selected hypothesis, not a manufacturer's
    # dimensional claim. The cap/body ratio follows the inspected front photo.
    g.profile('sealed_can_shell', [
        (0, .005), (.027, .002), (.031, .001), (.0325, .005),
        (.0325, .150), (.0315, .154), (.028, .159), (.021, .165),
        (.013, .169), (.0125, .172), (.0117, .172), (.0122, .169),
        (.0205, .1645), (.0275, .1585), (.031, .1535), (.032, .1495),
        (.032, .0055), (.0305, .0018), (.027, .0028), (0, .0058), (0, .005)
    ], STEEL, metal=.8, role='inferred_pressure_container_shell')
    g.profile('rolled_lower_seam', [(.0308, 0), (.0326, 0), (.033, .001),
        (.033, .004), (.0326, .005), (.0308, .005), (.0308, 0)], STEEL, metal=.8)
    g.profile('valve_mounting_cup', [(0,.171),(.012,.171),(.0125,.172),
        (.0125,.174),(.011,.175),(0,.175),(0,.171)], STEEL, metal=.85)
    g.cylinder('inferred_valve_stem', .002, .007, [0,0,.177], [231,230,220])
    # The catalogue identifies an EZ Touch conical tip. The exposed nozzle
    # topology, dimensions and actuator travel remain reconstruction hypotheses.
    cone = cq.Solid.makeCone(7.5, 5.0, 13.0, cq.Vector(0,0,179))
    cone = cone.cut(cq.Solid.makeCylinder(1.2, 9, cq.Vector(0,-9,187), cq.Vector(0,1,0)))
    solid(g, 'inferred_conical_actuator', cone, [185,40,34])
    g.ring('nozzle_orifice_insert', .00035, .00105, .0012,
        [0,-.0058,.187], [226,195,62], axis=(0,1,0))
    g.profile('inferred_press_pad', [(0,.192),(.005,.192),(.0058,.194),
        (.0048,.195),(0,.195),(0,.192)], [223,189,59])
    cap_start = len(g.parts)
    g.profile('cap_hollow_shell', [(.033,.154),(.033,.158),(.032,.180),
        (.0255,.2055),(.0247,.208),(0,.208),(0,.2066),(.024,.2066),
        (.0242,.205),(.0306,.1795),(.0316,.158),(.0316,.154),(.033,.154)],
        color, role='removable_protective_cap')
    # Small stepped shoulder visible in the front reference photograph.
    g.ring('cap_moulded_shoulder', .0319, .03245, .001,
        [0,0,.180], color, role='removable_protective_cap')
    cap_parts = [p['id'] for p in g.parts[cap_start:]]
    suffix = 'WHITE' if white else 'BLACK'
    sleeve(g, 'can_identification_text', .03255, .006, .150,
        [(120,'KRYLON',85),(270,'ColorMaster',70),(390,'PAINT + PRIMER',43),
         (620,'FLAT '+suffix,65),(800,'12 oz / 340 g',44)], dark=not white)
    return g, dict(selected_dimensions_m=[.066,.066,.208],
        dimensions_status='unmeasured_reconstruction_hypothesis',
        paper_identity='Brand/family and flat colour reported; exact SKU and package revision unreported',
        staged_quantity=1, net_content_g=340, material_dynamics_qualified=False,
        inspection=dict(kind='slide',parts=cap_parts,axis=[0,0,1],maximum=.10,frame_separated_parts=True,
            label='保护盖抬起 · 几何检查',basis='Authored separation view; snap fit, removal force and spray operation unqualified'))


def silver_paste():
    g = Geometry(); amber = [92,46,15]
    # A 75 mm preparation stand in the manufacturer's photograph supplies a
    # rough visual scale reference only. Perspective and packaging revisions
    # prevent treating the selected Ø32 x 63 mm package as measured dimensions.
    g.profile('amber_bottle_open_mouth', [(0,0),(.014,0),(.016,.002),
        (.016,.037),(.0157,.040),(.0125,.046),(.0125,.060),
        (.011,.060),(.011,.046),(.014,.039),(.014,.003),(0,.003),(0,0)],
        amber, role='inferred_glass_container', alpha=230)
    # Separate inferred neck thread; cap path is an exploded inspection view,
    # not a physically validated unscrewing motion.
    a = np.linspace(0, 6*np.pi, 360)
    p = np.column_stack([.0127*np.cos(a), .0127*np.sin(a), .050+a/(2*np.pi)*.0022])
    curved_tube(g, 'inferred_neck_thread', p, .00065, amber)
    # 25 g / manufacturer's approximate density 2.25 g/ml. This is a nominal
    # stock-volume representation; viscosity, adhesion and dispensing are open.
    volume = 25/2.25*1e-6; radius = .0138; height = volume/(math.pi*radius**2)
    g.cylinder('nominal_paste_stock', radius, height, [0,0,.003+height/2],
        [125,130,132], role='nominal_material_stock', metal=.35)
    cap_start = len(g.parts)
    g.profile('cap_white_hollow_shell', [(.0144,.047),(.0144,.061),
        (.0135,.063),(0,.063),(0,.061),(.0138,.061),(.0138,.047),(.0144,.047)],
        [229,231,226], role='removable_container_cap')
    for i, a in enumerate(np.linspace(0,2*np.pi,48,endpoint=False)):
        # Construct in millimetres before scaling: trimesh's default absolute
        # degeneracy tolerance otherwise removes these tiny end-cap triangles.
        rib=trimesh.creation.cylinder(.25,10,sections=24)
        rib.apply_scale(.001);rib.apply_translation([.0144*np.cos(a),.0144*np.sin(a),.055])
        g.add('cap_grip_rib_'+str(i),rib,[217,220,216],role='removable_container_cap')
    g.cylinder('cap_black_top', .0128, .0004, [0,0,.0632], [29,33,34], role='removable_container_cap')
    g.cylinder('cap_inferred_sealing_liner', .0133, .001,
        [0,0,.0604], [223,224,213], role='removable_container_cap')
    cap_parts = [p['id'] for p in g.parts[cap_start:]]
    sleeve(g, 'bottle_identification_text', .01605, .008, .035,
        [(180,'PELCO',78),(390,'16032',74),(600,'SILVER PASTE',47),(820,'25 g',56)])
    return g, dict(selected_dimensions_m=[.0321,.0321,.0634],
        dimensions_status='photo_relative_scale_hypothesis_not_measurement',
        selection_status='demo_material_candidate_not_identified_paper_brand',
        net_content_g=25, nominal_density_g_ml=2.25, nominal_stock_volume_m3=volume,
        material_dynamics_qualified=False, compatibility_qualified=False,
        inspection=dict(kind='slide',parts=cap_parts,axis=[0,0,1],maximum=.055,frame_separated_parts=True,
            label='银浆瓶盖分离 · 几何检查',basis='Exploded separation view; thread engagement, opening method and handling unqualified'))


def models():
    return [('krylon_51502',lambda:aerosol(True),{}),
            ('krylon_51602',lambda:aerosol(False),{}),
            ('pelco_16032',silver_paste,{})]
