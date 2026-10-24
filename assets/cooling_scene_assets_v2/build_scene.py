"""Original, metric reconstruction. Blender 2.82+; no imported vendor CAD.

Run: blender --background --python build_scene.py -- --render
All non-paper dimensions are design choices recorded in dimensions.json.
The scene is a review assembly, not a robot dynamics environment.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from interaction_geometry import PIN_SIGNALS, SENSOR_LAYOUT
for sub in ['geometry', 'evidence']:
    (ROOT / sub).mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene.render.engine = 'CYCLES'
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.view_layers[0].cycles.use_denoising = True
bpy.context.preferences.filepaths.save_version = 0
scene.render.resolution_x = 1600
scene.render.resolution_y = 1150
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .25, .3, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Filmic - Medium High Contrast' if bpy.app.version < (3, 0, 0) else 'Medium High Contrast'
scene.view_settings.exposure = -1
registry = []
current = None


def material(name, color, metal=0, rough=.35, noise=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if noise:
        n = m.node_tree.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 160
        n.inputs['Detail'].default_value = 3
        b = m.node_tree.nodes.new('ShaderNodeBump')
        b.inputs['Strength'].default_value = noise
        b.inputs['Distance'].default_value = .00012
        m.node_tree.links.new(n.outputs['Fac'], b.inputs['Height'])
        m.node_tree.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


AL = material('polished_aluminum', (.67, .7, .73), 1, .18)
BRUSH = material('machined_aluminum', (.48, .52, .57), .92, .3, .12)
FOIL = material('aluminized_mylar_fine_wrinkles', (.72, .74, .76), 1, .16, .7)
WHITE = material('flat_white_coating', (.84, .85, .82), 0, .82, .12)
BLACK = material('flat_black_coating', (.012, .014, .017), 0, .85, .1)
FOAM = material('foamular_insulation', (.48, .25, .39), 0, .92, .2)
PE = material('solid_polyethylene', (.83, .84, .78), 0, .42)
FILM = material('PE_film_visual_approximation', (.82, .86, .88), 0, .22)
FILM.node_tree.nodes['Principled BSDF'].inputs['Transmission'].default_value = .98
FILM.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value = 1.5
LDPE = material('white_LDPE_bag_visual_approximation', (.87,.87,.84), 0, .38)
LDPE.node_tree.nodes['Principled BSDF'].inputs['Transmission'].default_value = .60
COPPER = material('copper', (.65, .26, .1), .9, .3)
ORANGE = material('frame_insert_orange', (.8, .27, .025), 0, .5)
DARK = material('graphite_plastic', (.025, .032, .038), .1, .42)
CASE = material('instrument_light_gray', (.58, .62, .62), .15, .45)
GREEN = material('terminal_green', (.05, .22, .12), 0, .5)
RED = material('red_insulation', (.55, .018, .012), 0, .5)
YELLOW = material('K_type_lead', (.75, .57, .04), 0, .6)
BLUE = material('display_blue', (.025, .11, .16), .2, .25)
GLASS = material('display_glass', (.008, .022, .026), .1, .15)


def root(name, xyz):
    global current
    current = bpy.data.objects.new(name, None)
    scene.collection.objects.link(current)
    current.location = xyz
    current['role'] = 'assembly_root'
    return current


def finish(obj, name, mat, role='structural', bevel=0):
    obj.name = current.name + '__' + name if current else name
    if current:
        obj.parent = current
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        obj.data.use_auto_smooth = True
        m = obj.modifiers.new('manufactured_edge', 'BEVEL')
        m.width = bevel; m.segments = 3
        obj.modifiers.new('weighted_normals', 'WEIGHTED_NORMAL')
    obj['part_id'] = obj.name
    obj['role'] = role
    obj['geometry_basis'] = 'source_dimensions_plus_declared_reconstruction'
    registry.append(obj)
    return obj


def box(name, size, pos, mat, role='structural', bevel=.0005):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object; o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, mat, role, bevel)


def cylinder(name, radius, height, pos, mat, role='structural', rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=height, location=pos)
    o = bpy.context.object
    if rotation: o.rotation_euler = rotation
    for p in o.data.polygons: p.use_smooth = abs(p.normal.z) < .5
    return finish(o, name, mat, role, min(.0003, height/5))


def ring(name, inner, outer, height, pos, mat, role='structural'):
    n = 128; verts = []; faces = []
    for z, r in [(-height/2, outer), (height/2, outer), (-height/2, inner), (height/2, inner)]:
        verts += [(r*math.cos(2*math.pi*i/n),r*math.sin(2*math.pi*i/n),z) for i in range(n)]
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                      (n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o = bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.location = pos
    return finish(o,name,mat,role,.0001)


def wire(name, points, mat, radius=.0005):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points): p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o)
    return finish(o,name,mat,'routed_lead')


def ribbon(name,points,width,thickness,mat,role):
    verts=[];faces=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        normal=Vector((-tangent.y,tangent.x,0)).normalized()
        for zz,side in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            v=Vector(p)+normal*(side*width/2)+Vector((0,0,zz*thickness/2));verts.append(tuple(v))
    for i in range(len(points)-1):
        a=4*i;b=a+4
        faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
    faces.extend([(0,2,3,1),(len(verts)-4,len(verts)-3,len(verts)-1,len(verts)-2)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o)
    return finish(o,name,mat,role,0)


def label(name, text, pos, size, mat=WHITE, front=True):
    c=bpy.data.curves.new(name,'FONT');c.body=text;c.size=size;c.extrude=.000005
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.location=pos
    if front: o.rotation_euler=(math.pi/2,0,0)
    return finish(o,name,mat,'identity_label')


def extrusion(name, x, y, z, length, vertical=False):
    # Four real slot recesses are built as separated flanges, not painted lines.
    w=.02
    if vertical:
        box(name+'_core',(.011,.011,length),(x,y,z),BRUSH)
        for sx in [-1,1]:
            for sy in [-1,1]:box(name+'_flange_%s_%s'%(sx,sy),(.007,.007,length),(x+sx*.0065,y+sy*.0065,z),AL)
    else:
        box(name+'_core',(.011,length,.011),(x,y,z),BRUSH)
        for sx in [-1,1]:
            for sz in [-1,1]:box(name+'_flange_%s_%s'%(sx,sz),(.007,length,.007),(x+sx*.0065,y,z+sz*.0065),AL)


def cooling(name, xyz, black=False, exploded=False, fixed=False, mapping=False):
    root(name,xyz)
    # Base/frame endpoints are inferred from the SI photograph; 305 mm inner span is measured text.
    for x in [-.1625,.1625]:
        extrusion('rail_'+str(x),x,0,.012,.34)
        box('orange_insert_'+str(x),(.002,.325,.004),(x+.008,0,.022),ORANGE)
        ring('upright_'+str(x),.007,.01,.275,(x,.03,.158),BRUSH)
        box('upright_bracket_'+str(x),(.034,.035,.004),(x,.03,.026),BRUSH)
        for yy in [.018,.042]: cylinder('bracket_bolt',.003,.004,(x,yy,.03),DARK)
    box('acrylic_base',(.305,.28,.006),(0,0,.027),PE)
    box('mylar_base',(.297,.272,.0002),(0,0,.0302),FOIL,bevel=0)
    # Physical height adjuster visible below the raised assembly in SI Fig 1a2.
    box('lift_foot',(.075,.065,.008),(0,0,.035),DARK)
    cylinder('lift_thread',.006,.027,(0,0,.052),BRUSH)
    box('lift_plate',(.17,.17,.005),(0,0,.068),FOIL)
    z=.0705
    dz=.026 if exploded else 0
    for i in range(2):
        zz=z+.0125+i*(.025+dz)
        cylinder('foam_%d'%(i+1),.025,.025,(0,0,zz),FOAM,'insulation')
        ring('foam_mylar_%d'%(i+1),.025,.02503,.025,(0,0,zz),FOIL,'radiation_cover')
    ez=z+.05025+2*dz
    cylinder('emitter_copper',.025,.0005,(0,0,ez),COPPER,'sample')
    cylinder('emitter_'+('black' if black else 'white')+'_coating',.025,.00006,(0,0,ez+.00028),BLACK if black else WHITE,'sample_surface')
    ring('PE_support',.038,.051,.057,(0,0,z+.0285),PE,'removable_support')
    ring('PE_support_mylar',.051,.05103,.057,(0,0,z+.0285),FOIL,'radiation_cover')
    fz=z+.057+3*dz
    film_thickness=.000050 if fixed else .000016
    film_material=LDPE if fixed else FILM
    cylinder('cover_lower',.0635,film_thickness,(0,0,fz),film_material,'removable_film')
    ring('film_spacer',.0535,.0635,.0064,(0,0,fz+.0032+dz),BRUSH,'removable_spacer')
    cylinder('cover_upper',.0635,film_thickness,(0,0,fz+.0064+2*dz),film_material,'removable_film')
    sz=z+.0064+5*dz
    ring('radiation_shield',.07,.076,.057,(0,0,sz+.0285),AL,'removable_shield')
    ring('aperture_plate',.025,.076,.001,(0,0,sz+.0575),AL,'removable_aperture')
    rz=z+.0505+.15
    # Example curve, with a visible design-hypothesis status. Actual path comes from site/date inputs.
    pts=[(-.155+i*.31/40,.03+.025*(1-((-1+i/20)**2)),rz) for i in range(41)]
    if fixed:
        ribbon('fixed_reflector_band',pts,.06,.0015,AL,'fixed_reflector')
    else:
        ribbon('reflector_track',pts,.006,.0015,BRUSH,'track')
        box('reflector_carriage',(.015,.013,.004),(0,.055,rz+.002),DARK,'movable_carriage')
        cylinder('solar_reflector',.03,.001,(0,.055,rz+.005),AL,'removable_reflector')
    # Four independent sides of the lead terminal support plus retained, non-floating wires.
    box('terminal_mount',(.115,.02,.005),(0,-.105,.034),DARK)
    sensor_layout=SENSOR_LAYOUT if mapping else SENSOR_LAYOUT[:1]
    for i,(probe,target,point,region,basis) in enumerate(sensor_layout):
        x=-.048+i*.016
        box('TC_terminal_%d'%i,(.01,.012,.008),(x,-.105,.04),YELLOW,'terminal')
        for dx in [-.002,.002]:cylinder('TC_screw',.0012,.001,(x+dx,-.105,.0445),BRUSH)
        endpoint=(point[0],point[1],z+point[2]+(2*dz if i==0 else 0))
        contact=cylinder('probe_contact_'+probe,.0008,.0003,endpoint,COPPER,'sensor_contact_hypothesis')
        contact['target_part']=name+'__'+target
        contact['basis']=basis
        contact['region']=region
        wire('sensor_lead_%d'%i,[(x,-.105,.043),(x,-.075,.039),(point[0],-.035,endpoint[2]),endpoint],YELLOW,.00035)
    return current


def keithley(name, xyz):
    root(name,xyz)
    box('chassis',(.213,.370,.089),(0,0,.052),CASE,bevel=.002)
    box('front_panel',(.213,.004,.089),(0,-.187,.052),PE,bevel=.001)
    box('display',(.163,.001,.045),(-.022,-.1895,.072),GLASS,bevel=.001)
    label('model','KEITHLEY  2425',(-.1,-.1902,.091),.0045)
    label('readback','OUTPUT OFF',(-.09,-.1904,.07),.006,material('VFD',(.1,.65,.56)))
    label('source','SourceMeter',(.018,-.1904,.053),.003)
    for col,key in enumerate(['V','I','OHM','FCTN','V','I','UP','DN']):
        x=-.071+col*.0155
        cylinder('measure_source_'+key+'_'+str(col),.0035,.0015,(x,-.191,.040),DARK,'push_button',(math.pi/2,0,0))
        label('key_legend_'+str(col),key,(x-.002,-.192,.039),.0018)
    for row,keys in enumerate([['LOCAL','REL','FILTER','LIMIT','TRIG','SWEEP','<','>'],['DIGITS SPEED','STORE RECALL','CONFIG MENU','EXIT ENTER']]):
        spacing=.0155 if row==0 else .031
        for col,key in enumerate(keys):
            x=-.071+col*spacing+(0 if row==0 else .0077);zz=.029-row*.010
            box('key_'+key,(.012 if row==0 else .027,.002,.0045),(x,-.191,zz),CASE,'push_button',.0015)
            label('legend_'+key,key,(x-(.005 if row==0 else .012),-.1922,zz-.0007),.0013,DARK)
    for i,key in enumerate(['UP','AUTO','DN']):
        box('range_'+key,(.009,.002,.005),(.054,-.191,.040-i*.011),CASE,'push_button',.001)
        label('range_legend_'+key,key,(.050,-.1922,.039-i*.011),.0018,DARK)
    for col in range(2):
        for row in range(2):
            x=.076+col*.018; zz=.078-row*.02
            o=ring('sense' if col==0 else 'force',.002,.0055,.004,(x,-.192,zz),RED if row==0 else DARK,'electrical_port')
            o.rotation_euler=(math.pi/2,0,0)
    label('port_label','SENSE  INPUT',(.067,-.191,.089),.0028,DARK)
    box('output_button',(.012,.003,.008),(.078,-.191,.026),DARK,'push_button')
    label('output_label','ON/OFF',(.07,-.193,.025),.002)
    cylinder('power',.003,.002,(-.096,-.191,.019),DARK,'push_button',(math.pi/2,0,0))
    for x in [-.116,.116]:
        box('handle_side',(.008,.11,.052),(x,-.135,.039),DARK)
        cylinder('handle_pivot',.008,.005,(x,-.085,.052),DARK,rotation=(0,math.pi/2,0))
    box('handle_front',(.238,.008,.009),(0,-.192,.01),DARK)
    for x in [-.085,.085]:
        for y in [-.12,.13]:box('rubber_foot',(.018,.024,.008),(x,y,.004),DARK)
    for i in range(18):box('side_vent_%d'%i,(.001,.004,.035),(.107,-.04+i*.009,.057),DARK,bevel=0)
    box('rear_GPIB',(.037,.006,.012),(-.04,.188,.05),DARK,'electrical_port')
    box('rear_IEC',(.027,.006,.02),(.07,.188,.037),DARK,'electrical_port')


def usb_tc(xyz):
    root('MCC_USB_TC',xyz)
    box('case',(.12852,.08839,.03556),(0,0,.01778),DARK,bevel=.003)
    box('top_label',(.09,.039,.0002),(0,0,.0357),CASE,bevel=0)
    label('identity','USB-TC',(-.035,-.006,.0359),.009,DARK,False)
    # Figure2 topology: each 26-pin bank is interrupted by a CJC after ten
    # terminals. Pitch and offsets are inferred from enclosure proportions.
    for bank,y in enumerate([-.035,.035]):
        for i in range(26):
            pin=bank*26+i+1
            x=-.055+i*.0039+(.009 if i>=10 else 0)
            o=box('pin_%02d'%pin,(.0036,.006,.008),(x,y,.035),GREEN,'screw_terminal',bevel=.0002)
            o['signal']=PIN_SIGNALS[pin];o['pin_number']=pin
            # Inferred cavity dimensions, but actual open geometry rather than
            # a painted dot standing in for a conductor-entry interface.
            bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.0011,depth=.008,location=(xyz[0]+x,xyz[1]+y,xyz[2]+.034),rotation=(math.pi/2,0,0))
            cutter=bpy.context.object
            mod=o.modifiers.new('wire_entry_cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
            bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter,do_unlink=True)
            screw=cylinder('pin_%02d_screw'%pin,.0011,.0007,(x,y,.0394),BRUSH,'terminal_screw')
            bpy.ops.mesh.primitive_cube_add(size=1,location=(xyz[0]+x,xyz[1]+y,xyz[2]+.0398))
            cutter=bpy.context.object;cutter.dimensions=(.0025,.00045,.00065)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            mod=screw.modifiers.new('driver_slot','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
            bpy.context.view_layer.objects.active=screw;bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(cutter,do_unlink=True)
            entry=ring('pin_%02d_wire_entry'%pin,.0011,.0013,.0002,(x,y+(-.0031 if y<0 else .0031),.034),DARK,'wire_entry')
            entry.rotation_euler.x=math.pi/2
            label('pin_%02d_label'%pin,str(pin),(x-.001,y+(.005 if y<0 else -.007),.039),.0022,WHITE,False)
        cylinder('CJC_'+str(bank),.002,.003,(-.01345,y,.038),DARK,'CJC_sensor')
    # Chamfered Type-B shell, inferred envelope. Native opening supports review
    # of insertion direction; it is not a dimensionally qualified connector.
    outer=[(-.005,.014),(.005,.014),(.005,.021),(.0025,.024),(-.0025,.024),(-.005,.021)]
    inner=[(-.0042,.0148),(.0042,.0148),(.0042,.0207),(.0021,.0232),(-.0021,.0232),(-.0042,.0207)]
    verts=[(xx,y,z) for xx in [.061,.069] for profile in [outer,inner] for y,z in profile]
    faces=[]
    for i in range(6):
        j=(i+1)%6
        faces += [(i,j,12+j,12+i),(6+i,18+i,18+j,6+j),(12+i,12+j,18+j,18+i),(i,6+i,6+j,j)]
    mesh=bpy.data.meshes.new('USB_B_shell');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('USB_B_shell',mesh);bpy.context.collection.objects.link(obj)
    finish(obj,'USB_B',BRUSH,'electrical_port')
    box('USB_B_insulator',(.001,.007,.006),(.062,0,.0185),DARK,'connector_insert',0)


def bath(xyz):
    root('THERMO_A25_AC150_HYPOTHESIS',xyz)
    box('A25_lower_cabinet',(.273,.483,.29),(0,0,.145),CASE,bevel=.007)
    box('A25_rear_cabinet',(.273,.22,.20),(0,.1315,.39),CASE,bevel=.005)
    for x in [-.112]:box('A25_left_wall',(.049,.263,.20),(x,-.11,.39),CASE,bevel=.004)
    for x in [.112]:box('A25_right_wall',(.049,.263,.20),(x,-.11,.39),CASE,bevel=.004)
    box('A25_front_wall',(.175,.057,.20),(0,-.213,.39),CASE,bevel=.004)
    box('front_blue_panel',(.245,.008,.30),(0,-.245,.21),BLUE,bevel=.004)
    for i in range(18):box('intake_%d'%i,(.215,.003,.004),(0,-.25,.10+i*.009),DARK,bevel=.0003)
    # Four walls around a real open bath well; no solid box over the loading port.
    for x in [-.115,.115]:box('rim_side',(.043,.228,.02),(x,-.09,.50),BRUSH)
    for y in [-.192,.012]:box('rim_end',(.173,.02,.02),(0,y,.50),BRUSH)
    box('bath_floor',(.173,.184,.004),(0,-.09,.30),BRUSH)
    for x in [-.087,.087]:box('bath_wall',(.002,.184,.20),(x,-.09,.40),BRUSH)
    for y in [-.183,.003]:box('bath_wall',(.173,.002,.20),(0,y,.40),BRUSH)
    box('controller_body',(.165,.199,.239),(0,.115,.6295),CASE,bevel=.007)
    box('controller_display',(.11,.003,.06),(0,.014,.689),GLASS,bevel=.002)
    label('controller_label','AC150',(-.05,.010,.729),.011,DARK)
    for i in range(5):cylinder('controller_key',.007,.003,(-.048+i*.024,.010,.64),DARK,'push_button',(math.pi/2,0,0))
    label('bath_label','THERMO  A25',(-.105,-.251,.393),.014,WHITE)
    box('removable_lid',(.195,.205,.004),(.25,-.09,.04),BRUSH,'removable_lid')
    box('lid_handle',(.07,.018,.018),(.25,-.09,.051),DARK,'grasp_handle')
    cylinder('immersion_RTD',.003175,.17,(.035,-.09,.45),BRUSH,'probe')
    box('calibration_copper_block',(.04,.04,.04),(0,-.09,.36),COPPER,'calibration_fixture')


cooling('COOLER_WHITE',(-.23,0,0))
cooling('COOLER_BLACK',(.23,0,0),True)
cooling('COOLER_EXPLODED',(1.15,0,0),exploded=True)
cooling('COOLER_FIXED_BAND',(1.65,0,0),fixed=True)
cooling('COOLER_THERMAL_MAP',(2.20,0,0),mapping=True)
keithley('KEITHLEY_2425',(-.24,.85,0))
usb_tc((.08,.74,0))
bath((.53,1.03,0))
exec(compile((ROOT/'extra_devices.py').read_text(),str(ROOT/'extra_devices.py'),'exec'),globals())
current=None
box('presentation_floor',(200,200,.02),(0,0,-.02),material('floor',(.15,.17,.19),0,.8),bevel=0)

def area(name, pos, energy, size, target):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('key',(-.6,-.6,1.6),100,1.4,(0,0,.12))
area('strip',(1,.2,1.4),130,.8,(0,0,.15))
area('fill',(-1,1,1),80,1,(0,0,.1))
d=bpy.data.cameras.new('ReviewCamera');camera=bpy.data.objects.new('ReviewCamera',d);scene.collection.objects.link(camera);scene.camera=camera
d.type='ORTHO'
def view(pos,target,scale):
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=scale
view((.74,-1.15,.85),(0,0,.13),.97)
bpy.context.view_layer.update()
parts=[{'id':o.name,'root':o.parent.name if o.parent else None,'role':o.get('role'),
        'local_position_m':list(o.location),'bounds_m':list(o.dimensions),
        'contact_target':o.get('target_part'), 'contact_region':o.get('region'),
        'signal':o.get('signal'), 'pin_number':o.get('pin_number'),
        'physics_validated':False} for o in registry if o.parent]
(ROOT/'parts.json').write_text(json.dumps({'unit':'m','parts':parts},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'geometry/cooling_pilot.blend'),compress=True)
# Only assemblies are exported. Studio floor/lights/camera are presentation assets.
sys.path.insert(0,str(ROOT))
from export_geometry import export
export()
if '--render' in sys.argv:
    from render_views import render
    render()
print('PILOT_ASSET_COMPLETE',len(parts),'parts')
