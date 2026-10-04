"""Independent bounded-contract review. No hardware, source assets or publication.
Run with a task root argument outside the packet, or from its review/ directory.
"""
import sys
sys.dont_write_bytecode = True
import argparse, copy, hashlib, itertools, json, shutil, tempfile
from collections import Counter
from pathlib import Path


def run(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root / 'tests'))
    import contract as c
    from verify_export import verify as verify_export
    from verify_package import verify as verify_package
    results = []
    def record(name, passed, kind, details=None):
        row = dict(name=name, passed=bool(passed), kind=kind)
        if details is not None: row['details'] = details
        results.append(row)
    branches = ['PREPARE','REFERENCE','CALIBRATE','INTERPOLATE','REPEATABILITY','DRIFT_NOISE']
    for profile in c.PROFILES:
        record('default_hold_'+profile, not c.validate(*c.fixture(['FLOW_HOLD'],profile)), 'positive')
        for length in range(1, len(branches)+1):
            for selected in itertools.permutations(branches, length):
                record('ordered_branches_'+profile+'_'+'_'.join(selected), not c.validate(*c.fixture(list(selected),profile)), 'positive')
    base_ctx, base_events = c.fixture(['INTERPOLATE','REPEATABILITY','DRIFT_NOISE'])
    def reject(name, fn, kind='negative'):
        ctx, events = copy.deepcopy(base_ctx), copy.deepcopy(base_events)
        fn(ctx, events)
        record(name, bool(c.validate(ctx, events)), kind)
    def event_id(phase, branch=None):
        return next(e['event_id'] for e in base_events if e['phase']==phase and (branch is None or e['job_id']==branch))
    def change_observation(name, phase, key, value, branch=None):
        eid=event_id(phase, branch)
        reject(name, lambda ctx,events:ctx['observations'][eid].__setitem__(key,value))
    for profile in c.PROFILES:
        if profile == base_ctx['profile_id']: continue
        reject('cross_profile_context_only_'+profile,lambda ctx,e,p=profile:ctx.__setitem__('profile_id',p))
        alt,_=c.fixture(base_ctx['selected_branches'],profile)
        reject('cross_profile_whole_registry_'+profile,lambda ctx,e,a=alt:ctx.__setitem__('observations',a['observations']))
    alt,_=c.fixture(base_ctx['selected_branches'],episode_id='synthetic_episode_other')
    reject('cross_episode_whole_registry',lambda ctx,e:ctx.__setitem__('observations',alt['observations']))
    for eid in base_ctx['observations']:
        reject('missing_observation_'+eid,lambda ctx,e,x=eid:ctx['observations'].pop(x))
    for n,event in enumerate(base_events):
        reject('delete_event_'+str(n),lambda ctx,e,i=n:e.pop(i))
        reject('replay_event_'+str(n),lambda ctx,e,i=n:e.insert(i,copy.deepcopy(e[i])))
        reject('injected_actor_receipt_'+str(n),lambda ctx,e,i=n:e[i].__setitem__('accepted',True))
        if n+1<len(base_events):
            def swap(ctx,e,i=n):e[i],e[i+1]=e[i+1],e[i]
            reject('adjacent_order_'+str(n),swap)
    for phase,key,bad in [
        ('TARE:cal_low','zero_observed',False),
        ('WEIGH:cal_low','mass_record_ids',['same','same']),
        ('WEIGH:cal_low','mass_transfer_accepted',False),
        ('MIX:cal_low','endpoint_observed',False),
        ('LABEL_CAP:cal_low','cap_closed_observed',False),
        ('FILTER:cal_low','receiver_aliquot_id','cal_high_aliquot'),
        ('FILTER:cal_low','recovery_checked',False),
        ('PRESENT_REFERENCE:cal_low','aliquot_id','cal_low_bottle'),
        ('READ_REFERENCE:cal_low','instrument_calibration_card','stale'),
        ('CLEAN_REFERENCE:cal_low','cleaning_observed',False),
        ('SERVICE_EXCHANGE:test_a','source_flow_disagreement_resolved',True),
        ('SERVICE_EXCHANGE:test_a','numeric_pump_command_issued',True),
        ('SERVICE_EXCHANGE:test_a','carryover_clearance_id','previous_transfer'),
        ('FREEZE_CALIBRATION','training_samples',['cal_low','cal_mid','test_a']),
        ('FREEZE_CALIBRATION','test_data_used',True),
        ('REQUEST_DARK','laser_off_confirmation',False),
        ('READ_DARK','channel_role','speckle_camera_record'),
        ('READ_DARK','sample_ri_estimate',1.337),
        ('INSPECT','inspection_current',False),
        ('CLEAN_STORE','cleanup_observed',False),
    ]:
        eid=event_id(phase)
        reject('receipt_'+phase+'_'+key,lambda ctx,e,x=eid,k=key,v=bad:ctx['observations'][x]['phase_receipt'].__setitem__(k,v))
    for key in ['episode_id','run_id','sample_id','aliquot_id','parent_bottle_id','reference_id','reference_session','setup_version','profile_id','plate_id','cartridge_id','mount_version','calibration_id','attempt_id']:
        eid=event_id('REQUEST_ACQUISITION:test_a','INTERPOLATE')
        for bad in [None,'', 'stale', True, 1, [], {}]:
            reject('lineage_'+key+'_'+repr(bad),lambda ctx,e,x=eid,k=key,v=bad:ctx['observations'][x]['binding'].__setitem__(k,v))
    for phase,key,bad in [
        ('VERIFY_CLAMP:test_a','clamp_observed',False),
        ('VERIFY_CLAMP:test_a','clamp_closed',1),
        ('SWITCH_SAMPLE:test_a','clamp_closed',False),
        ('SERVICE_EXCHANGE:test_a','exchange_completed',False),
        ('OBSERVE_BUBBLES:test_a','bubbles','unknown'),
        ('REQUEST_ACQUISITION:test_a','reference_fresh',False),
        ('REQUEST_ACQUISITION:test_a','enclosure','open'),
        ('REQUEST_ACQUISITION:test_a','drift_alarm',True),
        ('REQUEST_ACQUISITION:test_a','stationary',False),
        ('SAFE_ISOLATE','isolated',False),
        ('INVALIDATE_CALIBRATION','calibration_invalidated',False),
        ('ARCHIVE','archive_complete',False),
    ]: change_observation('state_'+phase+'_'+key,phase,key,bad)
    for bad in [float('nan'),float('inf'),-float('inf'),1.3327,1.3404,True,1,'1.3343',None]:
        change_observation('range_type_'+repr(bad),'REQUEST_ACQUISITION:test_a','reference_riu',bad)
    for sample in ['cal_mid','cal_high','test_a','test_b']:
        src=event_id('SERVICE_EXCHANGE:cal_low'); dst=event_id('SERVICE_EXCHANGE:'+sample)
        reject('stale_exchange_'+sample,lambda ctx,e,a=src,b=dst:ctx['observations'].__setitem__(b,copy.deepcopy(ctx['observations'][a])))
        src=event_id('VERIFY_CLAMP:cal_low');dst=event_id('VERIFY_CLAMP:'+sample)
        reject('stale_clamp_'+sample,lambda ctx,e,a=src,b=dst:ctx['observations'].__setitem__(b,copy.deepcopy(ctx['observations'][a])))
    pairs=[e['event_id'] for e in base_events if e['phase'].startswith('READ_PAIR:')]
    for dst in pairs[1:]:
        for key in ['frame_pair_id','speckle_record_id','beam_record_id','raw_record_id','record_hash']:
            reject('frame_replay_'+dst+'_'+key,lambda ctx,e,a=pairs[0],b=dst,k=key:ctx['observations'][b].__setitem__(k,ctx['observations'][a][k]))
    change_observation('channel_swap','READ_PAIR:test_a','beam_record_id',base_ctx['observations'][event_id('READ_PAIR:test_a')]['speckle_record_id'])
    for key,value in [('mode','production'),('production_authority',True),('physical_execution',True),('whole_paper_complete',True),('fabrication_performed',True),('source_flow_resolved',True),('service_clearance','qualified_hardware'),('terminal_status','complete')]:
        reject('authority_'+key,lambda ctx,e,k=key,v=value:ctx.__setitem__(k,v))
    for key,value in [('fit_uses_test_data',True),('absolute_accuracy_claim',True),('precision_pass_threshold',6.4e-7),('technical_repeats_are_independent',True),('source_schedule_reproduced',True),('domain_riu',[1.0,2.0]),('preprocessing','refitted_with_tests')]:
        reject('analysis_'+key,lambda ctx,e,k=key,v=value:ctx['calibration'].__setitem__(k,v))
    for key in base_ctx['cards']:
        reject('absent_card_'+key,lambda ctx,e,k=key:ctx['cards'].pop(k))
        reject('unqualified_card_'+key,lambda ctx,e,k=key:ctx['cards'][k].__setitem__('qualified_for_fixture_only',False))
    for ctx,events in [(None,[]),({},[]),([],[]),(True,[]),({'selected_branches':[[]]},[]),({'selected_branches':['FLOW_HOLD','CALIBRATE']},[])]:
        record('malformed_'+repr(ctx),bool(c.validate(ctx,events)),'negative')
    record('static_baseline',not verify_package(root),'static')
    record('export_baseline',not verify_export(root),'export')
    manifest=json.loads((root/'EXPORT_ALLOWLIST.json').read_text())
    for name in manifest['files']:
        with tempfile.TemporaryDirectory() as d:
            clone=Path(d)/'packet';shutil.copytree(root,clone)
            (clone/name).unlink()
            record('missing_export_'+name,bool(verify_export(clone)),'export')
    def export_attack(name, edit):
        with tempfile.TemporaryDirectory() as d:
            clone=Path(d)/'packet';shutil.copytree(root,clone);edit(clone)
            record(name,bool(verify_export(clone)),'export')
    export_attack('empty_private_directory',lambda r:(r/'private').mkdir())
    export_attack('unlisted_text_payload',lambda r:(r/'unlisted.txt').write_text('authored test'))
    def symlink(r):
        (r/'README.md').unlink();(r/'README.md').symlink_to(r/'TASK_DESIGN.md')
    export_attack('symlink_payload',symlink)
    def selfconsistent_extra(r):
        (r/'source.pdf').write_bytes(b'authored fake source extension')
        m=json.loads((r/'EXPORT_ALLOWLIST.json').read_text());m['files'].append('source.pdf');m['payload_sha256']['source.pdf']=hashlib.sha256((r/'source.pdf').read_bytes()).hexdigest();(r/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m))
    export_attack('self_consistent_forbidden_source_extension',selfconsistent_extra)
    def payload_and_hash(r,text):
        (r/'README.md').write_text(text);m=json.loads((r/'EXPORT_ALLOWLIST.json').read_text());m['payload_sha256']['README.md']=hashlib.sha256((r/'README.md').read_bytes()).hexdigest();(r/'EXPORT_ALLOWLIST.json').write_text(json.dumps(m))
    export_attack('machine_path_self_consistent_hash',lambda r:payload_and_hash(r,'/'+'workspace'+'/example'))
    def nonfinite(r):
        m=json.loads((r/'STATUS.json').read_text());m['invalid_number']=float('nan');(r/'STATUS.json').write_text(json.dumps(m));a=json.loads((r/'EXPORT_ALLOWLIST.json').read_text());a['payload_sha256']['STATUS.json']=hashlib.sha256((r/'STATUS.json').read_bytes()).hexdigest();(r/'EXPORT_ALLOWLIST.json').write_text(json.dumps(a))
    export_attack('nonfinite_json_self_consistent_hash',nonfinite)
    summary=dict(passed=all(x['passed'] for x in results),counts=dict(Counter(x['kind'] for x in results)),failures=[x for x in results if not x['passed']],scope='Original synthetic trace contract, static metadata and fixed text-only export; no hardware or scientific validation',results=results)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',nargs='?',default=str(Path(__file__).resolve().parents[1]));parser.add_argument('--output');args=parser.parse_args();report=run(args.root)
    if args.output:Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2));sys.exit(not report['passed'])
