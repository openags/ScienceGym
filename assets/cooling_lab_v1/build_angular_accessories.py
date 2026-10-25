"""Original, source-constrained reflection accessories for asset inspection.

Outer dimensions, mirror figures and mounts are hypotheses. These meshes do
not simulate calibrated optics, the coupled mechanism, or robot operations.
"""
import math
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import solid, export_review, slotted_screw, STEEL, BLACK, DARK


def box_mm(x, y, z, center):
    return cq.Workplane('XY').box(x, y, z).val().translate(center)


def label(g,name,text,width,height,center):
    """Original text with pixel aspect and font size matched to its surface."""
    picture=Image.new('RGB',(round(256*width/height),256),tuple(BLACK))
    draw=ImageDraw.Draw(picture);size=190
    while True:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        if draw.textlength(text,font=font)<picture.width*.92:break
        size-=1
    draw.text((picture.width/2,128),text,font=font,fill=(228,231,226),anchor='mm')
    mesh=g.label(name,text,width,height,center,BLACK,[228,231,226])
    mesh.visual.material.baseColorTexture=picture
    return mesh


def transform_parts(g, names, matrix):
    for p in g.parts:
        if p['id'] in names:
            m = g.scene.geometry[p['id']]
            m.apply_transform(matrix)
            p['bounds_m'] = m.bounds.tolist()


def knob(g, name, center, radius=.006, length=.009, axis=(0, -1, 0)):
    # The shallow flutes are an authored grip approximation, not a knurl spec.
    origin = np.array(center)
    rotation = trimesh.geometry.align_vectors([0, 0, 1], axis)
    shape = cq.Solid.makeCylinder(radius*1000, length*1000,
        cq.Vector(0, 0, -length*500))
    for a in np.linspace(0, 2*np.pi, 16, endpoint=False):
        shape = shape.cut(cq.Solid.makeCylinder(.65, length*1000+2,
            cq.Vector(radius*1000*np.cos(a), radius*1000*np.sin(a), -length*500-1)))
    m = solid(g, name, shape, DARK)
    m.apply_transform(rotation); m.apply_translation(origin)
    g.parts[-1]['bounds_m'] = m.bounds.tolist()


def plate_mirror(g, name, center, width, height, yaw=0, tilt=0, front_datum=False):
    """Separate reflective face and backing, initially in XZ facing -Y."""
    names = []
    for suffix, size, pos, color, metallic in [
        ('back', [width+.004, .004, height+.004], [0, .003 if front_datum else .0025, 0], DARK, .1),
        ('face', [width, .001, height], [0, .0005 if front_datum else 0, 0], [211, 218, 220], .94)]:
        identity = name+'_'+suffix
        g.box(identity, size, pos, color, role='inferred_optical_mirror', metal=metallic)
        if suffix == 'face': g.scene.geometry[identity].visual.material.roughnessFactor = .12
        names.append(identity)
    r = trimesh.transformations.rotation_matrix(yaw, [0, 0, 1]) @ trimesh.transformations.rotation_matrix(tilt, [1, 0, 0])
    r[:3, 3] = center
    transform_parts(g, names, r)


def harrick():
    g = Geometry()
    # Selected 190 x 220 mm base, not a catalogue envelope or 6700 adapter.
    base = box_mm(190, 220, 10, (0, 0, 5))
    for x in [-82, 82]:
        for y in [-91, 91]:
            slot = cq.Workplane('XY').center(x, y).slot2D(14, 6.5, 90).extrude(12).val().translate((0, 0, -1))
            base = base.cut(slot)
    solid(g, 'optical_base_slotted_plate', base, BLACK, .2)
    # Four external mirrors follow the central FTIR base in printed p126.
    # Curvature/positions are inferred; rays and focal lengths are unqualified.
    for side, x in [('left', -.060), ('right', .060)]:
        g.box('rear_'+side+'_foot', [.032, .030, .006], [x, .070, .013], DARK)
        g.cylinder('rear_'+side+'_post', .005, .085, [x, .070, .0585], STEEL, metal=.8)
        g.box('rear_'+side+'_saddle', [.014, .014, .010], [x,.069,.096], DARK)
        normal = np.array([.32 if x < 0 else -.32, -.94741754, 0])
        center = np.array([x, .055, .106])
        g.cylinder('rear_'+side+'_mirror_cell', .024, .006, center-normal*.004, DARK, axis=normal)
        radius = .021; curvature = .18
        rr = np.linspace(0, radius, 33)
        sag = curvature-np.sqrt(curvature**2-rr**2)
        profile = [(0, -.002), (radius, -.002)] + list(zip(rr[::-1], sag[::-1])) + [(0, -.002)]
        m = g.profile('rear_'+side+'_concave_face', profile, [215, 220, 221],
            axis=normal, position=center, metal=.95, role='inferred_optical_mirror')
        m.visual.material.roughnessFactor = .12
        for i, a in enumerate(np.linspace(0, 2*np.pi, 3, endpoint=False)):
            p = center + np.array([.022*np.cos(a), 0, .022*np.sin(a)])
            g.cylinder('rear_'+side+'_retainer_'+str(i), .002, .008, p, STEEL, axis=normal, metal=.8)
        g.box('rear_'+side+'_adjuster_boss', [.008,.014,.006], [x,.067,.123], DARK)
        knob(g, 'rear_'+side+'_adjuster', [x, .068, .127], .0035, .007, (0,0,1))
    for side, x in [('left', -.062), ('right', .062)]:
        g.box('fold_'+side+'_foot', [.030, .030, .006], [x, -.048, .013], DARK)
        g.box('fold_'+side+'_pedestal', [.010, .012, .050], [x, -.048, .041], DARK)
        plate_mirror(g, 'fold_'+side, [x, -.054, .084], .033, .043,
                     yaw=np.radians(-35 if x<0 else 35))
        knob(g, 'fold_'+side+'_adjuster', [x, -.034, .077], .004, .009, (0,1,0))
    g.box('stage_receiver', [.066, .059, .014], [0, -.009, .017], DARK)
    for x in [-.023, .023]:
        g.cylinder('stage_inferred_socket_'+str(x), .004, .004, [x, -.009, .026], STEEL, metal=.8)
    knob(g, 'stage_receiver_lock', [0, -.046, .018])
    start = len(g.parts)
    # The HRS product photograph is an open C bracket. The circular dark patch
    # on its mirror is interpreted as the reflected upper aperture, not a hole.
    g.box('hrs_bottom', [.060, .054, .005], [0, -.009, .0305], BLACK)
    g.box('hrs_rear', [.060, .005, .053], [0, .0155, .0595], BLACK)
    top = box_mm(60, 54, 5, (0, -9, 88.5))
    top = top.cut(cq.Solid.makeCylinder(8.25, 7, cq.Vector(0,-9,85)))
    top = top.cut(cq.Solid.makeCylinder(10.2, 1.5, cq.Vector(0,-9,89.5)))
    solid(g, 'hrs_apertured_top', top, BLACK)
    plate_mirror(g, 'hrs_solid_inclined_mirror', [0, -.010, .059], .039, .040, tilt=np.pi/4)
    # Triangular braces leave an open front rather than filling the light path.
    for x in [-22.5, 22.5]:
        brace = cq.Workplane('YZ').polyline([(-27,33), (11,33), (11,78)]).close().extrude(2).val().translate((x,0,0))
        solid(g, 'hrs_side_brace_'+str(x), brace, DARK)
    label(g,'hrs_identification','HRS 12 deg',.044,.004,[0,-.0361,.0885])
    moving = [p['id'] for p in g.parts[start:]]
    masks = []
    for diameter, x in [(3,-.032),(6,0),(13,.032)]:
        name = 'hrs_mask_'+str(diameter)+'mm'
        ring = cq.Solid.makeCylinder(10,.6,cq.Vector(x*1000,-88,10)).cut(
            cq.Solid.makeCylinder(diameter/2,1,cq.Vector(x*1000,-88,9.8)))
        solid(g, name, ring, DARK, role='interchangeable_aperture_mask')
        masks.append(dict(part=name,diameter_m=diameter*.001,center_m=[x,-.088,.0103],normal=[0,0,1]))
    for x in [-.08,.08]:
        for y in [-.05,.05]:slotted_screw(g,'base_screw_'+str(x)+'_'+str(y),[x,y,.010])
    return g, dict(
        selected_base_dimensions_m=[.190,.220,.010],
        selected_stage_envelope_m=[.060,.054,.063],
        selected_mask_outer_diameter_m=.020,
        dimensional_status='unmeasured_reconstruction_hypothesis_except_documented_aperture_diameters',
        masks=masks,
        parts_by_component=dict(optical_base=[p['id'] for p in g.parts if p['id'] not in moving and p['id'] not in [m['part'] for m in masks]],
            horizontal_stage=moving,aperture_masks=[m['part'] for m in masks]),
        interfaces=[dict(id='sample_support',center_m=[0,-.009,.0901],face_normal=[0,0,-1],
            basis='Conditional datum with the selected 0.6 mm mask seated at Z89.5 mm. Face-down specimen must cover the 13 mm opening; footprint, support and retention remain unqualified'),
            dict(id='mask_seat',center_m=[0,-.009,.0895],basis='Inferred counterbore seat, not the top surface at Z91 mm'),
            dict(id='stage_receiver',center_m=[0,-.009,.028],basis='Authored plug-in mounting hypothesis')],
        inspection=dict(kind='slide',parts=moving,axis=[0,0,1],maximum=.10,frame_separated_parts=True,
            label='Harrick 上样架抬起 · 安装结构检查',basis='Exploded geometry inspection. Receiver dimensions, engagement and removal forces unverified'),
        mirror_interpretation='Solid sloped mirror, with no invented circular through-hole; the circular feature in the official photograph is interpreted as an aperture reflection.',
        mounting_adapter_supplied=False,optical_alignment_qualified=False,sample_retention_qualified=False)


def angle_scale(g, center, radius=.064):
    """Original scale typography, ticks in the physical rotation plane XZ."""
    x,y,z=center
    for degree in range(20,86):
        a=np.radians(degree);length=.0035 if degree%10==0 else .002 if degree%5==0 else .001
        r=radius-length/2
        mesh=g.box('scale_tick_'+str(degree),[.00035,.00015,length],
            [0,0,0],[224,227,222],role='original_angle_scale')
        rotation=trimesh.transformations.rotation_matrix(-a,[0,1,0]);rotation[:3,3]=[x+r*np.sin(a),y,z-r*np.cos(a)]
        transform_parts(g,['scale_tick_'+str(degree)],rotation)
    for degree in [20,30,40,50,60,70,80,85]:
        a=np.radians(degree);r=radius+.004
        label(g,'scale_number_'+str(degree),str(degree),.006,.003,
            [x+r*np.sin(a),y-.0001,z-r*np.cos(a)])


def spectratech():
    g=Geometry()
    # An inferred local optical-plane placement keeps the unchanged 36 mm
    # M3 backing inside the open housing throughout the rigid review sweep.
    beam_y=-.020
    base=box_mm(180,100,8,(0,0,4))
    for x in [-78,78]:
        for y in [-40,40]:base=base.cut(cq.Solid.makeCylinder(3.2,10,cq.Vector(x,y,-1)))
    solid(g,'chassis_base',base,BLACK,.2)
    g.box('chassis_optical_backplate',[.170,.006,.175],[0,.028,.0955],BLACK,metal=.15)
    housing=box_mm(22,78,133,(79,-4,74.5))
    housing=housing.cut(box_mm(21,70,125,(76.5,-5,74.5)))
    housing=housing.cut(cq.Solid.makeCylinder(10,26,cq.Vector(66,beam_y*1000,67),cq.Vector(1,0,0)))
    solid(g,'source_side_open_housing',housing,STEEL,.75)
    for z in [.030,.115]:
        g.cylinder('housing_fastener_'+str(z),.0017,.004,[.091,0,z],STEEL,axis=(1,0,0),metal=.9)
    # Catalogue p43 explicitly labels M4 / Sample. It is NOT a fifth
    # independent mirror followed by a separate specimen. The selected M4
    # reference occupies the sample holder, opposite the linked M3 mirror.
    # The catalogue places the V assembly above and left of the input fold,
    # beside the source housing. Local pivot offsets remain inferred. Keeping
    # the complete carrier left of that housing preserves its roof and mirrors.
    pivot_x=-.015;pivot_z=.165
    phi=np.radians(20);pivot=np.array([pivot_x,beam_y,pivot_z])
    # The photo shows extended faces along the carrier, not little mirrors
    # centred on one initial ray. A 105-degree near-retro corner is a selected
    # engineering hypothesis, NOT a dimension taken from the model-500 drawing.
    # The NRC comparison demonstrates this class of tandem reflector only.
    # Incoming inclination, corner angle and the 2.5 mm offset must be reviewed.
    corner=np.radians(105);sample_radius=.018;m3_radius=.0335
    tangent=np.array([np.cos(phi-corner+np.pi/2),0,np.sin(phi-corner+np.pi/2)])
    sample_normal=np.cross([0,1,0],tangent)
    sample_center=pivot-sample_radius*tangent
    m3_center=pivot+m3_radius*np.array([np.sin(phi),0,-np.cos(phi)])
    incoming=np.array([-np.sin(np.radians(15)),0,np.cos(np.radians(15))])
    offset_axis=np.array([incoming[2],0,-incoming[0]]);ray_anchor=pivot+.0025*offset_axis
    m2=ray_anchor+incoming*((.030-ray_anchor[2])/incoming[2])
    m3_normal=np.array([-np.cos(phi),0,-np.sin(phi)])
    hit3=m2+incoming*np.dot(pivot-m2,m3_normal)/np.dot(incoming,m3_normal)
    after3=incoming-2*np.dot(incoming,m3_normal)*m3_normal
    hit4=hit3+after3*np.dot(sample_center-hit3,sample_normal)/np.dot(after3,sample_normal)
    after4=after3-2*np.dot(after3,sample_normal)*sample_normal
    m5=hit4+after4*((.067-hit4[2])/after4[2])
    optical_points=[np.array(p) for p in [[.12,beam_y,.067],[0,beam_y,.067],
        m2,hit3,hit4,m5,[-.12,beam_y,.067]]]
    mirror_records=[];m3_parts=[]
    for number,index in [(1,1),(2,2),(3,3),(5,5)]:
        name='m'+str(number);hit=optical_points[index]
        center=m3_center if number==3 else hit
        incoming=hit-optical_points[index-1];incoming/=np.linalg.norm(incoming)
        outgoing=optical_points[index+1]-hit;outgoing/=np.linalg.norm(outgoing)
        normal=incoming-outgoing;normal/=np.linalg.norm(normal)
        if np.dot(normal,incoming)>0:normal=-normal
        start=len(g.parts)
        stem=center-normal*.005
        length=.029 if number==3 else .045
        g.cylinder(name+'_mount_stem',.002,length,[stem[0],beam_y+length/2,stem[2]],STEEL,axis=(0,1,0),metal=.8)
        plate_start=len(g.parts)
        plate_mirror(g,name,[0,0,0],.032,.064 if number==3 else .014,front_datum=True)
        ids=[p['id'] for p in g.parts[plate_start:]]
        r=np.eye(4);r[:3,:3]=np.column_stack([[0,1,0],-normal,np.cross([0,1,0],-normal)]);r[:3,3]=center
        transform_parts(g,ids,r)
        if number==3:m3_parts=[p['id'] for p in g.parts[start:]]
        mirror_records.append(dict(part=name+'_face',center_m=center.tolist(),nominal_hit_m=hit.tolist(),normal=normal.tolist(),incoming=incoming.tolist(),outgoing=outgoing.tolist()))
    # The same rotating carrier owns M3, the M4 specimen/reference and pointer.
    # Exact linkage, pivot, lever lengths and the optical prescription are
    # reconstruction hypotheses; a rigid angle sweep does not calibrate optics.
    pts=[(0,-6)]+[(70*np.sin(a),-70*np.cos(a)) for a in np.radians(np.linspace(0,90,91))]+[(6,0)]
    sector=cq.Workplane('XZ').polyline(pts).close().extrude(3).val().translate((pivot_x*1000,16,pivot_z*1000))
    solid(g,'stationary_quadrant_plate',sector,BLACK)
    angle_scale(g,[pivot_x,.0128,pivot_z])
    g.cylinder('rotary_bearing_housing',.012,.013,[pivot_x,.0165,pivot_z],DARK,axis=(0,1,0))
    g.cylinder('rotary_spindle',.004,.030,[pivot_x,.008,pivot_z],STEEL,axis=(0,1,0),metal=.9)
    start=len(g.parts)
    basis=np.column_stack([[0,1,0],tangent,sample_normal])
    frame_matrix=np.eye(4);frame_matrix[:3,:3]=basis;frame_matrix[:3,3]=sample_center
    local_start=len(g.parts)
    # Upper frame/guide ends stop short of the shared optical corner. The
    # former overhang crossed M3 even though the two parts moved together.
    frame=box_mm(32,38.5,3,(0,-1.75,-2.7)).cut(box_mm(16,26,5,(0,0,-2.7)))
    solid(g,'sample_carrier_open_frame',frame,DARK)
    for side in [-1,1]:
        u=side*.0142
        g.box('sample_guide_'+str(side*14.2),[.004,.0385,.004],[u,-.00275,.0008],DARK)
        g.box('sample_leaf_retainer_'+str(side*14.2),[.003,.026,.0007],[side*.0115,0,.0008],STEEL,metal=.85)
    # Two edge stops support the specimen without a full-width front ridge
    # across the grazing-angle exit. Their exact form remains inferred.
    for side in [-1,1]:
        g.box('sample_lower_stop_'+str(side),[.006,.004,.004],[side*.011,-.019,.0008],DARK)
    # An actual removable alignment reference represents M4 at the initial
    # inspection pose. Masks/blank remain loose alternatives, not hidden samples.
    g.box('alignment_mirror_7004_001',[.024,.034,.0012],[0,0,-.0006],[215,221,222],role='m4_removable_alignment_reference',metal=.95)
    g.scene.geometry['alignment_mirror_7004_001'].visual.material.roughnessFactor=.12
    transform_parts(g,[p['id'] for p in g.parts[local_start:]],frame_matrix)
    for name,end in [('m3_carrier_arm',m3_center-np.array(mirror_records[2]['normal'])*.005),('sample_carrier_arm',sample_center-sample_normal*.007)]:
        a=np.array([pivot_x,.005,pivot_z]);b=np.array([end[0],.005,end[2]])
        axis=b-a;length=np.linalg.norm(axis)
        g.cylinder(name,.0028,length,(a+b)/2,DARK,axis=axis/length)
    # The sample's back connects to the common carrier, outside the beam plane.
    back=sample_center-sample_normal*.007
    g.cylinder('sample_carrier_stem',.002,.025,[back[0],-.0075,back[2]],STEEL,axis=(0,1,0),metal=.8)
    # No large front knob is visible in the catalogue photograph. The carrier
    # edge is the proposed handling surface; the hidden bearing is unmeasured.
    r=.066
    a=pivot+np.array([np.sin(phi)*r,.014,-np.cos(phi)*r])
    pointer_root=pivot+[0,.014,0];pointer_axis=a-pointer_root
    g.cylinder('rotary_pointer_arm',.0015,r,(a+pointer_root)/2,DARK,axis=pointer_axis/r)
    tip=g.box('rotary_pointer_tip',[.001,.0005,.008],[0,0,0],STEEL,metal=.7)
    matrix=trimesh.transformations.rotation_matrix(phi,[0,-1,0]);matrix[:3,3]=a
    transform_parts(g,['rotary_pointer_tip'],matrix)
    moving=m3_parts+[p['id'] for p in g.parts[start:]]
    masks=[]
    for width,x in [(6,-.051),(13,-.023)]:
        mask=box_mm(24,34,1.4,(x*1000,-17,8.7))
        slot=box_mm(width,28,3,(x*1000,-27,8.7)).fuse(cq.Solid.makeCylinder(width/2,3,cq.Vector(x*1000,-13,7.2)))
        solid(g,'slot_mask_'+str(width)+'mm',mask.cut(slot),BLACK,role='interchangeable_slot_mask')
        masks.append(dict(part='slot_mask_'+str(width)+'mm',width_m=width*.001,center_m=[x,-.020,.0087],normal=[0,0,1]))
    g.box('blank_plate',[.024,.034,.0014],[.038,-.017,.0087],BLACK,role='accessory_blank_plate')
    label(g,'model_identification','MODEL 500',.070,.007,[-.042,.0248,.018])
    for x in [-.073,.058]:
        g.cylinder('backplate_fastener_'+str(x),.002,.001,[x,.024,.028],STEEL,axis=(0,1,0),metal=.8)
    mask_transform=frame_matrix.copy()
    mask_transform[:3,3]+=basis@np.array([.023,.017,-.0092])
    reference_record=dict(part='alignment_mirror_7004_001',role='M4 sample position occupied by removable alignment reference',
        center_m=sample_center.tolist(),nominal_hit_m=hit4.tolist(),normal=sample_normal.tolist(),
        incoming=((optical_points[4]-optical_points[3])/np.linalg.norm(optical_points[4]-optical_points[3])).tolist(),
        outgoing=((optical_points[5]-optical_points[4])/np.linalg.norm(optical_points[5]-optical_points[4])).tolist())
    return g,dict(selected_base_dimensions_m=[.180,.100,.008],
        selected_backplate_dimensions_m=[.170,.006,.175],
        dimensional_status='unmeasured_reconstruction_hypothesis_except_documented_mask_widths_and_angle_range',
        masks=masks,incidence_range_degrees=[20,85],initial_incidence_degrees=20,
        optical_surface_sequence=['M1','M2','M3','M4_sample_or_reference','M5'],
        sample_face_normal_initial=sample_normal.tolist(),sample_center_m=sample_center.tolist(),
        selected_corner_degrees=105,selected_input_inclination_degrees=15,selected_ray_offset_m=.0025,
        geometric_probe=dict(source_x_m=.12,exit_x_m=-.12,beam_y_m=beam_y,beam_z_m=.067,
            y_offsets_m=[-.0025,0,.0025],z_offsets_m=[-.0004,0,.0004],
            scope='Selected 5 x 0.8 mm parallel-ray diagnostic; not a manufacturer beam, focus, throughput or spectral model'),
        sample_frame_transform_m=frame_matrix.tolist(),
        mask_fit_hypothesis=dict(part='slot_mask_13mm',transform_m=mask_transform.tolist(),side_clearance_m=.0002,retainer_gap_m=.00025,
            scope='Alternative geometry-only seated mask, with the displayed alignment reference removed. No double occupation, forces or manipulation credit'),
        nominal_fold_geometry=dict(incidence_degrees=20,points_m=[p.tolist() for p in optical_points],mirrors=mirror_records,sample_surface=reference_record,
            scope='M1/M2/M3/M4-reference/M5 initial center ray only. Finite-aperture coverage over the angle range and manufacturer focal prescription are unqualified'),
        optical_direction='source right to detector left',
        parts_by_component=dict(optical_chassis=[p['id'] for p in g.parts if p['id'] not in moving and p['id'] not in [m['part'] for m in masks]],
            sample_rotation_assembly=[p for p in moving if p!='alignment_mirror_7004_001'],slot_masks=[m['part'] for m in masks],alignment_mirror=['alignment_mirror_7004_001']),
        interfaces=[dict(id='sample_loading',center_m=sample_center.tolist(),normal=sample_normal.tolist(),basis='M4 carrier on the shared M3/M4 rotor; initial reference face is actually present. Pivot and local mechanism dimensions are inferred'),
            dict(id='rotary_carrier_edge',center_m=(sample_center+[0,-.018,0]).tolist(),basis='Proposed carrier-edge approach. The source photograph does not establish a separate front rotation knob; grasp and locking forces remain unqualified')],
        inspection=dict(kind='hinge',parts=moving,axis=[0,1,0],pivot_m=pivot.tolist(),maximum=-math.radians(65),
            label='Spectra-Tech M3 / M4 样品组件 · 20–85° 几何检查',basis='Source-topology correction: M4 is the sample, not an extra mirror. Selected shared rigid rotor; finite optical coverage and calibration are unqualified'),
        mounting_adapter_supplied=False,optical_alignment_qualified=False,sample_retention_qualified=False)


def build():
    items=[]
    for identity,label,resource,builder in [
        ('harrick_hrs','Harrick 12° HRS + FTIR 光学底座 · 选定重构','equipment:ANGLE_12',harrick),
        ('spectratech_500','Spectra-Tech 500 变角反射附件 · 选定重构','equipment:ANGLE_VAR',spectratech)]:
        g,details=builder()
        items.append(dict(id=identity,label=label,resource_id=resource,
            geometry=export_review(g,'angular_'+identity),details=details,
            paper_variant_identified=False,asset_accepted=False,manipulation_qualified=False,
            status='source_constrained_reconstruction_pending_dimensional_and_mount_review'))
    write_json(HERE/'angular_accessories.json',dict(schema_version=1,items=items,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'angular_accessory_sources.json',HERE/'angular_topology_rejected.json',HERE/'angular_rotor_rejected.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']],
        reference_images_redistributed=False,owner_acceptance=None,
        scope='Bench-staged original reconstruction geometry. No installed/optically calibrated configuration or robot manipulation is qualified.'))
    print(json.dumps(dict(accessory_types=len(items),component_meshes=sum(i['geometry']['parts'] for i in items))))


if __name__=='__main__':build()
