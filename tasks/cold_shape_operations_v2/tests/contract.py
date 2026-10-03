"""Original static/synthetic contract checks. No physical model or live-device API."""
import json
import datetime
import itertools
import math
import pathlib
import re

DOI='10.1038/s41467-023-41170-4'
SCHEMA='cold_shape_paper_task.v1'
class ContractError(ValueError): pass
def check(value,message):
    if not value: raise ContractError(message)
def text(v): return isinstance(v,str) and bool(v.strip())
def finite(v): return type(v) in (int,float) and math.isfinite(v)
def unique_ids(items,label):
    out=[x['id'] for x in items]
    check(len(out)==len(set(out)),'duplicate '+label)
    return set(out)
def load(root): return {p.name:json.loads(p.read_text()) for p in pathlib.Path(root).glob('*.json')}
def validate_package(d):
    required={'operations.json','branches.json','provenance.json','source_access_audit.json','source_conflicts.json','unknown_parameters.json','episode_input_contract.json','coverage_matrix.json','nonmanual_scope.json','dependencies.json','transport_routes.json','material_cards.json','station_contracts.json','lineage_contract.json','state_contract.json','agent_visible.json','evaluator_reference.json','mock_contract.json','source_outcomes.json','STATUS.json','condition_requirements.json'}
    check(required<=d.keys(),'missing contract')
    for name,obj in d.items():
        check(obj.get('doi')==DOI,'wrong DOI '+name)
        if name not in {'EXPORT_ALLOWLIST.json','VERIFICATION.json'}:check(obj.get('schema_version')==SCHEMA,'wrong schema '+name)
    ops=d['operations.json']['operations']; bs=d['branches.json']['branches']
    oids=unique_ids(ops,'operation'); bids=unique_ids(bs,'branch')
    unknowns=d['unknown_parameters.json']['unknowns']; uids=unique_ids(unknowns,'gate')
    ev=set(d['provenance.json']['evidence']); sts=d['station_contracts.json']['stations']; sids=unique_ids(sts,'station')
    check(len(ops)==d['operations.json']['operation_count']==76,'operation count')
    check(len(bs)==d['branches.json']['branch_count']==32,'branch count')
    check(len(uids)==19 and all(x['default'] is None for x in unknowns),'gate defaults')
    cards=d['episode_input_contract.json']['cards']
    check(len(cards)==len(uids) and {x['unknown_id'] for x in cards}==uids and len({x['id'] for x in cards})==len(cards),'missing or duplicate input card')
    for c in d['episode_input_contract.json']['cards']:
        check(c['unknown_id'] in uids and c['required_fields'] and c['defaults'] is None,'input card')
    sm={s['id']:s for s in sts}
    for o in ops:
        check(o['station_id'] in sids|{'BETWEEN'},'station reference')
        if o['station_id']!='BETWEEN':check(o['interface_port'] in {p['id'] for p in sm[o['station_id']]['ports']},'port reference')
        check(set(o['source_evidence_ids'])<=ev,'operation evidence')
        check(set(o['unknown_parameter_ids'])<=uids,'operation gate')
        for k in ['preconditions','postconditions','objects','robot_actions']:check(bool(o[k]),'empty operation '+k)
        for k in ['source_fact','authored_translation','observable_completion','failure_recovery']:check(text(o[k]),'missing operation '+k)
        check(o['execution_mode']=='static_design_only','execution promotion')
        for obj in o['objects']:check(obj['identity_required'] and obj['version_required'] and text(obj['before_state_requirement']) and text(obj['after_state_evidence']),'object state binding')
        if o['kind']=='service_autonomous':check(o['actor']=='qualified_closed_service' and o['service_process'],'unsafe actor boundary')
    om={o['id']:o for o in ops}; bm={b['id']:b for b in bs}
    def visit(i,path):
        check(i not in path,'branch cycle')
        for p in bm[i]['required_branch_ids']:visit(p,path|{i})
    for b in bs:
        check(b['operation_ids'] and set(b['operation_ids'])<=oids,'branch operations')
        check(set(b['source_evidence_ids'])<=ev,'branch evidence')
        check(set(b['required_branch_ids'])<=bids,'branch dependency')
        direct={u for i in b['operation_ids'] for u in om[i]['unknown_parameter_ids']}
        check(direct<=set(b['direct_unknown_parameter_ids'])<=set(b['unknown_parameter_ids'])<=uids,'branch gate omission')
        for p in b['required_branch_ids']:check(set(bm[p]['unknown_parameter_ids'])<=set(b['unknown_parameter_ids']),'ancestor gate omission')
        visit(b['id'],set())
        check(b['phase_order'] and b['source_independent_sample_count'] is None,'phase/replicate invention')
    check(set(d['branches.json']['mandatory_physical_campaign_branches'])==bids,'campaign omission')
    cov=d['coverage_matrix.json']; mapped={r['source_scope_id']:r for r in cov['source_to_design']}
    check(set(mapped)=={f'P{i:02}' for i in range(19)}|{'N01','N02','N03','X01'},'source coverage omission')
    check({r['branch_id'] for r in cov['physical_coverage']}==bids,'physical coverage omission')
    for r in cov['physical_coverage']:check(r['operation_ids']==bm[r['branch_id']]['operation_ids'],'coverage drift')
    nums=d['nonmanual_scope.json']['items']; nids=unique_ids(nums,'nonmanual')
    check(len(nums)==6 and all(n['status']=='specified_not_run' and not n['physical_operation_ids'] for n in nums),'model promotion')
    check(not d['nonmanual_scope.json']['promotion_to_physical_evidence_allowed'],'model evidence promotion')
    allids=bids|nids|{x['id'] for x in d['nonmanual_scope.json']['excluded']}
    check(all(set(r['design_ids'])<=allids for r in mapped.values()),'coverage unknown design')
    for e in d['dependencies.json']['service_phase_edges']:check(e['source'] in oids and e['target'] in oids,'service edge')
    loops=d['dependencies.json']['loops'];check(len(loops)==7,'loop inventory')
    check({l['id']:l['count'] for l in loops}['L_TEN']==10 and {l['id']:l['count'] for l in loops}['L_FORTY']==40,'cycle scope')
    unique_ids(d['transport_routes.json']['routes'],'transport route')
    for r in d['transport_routes.json']['routes']:check(r['from_station'] in sids and r['to_station'] in sids and r['operation_id']=='MOVE' and r['geometry'] is None,'transport')
    check(bm['ELECTRONIC_STRIP']['conditions']['resistance_invariance_claim'] is False,'invented electrical metric')
    check(bm['ALT_RESIN_BATCH']['conditions']['primary_additives_inherited'] is False,'alternative recipe substitution')
    check(bm['FABRICATE']['conditions']['post_cure_default'] is None,'generic postcure')
    check(bm['HINGE_ANGLE_FORCE']['conditions']['source_angle_error_bar_experiments']==5,'n5 scope')
    check(bm['MEMORY_TEN_CYCLES']['conditions']['does_not_inherit_hot_or_cold_schedule'],'cycle recipe inheritance')
    check(bm['TENSILE_HOT']['conditions']['stress_axis_source_unit']=='kPa','source unit rewrite')
    actor=d['agent_visible.json'];check(actor['public_file_allowlist']==['agent_visible.json'] and not actor['loader_implemented'],'actor file allowlist')
    check({'source_outcomes.json','evaluator_reference.json','future_measurements','hidden_fault_schedule'}<=set(actor['forbidden_inputs']),'actor leakage protection')
    check(not set(actor['forbidden_inputs'])&set(actor['public_inputs']),'actor leaks')
    check(d['source_outcomes.json']['not_actor_input'],'outcome leak')
    check({c['id'] for c in d['source_conflicts.json']['conflicts']}=={'C_TC','C_LATTICE','C_HOT_UNIT','C_ALT_LABEL'},'source conflict omission')
    s=d['STATUS.json']
    for k,v in [('operation_count',len(ops)),('physical_branch_count',len(bs)),('unknown_gate_count',len(uids)),('nonmanual_disposition_count',len(nums)),('loop_count',len(loops)),('transport_route_count',len(d['transport_routes.json']['routes']))]:check(s[k]==v,'status count mismatch '+k)
    cr=d['condition_requirements.json']['branches'];check(len(cr)==len(bs) and {x['branch_id'] for x in cr}==bids,'condition inventory')
    for k in ['physical_recipe_complete','scene_built','physical_simulation_run','robot_execution_run','real_device_actuation','public_write_performed']:check(s[k] is False,'unearned claim '+k)
    audit=d['source_access_audit.json']['read_scope'];check(audit['SI_pages']==20 and audit['movie_bytes']==0 and not audit['source_workbook'],'source overclaim')
    return {'operations':len(ops),'physical_branches':len(bs),'gates':len(uids),'nonmanual':len(nums),'loops':len(loops),'transport_routes':len(d['transport_routes.json']['routes'])}

def validate_plan(plan,d):
    bm={b['id']:b for b in d['branches.json']['branches']}
    check(plan.get('mode') in {'selected_episode','whole_paper'},'mode')
    selected=plan.get('branch_ids');check(isinstance(selected,list) and selected and len(selected)==len(set(selected)) and set(selected)<=bm.keys(),'selected branches')
    if plan['mode']=='whole_paper':check(set(selected)==set(bm),'selected episode cannot claim whole paper')
    for bid in selected:
        b=bm[bid]; cards=plan.get('gate_cards',{})
        for u in b['unknown_parameter_ids']:
            c=cards.get(u,{})
            check(c.get('gate_id')==u and c.get('status')=='qualified' and text(c.get('qualification_receipt')) and text(c.get('revision')),'unresolved gate '+u)
            schema=next(x for x in d['episode_input_contract.json']['cards'] if x['unknown_id']==u)
            payload=c.get('payload',{})
            check(isinstance(payload,dict) and all(k in payload and payload[k] is not None and payload[k]!=[] and payload[k]!='' for k in schema['required_fields']),'incomplete card payload '+u)
        cells=plan.get('conditions',{}).get(bid)
        check(isinstance(cells,list) and cells and all(isinstance(x,dict) and text(x.get('id')) for x in cells),'empty/invalid schedule')
        check(len({x['id'] for x in cells})==len(cells),'duplicate schedule')
        cr=next(x for x in d['condition_requirements.json']['branches'] if x['branch_id']==bid)
        dims=cr['required_dimensions']; names=list(dims)
        expected=set(itertools.product(*(dims[k] for k in names))) if names else {()}
        actual={tuple(x.get(k) for k in names) for x in cells}
        check(expected<=actual,'missing reported condition dimension')
        for rule in d['condition_requirements.json']['conditional_requirements']:
            if rule['branch_id']==bid:
                subset=[x for x in cells if all(x.get(k)==v for k,v in rule['if'].items())]
                check(set(rule['values'])<={x.get(rule['dimension']) for x in subset},'missing conditional subseries')
        check(plan.get('phase_schedules',{}).get(bid)==b['phase_order'],'missing or reordered scientific phases')
        n=plan.get('replicate_counts',{}).get(bid)
        check(type(n) is int and n>0,'invalid repeat count')
        if b['source_cycles'] is not None:check(plan.get('cycles',{}).get(bid)==b['source_cycles'],'wrong cycle count')
    check(type(plan.get('retry_limit')) is int and plan['retry_limit']>=0,'retry bound')
    return True

PHASES=['prepared','loaded','verified','requested','acknowledged','completed','safe_to_unload','unloaded','committed']
def validate_service_trace(events,expected_job,expected_sample):
    check(isinstance(events,list) and len(events)==len(PHASES),'service event count')
    check([e.get('phase') for e in events]==PHASES,'service phase order')
    check(len({e.get('receipt_id') for e in events})==len(events),'reused service receipt')
    for i,e in enumerate(events):
        check(e.get('synthetic') is True,'fixture must be synthetic')
        check(e.get('job_id')==expected_job and e.get('sample_id')==expected_sample,'job/sample mismatch')
        check(type(e.get('sequence')) is int and e['sequence']==i,'service sequence')
        check(text(e.get('receipt_id')),'missing service receipt')
        if e['phase'] in {'loaded','verified','requested','acknowledged','completed'}:check(e.get('guard_closed') is True,'guard open')
        if e['phase']=='verified':check(e.get('qualified') is True and text(e.get('program_hash')),'unqualified program')
        check(e.get('program_hash')==events[2].get('program_hash') and text(e.get('program_hash')),'program changed after verification')
        if e['phase'] in {'safe_to_unload','unloaded','committed'}:check(e.get('stored_energy_released') is True and e.get('safe_to_handle') is True,'unsafe release')
    return True

def validate_record(r,context,allow_synthetic=False):
    check(allow_synthetic,'Live authentication/runtime is not implemented')
    check(r.get('synthetic') is True,'unlabeled mock')
    check(r.get('data_class')=='measurement_raw','not measured raw data')
    required=['record_id','sample_id','version','branch_id','condition_key','phase','attempt_id','raw_sha256','calibration_id','setup_signature','receipt_id','timestamp_utc']
    check(all(text(r.get(k)) for k in required),'missing raw field')
    check(re.fullmatch('[0-9a-f]{64}',r['raw_sha256']) is not None,'hash')
    check(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',r['timestamp_utc']) is not None,'time')
    try: datetime.datetime.strptime(r['timestamp_utc'],'%Y-%m-%dT%H:%M:%SZ')
    except ValueError: raise ContractError('impossible timestamp')
    check(context['objects'].get(r['sample_id'])==r['version'],'stale or invented specimen')
    check(r['sample_id'] not in context.get('consumed',[]),'consumed specimen reused')
    check(context['calibrations'].get(r['calibration_id'])==r['setup_signature'],'calibration mismatch')
    check(r['condition_key'] in context['conditions'].get(r['branch_id'],[]),'undeclared condition')
    check(r['phase'] in context['phases'].get(r['branch_id'],[]),'undeclared phase')
    check(r.get('quality') in {'accepted','rejected','incomplete'},'quality')
    check(finite(r.get('temperature_C')),'nonfinite temperature')
    check(r.get('material_variant')==context['materials'][r['sample_id']],'material substitution')
    check(not r.get('source_outcome_substituted',False),'literature outcome substituted')
    if r['branch_id']=='ELECTRONIC_STRIP':check(r.get('observable')=='qualitative_LED_state','unsupported electrical inference')
    return True

def validate_cycle_history(records,count,sample_id):
    check(type(count) is int and count>0,'cycle count')
    check(len(records)==count and [x.get('cycle_index') for x in records]==list(range(1,count+1)),'missing/duplicate cycles')
    receipt_ids=[r.get(k) for r in records for k in ['program_receipt','release_receipt','recovery_receipt','integrity_receipt']]
    check(all(text(x) for x in receipt_ids) and len(receipt_ids)==len(set(receipt_ids)),'replayed cycle receipt')
    for r in records:
        check(r.get('sample_id')==sample_id,'cycle specimen substitution')
        check(r.get('program_receipt') and r.get('release_receipt') and r.get('recovery_receipt') and r.get('integrity_receipt'),'incomplete cycle')
    return True

def evaluate_campaign(plan,records,d):
    """Strict synthetic schema/coverage check. Receipts are not authenticated here."""
    validate_plan(plan,d)
    bm={b['id']:b for b in d['branches.json']['branches']}
    expected={(b,c['id']) for b in plan['branch_ids'] for c in plan['conditions'][b]}
    keys=[(r['branch_id'],r['condition_key']) for r in records]
    check(len(keys)==len(set(keys)) and set(keys)==expected,'incomplete/duplicate campaign cells')
    destructive_ids=set(); global_receipts=set()
    def take(receipt):
        check(text(receipt) and receipt not in global_receipts,'missing/replayed campaign receipt')
        global_receipts.add(receipt)
    for r in records:
        bid=r['branch_id']; b=bm[bid]; cell=r['condition_key']
        check(r.get('synthetic') is True and r.get('status')=='accepted','unaccepted campaign evidence')
        take(r.get('custody_receipt'));take(r.get('cleanup_receipt'))
        ancestors=r.get('prerequisite_receipts',[])
        check(isinstance(ancestors,list) and {x.get('branch_id') for x in ancestors}==set(b['required_branch_ids']),'missing ancestor completion')
        for a in ancestors:
            check(a.get('status')=='accepted' and text(a.get('receipt_id')),'invalid ancestor receipt')
        reps=r.get('replicates',[])
        check(isinstance(reps,list) and len(reps)==plan['replicate_counts'][bid],'replicate deficit')
        check(len({x.get('sample_id') for x in reps})==len(reps),'replicates reuse specimen')
        controls={c['id'] for c in d['control_packages.json']['controls'] if c['scope']=='all specimen branches' or isinstance(c['scope'],list) and bid in c['scope']}
        for rep in reps:
            sid=rep.get('sample_id');version=rep.get('version')
            check(text(sid) and text(version),'missing specimen/version')
            if b['destructive_endpoint']:
                check(sid not in destructive_ids,'destructive specimen reused');destructive_ids.add(sid)
            phases=rep.get('phase_receipts',[])
            check([x.get('phase') for x in phases]==plan['phase_schedules'][bid],'incomplete or reordered campaign phases')
            for ph in phases:
                check(ph.get('condition_key')==cell and ph.get('sample_id')==sid and ph.get('version')==version,'wrong campaign phase binding');take(ph.get('receipt_id'))
            cr=rep.get('control_receipts',[])
            check({x.get('control_id') for x in cr}==controls and len(cr)==len(controls),'missing/duplicate control')
            for c in cr:take(c.get('receipt_id'))
            required_services={i[:-5] for i in b['operation_ids'] if i.endswith('_WAIT')}
            context=plan.get('evidence_context',{})
            check(isinstance(context,dict) and sid in context.get('objects',{}),'missing immutable evidence context')
            declared_cell=next(x for x in plan['conditions'][bid] if x['id']==cell)
            obj=context['objects'][sid]
            if 'material' in declared_cell:check(obj.get('material_variant')==declared_cell['material'],'specimen does not match material cell')
            for attribute in ['hinge_family','layout']:
                if attribute in declared_cell:check(obj.get(attribute)==declared_cell[attribute],'specimen does not match '+attribute+' cell')
            import copy
            local=copy.deepcopy(context)
            physical=rep.get('physical_events',[])
            check(isinstance(physical,list) and physical,'missing physical event chain')
            seen_services=set();moves=0
            for item in physical:
                if item.get('kind')=='transfer':
                    move=item.get('record',{});check(move.get('sample_id')==sid,'transfer specimen mismatch')
                    validate_transfer(move,local,d);local['objects'][sid]['location']=move['to_station'];moves+=1
                    for key in ['source_safe_release_receipt','retention_receipt','destination_ready_receipt','arrival_identity_receipt']:take(move[key])
                elif item.get('kind')=='service':
                    service=item.get('service');events=item.get('events',[])
                    check(service in required_services and events,'unexpected service')
                    expected_binding=context.get('service_bindings',{}).get(events[0].get('job_id'),{})
                    check(expected_binding.get('sample_id')==sid and expected_binding.get('version')==version and expected_binding.get('condition_key')==cell,'wrong service job binding')
                    wait=next(x for x in d['operations.json']['operations'] if x['id']==service+'_WAIT')
                    check(expected_binding.get('station_id')==wait['station_id'] and expected_binding.get('port_id')==wait['interface_port'],'wrong service station/port')
                    if bid in {'LOCAL_HAND','LOCAL_STRIP','DUAL_AXIS_PANEL','SYMMETRIC_PANEL'}:check(expected_binding.get('target_registration_required') is True,'registration bypass')
                    validate_service_binding(events,expected_binding,local)
                    for event in events:take(event.get('receipt_id'))
                    seen_services.add(service)
                else:raise ContractError('unknown physical event')
            check(seen_services==required_services and moves>0,'missing service or physical transfer')
            raw=rep.get('raw_records',[])
            req=next(x for x in d['condition_requirements.json']['branches'] if x['branch_id']==bid)
            needed=req['required_observation_phases']
            check(isinstance(raw,list) and (not needed or raw),'missing raw observations')
            check(set(needed)<={x.get('phase') for x in raw if x.get('quality')=='accepted'},'missing accepted raw observation phase')
            rawcontext={'objects':{k:v['version'] for k,v in context['objects'].items()},'consumed':context.get('consumed',[]),'calibrations':context['calibrations'],'materials':{k:v['material_variant'] for k,v in context['objects'].items()},'conditions':{bb:[x['id'] for x in cc] for bb,cc in plan['conditions'].items()},'phases':plan['phase_schedules']}
            for rr in raw:
                check(rr.get('sample_id')==sid and rr.get('version')==version and rr.get('branch_id')==bid and rr.get('condition_key')==cell,'wrong raw observation identity')
                validate_record(rr,rawcontext,True);take(rr['receipt_id'])
                required_stage=req.get('observation_stage_requirements',{}).get(rr['phase'])
                if required_stage:
                    check(rr.get('thermal_stage_id')==required_stage and text(rr.get('thermal_equilibration_receipt')),'missing thermal-stage evidence')
                    stage=context.get('thermal_stage_acceptance',{}).get(required_stage,{})
                    check(finite(stage.get('minimum_C')) and finite(stage.get('maximum_C')) and stage['minimum_C']<=stage['maximum_C'] and text(stage.get('qualification_receipt')),'missing qualified thermal acceptance')
                    check(stage['minimum_C']<=rr['temperature_C']<=stage['maximum_C'],'temperature outside qualified thermal stage')
            op_receipts=rep.get('operation_receipts',[])
            check({x.get('operation_id') for x in op_receipts}==set(b['operation_ids']),'missing operation receipt')
            for op in op_receipts:
                check(op.get('sample_id')==sid and op.get('version')==version and op.get('condition_key')==cell,'operation identity mismatch');take(op.get('receipt_id'))
            if b['source_cycles'] is not None:validate_cycle_history(rep.get('cycles',[]),b['source_cycles'],sid)
    return {'scope':plan['mode'],'result':'synthetic_bookkeeping_pass','physical_execution_validated':False}


def validate_transfer(r,context,d):
    check(r.get('synthetic') is True,'unlabeled transfer fixture')
    sid=r.get('sample_id'); obj=context['objects'].get(sid,{})
    check(obj and r.get('version')==obj.get('version'),'transfer identity/version')
    check(r.get('from_station')==obj.get('location'),'transfer origin')
    route=next((x for x in d['transport_routes.json']['routes'] if x['id']==r.get('route_id')),None)
    check(route is not None and (r.get('from_station'),r.get('to_station'))==(route['from_station'],route['to_station']),'route mismatch')
    check(r.get('tethers_connected') is False,'connected payload transfer')
    check(obj.get('state') not in {'loaded_or_hot','consumed'},'unsafe payload state')
    for f in ['source_safe_release_receipt','retention_receipt','destination_ready_receipt','arrival_identity_receipt']:
        check(text(r.get(f)),'missing transfer '+f)
    check(r.get('arrival_version')==r['version'] and r.get('arrival_sample_id')==sid,'arrival substitution')
    return True

def validate_service_binding(events,expected,context):
    validate_service_trace(events,expected['job_id'],expected['sample_id'])
    sid=expected['sample_id']; obj=context['objects'].get(sid,{})
    check(obj.get('version')==expected['version'] and obj.get('location')==expected['station_id'],'wrong specimen location/version')
    check(obj.get('state')=='accepted' and text(obj.get('acceptance_receipt')),'unaccepted specimen')
    check(obj.get('material_variant')==expected.get('material_variant'),'context material substitution')
    check(context['calibrations'].get(expected['calibration_id'])==expected['setup_signature'],'stale service calibration')
    for e in events:
        for f in ['version','station_id','port_id','condition_key','fixture_id','calibration_id','setup_signature','material_variant']:
            check(e.get(f)==expected.get(f) and text(e.get(f)),'service binding '+f)
        if expected.get('target_registration_required'):
            check(e.get('target_registration_id')==expected.get('target_registration_id') and text(e.get('target_registration_id')),'missing local/axis registration')
    return True
