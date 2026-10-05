"""Offline synthetic evidence guards. No hardware, physics, or receipt authentication.

Actor actions contain IDs only. The caller-owned evaluator fixture is trusted test
input, never data supplied by the actor. Its public fixtures prove no real state.
"""
from copy import deepcopy
import math

class ContractError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise ContractError(message)

def number(value, nonnegative=False):
    require(type(value) in (int, float) and math.isfinite(value), 'finite numeric value required')
    require(not nonnegative or value >= 0, 'nonnegative value required')
    return value

def text(value):
    require(type(value) is str and bool(value.strip()), 'nonempty identifier required')
    return value

OPERATIONS = tuple(f'R{i:02}' for i in range(1, 15))
EXPERIMENTS = {'B01':'M1','B02':'M1','B03':'M1','B04':'M2','B05':'M3'}
NUMERICAL = ('A01','A02','A03','A04')
SCOPE = ('specimen_id','design_id','carrier_id','array_id','array_revision','mount_epoch',
         'configuration_epoch','calibration_epoch','branch_id','trial_id','attempt_id','plan_id','lease_id')
KINDS = {
 'R01':('source_review',), 'R02':('plan',), 'R03':('fabrication','custody'),
 'R04':('array',), 'R05':('custody','support'), 'R06':('calibration','coordinates','clock'),
 'R07':('plan','fabrication','array','custody','support','calibration','coordinates','clock','capture_ready'),
 'R08':('plan','measurement','source_observed','calibration','coordinates','clock'), 'R09':('plan','measurement','source_observed','calibration','coordinates','clock','baseline','analysis'),
 'R10':('attempt_terminal',), 'R11':('source_numerical',),
 'R12':('acoustic_off','beam_safe','motion_safe','support_safe'),
 'R13':('custody','support','acoustic_off','beam_safe','motion_safe','support_safe','custody_return'), 'R14':('custody','support','acoustic_off','beam_safe','motion_safe','support_safe','custody_return','archive'),
}
DEPS = {'R01':(), 'R02':('R01',),'R03':('R01','R02'),'R04':('R01','R02'),
 'R05':('R03','R04'),'R06':('R05',),'R07':('R01','R02','R03','R04','R05','R06'),
 'R08':('R07',),'R09':('R08',),'R10':('R09',),'R11':('R01',),'R12':(),
 'R13':('R12',),'R14':('R12','R13')}
SAFE = ('acoustic_off','beam_safe','motion_safe','support_safe')
ROLES = {k:'review' for v in KINDS.values() for k in v}
ROLES.update({k:'safety' for k in SAFE})
ROLES.update({k:'measurement' for k in ('measurement','source_observed','capture_ready','attempt_terminal','array','calibration','coordinates','clock')})
ROLES.update({k:'custody' for k in ('custody','custody_return','support')})
ROLES['fabrication']='fabrication'
RAW_FIELDS = ('raw_ids','raw_hashes','device_clock_ids')
TERMINAL = ('SUCCEEDED','FAILED','INTERRUPTED')

class EvidenceStore:
    """Immutable copy for this finite checker; not a secure production vault."""
    def __init__(self, records):
        require(type(records) is list, 'receipt list required')
        self._records = {}
        for record in records:
            require(type(record) is dict and 'id' in record, 'receipt identifier required')
            rid = text(record['id'])
            require(rid not in self._records, 'duplicate receipt id')
            self._records[rid] = deepcopy(record)
    def get(self, rid):
        require(rid in self._records, 'unknown evaluator-owned evidence id')
        return deepcopy(self._records[rid])

def validate_context(context):
    require(type(context) is dict and set(context)==set(SCOPE)|{'now','synthetic','physical_execution_enabled'}, 'context fields')
    require(context['synthetic'] is True and context['physical_execution_enabled'] is False, 'synthetic scope only')
    for key in SCOPE:
        text(context[key])
    number(context['now'], True)
    branch=context['branch_id']
    require(branch in EXPERIMENTS or branch in NUMERICAL, 'unknown branch')
    if branch in EXPERIMENTS:
        require(context['design_id']==EXPERIMENTS[branch], 'branch/design mismatch')
    else:
        require(context['design_id']=='SOURCE_REVIEW_ONLY', 'numerical review cannot bind physical design')

def validate_receipt(record, context, registry):
    require(type(record) is dict and set(record)=={'id','kind','issuer','synthetic','scope','observed_at','valid_until','status','payload'}, 'receipt fields')
    text(record['id']); text(record['issuer']); kind=record['kind']
    require(kind in ROLES, 'unrecognized receipt kind')
    require(record['synthetic'] is True, 'real evidence authentication not implemented')
    require(type(registry) is dict and record['issuer'] in registry, 'unregistered synthetic issuer')
    require(registry[record['issuer']]==ROLES[kind], 'wrong independent issuer role')
    require(record['status']=='observed', 'request/acknowledgement is not observed evidence')
    scope=record['scope']
    require(type(scope) is dict and set(scope)==set(SCOPE), 'exact receipt scope')
    require(all(scope[k]==context[k] for k in SCOPE), 'identity or epoch mismatch')
    observed=number(record['observed_at'], True); end=number(record['valid_until'], True)
    require(observed<=context['now']<=end, 'future, expired or reversed receipt validity')
    require(type(record['payload']) is dict, 'receipt payload')

def validate_plan(plan, branch):
    require(type(plan) is dict and set(plan)=={'approved','synthetic','plan_id','branch_id','repeat_count','repeat_unit','conditions','exclusion_policy','scientific_thresholds','prospective','repeat_bindings'}, 'plan fields')
    require(plan['approved'] is True and plan['synthetic'] is True and plan['prospective'] is True, 'prospective synthetic plan approval required')
    text(plan['plan_id']);require(plan['branch_id']==branch,'plan branch mismatch')
    require(type(plan['repeat_count']) is int and plan['repeat_count']>0,'approved independent repeat count required')
    require(plan['repeat_unit'] in ('specimen','mount','trial'), 'frames/cells/points are not independent repeats')
    require(type(plan['conditions']) is list and bool(plan['conditions']) and all(type(x) is str and x.strip() for x in plan['conditions']) and len(set(plan['conditions']))==len(plan['conditions']), 'unique condition inventory')
    text(plan['exclusion_policy'])
    require(plan['scientific_thresholds'] is None,'source-derived scientific pass constants prohibited')
    bindings=plan['repeat_bindings'];require(type(bindings) is list and len(bindings)==plan['repeat_count'],'prospective repeat binding inventory')
    require(all(type(b) is dict and set(b)=={'repeat_unit_id','specimen_id','mount_epoch','trial_id','calibration_epoch','orientation'} for b in bindings),'repeat binding fields')
    for b in bindings:
        for value in b.values():text(value)
    require(len({b['repeat_unit_id'] for b in bindings})==len(bindings),'unique planned repeat identities')

def validate_raw(payload, context):
    for key in RAW_FIELDS:
        require(type(payload.get(key)) is list and bool(payload[key]) and len(set(payload[key]))==len(payload[key]) and all(type(x) is str and x.strip() for x in payload[key]), 'raw identity/hash/clock inventory')
    require(len(payload['raw_ids'])==len(payload['raw_hashes']), 'raw hashes require one-to-one parents')
    require(all(len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in payload['raw_hashes']), 'raw SHA-256 format')
    require(payload.get('retained_unmodified') is True,'raw data must be retained')
    streams=payload.get('streams')
    require(type(streams) is list and len(streams)==len(payload['raw_ids']), 'typed raw streams required')
    require([s.get('id') for s in streams]==payload['raw_ids'] and [s.get('sha256') for s in streams]==payload['raw_hashes'], 'raw stream identity/hash join')
    for stream in streams:
        require(type(stream) is dict and set(stream)=={'id','sha256','kind','clock_id','observed_interval','specimen_id','mount_epoch','trial_id','calibration_epoch','orientation'}, 'raw stream fields')
        require(stream['kind'] in ('camera_pixels','source_pose','source_events'), 'typed raw stream kind')
        for field in ('specimen_id','mount_epoch','trial_id','calibration_epoch','orientation'):text(stream[field])
        require(stream['specimen_id']==context['specimen_id'],'raw specimen identity mismatch')
        require(stream['clock_id'] in payload['device_clock_ids'], 'raw stream clock join')
        interval=stream['observed_interval'];require(type(interval) is list and len(interval)==2,'observed interval required')
        require(0<=number(interval[0])<=number(interval[1])<=context['now'],'raw stream observed time interval')
    require(set(payload['device_clock_ids'])=={s['clock_id'] for s in streams}, 'no unused or missing raw clocks')

def validate_calibration(payload, context):
    require(payload.get('current') is True and payload.get('qualified_scope')=='displacement_and_optional_force', 'current scoped calibration required')
    require(payload.get('sign_tested') is True and payload.get('optical_transform') is True and payload.get('torsion_geometry') is True,'missing optical/sign/torsion qualification')
    require(payload.get('uncertainty') is True and payload.get('effective_lever_inferred_from_rod') is False,'uncertainty and independently established lever required')
    require(payload.get('invalidations')==[], 'calibration invalidated')
    epochs=payload.get('qualified_epochs');require(type(epochs) is list and bool(epochs),'explicit calibration epoch inventory required')
    require(all(type(e) is dict and set(e)=={'calibration_epoch','specimen_id','mount_epoch','configuration_epoch','array_revision','sign_tested','uncertainty','qualified_interval','evidence_ref'} for e in epochs),'calibration epoch fields')
    require(len({e['calibration_epoch'] for e in epochs})==len(epochs),'unique calibration epochs required')
    for epoch in epochs:
        for key in ('calibration_epoch','specimen_id','mount_epoch','configuration_epoch','array_revision'):text(epoch[key])
        require(epoch['specimen_id']==context['specimen_id'] and epoch['configuration_epoch']==context['configuration_epoch'] and epoch['array_revision']==context['array_revision'],'calibration epoch scope mismatch')
        require(epoch['sign_tested'] is True and epoch['uncertainty'] is True,'qualified epoch evidence required')
        text(epoch['evidence_ref'])
        interval=epoch['qualified_interval'];require(type(interval) is list and len(interval)==2 and 0<=number(interval[0])<=number(interval[1]),'qualified calibration interval')
    require(any(e['calibration_epoch']==context['calibration_epoch'] and e['mount_epoch']==context['mount_epoch'] and e['qualified_interval'][0]<=context['now']<=e['qualified_interval'][1] for e in epochs),'current calibration endpoint missing or outside qualified interval')

def validate_clock(payload):
    require(payload.get('clock_ids')==['camera_clock','source_clock'] and payload.get('synchronization_evidence') and payload.get('continuous_epoch') is True,'cross-device clock evidence required')
    residual=number(payload.get('residual_error'),True); tolerance=number(payload.get('approved_tolerance'),True)
    require(residual<=tolerance,'clock residual exceeds scoped tolerance')

def validate_custody(payload, context, returning=False):
    require(payload.get('specimen_id')==context['specimen_id'] and payload.get('carrier_id')==context['carrier_id'],'custody identity mismatch')
    for field in ('from_holder','to_holder','event_id','condition_record','support_receipt','slot'):
        text(payload.get(field))
    require(payload['from_holder']!=payload['to_holder'],'custody requires distinct holders')
    require(payload.get('receiver_accepted') is True and payload.get('supported') is True and payload.get('occupancy_known') is True,'accepted supported custody required')
    require(payload.get('previous_holder')==payload['from_holder'],'broken custody chain')
    if returning:
        require(payload.get('final_state') in ('RETURNED_ACCEPTED','QUARANTINED_ACCEPTED'),'final custody state')
        require(payload.get('independent_access_release') is True,'current access release required')

def _check(action, evaluator):
    """Validate one symbolic action; returns no hardware command or side effect."""
    require(type(action) is dict and set(action)=={'operation_id','evidence_ids'},'actor accepts operation_id and evidence_ids only')
    operation=action['operation_id'];require(operation in OPERATIONS,'unknown operation')
    ids=action['evidence_ids'];require(type(ids) is list and all(type(x) is str and x.strip() for x in ids) and len(ids)==len(set(ids)),'unique evidence identifiers required')
    require(type(evaluator) is dict and set(evaluator)=={'context','plan','registry','records','completed_operations','attempts','admitted_specimens'},'evaluator fixture fields')
    context=evaluator['context'];validate_context(context);branch=context['branch_id']
    require(branch in NUMERICAL or evaluator['admitted_specimens']==[context['specimen_id']],'single scoped specimen episode requires admitted identity')
    require(type(evaluator['completed_operations']) is list and all(x in OPERATIONS for x in evaluator['completed_operations']) and len(set(evaluator['completed_operations']))==len(evaluator['completed_operations']),'completed operation ledger')
    require(set(DEPS[operation])<=set(evaluator['completed_operations']),'operation dependency not complete')
    require(branch not in NUMERICAL or operation in ('R01','R11'),'numerical branches are source review only')
    require(operation not in ('R07','R08','R09','R10') or branch in EXPERIMENTS,'numerical branches cannot enter experimental loop')
    require(operation!='R11' or branch in NUMERICAL,'numerical source review requires separately typed branch')
    attempts=evaluator['attempts'];require(type(attempts) is list,'attempt ledger')
    require(all(type(a) is dict and set(a)=={'attempt_id','specimen_id','status','raw_retained','failure_retained','scope'} for a in attempts),'attempt fields')
    require(len({a['attempt_id'] for a in attempts})==len(attempts),'duplicate admitted attempt')
    for attempt in attempts:
        text(attempt['attempt_id']);text(attempt['specimen_id'])
        require(type(attempt['scope']) is dict and set(attempt['scope'])==set(SCOPE),'attempt scope fields')
        require(attempt['scope']['attempt_id']==attempt['attempt_id'] and attempt['scope']['specimen_id']==attempt['specimen_id'],'attempt identity/scope join')
        require(attempt['specimen_id']==context['specimen_id'],'foreign specimen in single-specimen episode')
        require(attempt['status'] in TERMINAL+('PENDING','RUNNING','UNCERTAIN'),'attempt status')
    if operation in ('R08','R09','R10'):
        admitted=next((a for a in attempts if a['attempt_id']==context['attempt_id']),None)
        require(admitted and admitted['scope']=={k:context[k] for k in SCOPE},'current scoped attempt was not admitted')
    store=EvidenceStore(evaluator['records']);records=[store.get(i) for i in ids]
    for record in records:validate_receipt(record,context,evaluator['registry'])
    require(len({r['kind'] for r in records})==len(records),'duplicate evidence kind')
    require({r['kind'] for r in records}==set(KINDS[operation]),'exact operation receipt kinds required')
    payload={r['kind']:r['payload'] for r in records}
    reference_fields={'fabrication':('batch_id',),'coordinates':('mapping_id',),'clock':('synchronization_evidence',),'measurement':('uncertainty_record',),'analysis':('filter_policy','uncertainty_record'),'source_numerical':('source_locator',)}
    for kind, fields in reference_fields.items():
        if kind in payload:
            for field in fields:text(payload[kind].get(field))
    if operation in ('R02','R07','R08','R09'):
        validate_plan(evaluator['plan'],branch)
        require(evaluator['plan']['plan_id']==context['plan_id'],'context/plan mismatch')
        require(all(b['specimen_id']==context['specimen_id'] for b in evaluator['plan']['repeat_bindings']),'finite checker supports one specimen per episode')
        require(evaluator['plan']['repeat_unit']!='specimen' or evaluator['plan']['repeat_count']==1,'cross-specimen repeat aggregation is not implemented')
    if 'plan' in payload:
        require(payload['plan']==evaluator['plan'],'approved plan receipt does not match plan')
    if 'source_review' in payload:
        p=payload['source_review'];require(p.get('main_complete') is True and p.get('si_complete') is True and p.get('source_separate_from_design') is True and p.get('unknowns_preserved') is True,'source scope required')
    if 'fabrication' in payload:
        p=payload['fabrication'];require(p.get('design_id')==context['design_id'] and p.get('inert_released') is True and p.get('qa_accepted') is True and p.get('grooves_clear') is True and p.get('batch_id'),'qualified design-specific specimen required')
    if 'array' in payload:
        p=payload['array'];require(p.get('membership_revision')==context['array_revision'] and p.get('current_characterization') is True and p.get('drift_accepted') is True,'current array qualification required')
        require(type(p.get('member_ids')) is list and p['member_ids'] and all(type(x) is str and x.strip() for x in p['member_ids']) and len(set(p['member_ids']))==len(p['member_ids']),'unique selected members required')
        require(type(p.get('rejected_ids')) is list and all(type(x) is str and x.strip() for x in p['rejected_ids']) and len(set(p['rejected_ids']))==len(p['rejected_ids']) and not set(p['member_ids'])&set(p['rejected_ids']),'selected/rejected member mismatch')
    if 'custody' in payload:validate_custody(payload['custody'],context)
    if 'support' in payload:
        p=payload['support'];require(p.get('accepted') is True and p.get('supported') is True and p.get('exclusive_lease')==context['lease_id'] and p.get('lease_retained') is True,'supported exclusive lease required')
    if 'calibration' in payload:validate_calibration(payload['calibration'],context)
    if 'coordinates' in payload:
        p=payload['coordinates'];require(p.get('sign_tested') is True and p.get('source_unit')=='deg' and p.get('response_unit')=='m' and p.get('separate_transforms') is True and p.get('mapping_id'),'signed separate coordinate mapping required')
    if 'clock' in payload:validate_clock(payload['clock'])
    if 'capture_ready' in payload:
        p=payload['capture_ready'];require(p.get('actual_ready') is True and p.get('observed_service_status')=='READY' and p.get('duplicate_request') is False,'actual ready status and unique admission required')
    if operation=='R07':
        require(all(a['status'] in TERMINAL and a['raw_retained'] is True and a['failure_retained'] is True for a in evaluator['attempts']),'prior attempts require terminal retained evidence before new admission')
        require(not any(a.get('attempt_id')==context['attempt_id'] for a in evaluator['attempts']),'attempt already admitted; reconcile rather than retry')
    if 'measurement' in payload:
        p=payload['measurement'];validate_raw(p,context)
        require(set(p['device_clock_ids'])==set(payload['clock']['clock_ids']),'raw and selected calibration clock identities mismatch')
        camera_streams=[stream for stream in p['streams'] if stream['kind']=='camera_pixels']
        bindings=evaluator['plan']['repeat_bindings']
        fields=('specimen_id','mount_epoch','trial_id','calibration_epoch','orientation')
        require(len(camera_streams)==len(bindings),'complete planned camera-repeat inventory required')
        require([{k:x[k] for k in fields} for x in camera_streams]==[{k:x[k] for k in fields} for x in bindings],'measurement raw metadata must match approved repeat bindings')
        for stream in p['streams']:
            epoch=next((e for e in payload['calibration']['qualified_epochs'] if e['calibration_epoch']==stream['calibration_epoch']),None)
            require(epoch and epoch['specimen_id']==stream['specimen_id'] and epoch['mount_epoch']==stream['mount_epoch'],'raw stream must join qualified calibration/mount epoch')
            require(epoch['qualified_interval'][0]<=stream['observed_interval'][0]<=stream['observed_interval'][1]<=epoch['qualified_interval'][1],'raw observation outside calibration epoch interval')
            if stream['kind']!='camera_pixels':
                require(all(stream[k]==context[k] for k in ('specimen_id','mount_epoch','trial_id','calibration_epoch')),'current source stream identity mismatch')
        require(p.get('observed_source_state') is True and p.get('tracking_valid') is True and p.get('terminal_status') in TERMINAL and p.get('terminal_status')==admitted['status'],'observed measurement and admitted terminal state required')
        require(p.get('physical_quantity')=='specimen_displacement' and p.get('unit')=='m' and p.get('transform_chain')==['pixels_to_screen','screen_to_angle','angle_to_specimen'],'displacement lineage required; no uncalibrated force substitution')
        require(p.get('sign_tested') is True and p.get('clock_aligned') is True and p.get('calibration_current') is True and p.get('uncertainty_record'),'measurement qualification missing')
        if branch in ('B04','B05'):
            require(p.get('source_pose_kind')=='observed_readback' and any(x['id']==p.get('pose_raw_id') and x['kind']=='source_pose' for x in p['streams']),'actual source pose raw parent required')
        if branch=='B01':require(p.get('phases')==['pre_off','on','post_off'],'complete on/off phases required')
        if branch in ('B02','B05'):
            require(p.get('conditions')==evaluator['plan']['conditions'],'complete ordered planned condition inventory required')
    if 'source_observed' in payload:
        p=payload['source_observed'];require(p.get('observed') is True and p.get('evidence_type')=='measured_state' and p.get('command_only') is False,'source request not observed event')
        events=p.get('events');require(type(events) is list and bool(events),'observed timed events required')
        require(all(type(e) is dict and set(e)=={'event_id','state','observed_time','clock_id','raw_id'} for e in events),'source event fields')
        require(len({e['event_id'] for e in events})==len(events),'unique event ids')
        prior=-1
        for event in events:
            text(event['event_id']);require(event['state'] in ('OFF','ON'),'source event state')
            t=number(event['observed_time'],True);require(prior<=t<=context['now'],'ordered observed event times');prior=t
            stream=next((x for x in payload['measurement']['streams'] if x['id']==event['raw_id']),None)
            require(stream and stream['kind']=='source_events' and stream['clock_id']==event['clock_id'] and stream['observed_interval'][0]<=t<=stream['observed_interval'][1],'source event raw/time/clock join')
        if branch=='B01':require([e['state'] for e in events]==['OFF','ON','OFF'],'observed off/on/off phase events')
    if 'baseline' in payload:
        p=payload['baseline'];m=payload['measurement'];require(any(x['id']==p.get('raw_parent_id') and x['kind']=='camera_pixels' for x in m['streams']) and p.get('matched_epoch') is True and p.get('subtraction_keeps_parents') is True,'baseline camera parents and scope required')
    if 'analysis' in payload:
        p=payload['analysis'];m=payload['measurement'];require(p.get('raw_parent_ids')==m['raw_ids'] and p.get('raw_parent_hashes')==m['raw_hashes'],'analysis raw ancestry mismatch')
        require(p.get('failed_attempts_retained') is True and p.get('exclusions_recorded') is True and p.get('filter_policy') and p.get('uncertainty_record') and p.get('source_outcome_target') is None,'analysis cannot discard failures or target source result')
        require(p.get('repeat_unit')==evaluator['plan']['repeat_unit'] and type(p.get('independent_repeat_count')) is int and p['independent_repeat_count']==evaluator['plan']['repeat_count'],'independent repeat accounting mismatch')
        repeats=p.get('repeat_records');require(type(repeats) is list and len(repeats)==evaluator['plan']['repeat_count'],'explicit independent repeat records required')
        require(all(type(x) is dict and set(x)=={'repeat_unit_id','repeat_unit','raw_parent_id','status','specimen_id','mount_epoch','trial_id','calibration_epoch','orientation'} for x in repeats),'repeat record fields')
        require(len({x['repeat_unit_id'] for x in repeats})==len(repeats),'distinct independent repeat units required')
        require(len({x['raw_parent_id'] for x in repeats})==len(repeats),'repeat records cannot reuse camera data')
        independent_key={'specimen':'specimen_id','mount':'mount_epoch','trial':'trial_id'}[evaluator['plan']['repeat_unit']]
        require(len({x[independent_key] for x in repeats})==len(repeats),'declared repeat-unit identity not independent')
        for repeat in repeats:
            require(repeat['repeat_unit']==evaluator['plan']['repeat_unit'] and repeat['status'] in TERMINAL,'typed repeat result required')
            for key in ('repeat_unit_id','specimen_id','mount_epoch','trial_id'):text(repeat[key])
            stream=next((x for x in m['streams'] if x['id']==repeat['raw_parent_id'] and x['kind']=='camera_pixels'),None)
            require(stream,'repeat camera parent missing')
            for key in ('specimen_id','mount_epoch','trial_id','calibration_epoch','orientation'):
                require(repeat[key]==stream[key],'repeat raw metadata identity mismatch')
            planned=next((x for x in evaluator['plan']['repeat_bindings'] if x['repeat_unit_id']==repeat['repeat_unit_id']),None)
            require(planned and all(planned[k]==repeat[k] for k in planned),'repeat raw ancestry must match prospective binding')
        if branch=='B03':
            pair=p.get('orientation_pair');require(type(pair) is dict and pair.get('same_specimen_id')==context['specimen_id'] and pair.get('orientations')==['original','flipped'] and type(pair.get('mount_epochs')) is list and len(pair['mount_epochs'])==2 and len(set(pair['mount_epochs']))==2 and type(pair.get('calibration_epochs')) is list and len(pair['calibration_epochs'])==2 and len(set(pair['calibration_epochs']))==2 and pair.get('signed_comparison_approved') is True,'distinct qualified orientation pair required')
            require(context['mount_epoch'] in pair['mount_epochs'] and context['calibration_epoch'] in pair['calibration_epochs'],'orientation comparison must include current endpoint')
            require(pair.get('raw_parent_ids')==[x['raw_parent_id'] for x in repeats],'orientation raw ancestry required')
            require(pair['orientations']==[x['orientation'] for x in repeats] and pair['mount_epochs']==[x['mount_epoch'] for x in repeats] and pair['calibration_epochs']==[x['calibration_epoch'] for x in repeats],'orientation pair must join qualified raw metadata')
    if 'attempt_terminal' in payload:
        p=payload['attempt_terminal'];require(p.get('attempt_id')==context['attempt_id'] and p.get('state') in TERMINAL and p.get('state')==admitted['status'] and p.get('observed') is True,'terminal attempt state required')
        require(p.get('reconfiguration_requested') is False or p.get('safe_hold_and_requalification_required') is True,'changes require safe hold and requalification')
    if 'source_numerical' in payload:
        p=payload['source_numerical'];require(p.get('branch_id')==branch and p.get('evidence_type')=='source_numerical_review' and p.get('solver_executed') is False and p.get('physical_experiment') is False and p.get('source_locator'),'source numerical review only')
    if operation in ('R12','R13','R14'):
        for a in attempts:
            require(a['status'] in TERMINAL and a['raw_retained'] is True and a['failure_retained'] is True,'every admitted attempt terminal and retained')
    for kind in SAFE:
        if kind in payload:
            p=payload[kind];require(p.get('observed_safe') is True and p.get('independent') is True and p.get('command_only') is False and p.get('scope')=='actual_configuration' and p.get('safe_access_qualified') is True,'independent observed safe-state release required')
    if 'custody_return' in payload:
        validate_custody(payload['custody_return'],context,True)
        require(payload['custody_return']['from_holder']==payload['custody']['to_holder'],'return must start from current accepted holder')
    if 'archive' in payload:
        p=payload['archive'];ids=[a['attempt_id'] for a in evaluator['attempts']]
        require(p.get('attempt_ids')==ids and p.get('all_raw_retained') is True and p.get('failed_records_retained') is True and p.get('unknown_science_preserved') is True,'complete immutable archive required')
        admitted=evaluator['admitted_specimens'];require(type(admitted) is list and len(set(admitted))==len(admitted) and all(type(x) is str and x.strip() for x in admitted),'admitted specimen inventory')
        finals=p.get('final_custody');require(type(finals) is dict and set(finals)==set(admitted),'all admitted specimens require final custody')
        for specimen, final in finals.items():
            require(type(final) is dict and final.get('state') in ('RETURNED_ACCEPTED','QUARANTINED_ACCEPTED') and final.get('receiver_accepted') is True and final.get('occupancy_known') is True and final.get('condition_record') and final.get('holder'),'accepted final custody required')
        require(all(a['specimen_id'] in admitted for a in evaluator['attempts']),'attempt specimen absent from custody inventory')
        final=finals[context['specimen_id']];returned=payload['custody_return']
        require(final['state']==returned['final_state'] and final['holder']==returned['to_holder'] and final['condition_record']==returned['condition_record'],'archive final custody must match accepted return receipt')
    return {'status':'SYNTHETIC_ACCEPT','operation_id':operation,'physical_execution_enabled':False,'real_world_state':'HOLD_QUALIFICATION','scientific_reproduction':False}

def check(action, evaluator):
    try:
        return _check(action, evaluator)
    except ContractError:
        raise
    except (TypeError, KeyError, IndexError, AttributeError) as error:
        raise ContractError('malformed synthetic input: '+str(error)) from error

def action_for(operation, evaluator):
    return {'operation_id':operation,'evidence_ids':[r['id'] for r in evaluator['records'] if r['kind'] in KINDS[operation]]}

def fixture(branch='B01', operation='R07'):
    """Invented finite positive test data; not source data, thresholds or approvals."""
    require(branch in EXPERIMENTS or branch in NUMERICAL,'known fixture branch')
    c={k:k+'_synthetic_1' for k in SCOPE}
    c.update({'design_id':EXPERIMENTS.get(branch,'SOURCE_REVIEW_ONLY'),'branch_id':branch,'now':100,'synthetic':True,'physical_execution_enabled':False})
    plan={'approved':True,'synthetic':True,'plan_id':c['plan_id'],'branch_id':branch,'repeat_count':2,'repeat_unit':'trial','conditions':['condition_alpha','condition_beta'],'exclusion_policy':'retain_all_with_reason','scientific_thresholds':None,'prospective':True,'repeat_bindings':[{'repeat_unit_id':'synthetic_repeat_'+str(i),'specimen_id':c['specimen_id'],'mount_epoch':('mount_before' if branch=='B03' and i==0 else c['mount_epoch']),'trial_id':'synthetic_trial_'+str(i),'calibration_epoch':('cal_before' if branch=='B03' and i==0 else c['calibration_epoch']),'orientation':('flipped' if branch=='B03' and i==1 else 'original')} for i in range(2)]}
    custody={'specimen_id':c['specimen_id'],'carrier_id':c['carrier_id'],'from_holder':'carrier_service','to_holder':'metrology_service','previous_holder':'carrier_service','event_id':'handoff_synthetic_1','condition_record':'condition_synthetic_1','support_receipt':'support_synthetic_1','slot':'protected_slot','receiver_accepted':True,'supported':True,'occupancy_known':True}
    raw={'raw_ids':['raw_camera_synthetic','raw_camera_repeat_synthetic','raw_source_synthetic','raw_events_synthetic'],'raw_hashes':['a'*64,'b'*64,'c'*64,'d'*64],'device_clock_ids':['camera_clock','source_clock'],'retained_unmodified':True,'observed_source_state':True,'tracking_valid':True,'terminal_status':'SUCCEEDED','physical_quantity':'specimen_displacement','unit':'m','transform_chain':['pixels_to_screen','screen_to_angle','angle_to_specimen'],'sign_tested':True,'clock_aligned':True,'calibration_current':True,'uncertainty_record':'synthetic_uncertainty','source_pose_kind':'observed_readback','pose_raw_id':'raw_source_synthetic','phases':['pre_off','on','post_off'],'conditions':deepcopy(plan['conditions'])}
    raw['streams']=[{'id':rid,'sha256':digest,'kind':kind,'clock_id':clock,'observed_interval':[90,95],'specimen_id':c['specimen_id'],'mount_epoch':c['mount_epoch'],'trial_id':c['trial_id'],'calibration_epoch':c['calibration_epoch'],'orientation':'original'} for rid,digest,kind,clock in zip(raw['raw_ids'],raw['raw_hashes'],['camera_pixels','camera_pixels','source_pose','source_events'],['camera_clock','camera_clock','source_clock','source_clock'])]
    for i,binding in enumerate(plan['repeat_bindings']):raw['streams'][i].update({k:v for k,v in binding.items() if k!='repeat_unit_id'})
    p={'source_review':{'main_complete':True,'si_complete':True,'source_separate_from_design':True,'unknowns_preserved':True},'plan':deepcopy(plan),'fabrication':{'design_id':c['design_id'],'inert_released':True,'qa_accepted':True,'grooves_clear':True,'batch_id':'synthetic_batch'},'array':{'membership_revision':c['array_revision'],'current_characterization':True,'drift_accepted':True,'member_ids':['synthetic_member_a','synthetic_member_b'],'rejected_ids':['synthetic_rejected_c']},'custody':custody,'support':{'accepted':True,'supported':True,'exclusive_lease':c['lease_id'],'lease_retained':True},'calibration':{'current':True,'qualified_scope':'displacement_and_optional_force','sign_tested':True,'optical_transform':True,'torsion_geometry':True,'uncertainty':True,'effective_lever_inferred_from_rod':False,'invalidations':[]},'coordinates':{'sign_tested':True,'source_unit':'deg','response_unit':'m','separate_transforms':True,'mapping_id':'synthetic_sign_mapping'},'clock':{'clock_ids':['camera_clock','source_clock'],'synchronization_evidence':'synthetic_sync','continuous_epoch':True,'residual_error':0.01,'approved_tolerance':0.02},'capture_ready':{'actual_ready':True,'observed_service_status':'READY','duplicate_request':False},'measurement':raw,'source_observed':{'observed':True,'evidence_type':'measured_state','command_only':False,'events':[{'event_id':'synthetic_event_'+str(i),'state':state,'observed_time':91+i,'clock_id':'source_clock','raw_id':'raw_events_synthetic'} for i,state in enumerate(['OFF','ON','OFF'])]},'baseline':{'raw_parent_id':'raw_camera_synthetic','matched_epoch':True,'subtraction_keeps_parents':True},'analysis':{'raw_parent_ids':raw['raw_ids'],'raw_parent_hashes':raw['raw_hashes'],'failed_attempts_retained':True,'exclusions_recorded':True,'filter_policy':'unfiltered_synthetic','uncertainty_record':'synthetic_uncertainty','source_outcome_target':None,'repeat_unit':'trial','independent_repeat_count':2,'orientation_pair':{'same_specimen_id':c['specimen_id'],'orientations':['original','flipped'],'mount_epochs':[x['mount_epoch'] for x in plan['repeat_bindings']],'calibration_epochs':[x['calibration_epoch'] for x in plan['repeat_bindings']],'raw_parent_ids':raw['raw_ids'][:2],'signed_comparison_approved':True}},'attempt_terminal':{'attempt_id':c['attempt_id'],'state':'SUCCEEDED','observed':True,'reconfiguration_requested':False,'safe_hold_and_requalification_required':True},'source_numerical':{'branch_id':branch,'evidence_type':'source_numerical_review','solver_executed':False,'physical_experiment':False,'source_locator':'synthetic citation placeholder'},'custody_return':dict(custody,from_holder='metrology_service',to_holder='return_service',previous_holder='metrology_service',final_state='RETURNED_ACCEPTED',independent_access_release=True),'archive':{'attempt_ids':['prior_attempt_synthetic'],'all_raw_retained':True,'failed_records_retained':True,'unknown_science_preserved':True,'final_custody':{c['specimen_id']:{'state':'RETURNED_ACCEPTED','receiver_accepted':True,'occupancy_known':True,'condition_record':'condition_synthetic_1','holder':'return_service'}}}}
    epoch_pairs={(x['calibration_epoch'],x['mount_epoch']) for x in raw['streams']}
    p['calibration']['qualified_epochs']=[{'calibration_epoch':cal,'specimen_id':c['specimen_id'],'mount_epoch':mount,'configuration_epoch':c['configuration_epoch'],'array_revision':c['array_revision'],'sign_tested':True,'uncertainty':True,'qualified_interval':[80,110],'evidence_ref':'synthetic_calibration_'+cal} for cal,mount in sorted(epoch_pairs)]
    p['analysis']['repeat_records']=[dict(plan['repeat_bindings'][i],repeat_unit='trial',raw_parent_id=rid,status='SUCCEEDED') for i,rid in enumerate(raw['raw_ids'][:2])]
    for kind in SAFE:p[kind]={'observed_safe':True,'independent':True,'command_only':False,'scope':'actual_configuration','safe_access_qualified':True}
    registry={role+'_synthetic_authority':role for role in set(ROLES.values())}
    records=[{'id':kind+'_receipt','kind':kind,'issuer':ROLES[kind]+'_synthetic_authority','synthetic':True,'scope':{k:c[k] for k in SCOPE},'observed_at':90,'valid_until':110,'status':'observed','payload':deepcopy(value)} for kind,value in p.items()]
    attempts=[{'attempt_id':'prior_attempt_synthetic','specimen_id':c['specimen_id'],'status':'FAILED','raw_retained':True,'failure_retained':True,'scope':dict({k:c[k] for k in SCOPE},attempt_id='prior_attempt_synthetic')}]
    if operation in ('R08','R09','R10','R12','R13','R14'):
        attempts.append({'attempt_id':c['attempt_id'],'specimen_id':c['specimen_id'],'status':'SUCCEEDED','raw_retained':True,'failure_retained':True,'scope':{k:c[k] for k in SCOPE}})
        next(r for r in records if r['kind']=='archive')['payload']['attempt_ids']=[a['attempt_id'] for a in attempts]
    return {'context':c,'plan':plan,'registry':registry,'records':records,'completed_operations':list(OPERATIONS),'attempts':attempts,'admitted_specimens':[c['specimen_id']]}
