"""Synthetic document-ID fixtures. No pixels, measurements, physics or device commands."""
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contract import EvidenceLedger, digest, load_contract, TARGETS, ALL_BRANCHES

def measurement(branch,kind,state,condition='sphere'):
    optical=kind=='optical'
    rid=f'fixture.{branch}.{kind}.{condition}'
    return dict(record_id=rid,specimen_id=f'fixture.specimen.{branch}',state_id=state,roi_id=f'fixture.ROI.{branch}',calibration_id=f'fixture.calibration.{kind}',frame_id='FRAME_DETECTOR' if optical else 'FRAME_SEM',raw_record_sha256=digest({'fixture_record_token':rid}),modality=kind,mode=('transmission' if branch in ('E01','E02') else 'reflection') if optical else None,focus_receipt_id=f'fixture.focus.{branch}.{condition}',detector_scale_receipt_id=f'fixture.scale.{kind}',data_quality_receipt_id=f'fixture.quality.{rid}',outcome='not_assessed',origin='independent_fixture')

def payloads():
    p={}
    p['R01']=dict(doi='10.1038/ncomms1211',rights_scope='original_only',main_pages=6,si_pages=7,dedup_receipt_id='fixture.dedup',source_version_id='fixture.source.version',publisher_exports=False,repeat_policy_id='fixture.repeat.plan',metric_policy_id='fixture.metric.plan',exclusion_policy_id='fixture.exclusion.plan')
    p['R02']={b:dict(specimen_id=f'fixture.specimen.{b}',material_id=f'M{int(b[1:])+1:02}',state_id=f'fixture.{b}.received',container_id=f'fixture.carrier.{b}',lot_id=f'fixture.material.lot.{b}',surface_identity='unresolved' if b=='E04' else f'fixture.surface.{b}',identity_receipt_id=None if b=='E04' else f'fixture.identity.{b}',status='HELD' if b=='E04' else 'CONTRACT_REVIEWED') for b in TARGETS}
    p['R03']={}
    for b in TARGETS:
        row=dict(specimen_id=f'fixture.specimen.{b}',parent_state_id=f'fixture.{b}.received',state_id=f'fixture.{b}.prepared',closed_service_job_id=f'fixture.job.{b}',certificate_id=f'fixture.cert.{b}',geometry_certificate_id=f'fixture.geometry.{b}',surface_condition_id=f'fixture.condition.{b}',roi_map_id=f'fixture.map.{b}',status='CONTRACT_REVIEWED')
        if b=='E04':row={k:('HELD' if k=='status' else v if k=='specimen_id' else None) for k,v in row.items()}
        p['R03'][b]=row
    p['R04']={b:dict(status='HELD' if b=='E04' else 'CONTRACT_REVIEWED',reference=None if b=='E04' else measurement(b,'SEM',f'fixture.{b}.prepared'),post_service_state_id=None if b=='E04' else f'fixture.{b}.after_sem',perturbation_receipt_id=None if b=='E04' else f'fixture.perturbation.{b}') for b in TARGETS}
    p['R05']=dict(sphere_lots=[dict(lot_id=f'fixture.sphere.{i}',nominal_diameter_um=n,distribution_certificate_id=f'fixture.distribution.{i}',chemistry_certificate_id=f'fixture.chemistry.{i}') for i,n in enumerate([1,3,4.74,10,50])],sil_controls={'SIL_0p5mm':dict(material_id='M06',objective_magnification=80,compatibility_receipt_id='fixture.compatibility.small'),'SIL_2p5mm':dict(material_id='M07',objective_magnification=40,compatibility_receipt_id='fixture.compatibility.large')},star_sphere_diameter_um=None,contained_stock_receipt_id='fixture.containment.stock')
    p['R06']={}
    for b in TARGETS:
        row=dict(status='CONTRACT_REVIEWED',specimen_id=f'fixture.specimen.{b}',baseline_state_id=f'fixture.{b}.after_sem',child_state_id=f'fixture.{b}.sphere',contact_receipt_id=f'fixture.contact.{b}',sphere_lot_id='fixture.sphere.2',coverage_receipt_id=f'fixture.coverage.{b}',bare_state_id=f'fixture.{b}.after_sem')
        if b=='E04':row={k:('HELD' if k=='status' else v if k=='specimen_id' else None) for k,v in row.items()}
        p['R06'][b]=row
    p['R06']['C01']=dict(bare_specimen_id='fixture.specimen.E03',bare_state_id='fixture.E03.after_sem',matched_specimen_receipt_id='fixture.bare.equivalence',sil_0p5_contact_receipt_id='fixture.sil.small.contact',sil_2p5_contact_receipt_id='fixture.sil.large.contact',sil_0p5_child_state_id='fixture.E03.SIL_0p5mm',sil_2p5_child_state_id='fixture.E03.SIL_2p5mm')
    for op,bs in [('R07',['E01','E02']),('R08',['E03','E04'])]:
        p[op]={b:dict(status='HELD' if b=='E04' else 'CONTRACT_REVIEWED',optical=None if b=='E04' else measurement(b,'optical',f'fixture.{b}.sphere'),object_frame='FRAME_OBJECT',virtual_frame='FRAME_VIRTUAL',registration_receipt_id=None if b=='E04' else f'fixture.registration.{b}') for b in bs}
    p['R09']={}
    for c in ['bare','SIL_0p5mm','SIL_2p5mm']:
        p['R09'][c]=dict(optical=measurement('E03','optical','fixture.E03.after_sem' if c=='bare' else f'fixture.E03.{c}',c),objective_magnification=40 if c=='SIL_2p5mm' else 80,contact_receipt_id='fixture.sil.small.contact' if c=='SIL_0p5mm' else 'fixture.sil.large.contact' if c=='SIL_2p5mm' else 'fixture.bare.contact',matched_specimen_receipt_id='fixture.bare.equivalence')
    p['R10']={b:dict(evidence_class='illustrated_array_unqualified_processing' if b=='C04' else 'text_only',status='SOURCE_CONTEXT_ONLY',new_data=False,limitation=f'fixture.limitation.{b}') for b in ['C02','C03','C04','E05']}
    p['R11']={}
    for b in (*TARGETS,'C01'):
        ob='E03' if b=='C01' else b
        row=dict(status='CONTRACT_REVIEWED',optical_record_id=f'fixture.{ob}.optical.'+('bare' if b=='C01' else 'sphere'),reference_record_id=f'fixture.{ob}.SEM.sphere',correspondence='documented_equivalence',equivalence_receipt_id=f'fixture.equivalence.{b}',limitation_id=f'fixture.limit.{b}',metric_policy_id='fixture.metric.plan',uncertainty_receipt_id=f'fixture.uncertainty.{b}',reviewer_id='fixture.independent.reviewer',resolution_certified=False)
        if b=='E04':row.update(status='HELD',optical_record_id=None,reference_record_id=None)
        p['R11'][b]=row
    p['R12']={b:dict(status='UNRUN',source_method_receipt_id=f'fixture.method.{b}',code_run=False,simulation_run=False,generated_data=False) for b in ['N01','N02','N03','N04']}
    return p

def make_fixture(root=ROOT,mutate=None):
    ops,core=load_contract(root)
    ps=payloads(); receipts={}; ledger=EvidenceLedger(root,'fixture.campaign','fixture.epoch','fixture.plan',{})
    for op in ops:
        oid=op['id']
        if oid=='R13':
            ps[oid]=dict(archive_receipt_hashes={k:v['receipt_hash'] for k,v in ledger.completed.items()},branch_dispositions=ledger.final_branch_dispositions(),specimen_dispositions={b:dict(specimen_id=f'fixture.specimen.{b}',destination_id=f'fixture.archive.{b}',disposition='quarantine' if b=='E04' else 'archive') for b in TARGETS},safe_state_receipt_id='fixture.safe',containment_receipt_id='fixture.containment',service_release_id='fixture.release',failure_event_hashes=[],scientific_execution_complete=False)
        if oid in ['R01','R05','R10']:results={b:'SOURCE_CONTEXT_ONLY' for b in op['branch_ids']}
        elif oid=='R12':results={b:'UNRUN' for b in op['branch_ids']}
        elif oid=='R09':results={'C01':'CONTRACT_REVIEWED'}
        elif oid=='R06':results={b:ps[oid][b]['status'] for b in TARGETS};results['C01']='CONTRACT_REVIEWED'
        elif oid=='R13':results=ps[oid]['branch_dispositions']
        else:results={b:ps[oid][b]['status'] for b in op['branch_ids']}
        r=dict(receipt_id=f'fixture.receipt.{oid}',operation_id=oid,campaign_id='fixture.campaign',epoch='fixture.epoch',frozen_plan_id='fixture.plan',semantic_core_sha256=core,origin='independent_fixture',qualification_refs={u:f'fixture.qualification.{u}' for u in op['unresolved_input_refs']},status='ACCEPTED',branch_results=results,input_receipt_hashes={d:ledger.completed[d]['receipt_hash'] for d in op['depends_on']},payload=ps[oid],physical_execution=False)
        receipts[r['receipt_id']]=copy.deepcopy(r)
        # Fixture construction is evaluator-side. Rebuild with full immutable input;
        # replay earlier actions to derive the next dependency hash without editing it.
        ledger=EvidenceLedger(root,'fixture.campaign','fixture.epoch','fixture.plan',receipts)
        for old in receipts:ledger.propose({'operation_id':receipts[old]['operation_id'],'evidence_id':old})
    if mutate:mutate(receipts)
    return receipts

def new_ledger(receipts=None,root=ROOT):
    return EvidenceLedger(root,'fixture.campaign','fixture.epoch','fixture.plan',make_fixture(root) if receipts is None else receipts)

def run_until(ledger,stop=None):
    for i in range(1,14):
        oid=f'R{i:02}'
        if oid==stop:break
        ledger.propose(dict(operation_id=oid,evidence_id=f'fixture.receipt.{oid}'))
    return ledger
