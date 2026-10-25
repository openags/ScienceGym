"""Inspect the actual jack/base/platform/fastener meshes and preserve limits."""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json, imported_scene
from build_stock_cutplan import load_parts


def build():
    data=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    source=json.loads((ROOT/'assets/thorlabs_l200_v1/model.json').read_text())
    jack=load_parts(source['geometry']['path']);checks=[];items=[]
    def check(name,value,**details):
        checks.append(dict(name=name,passed=bool(value),**details))
        if not value:raise AssertionError(name+' '+str(details))
    for s in data['source_artifacts']:
        check('source_'+s['path'],sha(ROOT/s['path'])==s['sha256'])
    for item in data['items']:
        identity=item['id'];prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[identity]
        geometry=item['geometry'];mount=item['mounting'];parts=load_parts(geometry['path'])
        check('geometry_'+identity,sha(ROOT/geometry['path'])==geometry['sha256'])
        check('legacy_lift_and_unconnected_probes_removed_'+identity,not any(n.startswith(prefix+'sensor_lead_') or n.startswith(prefix+'probe_contact_') or n in [prefix+'lift_thread',prefix+'lift_foot'] for n in parts))
        names=[n for n in parts if n.startswith(prefix+'L200_M__')]
        check('all_source_jack_solids_'+identity,len(names)==86)
        for name in names:
            m=parts[name];original=jack[name.removeprefix(prefix)]
            expected=(original.vertices+mount['jack_translation_m']).astype(np.float32)
            check('unchanged_source_geometry_'+name,np.array_equal(m.faces,original.faces) and np.max(abs(m.vertices-expected))<2e-7)
        base,foil,platform=[parts[prefix+n] for n in ['acrylic_base','mylar_base','lift_plate']]
        lower,upper=[parts[prefix+f'L200_M__solid_{i:03d}'] for i in [1,0]]
        check('base_foil_jack_platform_contact_planes_'+identity,
              abs(base.bounds[1,2]-foil.bounds[0,2])<2e-7 and abs(foil.bounds[1,2]-lower.bounds[0,2])<2e-7 and abs(upper.bounds[1,2]-platform.bounds[0,2])<2e-7)
        check('platform_still_170x170x5_'+identity,np.allclose(platform.extents,[.17,.17,.005],atol=2e-7))
        check('foam_supported_by_new_platform_'+identity,abs(parts[prefix+'foam_1'].bounds[0,2]-platform.bounds[1,2])<2e-7)
        original=imported_scene('assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb',prefix=prefix)
        if prefix+'solar_reflector' in parts:
            gap=parts[prefix+'solar_reflector'].bounds.mean(axis=0)[2]-parts[prefix+'emitter_copper'].bounds[1,2]
            old_gap=original.geometry[prefix+'solar_reflector'].bounds.mean(axis=0)[2]-original.geometry[prefix+'emitter_copper'].bounds[1,2]
            check('reflector_emitter_relative_height_preserved_'+identity,abs(gap-old_gap)<2e-7)
        for face in [base,foil,platform]:
            flat=np.abs(face.face_normals[:,2])>.99999
            dots=np.einsum('fvi,fi->fv',face.vertex_normals[face.faces[flat]],face.face_normals[flat])
            check('flat_plate_render_normals_'+identity+'_'+str(round(face.extents[2],6)),np.min(dots)>.999)
            mesh=face.copy();mesh.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=8)
            check('closed_new_plate_'+identity+'_'+str(round(face.extents[2],6)),mesh.is_watertight)
        interfaces=[]
        for f in mount['interfaces']:
            xy=np.array(f['center_xy_m']);screw=parts[f['bottom_screw']];top=parts[f['top_screw']];washer=parts[f['bottom_washer']]
            origin=[*xy,.5]
            check('open_actual_mount_holes_'+identity+'_'+f['id'],all(not m.ray.intersects_any([origin],[[0,0,-1]])[0] for m in [base,foil,platform,washer]))
            check('top_countersink_has_recess_and_shank_land_'+identity+'_'+f['id'],not platform.contains([[xy[0]+.003,xy[1],platform.bounds[1,2]-.0001]])[0] and platform.contains([[xy[0]+.0023,xy[1],platform.bounds[0,2]+.0002]])[0])
            check('nominal_bottom_stack_'+identity+'_'+f['id'],abs(washer.bounds[1,2]-base.bounds[0,2])<2e-7 and abs(screw.bounds[0,2]+.003-washer.bounds[0,2])<2e-7 and abs(screw.bounds[1,2]-lower.bounds[0,2]-.003188)<2e-7)
            check('top_head_flush_and_three_mm_insertion_'+identity+'_'+f['id'],abs(top.bounds[1,2]-platform.bounds[1,2])<2e-7 and abs(upper.bounds[1,2]-top.bounds[0,2]-.003)<2e-7)
            # Probe adjacent plate material from its real mesh. Source M3
            # bores are unthreaded envelopes, not a helix engagement model.
            thickness=[]
            for plate in [lower,upper]:
                hits,_,_=plate.ray.intersects_location([[xy[0]+.00155,xy[1],.5]],[[0,0,-1]])
                thickness.append(float(np.ptp(hits[:,2])))
            check('tips_stay_within_source_plate_depth_'+identity+'_'+f['id'],all(abs(t-.005588)<2e-7 for t in thickness) and f['bottom_engagement_m']<thickness[0] and f['top_engagement_m']<thickness[1])
            interfaces.append(dict(id=f['id'],actual_adjacent_plate_thickness_m=thickness,bottom_engagement_m=f['bottom_engagement_m'],top_engagement_m=f['top_engagement_m']))
        items.append(dict(id=identity,interfaces=interfaces,nominal_mounting_geometry_consistent=True,load_and_thread_qualification=False))
    # Full triangle test on one rigidly repeated mounting: only the declared
    # source plate's nominal thread envelope may meet each screw. Preserve the
    # observed faceting overlap instead of describing these as force contacts.
    first=data['items'][0];prefix='COOLER_WHITE__';parts=load_parts(first['geometry']['path']);manager=trimesh.collision.CollisionManager()
    for n,m in parts.items():
        if n.startswith(prefix+'L200_M__'):manager.add_object(n,m)
    encounters=[]
    for f in first['mounting']['interfaces']:
        for role,plate in [('bottom_screw',1),('top_screw',0)]:
            collision,names,contacts=manager.in_collision_single(parts[f[role]],return_names=True,return_data=True)
            expected=prefix+f'L200_M__solid_{plate:03d}'
            check('no_nonmating_jack_intersection_'+role+'_'+f['id'],names<={expected})
            encounters.append(dict(screw=f[role],nominal_thread_plate=expected,intersecting_parts=sorted(names),maximum_mesh_depth_m=max((c.depth for c in contacts),default=0),qualification=False))
    old=imported_scene('assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb',prefix=prefix)
    gap=old.geometry[prefix+'lift_foot'].bounds[0,2]-(old.geometry[prefix+'acrylic_base'].bounds[1,2]+.000012)
    check('negative_legacy_foot_has_air_gap',gap>.0009,measured_gap_m=float(gap))
    bad=parts[prefix+'L200_M__solid_001'].copy();bad.apply_translation([0,0,.001])
    check('negative_lifted_base_loses_contact',abs(bad.bounds[0,2]-parts[prefix+'mylar_base'].bounds[1,2])>.0009)
    # Stock counts and real usable drives, independent of arrangement metadata.
    stock=json.loads((HERE/'lift_mount_stock.json').read_text());raw=load_parts(stock['geometry']['path'])
    check('twenty_four_separate_mounting_pieces',len(raw)==len(stock['units'])==24 and all(sum(u['kind']==kind for u in stock['units'])==8 for kind in ['cap_m3x10','csk_m3x8','washer_m3']))
    for name,mesh in raw.items():
        center=mesh.bounds.mean(axis=0);z=mesh.bounds[0,2]
        if name.startswith('washer'):
            check('stock_washer_has_open_bore_'+name,not mesh.contains([[*center[:2],z+.0004]])[0])
        else:
            check('stock_screw_has_real_drive_'+name,not mesh.contains([[*center[:2],z+.0006]])[0] and mesh.contains([[center[0]+.0024,center[1],z+.0003]])[0])
    report=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,items=items,thread_envelope_encounters=encounters,
                scope='Static source-scale central mounting and stock only; no thread force, structural load, tool motion or assembly qualification',
                tool_access_conditions=['Upper screw drives require the overlying thermal stack to be absent','Underside drives require an underside-accessible supported assembly state; the final bench pose does not supply tool clearance'],
                remaining=['Frame-to-base and upright/track connections','Film/shield support and retention','Physical thread, preload, acrylic stress and load qualification','Ordinary driver and fabrication-tool stock','Probe and cable installation'],
                owner_acceptance=None,physical_installation_qualified=False,
                source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'apparatus_stock_reconciliation.json',HERE/'lift_mount_stock.json',HERE/'apparatus_mount_sources.json',ROOT/'assets/thorlabs_l200_v1/model.json']])
    write_json(HERE/'apparatus_mount_checks.json',report)
    print(json.dumps(dict(passed=report['passed'],checks=len(checks),configurations=len(items),mount_stock_units=len(raw))))


if __name__=='__main__':build()
