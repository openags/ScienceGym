"""Independent synthetic record probes; no devices, source assets, or simulation.
Run from any directory with python3 -B. Writes only the requested review receipt.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys, datetime
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hydrogel_author_contract',ROOT/'tests/contract.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
rows=[]
def probe(name, mutator, selected=None, expected='reject'):
    context,events=c.fixture(selected)
    try:
        mutator(context,events)
        result=c.validate(context,events)
        actual='reject' if result else 'accept'
        errors=result[:6]
    except Exception as exc:
        actual='exception';errors=[type(exc).__name__+': '+str(exc)]
    rows.append({'name':name,'expected':expected,'actual':actual,'passed':actual==expected,'diagnostic':errors})
def sync(context,events,jid):
    job=context['jobs'][jid]
    for e in events:
        if e['job_id']==jid:
            for k in list(e):
                if k in job:e[k]=copy.deepcopy(job[k])
def remove_bound(context,events,key):
    jid=next(iter(context['jobs']))
    context['jobs'][jid].pop(key,None)
    for e in events:
        if e['job_id']==jid:e.pop(key,None)
def null_bound(context,events,key):
    jid=next(iter(context['jobs']));context['jobs'][jid][key]=None;sync(context,events,jid)
def wrong_parent_condition(context,events):
    afm=[j for j in context['jobs'].values() if j['branch_id']=='BEAM_AFM']
    j=next(j for j in context['jobs'].values() if j['branch_id']=='BEAM_POWER')
    wrong=next(p for p in afm if p['condition_id']!=j['condition_id'])
    j['parents']=[p for p in j['parents'] if context['jobs'][p]['branch_id']!='BEAM_AFM']+[wrong['job_id']]
def merge_angle_specimens(context,events):
    a=[j for j in context['jobs'].values() if j['branch_id']=='ANGLE_IMAGE_MAIN']
    b=[j for j in context['jobs'].values() if j['branch_id']=='ANGLE_IMAGE_VIDEO']
    sid=a[-1]['specimen_id'];version=a[-1]['output_version']
    for j in b:
        j['specimen_id']=sid;j['input_version']=version;j['output_version']=version+1;version+=1;sync(context,events,j['job_id'])
def merge_beam_specimens(context,events):
    a=[j for j in context['jobs'].values() if j['branch_id']=='BEAM_LINEAGES']
    a[1]['specimen_id']=a[0]['specimen_id'];a[1]['input_version']=a[0]['output_version'];a[1]['output_version']=a[1]['input_version']+1;sync(context,events,a[1]['job_id'])
def stale_card_in_job(context,events):
    jid=next(iter(context['jobs']));context['jobs'][jid]['card_revision']='obsolete';sync(context,events,jid)
def nonmatching_authoritative_release(context,events):
    j=next(j for j in context['jobs'].values() if j['service_id']=='RELEASE')
    j['optical_release_specimen_id']='different_specimen'
    j['optical_release_version']=999
    j['optical_release_record_id']=None

def concurrent_same_specimen(context,events):
    js=[j for j in context['jobs'].values() if j['branch_id']=='PREP_FORM'][:2]
    js[1]['specimen_id']=js[0]['specimen_id'];sync(context,events,js[1]['job_id'])
    chunks={j['job_id']:[e for e in events if e['job_id']==j['job_id']] for j in js}
    remaining=[e for e in events if e['job_id'] not in chunks]
    events[:]=chunks[js[0]['job_id']][:5]+chunks[js[1]['job_id']][:5]+[chunks[js[0]['job_id']][-1],chunks[js[1]['job_id']][-1]]+remaining
    for i,e in enumerate(events,1):e['sequence']=i

def quarantine(context,events):
    jid=next(iter(context['jobs']));context['jobs'][jid]['damage_state']='quarantined';sync(context,events,jid)

probe('baseline',lambda x,y:None,expected='accept')
for key in ['specimen_id','carrier_id','fixture_id','calibration_id','raw_record_id','record_hash','attempt_id','card_revision']:
    probe('remove_bound_'+key,lambda x,y,k=key:remove_bound(x,y,k))
    probe('null_bound_'+key,lambda x,y,k=key:null_bound(x,y,k))
for key in ['condition_allocations','lineage']:
    probe('missing_required_'+key,lambda x,y,k=key:x.pop(k,None))
probe('wrong_parent_condition',wrong_parent_condition)
probe('merge_angle_main_video',merge_angle_specimens,['ANGLE_IMAGE_MAIN','ANGLE_IMAGE_VIDEO'])
probe('merge_SI15_main50_beams',merge_beam_specimens,['BEAM_LINEAGES'])
probe('stale_card_job_and_event',stale_card_in_job)
probe('release_evidence_wrong_specimen_version',nonmatching_authoritative_release)
probe('same_specimen_concurrent_jobs',concurrent_same_specimen,['PREP_FORM'])
probe('quarantined_specimen',quarantine)
probe('extra_actor_hazard_action',lambda x,y:y[0].update(robot_action='start_laser'))
for field,value in [('selected_branches',[{}]),('plans',None),('jobs',None),('cards',None),('controls',None),('conflict_resolutions',None)]:
    probe('invalid_nested_type_'+field,lambda x,y,k=field,v=value:x.update({k:v}))
probe('invalid_job_record_type',lambda x,y:x['jobs'].__setitem__(next(iter(x['jobs'])),None))
probe('invalid_plan_record_type',lambda x,y:x['plans'].__setitem__(next(iter(x['plans'])),None))
probe('unknown_event_key',lambda x,y:y[0].update(unapproved_service_program='opaque'))
probe('valid_authority_replaced_by_source',lambda x,y:x.update(authority_id='source_reference'))
probe('release_optical_missing',lambda x,y:next(j for j in x['jobs'].values() if j['service_id']=='RELEASE').update(optical_free_movement=False))
probe('guard_open',lambda x,y:y[0].update(guard_closed=False))
probe('source_outcome_exposed',lambda x,y:x.update(actor_source_targets_exposed=True))
probe('remove_control',lambda x,y:x.update(controls={}))
probe('duplicate_sequence',lambda x,y:y[1].update(sequence=1))
probe('no_events',lambda x,y:y.clear())
receipt={'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent synthetic-record adversarial probes only; neither physical execution nor scientific reproduction','reviewer':'independent_contract_reviewer','contract_sha256':hashlib.sha256((ROOT/'tests/contract.py').read_bytes()).hexdigest(),'cases':rows,'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows)}
output=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'review/adversarial_receipt.json'
if output.resolve().parent != (ROOT/'review').resolve():raise ValueError('receipt must stay in review directory')
output.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'cases':len(rows),'passed':receipt['passed'],'failed':receipt['failed'],'receipt':output.name}))
for r in rows:
    if not r['passed']:print(r['name'],r['actual'],r['diagnostic'])
sys.exit(bool(receipt['failed']))
