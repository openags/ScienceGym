"""Original offline synthetic record contract. No hardware, network or solver.

The evaluator selects a fixture and supplies its independently pinned registry.
Public fixtures are integrity test vectors, not production authentication.
"""
from copy import deepcopy
from decimal import Decimal,localcontext,DecimalException
import hashlib,json,math
class ContractError(ValueError):pass
def require(test,message):
    if not test:raise ContractError(message)
def number(value,name='number'):
    require(type(value) in (int,float),name+' must be numeric, not boolean')
    try:value=float(value)
    except (ValueError,OverflowError):raise ContractError(name+' outside finite range')
    require(math.isfinite(value),name+' must be finite');return value
def strict(value):
    if type(value) is dict:
        require(all(type(k) is str for k in value),'nonstring JSON key')
        for v in value.values():strict(v)
    elif type(value) is list:
        for v in value:strict(v)
    elif type(value) in (int,float):number(value)
    else:require(type(value) in (str,bool,type(None)),'non-JSON value')
def canonical(value):
    try:strict(value);return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    except (TypeError,ValueError,OverflowError,RecursionError) as exc:raise ContractError('noncanonical data') from exc
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def checked_result(value):strict(value);return value
def decimal_float(value,name='result'):
    try:result=float(value)
    except (ValueError,OverflowError):raise ContractError(name+' outside range')
    require(math.isfinite(result),name+' overflow');require(value==0 or result!=0,name+' underflow');return result
def ratio(numerator,*denominators):
    n=number(numerator);ds=[number(x) for x in denominators];require(all(x!=0 for x in ds),'zero denominator')
    try:
        with localcontext() as ctx:
            ctx.prec=2500;v=Decimal.from_float(n)
            for d in ds:v/=Decimal.from_float(d)
            return decimal_float(v,'ratio')
    except DecimalException as exc:raise ContractError('ratio unavailable') from exc
def vectors(time,displacement,force):
    require(all(type(x) is list for x in [time,displacement,force]),'arrays must be lists')
    require(len(time)==len(displacement)==len(force) and len(time)>=3,'array lengths')
    t=[number(x) for x in time];d=[number(x) for x in displacement];f=[number(x) for x in force]
    require(all(b>a for a,b in zip(t,t[1:])),'time must increase');return t,d,f
def geometry(area,height,relative_density,solid_density,solid_modulus):
    a,h,r,s,e=[number(x) for x in [area,height,relative_density,solid_density,solid_modulus]]
    require(a>0 and h>0 and 0<r<=1 and s>0 and e>0,'invalid geometry or material scale');return a,h,r,s,e
def integrate(x,y):
    require(type(x) is list and type(y) is list and len(x)==len(y) and len(x)>=2,'integration arrays')
    x=[number(v) for v in x];y=[number(v) for v in y]
    try:
        with localcontext() as ctx:
            ctx.prec=2500;xx=[Decimal.from_float(v) for v in x];yy=[Decimal.from_float(v) for v in y]
            return decimal_float(sum(((b-a)*(u+v)/2 for a,b,u,v in zip(xx,xx[1:],yy,yy[1:])),Decimal(0)),'integral')
    except DecimalException as exc:raise ContractError('integration unavailable') from exc
def reduce_tension(time,displacement,force,area,height,relative_density,solid_density,solid_modulus,fit_indices):
    _,d,f=vectors(time,displacement,force);a,h,r,s,e=geometry(area,height,relative_density,solid_density,solid_modulus)
    require(all(v>=0 for v in d) and all(v>=0 for v in f),'nonnegative tensile loading required')
    require(all(b>a for a,b in zip(d,d[1:])),'loading displacement must strictly increase')
    require(type(fit_indices) is list and len(fit_indices)>=2 and all(type(i) is int and 0<=i<len(d) for i in fit_indices),'fit indices')
    require(fit_indices==sorted(set(fit_indices)),'fit indices unique and increasing')
    strain=[ratio(x,h) for x in d];stress=[ratio(y,a) for y in f];x=[strain[i] for i in fit_indices];y=[stress[i] for i in fit_indices]
    try:
        with localcontext() as ctx:
            ctx.prec=2500;xx=[Decimal.from_float(v) for v in x];yy=[Decimal.from_float(v) for v in y]
            xm=sum(xx,Decimal(0))/len(xx);ym=sum(yy,Decimal(0))/len(yy)
            den=sum(((v-xm)**2 for v in xx),Decimal(0));num=sum(((v-xm)*(w-ym) for v,w in zip(xx,yy)),Decimal(0))
            require(den>0,'fit has no usable support');modulus=decimal_float(num/den,'modulus')
        work=integrate(strain,stress)
        return checked_result(dict(strain=strain,stretch=[number(1+v) for v in strain],stress_Pa=stress,fit_modulus_Pa=modulus,loading_work_J_m3=work,specific_loading_work_J_kg=ratio(work,r,s),modulus_per_density_Pa_m3_kg=ratio(modulus,r,s),relative_specific_modulus=ratio(modulus,r,e),source_figure_specific_modulus_m3_kg=ratio(modulus,r,s,e),support_strain=[strain[0],strain[-1]],fit_indices=fit_indices,energy_kind='monotonic_loading_work_not_hysteresis_loss'))
    except (OverflowError,ZeroDivisionError,ValueError,DecimalException) as exc:
        if isinstance(exc,ContractError):raise
        raise ContractError('reduction unavailable') from exc
def cycle_loss(time,displacement,force,area,height,cycles,closure_tolerance):
    _,d,f=vectors(time,displacement,force);a=number(area);h=number(height);tol=number(closure_tolerance)
    require(a>0 and h>0 and tol>=0,'invalid cycle geometry/tolerance');require(type(cycles) is list and bool(cycles),'explicit cycles required')
    result=[];previous=None
    for segment in cycles:
        require(type(segment) is list and len(segment)==3 and all(type(i) is int for i in segment),'cycle indices')
        start,turn,end=segment;require(0<=start<turn<end<len(d),'cycle order');require((previous is None and start==0) or start==previous,'cycles must tile data');previous=end
        delta=number(d[turn]-d[start]);require(delta!=0,'empty excursion');direction=1 if delta>0 else -1
        require(all(direction*(b-a)>=0 for a,b in zip(d[start:turn],d[start+1:turn+1])),'nonmonotonic loading limb')
        require(all(direction*(b-a)<=0 for a,b in zip(d[turn:end],d[turn+1:end+1])),'nonmonotonic unloading limb')
        residual=ratio(number(d[end]-d[start]),h);require(abs(residual)<=tol,'cycle not closed within tolerance')
        strain=[ratio(v,h) for v in d[start:end+1]];stress=[ratio(v,a) for v in f[start:end+1]]
        loss=integrate(strain+[strain[0]],stress+[stress[0]]);require(loss>=0,'negative loop work; no absolute value')
        result.append(dict(loss_J_m3=loss,residual_strain=residual,direction='tension' if direction>0 else 'compression',closure_segment_included=True))
    require(previous==len(d)-1,'unsegmented tail');require(result[0]['loss_J_m3']>0,'positive baseline required');baseline=result[0]['loss_J_m3']
    for row in result:row['relative_to_first']=ratio(row['loss_J_m3'],baseline)
    return checked_result(result)
MODES=('OK','DAMAGED','DATA_HOLD','ISOLATION_HOLD')
PHYSICAL_BRANCHES=('TENSION_BCC','TENSION_CUBIC','TENSION_OCTAHEDRON','TENSION_DIAMOND','CYCLIC_BCC_TENSION','CYCLIC_BCC_COMPRESSION','CYCLIC_OCTAHEDRON_COMPRESSION','GRADED_RADIUS','GRADED_TURNS')
MODEL_OPS={'LINEAR_HOMOGENIZATION':'REQUEST_HOMOGENIZATION','MATERIAL_CHARACTERIZATION':'REQUEST_MATERIAL_MODEL','BEAM_CONTINUUM_COMPARISON':'REQUEST_BEAM_CONTINUUM','NONLINEAR_BEAM_MODEL':'REQUEST_NONLINEAR_MODEL','FAILURE_VARIABILITY':'REQUEST_FAILURE_VARIABILITY','CURVATURE_CONTACT':'REQUEST_CURVATURE_CONTACT','PATTERNED_DEFORMATION_MODEL':'REQUEST_PATTERN_MODELS','PATTERNED_FAILURE_MODEL':'REQUEST_PATTERN_MODELS'}
FIXTURE_IDS=tuple(f'{b}:{r}:{m}' for b in PHYSICAL_BRANCHES for r in ('FULL','PREPARED') for m in MODES)+tuple(f'PROGRAMMED_FAILURE_EXPERIMENT:{r}:{m}' for r in ('PLASMA_FIRST','COAT_FIRST','PREPARED') for m in MODES)+tuple('MODEL:'+b for b in MODEL_OPS)+('HOLD:QUALIFICATION','HOLD:TETRAKAIDECAHEDRON','HOLD:CUBIC_CONNECTIVITY','HOLD:CALIBRATION')
def context_for(fid):
    require(type(fid) is str and fid in FIXTURE_IDS,'unknown fixture');parts=fid.split(':');model=parts[0]=='MODEL';hold=parts[0]=='HOLD';b=parts[1] if model or hold else parts[0];route='NONE' if hold else 'MODEL' if model else parts[1]
    return dict(episode_id=fid,attempt_id=fid+':ATTEMPT1',branch_id=b,preparation_route=route,design_hash=digest(['original_synthetic_design',fid]),material_lot=fid+':LOT',sample_id=fid+':SAMPLE',carrier_id=fid+':CARRIER',mount_revision=fid+':M1',calibration_revision=fid+':CAL1',control_revision=fid+':CTRL1',analysis_revision=fid+':AN1',qualification_revision=fid+':QUAL1',axis_map_revision=fid+':AXIS1',process_order_revision=fid+':ORDER1')
def sequence_for(fid):
    context_for(fid)
    if fid.startswith('HOLD:'):
        k=fid.split(':')[1];h='HOLD_QUALIFICATION' if k=='QUALIFICATION' else 'HOLD_CALIBRATION' if k=='CALIBRATION' else 'HOLD_GEOMETRY';return ['REGISTER_INPUTS',h,'ARCHIVE','CLEAN_STORE']
    if fid.startswith('MODEL:'):return ['REGISTER_INPUTS','VERIFY_QUALIFICATION','DECLARE_DESIGN','FREEZE_GRAPH',MODEL_OPS[fid.split(':')[1]],'COMPARE_RESPONSE','ARCHIVE','CLEAN_STORE']
    branch,route,mode=fid.split(':');seq=['REGISTER_INPUTS','VERIFY_QUALIFICATION']
    if route!='PREPARED':
        seq+=['DECLARE_DESIGN','FREEZE_GRAPH','VERIFY_FABRICABILITY','RELEASE_DESIGN','REQUEST_PRINT','VERIFY_PRINT','REQUEST_DEVELOP_RINSE','VERIFY_DEVELOP_RINSE','REQUEST_CPD','VERIFY_CPD'];coat=['REQUEST_COATING','VERIFY_COATING'];plasma=['REQUEST_SUPPORT_REMOVAL','VERIFY_SUPPORT_REMOVAL'];seq+=plasma+coat if route=='PLASMA_FIRST' else coat+plasma if route=='COAT_FIRST' else coat
    seq+=['RECEIVE_SAMPLE','INSPECT_SAMPLE','DOCK_SAMPLE','VERIFY_INTERLOCK','VERIFY_MOUNT','VERIFY_CALIBRATION','FREEZE_TEST_PLAN',('REQUEST_CYCLIC' if branch.startswith('CYCLIC_') else 'REQUEST_TENSION'),'ACQUIRE_TEST_DATA']
    seq+=['HOLD_DATA'] if mode=='DATA_HOLD' else ['VALIDATE_DATA',('ANALYZE_CYCLES' if branch.startswith('CYCLIC_') else 'ANALYZE_TENSION'),'COMPARE_RESPONSE'];seq+=['REQUEST_SAFE_OFF']
    if mode=='ISOLATION_HOLD':seq+=['HOLD_ISOLATION','ARCHIVE','CLEAN_STORE']
    else:
        seq+=['VERIFY_SAFE_OFF','UNDOCK_SAMPLE','INSPECT_SAMPLE']
        if mode=='DAMAGED':seq+=['QUARANTINE']
        seq+=['ARCHIVE','CLEAN_STORE']
    return seq
def synthetic_data(fid):
    branch=fid.split(':')[0];v=(sum(fid.encode())%7)+1
    if branch.startswith('CYCLIC_'):
        sign=-1 if branch.endswith('COMPRESSION') else 1;raw=dict(time_s=[0,1,2,3,4],displacement_m=[sign*x for x in [0,1e-6,2e-6,1e-6,0]],force_N=[sign*v*x for x in [0,2e-6,3e-6,.7e-6,0]],cycles=[[0,2,4]],closure_tolerance=0.0)
    else:raw=dict(time_s=[0,1,2,3],displacement_m=[0,1e-6,2e-6,3e-6],force_N=[0,v*1e-6,v*1.7e-6,v*2.0e-6],fit_indices=[0,1,2])
    raw.update(nominal_area_m2=4e-9,gauge_height_m=1e-4,relative_density=.02,constituent_density_kg_m3=1200.0,constituent_modulus_Pa=1e9,units={'force':'N','displacement':'m','time':'s','area':'m2','height':'m'},image_ids=[fid+':IMAGE'+str(i) for i in range(len(raw['time_s']))],timebase_revision=fid+':CLOCK1',synthetic_only=True);return raw
def analysis_for(fid,data):
    if fid.split(':')[0].startswith('CYCLIC_'):return cycle_loss(data['time_s'],data['displacement_m'],data['force_N'],data['nominal_area_m2'],data['gauge_height_m'],data['cycles'],data['closure_tolerance'])
    return reduce_tension(data['time_s'],data['displacement_m'],data['force_N'],data['nominal_area_m2'],data['gauge_height_m'],data['relative_density'],data['constituent_density_kg_m3'],data['constituent_modulus_Pa'],data['fit_indices'])
def fixture(fid):
    ctx=context_for(fid);seq=sequence_for(fid);receipts={};events=[];previous=None;isphysical=not fid.startswith(('HOLD:','MODEL:'));mode=fid.split(':')[-1];data=synthetic_data(fid) if isphysical else None
    for i,op in enumerate(seq):
        rid=fid+':R'+str(i+1);payload={'synthetic_only':True,'role':'request_acknowledgement' if op.startswith('REQUEST_') else 'independent_record','stage_revision':fid+':STAGE'+str(i+1),'upstream_receipt_id':previous}
        if op=='VERIFY_QUALIFICATION':payload['qualified_scope']='offline_symbolic_fixture_only'
        if op=='FREEZE_GRAPH':payload.update(explicit_connectivity_revision=fid+':CONNECT1',independent_synthetic_connectivity_review=True,paper_exact_geometry=False)
        if op=='VERIFY_FABRICABILITY':payload.update(cad_release=fid+':CAD1',external_acceptance_revision=fid+':LIMIT1',physical_readiness=False)
        if op in ('REQUEST_SUPPORT_REMOVAL','VERIFY_SUPPORT_REMOVAL','REQUEST_COATING','VERIFY_COATING'):payload.update(external_order_card=ctx['process_order_revision'],source_plasma_coating_order='unspecified')
        if op=='RECEIVE_SAMPLE':payload.update(prepared_ancestry=digest(['independent_upstream_lineage',fid]),preparation_credit=ctx['preparation_route']!='PREPARED')
        if op=='ACQUIRE_TEST_DATA':payload.update(raw=data,raw_hash=digest(data),acquisition_complete=mode!='DATA_HOLD')
        if op in ('ANALYZE_TENSION','ANALYZE_CYCLES'):payload['reduction']=analysis_for(fid,data)
        if op=='COMPARE_RESPONSE':payload.update(measurement_kind='external_model_metadata_only' if fid.startswith('MODEL:') else 'synthetic_measurement_only',source_expected_outcome_used=False,physical_or_solver_execution=False,paper_exact_model=False)
        if op=='VERIFY_SAFE_OFF':payload['safe_release_observed']=True
        if op=='HOLD_ISOLATION':payload['safe_release_observed']=False
        if op=='INSPECT_SAMPLE':payload['condition']='damaged' if mode=='DAMAGED' and 'UNDOCK_SAMPLE' in seq[:i] else 'intact'
        if op=='CLEAN_STORE':payload.update(disposition='contained' if fid.startswith('HOLD:') or mode=='ISOLATION_HOLD' else 'quarantined' if mode=='DAMAGED' else 'stored',reusable=mode=='OK' and isphysical)
        receipts[rid]=dict(evidence_id=rid,operation_id=op,context=ctx,payload=payload);events.append(dict(event_id=fid+':E'+str(i+1),operation_id=op,evidence_id=rid));previous=rid
    return deepcopy(dict(fixture_id=fid,context=ctx,events=events,receipts=receipts,registry_digest=digest(receipts)))
def evaluate(events,receipts,expected_fixture_id):
    expected=fixture(expected_fixture_id);require(type(events) is list,'events list required');require(type(receipts) is dict,'independent registry required');canonical(events);canonical(receipts)
    require(canonical(receipts)==canonical(expected['receipts']),'registry differs from trusted pinned fixture');require(len(events)==len(expected['events']),'missing/extra event');seen=set()
    for actual,want in zip(events,expected['events']):
        require(type(actual) is dict and set(actual)=={'event_id','operation_id','evidence_id'},'actor event fields');require(all(type(x) is str and bool(x) for x in actual.values()),'actor IDs must be strings');require(actual['event_id'] not in seen,'duplicate event');seen.add(actual['event_id']);require(actual==want,'event order/operation/evidence mismatch')
    fid=expected_fixture_id;mode=fid.split(':')[-1];hold=fid.startswith('HOLD:');model=fid.startswith('MODEL:');terminal='HELD_CONTAINED' if hold or mode=='ISOLATION_HOLD' else 'QUARANTINED_SYNTHETIC' if mode=='DAMAGED' else 'CLOSED_SYNTHETIC';complete=not hold and not model and mode in ('OK','DAMAGED')
    return dict(contract_passed=True,fixture_id=fid,terminal_state=terminal,synthetic_measurement_complete=complete,synthetic_preparation_lineage_checked=complete and expected['context']['preparation_route']!='PREPARED',numerical_metadata_contract_checked=model,physical_execution=False,numerical_solver_execution=False,scientific_reproduction=False,whole_paper_execution_complete=False,sample_reusable=complete and mode=='OK',source_expected_outcome_used=False)
