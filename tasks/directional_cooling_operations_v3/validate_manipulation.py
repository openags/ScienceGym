"""Validate manipulation design links and supplied terminal configuration.

This checks authored contracts, not sensor observations or robot success.
"""
import math


def check(condition, message):
    if not condition:
        raise ValueError(message)


def validate_terminal_connection(connection, terminal_contract):
    """Reject polarity/compatibility shortcuts in a proposed connection card."""
    channels={v['channel']:v for v in terminal_contract['channels']}
    channel=connection.get('channel')
    check(type(channel) is int and channel in channels, 'unknown thermocouple channel')
    c=channels[channel]
    check((connection.get('positive_pin'),connection.get('negative_pin'))==(c['positive_pin'],c['negative_pin']), 'thermocouple polarity or pin assignment mismatch')
    gauge=connection.get('terminal_wire_AWG')
    lo,hi=terminal_contract['wire_gauge_AWG_range']
    check(type(gauge) is int and lo<=gauge<=hi, 'wire outside declared terminal gauge range')
    if connection.get('probe_wire_AWG')!=gauge:
        check(bool(connection.get('transition_id')) and bool(connection.get('transition_qualification_id')), 'fine-wire transition not qualified')
    check(bool(connection.get('calibrated_connection_path_id')), 'complete connection path has no calibration binding')
    return True


def validate_contract(ops, interface_doc, binding_doc, terminal_doc, sensor_doc, parts, coverage):
    interfaces=interface_doc['interfaces'];byid={v['id']:v for v in interfaces}
    check(len(byid)==len(interfaces), 'duplicate interaction interface')
    partbyid={v['id']:v for v in parts}
    bindings=binding_doc['bindings'];byop={v['operation_id']:v for v in bindings}
    check(len(byop)==len(bindings) and set(byop)=={o['id'] for o in ops}, 'incomplete or duplicate operation bindings')
    for i in interfaces:
        check(i['remaining'] and not i['execution_qualified'], 'unearned interaction qualification')
        for variant in i['asset_variants']:
            check(variant['root_id']!='COOLER_EXPLODED','display-only exploded root used for manipulation')
            for pid in variant['part_ids']:
                check(pid in partbyid, 'missing exact part '+pid)
                check(partbyid[pid]['root']==variant['root_id'], 'cross-root part binding')
    manual=0
    for o in ops:
        ids=set()
        for s in o['reference_steps']:
            if s['capability']=='manipulation':
                manual+=1
                d=s.get('interaction',{})
                check(d.get('interface_id') in byid, 'manual step has no declared interface')
                ids.add(d['interface_id'])
                for key in ('target_role','contact_region','tool_role','support_transition','preserve','recovery','pose_basis','completion_evidence'):
                    check(isinstance(d.get(key),str) and bool(d[key].strip()), 'missing interaction field '+key)
                check(d['completion_evidence']==s['completion_observation'], 'stale manipulation completion predicate')
            else:
                check('interaction' not in s, 'nonmanual context credited as manipulation')
        check(ids==set(o['manipulation_interface_ids'])==set(byop[o['id']]['interface_ids']), 'stale operation/interface mapping')
        expected={p for i in ids for v in byid[i]['asset_variants'] for p in v['part_ids']}
        check(set(byop[o['id']]['part_selection'])==expected, 'stale or ambiguous geometry selection')
        check(set(byop[o['id']]['part_selection'])<=set(partbyid), 'part suffix cannot substitute for exact identity')
    terminals=terminal_doc['terminals'];pins={v['pin']:v for v in terminals}
    check(len(terminals)==52 and set(pins)==set(range(1,53)), 'incomplete physical terminal map')
    check(len(terminal_doc['channels'])==8 and {c['channel'] for c in terminal_doc['channels']}==set(range(8)), 'incomplete channel map')
    for n,t in pins.items():
        for key in ('part_id','wire_entry_part_id','screw_part_id'):
            check(t[key] in partbyid,'missing terminal geometry '+t[key])
        part=partbyid[t['part_id']]
        check(part['pin_number']==n and part['signal']==t['signal'], 'pin identity differs from geometry')
    for c in terminal_doc['channels']:
        check(pins[c['positive_pin']]['signal']=='C%dH'%c['channel'] and pins[c['negative_pin']]['signal']=='C%dL'%c['channel'], 'reversed channel polarity')
    check(terminal_doc['wire_gauge_AWG_range']==[16,30] and terminal_doc['probe_wire_AWG']==36, 'changed source wire-gauge constraint')
    sensors=sensor_doc['sensors']
    check(len(sensors)==7 and len({s['probe_role'] for s in sensors})==7, 'incomplete or duplicate map probe identities')
    check(len({tuple(s['position_in_asset_root_m']) for s in sensors})==7,'duplicated map locations')
    for s in sensors:
        check(s['target_part_id'] in partbyid and s['contact_part_id'] in partbyid, 'sensor target/contact missing')
        contact=partbyid[s['contact_part_id']]
        check(contact['contact_target']==s['target_part_id'],'sensor marker points to another component')
        q=s['position_in_asset_root_m']
        check(len(q)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in q),'invalid sensor position')
        check(all(abs(a-b)<1e-6 for a,b in zip(q,contact['local_position_m'])),'sensor position differs from scene')
    cmap={o['operation_id']:o for o in coverage['operations']}
    check(set(cmap)==set(byop) and len(cmap)==len(coverage['operations']), 'incomplete source-to-action coverage')
    for o in ops:
        check(cmap[o['id']]['source_evidence_ids']==o['evidence_ids'],'stale action source links')
        check(cmap[o['id']]['manipulation_step_ids']==[s['id'] for s in o['reference_steps'] if 'interaction' in s],'stale manual-step coverage')
    return dict(manipulation_steps=manual,interaction_interfaces=len(interfaces),
        interfaces_with_partial_geometry=sum(bool(i['asset_variants']) for i in interfaces),
        interfaces_without_geometry=sum(not i['asset_variants'] for i in interfaces))
