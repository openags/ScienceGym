"""Check source bindings and prove that deliberate layout faults are rejected."""
import copy
import json
import tempfile
from pathlib import Path
import numpy as np
import mujoco
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_layout import inspect
from access_geometry import access_obstacles


def validate():
    scene=json.loads((HERE/'scene.json').read_text())
    inventory=json.loads((HERE/'inventory.json').read_text())
    contract=json.loads((HERE/'acceptance_contract.json').read_text())
    checks=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    check('source_inventory_pinned',sha(ROOT/inventory['source_inventory']['path'])==inventory['source_inventory']['sha256'])
    source=json.loads((ROOT/inventory['source_inventory']['path']).read_text())
    for row in inventory['items']:
        if row.get('source_pointer'):
            value=source
            for part in row['source_pointer'].strip('/').split('/'):
                value=value[int(part)] if isinstance(value,list) else value[part]
            check('source_row_'+row['id'],value==row['source_value'])
        for candidate in row['candidate_artifacts']:
            check('candidate_'+row['id']+'_'+candidate['path'],sha(ROOT/candidate['path'])==candidate['sha256'])
    check('inventory_count',len(inventory['items'])==inventory['required_records']==66)
    check('added_sensor_requirements_explicit',{'robot:HEAD_RGBD','robot:WRIST_RGB_LEFT','robot:WRIST_RGB_RIGHT'}<={r['id'] for r in inventory['items']})
    camera_folder=ROOT/'assets/realsense_cameras_v1'
    camera_record=json.loads((camera_folder/'model.json').read_text())
    camera_check=json.loads((camera_folder/'VERIFICATION.json').read_text())
    check('camera_verification_current',camera_check['passed'] and camera_check['model_sha256']==sha(camera_folder/'model.json') and camera_check['validator_sha256']==sha(camera_folder/'validate.py'))
    check('camera_sources_current',camera_record['source_ledger_sha256']==sha(camera_folder/'sources.json') and camera_record['builder_sha256']==sha(camera_folder/'build.py'))
    rig_path=ROOT/scene['sensor_rig']['path'];rig=json.loads(rig_path.read_text())
    fit=json.loads((ROOT/'assets/g1_sensor_rig_v1/fit_checks.json').read_text())
    check('sensor_rig_pinned',sha(rig_path)==scene['sensor_rig']['sha256']==fit['rig_sha256'])
    check('conflicting_mount_not_accepted',fit['checks_passed'] and not fit['active_installation'] and not fit['mechanical_compatibility_qualified'] and not rig['sensor_runtime_qualified'])
    for rec in rig['source_artifacts']+fit['source_artifacts']:check('rig_source_'+rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    supplies=json.loads((HERE/'supplies.json').read_text());supply_checks=json.loads((HERE/'supply_checks.json').read_text())
    check('supply_verification_current',supply_checks['checks_passed'] and supply_checks['supplies_sha256']==sha(HERE/'supplies.json') and supply_checks['validator_sha256']==sha(HERE/'check_supplies.py'))
    for ref in supplies['source_artifacts']:check('supply_source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for role in camera_record['selected_roles']:
        placed=[a for a in scene['assets'] if role['resource_id'] in a.get('resource_ids',[a['resource_id']])]
        check('camera_staged_'+role['resource_id'],len(placed)==1 and placed[0]['station']==('circulation' if role['model']=='native_g1_d435i' else 'assembly_white'))
    tc_folder=ROOT/'assets/omega_5tc_v1'
    tc=json.loads((tc_folder/'model.json').read_text());tc_check=json.loads((tc_folder/'VERIFICATION.json').read_text())
    check('tc_verification_current',tc_check['passed'] and tc_check['model_sha256']==sha(tc_folder/'model.json') and tc_check['validator_sha256']==sha(tc_folder/'validate.py'))
    check('tc_inputs_current',tc['source_ledger_sha256']==sha(tc_folder/'sources.json') and tc['builder_sha256']==sha(tc_folder/'build.py'))
    check('eight_loose_probe_instances',len([a for a in scene['assets'] if a['resource_id']=='equipment:TC'])==8 and tc['assembly_state']=='loose_stored_probe_not_attached_or_connected')
    check('room_details_pinned',scene['room_details_sha256']==sha(HERE/'room_details.py'))
    check('room_builder_pinned',scene['room_builder_sha256']==sha(HERE/'room_architecture.py'))
    check('current_scene_pinned',contract['current_scene']['sha256']==sha(HERE/'scene.json'))
    policy=json.loads((HERE/'pilot_contract.json').read_text())
    from build_readiness import validate_policy
    validate_policy(policy,scene)
    check('selected_embodiment_resources_present',set(policy['robot']['resource_ids'])<={r['id'] for r in inventory['items']})
    check('pilot_policy_pinned',scene['pilot_contract']['sha256']==sha(HERE/'pilot_contract.json'))
    integration=json.loads((ROOT/'assets/unitree_g1_inspire_v1/integration.json').read_text())
    workspace=json.loads((HERE/'workspace_checks.json').read_text())
    for record in [integration,workspace]:
        for evidence in record['source_artifacts']:check('integration_source_'+evidence['path'],sha(ROOT/evidence['path'])==evidence['sha256'])
    check('source_model_asset_checks',all(c['passed'] for c in integration['checks']) and integration['model']['nu']==41 and integration['model']['equality_constraints']==12)
    check('workspace_current_scene',workspace['scene_sha256']==sha(HERE/'scene.json'))
    access=dict(access_obstacles(scene))
    rack_boxes=[b for name,b in access.items() if name.startswith('raw_stock_')]
    check('rack_open_interior_not_filled',len(rack_boxes)==9 and not any(np.all(np.array([1.3,.45,1.30])>b[0]) and np.all(np.array([1.3,.45,1.30])<b[1]) for b in rack_boxes))
    check('rack_shelf_board_remains_solid',any(np.all(np.array([1.3,.45,1.10])>b[0]) and np.all(np.array([1.3,.45,1.10])<b[1]) for b in rack_boxes))
    check('rack_existing_stock_retained',{'stock_plate_stack','foam_acrylic_stock_stack','pe_stock'}<=set(access))
    check('floor_device_boxes_keep_identity',{'utility_cart','oily_waste_can','waterjet'}<=set(access))
    candidates=sum(r['result']['position_candidate'] for r in workspace['targets'])
    check('workspace_counts',workspace['counts']==dict(targets=len(workspace['targets']),position_candidates=candidates,needs_revision=len(workspace['targets'])-candidates))
    check('workspace_candidate_predicate',all(r['result']['position_candidate']==(r['result']['position_error_m']<.01 and not r['result']['external_overlaps'] and r['result']['self_contacts_checked'] and not r['result']['self_penetrations_over_0_5mm'] and r['result']['candidate_rig_checked'] and not r['result']['candidate_rig_other_link_intersections'] and not r['result']['candidate_rig_parent_contacts_unqualified']) for r in workspace['targets']))
    check('static_integration_not_execution_credit',not integration['full_physics_qualified'] and not workspace['full_workspace_qualified'])
    model=mujoco.MjModel.from_xml_path(str(ROOT/integration['model']['path']))
    def replay_pose(row):
        data=mujoco.MjData(model);data.qpos[:3]=row['base_position_m'];yaw=row['base_yaw_rad']
        data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
        for name,value in row['joint_coordinates'].items():data.qpos[model.joint(name).qposadr[0]]=value
        mujoco.mj_forward(model,data)
        penetration=max((-c.dist for c in data.contact if all(model.geom_bodyid[g]!=0 for g in c.geom)),default=0)
        return data,float(penetration)
    for target in workspace['targets']:
        if target['result']['position_candidate']:
            row=target['result'];data,penetration=replay_pose(row)
            error=np.linalg.norm(data.site(row['hand']+'_palm_review').xpos-target['point_m'])
            check('replay_static_candidate_'+target['id'],error<.01 and abs(error-row['position_error_m'])<1e-8 and penetration<=.0005)
    fixture=json.loads((HERE/'workspace_self_contact_fixture.json').read_text())
    _,penetration=replay_pose(fixture['pose'])
    check('reject_observed_arm_through_torso_pose',fixture['pose']['position_error_m']<.01 and not fixture['pose']['external_overlaps'] and penetration>=fixture['expected_self_penetration_minimum_m'])
    readiness=json.loads((HERE/'readiness.json').read_text())
    active=[r for r in readiness['requirements'] if r['disposition']!='historical_embodiment_reference']
    rc=readiness['counts']
    check('active_requirements_exclude_three_historical_models',rc['active_requirement_groups']==len(active)==63 and rc['historical_requirement_groups']==len(readiness['requirements'])-len(active)==3)
    check('active_component_and_geometry_counts',rc['active_component_requirements']==sum(len(r['components']) for r in active)==136 and rc['active_groups_without_geometry']==sum(not r['scene_instances'] and not r['authored_components'] for r in active)==6)
    for source in readiness['source_artifacts']:check('readiness_source_'+source['path'],sha(ROOT/source['path'])==source['sha256'])
    staged=[c for r in readiness['requirements'] for c in r['components'] if 'staged_candidates' in c]
    check('staged_supply_component_bindings',len(staged)==readiness['counts']['components_with_staged_unit_bindings']==20)
    check('staged_quantities_not_campaign_claims',all(c['required_quantity'] is None and not c['staged_candidates']['campaign_sufficiency_accepted'] and c['staged_candidates']['quantity']==len(c['staged_candidates']['members']) for c in staged))
    for c in staged:
        for unit_index,member in enumerate(c['staged_candidates']['members']):
            a=next(a for a in scene['assets'] if a['id']==member['asset_id'])
            check('staged_member_'+c['id']+'_'+str(unit_index)+'_'+a['id'],member['geometry_sha256']==a['geometry_sha256'] and bool(member['parts']) and set(member['parts'])<=set(a['part_names']))
    check('all_manual_requirements_mapped',len(readiness['manual_step_requirements'])==200)
    check('manual_requirements_follow_current_embodiment',all(set(policy['robot']['resource_ids'])<=set(s['embodiment_requirements']) and 'robot:H2' not in s['embodiment_requirements'] for s in readiness['manual_step_requirements']))
    check('ordinary_tools_only',not any(c['id'] in ['film_jig','emitter_jig','carrier_0','carrier_1'] for c in scene['authored_components']))
    for state in scene['inspection_states']:
        if state['kind']=='joint_tree':
            check('kinematic_source_'+state['id'],sha(ROOT/state['kinematics_source']['path'])==state['kinematics_source']['sha256'])
            check('kinematic_content_'+state['id'],json.loads((ROOT/state['kinematics_source']['path']).read_text())==state['kinematics'])
    for filename,builder,ledger in [('ordinary_tools.json','build_ordinary_tools.py','ordinary_tools_sources.json'),('waterjet.json','build_waterjet.py','waterjet_sources.json')]:
        model=json.loads((HERE/filename).read_text())
        check('builder_identity_'+filename,model['builder_sha256']==sha(HERE/builder))
        check('source_ledger_identity_'+filename,model['source_ledger_sha256']==sha(HERE/ledger))
        records=model.get('items',[model])
        for entry in records:
            geo=entry['geometry'];check('catalog_model_identity_'+entry['id'],sha(ROOT/geo['path'])==geo['sha256'])
    waterjet=json.loads((HERE/'waterjet.json').read_text())
    check('waterjet_selection_not_historical_claim',not waterjet['paper_model_identified'] and not waterjet['process_qualified'] and not waterjet['safety_interlocks_implemented'])
    actual=trimesh.load(ROOT/waterjet['geometry']['path'],force='scene').extents
    check('waterjet_selected_envelope',np.allclose(actual,[1.004,1.054,1.435],atol=.002))
    stock=json.loads((HERE/'stock_sources.json').read_text())
    check('stock_source_identity',sha(ROOT/stock['source_artifact']['path'])==stock['source_artifact']['sha256'])
    structure_parts={p['id']:p for p in scene['architecture']['part_records']}
    for part,thickness in [('stock_sheet_0',.0005),('stock_sheet_1',.0015),('foam_stock_sheet',.025)]:
        bounds=np.asarray(structure_parts[part]['bounds_m'])
        check('source_stock_thickness_'+part,abs(bounds[1,2]-bounds[0,2]-thickness)<1e-7)
    check('no_inferred_owner_acceptance',contract['owner_acceptance']['decision']=='pending' and all(g['status']=='open' for g in contract['gates']))
    check('no_new_manipulation_authority',not contract['new_manipulation_development_allowed'] and not scene['manipulation_development_allowed'])
    for gate in contract['gates']:
        for evidence in gate['evidence']:check('gate_evidence_'+gate['id']+'_'+evidence['path'],sha(ROOT/evidence['path'])==evidence['sha256'])
    for identity,expected in [('eko_ms402',[.16,.16,.108]),('hobo_u30',[.1805,.118,.189])]:
        actual=trimesh.load(HERE/'geometry'/f'{identity}.glb',force='scene').extents
        check('drawing_dimensions_'+identity,np.allclose(actual,expected,atol=.0001))
    body=json.loads((ROOT/scene['envelope']['body_evidence']['path']).read_text())
    hand=json.loads((ROOT/scene['envelope']['hand_evidence']['path']).read_text())
    check('hand_checker_identity',hand['checker_sha256']==sha(ROOT/'assets/unitree_g1_inspire_v1/check_space.py'))
    for source in hand['source_artifacts']:check('hand_envelope_source_'+source['path'],sha(ROOT/source['path'])==source['sha256'])
    check('body_evidence_hash',scene['envelope']['body_evidence']['sha256']==sha(ROOT/scene['envelope']['body_evidence']['path']))
    check('body_provisional_radius_covers_sampled_record',body['maximum_sampled']['radial_extent_m']<=scene['envelope']['transit_radius_m'])
    for p in body['source_artifacts']:check('body_source_'+p['path'],sha(ROOT/p['path'])==p['sha256'])
    original=inspect(quiet=True);check('base_layout',original['passed'])
    faults=[]
    # Separate independent faults exercise spatial predicates, not just schema.
    for name,expected in [('low_header','headroom_main'),('blocked_route','corridor_main'),('small_support','support_cary'),('overlapping_fixture','assets_and_authored_fixtures_separated'),('underestimated_hand_envelope','selected_hand_radius'),('opening_obstruction','external_opening_cary_lid')]:
        bad=copy.deepcopy(scene)
        if name=='low_header':bad['obstacles'].append(dict(id='injected_low_header',role='test',bounds_m=[[5,4,1.2],[7,4.1,1.35]]))
        elif name=='blocked_route':bad['obstacles'].append(dict(id='injected_crate',role='test',bounds_m=[[5.8,5,.0],[6.2,5.4,1.9]]))
        elif name=='small_support':next(s for s in bad['support_surfaces'] if s['id']=='cary_bench')['xy_bounds_m']=[2.2,8.6,2.3,8.7]
        elif name=='overlapping_fixture':
            next(a for a in bad['assets'] if a['id']=='heater')['position_m']=[9.7,2.7,.9]
        elif name=='underestimated_hand_envelope':bad['envelope']['transit_radius_m']=.5
        else:
            sweep=next(s for s in original['opening_states'] if s['id']=='cary_lid')['sweep_bounds_m'];center=(np.array(sweep[0])+sweep[1])/2
            bad['obstacles'].append(dict(id='injected_cover_obstacle',role='test',bounds_m=[(center-.01).tolist(),(center+.01).tolist()]))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'scene.json';write_json(p,bad);record=inspect(p,Path(tmp)/'result.json',quiet=True)
        failed=[c['name'] for c in record['checks'] if not c['passed']]
        check('reject_'+name,not record['passed'] and expected in failed)
        faults.append(dict(fault=name,expected_failure=expected,observed_failures=failed))
    record=dict(passed=True,checks=checks,negative_cases=faults,scene_sha256=sha(HERE/'scene.json'),
        validator_sha256=sha(__file__),layout_checker_sha256=sha(HERE/'check_layout.py'),
        workspace_sha256=sha(HERE/'workspace_checks.json'),self_contact_fixture_sha256=sha(HERE/'workspace_self_contact_fixture.json'),
        scope='Source identity and meaningful negative layout cases; no asset, full-body or safe-use acceptance')
    write_json(HERE/'review_verification.json',record)
    print(json.dumps(dict(passed=True,checks=len(checks),negative_cases=len(faults)),indent=2))


if __name__=='__main__':validate()
