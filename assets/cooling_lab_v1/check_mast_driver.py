"""Full ordinary-tool access to each U30 mounting nut, including counterexample."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_nut_driver import cylinder_x


def build():
    r=json.loads((HERE/'mast_driver_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(r['geometry']);p={n:m for n,m in parts.items() if n!='size_text'}
    check('three_physical_parts_and_label',len(p)==3 and len(parts)==4)
    for n,m in p.items():check('closed_connected_'+n,m.is_volume and len(m.split())==1)
    pairs=[dict(parts=[n,q],overlap_mm3=overlap(m,b)) for (n,m),(q,b) in itertools.combinations(p.items(),2)]
    check('distinct_tool_material_domains',all(np.isfinite(v['overlap_mm3']) and abs(v['overlap_mm3'])<.001 for v in pairs),pairs=pairs)
    steel=p['steel_shaft_and_blind_socket'];core=p['red_molded_core'];grip=p['black_soft_grip']
    check('catalogue_blade_and_overall',abs(core.bounds[0,0]-.125)<1e-7 and abs(core.bounds[1,0]-.246)<1e-7 and abs(steel.bounds[0,0])<1e-7)
    diameter=2*np.linalg.norm(grip.vertices[:,1:],axis=1).max()
    check('catalogue_maximum_grip_diameter',abs(diameter-.041)<3e-5,actual_m=float(diameter))
    check('selected_socket_and_solid_shaft_diameter',abs(2*np.linalg.norm(steel.vertices[:,1:],axis=1).max()-.0185)<3e-5 and steel.contains([[.050,.0037,0]])[0] and not steel.contains([[.050,.0038,0]])[0])
    a=np.arange(6)*np.pi/3
    def points(rad,x=.001):return np.column_stack([np.full(6,x),rad*np.cos(a),rad*np.sin(a)])
    check('real_AF1278_hex_bore',not steel.contains(points(.00638)).any() and steel.contains(points(.00640)).all())
    check('selected_blind_depth',not steel.contains([[.0253,0,0]])[0] and steel.contains([[.0255,0,0]])[0])
    section=steel.section(plane_normal=[1,0,0],plane_origin=[.0001,0,0]);mouth=min((Polygon(loop[:,1:]) for loop in section.discrete),key=lambda q:q.area).simplify(1e-7)
    check('six_sided_aligned_entrance',mouth.is_valid and len(mouth.exterior.coords)==7 and abs(mouth.area/mouth.convex_hull.area-1)<1e-5)
    u30=json.loads((HERE/'u30_assets.json').read_text());u30_checks=json.loads((HERE/'u30_checks.json').read_text())
    contexts={'closed':load_parts(u30['geometry']),'open':load_parts(u30_checks['fit_geometry'])}
    rotation=trimesh.transformations.rotation_matrix(-np.pi/2,[0,0,1])@trimesh.transformations.rotation_matrix(np.pi/6,[1,0,0])
    # The socket's invariant circular void bounds all hex clockings. It is
    # retained through the first 25.4 mm of the union of withdrawal poses,
    # so the fixed U-bolt rod is checked rather than silently excluded.
    socket=cylinder_x(.00925,0,.055)
    # Inscribe this cutter: enlarging the void would underestimate material.
    inner=trimesh.creation.cylinder(.00639,.0255,sections=192)
    inner.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));inner.apply_translation([.01265,0,0])
    socket=trimesh.boolean.difference([socket,inner],engine='manifold')
    envelopes={'socket':socket,'shaft':cylinder_x(.00375,.035,.145),'grip':cylinder_x(.0205,.125,.266)}
    tool_sections=[('socket',.00925,0,.035),('shaft',.00375,.035,.125),('grip',.0205,.125,.246)]
    fixtures=[];poses=[]
    for index,z in enumerate(u30['mounting']['u_bolt_axes_z_m'],1):
        for side,x in [('left',-.026162),('right',.026162)]:
            nut='mount_'+str(index)+'_nut_'+side;matrix=rotation.copy();matrix[:3,3]=[x,.1164,z];placed={}
            for n,m in parts.items():placed[n]=m.copy();placed[n].apply_transform(matrix)
            for state,context in contexts.items():
                hits=[];space_hits=[]
                for n,m in placed.items():
                    if n=='size_text':continue
                    for q,b in context.items():
                        if q.endswith('_text'):continue
                        v=overlap(m,b)
                        if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],overlap_mm3=v))
                check('whole_tool_fit_'+nut+'_'+state,not hits,intersections=hits)
                for n,m in envelopes.items():
                    moved=m.copy();moved.apply_transform(matrix)
                    for q,b in context.items():
                        if q==nut or q.endswith('_text'):continue
                        v=overlap(moved,b)
                        if not np.isfinite(v) or abs(v)>.001:space_hits.append(dict(envelope=n,part=q,overlap_mm3=v))
                check('continuous_turn_and_20mm_axial_clearance_'+nut+'_'+state,not space_hits,intersections=space_hits,
                    excluded_driven_part=nut,scope='Conservative rigid geometry union; fixed U-bolt retained, driven nut excluded. No thread movement, torque or robot grasp.')
                # Past 20 mm, the tip clears the fixed rod by 12.3 mm.
                # Check a separate outward clearance region, then extended
                # axial space. These are asset-space bounds, not a policy.
                offset=np.array([0,0,-.025 if index==1 else .025]);far=matrix.copy();far[:3,3]+=[0,-.020,0]
                for phase in ['outward','extended']:
                    hits=[]
                    for name,radius,start,end in tool_sections:
                        bound=cylinder_x(radius,start,end+(.100 if phase=='extended' else 0));bound.apply_transform(far)
                        if phase=='outward':
                            shifted=bound.copy();shifted.apply_translation(offset);bound=trimesh.util.concatenate([bound,shifted]).convex_hull
                        else:bound.apply_translation(offset)
                        for q,b in context.items():
                            if q.endswith('_text'):continue
                            v=overlap(bound,b)
                            if not np.isfinite(v) or abs(v)>.001:hits.append(dict(envelope=name,part=q,overlap_mm3=v))
                    check('detached_tool_'+phase+'_space_'+nut+'_'+state,not hits,intersections=hits,
                        scope='Filled conservative regions for a fully detached tool; all fixed parts including the nut remain checked.')
            transformed=contexts['closed'][nut].copy();transformed.apply_transform(np.linalg.inv(matrix))
            check('selected_nut_engagement_'+nut,abs(transformed.bounds[1,0]-.0062)<1e-7,engagement_m=float(transformed.bounds[1,0]),washer_gap_m=.0002)
            wrong=placed['steel_shaft_and_blind_socket'].copy();wrong.apply_transform(trimesh.transformations.rotation_matrix(np.pi/6,[0,1,0],point=matrix[:3,3]))
            check('negative_wrong_clocking_'+nut,overlap(wrong,contexts['closed'][nut])>1)
            prior=placed['steel_shaft_and_blind_socket'].copy();prior.apply_translation([0,0,u30['mounting']['prior_tool_obstructed_axes_z_m'][index-1]-z])
            old_hit=overlap(prior,contexts['closed']['outer_case'])
            check('negative_prior_mount_axis_'+nut,old_hit>1,overlap_mm3=old_hit,prior_axis_z_m=u30['mounting']['prior_tool_obstructed_axes_z_m'][index-1])
            if index==1:
                blocked=cylinder_x(.00925,0,.135);blocked.apply_transform(matrix)
                v=overlap(blocked,contexts['closed']['primary_channel_retaining_bar'])
                check('negative_unrestricted_lower_axial_exit_'+side,v>1,overlap_mm3=v,
                    finding='A 100 mm straight withdrawal at the seated height remains obstructed by the bottom channel. The separately checked outward region is required for geometric access.')
            poses.append(dict(nut=nut,tool_transform=matrix.tolist()))
            if (index,side) in [(1,'left'),(2,'right')]:
                g=Geometry()
                for n,m in {**contexts['open'],**{'tool_'+n:m for n,m in placed.items()}}.items():
                    g.scene.add_geometry(m,node_name=n,geom_name=n);g.parts.append(dict(id=n,role='static_tool_access',bounds_m=m.bounds.tolist()))
                fixtures.append(dict(nut=nut,geometry=g.export('wiha_34143_u30_'+str(index)+'_fit')))
    check('no_unearned_qualification',not any(r[k] for k in ['staged_in_lab','initial_stock_credit','torque_qualified','robot_use_qualified','owner_acceptance']))
    refs=[Path(__file__),HERE/'mast_driver_assets.json',HERE/'u30_assets.json',HERE/'u30_checks.json',HERE/'check_weather_assets.py',HERE/'check_nut_driver.py']
    report=dict(schema_version=1,passed=True,checks=checks,fit_geometries=fixtures,tool_poses=poses,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        axial_disengagement_space_m=.020,outward_clearance_region_m=.025,extended_axial_space_m=.100,
        unrestricted_lower_straight_withdrawal_clear=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Selected tool and inferred mounting dimensions only; actual manufacturing tolerances are unknown.',
            'The original inferred mount positions obstructed this complete tool. Revised local plate/axis geometry does not establish manufacturer CAD identity.',
            'The bottom channel obstructs unrestricted lower axial withdrawal; separate disengaged outward and extended regions are checked. These static regions are not a robot trajectory or assembly plan.',
            'Conservative turning/clearance geometry does not qualify nut engagement forces, screw threads, tightening, hand clearance or robot operation.',
            'Two fit views are alternative inspection poses of one tool; neither adds stock or an executed action.'])
    write_json(HERE/'mast_driver_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),fixtures=len(fixtures))))


if __name__=='__main__':build()
