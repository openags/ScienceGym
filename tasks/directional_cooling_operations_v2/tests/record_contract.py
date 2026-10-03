"""Authored record validators, not a robot/thermal simulation or runtime evaluator."""
import math

def finite_number(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def validate_plateau(r):
    errors=[]
    required=['id','attempt_id','sample_id','assembly_version','condition_signature','calibration_id','step_start_s','step_end_s','summary_start_s','summary_end_s','sampling_period_s','emitter_area_m2','temperature_units','power_units','data_class','samples','stable','shade_valid','output_saturated','intervention_intervals']
    for k in required:
        if k not in r or r[k] is None:errors.append('missing:'+k)
    if errors:return errors
    for k in ['step_start_s','step_end_s','summary_start_s','summary_end_s','sampling_period_s','emitter_area_m2']:
        if not finite_number(r[k]):errors.append('nonfinite:'+k)
    if errors:return errors
    if r['step_end_s']-r['step_start_s'] != 300:errors.append('wrong_step_duration')
    if r['summary_end_s'] != r['step_end_s'] or r['summary_start_s'] != r['step_end_s']-120:errors.append('shifted_summary_window')
    if r['sampling_period_s'] <= 0 or r['emitter_area_m2'] <= 0:errors.append('invalid_cadence_or_area')
    if r['temperature_units']!='C' or r['power_units']!='W':errors.append('invalid_units')
    if r['data_class'] not in ['measured_episode','synthetic_mock']:errors.append('source_or_model_not_observation')
    if r['stable'] is not True:errors.append('not_stable')
    if r['shade_valid'] is not True:errors.append('shade_not_verified')
    if r['output_saturated'] is not False:errors.append('output_saturated_or_unknown')
    a,b=r['summary_start_s'],r['summary_end_s']
    for gap in r['intervention_intervals']:
        if gap[0] < b and gap[1] > a:errors.append('intervention_in_summary')
    vals=[]
    for s in r['samples']:
        if not all(k in s for k in ['time_s','temperature','power','sample_id','assembly_version','condition_signature','calibration_id','valid']):errors.append('incomplete_sample');continue
        if any(not finite_number(s[k]) for k in ['time_s','temperature','power']):errors.append('nonfinite_sample');continue
        if a <= s['time_s'] <= b:
            vals.append(s)
            if s['valid'] is not True:errors.append('invalid_sample')
            for key in ['sample_id','assembly_version','condition_signature','calibration_id']:
                if s[key] != r[key]:errors.append('lineage_mismatch:'+key)
    times=[s['time_s'] for s in vals]
    if len(set(times))!=len(times):errors.append('duplicate_timestamp')
    if times!=sorted(times):errors.append('unordered_samples')
    # Synthetic fixture defines endpoint-inclusive cadence. Real instrument inclusion convention requires its own card.
    if r['sampling_period_s'] > 0:
        expected=[];t=a
        while t<=b and len(expected)<=100000:
            expected.append(t);t+=r['sampling_period_s']
        if times != expected:errors.append('incomplete_summary_coverage')
    return errors

def validate_transfer(r):
    e=[]
    for k in ['entity_id','origin','destination','detach_confirmed','output_safe','retained_carrier','destination_docked','identity_at_destination']:
        if k not in r or r[k] is None:e.append('missing:'+k)
    if e:return e
    if r['origin']==r['destination']:e.append('not_interstation_transfer')
    for k in ['detach_confirmed','output_safe','retained_carrier','destination_docked']:
        if r[k] is not True:e.append('invalid:'+k)
    if r['identity_at_destination']!=r['entity_id']:e.append('identity_mismatch')
    return e

def validate_modification(r):
    e=[]
    for k in ['assembly_id','old_version','new_version','removed_ids','installed_ids','post_qc_version']:
        if k not in r or r[k] is None:e.append('missing:'+k)
    if e:return e
    if not isinstance(r['old_version'],int) or not isinstance(r['new_version'],int) or r['new_version']<=r['old_version']:e.append('version_not_advanced')
    if not r['removed_ids'] or not r['installed_ids']:e.append('empty_component_change')
    if set(r['removed_ids']) & set(r['installed_ids']):e.append('same_component_relabelled')
    if r['post_qc_version']!=r['new_version']:e.append('stale_qc')
    return e
