"""Build the paper-specific portable contract, never experimental observations."""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'directional_cooling_operations_v2'
ASSET=HERE.parents[1]/'assets/cooling_scene_assets_v2'
SCHEMA='sciencegym.directional_cooling.v3'
def get(n,base=HERE): return json.loads((base/(n+'.json')).read_text())
def put(n,d,base=HERE):
    base.mkdir(parents=True,exist_ok=True)
    (base/(n+'.json')).write_text(json.dumps(d,indent=2,ensure_ascii=True)+'\n')

EQUIPMENT=[
 ('COOLER','Custom paired directional cooler','SI Figure 1 / Note 2','BUILD_PAIR','custom_source_reconstruction',['COOLER_WHITE','COOLER_BLACK']),
 ('SMU','Keithley 2425','Main Methods: cooling power','PID_POWER','manual_reconstruction',['KEITHLEY_2425']),
 ('DAQ','Measurement Computing USB-TC','Main Methods: temperature','CALIBRATE','manual_reconstruction',['MCC_USB_TC']),
 ('BATH','Thermo Scientific ARCTIC A25','Main Methods: temperature','CALIBRATE','body_dimensions_with_AC150_head_hypothesis',['THERMO_A25_AC150_HYPOTHESIS']),
 ('DMM','Keithley 2000','Main Methods: temperature','CALIBRATE','unbuilt',[]),
 ('TC','Omega 5TC-TT-K-36-36','Main Methods: temperature','CALIBRATE','surface_routes_only',[]),
 ('REF_RTD','Omega P-M-A-1/4-3-1/2-PS-12','Main Methods: temperature','CALIBRATE','probe_envelope_only',[]),
 ('AMB_RTD','Omega P-L-A-1/4-6-1/4-T-6','SI Note 4','ENVIRONMENT','unbuilt',[]),
 ('HEATER','Omega KHR-2/2-P','Main Methods: cooling power','PID_POWER','unbuilt_pending_fit',[]),
 ('UVVIS','Agilent Cary 5000 with DRA-2500','Main Methods: optical properties','OPT_HEMISPHERICAL','manual_photo_reconstruction_with_inferred_accessory_details',['AGILENT_CARY_5000']),
 ('FTIR','Thermo Nicolet 6700 with PIKE Mid-IR IntegratIR','Main Methods: optical properties','OPT_HEMISPHERICAL','photo_reconstruction_with_inferred_envelope_and_DTGS_variant',['THERMO_NICOLET_6700']),
 ('ANGLE_12','Harrick Scientific 12 degree specular reflection accessory','SI Note 3','OPT_ANGULAR','exact_accessory_variant_unresolved',[]),
 ('ANGLE_VAR','Spectra-Tech variable-angle accessory','SI Note 3','OPT_ANGULAR','exact_accessory_variant_unresolved',[]),
 ('SOLAR_TRACKER','EKO STR-32G','Main Methods: solar measurement','ENVIRONMENT','manual_reconstruction_mount_inferred',['EKO_STR_32G']),
 ('DNI','EKO MS-56 pyrheliometer','Main Methods: solar measurement','ENVIRONMENT','unbuilt',[]),
 ('GTI','EKO MS-402 pyranometer','Main Methods: solar measurement','ENVIRONMENT','unbuilt',[]),
 ('WEATHER','Onset HOBO U30','SI Note 7','ENVIRONMENT','variant_unresolved',[]),
 ('WATERJET','Water-jet cutter; manufacturer not specified','Main Methods: solar-reflector tracking','BUILD_PAIR','qualified_machine_input_required',[]),
]
URL={
 'MAIN':'https://www.nature.com/articles/s41467-018-07293-9',
 'MAIN_PDF':'https://www.nature.com/articles/s41467-018-07293-9.pdf',
 'SI':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-018-07293-9/MediaObjects/41467_2018_7293_MOESM1_ESM.pdf',
 'SMU_SPEC':'https://download.tek.com/document/2425RevC_DocSpec.pdf',
 'SMU_SERVICE':'https://download.tek.com/manual/2425-902-01B_Oct2004_Service1.pdf',
 'SMU_USER':'https://download.tek.com/manual/2400S-900-01_K-Sep2011_User.pdf',
 'SMU_CAD':'https://download.tek.com/document/Keithley%202400%20Standard%20Series%20SMU.zip',
 'USB_TC_MANUAL':'https://files.digilent.com/manuals/USB-TC.pdf',
 'BATH_MANUAL':'https://documents.thermofisher.com/TFS-Assets/LED/manuals/D00167~.pdf',
 'UVVIS_BROCHURE':'https://www.agilent.com/cs/library/brochures/5990-7786EN_Cary-4000-5000-6000i-UV-Vis-NIR_Brochure.pdf',
 'FTIR_MANUAL':'https://knowledge1.thermofisher.com/@api/deki/files/4426/269-155800_-_Nicolet_FT-IR_User_Guide.pdf?revision=1',
 'TRACKER_MANUAL':'https://eko-instruments.com/wp-content/uploads/2024/08/str-series-manual.pdf',
 'HEATER_CATALOG':'https://in.omega.com/pptst/KHR_KHLV_KH.html',
 'PIKE_DTGS_MANUAL':'https://www.piketech.com/files/user-manuals/MidIntegratIRwDTGSManual.pdf',
 'FTIR_BROCHURE':'https://mmrc.caltech.edu/FTIR/Nicolet/Nicolet%206700%20brochure.pdf',
 'DMM_MANUAL':'https://download.tek.com/manual/2000-900_J-Aug2010_User.pdf',
 'CARY_DIMENSIONS':'https://www.agilent.com/cs/library/sitepreparationchecklists/8510128000_Cary_4000-5000-6000i-7000_Site_Prep.pdf',
}
def main():
    ops=get('operations')['operations'];branches=get('branches')['branches']
    put('dependencies',{'schema_version':SCHEMA,'edges':[{'from':p,'to':o['id']} for o in ops for p in o['depends_on']],
        'semantics':'Reusable operation-definition prerequisites. Concrete occurrences also require scoped state guards and explicit transport; branch lists are not self-contained executable schedules.',
        'state_contract':'state_contract.json','occurrence_compiler':'planner.py',
        'loops':[
            {'id':'coats','axis':'specimen,coat_index','cardinality':3,'basis':'E_BUILD','ordering':'one coat, inspect, supplied intercoat wait; final supplied cure'},
            {'id':'optical','axis':'material,instrument,technical_repeat','materials':['white','black','aluminum','nanoporous_PE','LDPE'],'instruments':['UVVIS','FTIR'],'repeats':'episode.optical_repeats'},
            {'id':'angular','axis':'paint,angle_deg,polarization,technical_repeat','paints':['white','black'],'angles_deg':[12,30,40,50,60,70,80],'polarizations':['s','p'],'repeats':'episode.optical_repeats'},
            {'id':'pid','axis':'target_index,device','targets':'episode.pid_targets_K_relative_ambient','devices':['white','black'],'duration_s':300,'summary_last_s':120},
            {'id':'tracking','axis':'observed_sun_position_or_supplied_schedule','count':None,'note':'No invented adjustment count from source plot'},
            {'id':'map','axis':'clear_day,clear_night,hazy_noon','duration_s':3600,'sensors':7},
        ]})
    provenance=get('provenance');provenance['review_date']='2026-10-15'
    provenance['source_ids'].update(URL)
    provenance['evidence']['E_DAQ_MANUAL']={'source_id':'USB_TC_MANUAL','locator':'p7 and p17','facts':'K thermocouples require configuration away from Type J default; 30 minute warm-up; actual channel terminal map','basis':'manufacturer_manual_text'}
    put('provenance',provenance)
    source=[]
    inspected={
        'MAIN_PDF':('cooling-main.pdf',8,'8fb6012487230f3417e2d88b80bb057a0d2c4573481f04cf431e94db5e47c0a2','All text and Figures 1-4 visually inspected'),
        'SI':('cooling-si.pdf',25,'61f8587c1b34a45072fac9b25591b89f1a1b00b212b61e9c29c41e2e73a340b3','All text and Figures 1-9 visually inspected'),
        'SMU_SPEC':('keithley2425-spec.pdf',None,'b0aae405607feaa032401ad123892e288be691428abf2778e186102d995b02d1','Dimension specification'),
        'SMU_SERVICE':('keithley2425-service.pdf',141,'f5b8f66225c33dd8f306d1e2332f3ac928186f7a9c0451e11fda37bd7f72c002','Model identity, assembly and service sections; not a full service audit'),
        'SMU_USER':('keithley2400-user.pdf',None,'4df96f3b6fcbae944aa009ee6d1277fee5d00bf28cdf9bed02c1280618b34e74','Front-panel Figure 1-1 p1-6 is explicitly a generic 2400 family illustration; applicability includes 2425'),
        'BATH_MANUAL':('a25-user.pdf',96,'043311452bcf294d4381043b073a4ff4229291577f9ca9968d674971c53cd063','A25 dimensions table p2-2 and controller options p2-1'),
        'UVVIS_BROCHURE':('cary5000-brochure.pdf',None,'34790bdaddbe19a3d1a601887f454c7d88a0cbd0a1cce66941f3394d9acc60ea','Retrieved; product and accessory manufacturer photographs inspected separately'),
        'FTIR_MANUAL':('nicolet6700-user.pdf',170,'0bd488af3213c5d68261feee2b48cc00bff740f42890a919b45450740af17e57','Selected sample/holder, reference and accessory replacement sections'),
        'TRACKER_MANUAL':('eko-tracker-user.pdf',66,'b14e45e8b020dacbdb749f6e80fe5947fe2976bfc714336306b1bf0b3434b9ca','STR-32G dimensions Figure 9-2 inspected; not confused with STR-21G above it'),
        'FTIR_BROCHURE':('nicolet6700-brochure.pdf',12,'404878f7877b7ea1147623d4a0ad2a206b234fc5e438b081a14d69dd026b5ce2','Thermo-authored brochure hosted by Caltech MMRC; cover and p2 instrument photos inspected'),
        'DMM_MANUAL':('keithley2000-user.pdf',256,'92f25c498ac86b9146944ea66796daf17dcaec153652c6ede27684050a9fe942','Front panel Figure 2-1 inspected; remainder not a full manual review'),
    }
    for ident,(file,pages,sha,review) in inspected.items():
        source.append({'id':ident,'url':URL[ident],'retrieved_file_name':file,'sha256':sha,'pages':pages,'access':'retrieved','review':review,'review_date':'2026-10-15','redistributed':False})
    source += [
        {'id':'PIKE_DTGS_MANUAL','url':URL['PIKE_DTGS_MANUAL'],'access':'web_tool_full_text','sha256':None,'pages':11,'review':'18 mm upward sample port, 3 inch sphere, model-specific mount, isolated detector connection, gold reference cap and selector; DTGS variant is a reconstruction choice','redistributed':False},
        {'id':'CARY_DIMENSIONS','url':URL['CARY_DIMENSIONS'],'access':'web_tool_text','sha256':None,'review':'Cary5000 envelope W1020 D710 H380 mm; newer site guide, not proof of every historical exterior detail','redistributed':False},
        {'id':'USB_TC_MANUAL','url':URL['USB_TC_MANUAL'],'access':'web_tool_full_text','sha256':None,'pages':19,'review':'Configuration p7, terminals p8/p17, dimensions p16; direct download returned 403','redistributed':False},
        {'id':'HEATER_CATALOG','url':URL['HEATER_CATALOG'],'access':'web_tool_text','sha256':None,'review':'KHR-2 diameter 2 inches; exact historical watt-density/part ordering needs confirmation','redistributed':False},
        {'id':'SMU_CAD','url':URL['SMU_CAD'],'sha256':'0265ca4b56b7170296f9855139bc74dccb33c50260351f2bb22f7bf356e02119','access':'retrieved_zip_directory_inspected','review':'Contains 2400/2410 STEP files, not 2425; rejected as exact-model CAD','redistributed':False},
    ]
    put('source_inventory',{'schema_version':SCHEMA,'sources':source,'main_text_and_SI_complete':True,
        'other_materials':{'peer_review':'Listed by publisher; no additional experimental procedure used','experimental_video':'No video listed in inspected article supplement list','raw_data':'Article says available on request; not requested or obtained','source_code':'No executable historical robot program supplied'},
        'limits':'A review statement describes only the sections actually inspected. Vendor sources are not all fully read. No source PDF is bundled.'})
    scope=[('MAIN_F1','Main Figure 1','theory','E_MAIN_MODEL',[]),('MAIN_F2','Main Figure 2 / construction and spectra','physical','E_BUILD',['BUILD_PAIR','OPT_HEMISPHERICAL']),('MAIN_F3','Main Figure 3 / paired stagnation','physical','E_STAG',['TRACKED_STAGNATION','ENVIRONMENT']),('MAIN_F4','Main Figure 4 / cooling power and model','mixed','E_POWER',['PID_POWER']),('SI_F1','SI Figure 1 / Note 2','physical','E_BUILD',['BUILD_PAIR']),('SI_F2','SI Figure 2 / Note 3','physical','E_ANGLE',['OPT_ANGULAR']),('SI_F3','SI Figure 3 / Note 4','physical','E_ENV',['ENVIRONMENT']),('SI_F4','SI Figure 4 / Note 5','theory','E_MODELS',[]),('SI_F5','SI Figure 5 / Note 5','mixed','E_MAP',['MAP_CLEAR_DAY','MAP_CLEAR_NIGHT','MAP_HAZY_NOON']),('SI_F6','SI Figure 6 / Note 6','physical','E_FIXED',['FIXED_LDPE']),('SI_F7','SI Figure 7 / Note 7','physical','E_ENV',['ENVIRONMENT']),('SI_F8','SI Figure 8 / Note 8','theory','E_MODELS',[]),('SI_F9','SI Figure 9 / Note 9','concept','E_MODELS',[]),('METHOD_CAL','Main Methods / temperature measurement','physical','E_CAL',['CALIBRATE']),('METHOD_SOLAR','Main Methods / solar measurement and tracking','physical','E_SOLAR',['BUILD_PAIR','ENVIRONMENT']),('SI_N1','SI Note 1 / diffuse-radiation calculation','theory','E_MODELS',[])]
    put('coverage_matrix',{'schema_version':SCHEMA,'items':[{'id':i,'source_locator':l,'classification':c,'evidence_id':e,'branch_ids':b,'disposition':'reconstructed_design' if b else 'nonphysical_model_or_concept_retained'} for i,l,c,e,b in scope],
        'denominators':{'major_physical_branch_definitions':11,'reviewed_figure_obligations':13,'additional_method_or_note_obligations':3,'operation_definitions':len(ops),'reference_substeps':sum(len(o['reference_steps']) for o in ops),'physically_executed_branches':0},
        'whole_paper_scientific_replication':False,'coverage_rule':'All physical families and nonphysical source obligations are mapped. This is design coverage, not execution or complete quantitative reproducibility.'})
    equipment=[{'id':i,'identity':n,'paper_locator':loc,'used_by_branch':b,'geometry_status':s,'scene_roots':r,'exact_serial_and_configuration_known':False,'physics_validated':False} for i,n,loc,b,s,r in EQUIPMENT]
    source_map={'SMU':['SMU_SPEC','SMU_SERVICE','SMU_USER','SMU_CAD'],'DAQ':['USB_TC_MANUAL'],'BATH':['BATH_MANUAL'],'DMM':['DMM_MANUAL'],'UVVIS':['UVVIS_BROCHURE','CARY_DIMENSIONS'],'FTIR':['FTIR_MANUAL','FTIR_BROCHURE','PIKE_DTGS_MANUAL'],'SOLAR_TRACKER':['TRACKER_MANUAL'],'HEATER':['HEATER_CATALOG'],'COOLER':['SI']}
    for e in equipment:e['researched_source_ids']=source_map.get(e['id'],[])
    put('resources',{'schema_version':SCHEMA,'equipment':equipment,'material_cards':'material_cards.json',
        'tools':[{'id':i,'purpose':p,'identity_basis':'selected_reconstruction','execution_requires_qualified_selection':True} for i,p in [('caliper','dimensions and layer inspection'),('film_jig','support fragile film edges and establish gap'),('supported_carrier','transport without touching optical surfaces'),('cutting_fixture','retain copper, PE, foam and acrylic blanks'),('fastener_driver','frame and accessory fasteners'),('wire_stripper_and_driver','retain, terminate and inspect sensor wiring'),('coating_station','support, mask, coat and cure disks'),('storage_supports','retain distinct accepted and rejected samples')]],
        'consumables':['copper sheet','aluminum sheet/tube','solid PE tube','FOAMULAR 150','Targray nanoporous PE separator','LDPE bag film','white and black Krylon ColorMaster','silver paste','aluminized Mylar','acrylic','sensor leads','fasteners','masking and cleaning supplies'],
        'allocation':'Minimum reconstruction: white and black assemblies, identified optical specimens, eight calibrated K probes (two emitters plus six map sensors), two independent 2425 channels/devices for simultaneous heating, one USB-TC can accommodate eight channels; actual instrument quantities and session reuse are supplied inputs.'})
    put('equipment_research',{'review_date':'2026-10-15','equipment':equipment,'source_inventory':'../../tasks/directional_cooling_operations_v3/source_inventory.json',
        'search_decisions':[{'equipment':'SMU','search':'Tek official CAD portal and Standard Series ZIP','result':'2400 and 2410 only; no exact 2425 in retrieved archive','decision':'Original manual-derived reconstruction; retain generic-family front-panel limitation'},
            {'equipment':'DAQ','search':'Old MCC manual URL then current Digilent product manual','result':'Old and direct download access failed; web tool provided manufacturer manual text','decision':'Use text dimensions and pin map; exterior visual fidelity still needs photographic comparison'},
            {'equipment':'BATH','search':'Thermo A25 manufacturer manual','result':'A25 dimensions found; paper does not name AC150/AC200 head','decision':'AC150 is a selected reconstruction, not asserted historical identity'},
            {'equipment':'UVVIS,FTIR,SOLAR_TRACKER','search':'Manufacturer product, accessory and manual pages','result':'Primary references obtained; Caltech mirror supplies Thermo-authored brochure photos','decision':'Original compartment/port/selector/mount reconstructions; unmeasured envelope and accessory dimensions remain inferred, with no fidelity certification'}],
        'license':'No vendor CAD, images or manuals redistributed. New procedural geometry is project-authored. Manufacturer trademarks identify devices, not endorsement.',
        'release_grade':'partial_visual_reconstruction_not_equipment_fidelity_accepted'},ASSET)
    dims=[('emitter_diameter',.05,'m','SI Note 2','source'),('emitter_thickness',.0005,'m','SI Note 2','source'),('foam_layer_thickness',.025,'m','SI Note 2, two layers','source'),('PE_support_ID',.076,'m','SI Note 2','source'),('PE_support_OD',.102,'m','SI Note 2','source'),('spacer_ID',.107,'m','SI Note 2','source'),('spacer_OD',.127,'m','SI Note 2','source'),('spacer_thickness',.0064,'m','SI Note 2','source'),('nanoporous_film_each',.000016,'m','SI Note 2','source'),('shield_ID',.14,'m','SI Note 2','source'),('shield_OD',.152,'m','SI Note 2','source'),('shield_height',.057,'m','SI Note 2','source'),('reflector_diameter',.06,'m','SI Note 2','source'),('track_stock_thickness',.0015,'m','Main Methods','source'),('fixed_band_width',.06,'m','SI Note 6','source'),('frame_inner_span',.305,'m','SI Figure 1a2 endpoints','source'),('reflector_plane_height',.15,'m','SI Note 2 selected over unresolved Figure 1a2 100 mm','inference_with_conflict'),('PE_support_height',.057,'m','Stack alignment reconstruction','inference'),('acrylic_base', [.305,.28,.006],'m','Photo proportions and selected stock','inference'),('frame_rail', [.02,.34,.02],'m','Photo-guided approximate extrusion; exact 80/20 profile unknown','inference'),('SMU_chassis',[.213,.370,.089],'m','2425 specification W,D,H','manufacturer'),('USB_TC_case',[.12852,.08839,.03556],'m','USB-TC manual p16 metric values; imperial column has a printed unit typo','manufacturer'),('A25_overall',[.273,.483,.749],'m','Thermo manual p2-2 W,D,H','manufacturer'),('A25_work_area',[.173,.184,.2],'m','Thermo manual p2-2 W,L,depth','manufacturer')]
    dims += [('Cary5000_envelope',[1.020,.710,.380],'m','Agilent site preparation guide p13','manufacturer'),('Nicolet6700_envelope',[.69,.655,.25],'m','Selected approximate envelope; manufacturer brochure photos support shape but no dimensional verification','inference'),('IntegratIR_sample_port',.018,'m','PIKE DTGS manual p1','manufacturer_selected_variant'),('STR32G_flange_span',.302,'m','EKO manual Figure 9-2 main-body flange span; appended sun sensor excluded','manufacturer')]
    put('dimensions',{'unit':'m','dimensions':[{'id':i,'value':v,'unit':u,'source_locator':s,'basis':b} for i,v,u,s,b in dims],
        'global_inference_rule':'Every dimension not explicitly source/manufacturer listed is a selected visual reconstruction: fasteners, port placement, track curve, frame supports, accessory offsets and wire routes. They are not metrology-ready.',
        'known_geometry_gaps':['Track shown is illustrative, not generated for a site/date; solar_geometry.py checks qualified samples separately','Fixed-band model currently retains generic PE visual material; LDPE thickness and separation must be configured','Heater and underside mounting/lead fit are not modeled','Full rooftop support, foil DAQ box and shielded ambient mast not yet modeled','Sensor wire endpoints are schematic; six precise map surface bindings remain to be implemented','The 107 mm spacer bore exceeds the 102 mm PE support outside diameter: the cover attachment/load path is not specified by the source and needs qualification, not invisible support geometry','Cary DRA accessory shape/ports inferred from photos; Nicolet envelope and selected DTGS variant require dimensional and historical verification'],
        'physics':'No mass, friction, contact, deformable-film, heat transfer or spectral-material validation'},ASSET)
    initial={'schema_version':SCHEMA,'objects':[
        {'id':'white','location':'WS_STOCK','supported':True,'configuration':'raw','assembly_revision':0,'qc_revision':None,'film_layers':0,'heater_output':False,'probe_calibration':None},
        {'id':'black','location':'WS_STOCK','supported':True,'configuration':'raw','assembly_revision':0,'qc_revision':None,'film_layers':0,'heater_output':False,'probe_calibration':None}],
        'stations':'station_contracts.json','raw_observations':[],'execution_records':[],
        'final_state':'All outputs verified off, payloads supported in named storage, retained/rejected materials accounted for, every selected occurrence assigned a disposition; scientific outcome may disagree with paper.'}
    put('initial_state',initial)
    for n in ['station_contracts','episode_input_contract','lineage_contract']:
        d=copy.deepcopy(get(n,OLD));d['schema_version']=SCHEMA;put(n,d)
    stations=get('station_contracts')
    for s in stations['stations']:
        if s['id']=='WS_FAB':s['role']='Explicit stock clamping, machine setup, supervised device cutting, unloading, finishing and dimensional inspection'
        if s['id']=='WS_COATING':s['role']='Supported disk preparation, masking, robot spray application, intercoat waiting and final cure inspection'
        if s['id']=='WS_UVVIS':s['role']='Cary5000 and DRA2500 compartment, specimen holder, reference ports and scan controls'
        if s['id']=='WS_OUTDOOR':s['role']='Paired supported devices, weather/solar/ambient instruments, protected DAQ and independently controlled four-wire heaters'
        s['asset_status']='partial_asset_binding_see_asset_bindings'
    put('station_contracts',stations)
    inputs=get('episode_input_contract')
    for card in inputs['cards']:
        card['required_fields']=[{'enclosed_service_settings':'qualified_machine_settings','resolved_source_ambiguity':'selected_geometry_and_unresolved_conflict_record'}.get(f,f) for f in card['required_fields']]
    inputs['source_temporal_constants']['USB_TC_warmup_s']=1800
    inputs['source_temporal_constants']['scope_notes']['USB_TC_warmup_s']='Manufacturer USB-TC manual p7; separate from article-reported timings'
    put('episode_input_contract',inputs)
    put('recovery',{'schema_version':SCHEMA,'rules':[
        {'trigger':'failed grasp or uncertain support','preserve':['last_observed_pose','support','attempt_id'],'action':'Stop dependent motion, observe support, secure a compatible carrier, then retry with a new bounded attempt'},
        {'trigger':'film tear or wrong layer count','preserve':['retired_film_ids','assembly_revision'],'action':'Support assembly, remove affected cover, install two identified layers, increment revision and repeat assembly inspection'},
        {'trigger':'probe detached or channel changed','preserve':['raw_trace','probe_identity','calibration_id'],'action':'Mark affected data invalid, reattach and check electrical/contact configuration; requalify calibration if probe/channel conditions invalidate it'},
        {'trigger':'device/reference/accessory changed','preserve':['last_reference_id','configuration_id','raw_spectra'],'action':'Mount and inspect the new accessory; acquire a valid new reference before sample measurement'},
        {'trigger':'heater output unknown or sensor feedback lost','preserve':['commands','readbacks','partial_trace'],'action':'Request output off, verify actual readback; remain blocked while output state is unknown'},
        {'trigger':'weather or shade not eligible','preserve':['session_id','timestamps','weather_stream'],'action':'Stop or pause the affected acquisition, retain partial intervals and schedule a new eligible session without inventing data'}],
        'retry_limit':'episode-supplied finite integer; not an infinite retry-until-success rule'})
    put('state_contract',{'schema_version':SCHEMA,'object_fields':['id','location','supported','configuration','assembly_revision','qc_revision','film_layers','heater_output','probe_calibration'],
        'invariants':['No unsupported transfer','No transfer of an energized heater','Outdoor acquisition requires current assembly inspection','Cover always contains two distinct accepted layers','Optical reference binds accessory/configuration and specimen class','Map has seven distinct sensor identities with declared surface relations','No source outcome can establish an observed success'],
        'invalidation':{'change_film_or_reflector':'increment assembly_revision; clear qc_revision','attach_heater_or_map_probe':'increment assembly_revision; clear qc_revision','change_probe_or_channel':'clear affected probe_calibration until requalified','change_optical_accessory':'clear optical reference'},
        'implementation':'planner.py implements a limited symbolic state/plan checker, not a physics runtime'})
    put('asset_bindings',{'schema_version':SCHEMA,'asset_package':'../../assets/cooling_scene_assets_v2','bindings':[
        {'operation_id':o['id'],'part_selection':{'FILM':['cover_lower','film_spacer','cover_upper'],'SHIELD':['radiation_shield','aperture_plate'],'EMITTER':['emitter_copper'],'BASE':['foam_1','foam_2','PE_support'],'REFLECTOR':['solar_reflector','reflector_carriage'],'TRACK_ADJUST':['solar_reflector','reflector_carriage'],'PID_CONFIG':['KEITHLEY_2425__output_button'],'CAL_MOUNT':['THERMO_A25_AC150_HYPOTHESIS__calibration_copper_block','MCC_USB_TC__case']}.get(o['id'],[]),
        'binding_status':'named_visual_parts_only' if o['id'] in {'FILM','SHIELD','EMITTER','BASE','REFLECTOR','TRACK_ADJUST','PID_CONFIG','CAL_MOUNT'} else 'unimplemented',
        'robot_controller_implemented':False,'collision_and_reachability_validated':False} for o in ops]})
    put('agent_visible',{'schema_version':SCHEMA,'goal':'Construct and characterize the allocated cooling devices and complete the selected experimental conditions; preserve valid observations irrespective of their scientific sign.',
        'allowed_input_fields':['selected_branches','allocated_specimens','qualified_parameter_cards','available_equipment','current_observations','public_device_interfaces'],
        'excluded_fields':['reference_steps','reference_plan','source_outcomes','hidden_state','future_records','inference_review','evaluator_predicates'],
        'projection_function':'planner.actor_projection','loader_scope':'Returns a fresh explicit allowlist projection; no hardware interface implemented'})
    put('evaluator_reference',{'schema_version':SCHEMA,'procedural_success':'All selected, expanded occurrences have valid observations, required state/resource lineage, and verified closeout. An ended attempt is insufficient.',
        'scientific_metrics':['emitter minus simultaneous ambient temperature','paired white/black difference with session and uncertainty','heater V*I divided by measured emitter area during valid last-120-second plateau interval','GTI minus DNI only when sun-normal, synchronized and compatible','spectra with accessory/reference and specimen provenance','seven-sensor post-equilibrium averages by actual condition'],
        'forbidden_success_shortcuts':['match a literature temperature','claim a completed macro','select an evidence category','count a render as manipulation','count a test fixture as a real episode'],
        'raw_record_contract':{'required':['record_id','occurrence_id','attempt_id','specimen_id','assembly_revision','calibration_ids','instrument_configuration_id','timestamp_interval','units','raw_file_sha256','quality_flags','processing_parent_ids'], 'files_must_exist':True},
        'implementation_scope':'Static package and symbolic planning validation only; no real acquisition adapter or observation verifier'})
    put('review',{'reviewer':'Codex author self-review; not independent approval','date':'2026-10-15','gates':[
        {'id':'PTR-01','status':'design_reviewed','evidence':['source_inventory.json','coverage_matrix.json'],'remaining':'Raw author data unavailable; no quantitative replication claim'},
        {'id':'PTR-02','status':'partial','evidence':['operations.json','resources.json','dependencies.json'],'remaining':'Qualified fixture/tool choices and commercial interface geometry remain incomplete'},
        {'id':'PTR-03','status':'design_reviewed','evidence':['branches.json','planner.py'],'remaining':'Historical repeats and PID targets are not reported; test work order must not become experiment default'},
        {'id':'PTR-04','status':'partial','evidence':['operations.json','reconstruction_inferences.json'],'remaining':'Reference actions are a reconstructed manipulation design, not low-level robot trajectories'},
        {'id':'PTR-05','status':'partial','evidence':['state_contract.json','recovery.json','planner.py'],'remaining':'Only selected symbolic invariants implemented; no contact simulation or physical recovery validation'},
        {'id':'PTR-06','status':'design_reviewed','evidence':['package.json','validate.py'],'remaining':'Interchange contract is scoped to this pilot revision'},
        {'id':'PTR-07','status':'partial','evidence':['agent_visible.json','evaluator_reference.json','tests/test_pilot.py'],'remaining':'Allowlist projection tested; real observation evaluator not implemented'},
        {'id':'PTR-08','status':'partial','evidence':['VERIFICATION.json','../../assets/cooling_scene_assets_v2/equipment_research.json'],'remaining':'Standalone review package; existing explorer stays on frozen v2. Equipment fidelity and whole-paper execution not accepted'}],
        'accepted_as_gold_standard':False,'scale_to_1000_authorized_by_this_review':False})
    rolefiles={'narrative':'TASK_DESIGN.md','source_inventory':'source_inventory.json','coverage':'coverage_matrix.json','resources':'resources.json','initial_state':'initial_state.json','operations':'operations.json','dependencies':'dependencies.json','branches_and_loops':'branches.json','reconstruction_inferences':'reconstruction_inferences.json','lineage':'lineage_contract.json','controls_and_repeats':'control_packages.json','recovery':'recovery.json','episode_inputs':'episode_input_contract.json','asset_bindings':'asset_bindings.json','actor_projection':'agent_visible.json','evaluator':'evaluator_reference.json','unknown_inputs':'unknown_parameters.json','verification':'VERIFICATION.json'}
    put('package',{'record_kind':'paper_task_package','authoring_contract':'sciencegym.paper_to_robot.v1','family_id':'directional_cooling','package_version':3,
        'paper_identity':{'title':provenance['title'],'doi':provenance['doi']},
        'scope':{'unit':'paper_level_task_family','declared_physical_program':[b['id'] for b in branches],'whole_paper_execution_validated':False,'excluded_or_incomplete_work':['Low-level controllers','Full commercial equipment geometry','Qualified site-specific operating inputs','Physical and scientific validation']},
        'planning':{'method':'goal_states_to_causal_dependencies_to_robot_operations','reference_route_is_unique_required_policy':False,'operation_definitions_are_execution_occurrences':False,'repeat_and_allocation_inputs':'episode_input_contract.json','initial_and_final_state_walkthrough':'reference_plan.json'},
        'artifact_roles':[{'role':r,'path':f,'schema':'markdown' if f.endswith('.md') else SCHEMA,'visibility':'actor_filtered_inputs_only' if r=='actor_projection' else 'trusted_author_evaluator'} for r,f in rolefiles.items()],
        'conversion_review':{'record_path':'review.json','required_gate_ids':['PTR-%02d'%i for i in range(1,9)],'status':'partial_not_gold_standard'},
        'viewer_projection':{'registered_family_key':None,'adapter_path':None,'actor_safe':False,'reason':'Pilot remains a standalone review revision; no explorer family added'},
        'freeze':{'physical_execution_validated':False,'actual_published_commit':None,'hash_manifest':'MANIFEST.sha256'}})
    print('Built 18 role mappings, %d equipment identities, %d source records'%(len(equipment),len(source)))

if __name__=='__main__':main()
