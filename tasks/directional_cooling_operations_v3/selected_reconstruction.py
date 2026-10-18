"""Concrete simulation choices for missing paper details, with per-field origin.

This file selects a reconstructable manipulation scenario. Instrument processes
are external environment transitions; their synthetic outputs cannot validate
scientific reproduction or supply manipulation success receipts.
"""
from pathlib import Path
import json
import math

HERE=Path(__file__).resolve().parent

def read(name):return json.loads((HERE/(name+'.json')).read_text())

def selected(value,reason,source=None):
    return dict(value=value,origin='source' if source else 'inferred_selection',
                rationale=reason,source_locator=source,
                status='selected_for_simulation',hardware_qualified=False)


def build():
    cards={}
    def card(name,values):
        cards[name]={k:selected(*v) for k,v in values.items()}
    poses={s['id']:[2*(i%4),2*(i//4),0] for i,s in enumerate(read('station_contracts')['stations'])
           if s['id'] not in ['WS_TRANSFER','WS_ACTIVE','WS_OPTICAL_ACTIVE']}
    card('scene_card',dict(
        robot_limits=({'model':'Franka Panda','source':'simulation/cooling_v1/robot_source.json','joint_limits':'manufacturer URDF/MJCF','gripper_width_m':.08,'gravity_m_s2':9.81},'Use the pinned robot and its actual joint limits.'),
        station_frames=({'world_translations_m':poses,'local_table_height_m':.74,'axes':'x right, y away from robot, z up'},'Separate station workspaces; poses are layout selections, not the historical laboratory.'),
        grasps=({'source':'interaction_contracts.json','tools':['PANDA_STOCK_FINGERS','EDGE_JAWS_3MM','PASSIVE_BUTTON_PROBE','FILM_EDGE_FRAME','INSULATED_WIRE_GRIP','DRIVER_TORQUE_TOOL']},'Named contact regions are refined into task-specific approach frames by each physical workcell.'),
        docks=({'carrier_outer_m':[.38,.38,.025],'payload_retainer':'four adjustable corner stops and passive latch','release_requires':['three support contacts','latch closed','payload identity']},'A carrier retains the apparatus during transfers; release cannot be inferred from arrival alone.'),
        collision_routes=({'above_payload_m':.17,'maximum_lateral_segment_m':.025,'vertical_final_segment_m':.0005,'transport_between_stations':'external mobile-base motion; load and unload remain robot manipulation'},'Resolve manipulation locally and retain physical object identity across station handoffs.'),
        outdoor_weather_limits=({'wind_m_s_max':5,'precipitation_mm_h_max':0,'ambient_C_range':[5,40]},'Selected environment envelope for the simulation scenario; not a manufacturer outdoor rating.'),
        interlocks=({'machine_access':'output disabled and spindle/jet stationary before opening','electrical_transfer':'source output off and readback below 1 V','release':'support and retention observed','thermal_handling_C_max':40},'Explicit environment states precede physical access; they never prove the hand motion.')))
    card('allocation_card',dict(
        specimen_ids=(['white','black'],'Use distinct physical apparatus instances.'),
        lots=({'copper':'SIM_CU_01','white_paint':'SIM_WHITE_01','black_paint':'SIM_BLACK_01','nanoporous_PE':'SIM_NPPE_01','LDPE':'SIM_LDPE_01','foam':'SIM_XPS_01'},'Synthetic inventory identifiers preserve lineage without inventing historical batch numbers.'),
        condition_assignment=({'white':['tracked','power','fixed_LDPE','thermal_map'],'black':['tracked','power','fixed_LDPE']},'The mapping branch uses the white apparatus; preserve separate white/black identities.'),
        independent_specimen_count=(2,'One white and one black specimen in this selected demonstration, not an inference about the paper sample count.'),
        session_count=(8,'Calibration, optical and six outdoor sessions are separately identified.'),
        technical_repeats=(1,'One execution of each specified configuration is the nominal manipulation sample.'),
        reuse_policy=({'keep_ids':True,'configuration_change_increments_revision':True,'replace_consumed_films':True,'replace_removed_PSA_heater':True},'Do not relabel a newly created object as an earlier retained specimen.'),
        attempt_schedule=({'nominal':1,'recoverable_retry_max':1,'then':'stop dependent occurrence and preserve failure receipt'},'Bound recovery explicitly; failed attempts remain in the dataset.')))
    manifest={k:{a:b for a,b in v.items() if b is not None} for k,v in read('material_cards')['materials'].items()}
    manifest['pe_support']['selected_height_mm']=57
    manifest['disk_reflector']['selected_height_above_emitter_mm']=150
    card('fabrication_card',dict(
        part_manifest=(manifest,'Keep reported dimensions and append separately named reconstruction choices.'),
        drawing_revision=('COOLING_SIM_R1','Version the selected geometry independently of the source publication.'),
        actual_dimensions=({'PE_height_mm':57,'shield_shim_height_mm':6.9,'aperture_plate_mm':1,'copper_block_mm':[80,80,80],'RTD_bore_mm':6.6,'RTD_bore_depth_mm':78,'heater_diameter_mm':50.8},'Selected dimensions used by the workcells; these are design values, not measured manufactured parts.'),
        tolerances=({'rigid_part_mm':.1,'bore_diameter_mm':.05,'film_ring_concentricity_mm':.5,'stack_position_mm':2,'reflector_position_mm':1},'Explicit nominal inspection targets; each run must observe geometry before acceptance.'),
        qualified_machine_settings=({'kind':'simulated_device_process','hardware_qualified':False,'cutting':'enclosed water-jet process','fixture_hold_required':True,'completion_signal':'cut_complete_and_motion_stopped','physical_task':'load, clamp, close, operate controls, open, unclamp and unload'},'Internal cutting is a device process. No unreported nozzle pressure, feed rate or real-machine qualification is fabricated.'),
        coating_cure=({'coat_count':3,'intercoat_s':600,'final_cure_s':86400,'process_clock':'virtual environment clock','temperature_C':23,'application':'three separately logged spray passes'},'Three coats are reported; timing and ambient conditions are selected simulation assumptions.'),
        inspection=({'measure':['diameter','thickness','burr_free_edge','film_layer_count','port_clearance'],'disposition':['accept','rework','quarantine']},'Inspections observe the physical item, not the operation label.'),
        safe_release=({'machine_motion':False,'fixture_load_transferred':True,'temperature_C_max':40},'Release requires device isolation and an independently supported item.')))
    card('geometry_card',dict(
        component_join_map=({'foam_lower':'base','foam_upper':'foam_lower','emitter':'foam_upper','PE_tube':'base','lower_film':'cover_ring','upper_film':'cover_ring','cover':'PE_tube through lower membrane','shield':'three base shims','aperture':'shield','track':'frame clamps','reflector':'track carriage'},'An explicit support graph includes the membrane load path; the larger cover bore cannot rest directly on the PE rim.'),
        film_gap=({'ring_thickness_m':.0064,'nanoporous_sheet_m':.000016,'LDPE_sheet_m':.000050},'Two separate sheets enclose the reported spacer thickness.','SI Note 2; fixed-reflector section'),
        reflector_height_and_datum=({'height_m':.15,'datum':'emitter upper surface','disk_plane':'horizontal'},'Use the reported approximate separation as a concrete selected design datum.'),
        selected_geometry_and_unresolved_conflict_record=({'PE_height_m':.057,'aperture_m':.001,'shield_shims_m':.0069,'shield_alignment_pin_radius_m':.0805,'shield_alignment_radial_clearance_m':.0025,'heater_overhang_radial_m':.0004,'heater_policy':'retain full 50.8 mm commercial outline; support the 50 mm bonded area and keep the overhang free','thermocouple_policy':'0.3 mm deep local foam recess retains the rear-centre bead beneath the heater; no heater cutting','historical_cover_attachment':'unknown; selected permanent annular bond'},'Preserve source dimensions instead of silently resizing incompatible components; attachment and recess details are inferred.'),
        site_date_window=({'latitude_deg':42.3601,'longitude_deg':-71.0942,'timezone':'America/New_York','date':'2017-06-21','window':'solar_noon ± 2 h'},'A selected Cambridge summer scenario defines a track; it is not a claim about the paper measurement date.'),
        track_or_band_path=({'method':'solar_geometry.track_points','height_m':.15,'sample_cadence_s':60,'coordinate_frame':'east north up','track_stock_m':.0015,'band_width_m':.06,'input':'deterministic ephemeris for selected site/date'},'Both reflector paths derive from the same selected solar geometry; an illustrative curve is insufficient.'),
        shadow_acceptance=({'aperture_radius_m':.025,'reflector_radius_m':.03,'position_tolerance_m':.001,'solar_half_angle_deg':.2666,'check':'all aperture points shaded at all scheduled samples'},'Validate the geometric shadow independently of temperature or paper results.')))
    channel_map={'TC_W':0,'TC_B':1,**{'TC_MAP_'+str(i):i+1 for i in range(1,7)}}
    holes={'REF_RTD':[0,0],**{k:[.022*math.cos(i*math.pi/4),.022*math.sin(i*math.pi/4)] for i,k in enumerate(channel_map)}}
    card('calibration_card',dict(
        sensor_serials=({k:'SIM_'+k for k in channel_map},'Synthetic identities are not vendor serial numbers.'),
        reference_id=('SIM_OMEGA_PM_RTD_01','Use the exact paper model represented by assets/omega_pm_rtd_v1.'),
        bath_setpoints=([5,15,25,35],'Selected temperature states exercise loading, controls and retrieval; they do not reproduce historical readings.'),
        equilibrium_predicate=({'window_s':120,'slope_C_min_max':.02,'spread_C_max':.05},'Explicit simulated process gate; independent of manipulation acceptance.'),
        sample_cadence=(1,'Selected one-second process sampling.'),
        fit_method=('linear offset and slope regression against four-wire RTD','Source describes offset correction and propagation of slope error.','Main Methods: temperature measurement'),
        acceptance=({'synthetic_sensor_residual_C_max':.2,'physical_installation':'probe remains seated and cable retained after gripper release'},'Keep process checks separate from physical placement checks.'),
        validity=({'until':'sensor/connector path changes','identity':'sensor + extension + DAQ channel + calibration revision'},'Changing a lead or connector invalidates that path calibration.'),
        copper_block_hole_drawing=({'block_m':[.08,.08,.08],'positions_xy_m':holes,'RTD_bore_m':.0066,'RTD_depth_m':.078,'TC_bore_m':.001,'TC_depth_m':.065},'Paper reports a drilled isothermal block; bore sizes and arrangement are selected.'),
        bath_fluid_and_fill_range=({'fluid':'water','fill_depth_m':[.10,.13],'block_support':'retained bath basket','electrical_terminals_above_fluid_m_min':.03},'Water is reported; selected support and fill envelope keep wire terminations out of the bath.'),
        probe_to_channel_map=(channel_map,'Eight thermocouple channels receive two emitters and six additional map probes.'),
        probe_to_hole_map=({k:k for k in holes},'Each probe has a unique assigned bore.'),
        fine_wire_transition_and_qualification=({'probe_AWG':36,'extension_AWG':24,'transition':'K-compatible miniature connector with conductor-specific crimp contacts','direct_DAQ_clamp':False,'qualification':'whole-path synthetic calibration plus observed retention; no hardware qualification'},'The USB-TC accepts AWG16–30, so AWG36 cannot be treated as a qualified direct screw-terminal connection.'),
        complete_connection_path_id=('SIM_TC_PATH_R1','Version the complete probe–transition–extension–terminal path.')))
    card('optical_card',dict(
        sample_mount=({'coupon_diameter_m':.025,'sample_port_m':.018,'retention':'annular edge holder','film_frame':'two separate retained layers'},'A selected coupon covers the manufacturer-described FTIR sample port without grasping the optical centre.'),
        reference=({'FTIR':'gold reference cap','UVVIS':'instrument white reference'},'Use the device-specific reference and preserve its identity.'),
        scan_parameters=({'mode':'synthetic device process','FTIR_resolution_cm_1':4,'FTIR_scans':32,'UVVIS_step_nm':5},'Concrete simulated scan settings; no scientific result is inferred from completion.'),
        spectral_windows=({'UVVIS_nm':[300,2500],'FTIR_um':[2.5,25]},'Selected process windows cover the paper-relevant solar and infrared regions.'),
        angles=([12,30,40,50,60,70,80],'Use the paper angular configurations.','SI optical characterization'),
        polarizations=(['s','p'],'Keep polarizer configuration explicit.','SI optical characterization'),
        repeat_count=(1,'Nominal manipulation scenario uses one mount/scan/unload per configuration.'),
        processing_assumptions=({'output_origin':'synthetic','thermal_or_optical_reproduction_claim':False,'manipulation_success_uses_spectra':False},'Device outputs are observations of the simulated environment, never desired paper outcomes.')))
    card('outdoor_card',dict(
        site_coordinates=([42.3601,-71.0942],'Selected site in Cambridge; not the measured rooftop coordinates.'),
        timezone=('America/New_York','Use the selected site timezone and explicit UTC records.'),
        local_and_UTC_schedule=({'date':'2017-06-21','day':'solar_noon ± 2 h','night_local':['22:00','23:00'],'mapping_day':'solar_noon ± 30 min'},'Sessions are selected tasks; timestamps derive from the ephemeris and timezone.'),
        solar_noon=({'method':'minimize solar zenith over selected local date','time_step_s':1},'Compute instead of hard-coding noon to 12:00.'),
        orientation=({'x':'east','y':'north','z':'up','base_tilt_deg_max':.5},'The fixture frame must agree with the solar geometry frame.'),
        shadow_inspection=({'sample_period_s':60,'predicate':'full aperture occulted','reposition_if_margin_m_below':.001},'Check geometric shading rather than temperature sign.'),
        tracking_cadence=(60,'Selected one-minute carriage adjustments bound interpolation error.'),
        weather_eligibility=({'clear':'selected clear-sky environment','hazy':'selected diffuse-light environment','night':'sun elevation below 0 degrees'},'These are simulator condition assignments, not claimed historical weather measurements.'),
        abort_limits=({'wind_m_s':5,'rain_mm_h':0,'loss_of_retention':True},'Selected task envelope triggers a safe supported stop.')))
    card('acquisition_card',dict(
        channel_map=(channel_map,'Stable physical channel identities are shared with calibration.'),
        units=({'temperature':'degC','voltage':'V','current':'A','irradiance':'W/m2'},'Record units with every synthetic stream.'),
        sensor_geometry=({'source':'sensor_installation.json','RTD_asset':'assets/omega_pm_rtd_v1/interfaces.json'},'Use named contact regions and model-specific insertion datums.'),
        sampling_cadence_by_device=({'USB_TC_s':1,'Keithley2000_s':1,'Keithley2425_s':1,'weather_s':300},'Weather cadence is source-reported; other cadences are explicit selections.'),
        clock_sync_tolerance=(.1,'Selected maximum timestamp mismatch in seconds.'),
        raw_sink=('episode_artifacts/raw/','Store raw simulated outputs separately from physical receipts.'),
        missing_data_rule=({'mark_gap':True,'interpolate_for_acceptance':False,'stop_after_gap_s':10},'Do not silently replace missing observations.')))
    card('heater_card',dict(
        mount_receipt=({'requires':['full 50.8 mm outline inspected','0.4 mm radial overhang recorded','rear-centre probe retained','lead strain relief','released attachment support'],'receipt':'runtime-generated'},'A selected mount specification is not a successful attachment receipt.'),
        four_wire_port_graph=({'positive':['SMU_FORCE_HI','SMU_SENSE_HI','HEATER_NODE_A'],'negative':['SMU_FORCE_LO','SMU_SENSE_LO','HEATER_NODE_B'],'sense_tap':'heater-side ends of both 305 mm heater leads'},'Separate force and sense conductors meet at each heater node, not at the source meter.'),
        current_power_temperature_limits=({'current_A_max':.01,'power_W_max':.1,'temperature_C_max':40,'voltage_V_max':20},'Conservative selected simulated operating envelope; no hardware safety certification.'),
        independent_cutoff=({'state_model':'independent temperature switch','trip_C':40,'reset':'manual after output-off readback'},'A separate simulated device state must interrupt the circuit.'),
        strain_relief=({'clip_distance_from_lead_exit_m':.03,'service_loop_m':.05,'bend_radius_m_min':.003},'Route leads away from the thin emitter edge and provide a selected service loop.')))
    card('pid_card',dict(
        nonempty_targets=([-1,0,1],'Selected synthetic temperature offsets exercise all manipulation contexts.'),
        target_units=('K relative to ambient','Source uses ambient-relative cooling-power conditions.'),
        gains=({'Kp_W_K':.02,'Ki_W_K_s':.0001,'Kd_W_s_K':0,'antiwindup':True},'Selected process-model controller; no claim of apparatus tuning.'),
        step_duration_s=(300,'Use the paper plateau duration.','Main Figure 4 / SI power measurement'),
        summary_window_s=(120,'Use the final two minutes of the plateau.','Main Figure 4 / SI power measurement'),
        stability_predicate=({'window_s':120,'temperature_span_K_max':.1},'Selected synthetic process acceptance, excluded from manipulation scoring.'),
        compliance=({'power_W':[0,.1],'current_A_max':.01,'output_off_on_missing_sensor':True},'Bound the selected simulated source.'),
        controller_revision=('SIM_PID_R1','Keep process model revision distinct from robot controller revision.')))
    sensors=read('sensor_installation')['sensors']
    card('map_card',dict(
        seven_location_bindings=({s['probe_role']:s['target_part_id'] for s in sensors},'Preserve all seven distinct source-related contact roles.'),
        six_extra_sensor_coordinates=({s['probe_role']:s['position_from_insulation_bottom_m'] for s in sensors[1:]},'Coordinates are inferred from the source cross-section and separately marked in sensor_installation.json.'),
        attachment_tolerances=({'position_m':.001,'lead_pull_N_max':.05,'paste_patch_diameter_m':.002},'Selected contact-placement and retention limits for fine wires.'),
        equilibrium_predicate=({'temperature_slope_C_min_max':.02,'window_s':120},'Selected synthetic process gate.'),
        average_window_rule=({'window_s':120,'selection':'last complete stable interval after lid removal'},'Do not choose intervals by matching the paper temperature.'),
        one_hour_session_start_end=({'duration_s':3600,'clock':'session virtual UTC'},'One-hour mapping session is reported.','SI thermal mapping'),
        baseline_timing_within_total_session=({'baseline_s':[0,300],'baseline_in_total':True},'Five-minute baseline is explicitly inferred for mapping; source stagnation timing does not automatically transfer.'),
        open_lid_and_equilibrium_interval_selection=({'lid_remove_start_s':300,'settle_window_s':120,'remaining_interval':'after successful release and equilibrium until t=3600'},'Actual manipulation duration is included in the one-hour session.')))
    card('analysis_card',dict(
        emitter_area_m2=(math.pi*.025**2,'Area follows the reported 50 mm emitter; not the 50.8 mm heater.'),
        units=({'cooling_power':'W/m2','temperature_offset':'K'},'Explicit output units.'),
        interval_selection=('predeclared stable windows','Keep reporting choices independent of the desired scientific result.'),
        invalid_interval_policy=('retain raw stream and mark invalid','Missing evidence never becomes a successful manipulation.'),
        uncertainty_budget=({'kind':'simulation metadata only','physical_sensor_calibration_available':False},'Do not fabricate measured uncertainty for a simulated task.'),
        ambient_equal_estimate_rule=('interpolate between bracketing synthetic PID points; no extrapolation','A deterministic reporting rule, outside manipulation scoring.'),
        diffuse_geometry_rule=('sun-normal GTI minus DNI only','Require aligned geometry before subtraction.')))
    card('cleanup_card',dict(
        safe_temperature=(40,'Selected maximum handling temperature in degrees Celsius.'),
        isolation_readback=({'source_output':False,'terminal_voltage_V_max':1,'machine_motion':False},'Read observed device state before disconnecting or unloading.'),
        storage=({'coolers':'identified retained carrier','probes':'individual sheath cradles','reference':'capped optical reference box','witnesses':'separate labeled slots'},'Each returned object has a named support and identity.'),
        residue_cleaning=({'tool':'lint-free swab held by gripper','solvent':'none in nominal simulation','contact_force_N_max':1},'A selected dry-cleaning manipulation avoids inventing chemistry compatibility.'),
        waste_routes=({'used_PSA':'adhesive bin','used_films':'polymer bin','metal_offcuts':'metal bin','rejected_parts':'quarantine tray'},'Track each consumed or rejected object by identity.')))
    card('manipulation_card',dict(
        object_instance_map=({'white_prefix':'W_','black_prefix':'B_','shared_devices':'station-scoped persistent IDs','no_rename_on_transfer':True},'The same object persists through loading, manipulation and return.'),
        interface_to_instance_map=({'contract':'interaction_contracts.json','resolution':'station + payload identity + interface role','unresolved_instance':'execution error'},'A role name alone is not a physical binding.'),
        tool_and_fixture_ids=(['PANDA_STOCK_FINGERS','EDGE_JAWS_3MM','PASSIVE_BUTTON_PROBE','FILM_EDGE_FRAME','INSULATED_WIRE_GRIP','DRIVER_TORQUE_TOOL','RTD_STAND','COPPER_CAL_BLOCK','RETAINED_CARRIER'],'Selected tools expose their geometry, inertia and contact limits in workcell models.'),
        contact_regions_and_approach_frames=({'source':'operations.json/reference_steps/manipulation','RTD_stand_grip_yaw_rad':0,'RTD_block_retrieval_yaw_rad':math.pi/2,'cover_grip_local_m':[0,-.0595,0],'shield_grip_local_m':[0,-.073,.0085],'edge_jaw_thickness_m':.002,'edge_tip_height_m':.003},'Use observation and station-specific approach frames to keep wires clear of closing jaws.'),
        support_and_retention_checks=({'vertical_load_fraction_min':.8,'rigid_speed_m_s_max':.03,'rigid_tilt_rad_max':.035,'cover_tilt_rad_max':.012,'no_finger_contact_after_release':True,'recheck_retained_parts':True},'Support is measured from contact forces after release, not asserted by the action name.'),
        force_torque_clearance_limits=({'unintended_arm_force_N_max':2,'foam_grip_N':.8,'emitter_grip_N':12,'PE_tube_grip_N':14,'shield_grip_N':32,'aperture_grip_N':18,'RTD_grip_N':8,'nominal_rigid_clearance_m':.002},'Selected simulation controller limits; contact damage of physical materials remains uncalibrated.'),
        conditional_step_dispositions=({'performed':'physical receipt','not_applicable':'observed condition and justification','failed':'failure trace','unimplemented':'explicit incomplete status'},'No branch or repeated occurrence receives credit from another branch automatically.'),
        bounded_recovery_policy=({'max_retries':1,'allowed':['retract to clear pose','reobserve','regrasp with declared alternative frame'],'forbidden':['teleport payload','change collision mask to suppress fault','erase failure trace']},'Recovery remains physical and is recorded as an additional attempt.')))
    required={c['id']:set(c['required_fields']) for c in read('episode_input_contract')['cards']}
    assert set(cards)==set(required)
    for name in cards:assert set(cards[name])==required[name],(name,set(cards[name])^required[name])
    return dict(schema_version='sciencegym.selected_reconstruction.v1',id='COOLING_MANIPULATION_SIM_R1',
                doi='10.1038/s41467-018-07293-9',scope='Concrete simulation inputs for paper-derived manipulation tasks',
                whole_paper_physics_validated=False,hardware_qualified=False,
                inferred_values_are_source_facts=False,cards=cards)


if __name__=='__main__':
    profile=build();(HERE/'selected_reconstruction.json').write_text(json.dumps(profile,indent=2)+'\n')
    print('Selected',sum(map(len,profile['cards'].values())),'fields across',len(profile['cards']),'cards')
