"""Metric KHR-2/2-P reconstruction: full commercial outline and two leads.

The internal foil routing, wire gauge, selected laminate thickness and release
liner are inferred. They are individually tagged and never called vendor CAD.
"""
import bpy
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
for d in ['geometry','evidence']:(HERE/d).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=bpy.data.objects.new('OMEGA_KHR_2_2_P',None);scene.collection.objects.link(root);parts=[]

def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
amber=material('polyimide_amber',(.38,.16,.025),.18,.27)
foil=material('encapsulated_etched_foil',(.22,.10,.025),.65,.38)
psa=material('pressure_sensitive_adhesive',(.56,.40,.16),0,.6)
white=material('FEP_insulation',(.77,.76,.69),0,.35)
metal=material('stripped_conductor',(.6,.61,.58),.95,.3)
liner=material('release_liner',(.64,.59,.47),0,.8)

def finish(o,name,mat,role,basis):
 o.name=name;o.parent=root;o.data.materials.append(mat);o['part_id']=name;o['role']=role;o['basis']=basis;parts.append(o);return o

def disk(name,radius,depth,z,mat,role,basis):
 bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=radius,depth=depth,location=(0,0,z));return finish(bpy.context.object,name,mat,role,basis)

def path(name,points,radius,mat,role,basis):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3;c.resolution_u=1;c.use_fill_caps=True;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,xyz in zip(s.points,points):p.co=(*xyz,1)
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);return finish(o,name,mat,role,basis)

# Source gives 2 inch diameter and <=0.010 inch total except lead exit.
# Select 0.2 mm nominal including PSA; do not use the maximum as a measurement.
disk('heater_laminate',.0254,.00015,.000025,amber,'heater_body','source outline; inferred nominal thickness')
disk('PSA_layer',.0254,.00005,-.000075,psa,'adhesive_layer','-P denotes PSA; thickness inferred')
disk('release_liner',.0254,.00006,-.00013,liner,'removable_liner','selected as-supplied liner; not source-described')
# Subtle visible foil routing is a declared reconstruction, not an electrical
# resistor model. Flat ribbons stay inside the nominal outline.
points=[]
for row in range(25):
 y=-.0216+row*.0018;half=math.sqrt(.0232**2-y*y)
 pair=[(-half,y,.000103),(half,y,.000103)]
 if row%2:pair.reverse()
 points.extend(pair)
verts=[];faces=[];width=.00065;thickness=.000006
for j in range(len(points)-1):
 a=Vector(points[j]);b=Vector(points[j+1]);direction=(b-a).normalized();normal=Vector((-direction.y,direction.x,0))*width/2;k=len(verts)
 for dz in [-thickness/2,thickness/2]:
  for p in [a-normal,a+normal,b+normal,b-normal]:verts.append(tuple(p+Vector((0,0,dz))))
 faces.extend([tuple(k+i for i in q) for q in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]])
mesh=bpy.data.meshes.new('foil_route_mesh');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('foil',mesh);scene.collection.objects.link(o);finish(o,'inferred_foil_routing',foil,'visual_foil_only','inferred routing; resistance and local watt density unvalidated')
leads=[]
for index,y in enumerate([-.002,.002]):
 # Two separate leads leave radially. An outward service loop shows the full
 # 305 mm centreline without hiding excess cable inside the heater.
 start=Vector((.0245,y,.00055));straight=.030;radius=.028;remaining=.305-straight
 sign=-1 if index==0 else 1
 def coil(turns):
  result=[]
  for j in range(601):
   u=turns*j/600;r=radius-.0018*u;angle=-sign*math.pi/2+sign*2*math.pi*u
   result.append((.0245+straight+r*math.cos(angle),y+sign*radius+r*math.sin(angle),.00055))
  return result
 lo,hi=0.,3.
 for _ in range(50):
  mid=(lo+hi)/2;trial=coil(mid);length=sum((Vector(b)-Vector(a)).length for a,b in zip(trial,trial[1:]))
  if length<remaining:lo=mid
  else:hi=mid
 p=[tuple(start)]+coil((lo+hi)/2)
 path('lead_'+str(index+1),p[:-16],.0005,white,'insulated_lead','source 305 mm radial FEP lead; gauge and staging shape inferred')
 path('stripped_'+str(index+1),p[-17:],.00016,metal,'electrical_node','selected stripped length and AWG28 conductor')
 # Terminal reinforcement is visible in the manufacturer family photo.
 bpy.ops.mesh.primitive_cube_add(size=1,location=(.023,y,.0005));o=bpy.context.object;o.dimensions=(.004,.002,.0008);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'lead_exit_patch_'+str(index+1),amber,'lead_exit_reinforcement','envelope inferred from family photo')
 leads.append(dict(id='HEATER_NODE_'+('A' if index==0 else 'B'),position_m=p[-1],centerline_m=p,nominal_length_m=.305))
# Small liner pull tab, separate from the commercial heater outline.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-.027,0,-.00013));o=bpy.context.object;o.dimensions=(.006,.006,.00006);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'liner_pull_tab',liner,'liner_grasp','inferred release-liner handling tab')
bpy.context.view_layer.update()
rows=[dict(id=o.name,role=o['role'],basis=o['basis'],bounds_m=[list(map(min,zip(*[o.matrix_world@Vector(v) for v in o.bound_box]))),list(map(max,zip(*[o.matrix_world@Vector(v) for v in o.bound_box])))]) for o in parts]
(HERE/'parts.json').write_text(json.dumps(rows,indent=2)+'\n')
(HERE/'interfaces.json').write_text(json.dumps(dict(model='Omega KHR-2/2-P',units='m',heater_diameter_m=.0508,selected_body_thickness_m=.0002,manufacturer_max_body_thickness_m=.000254,
 mounting_face=dict(center_m=[0,0,-.0001],normal=[0,0,-1],bonded_radius_on_50mm_emitter_m=.025,radial_overhang_m=.0004),
 nonactive_grip_annulus_m=[.024,.0254],lead_exits_radial=True,terminals=leads,
 force_sense_topology='Each physical node accepts a distinct force and sense connection; the asset has two heater conductors, not four fictitious heater leads',
 internal_pattern_verified=False,contact_qualified=False),indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_layers[0].cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.19,.24,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
scene.view_settings.view_transform='Filmic';scene.view_settings.exposure=-2.5
for name,pos,power,size in [('key',(.02,-.08,.2),12,.18),('fill',(.15,.1,.18),10,.15)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.03,.02,0))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('camera');cam=bpy.data.objects.new('camera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=.22;cam.location=(.10,-.16,.26);cam.rotation_euler=(Vector((.036,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'geometry/omega_khr_2_2_p.blend'))
for o in parts:
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
root.select_set(True);bpy.ops.export_scene.gltf(filepath=str(HERE/'geometry/omega_khr_2_2_p.glb'),export_format='GLB',export_selected=True,export_apply=True,export_extras=True)
scene.render.filepath=str(HERE/'evidence/complete.png');bpy.ops.render.render(write_still=True)
d.ortho_scale=.065;cam.location=(.035,-.055,.13);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(HERE/'evidence/laminate.png');bpy.ops.render.render(write_still=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(HERE/'build_receipt.json').write_text(json.dumps(dict(builder_sha256=sha(Path(__file__)),source_sha256=sha(HERE/'sources.json'),blender=bpy.app.version_string,parts=len(parts),vendor_cad=False,contact_qualified=False,artifacts_sha256={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'geometry').glob('*'))}),indent=2)+'\n')
