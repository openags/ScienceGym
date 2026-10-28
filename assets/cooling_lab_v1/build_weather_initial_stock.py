"""Uninstalled weather stock on existing laboratory furniture.

Source parts retain their geometry and identity. Supplier assembly boundaries
come from the manuals, while the unpacked arrangement and folded linkage pose
are explicit design selections. This is an asset context, not a controller or
an assertion that a robot has unpacked, assembled, or transported anything.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from review_mesh_io import load_parts
from build_weather_assets import cable_mesh, rest_coil


def pose(rotation=None, translation=(0, 0, 0)):
    m = np.eye(4)
    if rotation is not None: m[:3, :3] = np.asarray(rotation)[:3, :3]
    m[:3, 3] = translation
    return m


def rotation(degrees, axis):
    return trimesh.transformations.rotation_matrix(np.radians(degrees), axis)


def folded_tripod(parts):
    """Close the existing pivoted frame, without scaling any member.

    The lower tri-clamp slides along the absent mast axis. Its height is solved
    from the unchanged brace length. The foot plates remain on their pivots.
    This is a selected static pose, not a certified folding range.
    """
    theta = np.radians(4)
    upper = np.array([0., .084, .790])
    foot = np.array([0., .510, .022])
    inner = np.array([-.015, .072, .450])
    outer = np.array([-.015, .297, .406])
    leg_angle = np.arctan2(.426, .768)
    base = trimesh.transformations.rotation_matrix(theta-leg_angle, [1, 0, 0], upper)
    new_outer = trimesh.transform_points([outer], base)[0]
    brace_length = np.linalg.norm(outer-inner)
    new_inner = inner.copy()
    new_inner[2] = new_outer[2] + np.sqrt(brace_length**2-(new_outer[1]-inner[1])**2)
    slide = new_inner[2]-inner[2]
    maps = {}; constraints = []
    for i, azimuth in enumerate([0, 120, 240], 1):
        az = rotation(azimuth, [0, 0, 1]); inv = np.linalg.inv(az)
        leg = az @ base @ inv
        old_vector = outer-inner; new_vector = new_outer-new_inner
        angle = np.arctan2(new_vector[2], new_vector[1])-np.arctan2(old_vector[2], old_vector[1])
        br = pose(translation=new_inner) @ rotation(np.degrees(angle), [1, 0, 0]) @ pose(translation=-inner)
        brace = az @ br @ inv
        maps['leg_'+str(i)] = leg
        maps['leg_brace_'+str(i)] = brace
        maps['foot_plate_and_fork_'+str(i)] = leg
        for prefix, matrix in [('upper_leg_', np.eye(4)), ('foot_', leg),
                               ('inner_brace_', pose(translation=[0, 0, slide])), ('outer_brace_', leg)]:
            for suffix in ['_pivot_bolt', '_pivot_nut']: maps[prefix+str(i)+suffix] = matrix
        constraints.append(dict(leg=i, old_brace_length_m=float(brace_length),
            new_brace_length_m=float(np.linalg.norm(new_outer-new_inner)),
            outer_pivot_error_m=float(np.linalg.norm(trimesh.transform_points([outer], br)[0]-new_outer))))
    maps['upper_leg_clamp_triangular_band'] = np.eye(4)
    maps['lower_brace_clamp_triangular_band'] = pose(translation=[0, 0, slide])
    return maps, dict(selected_leg_angle_from_vertical_deg=4, lower_clamp_slide_m=float(slide),
                      linkage_constraints=constraints, folding_motion_qualified=False)


def build():
    names = ['scene', 'weather_scene_binding', 'tripod_assets', 'weather_anchoring_assets',
             'weather_assets', 'wind_sensor_assets', 'wind_lead_assets', 'wind_kit_assets',
             'cable_tie_assets', 'long_cable_tie_assets', 'u30_assets', 'u30_ground_assets',
             'ordinary_tools', 'hose_clamp_assets', 'weather_preparation_assets',
             'tripod_sources', 'wind_sensor_sources', 'weather_sources']
    r = {n: json.loads((HERE/(n+'.json')).read_text()) for n in names}
    refs = {n: r[n]['geometry'] for n in names if 'geometry' in r[n]}
    refs.update({x['id']: x['geometry'] for x in r['weather_assets']['items']})
    refs['tray'] = next(x['geometry'] for x in r['ordinary_tools']['items'] if x['id']=='buerkle_4208_0022')
    refs['hose_clamp'] = next(x['geometry'] for x in r['hose_clamp_assets']['items'] if x['id']=='loose')
    cache = {n: load_parts(g) for n, g in refs.items()}
    surfaces = {s['id']: s for s in r['scene']['support_surfaces']}
    g = Geometry(); placements = []; groups = []; leads = []; consumed = set()

    def place(key, names, identity, group_id, support, xy, *, R=None, local=None, basis='loose_stock'):
        """Place the XY minimum on a support; never rescale or fuse solids."""
        local = local or {}; R = np.eye(4) if R is None else R
        matrices = {n: R @ local.get(n, np.eye(4)) for n in names}
        meshes = {n: cache[key][n].copy() for n in names}
        for n, m in meshes.items(): m.apply_transform(matrices[n])
        bounds = np.array([m.bounds for m in meshes.values()])
        lower = bounds[:, 0].min(axis=0)
        shift = pose(translation=np.array([*xy, surfaces[support]['top_m']])-lower)
        output_names = []
        for n, m in meshes.items():
            m.apply_transform(shift); name = group_id+'__'+n; output_names.append(name)
            assert (key, n, identity) not in consumed; consumed.add((key, n, identity))
            g.scene.add_geometry(m, node_name=name, geom_name=name)
            g.parts.append(dict(id=name, role=basis, bounds_m=m.bounds.tolist()))
            placements.append(dict(part=name, identity=identity, group=group_id,
                support=support, source_geometry={k:refs[key][k] for k in ['path','sha256']}, source_part=n,
                source_to_world=(shift@matrices[n]).tolist()))
        groups.append(dict(id=group_id, identity=identity, support=support, parts=output_names,
            state_basis=basis))
        # One group may consist of multiple supplier-fixed or pivoted pieces;
        # it is not a new welded object and does not change their identities.
        groups[-1]['bounds_m'] = [np.min([g.scene.geometry[n].bounds[0] for n in output_names], axis=0).tolist(),
                                  np.max([g.scene.geometry[n].bounds[1] for n in output_names], axis=0).tolist()]
        return shift @ R

    # Three ordinary trays on the existing fabrication rack. They initially
    # hold loose installation hardware; their later storage roles reuse them.
    tray_ids = ['weather_cutoff_tray', 'weather_removed_parts_tray', 'weather_unused_kit_tray']
    tray_slots = []
    for i, identity in enumerate(tray_ids):
        x = -5.35+.42*i; y = 3.56
        place('tray', list(cache['tray']), identity, identity, 'fabrication_storage_shelf_3', [x,y])
        support = identity+'_floor'
        surfaces[support] = dict(id=support, xy_bounds_m=[x+.030,y+.030,x+.270,y+.170],
            top_m=surfaces['fabrication_storage_shelf_3']['top_m']+.0012,
            physical_support_part=identity+'__formed_tray', load_rating_kg=None)
        tray_slots.append(dict(support=support,x=x+.030,y=y+.030,start_x=x+.030,end_x=x+.270,end_y=y+.170,row_height=0))

    def small(key, names, identity, group_id, R=None, basis='loose_installation_hardware'):
        R = np.eye(4) if R is None else R
        meshes = [cache[key][n].copy() for n in names]
        for m in meshes:m.apply_transform(R)
        bounds=np.array([m.bounds for m in meshes]);size=bounds[:,1].max(0)-bounds[:,0].min(0)
        # Explicit shelf packing, not automatic acceptance of any free area.
        for slot in tray_slots:
            x,y,row=slot['x'],slot['y'],slot['row_height']
            if x+size[0]>slot['end_x']: x,y,row=slot['start_x'],y+row+.008,0
            if y+size[1]>slot['end_y']:continue
            place(key,names,identity,group_id,slot['support'],[x,y],R=R,basis=basis)
            slot.update(x=x+float(size[0])+.008,y=y,row_height=max(row,float(size[1])))
            return
        raise ValueError('Three ordinary trays have insufficient space: '+group_id)

    mast='weather_mast_anchoring_set';tp=cache['tripod_assets']
    folded,fold_record=folded_tripod(tp)
    place('tripod_assets',list(folded),mast,'folded_tripod','fabrication_fixture',[-5.25,.45],
          R=rotation(90,[0,1,0]),local=folded,basis='supplier_pivoted_frame_selected_folded_pose')
    for name,y in [('lower_mast_with_indexing_creases',.20),('upper_mast_with_dimple_and_crossarm_holes',.28)]:
        place('tripod_assets',[name],mast,name,'fabrication_fixture',[-5.25,y],R=rotation(90,[0,1,0]))
    for name in tp:
        if name in folded or name.startswith(('lower_mast','upper_mast')):continue
        small('tripod_assets',[name],mast,'tripod_'+name)

    anch=cache['weather_anchoring_assets'];handled=set()
    for i in range(1,4):
        for prefix,y in [('guy_stake_',.44+.045*(i-1)),('foot_stake_',.64+.045*(i-1))]:
            n=prefix+str(i);place('weather_anchoring_assets',[n],mast,n,'fabrication_fixture',[-4.04,y]);handled.add(n)
        ns=[f'turnbuckle_{i}_{s}' for s in ['body','eye_lower','eye_upper']]
        place('weather_anchoring_assets',ns,mast,'turnbuckle_'+str(i),'fabrication_storage_shelf_3',[-5.35+(i-1)*.15,3.86],R=rotation(90,[0,0,1]),basis='supplier_adjustable_turnbuckle');handled.update(ns)
    place('weather_anchoring_assets',['ground_rod'],mast,'ground_rod','fabrication_fixture',[-5.25,.37]);handled.add('ground_rod')
    for n,xy in [('uncut_guy_wire',[.57,.19]),('uncut_ground_wire',[1.12,.20])]:
        m=place('weather_anchoring_assets',[n],mast,n,'raw_stock_shelf_3',xy);handled.add(n)
        wire=next(w for w in r['weather_anchoring_assets']['stored_wires'] if w['id']==n)
        leads.append(dict(id=n,identity=mast,length_m=wire['length_m'],radius_m=wire['radius_m'],
            points_m=trimesh.transform_points(wire['points_m'],m).tolist(),cut=False,source_part=n))
    place('weather_anchoring_assets',['guy_collar_triangular_band'],mast,'guy_collar_band','fabrication_storage_shelf_3',[-4.85,3.86]);handled.add('guy_collar_triangular_band')
    for n in anch:
        if n not in handled:small('weather_anchoring_assets',[n],mast,n)

    # Complete untouched straps; fourteen retained ties and two temporary ties
    # are distinct pieces. No installed strap or cutoff is initial stock.
    tie_ids=[e['id'] for e in r['weather_scene_binding']['physical_entities'] if e['id'].startswith('weather_tie_')]
    tie_ids+=['weather_temporary_leg','weather_temporary_brace']
    for i, identity in enumerate(tie_ids):
        key='long_cable_tie_assets' if identity.endswith('temporary_brace') else 'cable_tie_assets'
        place(key,list(cache[key]),identity,identity,'raw_stock_shelf_3',[1.43,.20+i*.014],R=rotation(90,[1,0,0]),basis='full_uncut_unfastened_tie')

    # RS3 manufacturer supplies an assembled shield, a separate bracket,
    # nuts, optional wall screws, six loose ties and one hose clamp.
    rs=cache['onset_rs3'];identity='weather_radiation_shield'
    body=[n for n in rs if n.startswith(('shield_','tie_rod_','rod_spacer_'))]
    place('onset_rs3',body,identity,'rs3_shield','specimens_shelf_1',[11.22,.20],R=rotation(180,[1,0,0]),basis='supplier_assembled_shield_resting_on_top_lid')
    place('onset_rs3',['inclined_mounting_bracket'],identity,'rs3_bracket','specimens_shelf_1',[11.22,.36],R=rotation(90,[0,1,0]))
    excluded=['mast_band_candidate','band_worm_housing','band_screw']
    for i in range(1,7):place('onset_rs3',[f'loose_tie_{i}_strap',f'loose_tie_{i}_head'],identity,f'rs3_kit_tie_{i}','specimens_shelf_1',[11.22,.55+i*.015])
    for n in ['knurled_nut_left','knurled_nut_right','optional_wall_screw_1','optional_wall_screw_2']:small('onset_rs3',[n],identity,'rs3_'+n)
    small('hose_clamp',list(cache['hose_clamp']),identity,'rs3_hose_clamp',basis='selected_NORMA_loose_replacement_for_unidentified_kit_clamp')

    probe=next(x for x in r['weather_assets']['items'] if x['id']=='onset_sthb_m002')
    matrix=place('onset_sthb_m002',list(cache['onset_sthb_m002']),'weather_temperature_humidity','temperature_sensor','specimens_shelf_2',[10.01,.22],basis='supplier_sensor_with_complete_unconnected_leads')
    for lead in probe['stored_leads']:
        leads.append(dict(id='temperature_'+lead['id'],identity='weather_temperature_humidity',length_m=lead['length_m'],radius_m=lead['radius_m'],
            points_m=trimesh.transform_points(lead['points_m'],matrix).tolist(),cut=False,source_part=lead['id']))

    wind=cache['wind_sensor_assets'];identity='weather_wind'
    arm_names=['bent_hollow_arm','stationary_hourglass_housing','lower_speed_shaft','upper_direction_d_shaft','lower_bearing_envelope','upper_bearing_envelope']
    arm=place('wind_sensor_assets',arm_names,identity,'wind_arm','specimens_shelf_1',[10.01,.20],R=rotation(90,[1,0,0]),basis='supplier_arm_and_factory_sensor_head_without_base_cups_or_vane')
    for ns,xy,rot in [(['three_cup_rotor','cup_set_screw'],[10.43,.20],None),
                      (['vane_with_d_bore','vane_set_screw','brass_vane_nose'],[10.62,.20],rotation(90,[1,0,0])),
                      (['mast_saddle_and_sleeve'],[10.83,.20],rotation(90,[1,0,0]))]:
        place('wind_sensor_assets',ns,identity,'wind_'+ns[0],'specimens_shelf_1',xy,R=rot,basis='manual_requires_field_attachment')
    wind_handled=set(arm_names+['three_cup_rotor','cup_set_screw','vane_with_d_bore','vane_set_screw','brass_vane_nose','mast_saddle_and_sleeve'])
    for n in wind:
        if n not in wind_handled:small('wind_sensor_assets',[n],identity,'wind_'+n)
    for n in cache['wind_kit_assets']:small('wind_kit_assets',[n],identity,'wind_kit_'+n)
    # Keep both complete leads connected to their original factory endpoints.
    # Move adapter/plug independently and solve continuous full-length curves.
    wl=cache['wind_lead_assets'];adapter=[n for n in wl if n.startswith('wind_adapter_')]
    plug=[n for n in wl if n.startswith('plug_') or n=='modular_plug_body_and_latch']
    am=place('wind_lead_assets',adapter,identity,'wind_adapter','specimens_shelf_1',[10.55,.61],R=rotation(180,[0,0,1]),basis='supplier_inline_adapter')
    pm=place('wind_lead_assets',plug,identity,'wind_free_plug','specimens_shelf_1',[10.85,.66],basis='free_unconnected_sensor_plug')
    bottom=surfaces['specimens_shelf_1']['top_m']
    starts=[trimesh.transform_points([[.003,0,.075]],arm)[0],trimesh.transform_points([[-.160,-.30,.0125]],am)[0]]
    ends=[trimesh.transform_points([[-.040,-.30,.0125]],am)[0],trimesh.transform_points([r['wind_lead_assets']['modular_plug']['cable_entry_m']],pm)[0]]
    for i,(name,length,centre,turns,angle) in enumerate([('wind_sensor_lead',2.5,[10.42,.50],4,np.pi),('wind_network_lead',.5,[10.78,.54],1,0)]):
        direction=arm[:3,:3]@np.array([-.55,0,-np.sqrt(1-.55**2)]) if i==0 else am[:3,:3]@np.array([-1,0,0])
        final=am[:3,:3]@np.array([-1,0,0]) if i==0 else np.array([1,0,0])
        if i==0:
            original=np.asarray(r['wind_sensor_assets']['cable_port']['selected_base_route_m'])
            end_index=np.flatnonzero(original[:,2]<=.055)[0]
            prefix=trimesh.transform_points(original[:end_index+1],arm)
            prefix_length=np.linalg.norm(np.diff(prefix,axis=0),axis=1).sum()
            tail=rest_coil(length-prefix_length,centre,turns,prefix[-1],ends[i],arm[:3,:3]@np.array([0,0,-1]),final,angle)
            path=np.vstack([prefix,tail[1:]])
        else:path=rest_coil(length,centre,turns,starts[i],ends[i],direction,final,angle)
        mesh=cable_mesh(path,.0015,[direction,final]);mesh.visual=wl[name].visual.copy()
        name_out='wind_stock__'+name;g.scene.add_geometry(mesh,node_name=name_out,geom_name=name_out);g.parts.append(dict(id=name_out,role='full_length_authored_stock_lead',bounds_m=mesh.bounds.tolist()))
        leads.append(dict(id=name,part=name_out,identity=identity,length_m=length,radius_m=.0015,points_m=path.tolist(),cut=False,source_part=name,
            support='specimens_shelf_1',source_geometry=refs['wind_lead_assets'],authored_shape=True))

    # Detailed original logger includes its unused channel plugs. It replaces
    # the same base logger identity; it is not a second logger on the bench.
    place('u30_assets',list(cache['u30_assets']),'hobo_u30','u30_stock','specimens_shelf_2',[10.62,.22],R=rotation(90,[1,0,0]),basis='detailed_logger_candidate_with_original_channel_plugs')
    # The selected preterminated ground lead remains explicitly inferred.
    # A rigid rest view retains its full conductor and every terminal; source
    # gauge, crimp procurement and its elastic rest shape remain open.
    place('u30_ground_assets',list(cache['u30_ground_assets']),'weather_logger_ground_lead','logger_ground_stock','specimens_shelf_2',[10.92,.22],R=rotation(90,[1,0,0]),basis='inferred_preterminated_ground_lead_rest_candidate')

    geometry=g.export('weather_initial_stock_candidate')
    bindings=r['weather_scene_binding'];staged=[m for m in bindings['modules'] if m['id'].startswith('weather_')]
    entities={p['identity'] for p in placements}|{l['identity'] for l in leads}
    existing=['utility_cart']
    references=[Path(__file__),HERE/'geometry_tools.py',HERE/'review_mesh_io.py',HERE/'build_weather_assets.py']+[HERE/(n+'.json') for n in names]
    record=dict(schema_version=1,status='uninstalled_stock_layout_candidate',state_id='weather_initial_stock_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in references],
        placements=placements,groups=groups,leads=leads,support_surfaces=list(surfaces.values()),folded_tripod=fold_record,
        source_part_exclusions=[dict(source='onset_rs3',parts=excluded,reason='Superseded low-detail unidentified clamp; same kit slot uses selected NORMA loose clamp, not additional stock.')],
        retained_base_identity_ids=existing,hide_base_identity_ids=['hobo_u30'],
        retained_tool_modules=staged,physical_identity_ids=sorted(entities|set(existing)|{m['id'] for m in staged}),
        supplied_assembly_basis=[dict(source_id='ONSET_TRIPOD_MANUAL',pages=[2,3],meaning='Open pivoted tripod first; radial fasteners and lower mast are installed separately.'),
            dict(source_id='ONSET_SWCF_MANUAL',pages=[2,3],meaning='Vane, cups, arm-to-base and mast fasteners require field attachment. Shipping packaging is still absent from this unpacked review.'),
            dict(source_id='ONSET_RS3_MANUAL',pages=[1],meaning='Shield supplied assembled; bracket, nuts, ties, screws and hose clamp supplied separately.')],
        initial_inventory_complete=False,initial_stock_credit=False,owner_acceptance=None,robot_use_qualified=False,
        limitations=['Unpacked stock context; supplier shipping cartons, unpacking and clean packaging collection are not represented.',
            'All shelf/bench furniture is existing authored geometry without verified load ratings.',
            'Folded tripod joint range, rolling stability, flexible-lead settling, grasp access and transport remain unqualified.',
            'Ground-lead gauge, length, terminal procurement and pretermination are explicit hypotheses, not manufacturer assembly evidence.',
            'The stored wind cable retains the selected 3 m interpretation; the source cable-length conflict remains open.',
            'Source-local dimensions and inferred features retain all limitations in the original asset records.'])
    write_json(HERE/'weather_initial_stock_assets.json',record)
    print(json.dumps(dict(parts=geometry['parts'],groups=len(groups),identities=len(record['physical_identity_ids']))))


if __name__=='__main__':build()
