"""Check the exported ordinary tool, real drive cavity and full-tool space."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def cylinder_x(radius,start,end):
    # Circumscription encloses the ideal circular turning envelope between
    # angular samples, rather than slightly underestimating it with chords.
    n=192
    m=trimesh.creation.cylinder(radius/np.cos(np.pi/n),end-start,sections=n)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]))
    m.apply_translation([(start+end)/2,0,0]);return m


def build():
    record=json.loads((HERE/'nut_driver_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(record['geometry']);physical={n:m for n,m in parts.items() if n!='size_text'}
    check('three_solids_and_one_size_label',len(physical)==3 and len(parts)==4)
    for n,m in physical.items():check('closed_connected_'+n,m.is_volume and len(m.split())==1)
    pairs=[dict(parts=[a,b],overlap_mm3=overlap(x,y)) for (a,x),(b,y) in itertools.combinations(physical.items(),2)]
    check('distinct_material_domains',all(np.isfinite(p['overlap_mm3']) and abs(p['overlap_mm3'])<.001 for p in pairs),pairs=pairs)
    steel=physical['steel_shaft_and_blind_socket'];core=physical['red_molded_core'];grip=physical['black_soft_grip']
    check('source_blade_and_overall_lengths',abs(core.bounds[0,0]-.125)<1e-7 and abs(core.bounds[1,0]-.238)<1e-7 and abs(steel.bounds[0,0])<1e-7)
    diameter=2*np.max(np.linalg.norm(grip.vertices[:,1:],axis=1))
    check('source_maximum_grip_diameter',abs(diameter-.036)<3e-5,actual_m=float(diameter),datum='Maximum radial diameter across rounded corners, not width across flats.')
    diameter=2*np.max(np.linalg.norm(steel.vertices[:,1:],axis=1))
    check('source_metric_socket_outer_diameter',abs(diameter-.01035)<3e-5,actual_m=float(diameter))
    # The hex flat normals are at 0, 60, ... degrees in this exported frame.
    angles=np.arange(6)*np.pi/3
    def probes(radius,x=.001):return np.column_stack([np.full(6,x),radius*np.cos(angles),radius*np.sin(angles)])
    check('actual_hex_flats_and_selected_clearance',not steel.contains(probes(.00353)).any() and steel.contains(probes(.00355)).all())
    check('blind_socket_depth',not steel.contains([[.0189,0,0]])[0] and steel.contains([[.0191,0,0]])[0])
    check('real_entrance_chamfer',not steel.contains(probes(.00363,.0001)).any() and steel.contains(probes(.00363,.001)).all())
    section=steel.section(plane_normal=[1,0,0],plane_origin=[.0001,0,0])
    mouth=min((Polygon(loop[:,1:]) for loop in section.discrete),key=lambda p:p.area).simplify(1e-7)
    check('aligned_six_sided_chamfer',mouth.is_valid and len(mouth.exterior.coords)==7 and abs(mouth.area/mouth.convex_hull.area-1)<1e-5,
        scope='Rejects a differently clocked chamfer that cuts a star-shaped entrance into an otherwise correct blind hex bore.')
    check('solid_shaft_and_real_factory_seat',steel.contains([[.05,0,0],[.128,0,0]]).all() and not core.contains([[.128,0,0]])[0])
    clamp=json.loads((HERE/'hose_clamp_assets.json').read_text());fit=json.loads((HERE/'hose_clamp_checks.json').read_text())
    item=next(i for i in clamp['items'] if i['id']=='installed');axis_y=item['band_route']['housing_translation_m'][1]-.0045
    context=load_parts(fit['fit_geometry']);matrix=trimesh.transformations.rotation_matrix(np.pi,[0,0,1]);matrix[:3,3]=[-.0122,axis_y,0]
    placed={}
    for n,m in parts.items():placed[n]=m.copy();placed[n].apply_transform(matrix)
    hits=[]
    for n,m in placed.items():
        if n=='size_text':continue
        for q,b in context.items():
            v=overlap(m,b)
            if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],overlap_mm3=v))
    check('complete_tool_in_actual_RS3_clamp_context',not hits,intersections=hits)
    screw=context['slotted_hex_worm_screw'];head=screw.copy();head.apply_transform(np.linalg.inv(matrix))
    check('head_engagement_depth',abs(head.bounds[1,0]-.0028)<1e-7,depth_m=float(head.bounds[1,0]),flange_gap_m=.0002)
    wrong=placed['steel_shaft_and_blind_socket'].copy();wrong.apply_transform(trimesh.transformations.rotation_matrix(np.pi/6,[1,0,0],point=matrix[:3,3]))
    check('negative_wrong_hex_clocking_rejected',overlap(wrong,screw)>.01,overlap_mm3=overlap(wrong,screw))
    filled=cylinder_x(.005175,0,.019);filled.apply_transform(matrix)
    check('negative_filled_socket_rejected',overlap(filled,screw)>1,overlap_mm3=overlap(filled,screw))
    # A filled outer envelope deliberately excludes the driven screw. It
    # bounds every tool angle and 100 mm straight withdrawal continuously.
    # No thread movement or contact-based execution is inferred from this.
    worst=record['alternative_literal_inch_socket_diameter_m']/2
    envelopes=[('socket',worst,0,.032),('shaft',.00275,.032,.125),('grip',.018,.125,.238)]
    sweep_hits=[]
    for name,r,start,end in envelopes:
        m=cylinder_x(r,start,end+.100);m.apply_transform(matrix)
        for q,b in context.items():
            if q=='slotted_hex_worm_screw':continue
            v=overlap(m,b)
            if not np.isfinite(v) or abs(v)>.001:sweep_hits.append(dict(envelope=name,part=q,overlap_mm3=v))
    check('whole_tool_turn_and_100mm_withdrawal_envelope',not sweep_hits,intersections=sweep_hits,
        source_conflict_outer_diameter_m=2*worst,excluded_part='slotted_hex_worm_screw',
        scope='Circumscribed rigid tool envelopes against fixed context. Does not move the worm, band, robot or flexible parts.')
    blocked=cylinder_x(.019,.125,.238);blocked.apply_transform(matrix)
    check('negative_obstruction_in_grip_space_rejected',overlap(placed['black_soft_grip'],blocked)>1)
    check('no_unearned_qualification',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','torque_qualified','robot_use_qualified','owner_acceptance']))
    g=Geometry()
    for n,m in {**context,**{'tool_'+n:m for n,m in placed.items()}}.items():
        g.scene.add_geometry(m,node_name=n,geom_name=n);g.parts.append(dict(id=n,role='static_interface_inspection',bounds_m=m.bounds.tolist()))
    # Imported glTF materials are already linear. Avoid a second conversion.
    fixture=g.export('wiha_34123_rs3_clamp_fit')
    refs=[Path(__file__),HERE/'nut_driver_assets.json',HERE/'hose_clamp_assets.json',HERE/'hose_clamp_checks.json',HERE/'check_weather_assets.py']
    report=dict(schema_version=1,passed=True,checks=checks,fit_geometry=fixture,tool_transform=matrix.tolist(),
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_conflict_retained=True,rigid_envelope_withdrawal_m=.1,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Full-tool geometry and continuous conservative space bounds only; no robot hand, controller, worm-drive contact, torque or assembly qualification.',
            'Original RS3 body and prior static clamp fit are reused; existing rod/nut thread-envelope overlaps remain declared in the weather report.',
            'Socket depth, local profile, drive clearance and handle construction details remain explicitly inferred. No added inventory.'])
    write_json(HERE/'nut_driver_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),fixture_parts=fixture['parts'])))


if __name__=='__main__':build()
