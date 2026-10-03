"""Independent original source-scope and design-boundary review checks."""
from pathlib import Path
import datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
rows=[]
def check(name,value):rows.append({'name':name,'passed':bool(value)})
branches=load('branches.json');bs={b['id']:b for b in branches['branches']}
ops=load('operations.json')['operations'];os={o['id']:o for o in ops};stations=load('station_contracts.json')['stations'];ss={s['id']:s for s in stations}
unknowns={u['id']:u for u in load('unknown_parameters.json')['unknowns']};evidence={e['id'] for e in load('provenance.json')['evidence']}
check('unique_branch_ids',len(bs)==len(branches['branches']))
check('unique_operation_ids',len(os)==len(ops))
check('branch_count_metadata',branches['branch_count']==branches['physical_branches']==len(bs))
check('all_services_have_six_phases',all(all(s['id'][3:]+'_'+phase in os for phase in ['LOAD','VERIFY','HANDOFF','READOUT','UNLOAD','COMMIT']) for s in stations if s.get('closed_service')))
for s in stations:
 if s.get('closed_service'):check('closed_boundary_'+s['id'],s['robot_scope']==['move','load','handoff','readout','unload'] and s['implemented'] is False and s['frame'] is None)
for o in ops:
 check('operation_contract_'+o['id'],o['station_id'] in ss and set(o['source_evidence_ids'])<=evidence and set(o['unknown_parameter_ids'])<=set(unknowns) and o['physical_execution_implemented'] is False and o['execution_mode']=='static_design_only' and o['actor']=='robot_carrier_handler_and_reader' and bool(o['failure_recovery']) and bool(o['preconditions']) and bool(o['postconditions']))
for b in bs.values():
 check('branch_contract_'+b['id'],b['execution_ready'] is False and b['expected_results_actor_visible'] is False and b['source_independent_specimens'] is None and set(b['operation_ids'])<=set(os) and set(b['source_evidence_ids'])<=evidence and set(b['unknown_parameter_ids'])<=set(unknowns) and all(b['condition_axes'].values()))
check('standalone_coupon_cure_retained','PREP_GEL_CURE' in bs['PREP_COUPON']['required_branch_ids'] and bs['PREP_GEL_CURE']['service_ids']==['GEL_CURE'])
check('all_inert_resist_variants_retained',set(bs['RESIST_COMPARISON']['condition_axes']['resist'])=={'gelatin_methacryloyl','DEGRAD_INX_N100','IP_S'})
check('three_d_source_material_IP_S',bs['THREE_D']['condition_axes']['resist']==['IP_S'])
check('incompatible_control_required','INCOMPATIBLE_CONTROL' in bs['SQUARE_LATTICES']['required_branch_ids'])
check('distinct_25_27_cycles',bs['LATTICE_CYCLES']['source_cycles']==27 and bs['IMAGE_CYCLES']['source_cycles']==25)
check('distinct_15_50_beams',bs['BEAM_LINEAGES']['condition_axes']['reported_beam']==['SI_Fig4_15mW','main_Fig3cd_50mW'])
check('scan_speed_no_invented_thermal_series',bs['BEAM_SPEED']['service_ids']==['AFM'])
check('spectral_material_subset',set(bs['HYDROGEL_TRANSMISSION']['condition_axes']['material'])=={'PNIPAM','LIHAM'})
check('spectral_temperature_context',set(bs['HYDROGEL_TRANSMISSION']['condition_axes']['reported_temperature_C'])=={25,60})
for key,required in {'material_controls':{'PREP_FORM','PREP_GEL_CURE','PREP_COUPON','HYDROGEL_CONTROLS','HYDROGEL_TRANSMISSION','MONOMER_SWEEP','COMPOSITION_SWEEP','RHEOMETRY'},'beam_controls':{'BEAM_AFM','BEAM_POWER','BEAM_SPEED','BEAM_LINEAGES'},'resist_comparison':{'RESIST_COMPARISON'},'cross_lattice':{'CROSS_MODES','SQUARE_LATTICES','INCOMPATIBLE_CONTROL','LATTICE_CYCLES'},'geometry_scales':{'TRIANGULAR','CIRCLES','ANISOTROPIC_GRID','THREE_D','MICRO_SCALE','MACRO_SCALE'},'power_image':{'POWER_IMAGE','IMAGE_CYCLES'},'angle_optics':{'POLAR_GRATING','ANGLE_IMAGE_MAIN','ANGLE_IMAGE_VIDEO'},'dual_encoding':{'DUAL_IMAGE'}}.items():check('source_program_'+key,required<=set(bs))
nonmanual=load('nonmanual_scope.json')['items'];check('numerical_analytic_fits_not_executed',all(x['executed'] is False for x in nonmanual) and {'N_FEA','N_ANALYTIC','N_FITS','N_UV_LITHOGRAPHY'}<={x['id'] for x in nonmanual})
cov=load('coverage_matrix.json');cr=cov['coverage'];check('coverage_53_records',len(cr)==cov['coverage_count']==53)
for prefix,n in [('MAIN_',6),('SI_',19),('ED_',4),('VIDEO_',9),('METHOD_',8),('DATA_',7)]:check('coverage_'+prefix,sum(x['id'].startswith(prefix) for x in cr)==n)
check('every_coverage_branch_exists',all(set(x['branch_ids'])<=set(bs) for x in cr))
check('four_ED_gaps_explicit',all(x['gap'] and x['disposition']=='caption_supported_visual_gap' for x in cr if x['id'].startswith('ED_')))
a=load('source_access_audit.json');check('audit_inspection_scope',a['main_figure_images_inspected']==6 and a['si_pages_inspected']==22 and a['si_figures_inspected']==19 and a['workbooks_parsed']==7 and a['video_count']==9 and a['frames_per_video']==8)
check('audit_visual_and_pdf_limits',a['extended_data_images_inspected']==0 and a['source_complete_for_entire_paper'] is False and a['main_pdf_acquired'] is False)
conf=load('source_conflicts.json')['conflicts'];check('ten_preserved_conflicts',len(conf)==10 and all(x['source_silent_correction_allowed'] is False for x in conf))
for cid,terms in {'C1':['20','50','Fig. 4l'],'C2':['3j','3.40847','9.607'],'C3':['metres'],'C4':['percent','solidity'],'C5':['16a','16b'],'C6':['85,000','12,400'],'C7':['10,000','27,000','27','25'],'C8':['--','features'],'C9':['flattening'],'C10':['20','18.88']}.items():
 text=json.dumps(next(x for x in conf if x['id']==cid)).lower();check('source_conflict_'+cid,all(t.lower() in text for t in terms))
actor=load('agent_visible.json');check('actor_no_future_or_source_targets',actor['source_targets_included'] is False and actor['future_measurements_included'] is False and actor['current_observations']==[] and actor['qualified_cards'] is None)
check('actor_forbids_chemical_actuation',set(['chemical_handling','UV_or_laser_actuation','fabrication_control','thermal_programming','writing_authority_maps'])<=set(actor['forbidden_actions']))
evalref=load('evaluator_reference.json');check('evaluator_separation',evalref['actor_files']==['agent_visible.json'] and evalref['production_authority_implemented'] is False and evalref['source_targets_are_acceptance_thresholds'] is False)
check('all_unknowns_remain_gated',all(u['execution_gate'] is True and u['default'] is None and u['status']=='unresolved' for u in unknowns.values()))
check('assets_not_implemented',load('asset_needs.json')['implemented_assets']==0)
check('no_universal_source_threshold',load('source_outcomes.json')['universal_acceptance_limits'] is False)
boundary=load('RELEASE_BOUNDARY.json');check('honest_release_boundary',boundary['physical_simulation_run'] is False and boundary['real_actuation_implemented'] is False and boundary['numerical_reproduction_run'] is False and boundary['publisher_assets_included'] is False and boundary['source_complete_for_entire_paper'] is False)
receipt={'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Original static source-audit alignment and closed-service contract checks; source media not independently reinspected','files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.json') if p.name not in ['STATUS.json','VERIFICATION.json','EXPORT_ALLOWLIST.json']},'checks':rows,'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows)}
(ROOT/'review/static_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'checks':len(rows),'passed':receipt['passed'],'failed':receipt['failed']}))
for r in rows:
 if not r['passed']:print(r['name'])
sys.exit(bool(receipt['failed']))
