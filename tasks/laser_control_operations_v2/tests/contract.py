"""Original offline record contract. No hardware, network, FFT or physical solver.

The evaluator chooses fixture_id and provides the exact synthetic registry; an actor
submits ID-only events. Public fixtures are audit data, not production authentication.
"""
from copy import deepcopy
import hashlib
import json
import math

class ContractError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ContractError(message)

def finite_number(value, name='number'):
    require(type(value) in (int, float), name + ' must be numeric, not boolean')
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        raise ContractError(name + ' outside finite numeric range')
    require(math.isfinite(converted), name + ' must be finite')
    return converted

def strict_json(value):
    if type(value) is dict:
        require(all(type(k) is str for k in value), 'JSON object keys must be strings')
        for v in value.values(): strict_json(v)
    elif type(value) is list:
        for v in value: strict_json(v)
    elif type(value) in (int, float):
        finite_number(value)
    else:
        require(type(value) in (str, bool, type(None)), 'unsupported JSON type')

def canonical(value):
    try:
        strict_json(value)
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ContractError('noncanonical data') from exc

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def validate_arrays(frequency, psd):
    require(type(frequency) is list and type(psd) is list, 'spectral arrays must be lists')
    require(len(frequency) == len(psd) and len(frequency) >= 3, 'spectral lengths')
    f = [finite_number(v, 'frequency') for v in frequency]
    s = [finite_number(v, 'PSD') for v in psd]
    require(all(v > 0 for v in f), 'positive frequency support required')
    require(all(b > a for a, b in zip(f, f[1:])), 'frequency order must increase')
    require(all(v >= 0 for v in s), 'negative PSD')
    return f, s

def interpolate(f, s, value):
    value = finite_number(value, 'frequency bound')
    require(f[0] <= value <= f[-1], 'no extrapolation')
    for i, (a, b) in enumerate(zip(f, f[1:])):
        if a <= value <= b:
            return s[i] + (s[i+1]-s[i])*((value-a)/(b-a))
    return s[-1]

def clipped_grid(frequency, psd, low, high):
    f, s = validate_arrays(frequency, psd)
    low, high = finite_number(low, 'low'), finite_number(high, 'high')
    require(f[0] <= low < high <= f[-1], 'integration support unavailable')
    ff = [low]+[x for x in f if low < x < high]+[high]
    return ff, [interpolate(f, s, x) for x in ff]

def rms_frequency(frequency, psd, low, high):
    f, s = clipped_grid(frequency, psd, low, high)
    try:
        area = math.fsum((b-a)*(u/2+v/2) for a,b,u,v in zip(f,f[1:],s,s[1:]))
    except (OverflowError, ValueError) as exc:
        raise ContractError('integrated noise overflow') from exc
    require(math.isfinite(area) and area >= 0, 'invalid integrated noise')
    return math.sqrt(area)

def beta_linewidth(frequency, psd, low, high):
    """Finite-band beta-separation approximation; no missing-tail correction."""
    f, s = clipped_grid(frequency, psd, low, high)
    beta = 8*math.log(2)/(math.pi**2)
    pieces = []
    for a,b,u,v in zip(f,f[1:],s,s[1:]):
        da, db = u-beta*a, v-beta*b
        if da <= 0 and db <= 0:
            continue
        left, right = a, b
        if da < 0 or db < 0:
            scale = max(abs(da),abs(db))
            da_scaled,db_scaled=da/scale,db/scale
            cross = a+(b-a)*((-da_scaled)/(db_scaled-da_scaled))
            if da < 0:
                left = cross
            else:
                right = cross
        ul = u+(v-u)*((left-a)/(b-a))
        vr = u+(v-u)*((right-a)/(b-a))
        pieces.append((right-left)*(ul/2+vr/2))
    try:
        area = math.fsum(pieces)
    except (OverflowError, ValueError) as exc:
        raise ContractError('beta integral overflow') from exc
    require(math.isfinite(area) and area >= 0, 'invalid beta integral')
    result = math.sqrt(area)*math.sqrt(8*math.log(2))
    require(math.isfinite(result), 'linewidth overflow')
    return result

def suppression_dB(free, locked):
    require(type(free) is list and type(locked) is list and len(free)==len(locked) and bool(free), 'suppression arrays')
    output=[]
    for a,b in zip(free,locked):
        a,b=finite_number(a),finite_number(b)
        require(a>0 and b>0,'log ratio requires positive PSD')
        output.append(10*(math.log10(a)-math.log10(b)))
    return output

def unity_crossing_details(frequency, free, locked):
    f,a=validate_arrays(frequency,free)
    _,b=validate_arrays(frequency,locked)
    d=[u-v for u,v in zip(a,b)]
    require(all(math.isfinite(x) for x in d),'difference overflow')
    crossing=[];i=0
    while i<len(f):
        if d[i]==0:
            j=i
            while j+1<len(f) and d[j+1]==0: j+=1
            before=d[i-1] if i>0 else None
            after=d[j+1] if j+1<len(f) else None
            if j>i:
                crossing.append(dict(kind='unity_plateau',support_Hz=[f[i],f[j]],direction='ambiguous'))
            else:
                direction='endpoint' if before is None or after is None else 'downward' if before>0 and after<0 else 'upward' if before<0 and after>0 else 'touch'
                crossing.append(dict(kind='point',frequency_Hz=f[i],direction=direction))
            i=j+1;continue
        if i+1<len(f) and d[i+1]!=0 and ((d[i]>0)!=(d[i+1]>0)):
            u,v=d[i],d[i+1];scale=max(abs(u),abs(v));us,vs=u/scale,v/scale
            root=f[i]+(f[i+1]-f[i])*(us/(us-vs))
            crossing.append(dict(kind='point',frequency_Hz=root,direction='downward' if u>0 else 'upward'))
        i+=1
    return crossing

def unity_crossings(frequency, free, locked):
    """All isolated roots and plateau endpoints; inspect details for direction."""
    values=[]
    for row in unity_crossing_details(frequency,free,locked):
        values.extend([row['frequency_Hz']] if row['kind']=='point' else row['support_Hz'])
    return values

def voltage_psd_to_frequency(voltage_psd, gain_V_per_Hz):
    require(type(voltage_psd) is list and bool(voltage_psd),'voltage PSD list')
    gain=finite_number(gain_V_per_Hz,'gain')
    require(gain != 0,'zero discriminator gain')
    denom=gain*gain
    require(math.isfinite(denom) and denom>0,'unusable gain')
    output=[]
    for v in voltage_psd:
        v=finite_number(v,'voltage PSD');require(v>=0,'negative voltage PSD')
        x=v/denom;require(math.isfinite(x),'conversion overflow');output.append(x)
    return output

FULL=['REGISTER_INPUTS','VERIFY_QUALIFICATION','FREEZE_DESIGN','REQUEST_PIC_FABRICATION','VERIFY_PIC','REQUEST_PCB_ASSEMBLY','VERIFY_PACKAGING']
PREPARED=['REGISTER_INPUTS','VERIFY_QUALIFICATION','VERIFY_PACKAGING']
MEASURE=['DOCK_PACKAGE','VERIFY_INTERLOCK','REQUEST_ALIGNMENT','VERIFY_ALIGNMENT','CALIBRATE_FREQUENCY_AXIS','REQUEST_OPEN_LOOP','ACQUIRE_OPEN_LOOP','FIT_RING','CALIBRATE_DISCRIMINATOR','REGISTER_LASER','VERIFY_REFERENCE_CHAIN','FREEZE_CONTROL_SETTINGS','ACQUIRE_FREE_RUNNING','REQUEST_LOCK','VERIFY_LOCK','ACQUIRE_IN_LOOP','ACQUIRE_HETERODYNE','VALIDATE_PSD','ANALYZE_NOISE']
CLOSE=['REQUEST_SAFE_OFF','VERIFY_SAFE_OFF','UNDOCK_PACKAGE','INSPECT_PACKAGE','ARCHIVE','CLEAN_STORE']
MODES=('OK','LOCK_LOSS','DAMAGED')
FIXTURE_IDS=tuple(f'DFB{d}:{r}:V{v}:{m}' for d in (1,2,3) for r in ('FULL','PREPARED') for v in (0,1,2) for m in MODES)+('HOLD',)
SPECTRUM_KEYS={'record_id','channel','frequency_Hz','psd_Hz2_per_Hz','context','convention','units','raw_hash','acquisition'}

def context_for(fixture_id):
    require(type(fixture_id) is str and fixture_id in FIXTURE_IDS,'unknown fixture')
    if fixture_id=='HOLD':
        return {'episode_id':'HOLD','attempt_id':'HOLD:A','branch_id':'QUALIFICATION_HOLD','preparation_route':'NONE','package_id':'UNQUALIFIED','qualification_revision':'NONE'}
    laser,route,variant,mode=fixture_id.split(':')
    return dict(episode_id=fixture_id,attempt_id=fixture_id+':A',branch_id=laser+'_STABILIZATION',preparation_route=route,design_hash=digest(['authored_design',fixture_id]),pic_id=fixture_id+':PIC',pic_lot='SYNTHETIC_LOT_'+variant,pcb_id=fixture_id+':PCB',package_id=fixture_id+':PACKAGE',dfb_id=laser+':SYNTHETIC:'+variant,dfb_wavelength_nm={'DFB1':1550.7,'DFB2':1547.8,'DFB3':1551.4}[laser],mount_revision=fixture_id+':M1',alignment_id=fixture_id+':AL1',frequency_calibration_id=fixture_id+':FC1',discriminator_calibration_id=fixture_id+':DC1',reference_chain_id=fixture_id+':REF',reference_lock_revision=fixture_id+':RL1',control_revision=fixture_id+':CTRL1',bias_noise_revision=fixture_id+':BIAS1',power_plane_id=fixture_id+':POWER1',temperature_revision=fixture_id+':T1',analysis_revision=fixture_id+':AN1',qualification_revision=fixture_id+':QUAL1')

def sequence_for(fixture_id):
    context_for(fixture_id)
    if fixture_id=='HOLD':
        return ['REGISTER_INPUTS','HOLD_QUALIFICATION','ARCHIVE','CLEAN_STORE']
    _,route,_,mode=fixture_id.split(':')
    seq=list(FULL if route=='FULL' else PREPARED)
    if mode=='LOCK_LOSS':
        seq+=MEASURE[:MEASURE.index('REQUEST_LOCK')+1]+['HOLD_LOCK']
    else:
        seq+=MEASURE
    seq+=CLOSE
    if mode=='DAMAGED':
        seq.insert(seq.index('ARCHIVE'),'QUARANTINE')
    return seq

def spectrum(channel, context, variant):
    f=[500.,1500.,5000.,10000.,20000.,40000.]
    scale=1+variant*0.13
    values={'free_running_comb_heterodyne':[8000,6000,4000,3000,2500,2000], 'locked_comb_heterodyne':[100,140,600,1000,3500,2600], 'locked_fpga_in_loop':[20,25,40,80,200,300]}[channel]
    values=[v*scale for v in values]
    acq=dict(sample_rate_Hz=200000.,rbw_Hz=100.,enbw_Hz=150.,window='authored_synthetic_psd_no_fft',one_sided=True,alias_check='synthetic_fixture_only',stationary=True,clipped=False,reference_floor_qualified=True)
    raw=dict(channel=channel,frequency_Hz=f,psd_Hz2_per_Hz=values,context=context,acquisition=acq)
    return dict(record_id=context['episode_id']+':'+channel,channel=channel,frequency_Hz=f,psd_Hz2_per_Hz=values,context=deepcopy(context),convention='one_sided',units='Hz^2/Hz',raw_hash=digest(raw),acquisition=acq)

def validate_spectrum(record,channel,context):
    require(type(record) is dict and set(record)==SPECTRUM_KEYS,'spectrum schema')
    require(record['channel']==channel and record['context']==context,'spectrum lineage/channel')
    require(record['record_id']==context['episode_id']+':'+channel,'spectrum ID')
    require(record['convention']=='one_sided' and record['units']=='Hz^2/Hz','spectrum convention/units')
    f,s=validate_arrays(record['frequency_Hz'],record['psd_Hz2_per_Hz'])
    a=record['acquisition']
    require(type(a) is dict and set(a)=={'sample_rate_Hz','rbw_Hz','enbw_Hz','window','one_sided','alias_check','stationary','clipped','reference_floor_qualified'},'acquisition schema')
    fs=finite_number(a['sample_rate_Hz']);rbw=finite_number(a['rbw_Hz']);enbw=finite_number(a['enbw_Hz'])
    require(fs>2*f[-1] and 0<rbw<=enbw,'sampling/ENBW support')
    require(a['one_sided'] is True and a['stationary'] is True and a['clipped'] is False and a['reference_floor_qualified'] is True,'acquisition validation')
    require(a['window']=='authored_synthetic_psd_no_fft' and a['alias_check']=='synthetic_fixture_only','fixture estimator identity')
    raw=dict(channel=channel,frequency_Hz=record['frequency_Hz'],psd_Hz2_per_Hz=record['psd_Hz2_per_Hz'],context=context,acquisition=a)
    require(record['raw_hash']==digest(raw),'raw spectral hash')
    return f,s

def analysis(free,locked,inloop,context):
    f,s0=validate_spectrum(free,'free_running_comb_heterodyne',context)
    f1,s1=validate_spectrum(locked,'locked_comb_heterodyne',context)
    f2,s2=validate_spectrum(inloop,'locked_fpga_in_loop',context)
    require(f==f1==f2,'matched spectral grids')
    details=unity_crossing_details(f,s0,s1)
    crossing=unity_crossings(f,s0,s1)
    downward=[row['frequency_Hz'] for row in details if row['kind']=='point' and row['direction']=='downward']
    ambiguity=len(details)!=1 or any(row['kind']!='point' or row['direction']!='downward' for row in details)
    return dict(origin='authored_synthetic_only',support_Hz=[f[0],f[-1]],independent_rms_free_Hz=rms_frequency(f,s0,f[0],f[-1]),independent_rms_locked_Hz=rms_frequency(f,s1,f[0],f[-1]),in_loop_relative_rms_Hz=rms_frequency(f,s2,f[0],f[-1]),suppression_dB=suppression_dB(s0,s1),unity_crossings_Hz=crossing,unity_crossing_details=details,unity_crossing_ambiguous=ambiguity,first_downward_crossing_Hz=downward[0] if downward else None,finite_band_beta_free_Hz=beta_linewidth(f,s0,f[0],f[-1]),finite_band_beta_locked_Hz=beta_linewidth(f,s1,f[0],f[-1]),missing_tails='not estimated',physical_measurement=False)

def fixture(fixture_id):
    """Return a fresh evaluator bundle; never accept actor supplied fixture settings."""
    context=context_for(fixture_id)
    hold=fixture_id=='HOLD'
    route='NONE' if hold else fixture_id.split(':')[1]
    mode='HOLD' if hold else fixture_id.split(':')[3]
    v=0 if hold else int(fixture_id.split(':')[2][1:])
    spectra={} if hold else {c:spectrum(c,context,v) for c in ('free_running_comb_heterodyne','locked_comb_heterodyne','locked_fpga_in_loop')}
    gain=(-1 if v==1 else 1)*1e-7
    receipts={};events=[];previous='GENESIS'
    for index,op in enumerate(sequence_for(fixture_id)):
        rid=fixture_id+':R'+str(index)
        payload={'evidence_type':'independent_observation','verified':True,'synthetic_only':True}
        if op.startswith('REQUEST_'):
            payload={'evidence_type':'request_acknowledgement','accepted':True,'synthetic_only':True}
        if op=='VERIFY_PACKAGING': payload.update(preparation_origin='foundry_and_assembly_receipts' if route=='FULL' else 'prepared_intake_only',upstream_fabrication_credited=route=='FULL')
        if op=='CALIBRATE_FREQUENCY_AXIS': payload.update(frequency_map_id=context['frequency_calibration_id'],reference_fsr_Hz=20000000.,mapping_hash=digest([context['frequency_calibration_id'],'synthetic_mapping']),frequency_units='Hz',direction='increasing',qualified_uncertainty_origin='authored_fixture_only')
        if op=='ACQUIRE_OPEN_LOOP': payload.update(sweep_id=fixture_id+':SWEEP',sniffer_trace_id=fixture_id+':SNIFFER',error_trace_id=fixture_id+':ERROR',common_clock_id=fixture_id+':CLOCK',raw_pair_hash=digest([fixture_id,'authored_simultaneous_pair']),trace_processing_implemented=False)
        if op=='FIT_RING': payload.update(fit_model_id=fixture_id+':FIT',raw_pair_hash=digest([fixture_id,'authored_simultaneous_pair']),numerical_fit_implemented=False)
        if op=='FREEZE_CONTROL_SETTINGS': payload.update(settings_hash=digest([fixture_id,'synthetic_settings']),bias_noise_revision=context['bias_noise_revision'],hardware_limits_qualified='synthetic_receipt_only',settings_are_actuation_parameters=False)
        if op=='CALIBRATE_DISCRIMINATOR': payload.update(gain_V_per_Hz=gain,units='V/Hz',linear_range_Hz=[-10000.,10000.],heater_state='off')
        if op=='ACQUIRE_FREE_RUNNING': payload.update(spectrum=spectra['free_running_comb_heterodyne'])
        if op=='VERIFY_REFERENCE_CHAIN': payload.update(fp_locked=True,repetition_locked=True,ceo_locked=True,beat_identity_verified=True,reference_floor_qualified=True)
        if op=='VERIFY_LOCK': payload.update(lock_observed=True,saturation=False,cycle_slip=False)
        if op=='HOLD_LOCK': payload.update(lock_observed=False,dependent_acquisition_blocked=True)
        if op=='ACQUIRE_IN_LOOP': payload.update(spectrum=spectra['locked_fpga_in_loop'],error_voltage_psd=[s*gain*gain for s in spectra['locked_fpga_in_loop']['psd_Hz2_per_Hz']],gain_V_per_Hz=gain,interpretation='relative_to_cavity')
        if op=='ACQUIRE_HETERODYNE': payload.update(spectrum=spectra['locked_comb_heterodyne'],method='comb_referenced_heterodyne')
        if op=='VERIFY_SAFE_OFF': payload.update(optical_isolated=True,electrical_isolated=True,supported=True)
        if op=='INSPECT_PACKAGE': payload.update(damaged=mode=='DAMAGED',reuse_allowed=mode!='DAMAGED')
        if op=='QUARANTINE': payload.update(reuse_allowed=False,disposition='quarantined')
        if op=='HOLD_QUALIFICATION': payload.update(qualified=False,activation_occurred=False)
        if op=='ARCHIVE': payload.update(all_attempts_retained=True)
        if op=='CLEAN_STORE': payload.update(clean_observed=True,stored_observed=True,activation_occurred=False if hold else True,disposition='quarantined' if mode=='DAMAGED' else 'stored')
        rec=dict(evidence_id=rid,operation_id=op,context=deepcopy(context),payload=payload,previous_hash=previous)
        rec['receipt_hash']=digest(rec);previous=rec['receipt_hash'];receipts[rid]=rec
        events.append(dict(event_id=fixture_id+':E'+str(index),operation_id=op,evidence_id=rid))
    return dict(fixture_id=fixture_id,context=context,receipts=receipts,registry_hash=digest(receipts),events=events)

def evaluate(events,registry,fixture_id):
    """The fixture identifier is evaluator-owned; actor input is events only."""
    expected=fixture(fixture_id)
    require(type(registry) is dict,'registry schema')
    # A JSON canonical digest is type sensitive (True differs from 1) and rejects NaN.
    require(digest(registry)==expected['registry_hash'],'registry not fixture-pinned')
    require(type(events) is list,'events must be list')
    require(len(events)==len(expected['events']),'incomplete or extra lifecycle events')
    seen_events=set();seen_evidence=set();previous='GENESIS'
    gained=None;free=locked=inloop=None;result=None;isolated=False;quarantined=False
    for actual,exp in zip(events,expected['events']):
        require(type(actual) is dict and set(actual)=={'event_id','operation_id','evidence_id'},'actor event schema')
        require(all(type(v) is str and v for v in actual.values()),'actor values must be IDs')
        require(actual==exp,'event order/identity/replay')
        require(actual['event_id'] not in seen_events and actual['evidence_id'] not in seen_evidence,'duplicate event/evidence')
        seen_events.add(actual['event_id']);seen_evidence.add(actual['evidence_id'])
        rec=registry[actual['evidence_id']];p=rec['payload'];op=actual['operation_id']
        require(rec['context']==expected['context'],'receipt context')
        unsigned={k:v for k,v in rec.items() if k!='receipt_hash'}
        require(rec['receipt_hash']==digest(unsigned) and rec['previous_hash']==previous,'receipt chain')
        previous=rec['receipt_hash']
        if op.startswith('REQUEST_'):
            require(p['evidence_type']=='request_acknowledgement','request must stay acknowledgement')
        else:
            require(p['evidence_type']=='independent_observation','state requires independent observation')
        if op=='CALIBRATE_DISCRIMINATOR': gained=finite_number(p['gain_V_per_Hz']);require(gained!=0,'zero gain')
        if op=='VERIFY_REFERENCE_CHAIN': require(all(p[k] is True for k in ('fp_locked','repetition_locked','ceo_locked','beat_identity_verified','reference_floor_qualified')),'reference lock/floor')
        if op=='VERIFY_LOCK':require(p['lock_observed'] is True and p['saturation'] is False and p['cycle_slip'] is False,'lock not established')
        if op=='ACQUIRE_FREE_RUNNING':free=p['spectrum']
        if op=='ACQUIRE_IN_LOOP':
            inloop=p['spectrum'];require(gained==p['gain_V_per_Hz'],'stale discriminator')
            converted=voltage_psd_to_frequency(p['error_voltage_psd'],gained)
            require(all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(converted,inloop['psd_Hz2_per_Hz'])),'voltage calibration mismatch')
        if op=='ACQUIRE_HETERODYNE':locked=p['spectrum'];require(p['method']=='comb_referenced_heterodyne','wrong final measurement route')
        if op=='ANALYZE_NOISE':result=analysis(free,locked,inloop,expected['context'])
        if op=='VERIFY_SAFE_OFF':isolated=all(p[k] is True for k in ('optical_isolated','electrical_isolated','supported'));require(isolated,'unsafe isolation')
        if op=='UNDOCK_PACKAGE':require(isolated,'unsafe undock')
        if op=='QUARANTINE':quarantined=p['reuse_allowed'] is False;require(quarantined,'damage disposition')
        if op=='ARCHIVE':require(p['all_attempts_retained'] is True,'failed attempts missing')
        if op=='CLEAN_STORE':require(p['clean_observed'] is True and p['stored_observed'] is True,'cleanup not observed')
    hold=fixture_id=='HOLD';mode='HOLD' if hold else fixture_id.split(':')[3]
    require(mode!='DAMAGED' or quarantined,'damage not quarantined')
    return dict(contract_passed=True,synthetic_only=True,analysis=result,closure='qualification_hold' if hold else 'quarantined' if mode=='DAMAGED' else 'lock_loss_safe_closed' if mode=='LOCK_LOSS' else 'stored',design_route_receipts_checked=not hold and fixture_id.split(':')[1]=='FULL',physical_execution=False,scientific_reproduction=False)
