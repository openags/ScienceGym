"""Finite synthetic metadata contract, never a service executor or physics model.

The trusted store and fixtures are evaluator-owned in-memory objects. They do not
implement authenticated real-world receipts. No method sends a command, generates
scientific values, changes physical custody, or resolves actual qualification.
"""
from copy import deepcopy
from datetime import datetime
import re

class ContractError(ValueError): pass

def require(ok, why):
    if not ok: raise ContractError(why)

def instant(x):
    require(isinstance(x,str),'timestamp required')
    try: t=datetime.fromisoformat(x.replace('Z','+00:00'))
    except (ValueError,TypeError): raise ContractError('invalid timestamp')
    require(t.tzinfo is not None,'timezone required')
    return t

def nonempty(v): return isinstance(v,str) and bool(v.strip())

def unique_strings(v):
    return isinstance(v,list) and bool(v) and all(nonempty(x) for x in v) and len(v)==len(set(v))

class SyntheticStore:
    """Private evaluator fixture store. Actor supplies IDs, never inline receipts."""
    def __init__(self, receipts):
        require(isinstance(receipts,list),'receipt list required')
        ids=[r.get('id') for r in receipts]
        require(unique_strings(ids),'unique receipt ids required')
        self._receipts=deepcopy(dict(zip(ids,receipts)))
    def lookup(self, rid):
        require(isinstance(rid,str) and rid in self._receipts,'unknown evidence ID')
        r=deepcopy(self._receipts[rid])
        require(r.get('origin')=='synthetic_evaluator_fixture','source or live receipt not accepted')
        require(r.get('provider')=='SYNTHETIC_QUALIFIED_PROVIDER','untrusted fixture provider')
        require(r.get('status')=='accepted','unaccepted evidence')
        return r

OPERATIONS={f'R{i:02d}' for i in range(15)}
MEASUREMENT_ROUTES={f'R{i:02d}' for i in range(5,12)}
MEASUREMENT_FIELDS=['bundle_hash','sample_id','chip_id','carrier_id','mount_id','custodian_id','job_id','configuration_revision','terminal_map_revision','method_revision','reference_id','test_id','ratio_direction','ratio_units','condition_id','field_sign','field_magnitude_record_id','temperature_record_id','thermal_history_id','uncertainty_semantics','chronology_id','exclusion_log_id']
LIST_FIELDS=['lease_ids','instrument_ids','calibration_ids','raw_timestamps','polarity_cycle_ids','raw_ratio_record_ids','per_reading_SD_record_ids','covariance_dependency_ids','repeat_unit_ids']
DIRECT_PAIRS={'R05':{'Array1','Array2'},'R06':{'HB','REF100'},'R08':{'HB','Array1'}}
SAFE_CHANNELS={'electrical_access','accessible_field','thermal_pressure','stopped_supported_motion','support_occupancy'}

class MetadataContract:
    def __init__(self, store): self.store=store
    def review(self, action):
        require(isinstance(action,dict),'action object required')
        require(set(action)=={'operation_id','evidence_ids'},'only operation/evidence IDs allowed')
        op=action['operation_id'];require(op in OPERATIONS,'unknown operation')
        require(unique_strings(action['evidence_ids']),'distinct evidence IDs required')
        receipts=[self.store.lookup(x) for x in action['evidence_ids']]
        require(all(r.get('operation_id')==op for r in receipts),'wrong operation evidence')
        kinds=[r.get('kind') for r in receipts]
        require(len(kinds)==len(set(kinds)),'ambiguous duplicate evidence kinds')
        index={r['kind']:r for r in receipts}
        if op in MEASUREMENT_ROUTES:
            require(set(index)=={'measurement','calibration','lease'},'measurement, calibration and lease required')
            self.measurement(index['measurement'],op);self.calibration(index['calibration'],index['measurement']);self.measurement_lease(index['lease'],index['measurement'])
        elif op=='R04':
            require(set(index)=={'characterization'},'characterization receipt required')
            self.characterization(index['characterization'])
        elif op=='R14':
            require(set(index)=={'closeout'},'closeout receipt required')
            self.closeout(index['closeout'])
        elif op in {'R12','R13'}:
            require(set(index)=={'analysis'},'analysis receipt required')
            self.analysis(index['analysis'],op)
        elif op in {'R01','R02','R03'}:
            require(set(index)=={'R01':{'custody','preparation'},'R02':{'custody'},'R03':{'custody','lease'}}[op],'required custody evidence kinds mismatch')
            require('custody' in index,'custody receipt required')
            self.custody(index['custody'])
            if op=='R01':
                require('preparation' in index,'preparation release required')
                self.preparation(index['preparation'],index['custody'])
            if op=='R03':
                require('lease' in index,'lease record required')
                self.leases(index['lease'])
                require(index['lease'].get('chip_id')==index['custody']['chip_id'],'handoff chip lease mismatch')
                require(index['lease'].get('custodian_id')==index['custody']['to_custodian'],'handoff custodian lease mismatch')
                require(nonempty(index['custody'].get('mount_id')) and index['lease'].get('sample_mount_id')==index['custody']['mount_id'],'handoff mount lease mismatch')
        else:
            require(set(index)=={'scope'},'scope evidence required')
            r=index['scope'];require(r.get('plan_id') and r.get('unknowns_resolved_in_fixture') is True,'scope unresolved')
        return {'status':'SYNTHETIC_METADATA_ACCEPTED','operation_id':op,'physical_execution_enabled':False,'physical_qualification':'HOLD_QUALIFICATION','scientific_observation_generated':False}

    def characterization(self,r):
        require(r.get('chip_id') and r.get('mount_id') and r.get('configuration_revision'),'characterization identity missing')
        require(r.get('region_chip_ids')=={x:r['chip_id'] for x in ['HB','Array1','Array2']},'characterization region identity mismatch')
        require(set(r.get('path_receipts',{}))=={'HB_Rxx','HB_Rxy','HB_contacts','subarray_transition','subarray_magnetotransport','voltmeter_offset','noise_floor'},'characterization path missing')
        require(all(nonempty(v) for v in r['path_receipts'].values()),'empty characterization path')
        require(r.get('calibration_receipt_id') and r.get('terminal_map_revision'),'characterization calibration missing')
        require(r.get('source_outcome_ids')==[] and r.get('scientific_values') is None,'source/observation contamination')
        require(r.get('apparent_plateau_certifies_quantization') is False,'ordinary plateau is not precision quantization')
        require(r.get('HB_density_is_direct_subarray_measurement') is False,'Hall-bar proxy cannot become direct array measurement')

    def measurement(self,r,op):
        require(all(nonempty(r.get(k)) for k in MEASUREMENT_FIELDS),'measurement lineage missing')
        require(all(unique_strings(r.get(k)) for k in LIST_FIELDS),'measurement list lineage missing')
        require(re.fullmatch('[0-9a-f]{64}',r['bundle_hash']) is not None,'invalid bundle digest')
        require(r.get('new_observation') is False,'fixtures may not claim new observation')
        require(r.get('scientific_values') is None,'no scientific values in metadata fixtures')
        require(r.get('source_outcome_ids')==[],'source outcome contamination')
        require(r.get('source_derived_threshold') is False,'source-value reward prohibited')
        require(r['ratio_units']=='dimensionless','ratio unit unresolved')
        require(r['ratio_direction']==f"{r['test_id']}/{r['reference_id']}",'ratio orientation mismatch')
        require(r['reference_id']!=r['test_id'],'reference/test identity alias')
        pair={r['reference_id'],r['test_id']}
        if op in DIRECT_PAIRS: require(pair==DIRECT_PAIRS[op],'wrong source comparison edge')
        if op=='R07': require(pair in ({'Array1','REF100'},{'Array2','REF100'}),'wrong transfer edge')
        if op=='R09': require(pair in ({'Array1','Array2'},{'Array1','REF100'},{'Array2','REF100'}) and r.get('intentional_nonquantizing') is True,'off-plateau semantics missing')
        if op=='R10':
            require(pair=={'Array1','Array2'},'wrong high-bias pair')
            require(r.get('performance_test_permit')=='SYNTHETIC_PERMIT','high-bias permit missing')
            require(r.get('screen_kind') in {'short_screen','long_record'},'screen identity missing')
            if r['screen_kind']=='short_screen': require(r['uncertainty_semantics']=='reading_SD' and r.get('allan_used') is False,'short-screen uncertainty mismatch')
        if op=='R11':
            require('REF12K9' in pair and len(pair & {'Array1','Array2'})==1,'external identity unresolved')
            require(r.get('source_SI4_identity_resolved') is False,'do not claim historical SI4 identity resolved')
            require(r.get('runtime_region_evidence')=='SYNTHETIC_REGION_RECEIPT','new-run region evidence missing')
        require(r['field_sign'] in {'positive','negative','zero_characterization'},'field sign unresolved')
        regions=pair & {'Array1','Array2','HB'}
        require(r.get('region_chip_ids')=={x:r['chip_id'] for x in regions},'chip/region mismatch')
        require(r.get('per_device_current_records') and set(r['per_device_current_records'])==pair,'per-device current missing')
        require(r.get('per_device_power_records') and set(r['per_device_power_records'])==pair,'per-device power missing')
        for k in ('per_device_current_records','per_device_power_records'):
            require(all(nonempty(x) for x in r[k].values()),'empty per-device record')
        baths=r.get('reference_baths',{})
        if 'REF100' in pair: require(baths.get('REF100')=='OIL100','100-ohm bath mismatch')
        if 'REF12K9' in pair: require(baths.get('REF12K9')=='AIR12K9','12k9 bath mismatch')
        require(r.get('bath_stability_record_ids') and all(nonempty(x) for x in r['bath_stability_record_ids']),'bath evidence missing')
        start,end=instant(r.get('start')),instant(r.get('end'));require(start<end,'invalid acquisition interval')
        ts=[instant(x) for x in r['raw_timestamps']]
        require(ts==sorted(ts) and len(ts)==len(set(ts)) and all(start<=t<=end for t in ts),'timestamp order/range')
        require(len(r['raw_ratio_record_ids'])==len(ts)==len(r['per_reading_SD_record_ids']),'raw evidence length mismatch')
        require(r.get('independent_unit') in {'within_run_readings','new_chip','new_cooldown','new_remount'},'repeat unit missing')
        require(r.get('independent_chip_count') is None,'synthetic readings cannot establish chip count')

    def calibration(self,c,m):
        require(nonempty(c.get('revision')) and c.get('configuration_revision')==m['configuration_revision'],'calibration configuration mismatch')
        require(c.get('method_revision')==m['method_revision'],'calibration method mismatch')
        require(c.get('sample_mount_id')==m['mount_id'],'calibration mount mismatch')
        require(c.get('terminal_map_revision')==m['terminal_map_revision'],'calibration terminal map mismatch')
        require(set(c.get('calibration_ids',[]))==set(m['calibration_ids']),'calibration ID mismatch')
        require(set(c.get('instrument_ids',[]))==set(m['instrument_ids']),'calibration instrument mismatch')
        require(instant(c.get('valid_from'))<=instant(m['start']) and instant(c.get('valid_until'))>=instant(m['end']),'calibration expired during acquisition')
        require(c.get('before_check') and c.get('after_check'),'calibration brackets missing')
        require(c.get('reference_change') is False and c.get('configuration_change') is False,'configuration/reference change requires requalification')

    def measurement_lease(self,l,m):
        self.leases(l)
        require(m['lease_ids']==[l.get('lease_id')],'measurement lease ID mismatch')
        require(l.get('job_id')==m['job_id'] and l.get('custodian_id')==m['custodian_id'],'measurement lease ownership mismatch')
        require(l.get('sample_mount_id')==m['mount_id'],'measurement mount lease mismatch')
        require(unique_strings(m.get('physical_resource_ids')) and set(l['resources'])==set(m['physical_resource_ids']),'physical resource lease mismatch')
        require(l.get('chip_id')==m['chip_id'],'physical chip lease mismatch')

    def custody(self,c):
        keys=['event_id','sample_id','chip_id','from_custodian','to_custodian','from_support','to_support','carrier_id','condition_before','condition_after','orientation_evidence','acceptance_id']
        require(all(nonempty(c.get(k)) for k in keys),'custody lineage missing')
        require(c.get('receiver_accepted') is True and c.get('receiving_support_observed') is True and c.get('identity_occupancy_observed') is True,'custody receipt not observed')
        require(c.get('releases_previous_support') is False,'fixture cannot release physical support')
        require(c.get('unresolved_hazards')==[],'custody hazard unresolved')
        require(instant(c.get('support_observed_at'))<=instant(c.get('accepted_at')),'acceptance precedes support')

    def preparation(self,p,c):
        for key in ['supplier_lot','wafer_die_id','process_revision','contact_release','doping_release','encapsulation_condition','release_id']:
            require(nonempty(p.get(key)),'preparation evidence missing')
        require(p.get('chip_id')==c['chip_id'],'preparation identity mismatch')
        require(p.get('specialist_release_accepted') is True,'preparation not released')
        require(p.get('process_recipe') is None,'operating recipe prohibited')

    def leases(self,l):
        require(unique_strings(l.get('resources')),'physical resource map missing')
        require(l.get('lease_owner')==l.get('job_id') and nonempty(l.get('job_id')),'lease owner mismatch')
        require(l.get('resource_ids_are_physical') is True,'logical station lease insufficient')
        require(l.get('conflicting_owners')==[],'shared instrument conflict')
        require(l.get('release_requested') is False,'lease release premature')

    def analysis(self,r,op):
        require(r.get('raw_bundle_ids') and r.get('raw_source_class')=='synthetic_metadata_only','raw provenance missing')
        require(r.get('source_outcome_ids')==[],'source results cannot become observations')
        require(r.get('unresolved_equation_holds')==[],'printed equation ambiguity blocks analysis')
        require(r.get('qualified_method_revision')=='SYNTHETIC_APPROVED_METADATA_METHOD','qualified analysis method missing')
        require(r.get('numerical_analysis_performed') is False,'no scientific calculation implemented')
        require(r.get('covariance_record') and r.get('exclusion_log'),'covariance/exclusions missing')
        if op=='R13':
            require(r.get('source_graph_edge_ids')==['E01','E02','E03','E04','E05'],'source network edges invalid')
            require(r.get('simple_loop_count')==3 and r.get('independent_cycle_count')==2,'graph cycle distinction lost')
            require(r.get('derived_paths_are_independent') is False,'derived paths are dependent')
            require(r.get('claims_exact_absolute_quantization') is False,'agreement is not absolute proof')
            require(r.get('branch_statuses') and 'R09' in r['branch_statuses'] and 'R10' in r['branch_statuses'] and 'R11' in r['branch_statuses'],'optional/negative controls omitted')
            allowed={'completed_observation','partial_evidence','failed_observation','held_qualification','unattempted','analysis_hold'}
            require(all(x in allowed for x in r['branch_statuses'].values()),'invalid analysis branch status')
            require(set(r.get('edge_statuses',{}))==set(r['source_graph_edge_ids']),'edge coverage incomplete')
            require(all(x in allowed for x in r['edge_statuses'].values()),'invalid edge status')
            acquired=r.get('acquired_direct_edge_ids')
            require(isinstance(acquired,list) and len(acquired)==len(set(acquired)) and set(acquired)<=set(r['source_graph_edge_ids']),'acquired edge inventory invalid')
            require(set(acquired)=={e for e,v in r['edge_statuses'].items() if v in {'completed_observation','partial_evidence','failed_observation'}},'source edges cannot masquerade as acquired edges')

    def closeout(self,r):
        require(isinstance(r.get('started_jobs'),list) and bool(r['started_jobs']),'started-job inventory required')
        require(len(r['started_jobs'])==len(set(r['started_jobs'])),'duplicate started jobs')
        require(set(r.get('terminal_acknowledged_jobs',[]))==set(r['started_jobs']),'unjoined started jobs')
        require(r.get('pending_jobs')==[],'pending job prevents release')
        require(r.get('analysis_success_required') is False,'analysis may not gate physical closeout')
        evidence=r.get('independent_safety_evidence',{})
        require(set(evidence)==SAFE_CHANNELS,'independent safe-state channels missing')
        require(all(nonempty(evidence[k]) and evidence[k].startswith('SYNTHETIC_OBS_') for k in SAFE_CHANNELS),'safe state not independently observed')
        require(len(set(evidence.values()))==len(SAFE_CHANNELS),'distinct safety-channel observations required')
        require(r.get('safe_basis')=='independent_qualified_observations','stop/timer/icon is not safety')
        require(r.get('custody_accepted') is True and r.get('storage_accepted') is True and r.get('post_condition_id'),'receiving custody/storage incomplete')
        require(r.get('lease_release_ack') is True,'lease release unacknowledged')
        require(set(r.get('branch_statuses',{}))=={f'R{i:02d}'for i in range(3,12)},'branch status missing')
        require(all(x in {'completed_observation','partial_evidence','failed_observation','held_qualification','unattempted'} for x in r['branch_statuses'].values()),'invalid branch completion status')
        require(r.get('physical_release_performed') is False,'metadata test cannot release hardware')


def measurement_fixture(op='R05', pair=('Array1','Array2')):
    """Synthetic names and timestamps only; no measured ratio/current/field values."""
    test,ref=pair
    m={'id':'SYNTHETIC_M','origin':'synthetic_evaluator_fixture','provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':op,'kind':'measurement'}
    m.update({k:'SYNTHETIC_'+k for k in MEASUREMENT_FIELDS})
    m.update({k:['SYNTHETIC_'+k] for k in LIST_FIELDS})
    m.update({'bundle_hash':'a'*64,'sample_id':'SYNTHETIC_SAMPLE','chip_id':'SYNTHETIC_CHIP','test_id':test,'reference_id':ref,'ratio_direction':test+'/'+ref,'ratio_units':'dimensionless','new_observation':False,'scientific_values':None,'source_outcome_ids':[],'source_derived_threshold':False,'field_sign':'positive','region_chip_ids':{x:'SYNTHETIC_CHIP' for x in set(pair)&{'Array1','Array2','HB'}},'per_device_current_records':{x:'SYNTHETIC_CURRENT_'+x for x in pair},'per_device_power_records':{x:'SYNTHETIC_POWER_'+x for x in pair},'reference_baths':{'REF100':'OIL100','REF12K9':'AIR12K9'},'bath_stability_record_ids':['SYNTHETIC_BATH'],'start':'2000-01-01T00:00:00Z','end':'2000-01-01T00:00:02Z','raw_timestamps':['2000-01-01T00:00:01Z'],'independent_unit':'within_run_readings','independent_chip_count':None,'intentional_nonquantizing':True,'performance_test_permit':'SYNTHETIC_PERMIT','screen_kind':'short_screen','uncertainty_semantics':'reading_SD','allan_used':False,'source_SI4_identity_resolved':False,'runtime_region_evidence':'SYNTHETIC_REGION_RECEIPT'})
    c={'id':'SYNTHETIC_C','origin':'synthetic_evaluator_fixture','provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':op,'kind':'calibration','revision':'SYNTHETIC_REV','configuration_revision':m['configuration_revision'],'calibration_ids':m['calibration_ids'],'instrument_ids':m['instrument_ids'],'valid_from':'1999-01-01T00:00:00Z','valid_until':'2001-01-01T00:00:00Z','before_check':'SYNTHETIC_BEFORE','after_check':'SYNTHETIC_AFTER','reference_change':False,'configuration_change':False}
    c.update({'method_revision':m['method_revision'],'sample_mount_id':m['mount_id'],'terminal_map_revision':m['terminal_map_revision']})
    m['lease_ids']=['SYNTHETIC_LEASE_ID'];m['physical_resource_ids']=['SYNTHETIC_CHIP_RESOURCE','SYNTHETIC_CCC_RESOURCE','SYNTHETIC_CRYOSTAT_RESOURCE']
    if 'REF100' in pair:m['physical_resource_ids'].append('SYNTHETIC_REF100_RESOURCE')
    if 'REF12K9' in pair:m['physical_resource_ids'].append('SYNTHETIC_REF12K9_RESOURCE')
    l={'id':'SYNTHETIC_L','origin':'synthetic_evaluator_fixture','provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':op,'kind':'lease','lease_id':'SYNTHETIC_LEASE_ID','lease_owner':m['job_id'],'job_id':m['job_id'],'custodian_id':m['custodian_id'],'sample_mount_id':m['mount_id'],'chip_id':m['chip_id'],'resources':m['physical_resource_ids'],'resource_ids_are_physical':True,'conflicting_owners':[],'release_requested':False}
    return m,c,l

def closeout_fixture():
    return {'id':'SYNTHETIC_CLOSE','origin':'synthetic_evaluator_fixture','provider':'SYNTHETIC_QUALIFIED_PROVIDER','status':'accepted','operation_id':'R14','kind':'closeout','started_jobs':['SYNTHETIC_JOB_A','SYNTHETIC_JOB_FAILED'],'terminal_acknowledged_jobs':['SYNTHETIC_JOB_A','SYNTHETIC_JOB_FAILED'],'pending_jobs':[],'analysis_success_required':False,'independent_safety_evidence':{x:'SYNTHETIC_OBS_'+x for x in SAFE_CHANNELS},'safe_basis':'independent_qualified_observations','custody_accepted':True,'storage_accepted':True,'post_condition_id':'SYNTHETIC_CONDITION','lease_release_ack':True,'branch_statuses':{f'R{i:02d}':('failed_observation' if i==5 else 'unattempted') for i in range(3,12)},'physical_release_performed':False}
