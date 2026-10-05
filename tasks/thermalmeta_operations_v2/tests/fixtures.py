"""Synthetic identity/Boolean tokens; no temperature or physical data arrays."""
from runtime.symbolic_guard import fixture_receipt as r, FAMILIES, CONDITIONS

def plan():
    return [dict(slot_id=f'SLOT_{f}_{d}', condition_id=f'COND_{f}_{d}', specimen_id=f'SPEC_{f}_DEMO_001', repeat_kind='base', approved=True) for f in FAMILIES for d in ('X','Y')]

def chain(f='CLOAK', specimen=None, revision='R0'):
    specimen = specimen or f'SPEC_{f}_DEMO_001'
    prefix = specimen+'_'+revision
    common=dict(paper_id='thermalmeta-2024-49630',sample_family_id=f,design_id=f'DES_{f}_DEMO',design_revision=revision,specimen_id=specimen,service_job_id='JOB_'+prefix,material_lot_ids=['LOT_METAL','LOT_PDMS','LOT_BACKGROUND'])
    result=[]
    core='PDMS' if f=='CLOAK' else 'background_encapsulant'
    for kind in ('design','materials','lattice','intermediate','specimen'):
        fields=dict(common,record_type=kind,object_id=prefix+'_'+kind,parent_id=result[-1]['object_id'] if result else None)
        if kind=='design': fields['geometry_qualification']=True
        if kind in ('intermediate','specimen'): fields['core_assignment']=core
        if kind=='specimen': fields.update(lattice_parent_id=result[2]['object_id'],intermediate_parent_id=result[3]['object_id'],safe_release=True,dry_ambient=True)
        result.append(r('RCPT_'+prefix+'_'+kind,**fields))
    return result

def reseal(record, **changes):
    p=dict(record); p.update(changes); p.pop('content_hash',None)
    rid=p.pop('receipt_id'); p.pop('evidence_class',None); p.pop('issuer_role',None); p.pop('valid',None)
    return r(rid,**p)

def calibration():
    return r('CAL_RECEIPT',calibration_id='CAL_001',reference_id='REF_001',configuration_id='CAM_001',uncertainty_contract_id='UNC_001',current=True,bracketing_valid=True)

def mount(slot, suffix=''):
    return r('MOUNT_RECEIPT_'+slot['slot_id']+suffix,specimen_id=slot['specimen_id'],condition_id=slot['condition_id'],orientation=slot['condition_id'].split('_')[-1],calibration_id='CAL_001',mount_id='MOUNT_'+slot['slot_id']+suffix,zero_energy=True,dry_ambient=True,qualified_fit=True,registered_transform=True,supported_carrier=True)

def handoff(slot, run_id, suffix=''):
    return r('HANDOFF_'+run_id,run_id=run_id,mount_id='MOUNT_'+slot['slot_id']+suffix,specimen_id=slot['specimen_id'],interlocks_valid=True,acceptance='accepted')

def transient(run_id):
    return r('TRANSIENT_'+run_id,run_id=run_id,dataset_id='DATA_'+run_id,timebase='synthetic_order_only',configuration_id='CAM_001',data_origin='synthetic_metadata_only',stream_integrity=True,boundary_metadata=True)

def stable(run_id):
    return r('STABLE_'+run_id,run_id=run_id,data_origin='synthetic_metadata_only',qualified_stable=True,drift_contract=True,uncertainty_valid=True)

def result(slot,run_id):
    return r('RESULT_'+run_id,run_id=run_id,dataset_id='DATA_'+run_id,condition_id=slot['condition_id'],calibration_id='CAL_001',profile_direction='transverse' if 'ROTATOR45' in slot['condition_id'] else 'parallel',masks_registered=True,transform_registered=True,measured_boundaries_present=True,ambient_present=True,uncertainty_valid=True,data_hash_valid=True,data_origin='synthetic_metadata_only')

def release(slot,run_id,suffix=''):
    return r('RELEASE_'+run_id+suffix,run_id=run_id,specimen_id=slot['specimen_id'],zero_energy=True,cool=True,dry=True,supported_carrier=True,receiver_accepts=True,condition_assessed=True)

def controls():
    return r('CONTROLS',matched=True,independent_identity=True,data_origin='synthetic_metadata_only',denominator_safe=True,covers_conditions=sorted(CONDITIONS))

def assessment():
    return r('ASSESSMENT',claim_kind='synthetic_contract_pass_only',source_holds_preserved=True,numerical_computation_performed=False,uncertainty_contract_present=True)

def ready(ep):
    for f in FAMILIES: ep.receive(chain(f))
    ep.calibrate(calibration())
    return ep

def start(ep,index=0,run_id='RUN_001',suffix=''):
    slot=ep.plan[index]; ep.mount(slot['slot_id'],mount(slot,suffix)); ep.handoff(run_id,handoff(slot,run_id,suffix)); return slot

def capture(ep,slot,run_id='RUN_001'):
    ep.observe('P12',transient(run_id)); ep.observe('P13',stable(run_id)); ep.observe('P14',result(slot,run_id))

def finish(ep,slot,run_id='RUN_001'):
    capture(ep,slot,run_id); ep.release(release(slot,run_id)); ep.retrieve()
