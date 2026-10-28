"""Check real starting stock, reservations and integrated cover configurations."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_stock_cutplan import load_parts
from check_apparatus_frame import solid, intersection_mm3


def build():
    record=json.loads((HERE/'cover_stock.json').read_text());apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    template=load_parts(record['template_geometry']['path']);checks=[];cuts=[];integrations=[]
    def check(name,value,**details):
        checks.append(dict(name=name,passed=bool(value),**details))
        if not value:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']+apparatus['source_artifacts']+[record['template_geometry']]:
        check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    items={i['id']:i for i in record['items']};stock={k:load_parts(i['geometry']['path']) for k,i in items.items()}
    for identity,item in items.items():
        parts=stock[identity];used=[]
        check('geometry_'+identity,sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'])
        for unit in item['units']:
            check('unique_actual_unit_'+unit['id'],bool(unit['parts']) and not set(used)&set(unit['parts']) and set(unit['parts'])<=parts.keys());used+=unit['parts']
        check('all_parts_accounted_'+identity,set(used)==set(parts))
        for name,m in parts.items():check('closed_positive_'+identity+'/'+name,solid(m).is_volume)
        for a,b in itertools.combinations(parts,2):
            if np.any(np.minimum(parts[a].bounds[1],parts[b].bounds[1])-np.maximum(parts[a].bounds[0],parts[b].bounds[0])<=1e-8):continue
            check('stock_not_interpenetrating_'+identity+'/'+a+'/'+b,intersection_mm3(parts[a],parts[b])<.001)
    angle=stock['cover_angle_stock']['raw_angle_250mm'];intervals=[]
    check('supplier_angle_real_section',np.allclose(angle.extents,[.250,.0127,.0127],atol=1e-8) and abs(angle.volume/.250-(2*.0127*.0015875-.0015875**2))<1e-10)
    for cut in items['cover_angle_stock']['cuts']:
        m=template[cut['source_part']].copy();m.apply_transform(cut['stock_from_template'])
        outside=float(trimesh.boolean.difference([solid(m),solid(angle)],engine='manifold').volume*1e9)
        check('actual_finished_angle_inside_stock_'+cut['id'],np.isfinite(outside) and abs(outside)<.001,outside_mm3=outside)
        interval=cut['stock_axis_interval_m'];check('real_cut_length_'+cut['id'],abs(m.extents[0]-.010)<2e-7 and np.allclose(m.bounds[:,0],interval,atol=2e-7))
        intervals.append(interval);cuts.append(dict(id=cut['id'],outside_stock_mm3=outside))
    check('six_distinct_angle_reservations',len(intervals)==6 and all(b[0]-a[1]>=.001-1e-8 for a,b in zip(sorted(intervals),sorted(intervals)[1:])))
    shortened=angle.copy();shortened.vertices[:,0]*=.2
    check('negative_short_angle_cannot_supply_reservations',max(v[1] for v in intervals)-min(v[0] for v in intervals)>shortened.extents[0])
    units=items['cover_mount_hardware']['units']
    check('twelve_screws_six_washers',sum(u['kind']=='M3x6_cap_screw' for u in units)==12 and sum(u['kind']=='M3_large_washer' for u in units)==6)
    for u in units:
        m=stock['cover_mount_hardware'][u['id']];original=template[u['source_part']]
        check('original_hardware_shape_'+u['id'],abs(m.volume-original.volume)<1e-11 and np.allclose(np.linalg.eigvalsh(m.moment_inertia),np.linalg.eigvalsh(original.moment_inertia),atol=1e-14))
        check('hardware_rests_on_support_'+u['id'],abs(m.bounds[0,2])<1e-8)
    reserved=items['cover_adhesive_stock']['reservations'];seen=set()
    for r in reserved:
        m=stock['cover_adhesive_stock'][r['raw_part']]
        check('one_new_sheet_per_attachment_'+r['id'],r['stock_unit'] not in seen);seen.add(r['stock_unit'])
        check('annulus_and_cut_margin_fit_'+r['id'],min(m.extents[:2])>=r['outer_diameter_m']+.002 and abs(m.extents[2]-r['finished_gauge_m'])<1e-8)
        check('typical_liner_gauge_'+r['id'],abs(stock['cover_adhesive_stock'][r['raw_part'].replace('adhesive','liner')].extents[2]-.000102)<1e-8)
    check('initial_fixed_restore_adhesive_count',len(reserved)==12 and sum(r['location']=='aperture' for r in reserved)==2 and sum(r['stage']=='RESTORE_TRACKED' for r in reserved)==2)
    check('negative_140mm_raw_sheet_cannot_make_aperture_bond',any(r['outer_diameter_m']+.002>.140 for r in reserved))
    rejected=json.loads((HERE/'cover_export_rejected.json').read_text())
    check('retained_export_failure_pinned',sha(ROOT/rejected['geometry']['path'])==rejected['geometry']['sha256'])
    bad=load_parts(rejected['geometry']['path']);a,b=rejected['parts'];manager=trimesh.collision.CollisionManager();manager.add_object(a,bad[a])
    check('negative_world_baked_float32_export_intersects',manager.in_collision_single(bad[b]))
    # Independently inspect the exported configuration meshes, not just the
    # isolated template or generator parameters.
    for item in apparatus['items']:
        identity=item['id'];cover=item['cover'];prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[identity]
        p=load_parts(item['geometry']['path']);names=cover['rebuilt_parts']+cover['added_parts'];local={n.removeprefix(prefix):p[n].copy() for n in names}
        exported=trimesh.load(ROOT/item['geometry']['path'],force='scene')
        transform,key=exported.graph[prefix+'foam_mylar_1']
        check('thin_geometry_keeps_local_vertex_precision_'+identity,np.max(abs(exported.geometry[key].vertices[:,0]))<.03 and np.allclose(transform[:3,3],cover['translation_m'],atol=1e-10))
        for m in local.values():m.apply_translation(-np.array(cover['translation_m']))
        check('complete_cover_configuration_'+identity,len(local)==29 and len(cover['added_parts'])==15)
        expected=.000050 if identity=='cooler_fixed' else .000016
        check('actual_film_gauge_'+identity,abs(local['cover_upper'].extents[2]-expected)<1e-8)
        check('actual_pe_height_'+identity,abs(local['PE_support'].extents[2]-.051)<1e-8)
        check('platform_supports_shield_'+identity,abs(local['lift_plate'].bounds[1,2]-local['radiation_shield'].bounds[0,2])<1e-8)
        check('physical_cover_parts_declared_'+identity,set(local)==(set(template)-{'emitter_white_coating'}|{'emitter_black_coating'} if identity=='cooler_black' else set(template)))
        for n,m in local.items():
            check('integrated_closed_solid_'+identity+'/'+n,solid(m).is_volume)
            if n in ['cover_lower','cover_upper']:continue
            source_name='emitter_white_coating' if n=='emitter_black_coating' else n
            check('template_shape_preserved_'+identity+'/'+n,np.array_equal(m.faces,template[source_name].faces) and np.max(abs(m.vertices-template[source_name].vertices))<2e-7)
        # The lower film has a sloped region; use actual surface-normal gauge.
        gauges=[];m=local['cover_lower']
        for radius in [.015,.052,.060]:
            theta=np.pi/256;origin=[radius*np.cos(theta),radius*np.sin(theta),.045]
            hits,_,faces=m.ray.intersects_location([origin],[[0,0,1]])
            check('two_lower_film_faces_'+identity+'/'+str(radius),len(hits)==2)
            i=np.argmin(hits[:,2]);hit=hits[i];direction=-m.face_normals[faces[i]]
            across,_,_=m.ray.intersects_location([hit-direction*.000010],[direction]);distance=np.sort((across-hit)@direction)
            gauge=float(np.ptp(distance))
            check('lower_film_normal_gauge_'+identity+'/'+str(radius),len(distance)==2 and abs(gauge-expected)<3e-7,actual_m=gauge);gauges.append(gauge)
        integrations.append(dict(id=identity,actual_lower_normal_gauges_m=gauges,physical_installation_qualified=False))
    report=dict(passed=True,checks=checks,stock_units=record['stock_units'],angle_cut_containment=cuts,configurations=integrations,
        scene_access_qualified=False,physical_installation_qualified=False,owner_acceptance=None,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'cover_stock.json',HERE/'apparatus_stock_reconciliation.json',HERE/'check_apparatus_frame.py',HERE/'cover_export_rejected.json']],
        limits=['Static exported stock and configuration geometry only; no material, assembly, adhesion, tool or robot execution acceptance'])
    write_json(HERE/'cover_stock_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),stock_units=record['stock_units'],configurations=len(integrations))))


if __name__=='__main__':build()
