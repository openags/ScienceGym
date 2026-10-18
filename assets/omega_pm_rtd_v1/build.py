"""Omega P-M-A-1/4-3-1/2-PS-12: documented probe and cable, inferred fitting.

Run with Blender 2.82+. Geometry uses metres; the probe tip is the origin
and its axis is +X. The cable is a separately identified rest-shape mesh.
"""
import bpy
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
for n in ['geometry','evidence']:(HERE/n).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('OMEGA_PM_A_QUARTER_3_HALF_PS_12',None);scene.collection.objects.link(root)
parts=[]


def material(name,color,metal=0,rough=.4):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    return m


STEEL=material('stainless_sheath',(.48,.51,.54),.92,.28)
FITTING=material('machined_fitting',(.58,.60,.62),.95,.3)
PVC=material('shielded_pvc_jacket',(.014,.017,.020),0,.5)
RED=material('red_wire_insulation',(.56,.013,.018),0,.45)
WHITE=material('white_wire_insulation',(.8,.81,.78),0,.45)
TIN=material('stripped_tinned_conductor',(.65,.67,.66),.9,.24)


def finish(o,name,mat,role):
    o.name=name;o.parent=root;o.data.materials.append(mat);o['part_id']=name;o['role']=role
    parts.append(o);return o


def cylinder(name,radius,length,x,mat,role,vertices=96):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=length,
        location=(x,0,0),rotation=(0,math.pi/2,0))
    return finish(bpy.context.object,name,mat,role)


def tube_path(name,points,radius,mat,role):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius
    curve.bevel_resolution=3;curve.resolution_u=1;curve.use_fill_caps=True
    line=curve.splines.new('POLY');line.points.add(len(points)-1)
    for p,xyz in zip(line.points,points):p.co=(*xyz,1)
    obj=bpy.data.objects.new(name,curve);scene.collection.objects.link(obj)
    return finish(obj,name,mat,role)


# Manufacturer ordering grammar gives 1/4 inch diameter and 3 inch immersion
# length. The fitting begins at the end of that immersion length.
cylinder('immersion_sheath',.003175,.0762,.0381,STEEL,'immersed_probe')
tip=cylinder('closed_tip',.003175,.0002,.0001,STEEL,'probe_tip')
bevel=tip.modifiers.new('rounded_tip_edge','BEVEL');bevel.width=.0001;bevel.segments=3
# The manufacturer identifies 1/2 NPT, but gives no fitting envelope drawing.
# These are reconstruction dimensions; the thread is visual, not a mating
# contact mesh. Insertion tasks grip the hex and never credit thread engagement.
cylinder('thread_core',.0096,.015,.0837,FITTING,'mounting_thread_core')
pitch=.0254/14
thread=[]
for i in range(1201):
    x=.0765+i/1200*.0144;angle=2*math.pi*(x-.0765)/pitch
    r=.0097+(x-.0765)/32
    thread.append((x,r*math.cos(angle),r*math.sin(angle)))
tube_path('thread_crest_visual',thread,.00038,FITTING,'visual_thread_only')
cylinder('hex_grip',.0127/math.cos(math.pi/6),.006,.0942,FITTING,'grip_hex',6)
cylinder('cable_transition',.0048,.019,.1067,STEEL,'cable_transition')
cylinder('strain_relief',.003,.006,.1192,PVC,'strain_relief')

# A continuous 12 ft cable, including the selected 80 mm four-wire breakout.
# Coil pitch exceeds the selected 4 mm jacket diameter; no self-overlap is
# hidden in the reference asset. This rest shape is not a dynamics model.
start=.1222;lead_start=.20;radius=.065;rise=.0045;breakout=.08
jacket_length=3.6576-breakout
turns=(jacket_length-(lead_start-start))/math.sqrt((2*math.pi*radius)**2+rise**2)
points=[(start,0,0),(lead_start,0,0)]
for i in range(1,2401):
    u=turns*i/2400;theta=-math.pi/2+2*math.pi*u
    points.append((lead_start+radius*math.cos(theta),radius+radius*math.sin(theta),rise*u))
tube_path('shielded_cable',points,.002,PVC,'cable_rest_shape')
end=Vector(points[-1]);tangent=(Vector(points[-1])-Vector(points[-2])).normalized()
normal=Vector((-tangent.y,tangent.x,0)).normalized()
terminal_points=[]
for i in range(4):
    p=[end+tangent*(breakout*j/20)+normal*((i-1.5)*.006*min(1,j/10)) for j in range(21)]
    tube_path('wire_'+str(i+1),p[:-2],.00055,RED if i<2 else WHITE,'insulated_lead')
    tube_path('stripped_'+str(i+1),p[-3:],.000203,TIN,'stripped_conductor')
    terminal_points.append(list(p[-1]))

bpy.context.view_layer.update()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
interfaces=dict(model='Omega P-M-A-1/4-3-1/2-PS-12',units='m',
    tip=[0,0,0],insertion_axis=[-1,0,0],probe_diameter=.00635,immersion_length=.0762,
    selected_grip=dict(part='hex_grip',center=[.0942,0,0],across_flats=.0254),
    terminals=[dict(id='lead_'+str(i+1),position_m=p,color='red' if i<2 else 'white',
                    electrical_node='A' if i<2 else 'B') for i,p in enumerate(terminal_points)],
    cable=dict(nominal_length_m=3.6576,jacket_diameter_m=.004,rest_points_m=points,
               breakout_length_m=.08,physical_cable_qualified=False),
    inferred=['fitting envelope','hex across flats','cable diameter','breakout length','lead colors','thread contact geometry'],
    thread_engagement_qualified=False)
(HERE/'interfaces.json').write_text(json.dumps(interfaces,indent=2)+'\n')
(HERE/'parts.json').write_text(json.dumps([dict(id=o.name,role=o['role'],dimensions_m=list(o.dimensions)) for o in parts],indent=2)+'\n')

scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.14,.18,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-1.8
for name,pos,power,size in [('key',(.05,-.15,.35),35,.3),('fill',(.3,.2,.25),25,.25)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos
    o.rotation_euler=(Vector((.15,.05,0))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('camera');camera=bpy.data.objects.new('camera',data);scene.collection.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=.34
camera.location=(.12,-.3,.4);camera.rotation_euler=(Vector((.145,.045,.01))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/omega_pm_rtd.blend'))
# Blender 2.82 glTF omits curve objects unless explicitly converted. Keep
# editable paths in the saved .blend, but export every physical part as mesh.
for o in parts:
    if o.type in {'CURVE','FONT'}:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
        bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/omega_pm_rtd.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
scene.render.filepath=str(HERE/'evidence/complete.png');bpy.ops.render.render(write_still=True)
camera.location=(.05,-.20,.14);camera.data.ortho_scale=.145
camera.rotation_euler=(Vector((.059,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(HERE/'evidence/probe.png');bpy.ops.render.render(write_still=True)
(HERE/'build_receipt.json').write_text(json.dumps(dict(builder_sha256=sha(Path(__file__)),blender=bpy.app.version_string,
    parts=len(parts),source_sha256=sha(HERE/'sources.json'),artifacts_sha256={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'geometry').glob('*'))},
    vendor_cad=False,contact_qualified=False),indent=2)+'\n')
