"""Compile explicit action/interface/source links and a readable review guide."""
import hashlib
import json
import sys
from pathlib import Path
from manipulation_refinement import INTERFACES

HERE = Path(__file__).resolve().parent
ASSET = HERE.parents[1] / 'assets/cooling_scene_assets_v2'
sys.path.insert(0, str(ASSET))
from interaction_geometry import TC_CHANNEL_PINS, PIN_SIGNALS, SENSOR_LAYOUT


def read(name, base=HERE):
    return json.loads((base / (name + '.json')).read_text())


def write(name, value, base=HERE):
    (base / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')


# Selectors are explicit per-interface, restricted to named instance roots.
# A geometry selection is a review link, not an executable grasp binding.
COOLERS = ['COOLER_WHITE', 'COOLER_BLACK', 'COOLER_FIXED_BAND', 'COOLER_THERMAL_MAP']
SELECT = {
    'base': [(COOLERS, ['acrylic_base', 'foam_1', 'foam_2'])],
    'emitter': [(COOLERS, ['emitter_copper', 'PE_support'])],
    'film': [(COOLERS, ['film_spacer', 'cover_lower', 'cover_upper'])],
    'shield': [(COOLERS, ['radiation_shield', 'aperture_plate', 'mylar_base'])],
    'reflector': [(COOLERS, ['reflector_track', 'reflector_carriage', 'solar_reflector', 'fixed_reflector_band'])],
    'bath_lid': [(['THERMO_A25_AC150_HYPOTHESIS'], ['removable_lid', 'lid_handle'])],
    'bath_fill': [(['THERMO_A25_AC150_HYPOTHESIS'], ['calibration_copper_block'])],
    'cal_block': [(['THERMO_A25_AC150_HYPOTHESIS'], ['calibration_copper_block', 'immersion_RTD'])],
    'bath_ui': [(['THERMO_A25_AC150_HYPOTHESIS'], ['controller_key', 'controller_key.001', 'controller_key.002', 'controller_key.003', 'controller_key.004'])],
    'daq_terminals': [(['MCC_USB_TC'], ['pin_%02d'%n for pair in TC_CHANNEL_PINS for n in pair] + ['pin_%02d_wire_entry'%n for pair in TC_CHANNEL_PINS for n in pair] + ['pin_%02d_screw'%n for pair in TC_CHANNEL_PINS for n in pair])],
    'probe_attachment': [(['COOLER_THERMAL_MAP'], ['probe_contact_'+s[0] for s in SENSOR_LAYOUT])],
    'optical_access': [(['AGILENT_CARY_5000'], ['sample_lid','sample_front_door']), (['THERMO_NICOLET_6700'], ['sample_bay_lid'])],
    'optical_accessory': [(['AGILENT_CARY_5000'], ['sample_floor','DRA2500_body']), (['THERMO_NICOLET_6700'], ['sample_compartment_floor','IntegratIR_base'])],
    'ftir_connections': [(['THERMO_NICOLET_6700'], ['IntegratIR_detector_connector','IntegratIR_detector_cable','IntegratIR_purge_port'])],
    'optical_reference': [(['AGILENT_CARY_5000'], ['DRA2500_port_plug']), (['THERMO_NICOLET_6700'], ['IntegratIR_gold_reference','IntegratIR_reference_cap','IntegratIR_selector'])],
    'optical_sample': [(['AGILENT_CARY_5000'], ['DRA2500_sample_port']), (['THERMO_NICOLET_6700'], ['IntegratIR_18mm_sample_port'])],
    'solar_mount': [(['EKO_STR_32G'], ['selected_mount_plate','azimuth_mount','elevation_flange_-0.145','elevation_flange_0.145'])],
    'heater_wiring': [(['KEITHLEY_2425'], ['sense','sense.001','force','force.001'])],
    'smu_ui': [(['KEITHLEY_2425'], ['output_button','power'])],
    'daq_box': [(['MCC_USB_TC'], ['case','USB_B'])],
}

MISSING = {
    'carrier': 'Carrier handles, retention latches and station docks have no modeled fixture.',
    'stock': 'Stock rack, trays, unfinished blanks and replacement inventory need geometry.',
    'cutting': 'Selected cutting machines, stock fixtures, cutting paths and finishing tools need geometry; map recesses are a thermal-path-changing hypothesis.',
    'machine_ui': 'Water-jet model and actual control interface are unselected.',
    'coating': 'Spray can/nozzle, masking, coating support and compatible surface-preparation tools need geometry.',
    'base': 'Exact framing fastener and jig interfaces remain inferred.',
    'emitter': 'Edge gripper and reversible jig have not been fitted to the 0.5 mm copper disk.',
    'film': 'Ring jig, attachment tooling and membrane load-bearing qualification are absent.',
    'shield': 'Lead clearance and fasteners are not metrology qualified.',
    'reflector': 'Site/date track, actual locking mechanism and fastener fit remain unresolved.',
    'bath_lid': 'Actual lid handling clearance needs checking against installed controller.',
    'bath_fill': 'Drain, pouring vessel, liquid level and block cradle are not modeled.',
    'cal_block': 'Probe holes, immersion depths and block cradle require a fabrication drawing.',
    'bath_ui': 'AC150 controller is a selected variant; installed head is not historically established.',
    'daq_terminals': 'Terminal pitch is inferred; fine-wire transition and its retention/CJC effects require qualification.',
    'rtd_meter': 'Keithley2000, probe terminal configuration and compatible connectors are unmodeled.',
    'probe_attachment': 'Contact markers are inferred locations, not attachment/thermal qualification; insulation recesses and lead channels are not cut into the mesh.',
    'optical_access': 'Commercial cover hinge axes, travel limits and grasp regions require dimensional verification.',
    'optical_accessory': 'Exact holders/locators and all angular accessories remain unqualified or absent.',
    'ftir_connections': 'Selected DTGS detector interface and purge arrangement need actual-model checks.',
    'optical_reference': 'Angular reference/holder and DRA reference layout require verification.',
    'optical_sample': 'Witness carriers, clamps and angular sample holder are missing; full cooler is not a substitute.',
    'angle_controls': 'Harrick/SpectraTech variants and polarizer mounting/controls are unmodeled.',
    'acquisition_ui': 'Per-instrument software/button interface and input tool are not implemented.',
    'ambient_mount': 'Ambient RTD, ventilated shield and mast/fixture are absent.',
    'weather_mount': 'HOBO variant, sensor mounts and logger connectors are absent.',
    'solar_mount': 'MS-56/MS-402 sensor bodies, mounts and qualified tracker joints are absent.',
    'daq_box': 'Reflective enclosure, cable exits, mounting and strain relief are absent.',
    'metal_lids': 'Baseline lids, grasp regions and storage stands are absent.',
    'heater': 'Heater attachment and 50.8/50 mm fit conflict are unresolved; no fitted heater mesh.',
    'heater_wiring': 'Four-wire nodes/terminations and second independently controlled instrument instance require binding.',
    'smu_ui': 'Exact 2425 panel/actuation and per-channel controller interfaces are not qualified.',
    'storage': 'Storage supports, material containers and tool racks are absent.',
}


def build():
    ops = read('operations')['operations']
    parts = {v['id']: v for v in read('parts', ASSET)['parts']}
    interfaces = []
    for iid, (target, region, tool, support, constraint, recovery) in INTERFACES.items():
        variants = []
        for roots, suffixes in SELECT.get(iid, []):
            for root in roots:
                selected = [root+'__'+s for s in suffixes if root+'__'+s in parts]
                if selected:
                    variants.append(dict(root_id=root, part_ids=selected, instance_selection='Bind the current payload/instrument configuration; never choose all variants at once'))
        interfaces.append(dict(id=iid, target_role=target, contact_region=region, tool_role=tool,
            support_transition=support, preserve=constraint, recovery=recovery, asset_variants=variants,
            geometry_status='partial_named_geometry' if variants else 'unmodeled', remaining=MISSING[iid],
            execution_qualified=False))
    byid={i['id']:i for i in interfaces}
    write('interaction_contracts', dict(schema_version='sciencegym.cooling.manipulation.v1',
        visibility='trusted_author_evaluator', selection_semantics='Role templates must bind actual instance IDs. Reference actions are not observed outcomes.',
        interfaces=interfaces, parameter_card='manipulation_card', step_contract='operations.schema.json#/$defs/interaction'))
    bindings=[]
    for o in ops:
        ids=o['manipulation_interface_ids']
        selected=sorted({p for i in ids for v in byid[i]['asset_variants'] for p in v['part_ids']})
        bindings.append(dict(operation_id=o['id'], interface_ids=ids, part_selection=selected,
            binding_status='partial_review_links' if ids else 'nonmanual_context',
            unmodeled_interface_ids=[i for i in ids if not byid[i]['asset_variants']],
            robot_controller_implemented=False, collision_and_reachability_validated=False))
    write('asset_bindings', dict(schema_version='sciencegym.directional_cooling.v3', asset_package='../../assets/cooling_scene_assets_v2',
        interfaces='interaction_contracts.json', selector_rule='Only exact part IDs and explicitly enumerated variant roots; exploded display root is excluded',bindings=bindings))

    pinout=dict(source_id='USB_TC_MANUAL', source_locator='Rev10A Figure2 p8 and Table14 p17',
        wire_gauge_AWG_range=[16,30], probe_wire_AWG=36, probe_source_id='TC_DATASHEET',
        direct_probe_clamp_qualified=False, selected_reconstruction='Qualified K-compatible fine-wire transition to supported terminal-size extension; calibrate the complete path',
        terminals=[dict(pin=n,signal=s,part_id='MCC_USB_TC__pin_%02d'%n,wire_entry_part_id='MCC_USB_TC__pin_%02d_wire_entry'%n,screw_part_id='MCC_USB_TC__pin_%02d_screw'%n) for n,s in PIN_SIGNALS.items()],
        channels=[dict(channel=i,positive_pin=plus,negative_pin=minus) for i,(plus,minus) in enumerate(TC_CHANNEL_PINS)],
        geometry_basis='Figure/table pin topology; spacing and port shape are inferred, not manufacturer CAD',
        source_discrepancy='p8 prose says four rows with 26 connections each; Figure2 and Table14 enumerate 52 pins. Geometry follows the numbered diagram/table, with a CJC gap after pin10/36.')
    write('daq_terminal_contract',pinout)
    sensors=[]
    for probe,target,point,region,basis in SENSOR_LAYOUT:
        sensors.append(dict(probe_role=probe,target_part_id='COOLER_THERMAL_MAP__'+target,
            contact_part_id='COOLER_THERMAL_MAP__probe_contact_'+probe,region=region,
            position_from_insulation_bottom_m=list(point),position_in_asset_root_m=[point[0],point[1],point[2]+.0705],
            position_basis=basis,source_locator='SI Figure5 p6 / Note5 pp16-17',
            insertion_or_attachment_qualified=False))
    write('sensor_installation',dict(schema_version='sciencegym.cooling.sensor_installation.v1',
        source_geometry='Two-dimensional source cross section; azimuth, exact coordinates and attachment procedure are inferred',
        geometry_frame='COOLER_THERMAL_MAP; local X follows source cross section and Z points up; insulation bottom z=0.0705 m',
        sensor_count=7,sensors=sensors,
        warning='Contact markers do not qualify access, recess geometry, adhesive or lead heat conduction; the cutaway render removes front halves for inspection only.'))

    coverage=read('coverage_matrix')['items']
    branches=read('branches')['branches']
    from planner import compile_reference, fixture
    plan=compile_reference(fixture())
    routes=[]
    for b in branches:
        # Include stateful campaign transitions omitted from legacy membership.
        ids=list(dict.fromkeys(e['operation_id'] for e in plan['occurrences'] if e['branch_id']==b['id'])) or b['operation_ids']
        used=[o for o in ops if o['id'] in ids]
        routes.append(dict(branch_id=b['id'],source_obligation_ids=[v['id'] for v in coverage if b['id'] in v['branch_ids']],
            declared_operation_ids=b['operation_ids'], reference_campaign_operation_ids=ids,
            manipulation_step_ids=[s['id'] for o in used for s in o['reference_steps'] if 'interaction' in s],
            context_step_ids=[s['id'] for o in used for s in o['reference_steps'] if 'interaction' not in s],
            interface_ids=sorted({i for o in used for i in o['manipulation_interface_ids']})))
    write('manipulation_coverage',dict(schema_version='sciencegym.cooling.manipulation.v1',
        unit='step definitions, not attempts or independent experiments',
        branches=routes,operations=[dict(operation_id=o['id'],source_evidence_ids=o['evidence_ids'],
            manipulation_step_ids=[s['id'] for s in o['reference_steps'] if 'interaction' in s],
            scientific_context_step_ids=[s['id'] for s in o['reference_steps'] if 'interaction' not in s]) for o in ops]))

    # Readable complete action dossier; source locators and gaps remain next to
    # the task, rather than hidden behind aggregate step-count claims.
    prov=read('provenance')['evidence']
    lines=['# Cooling paper: manipulation review dossier','',
        'The full experimental sequence is retained. Manipulation steps describe physical work; perception, planning, waiting and analysis provide its conditions and checks. This is a reference design with zero execution observations.','',
        'Generated by `build_manipulation_contract.py` from authored JSON. Read [source inventory](source_inventory.json), [geometry gaps](interaction_contracts.json), [terminal map](daq_terminal_contract.json) and [sensor installation](sensor_installation.json).','',
        '## Experimental routes','']
    for r in routes:
        lines += ['- **'+r['branch_id']+'**: '+' → '.join('['+i+'](#'+i.lower().replace('_','-')+')' for i in r['reference_campaign_operation_ids'])]
    for o in ops:
        lines += ['', '## '+o['id'].replace('_',' '), '', '**'+o['title']+'**', '',
            'Station: `'+o['location_id']+'`. Prerequisites: '+(', '.join(o['depends_on']) or 'work-order inputs')+'.','',
            'Evidence: '+('; '.join(e+': '+prov[e]['locator'] for e in o['evidence_ids']) or 'Authored enabling work; no direct paper procedure is claimed')+'.','']
        for s in o['reference_steps']:
            lines += ['- **'+s['id']+' · '+s['capability']+'** — '+s['action'],
                '  Basis: `'+s['basis']+'`'+(' · `'+s['inference_id']+'`' if s.get('inference_id') else '')+'.',
                '  Completion observation: '+s['completion_observation']]
            if 'condition' in s:lines += ['  Applies when: '+s['condition']+'. Otherwise record an evidenced nonapplicable disposition.']
            if 'interaction' in s:
                d=s['interaction']
                lines += ['  Contact: '+d['contact_region']+'. Tool: '+d['tool_role']+'.',
                    '  Support: '+d['support_transition']+'.', '  Preserve: '+d['preserve']+'.',
                    '  Recovery: '+d['recovery']+'.']
        if o['manipulation_interface_ids']:
            lines += ['', '**Unresolved interaction geometry:**','']
            lines += ['- `'+i+'`: '+MISSING[i] for i in o['manipulation_interface_ids']]
        for loop in o.get('iteration_contracts',[]):
            lines += ['', 'Iteration `'+loop['id']+'`: '+loop['items']+'. Body: '+', '.join(loop['body_step_ids'])+'. '+loop['rule']+'.']
    (HERE/'MANIPULATION_REVIEW.md').write_text('\n'.join(lines)+'\n')
    update_revision_metadata()
    return dict(interfaces=len(interfaces),manual_steps=sum('interaction' in s for o in ops for s in o['reference_steps']),
        interfaces_with_partial_geometry=sum(bool(i['asset_variants']) for i in interfaces),
        interfaces_without_geometry=sum(not i['asset_variants'] for i in interfaces))


def update_revision_metadata():
    inputs=read('episode_input_contract')
    inputs['implemented_loader']=True
    inputs['loader']='episode_inputs.load'
    inputs['selected_simulation_profile']='selected_reconstruction.json'
    inputs['loader_scope']='Explicit inferred simulation choices with per-field provenance; no hardware qualification or physical-success receipts'
    inputs['cards']=[c for c in inputs['cards'] if c['id']!='manipulation_card']
    inputs['cards'].append(dict(id='manipulation_card',defaults=None,required_fields=[
        'object_instance_map','interface_to_instance_map','tool_and_fixture_ids',
        'contact_regions_and_approach_frames','support_and_retention_checks',
        'force_torque_clearance_limits','conditional_step_dispositions','bounded_recovery_policy']))
    for card in inputs['cards']:
        if card['id']=='calibration_card':
            card['required_fields']=list(dict.fromkeys(card['required_fields']+[
                'copper_block_hole_drawing','bath_fluid_and_fill_range','probe_to_channel_map',
                'probe_to_hole_map','fine_wire_transition_and_qualification','complete_connection_path_id']))
    write('episode_input_contract',inputs)
    resources=read('resources')
    resources['manipulation_interfaces']='interaction_contracts.json'
    resources['additional_reconstructed_materials']=[
        dict(id='calibration_block_stock',purpose='Fabricate probe holes explicitly through CAL_BLOCK_PREP',source_basis='E_CAL; dimensions and tooling inferred'),
        dict(id='fine_wire_transition',purpose='Join 36 AWG K probes to qualified DAQ-compatible conductors with strain relief',source_basis='E_TC_WIRE and E_DAQ_MANUAL; selected hardware remains a reconstruction input'),
        dict(id='bath_water_and_fill_vessel',purpose='Fill stationary bath with block displacement accounted for',source_basis='E_CAL and E_BATH_FILL'),
        dict(id='reversible_emitter_jig',purpose='Retain thin emitter during underside probe/heater work',source_basis='Reconstructed manipulation fixture; dimensions/load qualification required'),
    ]
    write('resources',resources)
    package=read('package')
    package['supporting_artifacts']['authored_cavity_checks']='../../assets/cooling_scene_assets_v2/geometry/interaction_checks.json'
    package['reconstruction_revision']='2026-10-17.manipulation.1'
    package['scope']['core_deliverable']='Full paper-derived experimental task chain with explicit manipulation and scientific conditions'
    package['scope']['context_steps']='Perception, planning, instrument processes, waits and data handling retain causal conditions; they are not credited as physical hand actions'
    package['scope']['scientific_result_agreement_required_for_manipulation_design']=False
    package['conversion_review']['status']='changes_required'
    write('package',package)
    review=read('review')
    review.update(date='2026-10-17',reconstruction_revision=package['reconstruction_revision'],
        base_commit='f7137685961e3828ad32bf7d399cefa8824b1d62',
        supersedes='review_history/2026-10-15/review.json',
        scope='Manipulation reconstruction and static interface consistency; no robot execution or scientific-result replication claim')
    messages={
        'PTR-01':('pass','Inspected source corpus and declared physical scope are traceable. Reused source reviews are pinned by byte hashes. Unavailable historical raw data limits result replication, not the task-chain scope.'),
        'PTR-02':('changes_required','Calibration block production, underside access and conditional accessory handling are explicit. Concrete fixture/tool selection and fine-grained component resource allocation remain incomplete.'),
        'PTR-03':('pass','Fixture walkthrough retains all 11 branches, explicit loops and configuration-bound angular references; invented fixture repeats remain distinct from historical repetitions.'),
        'PTR-04':('changes_required','Every manipulation step has a contact/tool/support/observation/recovery contract. Remaining interface-specific fixture and geometry decisions are enumerated; design does not require pre-existing joint trajectories.'),
        'PTR-05':('changes_required','Symbolic replay rejects omitted steps, stale references and invalid assembly revisions. Support, retention and contact predicates still need scene/instance qualification.'),
        'PTR-06':('pass','18 artifact roles plus explicit supporting manipulation artifacts resolve; exact step/interface/part links have schema and semantic checks.'),
        'PTR-07':('changes_required','Actor projection excludes reference manipulation artifacts. Observation evaluation and bounded alternative/recovery execution remain unimplemented.'),
        'PTR-08':('changes_required','Rebuilt source-topology terminals, LDPE thickness and seven inferred map contacts are reviewable. Missing fixture/equipment geometry and frozen explorer integration remain open.'),
    }
    for g in review['gates']:
        g['status'],g['remaining']=messages[g['id']]
        if g['id'] in ('PTR-02','PTR-04','PTR-06','PTR-08'):
            g['evidence']=list(dict.fromkeys(g['evidence']+['interaction_contracts.json','manipulation_coverage.json','MANIPULATION_REVIEW.md']))
    review['accepted_as_manipulation_template']=False
    inputs_to_pin=['operations.json','operations.schema.json','interaction_contracts.json','asset_bindings.json','daq_terminal_contract.json','sensor_installation.json','manipulation_coverage.json','source_inventory.json','episode_input_contract.json','package.json','../../assets/cooling_scene_assets_v2/parts.json']
    review['reviewed_inputs_sha256']={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in inputs_to_pin}
    write('review',review)


if __name__=='__main__':
    print(json.dumps(build(),indent=2))
