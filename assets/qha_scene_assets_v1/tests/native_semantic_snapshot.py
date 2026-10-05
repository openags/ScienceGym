"""Read-only Blender native equivalence snapshot. Run with blender -b --python."""
import bpy,sys,json,hashlib,pathlib
args=sys.argv[sys.argv.index('--')+1:];source=pathlib.Path(args[0]);output=pathlib.Path(args[1]);bpy.ops.wm.open_mainfile(filepath=str(source))
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [value(x) for x in v]
 except (TypeError,ValueError):return getattr(v,'name',str(type(v).__name__))
def scalars(obj):
 out={}
 for p in obj.bl_rna.properties:
  if p.identifier in {'rna_type','bl_rna'} or p.type in {'COLLECTION','POINTER'}:continue
  try:out[p.identifier]=value(getattr(obj,p.identifier))
  except (AttributeError,TypeError,ValueError):pass
 return out
def custom(o):return {k:value(o[k]) for k in sorted(o.keys())}
def nodes(tree):
 if not tree:return None
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'properties':scalars(n),'inputs':[{'name':s.name,'identifier':s.identifier,'value':value(s.default_value) if hasattr(s,'default_value') else None} for s in n.inputs]} for n in sorted(tree.nodes,key=lambda x:x.name)],'links':sorted([(x.from_node.name,x.from_socket.identifier,x.to_node.name,x.to_socket.identifier) for x in tree.links])}
r={
 'schema':'sciencegym3d.native_semantics.v1',
 'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'data':o.data.name if o.data else None,'matrix_world':value(o.matrix_world),'matrix_local':value(o.matrix_local),'dimensions':value(o.dimensions),'bound_box':value(o.bound_box),'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'custom':custom(o),'modifiers':[{'type':x.type,'values':scalars(x)} for x in o.modifiers],'constraints':[{'type':x.type,'values':scalars(x)} for x in o.constraints]} for o in sorted(bpy.data.objects,key=lambda x:x.name)],
 'meshes':[{'name':x.name,'vertices':[list(v.co) for v in x.vertices],'edges':[list(e.vertices) for e in x.edges],'polygons':[{'vertices':list(p.vertices),'material':p.material_index,'smooth':p.use_smooth} for p in x.polygons],'materials':[m.name if m else None for m in x.materials],'uv_layers':[{'name':u.name,'values':[list(v.uv) for v in u.data]} for u in x.uv_layers],'custom':custom(x)} for x in sorted(bpy.data.meshes,key=lambda x:x.name)],
 'curves':[{'name':x.name,'type':x.bl_rna.identifier,'values':scalars(x),'font':x.font.name if hasattr(x,'font') and x.font else None,'materials':[m.name if m else None for m in x.materials]} for x in sorted(bpy.data.curves,key=lambda x:x.name)],
 'materials':[{'name':x.name,'values':scalars(x),'nodes':nodes(x.node_tree),'custom':custom(x)} for x in sorted(bpy.data.materials,key=lambda x:x.name)],
 'cameras':[{'name':x.name,'values':scalars(x),'dof':scalars(x.dof)} for x in sorted(bpy.data.cameras,key=lambda x:x.name)],
 'lights':[{'name':x.name,'values':scalars(x),'nodes':nodes(x.node_tree)} for x in sorted(bpy.data.lights,key=lambda x:x.name)],
 'worlds':[{'name':x.name,'values':scalars(x),'nodes':nodes(x.node_tree)} for x in sorted(bpy.data.worlds,key=lambda x:x.name)],
 'collections':[{'name':x.name,'objects':sorted(o.name for o in x.objects),'children':sorted(o.name for o in x.children)} for x in sorted(bpy.data.collections,key=lambda x:x.name)],
 'scenes':[{'name':x.name,'camera':x.camera.name if x.camera else None,'render':scalars(x.render),'image_settings':scalars(x.render.image_settings),'cycles':scalars(x.cycles),'view_settings':scalars(x.view_settings),'display_settings':scalars(x.display_settings),'units':scalars(x.unit_settings),'custom':custom(x),'frame_current':x.frame_current,'frame_start':x.frame_start,'frame_end':x.frame_end,'rigidbody':x.rigidbody_world is not None} for x in sorted(bpy.data.scenes,key=lambda x:x.name)],
 'safety':{'text_blocks':len(bpy.data.texts),'images':len(bpy.data.images),'actions':len(bpy.data.actions),'object_drivers':sum(len(x.animation_data.drivers) for x in bpy.data.objects if x.animation_data)},
}
encoded=json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();output.write_text(json.dumps({'semantic_sha256':hashlib.sha256(encoded).hexdigest(),'snapshot':r},indent=2)+'\n')
print('SNAPSHOT_SHA256',hashlib.sha256(encoded).hexdigest())
