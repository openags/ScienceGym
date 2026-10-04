"""Independent read-only Blender inspection of saved native or freshly imported GLB.
Usage: blender --background --factory-startup --disable-autoexec --python tests/independent_geometry_audit.py -- native|glb
Writes observations to review/; never rebuilds or saves scene assets.
"""
import bpy, bmesh, json, sys, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
mode=sys.argv[sys.argv.index('--')+1]
assert mode in ('native','glb')
if mode=='native':
    bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/midinfrared_lab.blend'),use_scripts=False)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(P/'geometry/midinfrared_lab.glb'))
bpy.context.view_layer.update()
S=bpy.context.scene; O=bpy.data.objects
report={'audit_kind':'independent fresh read of saved '+mode,'blender_version':bpy.app.version_string,'errors':[],'checks':{},'observations':{}}
def check(name,value,detail=None):
    report['checks'][name]=bool(value)
    if not value:report['errors'].append({'check':name,'detail':detail})
def near(a,b,t=2e-6):return len(a)==len(b) and max([abs(x-y) for x,y in zip(a,b)]+[0])<t
def world_vertices(o):
    return [o.matrix_world@v.co for v in o.data.vertices]
def bounds(o):
    v=world_vertices(o);lo=[min(p[i] for p in v) for i in range(3)];hi=[max(p[i] for p in v) for i in range(3)];return lo,hi
contract=json.loads((P/'operation_binding_contract.json').read_text())
aff=json.loads((P/'affordances.json').read_text())
inv=json.loads((P/'asset_inventory.json').read_text())
roots=[o for o in O if o.name.startswith('ASSET.')]
anchors=[o for o in O if o.name.startswith('ANCHOR.')]
check('exact_13_roots',set(o.name for o in roots)=={'ASSET.A%02d'%n for n in range(1,14)})
check('exact_44_anchor_objects',set(o.name for o in anchors)=={'ANCHOR.R%02d.%s'%(n,r) for n in range(1,23) for r in ('primary','control')})
check('exact_22_operation_ids',set(x['operation_id'] for x in contract['operations'])=={'R%02d'%n for n in range(1,23)})
check('exact_5_station_ids',set(contract['station_ids'])=={'S%02d'%n for n in range(1,6)})
check('exact_8_branch_ids',set(contract['branch_ids'])=={'B%02d'%n for n in range(1,9)})
for r in roots:
    check(r.name+'_identity_transform',near(tuple(r.matrix_world.translation),(0,0,0)) and near(tuple(r.scale),(1,1,1)))
    check(r.name+'_metadata',r.get('asset_id')==r.name[-3:] and not r.get('physical_execution_enabled',True) and not r.get('physical_geometry_validated',True))
for a in aff['anchors']:
    o=O.get(a['scene_object']);t=O.get(a['target_object']);owner=O.get('ASSET.'+a['asset_id'])
    check(a['anchor_id']+'_concrete_mesh_target',o is not None and t is not None and t.type=='MESH')
    if o is None or t is None:continue
    check(a['anchor_id']+'_owner',o.parent==owner and t.parent==owner and o.get('target_object')==t.name)
    check(a['anchor_id']+'_world_position',near(tuple(o.matrix_world.translation),a['translation_m']) and near(tuple(o.matrix_world.translation),tuple(t.matrix_world.translation)))
    q=o.matrix_world.to_quaternion();check(a['anchor_id']+'_rotation',near((q.x,q.y,q.z,q.w),a['rotation_quaternion_xyzw']))
    check(a['anchor_id']+'_disabled',not o.get('physical_execution_enabled',True) and a['qualified_pose'] is None)
for op in contract['operations']:
    for role in ('primary','control'):
        a=O.get(op[role+'_anchor']);t=O.get(op[role+'_target'])
        check(op['operation_id']+'_'+role+'_contract_consistent',a is not None and t is not None and a.get('target_object')==t.name and a.parent is not None and a.parent.name=='ASSET.'+op['primary_asset_id'] and t.parent==a.parent)
# Independent inventory comparisons distinguish GLB label tessellation and intentionally excluded proxies.
for asset in inv['assets']:
    for p in asset['parts']:
        n=p['scene_object'];o=O.get(n)
        if mode=='glb' and p['type']=='FONT':o=O.get(n+'.portable')
        if mode=='glb' and n.startswith('COLLISION.'):
            check(n+'_not_exported',o is None);continue
        check(n+'_inventory_object',o is not None)
        if o is None:continue
        check(n+'_inventory_owner',o.parent is not None and o.parent.name==asset['root'])
        check(n+'_inventory_translation',near(tuple(o.matrix_world.translation),p['translation_m']))
        # Evaluated bevels/text tessellation may change rendered extents; compare original native dimensions strictly.
        if mode=='native':check(n+'_inventory_dimensions',near(tuple(o.dimensions),p['dimensions_m']))
for c in aff['candidate_contacts']:
    o=O.get(c['scene_object']);check(c['scene_object']+'_contact_transform',o is not None and near(tuple(o.matrix_world.translation),c['translation_m']))
    if o:check(c['scene_object']+'_not_qualified',not o.get('qualified_grasp',True) and not c['physical_grasp_enabled'] and c['qualified_pose'] is None)
for e in aff['exclusion_regions']:
    o=O.get(e['scene_object']);check(e['scene_object']+'_contact_excluded',o is not None and bool(o.get('contact_excluded')) and not e['robot_contact_allowed'])
# Surface topology and actual rays are checked on saved geometry, not on constructor parameters.
report['observations']['copper']={}
for ch in 'ECNU':
    o=O.get('copper.'+ch+'.mask');lo,hi=bounds(o);ext=[hi[i]-lo[i] for i in range(3)]
    vertices=world_vertices(o);tree=BVHTree.FromPolygons(vertices,[list(p.vertices) for p in o.data.polygons],all_triangles=False)
    center=o.matrix_world.translation
    def solid(x,z):return tree.ray_cast(Vector((center.x+x,lo[1]-.02,center.z+z)),Vector((0,1,0)),.05)[0] is not None
    # Geometry-independent low-resolution transmission map (31 x 33 samples inside plate footprint).
    bitmap=[''.join('#' if solid((i-15)*.0048,(j-16)*.0048) else '.' for i in range(31)) for j in reversed(range(33))]
    rays=sum(row.count('.') for row in bitmap);bm=bmesh.new();bm.from_mesh(o.data)
    indexed_manifold=sum(not e.is_manifold for e in bm.edges)==0
    if mode=='glb':bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7) # Only temporary audit mesh: glTF duplicates hard-edge normals.
    manifold=sum(not e.is_manifold for e in bm.edges)==0;vol=abs(bm.calc_volume(signed=True))*abs(o.matrix_world.to_3x3().determinant());bm.free()
    check('copper_'+ch+'_actual_dimensions',near(ext,(.16,.0015,.165)))
    check('copper_'+ch+'_closed_manifold',manifold)
    check('copper_'+ch+'_real_aperture_rays',rays>20 and solid(.07,.07) and solid(-.07,-.07))
    check('copper_'+ch+'_positive_removed_volume',0<vol<.16*.0015*.165*.9)
    report['observations']['copper'][ch]={'world_extent_m':ext,'volume_m3':vol,'non_solid_rays_of_1023':rays,'transmission_map_solid_hash_hole_dot':bitmap,'closed_manifold_after_export_normal_weld':manifold,'original_indexed_mesh_manifold':indexed_manifold}
si=O.get('silicon.wafer');lo,hi=bounds(si);ext=[hi[i]-lo[i] for i in range(3)]
check('silicon_real_source_200um_thickness',abs(ext[1]-.0002)<2e-7,ext)
check('silicon_authored_160mm_diameter',near((ext[0],ext[2]),(.16,.16)))
report['observations']['silicon_extent_m']=ext
check('silicon_mark_separate_surface',O.get('silicon.star_mark') is not None and O.get('silicon.star_mark').parent==si.parent and O.get('silicon.star_mark').get('contact_excluded'))
# Dock remains unoccupied by all authored physical samples.
dock=O.get('optics.load_dock');sample_objects=[O['copper.'+c+'.mask'] for c in 'ECNU']+[si]
dlo,dhi=bounds(dock);region=([dlo[0],dlo[1],dhi[2]],[dhi[0],dhi[1],dhi[2]+.30])
intersect=[]
for o in sample_objects:
    lo,hi=bounds(o)
    if all(lo[i]<region[1][i] and hi[i]>region[0][i] for i in range(3)):intersect.append(o.name)
check('empty_optics_dock_no_sample_intersection',not intersect,intersect)
check('A13_spatial_service_distinct_from_A06',all(O.get(n) is not None and O[n].parent.name=='ASSET.A13' for n in ['diagnostic.spatial_sensor_shell','diagnostic.capped_spatial_aperture','diagnostic.map_transfer_port','diagnostic.registration_port']) and all(O[n].parent.name=='ASSET.A06' for n in ['instruments.analog.shell','instruments.photon.shell']))
# Inspect potentially active scene payloads and file dependencies.
check('no_embedded_script_texts',len(bpy.data.texts)==0)
check('no_external_libraries',len(bpy.data.libraries)==0)
check('no_texture_images',all(x.type in {'RENDER_RESULT','COMPOSITING'} and not x.filepath for x in bpy.data.images),[{'name':x.name,'type':x.type,'filepath':x.filepath} for x in bpy.data.images])
check('no_actions_or_animation_data',len(bpy.data.actions)==0 and all(not o.animation_data for o in O))
check('no_rigid_body_world',all(not s.rigidbody_world for s in bpy.data.scenes))
check('no_physics_modifiers',not [(o.name,m.type) for o in O for m in o.modifiers if m.type in {'CLOTH','SOFT_BODY','FLUID','PARTICLE_SYSTEM','DYNAMIC_PAINT','NODES'}])
check('no_object_rigid_bodies_or_constraints',all(not o.rigid_body and not o.rigid_body_constraint and not o.constraints for o in O))
check('no_movie_sound_cache_files',len(bpy.data.movieclips)==0 and len(bpy.data.sounds)==0 and len(bpy.data.cache_files)==0)
if mode=='native':
    check('metric_native_units',S.unit_settings.system=='METRIC' and S.unit_settings.scale_length==1)
    check('all_collision_proxies_hidden_disabled',all(O[p['scene_object']].hide_render and not O[p['scene_object']].get('collision_enabled',True) for p in aff['collision_proxies']))
    report['observations']['native_render']={'engine':S.render.engine,'device':S.cycles.device,'samples':S.cycles.samples,'resolution':[S.render.resolution_x,S.render.resolution_y],'cameras':[x.name for x in O if x.type=='CAMERA'],'render_path':S.render.filepath}
report['observations']['object_counts']={t:sum(o.type==t for o in O) for t in sorted({o.type for o in O})}
report['observations']['checked_sha256']={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['geometry/midinfrared_lab.'+('blend' if mode=='native' else 'glb'),'asset_inventory.json','affordances.json','operation_binding_contract.json']}
report['status']='PASS' if not report['errors'] else 'FAIL'
out=P/'review'/('independent_'+mode+'_geometry.json');out.write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT_AUDIT',mode,report['status'],len(report['checks']),'checks',len(report['errors']),'errors',out)
for e in report['errors']:print('AUDIT_ERROR',e)
if report['errors']:sys.exit(1)
