"""Original synthetic bookkeeping validators; no acoustic simulation or trusted logger."""
import math

BRANCH_TYPES = {'NO_OBJECT':'sweep','HALF_APERTURE':'sweep','SINGLE_EDGE_1D':'scan_1d','PLATE_32_1D':'scan_1d','ROD_10_1D':'scan_1d','DISC_2D':'scan_2d','ETH_2D':'scan_2d'}
BIND = ['guide_id','guide_version','target_id','target_version','rig_signature','channel_map_id','calibration_id','reference_id']

def finite(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def fail_missing(record, keys):
    return ['missing:'+key for key in keys if key not in record]

def validate_run(r):
    """Check synthetic record structure. This never authenticates physical events."""
    if not isinstance(r,dict):return ['invalid_run_type']
    e=fail_missing(r,['branch_id','acquisition_type','data_class','schedule','records','sensor_serials','physical_step_mm','repeat_count','calibration','source_enabled','configuration_valid','condition_verified','final_state']+BIND)
    if e:return e
    typ=BRANCH_TYPES.get(r['branch_id'])
    if typ is None or r['acquisition_type']!=typ:e.append('branch_type_mismatch')
    if r['data_class'] not in ('synthetic_mock','measured_episode'):e.append('not_acquisition_data')
    if not isinstance(r['repeat_count'],int) or isinstance(r['repeat_count'],bool) or r['repeat_count']<1:e.append('unresolved_repeat_count')
    elif r['repeat_count']!=1:e.append('repeat_expansion_not_implemented_in_single_run_validator')
    if not isinstance(r['sensor_serials'],list) or len(r['sensor_serials'])!=4 or not all(isinstance(v,str) and v for v in r['sensor_serials']):return e+['four_unique_sensors_required']
    if len(set(r['sensor_serials']))!=4:e.append('four_unique_sensors_required')
    if r['source_enabled'] is not True or r['configuration_valid'] is not True or r['condition_verified'] is not True:e.append('missing_acquisition_gate')
    if r['branch_id']=='NO_OBJECT':
        if r['target_id'] is not None or r['target_version'] is not None:e.append('baseline_contains_target')
    elif not r['target_id'] or not isinstance(r['target_version'],int):e.append('missing_target_lineage')
    if typ=='scan_1d' and r['physical_step_mm']!=0.6:e.append('wrong_1d_physical_grid')
    if typ=='scan_2d' and r['physical_step_mm']!=1.6:e.append('display_grid_used_for_acquisition')
    if typ=='sweep' and r['physical_step_mm'] is not None:e.append('sweep_recast_as_scan')
    if not isinstance(r['schedule'],list) or not r['schedule']:return e+['empty_or_unknown_schedule']
    expected={}
    for s in r['schedule']:
        if not isinstance(s,dict) or fail_missing(s,['point_id','coordinates_mm','frequency_hz']):e.append('incomplete_schedule_point');continue
        if not isinstance(s['point_id'],str) or not s['point_id']:e.append('invalid_point_id');continue
        if s['point_id'] in expected:e.append('duplicate_schedule_point')
        expected[s['point_id']]=s
        if not finite(s['frequency_hz']) or s['frequency_hz']<=0:e.append('invalid_frequency')
        if typ in ('scan_1d','scan_2d') and s['frequency_hz']!=7740:e.append('wrong_imaging_frequency')
        dim=1 if typ=='scan_1d' else 2 if typ=='scan_2d' else 0
        if not isinstance(s['coordinates_mm'],list) or len(s['coordinates_mm'])!=dim or not all(finite(v) for v in s['coordinates_mm']):e.append('invalid_coordinate_dimension')
    # A declared step must agree with all grid coordinate values, not only the label.
    if typ in ('scan_1d','scan_2d') and expected:
        dim=1 if typ=='scan_1d' else 2; step=0.6 if typ=='scan_1d' else 1.6
        coords=[s['coordinates_mm'] for s in expected.values()]
        if all(isinstance(c,list) and len(c)==dim and all(finite(v) for v in c) for c in coords):
            if len({tuple(c) for c in coords})!=len(coords):e.append('duplicate_physical_coordinate')
            for axis in range(dim):
                vals=sorted(set(c[axis] for c in coords)); origin=vals[0]
                if any(not math.isclose((v-origin)/step,round((v-origin)/step),abs_tol=1e-8) for v in vals):e.append('coordinates_not_on_physical_grid')
    cal=r['calibration']
    if not isinstance(cal,dict) or fail_missing(cal,['calibration_id','channel_map_id','sensor_serials','guide_version','valid','valid_from','valid_until']):e.append('incomplete_calibration');return e
    if cal['valid'] is not True:e.append('failed_calibration')
    for key in ['calibration_id','channel_map_id','sensor_serials','guide_version']:
        if cal[key]!=r[key]:e.append('calibration_binding_mismatch:'+key)
    if not finite(cal['valid_from']) or not finite(cal['valid_until']) or cal['valid_until']<cal['valid_from']:e.append('invalid_calibration_interval');return e
    raw_ids=set(); attempt_keys=set(); valid_counts={key:0 for key in expected}; last_time=None
    if not isinstance(r['records'],list):return e+['invalid_records_type']
    for q in r['records']:
        keys=['raw_id','attempt_id','point_id','timestamp','coordinates_mm','frequency_hz','complex_pressures','sensor_serials','data_class','valid','failure_reason','settled','reference_locked','clipped','motion_stopped']+BIND
        if not isinstance(q,dict) or fail_missing(q,keys):e.append('incomplete_raw_record');continue
        if not isinstance(q['raw_id'],str) or not q['raw_id']:e.append('invalid_raw_id');continue
        if q['raw_id'] in raw_ids:e.append('duplicate_raw_id')
        raw_ids.add(q['raw_id'])
        if not isinstance(q['attempt_id'],str) or not q['attempt_id']:e.append('missing_attempt_identity');continue
        if not isinstance(q['point_id'],str):e.append('invalid_point_id');continue
        key=(q['point_id'],q['attempt_id'])
        if key in attempt_keys:e.append('duplicate_attempt_key')
        attempt_keys.add(key)
        if q['point_id'] not in expected:e.append('unscheduled_raw_point');continue
        s=expected[q['point_id']]
        for key in BIND+['sensor_serials','data_class']:
            if q[key]!=r[key]:e.append('raw_binding_mismatch:'+key)
        if q['coordinates_mm']!=s['coordinates_mm'] or q['frequency_hz']!=s['frequency_hz']:e.append('wrong_actual_condition')
        if not finite(q['timestamp']):e.append('invalid_timestamp')
        else:
            if not cal['valid_from']<=q['timestamp']<=cal['valid_until']:e.append('expired_calibration')
            if last_time is not None and q['timestamp']<last_time:e.append('raw_time_reversal')
            last_time=q['timestamp']
        p=q['complex_pressures']
        complete=isinstance(p,list) and len(p)==4 and all(isinstance(x,list) and len(x)==2 and all(finite(v) for v in x) for x in p)
        if q['valid'] is True:
            valid_counts[q['point_id']]+=1
            if not complete:e.append('complex_four_channels_required')
            if q['failure_reason'] is not None:e.append('valid_record_has_failure')
            for key in ['settled','reference_locked','motion_stopped']:
                if q[key] is not True:e.append('invalid_point_gate:'+key)
            if q['clipped'] is not False:e.append('clipped_or_unknown')
        elif q['valid'] is False:
            if not q['failure_reason']:e.append('failure_not_explained')
        else:e.append('unknown_validity')
    # This narrow validator checks one expanded run, not a multi-run campaign.
    # Its explicit fixture repeat_count must be one; no source repetition default is implied.
    if any(n==0 for n in valid_counts.values()):e.append('missing_valid_schedule_point')
    if any(n>1 for n in valid_counts.values()):e.append('ambiguous_multiple_valid_attempts')
    final=r['final_state']
    if not isinstance(final,dict) or any(final.get(k) is not True for k in ['source_off','motion_stopped','target_stored_or_absent','records_archived']):e.append('unsafe_or_incomplete_closure')
    return sorted(set(e))

def validate_transfer(r):
    e=fail_missing(r,['entity_id','origin','destination','identity_at_destination','detached','source_safe','retained','docked','old_version','new_version'])
    if e:return e
    if r['origin']==r['destination']:e.append('no_location_change')
    if r['identity_at_destination']!=r['entity_id']:e.append('wrong_item_at_destination')
    if any(r[k] is not True for k in ['detached','source_safe','retained','docked']):e.append('unsafe_transfer')
    if r['old_version']!=r['new_version']:e.append('transport_cannot_rewrite_version')
    return e

def modal_amplitudes(pressures):
    """Algebra on four supplied complex values; not a propagation/physics model."""
    if not isinstance(pressures,list) or len(pressures)!=4 or not all(isinstance(p,list) and len(p)==2 and all(finite(x) for x in p) for p in pressures):raise ValueError('Four finite complex values required')
    p=[complex(*q) for q in pressures]
    return {'a00_pair13':(p[0]+p[2])/2,'a00_pair24':(p[1]+p[3])/2,'a01':(p[0]-p[2])/2,'a10':(p[1]-p[3])/2}

def validate_derivative(d,raw_ids,typ):
    e=fail_missing(d,['data_class','raw_parent_ids','processing_version','acquisition_step_mm','display_step_mm','creates_measured_samples','validity_mask_preserved'])
    if e:return e
    if d['data_class']!='derived_analysis':e.append('derived_relabelled_as_measurement')
    if not d['raw_parent_ids'] or set(d['raw_parent_ids'])!=set(raw_ids):e.append('wrong_raw_parents')
    if not d['processing_version']:e.append('missing_processing_version')
    if d['creates_measured_samples'] is not False or d['validity_mask_preserved'] is not True:e.append('fabricated_or_erased_raw_points')
    if typ=='scan_2d' and (d['acquisition_step_mm']!=1.6 or d['display_step_mm']!=0.8):e.append('raw_display_grid_confusion')
    return e

def project_actor(goal,materials,cards,observations):
    """Illustrative test-only projection, not a production actor loader."""
    result={'goal':{k:goal[k] for k in ['id','goal','required_public_cards','public_observations']},'materials':materials,'qualified_cards':cards,'observations':observations}
    forbidden={'source_outcomes','reference_route','operation_ids','fault_seed','hidden_faults','expected_scientific_outcomes','evaluator_reference'}
    def inspect(v):
        if isinstance(v,dict):
            if set(v)&forbidden:raise ValueError('Forbidden actor projection field')
            for x in v.values():inspect(x)
        elif isinstance(v,list):
            for x in v:inspect(x)
    inspect(result)
    return result
