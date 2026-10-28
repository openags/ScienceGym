"""Independent physical-dimension and usable-shape checks for staged supplies."""
import json
import struct
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json


def validate():
    report=json.loads((HERE/'supplies.json').read_text());sources=json.loads((HERE/'supply_sources.json').read_text());checks=[];scenes={}
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        if not passed:raise AssertionError(name+' '+str(data))
    for ref in report['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for item in report['items']:
        g=item['geometry'];check('identity_'+item['id'],sha(ROOT/g['path'])==g['sha256'])
        raw=(ROOT/g['path']).read_bytes();length=struct.unpack('<I',raw[12:16])[0];tree=json.loads(raw[20:20+length])
        check('explicit_pbr_materials_'+item['id'],all('material' in p for m in tree['meshes'] for p in m['primitives']) and bool(tree.get('materials')))
        check('explicit_surface_normals_'+item['id'],all('NORMAL' in p['attributes'] for m in tree['meshes'] for p in m['primitives']))
        if item['id'] in ['krylon_51502','krylon_51602','pelco_16032']:
            labels=[m['pbrMetallicRoughness'] for m in tree['materials'] if 'baseColorTexture' in m.get('pbrMetallicRoughness',{})]
            check('coating_label_is_nonmetallic_'+item['id'],len(labels)==1 and labels[0].get('metallicFactor',1)==0)
        if item['id']=='rubbermaid_1997206':
            palette=np.array([45,48,51])/255;linear=((palette+.055)/1.055)**2.4
            factors=[m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])[:3] for m in tree['materials']]
            check('cart_dark_plastic_linear_color',any(np.allclose(c,linear,atol=1e-7) for c in factors))
        scene=trimesh.load(ROOT/g['path'],force='scene');scenes[item['id']]=scene
        check('bounded_'+item['id'],np.isfinite(scene.bounds).all() and np.allclose(scene.bounds,g['bounds_m'],atol=1e-6))
        for node in scene.graph.nodes_geometry:
            t,k=scene.graph[node];m=scene.geometry[k]
            role=next((r.get('role') for r in g['part_records'] if r['id']==node),None)
            if role!='original_size_label' and 'text' not in node and 'lot_card' not in node and 'waste_role' not in node:
                welded=m.copy();welded.merge_vertices(digits_vertex=8)
                check('closed_'+item['id']+'_'+node,welded.is_watertight)
    def mesh(item,node):
        s=scenes[item];t,k=s.graph[node];m=s.geometry[k].copy();m.merge_vertices(digits_vertex=8);m.apply_transform(t);return m
    facts={s['id']:s.get('facts',{}) for s in sources['items']}
    check('stripper_catalog_envelope',np.allclose(scenes['jonard_st450'].extents,facts['jonard_st450']['dimensions_m'],atol=.00005),measured_m=scenes['jonard_st450'].extents.tolist())
    t=scenes['idealtek_aa_sa_t6'].extents
    check('tweezer_catalog_envelope',np.allclose(t,[.13,.0125,.0115],atol=1e-6),measured_m=t.tolist())
    check('driver_overall_length',abs(scenes['wiha_26015'].extents[0]-.120)<1e-6)
    probe=mesh('omega_ambient_rtd','vented_air_sheath')
    check('ambient_probe_source_dimensions',np.allclose(probe.extents,[.1524,.00635,.00635],atol=1e-6))
    # A solid stick mislabeled as an air probe must fail: source-inspired vents
    # actually connect outside to the hollow bore.
    check('ambient_probe_hollow_and_vented',not probe.contains([[.009,0,0],[.009,.00295,0]]).any())
    cable=next(i['cable'] for i in report['items'] if i['id']=='omega_ambient_rtd')
    measured=np.linalg.norm(np.diff(cable['rest_points_m'],axis=0),axis=1).sum()+cable['breakout_length_m']
    check('ambient_six_foot_lead',abs(measured-1.8288)<1e-6,measured_m=float(measured))
    cup=mesh('buerkle_7102_2000','open_pp_vessel')
    check('jug_height',abs(cup.extents[2]-.213)<1e-6)
    check('jug_mouth_is_open',not cup.contains([[0,0,.1],[0,0,.212]]).any())
    check('jug_bottom_exists',cup.contains([[0,0,.001]]).all())
    # Independent axial ray sees the base at 3 mm and no lid at the mouth.
    locations,_,_=cup.ray.intersects_location([[0,0,.25]],[[0,0,-1]])
    check('jug_open_ray',len(locations)==2 and np.max(locations[:,2])<.00301)
    kit=next(i for i in report['items'] if i['id']=='omega_smpw_cc_kit');contents=kit['contents']
    check('eight_independent_connector_pairs',len(contents)==16 and len({c['id'] for c in contents})==16 and sum(c['model'].endswith('-M') for c in contents)==8)
    # 1.2 mm tray wall; bottom inside is narrower than the top rim. All staged
    # hardware must lie inside the smaller bottom footprint, not merely the AABB.
    s=scenes['omega_smpw_cc_kit'];hardware=[]
    for node in s.graph.nodes_geometry:
        if node.startswith('ordinary_tray_'):continue
        m=mesh('omega_smpw_cc_kit',node);hardware.extend(m.vertices)
    p=np.array(hardware)
    check('connector_contents_inside_tray',p[:,0].min()>-.1378 and p[:,0].max()<.1378 and p[:,1].min()>-.0878 and p[:,1].max()<.0878 and p[:,2].min()>=.001199 and p[:,2].max()<.050,bounds_m=[p.min(axis=0).tolist(),p.max(axis=0).tolist()])
    for item,count,thickness in [('nano_pe_stock',8,.000016),('ldpe_stock',6,.00005),('mylar_stock',3,.000012)]:
        nodes=[n for n in scenes[item].graph.nodes_geometry if n.startswith('raw_film_')]
        check('film_quantity_'+item,len(nodes)==count)
        check('actual_film_thickness_'+item,all(abs(mesh(item,n).extents[2]-thickness)<1e-8 for n in nodes),thickness_m=thickness)
    block=mesh('calibration_copper_stock','unmachined_copper_block')
    check('raw_block_not_pre_drilled',block.contains([[0,0,.015],[.01,0,.015],[-.01,0,.015]]).all())
    check('block_selected_dimensions',np.allclose(block.extents,[.06,.05,.03],atol=1e-6))
    check('cart_catalog_envelope',np.allclose(scenes['rubbermaid_1997206'].extents,facts['rubbermaid_1997206']['overall_dimensions_m'],atol=.0001),measured_m=scenes['rubbermaid_1997206'].extents.tolist())
    cart=scenes['rubbermaid_1997206']
    wheel_nodes=[n for n in cart.graph.nodes_geometry if n.startswith('rubber_wheel_')]
    check('four_grounded_five_inch_wheels',len(wheel_nodes)==4 and all(abs(mesh('rubbermaid_1997206',n).bounds[0,2])<1e-7 and abs(mesh('rubbermaid_1997206',n).extents[2]-.127)<1e-7 for n in wheel_nodes))
    check('cart_shelves_open',not mesh('rubbermaid_1997206','lower_shelf').contains([[0,0,.22]]).any() and not mesh('rubbermaid_1997206','upper_shelf').contains([[0,0,.81]]).any())
    check('waste_body_not_solid',not mesh('justrite_09100','steel_body').contains([[0,0,.20]]).any())
    check('waste_height',abs(scenes['justrite_09100'].extents[2]-.403)<1e-6)
    # Catalogue kit quantities and actual through-bores, independently of the
    # model's metadata. A painted solid block cannot pass as usable hardware.
    kit=next(i['details'] for i in report['items'] if i['id']=='omax_317864')
    check('workholding_kit_thirteen_units',len(kit['units'])==13 and len({u['id'] for u in kit['units']})==13)
    for i,L in enumerate([.2032]*3+[.1524]*2,1):
        arm=mesh('omax_317864',f'arm_{i}_bowed_arm_with_post_bore');y=(i-1)*.032
        check(f'holding_arm_{i}_catalog_length',abs(arm.extents[0]-L)<1e-7)
        check(f'holding_arm_{i}_actual_post_bore',not arm.contains([[L-.018,y,.006]]).any() and arm.contains([[L-.018,y+.008,.006]]).all())
    for i in range(1,5):
        nut=mesh('omax_317864',f'tnut_{i}');y=(i-1)*.032
        check(f'tnut_{i}_actual_through_hole',not nut.contains([[.359,y,.0025]]).any() and nut.contains([[.367,y,.0025]]).all())
    check('cutter_catalog_length',abs(scenes['knipex_7803125'].extents[0]-.125)<1e-6)
    check('cutter_separate_levers',all(n in scenes['knipex_7803125'].graph.nodes_geometry for n in ['lever_-1','lever_1','opening_spring','rivet']))
    check('deburring_holder_twelve_mm_across_flats',abs(mesh('noga_rb1000','hexagonal_holder').extents[1]-.012)<1e-6)
    leads=next(i['details']['leads'] for i in report['items'] if i['id']=='pomona_5908a')
    check('four_leads_two_red_two_black',len(leads)==4 and [x['color'] for x in leads].count('red')==2 and [x['color'] for x in leads].count('black')==2)
    separate=trimesh.collision.CollisionManager()
    for lead in leads:
        name=lead['id'];p=np.array(lead['rest_points_m']);segments=np.linalg.norm(np.diff(p,axis=0),axis=1)
        check(name+'_entry_to_entry_48_inches',abs(segments.sum()-1.2192)<1e-6 and segments.min()>1e-6,measured_m=float(segments.sum()))
        # Bind the declared rest curve to the exported cable, so a short cord
        # carrying a correct length field cannot receive dimensional credit.
        cable_mesh=mesh('pomona_5908a',name+'_silicone_cable')
        _,distances,_=trimesh.proximity.closest_point(cable_mesh,p[12:-12:12])
        check(name+'_exported_tube_follows_declared_curve',np.all((distances>.0036576*.45)&(distances<.0036576*.51)),minimum_radius_m=float(distances.min()),maximum_radius_m=float(distances.max()))
        for end,origin,tangent in [('A',p[0],p[1]-p[0]),('B',p[-1],p[-2]-p[-1])]:
            direction=tangent/np.linalg.norm(tangent);T=trimesh.geometry.align_vectors([1,0,0],direction);T[:3,3]=origin-direction*.06858
            shroud=mesh('pomona_5908a',name+'_'+end+'_insulating_shroud');shroud.apply_transform(np.linalg.inv(T))
            check(name+'_'+end+'_hollow_guarded_nose',abs(shroud.extents[0]-.023495)<1e-7 and not shroud.contains([[.001,0,0],[.010,.0027,0]]).any() and shroud.contains([[.010,.0035,0]]).all())
            body=[]
            for node in scenes['pomona_5908a'].graph.nodes_geometry:
                if node.startswith(name+'_'+end+'_'):
                    m=mesh('pomona_5908a',node);m.apply_transform(np.linalg.inv(T));body.append(m)
            check(name+'_'+end+'_plug_length_2_7_inches',abs(trimesh.util.concatenate(body).extents[0]-.06858)<1e-7)
        combined=trimesh.util.concatenate([mesh('pomona_5908a',n) for n in scenes['pomona_5908a'].graph.nodes_geometry if n.startswith(name+'_')])
        separate.add_object(name,combined)
    overlap,pairs=separate.in_collision_internal(return_names=True)
    check('separately_counted_leads_do_not_intersect',not overlap,intersections=sorted([list(p) for p in pairs]))
    battery_case=trimesh.util.concatenate([mesh('unitree_g1_battery_v10',n) for n in ['battery_housing_with_recesses','front_cap_with_latch_pockets']])
    check('g1_battery_drawing_case_dimensions',np.allclose(battery_case.extents,[.120,.182,.080],atol=1e-6),measured_m=battery_case.extents.tolist())
    front=mesh('unitree_g1_battery_v10','front_cap_with_latch_pockets')
    check('g1_latch_pockets_are_recessed',not front.contains([[-.026,-.090,.039],[.026,-.090,.039]]).any() and front.contains([[-.026,-.080,.039],[.026,-.080,.039]]).all())
    back=mesh('unitree_g1_battery_v10','battery_housing_with_recesses')
    check('g1_back_connectors_have_actual_pockets',not back.contains([[0,.090,.029],[-.048,.090,.043]]).any() and back.contains([[0,.080,.029],[-.048,.080,.043]]).all())
    charge=mesh('unitree_g1_battery_v10','recessed_charge_socket')
    check('g1_rear_charge_port_matches_drawing_handedness',charge.bounds[1,0]<-.040,
          basis='Manual page 2 rear view: charging is on viewer right, corresponding to model -X when viewed from +Y')
    socket=mesh('unitree_g1_battery_v10','recessed_discharge_socket')
    check('g1_discharge_socket_has_open_mouth',not socket.contains([[0,.090,.029]]).any() and socket.contains([[0,.0845,.029]]).all())
    latches=[n for n in scenes['unitree_g1_battery_v10'].graph.nodes_geometry if n.startswith('release_latch_')]
    check('g1_separate_latches_and_unlit_windows',len(latches)==2 and sum(n.startswith('unlit_led_') for n in scenes['unitree_g1_battery_v10'].graph.nodes_geometry)==4)
    charger_case=trimesh.util.concatenate([mesh('unitree_g1_charger_v10',n) for n in ['charger_lower_case','charger_upper_case']])
    check('g1_charger_v10_case_dimensions',np.allclose(charger_case.extents,[.154,.060,.036],atol=1e-6),measured_m=charger_case.extents.tolist())
    for key in ['unitree_g1_battery_v10','unitree_g1_charger_v10']:
        detail=next(i['details'] for i in report['items'] if i['id']==key)
        check(key+'_no_electrical_credit',detail['electrical_qualified'] is False)
    for key in ['krylon_51502','krylon_51602']:
        cap=mesh(key,'cap_hollow_shell');tip=mesh(key,'inferred_conical_actuator')
        check(key+'_protective_cap_is_hollow',not cap.contains([[0,0,.19]]).any() and cap.contains([[0,0,.2075]]).all())
        check(key+'_actuator_has_recessed_nozzle',not tip.contains([[0,-.005,.187]]).any() and tip.contains([[.003,-.004,.187]]).all())
        check(key+'_selected_scale_not_manufacturer_dimensions',np.allclose(scenes[key].extents,[.066,.066,.208],atol=1e-6) and 'dimensions_m' not in facts[key],measured_mesh_m=scenes[key].extents.tolist(),status='selected hypothesis only')
    bottle=mesh('pelco_16032','amber_bottle_open_mouth')
    check('silver_bottle_actual_open_mouth',not bottle.contains([[0,0,.055],[0,0,.040]]).any() and bottle.contains([[.01175,0,.057],[0,0,.001]]).all())
    stock=mesh('pelco_16032','nominal_paste_stock')
    check('silver_nominal_mass_volume_consistent',abs(stock.volume*1e6*2.25-25)<.1,nominal_mass_from_mesh_g=float(stock.volume*1e6*2.25),scope='Nominal inventory volume, not material physics')
    check('silver_stock_inside_cavity',stock.bounds[0,2]>=.002999 and stock.bounds[1,2]<.037 and stock.extents[0]<.028)
    for key in ['krylon_51502','krylon_51602','pelco_16032']:
        detail=next(i['details'] for i in report['items'] if i['id']==key)
        check(key+'_unqualified_material_and_explicit_scale',detail['material_dynamics_qualified'] is False and 'hypothesis' in detail['dimensions_status'])
        check(key+'_cap_part_binding',all(n in scenes[key].graph.nodes_geometry for n in detail['inspection']['parts']))
    out=dict(schema_version=1,checks_passed=all(c['passed'] for c in checks),checks=checks,supplies_sha256=sha(HERE/'supplies.json'),validator_sha256=sha(__file__),asset_acceptance=False,
        limitations=['Catalogue shape checks do not qualify handling, deformation or electrical functions','Staged quantity is a selected starting allocation, not full campaign coverage','Commercial models contain explicitly recorded local inferences; source CAD was not obtained'])
    write_json(HERE/'supply_checks.json',out);print(json.dumps(dict(checks=len(checks),passed=out['checks_passed'])))


if __name__=='__main__':validate()
