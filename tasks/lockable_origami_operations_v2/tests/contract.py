"""Original offline synthetic contracts. No device, network, robot, physics or solver.

The evaluator, not the actor, selects an immutable registry fixture. Public fixture
pins test integrity only and are not production observation authentication.
"""
from copy import deepcopy
from decimal import Decimal, localcontext, DecimalException
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
BRANCHES={b['id']:b for b in json.loads((ROOT/'branches.json').read_text())['branches']}
CONTEXT_KEYS=tuple(json.loads((ROOT/'lineage_contract.json').read_text())['context_keys'])
class ContractError(ValueError):pass
def require(ok,message):
    if not ok:raise ContractError(message)
def number(v):
    require(type(v) in (int,float),'numeric nonboolean value required')
    try:x=float(v)
    except (OverflowError,ValueError):raise ContractError('number out of range')
    require(math.isfinite(x),'finite value required');return x
def strict(v):
    if type(v) is dict:
        require(all(type(k) is str for k in v),'JSON keys must be strings')
        for x in v.values():strict(x)
    elif type(v) is list:
        for x in v:strict(x)
    elif type(v) in (int,float):number(v)
    else:require(type(v) in (str,bool,type(None)),'JSON value required')
def canonical(v):
    try:strict(v);return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    except (ValueError,TypeError,OverflowError,RecursionError) as e:raise ContractError('invalid canonical record') from e
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def cast(v):
    try:x=float(v)
    except (ValueError,OverflowError):raise ContractError('output out of range')
    require(math.isfinite(x) and (v==0 or x!=0),'output overflow/underflow');return x
def calc(fn):
    try:
        with localcontext() as c:c.prec=2500;return cast(fn())
    except (DecimalException,ZeroDivisionError,OverflowError) as e:raise ContractError('arithmetic unavailable') from e
def dec(v):return Decimal.from_float(number(v))
def ratio(a,b):
    a,b=number(a),number(b);require(b!=0,'zero denominator');return calc(lambda:dec(a)/dec(b))
def integrate(x,y):
    require(type(x) is list and type(y) is list and len(x)==len(y) and len(x)>1,'matched integration arrays')
    xx=[dec(v) for v in x];yy=[dec(v) for v in y]
    return calc(lambda:sum(((b-a)*(u+v)/2 for a,b,u,v in zip(xx,xx[1:],yy,yy[1:])),Decimal(0)))
def raw_check(raw):
    require(type(raw) is dict,'raw record required');strict(raw)
    require(raw.get('synthetic_only') is True,'offline synthetic flag')
    require(raw.get('units')=={'time':'s','displacement':'m','force':'N','area':'m2','height':'m'},'unit contract')
    arrays=[raw.get(k) for k in ('time_s','displacement_m','force_N')]
    require(all(type(a) is list for a in arrays),'arrays required')
    require(len(arrays[0])>=3 and len(set(map(len,arrays)))==1,'raw array lengths')
    t,d,f=[[number(v) for v in a] for a in arrays]
    require(all(b>a for a,b in zip(t,t[1:])),'strict chronology')
    require(all(v>=0 for v in d+f),'positive displacement/load convention')
    require(raw.get('loading_kind') in ('compression','tension'),'declared loading kind')
    a,h=number(raw['area_m2']),number(raw['height_m']);require(a>0 and h>0,'positive geometry')
    require(type(raw.get('image_ids')) is list and len(raw['image_ids'])==len(t) and len(set(raw['image_ids']))==len(t),'registered images')
    require(all(type(x) is str and x for x in raw['image_ids']),'image IDs')
    return t,d,f,a,h
def linear_fit(x,y,indices,max_strain=None):
    require(type(indices) is list and len(indices)>=2 and all(type(i) is int and 0<=i<len(x) for i in indices),'fit indices')
    require(indices==sorted(set(indices)),'unique ordered fit indices')
    require(all(b>a for a,b in zip(x,x[1:])),'monotonic loading support')
    if max_strain is not None:require(all(x[i]<=number(max_strain) for i in indices),'fit outside declared strain support')
    xx=[dec(x[i]) for i in indices];yy=[dec(y[i]) for i in indices]
    def slope():
        xm=sum(xx,Decimal(0))/len(xx);ym=sum(yy,Decimal(0))/len(yy)
        den=sum(((z-xm)**2 for z in xx),Decimal(0));require(den>0,'zero fit variance')
        return sum(((a-xm)*(b-ym) for a,b in zip(xx,yy)),Decimal(0))/den
    return calc(slope)
def compression(raw,fit_indices,peak_index):
    require(type(raw) is dict and raw.get('loading_kind')=='compression','compression record required')
    require(type(fit_indices) is list and all(type(i) is int for i in fit_indices),'integer fit indices')
    _,d,f,a,h=raw_check(raw);x=[ratio(v,h) for v in d];y=[ratio(v,a) for v in f]
    require(type(peak_index) is int and 0<peak_index<len(y)-1,'interior peak required')
    peaks=[i for i in range(1,len(y)-1) if y[i]>y[i-1] and y[i]>=y[i+1]]
    require(bool(peaks) and peak_index==peaks[0],'first peak required, not densification global maximum')
    require(all(i<peak_index for i in fit_indices),'fit must precede first peak')
    m=linear_fit(x,y,fit_indices,.05)
    return dict(strain=x,stress_Pa=y,engaged_modulus_Pa=m,yield_first_peak_Pa=y[peak_index],first_peak_index=peak_index,loading_work_J_m3=integrate(x,y),work_kind='monotonic_loading_not_hysteresis',synthetic_only=True)
def tensile(raw,fit_indices,direction,normalization_direction):
    require(type(raw) is dict and raw.get('loading_kind')=='tension','tension record required')
    require(direction in ('MD','CD') and normalization_direction==direction,'direction-specific material reference')
    _,d,f,a,h=raw_check(raw);x=[ratio(v,h) for v in d];y=[ratio(v,a) for v in f]
    return dict(direction=direction,modulus_Pa=linear_fit(x,y,fit_indices),max_recorded_stress_Pa=max(y),gauge_m=h,synthetic_only=True)
def cyclic(raw,segments,baseline_peak,expected_cycles):
    require(type(raw) is dict and raw.get('loading_kind')=='compression','compression cycle record required')
    _,d,f,a,h=raw_check(raw)
    require(type(expected_cycles) is int and expected_cycles>0,'bounded cycle count')
    require(type(segments) is list and len(segments)==expected_cycles,'cycle schedule mismatch')
    baseline=number(baseline_peak);require(baseline>0,'independent positive baseline peak')
    previous=0;out=[]
    for seg in segments:
        require(type(seg) is list and len(seg)==3 and all(type(i) is int for i in seg),'cycle segment indices')
        start,turn,end=seg;require(start==previous and 0<=start<turn<end<len(d),'cycle chronology/coverage');previous=end
        require(all(v>=u for u,v in zip(d[start:turn],d[start+1:turn+1])) and d[turn]>d[start],'loading limb')
        require(all(v<=u for u,v in zip(d[turn:end],d[turn+1:end+1])) and d[end]<d[turn],'unloading limb')
        x=[ratio(v,h) for v in d[start:end+1]];y=[ratio(v,a) for v in f[start:end+1]]
        work=integrate(x,y);require(work>=0,'negative work; no absolute-value concealment')
        out.append(dict(open_path_work_J_m3=work,residual_strain=ratio(d[end]-d[start],h),reversal_fraction_of_independent_peak=ratio(f[turn],baseline),closed_loop_loss_claimed=False))
    require(previous==len(d)-1,'unsegmented tail');return out
def mixed_ratios(modulus,area,configuration1_modulus,configuration4_area):
    vals=[number(x) for x in [modulus,area,configuration1_modulus,configuration4_area]]
    require(vals[0]>=0 and vals[1]>=0 and vals[2]>0 and vals[3]>0,'positive independent mixed-mode baselines')
    return dict(modulus_relative_to_configuration1=ratio(vals[0],vals[2]),channel_area_relative_to_configuration4=ratio(vals[1],vals[3]),measured_permeability=False)
def specimen_statistics(rows):
    require(type(rows) is list and len(rows)>=2,'at least two independent specimens')
    require(all(type(r) is dict and set(r)=={'sample_id','value'} for r in rows),'sample values only')
    ids=[r['sample_id'] for r in rows];require(all(type(x) is str and x for x in ids) and len(set(ids))==len(ids),'independent unique specimen IDs')
    vv=[dec(r['value']) for r in rows]
    mean=calc(lambda:sum(vv,Decimal(0))/len(vv))
    sd=calc(lambda:(sum(((v-sum(vv,Decimal(0))/len(vv))**2 for v in vv),Decimal(0))/(len(vv)-1)).sqrt())
    return dict(n_specimens=len(rows),mean=mean,sample_sd=sd)
def compatible_mode(N,mode,tessellated):
    require(type(N) is int and N>=4 and N%2==0,'even primitive')
    require(type(tessellated) is bool,'tessellation flag')
    if mode=='IRREGULAR':require(not tessellated and N>4 and (N//2)%2==1,'irregular single-chain restriction')
    else:
        require(type(mode) is str and len(mode)==N//2 and set(mode)<={'A','O'},'explicit mode word')
    return True
PHYSICAL=tuple(b for b,r in BRANCHES.items() if r['execution_class']=='closed_service')
MODELS=tuple(b for b,r in BRANCHES.items() if r['execution_class']=='external_model_metadata')
OUTCOMES=('GOOD','DAMAGED','DATA_HOLD','ISOLATION_HOLD')
FIXTURE_IDS=tuple(f'{b}:{entry}:{out}' for b in PHYSICAL for entry in ('FULL','PREPARED') if not (b=='FULL_FABRICATION' and entry=='PREPARED') for out in OUTCOMES)+tuple('MODEL:'+b for b in MODELS)+('DESIGN:GENERATIVE_GEOMETRY','SOURCE:LOAD_BEARING_DEMONSTRATIONS')+tuple('HOLD:'+h for h in ('QUALIFICATION','GEOMETRY','CONFIGURATION','CALIBRATION','DATA'))
def context(fid):
    require(type(fid) is str and fid in FIXTURE_IDS,'unknown evaluator fixture')
    parts=fid.split(':');b=parts[1] if parts[0] in ('MODEL','DESIGN','SOURCE','HOLD') else parts[0]
    ctx={k:fid+':'+k for k in CONTEXT_KEYS};ctx.update(episode_id=fid,branch_id=b,design_hash=digest(['original_synthetic_design',fid]),layer_set_hash=digest(['layer1','layer2',fid]));return ctx

def raw_data(fid):
    if fid.startswith('CYCLIC_'):
        count=10 if fid.startswith('CYCLIC_N4') else 4;d=[0.0];f=[0.0];segs=[]
        for i in range(count):
            start=len(d)-1;base=i*.0001;d += [base+.001,base+.002,base+.001,(i+1)*.0001];f += [3.0,7.5,2.0,0.0];segs.append([start,start+2,start+4])
    else:d=[0,.0001,.0002,.0003,.0004,.0005,.0006,.0007];f=[0,.2,.5,.8,1.0,.6,.9,1.8];segs=None
    return dict(time_s=list(range(len(d))),displacement_m=d,force_N=f,loading_kind='tension' if fid.startswith('BASE_MATERIAL_TENSION') else 'compression',area_m2=.001,height_m=.01,units={'time':'s','displacement':'m','force':'N','area':'m2','height':'m'},image_ids=[fid+':IMG'+str(i) for i in range(len(d))],synthetic_only=True,cycle_segments=segs,baseline_peak_N=10.0)
def fixture(fid):
    ctx=context(fid);parts=fid.split(':');mode=parts[-1];receipts={};events=[];latest=None
    def add(op,deps=None,payload=None):
        nonlocal latest
        eid=fid+':E'+str(len(events)+1);rid=fid+':R'+str(len(events)+1)
        body=dict(synthetic_only=True,role='request_acknowledgement' if op.startswith('REQUEST_') else 'independent_record')
        if payload:body.update(payload)
        receipts[rid]=dict(evidence_id=rid,operation_id=op,context=deepcopy(ctx),depends_on=([latest] if latest else []) if deps is None else deps,payload=body)
        events.append(dict(event_id=eid,operation_id=op,evidence_id=rid));latest=rid;return rid
    add('REGISTER_INPUTS')
    if parts[0]=='HOLD':add('HOLD_'+parts[1]);add('ARCHIVE_RECORDS');add('CLEAN_STATION',payload={'disposition':'held_contained'} )
    elif parts[0]=='SOURCE':add('ARCHIVE_RECORDS',payload={'physical_demo_reenactment':False});add('CLEAN_STATION',payload={'disposition':'source_context_only'})
    elif parts[0] in ('MODEL','DESIGN'):
        add('VERIFY_QUALIFICATION',payload={'qualified_scope':'offline_metadata_only'});add('DECLARE_DESIGN')
        if parts[0]=='MODEL':
            op=next(o for o in BRANCHES[parts[1]]['operation_ids'] if o.startswith('REQUEST_'));add(op);add('VERIFY_MODEL_RECORD',payload={'solver_executed':False,'original_model_inputs':True})
        else:add('FREEZE_MODE_MAP');add('VERIFY_GEOMETRY',payload={'physical_geometry_validated':False});add('RELEASE_DESIGN')
        add('ARCHIVE_RECORDS');add('CLEAN_STATION',payload={'disposition':'metadata_closed'})
    else:
        b,entry,out=parts;add('VERIFY_QUALIFICATION',payload={'qualified_scope':'offline_synthetic_only'})
        if entry=='FULL':
            prep=['DECLARE_DESIGN','FREEZE_MODE_MAP','VERIFY_GEOMETRY','RELEASE_DESIGN','REQUEST_CUT','VERIFY_CUT']
            if b!='BASE_MATERIAL_TENSION':prep+=['REQUEST_FOLD','VERIFY_FOLD','REQUEST_STACK_BOND','VERIFY_STACK_BOND','VERIFY_CURE']
            for op in prep:add(op)
        add('RECEIVE_SAMPLE',payload={'preparation_credit':entry=='FULL','independent_ancestry':digest(['ancestry',fid])});add('INSPECT_SAMPLE',payload={'condition':'intact','virgin':True});add('TRANSFER_CARRIER')
        has_test=b not in ('FULL_FABRICATION','PROTOTYPE_RECONFIGURATION')
        if b not in ('FULL_FABRICATION','BASE_MATERIAL_TENSION'):
            for op in ['FREEZE_RECONFIGURATION_PLAN','REQUEST_RECONFIGURATION','VERIFY_CONFIGURATION']:add(op)
        if has_test:
            add('DOCK_TENSILE' if b=='BASE_MATERIAL_TENSION' else 'DOCK_COMPRESSION');add('VERIFY_MOUNT');add('VERIFY_INTERLOCK');add('VERIFY_CALIBRATION');add('FREEZE_TEST_PLAN',payload={'baseline_known_before_request':True,'cycle_count':10 if b=='CYCLIC_N4_A2' else 4 if b=='CYCLIC_N6_A3' else None})
            add('REQUEST_TENSION' if b=='BASE_MATERIAL_TENSION' else 'REQUEST_CYCLES' if b.startswith('CYCLIC_') else 'REQUEST_COMPRESSION')
            if b=='RUBBER_BAND_CONTROL':add('REQUEST_BAND_RELEASE',payload={'independent_preload_observed':True});add('VERIFY_BAND_RELEASE',payload={'band_removed':True})
            raw=raw_data(fid);root=add('ACQUIRE_RECORDS',payload={'raw':raw,'raw_hash':digest(raw),'acquisition_complete':out!='DATA_HOLD'})
            if out=='DATA_HOLD':analysis_end=add('HOLD_DATA')
            else:
                add('VALIDATE_RECORDS')
                if b.startswith('CYCLIC_'):res=cyclic(raw,raw['cycle_segments'],raw['baseline_peak_N'],10 if b=='CYCLIC_N4_A2' else 4);op='ANALYZE_CYCLES'
                elif b=='BASE_MATERIAL_TENSION':res=tensile(raw,[1,2,3],'MD','MD');op='ANALYZE_MATERIAL'
                elif b=='MIXED_MODES_N4':res=mixed_ratios(5,2,10,1);op='ANALYZE_MODE_CHANNELS'
                else:res=compression(raw,[1,2,3],4);op='ANALYZE_COMPRESSION'
                add(op,payload={'reduction':res});analysis_end=add('COMPARE_RESPONSES',payload={'fixture_is_one_bookkeeping_instance_not_complete_campaign':True})
        else:
            root=latest;analysis_end=add('HOLD_DATA') if out=='DATA_HOLD' else latest
        add('REQUEST_SAFE_OFF',deps=[root])
        if out=='ISOLATION_HOLD':add('HOLD_ISOLATION',payload={'safe_release_observed':False});disposition='held_contained'
        else:
            add('VERIFY_SAFE_OFF',payload={'safe_release_observed':True})
            if has_test:add('UNDOCK_SAMPLE')
            add('INSPECT_SAMPLE',payload={'condition':'damaged' if out=='DAMAGED' else 'intact','virgin':False if has_test else True})
            if out=='DAMAGED':add('QUARANTINE_SAMPLE')
            disposition='quarantined' if out=='DAMAGED' else 'stored'
        closure_end=latest;add('ARCHIVE_RECORDS',deps=list(dict.fromkeys([analysis_end,closure_end])))
        add('STORE_SAMPLE',payload={'disposition':disposition,'virgin_reusable':out=='GOOD' and b=='FULL_FABRICATION','preparation_credit':entry=='FULL' and out=='GOOD'})
        add('CLEAN_STATION',payload={'disposition':disposition})
    return deepcopy(dict(fixture_id=fid,context=ctx,events=events,receipts=receipts,registry_digest=digest(receipts)))
def evaluate(events,receipts,expected_fixture_id):
    expected=fixture(expected_fixture_id);require(type(events) is list and type(receipts) is dict,'actor events and independent registry')
    require(canonical(receipts)==canonical(expected['receipts']),'registry differs from evaluator-pinned evidence')
    require(len(events)==len(expected['events']),'missing/extra event');want={e['event_id']:e for e in expected['events']};seen=set();observed=set()
    for event in events:
        require(type(event) is dict and set(event)=={'event_id','operation_id','evidence_id'},'actor may submit IDs only')
        require(all(type(v) is str and v for v in event.values()),'nonempty IDs required')
        eid=event['event_id'];require(eid in want and eid not in seen,'unknown/duplicate occurrence');require(event==want[eid],'event/evidence binding mismatch')
        r=receipts[event['evidence_id']];require(set(r['depends_on'])<=observed,'dependency order violated');seen.add(eid);observed.add(event['evidence_id'])
    parts=expected_fixture_id.split(':');physical=parts[0] in PHYSICAL;mode=parts[-1];good=physical and mode=='GOOD';tested=physical and parts[0] not in ('FULL_FABRICATION','PROTOTYPE_RECONFIGURATION')
    return dict(contract_passed=True,synthetic_instance_complete=good,synthetic_preparation_lineage_checked=good and parts[1]=='FULL',synthetic_measurement_checked=good and tested,numerical_metadata_checked=parts[0]=='MODEL',whole_campaign_complete=False,physical_execution=False,numerical_solver_execution=False,scientific_reproduction=False,whole_paper_execution_complete=False,source_expected_outcome_used=False,virgin_sample_reusable=good and parts[0]=='FULL_FABRICATION')
