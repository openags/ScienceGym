"""Reconcile existing operation requirements with the current scene, without
turning static definitions, candidate meshes or old Panda runs into task credit.
"""
import json
from pathlib import Path
from geometry_tools import HERE,ROOT,sha,write_json

TASK=ROOT/'tasks/directional_cooling_operations_v3'
# Explicit author mapping, not a substring guess or an actor's reference plan.
INTERFACES={
 'carrier':['tools:supported_carrier','facility:CARRIERS'],
 'stock':['facility:STORAGE']+[f'consumables:consumable_{i:02d}' for i in range(1,14)],
 'cutting':['equipment:WATERJET','tools:cutting_fixture','tools:caliper','facility:FABRICATION'],
 'machine_ui':['equipment:WATERJET','facility:FABRICATION'],
 'coating':['tools:coating_station','consumables:consumable_07','consumables:consumable_13','facility:COATING','facility:WASTE'],
 'base':['equipment:COOLER','consumables:consumable_01','consumables:consumable_04','consumables:consumable_10','consumables:consumable_12','tools:fastener_driver'],
 'emitter':['equipment:COOLER','consumables:consumable_01','consumables:consumable_03','additional_reconstructed_materials:reversible_emitter_jig'],
 'film':['equipment:COOLER','consumables:consumable_05','consumables:consumable_06','tools:film_jig'],
 'shield':['equipment:COOLER','consumables:consumable_09','consumables:consumable_02'],
 'reflector':['equipment:COOLER','consumables:consumable_02','tools:fastener_driver'],
 'bath_lid':['equipment:BATH'],
 'bath_fill':['equipment:BATH','additional_reconstructed_materials:bath_water_and_fill_vessel','facility:WET_SERVICES'],
 'cal_block':['additional_reconstructed_materials:calibration_block_stock','equipment:REF_RTD','equipment:TC'],
 'daq_terminals':['equipment:TC','equipment:DAQ','tools:wire_stripper_and_driver','additional_reconstructed_materials:fine_wire_transition'],
 'rtd_meter':['equipment:REF_RTD','equipment:DMM','consumables:consumable_11'],
 'bath_ui':['equipment:BATH'],
 'probe_attachment':['equipment:TC','consumables:consumable_08','additional_reconstructed_materials:reversible_emitter_jig'],
 'optical_access':['equipment:UVVIS','equipment:FTIR'],
 'optical_accessory':['accessory:DRA_2500','accessory:INTEGRATIR','equipment:ANGLE_12','equipment:ANGLE_VAR','tools:fastener_driver'],
 'ftir_connections':['equipment:FTIR','accessory:INTEGRATIR','consumables:consumable_11','facility:UTILITIES'],
 'optical_reference':['accessory:DRA_2500','accessory:INTEGRATIR','tools:storage_supports'],
 'optical_sample':['equipment:UVVIS','equipment:FTIR','accessory:DRA_2500','accessory:INTEGRATIR','tools:storage_supports'],
 'angle_controls':['equipment:ANGLE_12','equipment:ANGLE_VAR'],
 'acquisition_ui':['equipment:UVVIS','equipment:FTIR','equipment:DAQ','equipment:DMM','equipment:SMU'],
 'ambient_mount':['equipment:AMB_RTD','facility:OUTDOOR'],
 'weather_mount':['equipment:WEATHER','facility:OUTDOOR','tools:fastener_driver'],
 'solar_mount':['equipment:SOLAR_TRACKER','equipment:DNI','equipment:GTI','facility:OUTDOOR','tools:fastener_driver'],
 'daq_box':['equipment:DAQ','consumables:consumable_11','tools:fastener_driver'],
 'metal_lids':['equipment:COOLER','consumables:consumable_02','tools:storage_supports'],
 'heater':['equipment:HEATER','additional_reconstructed_materials:reversible_emitter_jig'],
 'heater_wiring':['equipment:HEATER','equipment:SMU','consumables:consumable_11','tools:wire_stripper_and_driver'],
 'smu_ui':['equipment:SMU'],
 'storage':['facility:STORAGE','facility:WASTE','tools:storage_supports'],
}

# Split compound descriptions. Quantities without an evidenced allocation stay
# null: a type list is not a sufficient bill of materials for the campaign.
DECOMPOSE={
 'robot:HEAD_RGBD':['native G1 D435i camera','source head optical frame','USB power/data and strain relief','optical and mounting calibration'],
 'robot:WRIST_RGB_LEFT':['selected left D405 camera','left wrist mounting hardware','USB power/data and strain relief','optical and mounting calibration'],
 'robot:WRIST_RGB_RIGHT':['selected right D405 camera','right wrist mounting hardware','USB power/data and strain relief','optical and mounting calibration'],
 'equipment:WATERJET':['cutting table and slats','stage and nozzle','guard and interlocks','pump and pressure circuit','abrasive hopper and feed','abrasive stock','water supply and filtration','drain and spent-abrasive collection','controller and laptop'],
 'equipment:COOLER':['white tracked assembly','black tracked assembly','fixed-band configuration and reusable parts'],
 'equipment:WEATHER':['U30 logger','temperature/humidity sensor','wind sensor','mast and brackets','power and data connections'],
 'equipment:TC':['identified K probes','lead pairs','numbered transition terminals','strain relief'],
 'equipment:AMB_RTD':['ambient probe','radiation shield','mount','lead termination'],
 'tools:film_jig':['ordinary film-edge handling tool selection','ordinary spacer and support method'],
 'tools:wire_stripper_and_driver':['fine-wire compatible stripping tool','terminal slotted driver','cutting tool','inspection tool'],
 'tools:cutting_fixture':['ordinary machine workholding','cutting tool','deburring tool'],
 'tools:storage_supports':['accepted sample storage','rejected sample storage','reference standard storage','caps and plugs'],
 'consumables:consumable_02':['aluminum sheet stock','aluminum tube stock'],
 'consumables:consumable_07':['white coating','black coating'],
 'consumables:consumable_11':['sensor leads','heater force/sense leads','instrument data cables','power leads'],
 'consumables:consumable_12':['frame fasteners','accessory fasteners','electrical termination fasteners'],
 'consumables:consumable_13':['masking tape','cleaning supplies','wipes','compatible waste containers'],
 'additional_reconstructed_materials:calibration_block_stock':['copper block raw stock','machined block state','drill tooling'],
 'additional_reconstructed_materials:fine_wire_transition':['compatible conductor pairs','K-type connector pairs or transition terminals','insulation and strain relief'],
 'additional_reconstructed_materials:bath_water_and_fill_vessel':['water allocation','ordinary fill vessel','drain hose','collection vessel'],
 'additional_reconstructed_materials:reversible_emitter_jig':['ordinary edge support method','ordinary handling tool'],
 'facility:CARRIERS':['ordinary specimen trays','ordinary heavy-equipment cart','staging positions'],
 'facility:UTILITIES':['grounded outlets','isolators','cable routes','data network'],
 'facility:WET_SERVICES':['fill source','drain path','spill containment'],
 'facility:SAFETY':['access and egress','emergency controls','hazard-specific protective provisions'],
 'facility:OUTDOOR':['apparatus supports','sensor mast','weather protection','power and data routing'],
 'facility:WASTE':['coating waste','cleaning waste','sharp stock waste','discarded specimen storage'],
 'facility:ROBOT_SERVICE':['staging position','battery or charging service','ordinary service tools'],
}

def validate_policy(c,scene):
    if c['observations']['actor_mode']!='robot_sensors_only':raise ValueError('sensor-only actor contract required')
    sensor_channels={'camera RGB','camera depth','joint encoders','IMU','qualified tactile and contact sensor outputs'}
    if not set(c['observations']['allowed_channels'])<=sensor_channels:raise ValueError('privileged or undeclared observation channel')
    if c['adaptations']['robot_specific_fixtures_allowed'] or c['adaptations']['added_fiducials_allowed']:raise ValueError('owner disallowed fixture/fiducial adaptation')
    if any(p['role'] in ['custom_fixture','custom_carrier','fiducial'] for p in scene['architecture']['part_records']):raise ValueError('disallowed fixture remains in scene')
    if c['new_manipulation_development_allowed'] or scene['manipulation_development_allowed']:raise ValueError('scene acceptance has not been received')
    if c['owner_scene_acceptance'] is not None:raise ValueError('no owner acceptance receipt for this revision')
    robot=c['robot']
    if robot['body_manufacturer']!='Unitree':raise ValueError('owner requires a Unitree body')
    if robot['silent_model_relabeling_allowed']:raise ValueError('silent model relabeling is not allowed')
    record=(ROOT/robot['selection_record']).resolve()
    if not record.is_relative_to(ROOT) or not record.is_file():raise ValueError('missing selection provenance')
    selected=json.loads(record.read_text())
    if any(robot[k]!=selected[k] for k in ['body_manufacturer','body_candidate','hands','resource_ids']):raise ValueError('model identity differs from selection provenance')
    source=selected['source_bundle']
    if sha(ROOT/source['path'])!=source['sha256']:raise ValueError('selection provenance source mismatch')

def build():
    c=json.loads((HERE/'pilot_contract.json').read_text());scene=json.loads((HERE/'scene.json').read_text())
    inv=json.loads((HERE/'inventory.json').read_text());validate_policy(c,scene)
    items={i['id']:i for i in inv['items']}
    interfaces=json.loads((TASK/'interaction_contracts.json').read_text())['interfaces']
    assert set(INTERFACES)=={i['id'] for i in interfaces},'All interfaces require explicit review mapping'
    ops=json.loads((TASK/'operations.json').read_text())['operations']
    branches=json.loads((TASK/'branches.json').read_text())['branches']
    requirements=[]
    selected_minimum={**{r:1 for r in c['robot']['resource_ids']},
      'robot:HEAD_RGBD':1,'robot:WRIST_RGB_LEFT':1,'robot:WRIST_RGB_RIGHT':1,
      'equipment:COOLER':2,'equipment:SMU':2,'equipment:TC':8}
    for r in inv['items']:
        components=DECOMPOSE.get(r['id'],[r['label']])
        requirements.append(dict(resource_id=r['id'],label=r['label'],
          components=[dict(id=r['id']+':component_'+str(i+1),label=label,required_quantity=None,quantity_status='not_allocated') for i,label in enumerate(components)],
          scene_instances=[a['id'] for a in r.get('scene_instances',[])],
          authored_components=[a['id'] for a in r.get('authored_scene_components',[])],
          selected_minimum_quantity=selected_minimum.get(r['id']),
          quantity_basis='Owner-selected embodiment / existing minimum paired-apparatus allocation; not historical quantities' if r['id'] in selected_minimum else 'Not yet allocated',
          instance_count_accepted=False,completeness_accepted=False,
          disposition='historical_embodiment_reference' if r.get('requirement_role')=='superseded_embodiment_reference' else 'ordinary_tool_method_required' if r['id'] in ['tools:film_jig','additional_reconstructed_materials:reversible_emitter_jig'] else 'review_required'))
    staged=json.loads((HERE/'staged_supply_bindings.json').read_text())
    assert staged['asset_acceptance'] is False and staged['campaign_sufficiency_accepted'] is False
    by_component={(r['resource_id'],c['label']):c for r in requirements for c in r['components']}
    assets={a['id']:a for a in scene['assets']};seen=set()
    for binding in staged['bindings']:
        key=(binding['resource_id'],binding['component_label']);assert key in by_component and key not in seen,key;seen.add(key)
        units=[];parts_used={}
        for member in binding['members']:
            a=assets[member['asset_id']];parts=member.get('parts',a['part_names'])
            assert parts and set(parts)<=set(a['part_names']),member
            used=parts_used.setdefault(a['id'],set());assert not used.intersection(parts),'Staged units overlap';used.update(parts)
            units.append(dict(asset_id=a['id'],parts=parts,geometry_path=a['geometry'],geometry_sha256=a['geometry_sha256']))
        by_component[key]['staged_candidates']=dict(quantity=len(units),unit=binding['unit'],members=units,scope=binding['scope'],campaign_sufficiency_accepted=False)
    step_rows=[]
    for op in ops:
        for step in op['reference_steps']:
            if step['capability']!='manipulation':continue
            iface=step['interaction']['interface_id'];resources=INTERFACES[iface]
            assert all(r in items for r in resources),iface
            step_rows.append(dict(step_id=step['id'],operation_id=op['id'],interface_id=iface,action=step['action'],
                resource_requirements=resources,
                missing_scene_resources=[r for r in resources if not items[r].get('scene_instances') and not items[r].get('authored_scene_components')],
                embodiment_requirements=c['robot']['resource_ids']+['robot:HEAD_RGBD','robot:WRIST_RGB_LEFT','robot:WRIST_RGB_RIGHT'],
                humanoid_execution_binding=None,sensor_completion_binding=None,qualified=False))
    relevant_legacy=[]
    for i in interfaces:
        text=' '.join(str(i.get(k,'')) for k in ['target_role','tool_role','contact_region'])
        if any(t in text.lower() for t in ['parallel gripper','dock latch','jig','frame','nest']):
            relevant_legacy.append(dict(interface_id=i['id'],legacy_tool_role=i['tool_role'],
              disposition='Inspect against ordinary-tool-only contract; old text remains historical, not current runtime authority'))
    branch_rows=[dict(id=b['id'],title=b['title'],manual_step_ids=[s['step_id'] for s in step_rows if s['operation_id'] in b['operation_ids']],
                     status='requirements_only_no_humanoid_execution',qualified_trials=0) for b in branches]
    source_paths=[HERE/'pilot_contract.json',ROOT/c['robot']['selection_record'],HERE/'scene.json',HERE/'inventory.json',HERE/'staged_supply_bindings.json',TASK/'operations.json',TASK/'interaction_contracts.json',TASK/'branches.json',Path(__file__)]
    active=[r for r in requirements if r['disposition']!='historical_embodiment_reference']
    out=dict(schema_version=1,status='asset_phase_incomplete',visibility='author_and_reviewer_only_not_actor_input',
      source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in source_paths],
      policy=c,counts=dict(requirement_groups=len(requirements),decomposed_component_requirements=sum(len(r['components']) for r in requirements),
       active_requirement_groups=len(active),historical_requirement_groups=len(requirements)-len(active),active_component_requirements=sum(len(r['components']) for r in active),
       active_groups_without_geometry=sum(not r['scene_instances'] and not r['authored_components'] for r in active),
       manual_definitions=len(step_rows),interfaces=len(interfaces),branches=len(branch_rows),scene_instances=len(scene['assets']),
       groups_with_partial_geometry=sum(bool(r['scene_instances'] or r['authored_components']) for r in requirements),
       components_with_staged_unit_bindings=len(seen),
       qualified_humanoid_branches=0),requirements=requirements,manual_step_requirements=step_rows,branches=branch_rows,
      legacy_interface_review=relevant_legacy,
      hard_dependencies=[dict(id='HAND',label='G1 与 Inspire FTP 集成',detail='官方左右手、腕部安装、惯性与联动参数已下载；已进入实验室；重力与浮动基座模型已编译，手掌碰撞分块和真实驱动、接触参数仍待物理验收'),
       dict(id='TOOLS',label='普通工具操作方法',detail='旧薄膜和翻面专用夹具已移除；普通工具方法尚需证明可行'),
       dict(id='RESOURCES',label='全部资源与设备',detail='已补剥线器、普通镊子、量杯、环境 RTD、转接头及部分原料；尚缺加工配套、光学附件、完整布线和消耗品，数量分配尚未完成'),
       dict(id='SPACE',label='完整携物空间',detail='已有 G1 限定静态通道检查与逐点工位筛查；双手协同、携物、行走与制动仍需验证'),
       dict(id='OBSERVATION',label='传感器闭环',detail='原生 D435i 已有名义光学视角；D405 官方支架已转为上置候选，已避开原腕俯仰部件冲突，适配抱环与标准紧固件已排除刚性干涉；衬垫预紧、线缆和独立观察流仍缺'),
       dict(id='OWNER',label='场景验收',detail='资产场景尚未具备完整验收条件，没有自动推断你的批准')],
      limitations=['Mapping records design requirements, not implemented controller bindings',
       'Component splitting is an explicit working decomposition, not accepted quantity allocation or complete instance coverage',
       'Ordinary tools do not automatically resolve legacy specialized-fixture interactions'])
    write_json(HERE/'readiness.json',out)
    print(json.dumps(out['counts']))

if __name__=='__main__':build()
