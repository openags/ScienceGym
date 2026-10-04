"""Original finite synthetic contract fixtures. No hardware, solver or source data."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
BRANCHES={b['id']:b for b in read('branches.json')['branches']}
OPERATIONS={o['id']:o for o in read('operations.json')['operations']}
CONTEXT_KEYS=read('lineage_contract.json')['context_keys']
FAB={'STO_FABRICATION','KTO_FABRICATION','CNT_SQD_FABRICATION','CNT_DQD_FABRICATION','MODULE_ASSEMBLY'}
MEASURE=tuple(b for b,v in BRANCHES.items() if v['execution_class']=='closed_service' and b not in FAB)
MODELS=tuple(b for b,v in BRANCHES.items() if v['execution_class']=='external_model_metadata')
CONTEXT=tuple(b for b,v in BRANCHES.items() if v['execution_class']=='source_context_metadata')
OUTCOMES=('GOOD','DAMAGED','DATA_HOLD','ISOLATION_HOLD')
FIXTURE_IDS=tuple(f'{b}:{entry}:{out}' for b in MEASURE for entry in ('FULL','PREPARED') for out in OUTCOMES)+tuple(f'{b}:FULL:{out}' for b in sorted(FAB) for out in OUTCOMES)+tuple('MODEL:'+b for b in MODELS)+tuple('CONTEXT:'+b for b in CONTEXT)+tuple('HOLD:'+h for h in ('QUALIFICATION','SOURCE_CONFLICT','CALIBRATION','DATA','ISOLATION'))
class ContractError(ValueError):pass
def require(ok,message):
 if not ok:raise ContractError(message)
def finite(x):
 require(type(x) in (int,float),'finite real number required, not bool/string')
 try:y=float(x)
 except (ValueError,OverflowError):raise ContractError('number out of finite range')
 require(math.isfinite(y),'nonfinite number');return y
def result(x):
 if isinstance(x,complex):require(math.isfinite(x.real) and math.isfinite(x.imag),'nonfinite result')
 else:require(math.isfinite(x),'nonfinite result')
 return x
def strict(x):
 if type(x) is dict:
  require(all(type(k) is str for k in x),'string keys only')
  for v in x.values():strict(v)
 elif type(x) is list:
  for v in x:strict(v)
 elif type(x) is float:finite(x)
 elif type(x) in (str,bool,int) or x is None:pass
 else:raise ContractError('JSON type required')
def canonical(x):
 strict(x)
 try:return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
 except (ValueError,OverflowError,TypeError) as e:raise ContractError(str(e))
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def reflection(resistance_ohm,reactance_ohm,z0_ohm):
 r,x,z0=map(finite,(resistance_ohm,reactance_ohm,z0_ohm));require(r>=0 and z0>0,'passive resistance and positive reference impedance')
 try:g=result((complex(r,x)-z0)/(complex(r,x)+z0))
 except (OverflowError,ZeroDivisionError):raise ContractError('invalid reflection arithmetic')
 return {'real':g.real,'imag':g.imag,'magnitude':abs(g),'phase_rad':math.atan2(g.imag,g.real),'phase_defined':abs(g)>0,'synthetic_only':True}
def series_capacitance(c1_F,c2_F):
 c1,c2=map(finite,(c1_F,c2_F));require(c1>0 and c2>0,'positive capacitances')
 v=result(min(c1,c2)/(1+min(c1,c2)/max(c1,c2)));require(v>0,'capacitance underflow');return v
def loss_bound(resistance_ohm,capacitance_F,frequency_Hz):
 r,c,f=map(finite,(resistance_ohm,capacitance_F,frequency_Hz));require(r>=0 and c>0 and f>0,'nonnegative loss and positive capacitance/frequency')
 return {'tan_delta_upper_bound':result(r*c*2*math.pi*f),'attribution':'circuit_inclusive_upper_bound','intrinsic_loss_measured':False}
def snr_from_power(signal_W,noise_W):
 s,n=map(finite,(signal_W,noise_W));require(s>0 and n>0,'positive signal and noise')
 ratio=result(s/n);require(ratio>0,'SNR ratio underflow');return {'power_ratio':ratio,'dB':result(10*math.log10(ratio))}
def sensitivity(delta,snr_dB,bandwidth_Hz,unit,sideband_factor=2):
 d,s,b=map(finite,(delta,snr_dB,bandwidth_Hz));require(d>0 and b>0,'positive modulation and bandwidth')
 require(unit in ('e','F'),'explicit charge/capacitance unit');require(type(sideband_factor) is int and sideband_factor==2,'declared two-sideband convention')
 try:den=result((10**(s/20))*math.sqrt(2*b));require(den>0,'positive finite sensitivity denominator');v=result(d/den);require(v>0,'sensitivity underflow')
 except (OverflowError,ZeroDivisionError):raise ContractError('sensitivity arithmetic out of range')
 return {'value':v,'unit':unit+'/sqrt(Hz)','convention':'delta/(10**(SNR_dB/20)*sqrt(2*bandwidth_Hz))','synthetic_only':True}
def quadrature_snr(signal,background):
 require(type(background) is list and len(background)>=2,'background samples required');vals=[finite(v) for v in background];s=finite(signal)
 try:
  m=result(math.fsum(vals)/len(vals));var=result(math.fsum((v-m)**2 for v in vals)/(len(vals)-1));require(var>0,'nonzero background sample variance');ratio=result((s-m)**2/var);require(ratio>0,'nonzero signal contrast')
 except (OverflowError,ZeroDivisionError):raise ContractError('quadrature arithmetic out of range')
 return {'background_mean':m,'background_sample_sd':math.sqrt(var),'power_ratio':ratio,'dB':result(10*math.log10(ratio)),'sample_count':len(vals),'independent_device_count':None}
def phase_regime(record):
 require(type(record) is dict and set(record)=={'regime','evidence_kind','phase_record_id','calibration_revision','expected_calibration_revision'},'phase regime fields')
 require(record['regime'] in ('under','matched','over'),'known coupling regime');require(record['evidence_kind']=='independent_phase','magnitude-only coupling ambiguous')
 require(type(record['phase_record_id']) is str and record['phase_record_id'],'phase evidence required');require(all(type(record[k]) is str and record[k] for k in ('calibration_revision','expected_calibration_revision')),'nonempty calibration IDs');require(record['calibration_revision']==record['expected_calibration_revision'],'stale phase calibration');return record['regime']
def stability(raw):
 require(type(raw) is dict and set(raw)=={'time_s','x','y','units','synthetic_only'},'stability fields')
 require(raw['synthetic_only'] is True and raw['units']=={'time':'s','quadrature':'dimensionless'},'stability units/scope')
 arrays=[raw[k] for k in ('time_s','x','y')];require(all(type(a) is list for a in arrays) and len(arrays[0])>=3 and len(set(map(len,arrays)))==1,'matched stability arrays')
 t,x,y=[[finite(v) for v in a] for a in arrays];require(all(b>a for a,b in zip(t,t[1:])),'strict time chronology')
 try:
  mx,my=math.fsum(x)/len(x),math.fsum(y)/len(y);mt=math.fsum(t)/len(t)
  den=math.fsum((v-mt)**2 for v in t);require(den>0,'positive time variance')
  sx=result(math.fsum((a-mt)*(b-mx) for a,b in zip(t,x))/den);sy=result(math.fsum((a-mt)*(b-my) for a,b in zip(t,y))/den)
  scatter=[result(math.hypot(a-mx,b-my)) for a,b in zip(x,y)]
 except (OverflowError,ZeroDivisionError):raise ContractError('stability arithmetic out of range')
 return {'centered_scatter':scatter,'x_drift_per_s':sx,'y_drift_per_s':sy,'observed_span_s':t[-1]-t[0],'no_drift_claimed':False,'varactor_noise_absence_claimed':False,'independent_device_count':1}
def hysteresis(forward,reverse):
 def rows(data,direction):
  require(type(data) is dict and set(data)=={'direction','history_id','samples','synthetic_only'},'hysteresis fields')
  require(data['direction']==direction and data['synthetic_only'] is True,'direction/scope');require(type(data['history_id']) is str and data['history_id'],'history ID')
  require(type(data['samples']) is list and len(data['samples'])>=2,'hysteresis samples');out={}
  for r in data['samples']:
   require(type(r) is dict and set(r)=={'coordinate_id','minimum_magnitude'},'hysteresis sample fields');k=r['coordinate_id'];require(type(k) is str and k and k not in out,'unique coordinates');v=finite(r['minimum_magnitude']);require(0<=v<=1,'normalized magnitude');out[k]=v
  return out
 a=rows(forward,'forward');b=rows(reverse,'reverse');require(forward['history_id']!=reverse['history_id'],'distinct histories');require(set(a)==set(b),'matched coordinate support');return {'differences':{k:result(a[k]-b[k]) for k in sorted(a)},'history_erased':False,'intrinsic_material_hysteresis_proven':False}
def paired_readout(left,right,mode):
 required={'sample_id','varactor_ids','device_id','circuit_revision','reference_plane_revision','filter_revision','thermal_revision','history_revision','amplifier_state','gain_noise_revision','transition_id','carrier_plan_revision','acquisition_plan_revision','comparison_region_id','baseline_revision','snr_dB','saturated','power_broadened','synthetic_only'}
 for r in (left,right):
  require(type(r) is dict and set(r)==required,'paired readout fields');require(r['synthetic_only'] is True,'synthetic scope');finite(r['snr_dB']);require(r['saturated'] is False and r['power_broadened'] is False,'excluded nonlinear record')
  require(all(type(r[k]) is str and r[k] for k in required-{'varactor_ids','snr_dB','saturated','power_broadened','synthetic_only'}),'nonempty lineage strings')
  require(type(r['varactor_ids']) is list and len(r['varactor_ids'])==2 and all(type(v) is str and v for v in r['varactor_ids']) and len(set(r['varactor_ids']))==2,'two varactor identities')
 require(mode=='JPA_OFF_ON','explicit pair mode');require(left['amplifier_state']=='off' and right['amplifier_state']=='on','off/on order')
 for k in ('sample_id','varactor_ids','device_id','circuit_revision','reference_plane_revision','filter_revision','thermal_revision','history_revision','transition_id','carrier_plan_revision','acquisition_plan_revision','comparison_region_id','baseline_revision'):require(left[k]==right[k],'incompatible paired '+k)
 require(left['gain_noise_revision']!=right['gain_noise_revision'],'independent state-specific amplifier calibration')
 return {'snr_improvement_dB':result(right['snr_dB']-left['snr_dB']),'source_gain_used':False}
def reconfiguration(before,after):
 fields={'varactor_ids','material','device_id','device_kind','module_revision','circuit_revision','calibration_revision','history_revision','series_capacitor_present','synthetic_only'}
 for r in (before,after):
  require(type(r) is dict and set(r)==fields,'reconfiguration fields');require(r['synthetic_only'] is True and r['material']=='STO','same STO specimen scope');require(type(r['varactor_ids']) is list and len(r['varactor_ids'])==2 and all(type(v) is str and v for v in r['varactor_ids']) and len(set(r['varactor_ids']))==2,'two stable varactor IDs')
  for k in ('device_id','module_revision','circuit_revision','calibration_revision','history_revision'):require(type(r[k]) is str and r[k],'revision ID')
 require(before['device_kind']=='SQD' and after['device_kind']=='DQD','SQD to DQD route');require(before['varactor_ids']==after['varactor_ids'],'shared STO physical identity lost');require(before['series_capacitor_present'] is False and after['series_capacitor_present'] is True,'DQD series topology')
 for k in ('device_id','module_revision','circuit_revision','calibration_revision'):require(before[k]!=after[k],'stale reconfiguration '+k)
 require(before['history_revision']==after['history_revision'],'custody cannot reset sweep history');return {'same_varactors_preserved':True,'physical_reassembly_executed':False}
def fixture(fid):
 require(type(fid) is str and fid in FIXTURE_IDS,'evaluator selects finite fixture')
 parts=fid.split(':');special=parts[0] in ('MODEL','CONTEXT','HOLD');bid=parts[1] if special else parts[0]
 ctx={k:fid+':'+k for k in CONTEXT_KEYS};ctx['branch_id']=bid
 comparison_constituents={m:{'sample_id':fid+':specimen:'+m,'material_revision':fid+':material:'+m,'material':m} for m in ('STO','KTO')} if bid=='STO_KTO_COMPARISON' else {}
 if comparison_constituents:ctx['sample_id']=fid+':comparison_bundle'
 events=[];receipts={};last=None
 def add(op,deps=None,payload=None):
  nonlocal last
  require(op in OPERATIONS,'unknown operation')
  n=len(events)+1;eid=fid+':E'+str(n);rid=fid+':R'+str(n)
  p={'synthetic_only':True,'role':'request_acknowledgement' if op.startswith('REQUEST_') else 'independent_record'}
  if payload:p.update(payload)
  r={'evidence_id':rid,'operation_id':op,'context':deepcopy(ctx),'depends_on':([last] if last else []) if deps is None else deps,'payload':p}
  receipts[rid]=r;events.append({'event_id':eid,'operation_id':op,'evidence_id':rid});last=rid;return rid
 add('REGISTER_INPUTS')
 if parts[0]=='HOLD':
  add('HOLD_'+parts[1],payload={'reason':'missing independently qualified input'});add('ARCHIVE_RECORDS');add('CLEAN_STATION',payload={'disposition':'held_contained','physical_cleanup_executed':False})
 else:
  for op in ('VERIFY_QUALIFICATION','FREEZE_DESIGN','RELEASE_DESIGN','FREEZE_ROUTE_PLAN'):add(op,payload={'scope':'offline_synthetic_only'})
  branch=BRANCHES[bid]
  if special:
   for op in branch['route_operation_ids']:add(op,payload={'solver_executed':False,'physical_execution':False})
   add('ARCHIVE_RECORDS');add('CLEAN_STATION',payload={'disposition':'metadata_closed','physical_cleanup_executed':False})
  else:
   entry,out=parts[1:];measured=bid in MEASURE
   if measured:
    if entry=='FULL':
     for preparation_branch in branch['full_preparation_branch_ids']:
      for op in BRANCHES[preparation_branch]['route_operation_ids']:
       preparation_payload={'preparation_scope':'synthetic '+preparation_branch+' ancestry only'}
       material=preparation_branch.split('_')[0]
       if material in comparison_constituents:preparation_payload.update(constituent=deepcopy(comparison_constituents[material]),comparison_bundle_id=ctx['sample_id'])
       add(op,payload=preparation_payload)
    else:
     add('RECEIVE_PREPARED',payload={'fabrication_credit':False});add('VERIFY_ANCESTRY',payload={'ancestry_hash':digest(['synthetic independent ancestry',fid]),'comparison_constituents':deepcopy(comparison_constituents)})
    for op in ('INSPECT_SAMPLE','TRANSFER_CARRIER','DOCK_MODULE','VERIFY_PORT_MAP','VERIFY_MOUNT','FREEZE_CIRCUIT_CARD','REQUEST_CRYOGENIC_SERVICE','VERIFY_THERMAL_RECORD','VERIFY_INTERLOCK','VERIFY_RF_CALIBRATION','VERIFY_GAIN_NOISE_CALIBRATION','VERIFY_FILTER_CALIBRATION','FREEZE_MEASUREMENT_PLAN'):add(op)
   if bid=='MODULE_ASSEMBLY':
    add('RECEIVE_PREPARED',payload={'fabrication_credit':False});add('VERIFY_ANCESTRY',payload={'ancestry_hash':digest(['independent incoming fabrication',fid])})
   # Non-analysis route records are returned independently after each request.
   analysis=[]
   for op in branch['route_operation_ids']:
    if op.startswith(('ANALYZE_','COMPARE_')):analysis.append(op)
    else:add(op)
   raw={'record_id':fid+':raw','time_s':[0,1,2],'x':[0.01,0.011,0.009],'y':[0.02,0.019,0.021],'units':{'time':'s','quadrature':'dimensionless'},'synthetic_only':True,'source_data':False}
   if comparison_constituents:raw['comparison_constituents']=deepcopy(comparison_constituents)
   root=add('ACQUIRE_RECORDS',payload={'raw':raw,'raw_hash':digest(raw),'acquisition_complete':out!='DATA_HOLD'}) if measured else last
   if out=='DATA_HOLD':analysis_end=add('HOLD_DATA')
   else:
    if measured:add('VALIDATE_RECORDS')
    for op in analysis:add(op,payload={'source_expected_outcome_used':False,'real_analysis_executed':False})
    analysis_end=last
   add('REQUEST_SAFE_OFF',deps=[root])
   if out=='ISOLATION_HOLD':add('HOLD_ISOLATION',payload={'safe_release_observed':False});disposition='held_contained'
   else:
    add('VERIFY_SAFE_OFF',payload={'safe_release_observed':True})
    if measured:add('UNDOCK_MODULE')
    add('INSPECT_SAMPLE',payload={'condition':'damaged' if out=='DAMAGED' else 'intact','history_erased':False})
    if out=='DAMAGED':add('QUARANTINE_SAMPLE')
    disposition='quarantined' if out=='DAMAGED' else 'stored'
   closure_end=last;add('ARCHIVE_RECORDS',deps=list(dict.fromkeys([analysis_end,closure_end])))
   if disposition!='held_contained':add('STORE_SAMPLE',payload={'disposition':disposition,'fabrication_credit':entry=='FULL' and out=='GOOD' and bid!='MODULE_ASSEMBLY','virgin_reset':False})
   add('CLEAN_STATION',payload={'disposition':disposition,'physical_cleanup_executed':False})
 return deepcopy({'fixture_id':fid,'context':ctx,'events':events,'receipts':receipts,'registry_digest':digest(receipts)})
def evaluate(events,registry,expected_fixture_id):
 expected=fixture(expected_fixture_id)
 require(type(events) is list and type(registry) is dict,'event list and independent registry required')
 require(canonical(registry)==canonical(expected['receipts']),'registry differs from evaluator-pinned finite evidence')
 require(len(events)==len(expected['events']),'missing/extra event occurrence')
 expected_events={e['event_id']:e for e in expected['events']};seen=set();observed=set()
 for event in events:
  require(type(event) is dict and set(event)=={'event_id','operation_id','evidence_id'},'actor may supply IDs only')
  require(all(type(v) is str and v for v in event.values()),'nonempty IDs required');eid=event['event_id']
  require(eid in expected_events and eid not in seen,'unknown/duplicate occurrence');require(event==expected_events[eid],'event/evidence/operation mismatch')
  receipt=registry[event['evidence_id']];require(set(receipt['depends_on'])<=observed,'dependency order violated');seen.add(eid);observed.add(event['evidence_id'])
 parts=expected_fixture_id.split(':');good=len(parts)==3 and parts[-1]=='GOOD';measured=parts[0] in MEASURE
 return {'contract_passed':True,'synthetic_instance_complete':good,'synthetic_preparation_lineage_checked':good and parts[1]=='FULL','synthetic_measurement_metadata_checked':good and measured,'numerical_metadata_checked':parts[0]=='MODEL','whole_campaign_complete':False,'physical_execution':False,'numerical_solver_execution':False,'scientific_reproduction':False,'whole_paper_execution_complete':False,'source_expected_outcome_used':False,'production_authentication_established':False}
def circuit_card(card,expected_family):
 cards={c['id']:c for c in read('circuit_family_cards.json')['cards']}
 require(expected_family in cards,'known circuit family');require(type(card) is dict,'circuit card object')
 require(canonical(card)==canonical(cards[expected_family]),'circuit family mismatch or unsupported alteration')
 return {'source_card_matches':True,'hardware_qualified':False,'physical_topology_verified':False}
