"""Inspect exported frame solids, real holes, connections and retained failures."""
import json
import warnings
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_stock_cutplan import load_parts


def solid(m):
    m=m.copy();m.merge_vertices(merge_tex=True,merge_norm=True,digits_vertex=8)
    return m


def intersection_mm3(a,b):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        value=float(trimesh.boolean.intersection([solid(a),solid(b)],engine='manifold').volume*1e9)
    if not np.isfinite(value):raise ValueError('Non-finite solid intersection volume')
    return max(0.,value)


def build():
    record=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    checks=[];rows=[];intersections=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:
        check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for item in record['items']:
        identity=item['id'];prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[identity]
        p=load_parts(item['geometry']['path']);frame=item['frame'];names=frame['review_parts']
        check('artifact_'+identity,sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'])
        check('legacy_frame_removed_'+identity,not set(frame['removed_legacy_parts'])&p.keys())
        for n in names:
            check('closed_solid_'+n,solid(p[n]).is_watertight and solid(p[n]).is_winding_consistent and solid(p[n]).volume>0)
        center=p[prefix+'acrylic_base'].bounds.mean(axis=0)[:2]
        local={n.removeprefix(prefix):m.copy() for n,m in p.items()}
        for m in local.values():m.apply_translation([-center[0],-center[1],0])
        rail=local['frame_rail_right'];rail_center=rail.bounds.mean(axis=0)
        area=solid(rail).volume/.340*1e6
        check('real_20mm_rail_and_340mm_length_'+identity,np.allclose(rail.extents,[.020,.340,.020],atol=2e-7))
        check('independent_catalog_area_comparison_'+identity,abs(area-159.1)/159.1<.02,area_mm2=area,relative_difference=(area-159.1)/159.1)
        check('open_through_core_'+identity,not rail.ray.intersects_any([[*rail_center[:1],-.3,rail_center[2]]],[[0,1,0]])[0])
        for dx,dz in [(0,9),(0,-9),(9,0),(-9,0)]:
            check(f'open_real_slot_{identity}_{dx}_{dz}',not rail.contains([[rail_center[0]+dx*.001,0,rail_center[2]+dz*.001]])[0])
        left=local['frame_rail_left'];base=local['acrylic_base'];foil=local['mylar_base']
        check('paper_inner_span_and_base_below_rail_tops_'+identity,abs(rail.bounds[0,0]-left.bounds[1,0]-.305)<2e-7 and abs(base.bounds[0,2]-rail.bounds[0,2])<2e-7 and base.bounds[1,2]<rail.bounds[1,2])
        for j in frame['joints']:
            key=j['id']
            if key.startswith('frame_bridge'):
                x,y,_=np.asarray(j['panel_hole_xyz_mm'])*.001
                check('panel_clearance_holes_'+identity+'_'+key,all(not local[n].ray.intersects_any([[x,y,.5]],[[0,0,-1]])[0] for n in ['acrylic_base','mylar_base',key,key+'_washer',key+'_nut']))
                check('plate_bears_on_base_'+identity+'_'+key,abs(local[key].bounds[1,2]-base.bounds[0,2])<2e-7)
                check('washer_nut_stack_'+identity+'_'+key,abs(local[key+'_washer'].bounds[0,2]-foil.bounds[1,2])<2e-7 and abs(local[key+'_nut'].bounds[0,2]-local[key+'_washer'].bounds[1,2])<2e-7)
                check('panel_tip_projects_past_nut_'+identity+'_'+key,abs(local[key+'_panel_screw'].bounds[1,2]-local[key+'_nut'].bounds[1,2]-.001188)<2e-7)
            elif key.startswith('upright_'):
                side=key.removeprefix('upright_');tube=local['frame_tube_'+side]
                cap=local['frame_upper_clamp_'+side];axis=tube.bounds.mean(axis=0)[:2]
                check('tube_outboard_of_rails_'+identity+'_'+side,abs(axis[0])-.010>.1725)
                check('tube_20_14_and_real_bore_'+identity+'_'+side,np.allclose(tube.extents[:2],[.020,.020],atol=2e-7) and not tube.contains([[*axis,tube.bounds.mean(axis=0)[2]]])[0])
                check('upper_cap_shoulder_supported_by_tube_end_'+identity+'_'+side,abs(tube.bounds[1,2]-cap.bounds[0,2]-.017)<2e-7 and cap.contains([[*axis,tube.bounds[1,2]+.001]])[0])
                check('track_bears_on_upper_cap_'+identity+'_'+side,abs(cap.bounds[1,2]-local['fixed_reflector_band' if identity=='cooler_fixed' else 'reflector_track'].bounds[0,2])<2e-7)
                check('negative_lifted_cap_loses_shoulder_contact_'+identity+'_'+side,abs(tube.bounds[1,2]-(cap.bounds[0,2]+.001)-.017)>.0009)
            else:
                check('reflector_bears_on_backing_plate_'+identity,abs(local['solar_reflector'].bounds[0,2]-local['frame_carriage_upper'].bounds[1,2])<2e-7)
                check('track_captured_between_separate_plates_'+identity,abs(local['frame_carriage_lower'].bounds[1,2]-local['reflector_track'].bounds[0,2])<2e-7 and abs(local['frame_carriage_upper'].bounds[0,2]-local['reflector_track'].bounds[1,2])<2e-7)
        feet=[m for n,m in local.items() if n.startswith('frame_bumper_')]
        check('feet_support_base_clear_of_screw_heads_'+identity,len(feet)==4 and all(abs(m.bounds[1,2]-base.bounds[0,2])<2e-7 for m in feet) and min(m.bounds[0,2] for n,m in local.items() if n.startswith('frame_') and 'bumper' not in n)>min(m.bounds[0,2] for m in feet)+.003)
        rows.append(dict(id=identity,frame_parts=len(names),nominal_geometry_consistent=True,physical_installation_qualified=False))
        # Coplanar FCL contacts can have large reported depth. Evaluate actual
        # solid intersection volumes, and identify nominal thread/seat pairs
        # explicitly instead of treating FCL depth as elastic penetration.
        manager=trimesh.collision.CollisionManager()
        for n in names:manager.add_object(n,p[n])
        _,pairs=manager.in_collision_internal(return_names=True)
        for a,b in sorted(pairs):
            volume=intersection_mm3(p[a],p[b]);aa=a.removeprefix(prefix);bb=b.removeprefix(prefix)
            is_screw=lambda n:'screw' in n or 'pinch' in n
            mating=(is_screw(aa) and any(t in bb for t in ['tnut','_nut','clamp','carriage','solar_reflector'])) or (is_screw(bb) and any(t in aa for t in ['tnut','_nut','clamp','carriage','solar_reflector']))
            # Allow <=0.05 mm3 only for declared smooth thread/countersink
            # envelope faceting. Other solid pairs have a 0.001 mm3 numerical
            # export allowance, neither an assembly nor force tolerance.
            check('solid_pair_'+identity+'_'+aa+'__'+bb,volume<(.05 if mating else .001),intersection_mm3=volume,nominal_thread_or_seat=mating)
            if volume>.0001:intersections.append(dict(configuration=identity,parts=[a,b],volume_mm3=volume,nominal_thread_or_seat=mating,physical_contact_qualified=False))
    bad=json.loads((HERE/'frame_sharp_tnut_rejected.json').read_text());check('rejected_mesh_pinned',sha(ROOT/bad['geometry']['path'])==bad['geometry']['sha256'])
    p=load_parts(bad['geometry']['path']);bad_volume=intersection_mm3(*p.values())
    check('negative_sharp_tnut_cuts_diagonal_web',bad_volume>.02,intersection_mm3=bad_volume)
    report=dict(schema_version=1,passed=True,checks=checks,items=rows,section=dict(area_mm2=area,catalog_area_mm2=159.1,shape_and_strength_qualified=False),
        intersections=intersections,negative_sharp_tnut_intersection_mm3=bad_volume,physical_installation_qualified=False,owner_acceptance=None,
        scope='Exported nominal frame geometry only. No clamp deformation, thread force, tolerance, load, adhesion, robot assembly or complete travel qualification.',
        source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in [Path(__file__),HERE/'apparatus_stock_reconciliation.json',HERE/'apparatus_frame_sources.json',HERE/'frame_sharp_tnut_rejected.json']])
    write_json(HERE/'apparatus_frame_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),configurations=len(rows),nominal_thread_seat_intersections=len(intersections))))


if __name__=='__main__':build()
