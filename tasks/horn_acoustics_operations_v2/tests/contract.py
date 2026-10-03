"""Static and synthetic-record checks; never hardware authentication or acoustics."""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
POINTS = {(x, y) for x in range(1, 11) for y in range(1, 20)}
SHARED = ['rig_revision', 'source_config', 'frequency_hz', 'reference_microphone',
          'scan_microphone', 'reference_pose_revision', 'calibration_ids',
          'channel_map', 'grid_revision', 'DAQ_card', 'normalization_card', 'phase_card']
EPOCHS = ['rig_revision', 'source_config', 'reference_pose_revision', 'grid_revision', 'DAQ_card', 'phase_card']

def require(value, message):
    if not value:
        raise ValueError(message)

def load(name):
    return json.loads((ROOT / name).read_text())

def nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def complex_value(value):
    return isinstance(value, list) and len(value) == 2 and all(finite(v) for v in value)

def receipt(value):
    return (isinstance(value, dict) and nonempty(value.get('id')) and
            value.get('status') == 'accepted' and nonempty(value.get('revision')))

def validate_cards(cards):
    expected = {r['id'] for r in load('unknown_parameters.json')['unknowns']}
    require(set(cards) == expected, 'Missing or unexpected qualification cards')
    for key, card in cards.items():
        require(isinstance(card, dict) and card.get('id') == key, 'Card identity mismatch')
        require(nonempty(card.get('revision')), 'Missing card revision')
        require(nonempty(card.get('qualification_receipt')), 'Missing qualification receipt')
        require(isinstance(card.get('parameter_payload'), dict) and card['parameter_payload'],
                'Bare qualification flag or empty payload is not sufficient')
        require(nonempty(card.get('valid_scope')), 'Missing qualification scope')
    return True

def validate_panel(panel):
    require(nonempty(panel.get('id')) and nonempty(panel.get('revision')), 'Missing panel identity')
    require(panel.get('design') == 'focusing', 'Physical panel must be focusing design')
    require(receipt(panel.get('inspection')), 'Missing accepted panel inspection')
    require(panel['inspection']['revision'] == panel['revision'], 'Stale panel inspection')
    entries = panel.get('positions', [])
    require(len(entries) == 30 and {p.get('position') for p in entries} == set(range(1, 31)),
            'Panel must cover all thirty positions exactly once')
    parts = panel.get('parts', {})
    require(isinstance(parts, dict) and bool(parts), 'Finite part manifest required')
    for entry in entries:
        p = entry['position']
        require(type(p) is int and type(entry.get('row')) is int, 'Position and row must be integers, not booleans')
        require(entry.get('row') == min(p, 31-p), 'Incorrect mirrored row')
        require(entry.get('part_id') in parts, 'Unbound physical part')
    require(set(parts) == {e['part_id'] for e in entries}, 'Unallocated manifest part')
    for part_id, part in parts.items():
        require(all(nonempty(part.get(k)) for k in ['job_id','stock_lot','CAD_revision','revision']),
                'Missing fabrication lineage')
        require(receipt(part.get('inspection')) and part['inspection']['revision'] == part['revision'],
                'Missing or stale part inspection')
        require(part.get('quarantined') is False, 'Quarantined component cannot be installed')
    return True

def validate_condition(condition, panel, ids=None):
    ids = ids if ids is not None else set()
    require(condition.get('data_class') == 'synthetic_bookkeeping', 'Only explicitly synthetic test records are accepted by this checker')
    require(condition.get('name') in ('without','with'), 'Invalid physical condition')
    for key in ['id','pair_id'] + [k for k in SHARED if k not in ('frequency_hz','calibration_ids','channel_map')]:
        require(nonempty(condition.get(key)), 'Missing condition field: ' + key)
    require(condition['frequency_hz'] == 1000, 'Frequency differs from declared source design')
    require(condition['reference_microphone'] != condition['scan_microphone'], 'Microphone identities must be distinct')
    require(condition.get('source_off_before_configuration') is True, 'Reconfiguration requires source isolation')
    require(condition.get('source_off_after_mapping') is True, 'Mapping closure requires source isolation')
    require(condition.get('reference_stable') is True, 'Reference drift invalidates condition')
    require(receipt(condition.get('configuration_receipt')), 'Missing configuration inspection')
    require(receipt(condition.get('archive_receipt')), 'Missing archive receipt')
    require(condition.get('normalization_uses_paper_data') is False, 'Literature values cannot be observations')
    if condition['name'] == 'with':
        require(condition.get('panel_id') == panel['id'] and condition.get('panel_revision') == panel['revision'],
                'Installed panel does not match accepted revision')
    else:
        require(condition.get('panel_id') is None and condition.get('panel_revision') is None,
                'Without-panel condition contains a panel')
    require(condition.get('channel_map') == {'reference': condition['reference_microphone'], 'scan': condition['scan_microphone']},
            'Channel roles changed or are incomplete')
    calibrations = condition.get('calibrations', {})
    require(set(calibrations) == {condition['reference_microphone'],condition['scan_microphone']}, 'Both calibrations required')
    require(condition.get('calibration_ids') == {k:v.get('id') for k,v in calibrations.items()}, 'Calibration identity mismatch')
    for mic, cal in calibrations.items():
        require(receipt(cal) and finite(cal.get('valid_from')) and finite(cal.get('valid_until')),
                'Invalid calibration receipt')
        require(cal['valid_from'] < cal['valid_until'], 'Empty calibration validity interval')
    points = condition.get('points', [])
    require(len(points) == 190 and {(p.get('x'),p.get('y')) for p in points} == POINTS,
            'Exactly 190 unique registered points are required')
    for point in points:
        require(type(point.get('x')) is int and type(point.get('y')) is int, 'Grid indices must be integers, not booleans')
        require(receipt(point.get('pose_receipt')), 'Unverified probe position')
        require(point.get('grid_revision') == condition['grid_revision'], 'Stale grid placement')
        require(point.get('position_accepted') is True and point.get('settled') is True,
                'Probe outside tolerance or not settled')
        attempts = point.get('attempts', [])
        require(isinstance(attempts,list) and attempts, 'Missing raw attempts')
        known = {}
        for attempt in attempts:
            rid = attempt.get('id')
            require(nonempty(rid) and rid not in ids, 'Repeated raw record identity')
            ids.add(rid)
            require(attempt.get('slot') in range(1,11) and type(attempt.get('slot')) is int, 'Invalid readout slot')
            require(attempt.get('condition_id') == condition['id'] and attempt.get('point') == [point['x'],point['y']],
                    'Cross-point or cross-condition raw record')
            require(attempt.get('data_class') == 'synthetic_bookkeeping', 'Published or generated scientific data cannot fill a readout')
            require(attempt.get('epochs') == {k:condition[k] for k in EPOCHS}, 'Readout from stale instrument state')
            require(complex_value(attempt.get('complex')), 'Complex value must contain two finite signed numbers')
            timestamp = attempt.get('timestamp')
            require(finite(timestamp), 'Invalid acquisition time')
            require(all(c['valid_from'] <= timestamp <= c['valid_until'] for c in calibrations.values()),
                    'Readout outside calibration validity')
            require(attempt.get('valid') in (True,False) and type(attempt['valid']) is bool, 'Validity must be explicit')
            if not attempt['valid']:
                require(nonempty(attempt.get('failure_reason')), 'Failed attempt reason missing')
            previous = attempt.get('supersedes')
            if previous is not None:
                require(previous in known and not known[previous]['valid'] and known[previous]['slot'] == attempt['slot'],
                        'Retry must explicitly supersede prior invalid attempt in same slot')
            for prior in known.values():
                if prior['slot'] == attempt['slot']:
                    require(previous == prior['id'] or prior['id'] in ancestors(known, previous),
                            'Duplicate slot without complete retry chain')
            known[rid] = attempt
        selected = point.get('selected_readouts', [])
        require(len(selected) == 10 and len(set(selected)) == 10 and all(s in known for s in selected),
                'Ten distinct acquired readouts must be selected')
        records = [known[s] for s in selected]
        require({r['slot'] for r in records} == set(range(1,11)) and all(r['valid'] for r in records),
                'Missing valid readout slots')
        require(point.get('average_inputs') == selected, 'Average ancestry differs from selected records')
        require(complex_value(point.get('average')), 'Missing complex average')
        mean = [sum(r['complex'][axis] for r in records)/10 for axis in (0,1)]
        require(all(abs(a-b) < 1e-12 for a,b in zip(mean,point['average'])), 'Average not derived from retained readouts')
    return True

def ancestors(known, previous):
    result = set()
    while previous in known and previous not in result:
        result.add(previous)
        previous = known[previous].get('supersedes')
    return result

def validate_campaign(campaign):
    require(campaign.get('data_class') == 'synthetic_bookkeeping', 'Synthetic label is mandatory')
    validate_cards(campaign.get('cards', {}))
    validate_panel(campaign.get('panel', {}))
    conditions = campaign.get('conditions', [])
    require(len(conditions) == 2 and {c.get('name') for c in conditions} == {'with','without'}, 'Both distinct conditions required')
    require(len({c.get('id') for c in conditions}) == 2, 'Condition IDs must differ')
    require(len({c.get('pair_id') for c in conditions}) == 1, 'Conditions belong to different pairs')
    ids = set()
    for c in conditions:
        validate_condition(c,campaign['panel'],ids)
    require(all(conditions[0][k] == conditions[1][k] for k in SHARED), 'Matched-state control mismatch')
    expected = {o['id'] for o in load('operations.json')['operations']}
    observed = campaign.get('operation_receipts', {})
    require(set(observed) == expected and all(receipt(v) for v in observed.values()), 'Missing fabrication, setup, custody, analysis or cleanup closure')
    require(campaign.get('cleanup_complete') is True, 'Cleanup incomplete')
    require(campaign.get('independent_replicates') is None, 'Independent replication cannot be fabricated')
    require(campaign.get('source_Table2_used_as_acquisition') is False, 'Source table cannot fill acquisition')
    validate_occurrences(campaign)
    return True

def validate_export():
    manifest = load('EXPORT_ALLOWLIST.json')
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    require(not any(p.is_symlink() for p in ROOT.rglob('*')), 'Symlinks are forbidden')
    require(set(manifest['allowlist']) == actual, 'Export has missing or unexpected files')
    require(len(manifest['allowlist']) == len(set(manifest['allowlist'])), 'Duplicate manifest entry')
    require(manifest['total_file_count_including_manifest'] == len(actual), 'Incorrect total file count')
    payload = {r['path']:r for r in manifest['files']}
    require(set(payload) == actual - {'EXPORT_ALLOWLIST.json'}, 'Incomplete manifest payload')
    require(manifest['payload_file_count'] == len(payload), 'Incorrect payload count')
    for name, entry in payload.items():
        p = ROOT / name
        require(p.suffix in {'.json','.md','.py'}, 'Forbidden source or binary file')
        raw = p.read_bytes()
        require(len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256'], 'Changed payload: '+name)
        require(('/'+'workspace'+'/') not in raw.decode() and ('/'+'tmp'+'/') not in raw.decode(), 'Host-specific path in public payload')
    return True

# This graph concerns scoped bookkeeping evidence, never physical authenticity.
def occurrence_graph(campaign):
    graph = {}
    def add(op, scope='shared', entity='campaign', after=()):
        key = (op, scope, entity)
        graph[key] = set(after)
        return key
    plan=add('PLAN');stock=add('STOCK',after=[plan]);carrier=add('CARRIER',after=[plan])
    add('MOVE',scope='route',entity='stock_to_print',after=[stock,carrier])
    parts=campaign['panel']['parts']; jobs={p['job_id'] for p in parts.values()}
    job_done={}
    for job in sorted(jobs):
        prev=add('PRINT_LOAD','job',job,after=[stock,carrier,('MOVE','route','stock_to_print')])
        for op in ['PRINT_START','PRINT_PROCESS','PRINT_UNLOAD']:prev=add(op,'job',job,[prev])
        job_done[job]=prev
    parts_done=[]
    for pid,part in sorted(parts.items()):
        prev=job_done[part['job_id']]
        prev=add('MOVE','part_route',pid+':print_to_finish',[prev])
        prev=add('POSTPROCESS','part',pid,[prev])
        prev=add('MOVE','part_route',pid+':finish_to_inspect',[prev])
        prev=add('METROLOGY','part',pid,[prev])
        prev=add('MOVE','part_route',pid+':inspect_to_assembly',[prev])
        parts_done.append(prev)
    panel=add('PANEL_ASSEMBLE',after=parts_done)
    panel=add('MOVE','panel_route','assembly_to_inspect',[panel])
    panel=add('PANEL_INSPECT',after=[panel])
    panel=add('MOVE','panel_route','inspect_to_rig',[panel])
    prev=plan
    for op in ['BOARD_RETRIEVE','BASE_PLACE','SPACERS_PLACE','SOURCE_MOUNT','TOP_PLACE','DOMAIN_INSPECT']:
        prev=add(op,after=[prev])
    domain=prev
    microphones=add('MIC_RETRIEVE',after=[plan]); calibrated=[]
    for mic in sorted(campaign['conditions'][0]['calibrations']):
        prev=add('MOVE','mic_route',mic+':stock_to_cal',[microphones])
        for op in ['CAL_MOUNT','CAL_ACQUIRE','CAL_RELEASE']:prev=add(op,'microphone',mic,[prev])
        prev=add('MOVE','mic_route',mic+':cal_to_rig',[prev]);calibrated.append(prev)
    ref=add('REF_MOUNT',after=calibrated+[domain]);probe=add('PROBE_MOUNT',after=calibrated+[domain])
    grid=add('GRID_REGISTER',after=[probe,domain]);daq=add('DAQ_CONNECT',after=[ref,probe,grid])
    source=add('SOURCE_SET',after=[daq])
    previous=None
    for c in campaign['conditions']:
        cid=c['id']; prerequisites=[source,grid]+([previous] if previous else [])
        isolated=add('CONDITION_ISOLATE','condition',cid,prerequisites)
        presence=add('PANEL_INSTALL' if c['name']=='with' else 'PANEL_ABSENT','condition',cid,[isolated]+([panel] if c['name']=='with' else []))
        start=add('CONDITION_START','condition',cid,[presence,daq,grid]); point_done=[]; previous_reads=[]
        for p in c['points']:
            point_id=f"{cid}:X{p['x']}Y{p['y']}"
            positioned=add('PROBE_MOVE','point',point_id,[start]+previous_reads)
            reads=[]
            for a in p['attempts']:
                retry_dependency=[('POINT_READ','readout',a['supersedes'])] if a.get('supersedes') else []
                reads.append(add('POINT_READ','readout',a['id'],[positioned]+retry_dependency))
            previous_reads=reads
            point_done.append(add('POINT_AVERAGE','point',point_id,reads))
        closed=add('CONDITION_CLOSE','condition',cid,point_done)
        previous=add('DRIFT_CHECK','condition',cid,[closed])
    ends=[('DRIFT_CHECK','condition',c['id']) for c in campaign['conditions']]
    prev=add('PAIR_CHECK',after=ends)
    for op in ['NORMALIZE','INTERPOLATE','ARCHIVE','SHUTDOWN','PANEL_RETURN','MIC_RETURN','CLEAN']:
        prev=add(op,after=[prev])
    return graph

def validate_occurrences(campaign):
    graph=occurrence_graph(campaign)
    events=campaign.get('occurrences',[])
    require(len(events)==len(graph),'Incomplete scoped occurrence coverage')
    observed={}; event_ids=set(); sequences=set()
    for event in events:
        key=(event.get('operation_id'),event.get('scope'),event.get('entity_id'))
        require(key in graph and key not in observed,'Duplicate or unexpected scoped occurrence')
        require(receipt(event),'Missing occurrence receipt')
        require(event['id'] not in event_ids,'Reused occurrence event identity')
        require(type(event.get('sequence')) is int and event['sequence']>0 and event['sequence'] not in sequences,
                'Invalid or repeated event sequence')
        require(event.get('campaign_id')==campaign.get('id'),'Occurrence belongs to another campaign')
        event_ids.add(event['id']);sequences.add(event['sequence']);observed[key]=event
    require(set(observed)==set(graph),'Missing scoped operations')
    for key,prerequisites in graph.items():
        event=observed[key]
        expected={observed[p]['id'] for p in prerequisites}
        require(set(event.get('prerequisite_events',[]))==expected,'Wrong dependency evidence')
        require(all(observed[p]['sequence'] < event['sequence'] for p in prerequisites),'Dependency order violated')
    # Inspection, calibration and acquisition records bind to current scoped events.
    require(campaign['panel']['inspection']['id']==observed[('PANEL_INSPECT','shared','campaign')]['id'] and
            campaign['panel']['revision']==observed[('PANEL_INSPECT','shared','campaign')]['revision'],
            'Panel inspection is detached from current panel event')
    for pid,part in campaign['panel']['parts'].items():
        require(part['inspection']['id']==observed[('METROLOGY','part',pid)]['id'] and
                part['revision']==observed[('METROLOGY','part',pid)]['revision'],
                'Part inspection is detached from current metrology event')
    for c in campaign['conditions']:
        for mic,cal in c['calibrations'].items():
            event=observed[('CAL_RELEASE','microphone',mic)]
            require(cal['id']==event['id'] and cal['revision']==event['revision'],
                    'Calibration receipt is detached from current microphone event')
        presence='PANEL_INSTALL' if c['name']=='with' else 'PANEL_ABSENT'
        require(c['configuration_receipt']['id']==observed[(presence,'condition',c['id'])]['id'] and c['configuration_receipt']['revision']==observed[(presence,'condition',c['id'])]['revision'],
                'Configuration inspection detached from panel-state event')
        require(c['archive_receipt']['id']==observed[('CONDITION_CLOSE','condition',c['id'])]['id'] and c['archive_receipt']['revision']==observed[('CONDITION_CLOSE','condition',c['id'])]['revision'],
                'Archive receipt detached from condition closure')
        for p in c['points']:
            point_id=f"{c['id']}:X{p['x']}Y{p['y']}"
            require(p['pose_receipt']['id']==observed[('PROBE_MOVE','point',point_id)]['id'],
                    'Position receipt is detached from positioning event')
            for a in p['attempts']:
                require(a.get('acquisition_event_id')==observed[('POINT_READ','readout',a['id'])]['id'],
                        'Raw record detached from acquisition event')
    last=campaign['conditions'][-1]['name']
    cleanup=observed[('PANEL_RETURN','shared','campaign')]
    require(cleanup.get('panel_action')==('remove_installed' if last=='with' else 'verify_carrier'),
            'Cleanup is not bound to final panel location')
    return True
