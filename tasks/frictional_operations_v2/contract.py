"""Original finite offline evidence contract. No device API, physics or data synthesis.

The evaluator supplies immutable receipts and a frozen study plan. Hashes detect
record drift; they do not authenticate a laboratory, certify safety or verify that
external files exist. Synthetic fixtures test bookkeeping only.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import re

BRANCHES=tuple(f'B{i:02}' for i in range(1,10))
EXPERIMENTAL=('B02','B03','B05','B06','B07')
SERVICE_STAGES=frozenset(('R03','R04','R05','R06','R07'))
STATES=frozenset(('CONTRACT_REVIEWED','HELD','UNRUN','SOURCE_CONTEXT_ONLY'))
TOKEN=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z')
HEX=re.compile(r'[0-9a-f]{64}\Z')
class ContractError(ValueError): pass
def require(ok,message):
    if not ok: raise ContractError(message)
def canonical(value):
    try:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    except (ValueError,TypeError) as exc:raise ContractError('Noncanonical JSON') from exc
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def exact(value,fields):require(type(value) is dict and set(value)==set(fields),'Unexpected or missing fields')
def token(value):require(type(value) is str and TOKEN.fullmatch(value) is not None,'Invalid identifier')
def sha(value):require(type(value) is str and HEX.fullmatch(value) is not None,'Invalid SHA256')
def ids(row,fields):
    for field in fields:token(row[field])
def unique(rows,field):
    require(type(rows) is list and all(type(r) is dict and field in r and type(r[field]) is str for r in rows),'Malformed record list')
    require(len({r[field] for r in rows})==len(rows),'Duplicate '+field)
def nonempty(rows):require(type(rows) is list and len(rows)>0,'Nonempty list required')

def load_contract(root):
    root=Path(root); ops=json.loads((root/'operations.json').read_text())['operations']; bind=json.loads((root/'shared_binding_contract.json').read_text()); semantic=json.loads((root/'semantic_core.json').read_text())
    require([r['id'] for r in ops]==[f'R{i:02}' for i in range(1,13)],'Route inventory drift')
    require(type(bind) is dict and type(semantic) is dict,'Contract objects required')
    require(type(bind.get('route_bindings')) is list and len(bind['route_bindings'])==12 and all(type(x) is dict for x in bind['route_bindings']),'Route binding inventory incomplete')
    require([x.get('route_id') for x in bind['route_bindings']]==[f'R{i:02}' for i in range(1,13)],'Route binding IDs/order drift')
    for key,prefix,count in [('route_ids','R',12),('branch_ids','B',9),('station_ids','ST',6),('asset_ids','A',8),('material_ids','M',8),('unknown_ids','U',20),('conflict_ids','C',4)]:
        require(bind.get(key)==[f'{prefix}{i:02}' for i in range(1,count+1)],'Semantic identifier inventory drift')
    require(bind.get('physical_execution_enabled') is False and bind.get('model_implemented') is False,'Executable semantics prohibited')
    require(digest(bind)==semantic['shared_binding_contract_sha256'],'Semantic digest drift')
    require(bind==json.loads((root/'scene_task_contract.json').read_text()),'Scene/task contract drift')
    require(len(bind['anchors'])==32 and len({a['anchor_id'] for a in bind['anchors']})==32,'Anchor inventory drift')
    for op,row in zip(ops,bind['route_bindings']):
        require(row=={'route_id':op['id'],'station_ids':[op['station']],'branch_ids':op['branch_ids'],'asset_ids':op['asset_ids'],'anchor_ids':op['anchor_ids'],'depends_on':op['depends_on']},'Route binding drift')
        require(op['device_command_implemented'] is False and op['physical_execution_authority'] is False,'Actuation prohibited')
    return {r['id']:r for r in ops},digest(bind)

class EvidenceLedger:
    """Only two actor-selected IDs enter propose(). Evaluator data are deep copied.

    Every failed action is retained. Two digital attempts per route, or per job
    for R11, bound retries without creating a physical parameter-search loop.
    No accepted state enables a physical action or certifies a source outcome.
    """
    def __init__(self,root,campaign_id,epoch,plan,trusted_receipts):
        token(campaign_id);token(epoch);self._ops,self._semantic=load_contract(root)
        self._plan=json.loads(canonical(plan));self._validate_plan();self._campaign=campaign_id;self._epoch=epoch
        require(type(trusted_receipts) is dict,'Evaluator receipt map required');self._receipts=json.loads(canonical(trusted_receipts))
        for key,row in self._receipts.items():token(key);require(type(row) is dict and row.get('receipt_id')==key,'Receipt identity mismatch')
        self._done={};self._history=[];self._used=set();self._attempts={};self._jobs={};self._closeouts={};self._closed=False
    def _validate_plan(self):
        p=self._plan;exact(p,('plan_id','condition_plan','repeat_policy_id','analysis_policy_id','exclusion_policy_id','randomization_policy_id'))
        ids(p,('plan_id','repeat_policy_id','analysis_policy_id','exclusion_policy_id','randomization_policy_id'));nonempty(p['condition_plan']);unique(p['condition_plan'],'condition_id')
        for row in p['condition_plan']:
            exact(row,('condition_id','branch_id','material_id','cell_variant','independent_preparation_id','repeat_group_id','condition_role','matched_pair_id'));ids(row,tuple(row))
            require(row['branch_id'] in EXPERIMENTAL,'Unsupported measured branch');require(row['cell_variant'] in {'cell_10mm','cell_19mm'},'Unknown cell variant')
            require(row['condition_role'] in {'low_filling_comparison','high_filling_comparison','sweep','baseline_control','altered_viscosity','high_filling'},'Unknown condition role')
            expected_material=('M03' if row['condition_role']=='baseline_control' else 'M07') if row['branch_id']=='B06' else {'B02':'M03','B03':'M03','B05':'M03','B07':'M08'}[row['branch_id']]
            require(row['material_id']==expected_material,'Wrong condition material')
        require({x['branch_id'] for x in p['condition_plan']}==set(EXPERIMENTAL),'Plan drops required branch')
        unique(p['condition_plan'],'independent_preparation_id')
        require({x['condition_role'] for x in p['condition_plan'] if x['branch_id']=='B02'}=={'low_filling_comparison','high_filling_comparison'},'Low-rate comparison requires distinct filling roles')
        require(all(x['condition_role']=='sweep' for x in p['condition_plan'] if x['branch_id'] in {'B03','B05'}),'Sweep role mismatch')
        require(all(x['condition_role']=='high_filling' for x in p['condition_plan'] if x['branch_id']=='B07'),'High-filling role mismatch')
        require({x['condition_role'] for x in p['condition_plan'] if x['branch_id']=='B06'}=={'baseline_control','altered_viscosity'},'Viscosity comparison needs separate baseline and altered conditions')
        for branch,roles in [('B02',{'low_filling_comparison','high_filling_comparison'}),('B06',{'baseline_control','altered_viscosity'})]:
            rows=[x for x in p['condition_plan'] if x['branch_id']==branch]
            for group in {x['matched_pair_id'] for x in rows}:
                pair=[x for x in rows if x['matched_pair_id']==group]
                require(len(pair)==2 and {x['condition_role'] for x in pair}==roles,'Matched comparison group incomplete')
                require(len({x['cell_variant'] for x in pair})==1,'Matched comparison cell variant mismatch')
    @property
    def history(self):return copy.deepcopy(self._history)
    @property
    def completed(self):return copy.deepcopy(self._done)
    @property
    def jobs(self):return copy.deepcopy(self._jobs)
    @property
    def closeouts(self):return copy.deepcopy(self._closeouts)
    @property
    def physical_execution_enabled(self):return False
    @property
    def design_complete(self):return self._closed and set(self._done)=={f'R{i:02}' for i in range(1,11)}|{'R12'} and set(self._jobs)==set(self._closeouts)
    def _record(self,action,accepted,reason):
        self._history.append({'index':len(self._history),'proposal':copy.deepcopy(action),'accepted':accepted,'reason':reason,'prior_event_hash':digest(self._history[-1]) if self._history else None})
    def propose(self,action):
        try:
            canonical(action);exact(action,('operation_id','evidence_id'));ids(action,tuple(action));oid,eid=action['operation_id'],action['evidence_id']
            require(not self._closed,'Ledger already closed');require(oid in self._ops,'Unknown operation');require(oid=='R11' or oid not in self._done,'Stage already dispositioned')
            require(eid in self._receipts,'Receipt not independently supplied');require(eid not in self._used,'Receipt replay')
            r=copy.deepcopy(self._receipts[eid]);op=self._ops[oid]
            attempt=oid+(':'+str(r.get('payload',{}).get('job_id','invalid')) if oid=='R11' and type(r.get('payload')) is dict else '')
            self._attempts[attempt]=self._attempts.get(attempt,0)+1;require(self._attempts[attempt]<=2,'Digital attempt budget exhausted')
            require(all(d in self._done for d in op['depends_on']),'Missing dependency disposition');self._common(r,op)
            if r['status']=='ACCEPTED':getattr(self,'_'+oid)(r['payload'],r)
            else:
                require(oid not in {'R01','R11','R12'},'Intake/closeout/archive needs complete evidence')
                exact(r['payload'],('reason_id','safe_state_receipt_id'));ids(r['payload'],tuple(r['payload']))
                require(all(v in {'HELD','UNRUN','SOURCE_CONTEXT_ONLY'} for v in r['branch_results'].values()),'Held stage promotes evidence')
            for job in r['service_jobs']:
                require(job['job_id'] not in self._jobs,'Service job replay or identity collision')
            result={'receipt_hash':digest(r),'receipt':r,'digital_status':r['status'],'physical_execution':False}
            if oid=='R11':self._closeouts[r['payload']['job_id']]=result
            else:self._done[oid]=result
            for job in r['service_jobs']:self._jobs[job['job_id']]={'operation_id':oid,'receipt_hash':digest(r),'job':job}
            if oid=='R12':self._closed=True
            self._used.add(eid);self._record(action,True,'Digital disposition only; physical execution disabled');return copy.deepcopy(result)
        except (ContractError,KeyError,TypeError,IndexError,AttributeError) as exc:
            try:safe=json.loads(canonical(action))
            except ContractError:safe={'invalid_proposal':True}
            self._record(safe,False,str(exc));raise ContractError(str(exc)) from exc
    def _common(self,r,op):
        exact(r,('receipt_id','operation_id','campaign_id','epoch','frozen_plan_sha256','semantic_core_sha256','origin','status','qualification_refs','input_receipt_hashes','branch_results','service_jobs','payload','physical_execution'))
        ids(r,('receipt_id','operation_id','campaign_id','epoch'));require(r['operation_id']==op['id'],'Receipt operation mismatch');require((r['campaign_id'],r['epoch'])==(self._campaign,self._epoch),'Stale or foreign campaign')
        require(r['frozen_plan_sha256']==digest(self._plan),'Plan drift');require(r['semantic_core_sha256']==self._semantic,'Semantic drift')
        require(r['origin'] in {'synthetic_contract_fixture','external_qualified_record'},'Source reports or actor outputs are not observations');require(r['physical_execution'] is False,'Physical execution prohibited')
        require(r['status'] in {'ACCEPTED','HOLD','UNRUN'},'Unknown status');scope=op['branch_ids']
        if op['id']=='R11':
            require(type(r['payload']) is dict and r['payload'].get('job_id') in self._jobs,'Closeout job not registered');scope=self._jobs[r['payload']['job_id']]['job']['branch_ids']
        exact(r['branch_results'],scope);require(all(v in STATES for v in r['branch_results'].values()),'Invalid branch status')
        exact(r['qualification_refs'],op['unknown_refs'])
        for ref in r['qualification_refs'].values():
            if ref is not None:token(ref)
        exact(r['input_receipt_hashes'],op['depends_on']);require(r['input_receipt_hashes']=={d:self._done[d]['receipt_hash'] for d in op['depends_on']},'Dependency hash mismatch')
        require(type(r['service_jobs']) is list,'Job list required');unique(r['service_jobs'],'job_id')
        if op['id'] not in SERVICE_STAGES:require(not r['service_jobs'],'Unexpected service job')
        for j in r['service_jobs']:
            exact(j,('job_id','subject_id','job_kind','job_status','safe_state_required','branch_ids'));ids(j,('job_id','subject_id','job_kind'));require(type(j['branch_ids']) is list and j['branch_ids']==sorted(set(j['branch_ids'])) and len(j['branch_ids'])>0 and set(j['branch_ids'])<=set(op['branch_ids']),'Job branch scope invalid');require(j['job_status'] in {'receipt_reviewed','failed','not_started'},'Invalid job disposition');require(j['safe_state_required'] is True,'No safe-state bypass');require(j['job_kind']==('preparation' if op['id']=='R03' else 'qualification' if op['id']=='R04' else 'measurement'),'Service job kind mismatch')
        if r['status']=='ACCEPTED':
            require(all(j['job_status']=='receipt_reviewed' for j in r['service_jobs']),'Accepted service contains failed job')
            require(all(v is not None for v in r['qualification_refs'].values()),'Accepted receipt lacks qualification references')
            if op['id'] in SERVICE_STAGES:require(all(self._done[d]['digital_status']=='ACCEPTED' for d in op['depends_on']),'Held dependency cannot release downstream service')
        if op['id'] in {'R01','R10'}:require(all(v=='SOURCE_CONTEXT_ONLY' for v in r['branch_results'].values()),'Source review cannot create measured result')
        if r['status']=='ACCEPTED' and op['id'] not in {'R01','R10','R12'}:require(all(v=='CONTRACT_REVIEWED' for v in r['branch_results'].values()),'Accepted contract branch mismatch')
    def _accepted(self,oid):
        require(oid in self._done and self._done[oid]['digital_status']=='ACCEPTED','Required accepted evidence missing');return self._done[oid]['receipt']['payload']
    def _job_refs(self,r,expected):require({j['job_id'] for j in r['service_jobs']}==set(expected),'Job receipt scope mismatch')
    def _R01(self,p,r):
        exact(p,('doi','source_version_id','rights_scope','main_pages','figures','equations','supplement_descriptions','separate_technical_si','dedup_receipt_id','publisher_exports','conflicts_preserved'))
        require(p['doi']=='10.1038/ncomms1289' and p['rights_scope']=='original_only','Wrong source or rights scope');ids(p,('source_version_id','dedup_receipt_id'))
        for field,value in [('main_pages',8),('figures',5),('equations',9),('supplement_descriptions',2)]:require(type(p[field]) is int and p[field]==value,'Incomplete source coverage')
        require(p['separate_technical_si'] is False and p['publisher_exports'] is False,'Source scope drift');require(p['conflicts_preserved']==['C01','C02','C03','C04'],'Source issue inventory drift')
    def _R02(self,p,r):
        exact(p,('grain_lot','host_lot','altered_host_lot','cells','custody_receipt_id'))
        for name in ['grain_lot','host_lot','altered_host_lot']:
            row=p[name];exact(row,('lot_id','identity_certificate_id','contained','composition_convention_id'));ids(row,('lot_id','identity_certificate_id','composition_convention_id'));require(row['contained'] is True,'Uncontained stock prohibited')
        require(len({p[name]['lot_id'] for name in ('grain_lot','host_lot','altered_host_lot')})==3,'Grain and host lot identities conflated')
        exact(p['cells'],('cell_10mm','cell_19mm'))
        for variant,row in p['cells'].items():
            exact(row,('cell_id','cell_variant','rating_receipt_id','inspection_receipt_id','geometry_receipt_id','compliance_receipt_id'));ids(row,tuple(row));require(row['cell_variant']==variant,'Cell variant mismatch')
        require(len({c['cell_id'] for c in p['cells'].values()})==2,'Cell variants conflated');token(p['custody_receipt_id'])
    def _R03(self,p,r):
        exact(p,('preparations',));nonempty(p['preparations']);unique(p['preparations'],'condition_id');inventory=self._accepted('R02');plans={x['condition_id']:x for x in self._plan['condition_plan']}
        require({x['condition_id'] for x in p['preparations']}==set(plans),'Preparation scope mismatch')
        fresh=[];batch_parents={}
        for row in p['preparations']:
            exact(row,('condition_id','branch_id','material_id','independent_preparation_id','grain_lot_id','host_lot_id','dispersion_batch_id','aliquot_id','cell_id','cell_variant','loaded_state_id','settled_state_id','normalized_phi_receipt_id','settling_receipt_id','mixture_properties_receipt_id','service_job_id','custody_receipt_id'))
            ids(row,tuple(row));plan=plans[row['condition_id']]
            for k in ('branch_id','material_id','independent_preparation_id','cell_variant'):require(row[k]==plan[k],'Preparation plan drift')
            require(row['grain_lot_id']==inventory['grain_lot']['lot_id'],'Grain lot mismatch');host='altered_host_lot' if row['material_id']=='M07' else 'host_lot';require(row['host_lot_id']==inventory[host]['lot_id'],'Host formulation lineage mismatch')
            require(row['cell_id']==inventory['cells'][row['cell_variant']]['cell_id'],'Cell identity mismatch');require(row['loaded_state_id']!=row['settled_state_id'],'Settling requires child-state identity')
            parents=(row['grain_lot_id'],row['host_lot_id']);require(row['dispersion_batch_id'] not in batch_parents or batch_parents[row['dispersion_batch_id']]==parents,'Dispersion batch parent identity changed');batch_parents[row['dispersion_batch_id']]=parents
            fresh.extend([row['aliquot_id'],row['loaded_state_id'],row['settled_state_id'],row['independent_preparation_id']])
        require(len(set(fresh))==len(fresh),'Aliquot/state/preparation identity reuse');self._job_refs(r,[x['service_job_id'] for x in p['preparations']])
        subjects={j['job_id']:j['subject_id'] for j in r['service_jobs']};require(all(subjects[x['service_job_id']]==x['settled_state_id'] for x in p['preparations']),'Preparation job subject mismatch')
        branches={j['job_id']:j['branch_ids'] for j in r['service_jobs']};require(all(branches[x['service_job_id']]==sorted({'B01',x['branch_id']}) for x in p['preparations']),'Preparation job branch mismatch')
    def _R04(self,p,r):
        exact(p,('instrument_config_id','calibration_id','clock_map_id','pressure_reference_id','gas_reference_state_id','pump_calibration_id','camera_calibration_id','daq_calibration_id','total_compliance_receipt_id','safe_envelope_receipt_id','interlock_receipt_id','geometry_transform_id','clock_domain','service_job_id'))
        ids(p,tuple(p));require(p['clock_domain']=='experiment_time','Movie playback time is not acquisition time');self._job_refs(r,[p['service_job_id']]);require(r['service_jobs'][0]['subject_id']==p['instrument_config_id'],'Qualification job subject mismatch');require(r['service_jobs'][0]['branch_ids']==['B01'],'Qualification branch mismatch')
    def _run_route(self,p,r,branches):
        exact(p,('runs',));nonempty(p['runs']);unique(p['runs'],'condition_id');unique(p['runs'],'run_id');preps={x['condition_id']:x for x in self._accepted('R03')['preparations']};instruments=self._accepted('R04')
        expected={x['condition_id'] for x in self._plan['condition_plan'] if x['branch_id'] in branches};require({x['condition_id'] for x in p['runs']}==expected,'Run scope must match frozen condition plan')
        previous=[x for stage in ['R05','R06','R07'] if stage in self._done and self._done[stage]['digital_status']=='ACCEPTED' for x in self._done[stage]['receipt']['payload']['runs']]
        seen_raw={x[f]['raw_evidence_id'] for x in previous for f in ('pressure_raw','image_raw')};seen_states={x['spent_state_id'] for x in previous}|{prep[k] for prep in preps.values() for k in ('loaded_state_id','settled_state_id','aliquot_id','independent_preparation_id')};seen_hashes={x[f]['sha256'] for x in previous for f in ('pressure_raw','image_raw')};seen_run={x['run_id'] for stage in ['R05','R06','R07'] if stage in self._done and self._done[stage]['digital_status']=='ACCEPTED' for x in self._done[stage]['receipt']['payload']['runs']}
        for row in p['runs']:
            exact(row,('run_id','condition_id','branch_id','settled_state_id','spent_state_id','cell_id','instrument_config_id','calibration_id','clock_map_id','service_job_id','requested_condition_receipt_id','observed_condition_receipt_id','pressure_raw','image_raw','quality_receipt_id','conflict_disposition_id','scientific_outcome'))
            ids(row,tuple(k for k in row if k not in ('pressure_raw','image_raw','scientific_outcome')));prep=preps[row['condition_id']]
            require(row['branch_id']==prep['branch_id'] and row['settled_state_id']==prep['settled_state_id'] and row['cell_id']==prep['cell_id'],'Run state/condition lineage mismatch')
            require(row['spent_state_id']!=row['settled_state_id'],'Displacement needs new state');require(row['run_id'] not in seen_run,'Run identity replay');require(row['spent_state_id'] not in seen_states,'Spent state replay');seen_states.add(row['spent_state_id'])
            for key in ('instrument_config_id','calibration_id','clock_map_id'):require(row[key]==instruments[key],'Cross-device configuration mismatch')
            require(row['requested_condition_receipt_id']!=row['observed_condition_receipt_id'],'Requested and independently observed condition receipts must be distinct')
            require(row['scientific_outcome']=='not_assessed','Contract does not certify morphology or scientific outcome')
            for field,modality in [('pressure_raw','pressure'),('image_raw','image')]:
                raw=row[field];exact(raw,('raw_evidence_id','sha256','modality','run_id','clock_map_id','origin','raw_acquisition','units','record_kind'));ids(raw,('raw_evidence_id','run_id','clock_map_id'));sha(raw['sha256'])
                require(raw['raw_evidence_id'] not in seen_raw,'Duplicate raw stream identity');seen_raw.add(raw['raw_evidence_id']);require(raw['sha256'] not in seen_hashes,'Raw stream content reuse');seen_hashes.add(raw['sha256'])
                require(raw['modality']==modality and raw['run_id']==row['run_id'] and raw['clock_map_id']==row['clock_map_id'],'Raw evidence association mismatch');require(raw['origin']==r['origin'],'Receipt origin laundering')
                require(raw['record_kind']==('hash_only_placeholder' if r['origin']=='synthetic_contract_fixture' else 'external_raw_record_reference'),'Wrong evidence kind')
                require(raw['raw_acquisition'] is (r['origin']=='external_qualified_record'),'Synthetic fixture cannot claim acquisition');require(raw['units']==('declared_pressure_reference' if modality=='pressure' else 'calibrated_image_frame'),'Unqualified stream units')
        self._job_refs(r,[x['service_job_id'] for x in p['runs']]);subjects={j['job_id']:j['subject_id'] for j in r['service_jobs']};require(all(subjects[x['service_job_id']]==x['run_id'] for x in p['runs']),'Run job subject mismatch')
        branches_by_job={j['job_id']:j['branch_ids'] for j in r['service_jobs']};require(all(branches_by_job[x['service_job_id']]==[x['branch_id']] for x in p['runs']),'Run job branch mismatch')
    def _R05(self,p,r):self._run_route(p,r,('B02','B03'))
    def _R06(self,p,r):self._run_route(p,r,('B05',))
    def _R07(self,p,r):self._run_route(p,r,('B06','B07'))
    def _runs(self):return [x for s in ('R05','R06','R07') for x in self._accepted(s)['runs']]
    def _R08(self,p,r):
        exact(p,('derived_records',));nonempty(p['derived_records']);unique(p['derived_records'],'run_id');unique(p['derived_records'],'derived_evidence_id');runs={x['run_id']:x for x in self._runs()};require({x['run_id'] for x in p['derived_records']}==set(runs),'Derived scope mismatch')
        for row in p['derived_records']:
            exact(row,('derived_evidence_id','run_id','raw_hashes','analysis_policy_id','analysis_version_id','segmentation_receipt_id','area_perimeter_definition_id','geometry_model_id','derivative_estimator_id','uncertainty_receipt_id','clock_map_id','metrics_generated','source_plot_used_as_raw'))
            ids(row,tuple(k for k in row if k not in ('raw_hashes','metrics_generated','source_plot_used_as_raw')));run=runs[row['run_id']]
            require(row['derived_evidence_id'] not in {v[f]['raw_evidence_id'] for v in runs.values() for f in ('pressure_raw','image_raw')},'Derived evidence aliases raw record')
            require(row['raw_hashes']=={f:run[f]['sha256'] for f in ('pressure_raw','image_raw')},'Derived/raw lineage mismatch');require(row['analysis_policy_id']==self._plan['analysis_policy_id'],'Analysis plan changed');require(row['clock_map_id']==run['clock_map_id'],'Derived clock mismatch')
            require(row['metrics_generated'] is False and row['source_plot_used_as_raw'] is False,'No generated metrics or plot-to-raw substitution')
    def _R09(self,p,r):
        exact(p,('controls_review_id','repeat_policy_id','exclusion_policy_id','randomization_policy_id','independent_preparation_ids','within_image_samples_are_repeats','missing_grid_cells_are_negative','source_threshold_is_acceptance_band','parameter_sensitivity_is_confidence_interval','model_executed','conflict_ids','branch_assessments','control_links'))
        ids(p,('controls_review_id','repeat_policy_id','exclusion_policy_id','randomization_policy_id'))
        for k in ('repeat_policy_id','exclusion_policy_id','randomization_policy_id'):require(p[k]==self._plan[k],'Statistical plan changed')
        require(p['independent_preparation_ids']==sorted(x['independent_preparation_id'] for x in self._plan['condition_plan']),'Preparation-repeat accounting mismatch')
        for k in ('within_image_samples_are_repeats','missing_grid_cells_are_negative','source_threshold_is_acceptance_band','parameter_sensitivity_is_confidence_interval','model_executed'):require(p[k] is False,'Scientific evidence-class promotion prohibited')
        exact(p['control_links'],tuple(f'CR{i:02}' for i in range(1,10)))
        scopes={'CR01':['B02'],'CR02':['B03'],'CR03':['B05'],'CR04':['B06'],'CR05':list(EXPERIMENTAL),'CR06':[],'CR07':[],'CR08':[],'CR09':[]}
        evidence={'CR01':'matched_low_rate_conditions','CR02':'sparse_sweep_conditions','CR03':'rate_sweep_conditions','CR04':'paired_viscosity_conditions','CR05':'cell_compliance_qualification','CR06':'replicate_sd_n_unknown','CR07':'within_pattern_width_samples','CR08':'within_run_bubble_events','CR09':'parameter_sensitivity'}
        for cid,row in p['control_links'].items():
            exact(row,('review_receipt_id','condition_ids','evidence_kind','new_measurement'));token(row['review_receipt_id'])
            require(row['condition_ids']==sorted(x['condition_id'] for x in self._plan['condition_plan'] if x['branch_id'] in scopes[cid]),'Control condition scope mismatch')
            require(row['evidence_kind']==evidence[cid] and row['new_measurement'] is False,'Control evidence class promoted')
        require(p['conflict_ids']==['C01','C02','C03','C04'],'Conflict dropped');exact(p['branch_assessments'],('B02','B03','B04','B05','B06','B07','B09'));require(all(v=='inconclusive_design_only' for v in p['branch_assessments'].values()),'No physical science certification')
    def _R10(self,p,r):
        exact(p,('porous_medium_attribution','borrowed_media_exported','context_counted_as_new_experiment','boyle_sign_resolved','model_executed','conflicts_preserved'))
        require(p['porous_medium_attribution']=='external_authors_refs_38_42','External comparison attribution missing')
        for k in ('borrowed_media_exported','context_counted_as_new_experiment','boyle_sign_resolved','model_executed'):require(p[k] is False,'Source/model/context promoted')
        require(p['conflicts_preserved']==['C01','C02','C03','C04'],'Source conflict altered')
    def _R11(self,p,r):
        exact(p,('job_id','job_receipt_hash','subject_id','safe_release_receipt_id','contained_disposition_id','cleaning_inspection_id','reuse_policy_id','disposition','physical_uncoupling_performed'))
        ids(p,tuple(k for k in p if k not in ('job_receipt_hash','physical_uncoupling_performed')));sha(p['job_receipt_hash']);require(p['job_id'] in self._jobs,'Closeout job not registered');require(p['job_id'] not in self._closeouts,'Job already closed')
        job=self._jobs[p['job_id']];require(p['job_receipt_hash']==job['receipt_hash'] and p['subject_id']==job['job']['subject_id'],'Closeout lineage mismatch');require(p['disposition'] in {'archive_record','return_contained','quarantine','not_started'},'Invalid disposition')
        if job['job']['job_status']=='receipt_reviewed':require(p['disposition']!='not_started','Reviewed job cannot be labeled unstarted')
        if job['job']['job_status']=='failed':require(p['disposition']=='quarantine','Failed job must remain quarantined')
        if job['job']['job_status']=='not_started':require(p['disposition']=='not_started','Unstarted job cannot imply handling')
        require(p['physical_uncoupling_performed'] is False,'No physical handoff implemented')
    def final_branch_dispositions(self):
        # This digital implementation cannot create measured science, including
        # when a receipt points at a qualified external record.
        return {b:('SOURCE_CONTEXT_ONLY' if b in {'B08','B09'} else 'UNRUN') for b in BRANCHES}
    def _R12(self,p,r):
        exact(p,('archive_receipt_hashes','job_closeout_hashes','failure_event_hashes','branch_dispositions','raw_references_retained','exclusion_reasons_retained','qualification_holds','scientific_execution_complete'))
        require(set(self._done)=={f'R{i:02}' for i in range(1,11)},'All primary route dispositions required');require(set(self._jobs)==set(self._closeouts),'Open service job blocks archive')
        require(p['archive_receipt_hashes']=={k:v['receipt_hash'] for k,v in self._done.items()},'Archive receipt mismatch');require(p['job_closeout_hashes']=={k:v['receipt_hash'] for k,v in self._closeouts.items()},'Closeout archive mismatch')
        require(p['failure_event_hashes']==[digest(x) for x in self._history if not x['accepted']],'Rejected/failure evidence omitted');require(p['branch_dispositions']==self.final_branch_dispositions() and r['branch_results']==p['branch_dispositions'],'Final branch promotion')
        require(p['raw_references_retained'] is True and p['exclusion_reasons_retained'] is True,'Evidence retention required');require(p['qualification_holds']==[f'U{i:02}' for i in range(1,21)],'Qualification hold dropped');require(p['scientific_execution_complete'] is False,'Design archive is not science completion')
