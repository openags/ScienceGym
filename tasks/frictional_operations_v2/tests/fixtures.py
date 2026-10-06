"""Evaluator-only synthetic identifiers/hashes. No fluid fields or measured values."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contract import digest,load_contract

def make_fixture(held=()):
    ops,semantic=load_contract(ROOT)
    rows=[('LOW','B02','M03','low_filling_comparison'),('HIGH','B02','M03','high_filling_comparison'),('GRID','B03','M03','sweep'),('RATE','B05','M03','sweep'),('BASE','B06','M03','baseline_control'),('VISC','B06','M07','altered_viscosity'),('FRACT','B07','M08','high_filling')]
    conditions=[{'condition_id':'CON_'+n,'branch_id':b,'material_id':m,'cell_variant':'cell_19mm' if n in {'GRID','FRACT'} else 'cell_10mm','independent_preparation_id':'PREP_'+n,'repeat_group_id':'GROUP_'+b,'condition_role':role,'matched_pair_id':'PAIR_'+b if b in {'B02','B06'} else 'UNPAIRED_'+n} for n,b,m,role in rows]
    plan={'plan_id':'PLAN_SYNTHETIC','condition_plan':conditions,'repeat_policy_id':'REPEAT_POLICY','analysis_policy_id':'ANALYSIS_POLICY','exclusion_policy_id':'EXCLUSION_POLICY','randomization_policy_id':'RANDOM_POLICY'}
    receipts={};order=[];stage={};jobs={};closeouts={}
    def add(oid,p,jlist=(),eid=None):
        op=ops[oid];eid=eid or 'REC_'+oid;status='HOLD' if oid in held else 'ACCEPTED'
        if status=='HOLD':p={'reason_id':'UNRESOLVED_QUALIFICATION','safe_state_receipt_id':'SAFE_HOLD_'+oid};jlist=[dict(j,job_status='failed') for j in jlist]
        branch={b:('HELD' if status=='HOLD' else 'SOURCE_CONTEXT_ONLY' if oid in {'R01','R10'} else 'CONTRACT_REVIEWED') for b in op['branch_ids']}
        if oid=='R11':branch={b:'CONTRACT_REVIEWED' for b in jobs[p['job_id']]['job']['branch_ids']}
        if oid=='R12':branch=p['branch_dispositions']
        r={'receipt_id':eid,'operation_id':oid,'campaign_id':'CAM_SYNTHETIC','epoch':'EPOCH_1','frozen_plan_sha256':digest(plan),'semantic_core_sha256':semantic,'origin':'synthetic_contract_fixture','status':status,'qualification_refs':{u:'FIXTURE_REF_'+u if status=='ACCEPTED' else None for u in op['unknown_refs']},'input_receipt_hashes':{d:digest(stage[d]) for d in op['depends_on']},'branch_results':branch,'service_jobs':list(jlist),'payload':p,'physical_execution':False}
        receipts[eid]=r;order.append({'operation_id':oid,'evidence_id':eid})
        if oid!='R11':stage[oid]=r
        for j in jlist:jobs[j['job_id']]={'job':j,'receipt':r}
        return r
    def job(j,subject,kind,branches):return {'job_id':j,'subject_id':subject,'job_kind':kind,'job_status':'receipt_reviewed','safe_state_required':True,'branch_ids':sorted(branches)}
    def close(jid):
        row=jobs[jid];j=row['job'];p={'job_id':jid,'job_receipt_hash':digest(row['receipt']),'subject_id':j['subject_id'],'safe_release_receipt_id':'SAFE_'+jid,'contained_disposition_id':'DISP_'+jid,'cleaning_inspection_id':'CLEAN_'+jid,'reuse_policy_id':'REUSE_POLICY','disposition':'quarantine' if j['job_status']=='failed' else 'archive_record','physical_uncoupling_performed':False}
        r=add('R11',p,eid='CLOSE_'+jid);closeouts[jid]=digest(r)
    add('R01',{'doi':'10.1038/ncomms1289','source_version_id':'FINAL_2011','rights_scope':'original_only','main_pages':8,'figures':5,'equations':9,'supplement_descriptions':2,'separate_technical_si':False,'dedup_receipt_id':'DEDUP_REVIEW','publisher_exports':False,'conflicts_preserved':['C01','C02','C03','C04']})
    lot=lambda n:{'lot_id':n,'identity_certificate_id':'CERT_'+n,'contained':True,'composition_convention_id':'BASIS_'+n}
    cells={v:{'cell_id':'CELL_'+v,'cell_variant':v,'rating_receipt_id':'RATING_'+v,'inspection_receipt_id':'INSPECT_'+v,'geometry_receipt_id':'GEOM_'+v,'compliance_receipt_id':'COMPLIANCE_'+v} for v in ('cell_10mm','cell_19mm')}
    add('R02',{'grain_lot':lot('GRAIN'),'host_lot':lot('HOST'),'altered_host_lot':lot('ALTERED_HOST'),'cells':cells,'custody_receipt_id':'CUSTODY_INTAKE'})
    preps=[]
    for c in conditions:
        n=c['condition_id'];preps.append({k:c[k] for k in ('condition_id','branch_id','material_id','independent_preparation_id','cell_variant')})
        preps[-1].update(grain_lot_id='GRAIN',host_lot_id='ALTERED_HOST' if c['material_id']=='M07' else 'HOST',dispersion_batch_id='BATCH_'+n,aliquot_id='ALIQ_'+n,cell_id=cells[c['cell_variant']]['cell_id'],loaded_state_id='LOADED_'+n,settled_state_id='SETTLED_'+n,normalized_phi_receipt_id='PHI_'+n,settling_receipt_id='SETTLING_'+n,mixture_properties_receipt_id='MIXTURE_'+n,service_job_id='PREP_JOB_'+n,custody_receipt_id='CUSTODY_'+n)
    add('R03',{'preparations':preps},[job(p['service_job_id'],p['settled_state_id'],'preparation',{'B01',p['branch_id']}) for p in preps])
    instr={k:k.upper() for k in ('instrument_config_id','calibration_id','clock_map_id','pressure_reference_id','gas_reference_state_id','pump_calibration_id','camera_calibration_id','daq_calibration_id','total_compliance_receipt_id','safe_envelope_receipt_id','interlock_receipt_id','geometry_transform_id')};instr.update(clock_domain='experiment_time',service_job_id='INSTRUMENT_JOB')
    add('R04',instr,[job('INSTRUMENT_JOB',instr['instrument_config_id'],'qualification',['B01'])])
    allruns=[]
    for oid,branches in [('R05',('B02','B03')),('R06',('B05',)),('R07',('B06','B07'))]:
        runrows=[]
        for prep in preps:
            if prep['branch_id'] not in branches:continue
            n=prep['condition_id'];rid='RUN_'+n
            raw=lambda modality:{'raw_evidence_id':'RAW_'+modality+'_'+rid,'sha256':digest({'synthetic_token':modality+'_'+rid}),'modality':modality,'run_id':rid,'clock_map_id':instr['clock_map_id'],'origin':'synthetic_contract_fixture','raw_acquisition':False,'units':'declared_pressure_reference' if modality=='pressure' else 'calibrated_image_frame','record_kind':'hash_only_placeholder'}
            rr={k:prep[k] for k in ('condition_id','branch_id','settled_state_id','cell_id')};rr.update({k:instr[k] for k in ('instrument_config_id','calibration_id','clock_map_id')});rr.update(run_id=rid,spent_state_id='SPENT_'+n,service_job_id='RUN_JOB_'+n,requested_condition_receipt_id='REQUEST_'+n,observed_condition_receipt_id='OBSERVED_REF_'+n,pressure_raw=raw('pressure'),image_raw=raw('image'),quality_receipt_id='QUALITY_'+n,conflict_disposition_id='CONFLICT_HOLD_'+n,scientific_outcome='not_assessed');runrows.append(rr)
        add(oid,{'runs':runrows},[job(x['service_job_id'],x['run_id'],'measurement',[x['branch_id']]) for x in runrows]);allruns.extend(runrows)
        # Demonstrates closeout before other independent branches and analysis.
        if oid=='R05':
            for rr in runrows:close(rr['service_job_id'])
    for jid in jobs:
        if jid not in closeouts:close(jid)
    derived=[]
    for rr in allruns:
        n=rr['run_id'];derived.append({'derived_evidence_id':'DERIVED_'+n,'run_id':n,'raw_hashes':{f:rr[f]['sha256'] for f in ('pressure_raw','image_raw')},'analysis_policy_id':plan['analysis_policy_id'],'analysis_version_id':'ANALYSIS_V1','segmentation_receipt_id':'SEG_'+n,'area_perimeter_definition_id':'AS_DEFINITION','geometry_model_id':'AREA_VOLUME_QUALIFICATION','derivative_estimator_id':'DERIVATIVE_QUALIFICATION','uncertainty_receipt_id':'UNCERT_'+n,'clock_map_id':instr['clock_map_id'],'metrics_generated':False,'source_plot_used_as_raw':False})
    add('R08',{'derived_records':derived})
    scopes={'CR01':['B02'],'CR02':['B03'],'CR03':['B05'],'CR04':['B06'],'CR05':['B02','B03','B05','B06','B07'],'CR06':[],'CR07':[],'CR08':[],'CR09':[]}
    evidence={'CR01':'matched_low_rate_conditions','CR02':'sparse_sweep_conditions','CR03':'rate_sweep_conditions','CR04':'paired_viscosity_conditions','CR05':'cell_compliance_qualification','CR06':'replicate_sd_n_unknown','CR07':'within_pattern_width_samples','CR08':'within_run_bubble_events','CR09':'parameter_sensitivity'}
    links={cid:{'review_receipt_id':'REVIEW_'+cid,'condition_ids':sorted(x['condition_id'] for x in conditions if x['branch_id'] in scopes[cid]),'evidence_kind':evidence[cid],'new_measurement':False} for cid in scopes}
    add('R09',dict(control_links=links,controls_review_id='CONTROLS_REVIEW',repeat_policy_id=plan['repeat_policy_id'],exclusion_policy_id=plan['exclusion_policy_id'],randomization_policy_id=plan['randomization_policy_id'],independent_preparation_ids=sorted(x['independent_preparation_id'] for x in conditions),within_image_samples_are_repeats=False,missing_grid_cells_are_negative=False,source_threshold_is_acceptance_band=False,parameter_sensitivity_is_confidence_interval=False,model_executed=False,conflict_ids=['C01','C02','C03','C04'],branch_assessments={b:'inconclusive_design_only' for b in ('B02','B03','B04','B05','B06','B07','B09')}))
    add('R10',{'porous_medium_attribution':'external_authors_refs_38_42','borrowed_media_exported':False,'context_counted_as_new_experiment':False,'boyle_sign_resolved':False,'model_executed':False,'conflicts_preserved':['C01','C02','C03','C04']})
    add('R12',{'archive_receipt_hashes':{k:digest(v) for k,v in stage.items()},'job_closeout_hashes':closeouts,'failure_event_hashes':[],'branch_dispositions':{b:('SOURCE_CONTEXT_ONLY' if b in {'B08','B09'} else 'UNRUN') for b in (f'B{i:02}' for i in range(1,10))},'raw_references_retained':True,'exclusion_reasons_retained':True,'qualification_holds':[f'U{i:02}' for i in range(1,21)],'scientific_execution_complete':False})
    return plan,receipts,order
