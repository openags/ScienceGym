"""Original offline record verifier. No device access, image segmentation or physics.

Only an independently provided, fixture-pinned bundle can supply observations.
These public fixtures are NOT authentication and are NOT a production controller.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
BRANCHES = ('PHYSICAL_ORTHOGONAL', 'PHYSICAL_ANTIPARALLEL', 'DIRECTION_HOLD')
SCENARIOS = ('valid', 'wrong_way', 'short_input', 'occluded_after', 'base_slip', 'damage')
CONFLICTS = ('C_DIRECTION_CROSSREF','C_MOVIE_POINTERS','C_PHYSICAL_RESULTS_POINTER','C_FORCE_PANEL_POINTER')
CARDS = ('U_DIRECTION','U_FIXTURE','U_CALIPER','U_CAMERA','U_SEGMENTATION','U_RATE','U_ANGULAR_N','U_CLEANUP')
PREFIX = ['VERIFY_SPECIMEN','VERIFY_CARDS','RESOLVE_DIRECTION','DOCK_SPECIMEN','FIX_BASE','VERIFY_BASE','CALIBRATE_IMAGE','CAPTURE_BEFORE','REQUEST_INPUT','VERIFY_INPUT']
SUFFIX = ['RELEASE_INPUT','VERIFY_UNLOADED','UNFIX_BASE','RETRIEVE_SPECIMEN','INSPECT_SPECIMEN','ARCHIVE','CLEAN_STORE']
ROLES = ('human_design','machine_design')
GROUPS = {'input':['I1','I2'],'output':['O1','O2'],'base':['B1','B2']}
VECTORS = {'PHYSICAL_ORTHOGONAL':([0.0,-1.0],[-1.0,0.0]),'PHYSICAL_ANTIPARALLEL':([0.0,-1.0],[0.0,1.0])}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def strict_equal(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,dict): return set(a)==set(b) and all(strict_equal(a[k],b[k]) for k in a)
    if isinstance(a,list): return len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
    if isinstance(a,float) and not math.isfinite(a): return False
    return a==b


def finite_number(x):
    return type(x) in (int,float) and math.isfinite(x)


def mean_delta(before,after,ids,matrix):
    """Map mean matched pixel deltas into an explicitly calibrated plane."""
    if type(ids) is not list or not ids or len(set(ids))!=len(ids): raise ValueError('node group')
    if len(matrix)!=2 or any(len(r)!=2 for r in matrix): raise ValueError('matrix shape')
    if any(not finite_number(x) for r in matrix for x in r): raise ValueError('matrix finite')
    determinant=matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0]
    if abs(determinant)<1e-12: raise ValueError('singular calibration')
    deltas=[]
    for key in ids:
        p,q=before[key],after[key]
        if type(p) is not list or type(q) is not list or len(p)!=2 or len(q)!=2:raise ValueError('node coordinate')
        if any(not finite_number(x) for x in p+q): raise ValueError('node finite')
        d=[q[k]-p[k] for k in (0,1)]
        deltas.append([sum(row[k]*d[k] for k in (0,1)) for row in matrix])
    return [sum(d[k] for d in deltas)/len(deltas) for k in (0,1)]


def project_ratio(input_delta,output_delta,t_in,t_out):
    for vector in (input_delta,output_delta,t_in,t_out):
        if type(vector) is not list or len(vector)!=2 or not all(finite_number(x) for x in vector):raise ValueError('finite two-vector required')
    for t in (t_in,t_out):
        if not math.isclose(sum(x*x for x in t),1.0,rel_tol=0,abs_tol=1e-12):raise ValueError('direction must be unit vector')
    denominator=sum(x*y for x,y in zip(input_delta,t_in))
    if denominator<=1e-12:raise ValueError('input projection must be positive')
    return sum(x*y for x,y in zip(output_delta,t_out))/denominator


def phases(scenario):
    if scenario in ('short_input','base_slip'):return PREFIX+['QUARANTINE']+SUFFIX
    if scenario=='occluded_after':return PREFIX+['CAPTURE_AFTER','QUARANTINE']+SUFFIX
    tail=SUFFIX[:]
    if scenario=='damage':tail.insert(tail.index('ARCHIVE'),'QUARANTINE')
    return PREFIX+['CAPTURE_AFTER','MEASURE_NODES','COMPUTE_EFFICIENCY']+tail


def schedule(branch,scenario):
    if branch=='DIRECTION_HOLD': return [(None,o) for o in ['HOLD_DIRECTION','ARCHIVE','CLEAN_STORE']]
    return [(role,o) for role in ROLES for o in phases(scenario)]


def binding(ep,branch,role):
    return dict(episode_id=ep,attempt_id=ep+'_'+str(role)+'_attempt_1',specimen_id=ep+'_'+str(role),specimen_role=role,branch_id=branch,topology_hash=digest(['authored topology identity',branch,role]),material_lot='synthetic_TPU_lot',mount_revision=ep+'_'+str(role)+'_mount_1',node_map_id=ep+'_'+str(role)+'_nodes_1',calibration_id=ep+'_'+str(role)+'_calibration_1',camera_pose_id='synthetic_camera_pose_1',direction_card_id=branch+'_direction_fixture',qualification_revision='synthetic_only_v1')


def calibration(ep,branch,role):
    return dict(id=binding(ep,branch,role)['calibration_id'],matrix_mm_per_pixel=[[0.1,0.0],[0.0,-0.1]],plane='synthetic specimen plane x-right y-up',pixel_axes='x-right y-down',registration_id=ep+'_'+role+'_registration_1',node_groups=deepcopy(GROUPS),input_target_mm=5.0,input_tolerance_mm=0.1,transverse_tolerance_mm=0.05,base_drift_tolerance_mm=0.05,uncertainty_mm=0.01,uncertainty_origin='authored_fixture_bound_not_instrument_specification',n=2,source_physical_n=None,t_in=VECTORS[branch][0],t_out=VECTORS[branch][1],qualified_for_real_use=False)


def frame(ep,branch,role,which,scenario,variant):
    nodes={'I1':[100.0,100.0],'I2':[120.0,100.0],'O1':[300.0,100.0],'O2':[320.0,100.0],'B1':[100.0,300.0],'B2':[300.0,300.0]}
    if which=='after':
        for k in GROUPS['input']:nodes[k][1]+=50.0
        # Authored values deliberately differ from reported paper outcomes.
        magnitude=(2.0 if role=='human_design' else 3.0)+variant*0.25
        sign=-1.0 if scenario=='wrong_way' else 1.0
        direction=VECTORS[branch][1]
        for ix,k in enumerate(GROUPS['output']):
            nodes[k][0]+=direction[0]*magnitude*sign/0.1
            nodes[k][1]-=direction[1]*magnitude*sign/0.1
            # An off-axis component ensures a norm ratio is not interchangeable.
            if branch=='PHYSICAL_ORTHOGONAL':nodes[k][1]+=(ix+1)*2.0
            else:nodes[k][0]+=(ix+1)*2.0
    result=dict(id=ep+'_'+role+'_'+which,kind='synthetic_coordinate_frame_not_image',binding=binding(ep,branch,role),timestamp_tick=100 if which=='before' else 200,nodes=nodes,registered=True,all_nodes_visible=not (scenario=='occluded_after' and which=='after'),base_fixed=True,output_free=True,camera_pose_current=True,unloaded=which=='before',input_verified=which=='after',raw_payload_kind='original_synthetic_node_coordinates')
    result['raw_record_hash']=digest(result)
    return result


def fixture(branch='DIRECTION_HOLD',scenario='valid',variant=0,episode_id='synthetic_episode_001'):
    if branch not in BRANCHES or scenario not in SCENARIOS: raise ValueError('unsupported branch or scenario')
    if type(variant) is not int or variant not in range(4):raise ValueError('fixture variant')
    if type(episode_id) is not str or not episode_id.startswith('synthetic_episode_') or len(episode_id)>80:raise ValueError('episode identity')
    if branch=='DIRECTION_HOLD' and (scenario!='valid' or variant!=0):raise ValueError('hold configuration')
    frames={}; calibrations={}
    if branch!='DIRECTION_HOLD':
        for role in ROLES:
            c=calibration(episode_id,branch,role);calibrations[c['id']]=c
            for which in ['before']+([] if scenario in ('short_input','base_slip') else ['after']):
                f=frame(episode_id,branch,role,which,scenario,variant);frames[f['id']]=f
    receipts={};events=[]
    for n,(role,op) in enumerate(schedule(branch,scenario),1):
        eid='E%03d'%n; rid=episode_id+'_'+eid+'_receipt'
        b=binding(episode_id,branch,role)
        details={'observed':True,'scope':'synthetic_fixture_only'}
        if op=='VERIFY_SPECIMEN':details.update(specimen_role=role,material='NinjaFlex TPU declared by fixture',identity_observed=True,condition='intact')
        elif op=='VERIFY_CARDS':details.update(card_ids=list(CARDS),authority='fixture_author',current=True,production_authority=False)
        elif op=='RESOLVE_DIRECTION':details.update(t_in=VECTORS[branch][0],t_out=VECTORS[branch][1],interpretation='explicit_specimen_frame_fixture_only',source_conflicts_resolved=False,source_conflicts_preserved=list(CONFLICTS))
        elif op in ('FIX_BASE','REQUEST_INPUT','RELEASE_INPUT'):details={'acknowledged':True,'state_observed':False,'scope':'synthetic_fixture_only'}
        elif op=='VERIFY_BASE':details.update(base_fixed=True,output_free=True,independent_observation=True)
        elif op=='CALIBRATE_IMAGE':details.update(calibration_id=b['calibration_id'],current=True)
        elif op in ('CAPTURE_BEFORE','CAPTURE_AFTER'):details.update(frame_id=episode_id+'_'+role+('_before' if op=='CAPTURE_BEFORE' else '_after'),quality_pass=not (scenario=='occluded_after' and op=='CAPTURE_AFTER'))
        elif op=='VERIFY_INPUT':details.update(independent_observation=True,caliper_id='synthetic_caliper',calibration_current=True,measured_input_vector_mm=[0.0,-4.0 if scenario=='short_input' else -5.0],base_fixed=scenario!='base_slip',output_free=True,input_pass=scenario not in ('short_input','base_slip'))
        elif op=='MEASURE_NODES':details.update(before_frame_id=episode_id+'_'+role+'_before',after_frame_id=episode_id+'_'+role+'_after',segmentation='synthetic_coordinates_only',node_map_id=b['node_map_id'])
        elif op=='COMPUTE_EFFICIENCY':
            c=calibrations[b['calibration_id']];bf=frames[episode_id+'_'+role+'_before'];af=frames[episode_id+'_'+role+'_after']
            di=mean_delta(bf['nodes'],af['nodes'],GROUPS['input'],c['matrix_mm_per_pixel']);do=mean_delta(bf['nodes'],af['nodes'],GROUPS['output'],c['matrix_mm_per_pixel'])
            details.update(n=2,metric='signed_projected_displacement_ratio',value=project_ratio(di,do,c['t_in'],c['t_out']),source_outcome_used=False)
        elif op=='VERIFY_UNLOADED':details.update(independent_observation=True,unloaded=True,supported=True,recovery_claim='no_source_elastic_restoration_claim')
        elif op=='UNFIX_BASE':details.update(supported=True,base_released=True)
        elif op=='RETRIEVE_SPECIMEN':details.update(carrier_id=episode_id+'_'+role+'_carrier',custody_complete=True)
        elif op=='INSPECT_SPECIMEN':details.update(condition='damaged' if scenario=='damage' else 'intact',reuse_permitted=scenario!='damage')
        elif op=='QUARANTINE':details.update(reason=scenario,retained=True,reuse_permitted=False)
        elif op=='ARCHIVE':details.update(raw_records_preserved=True,failed_attempts_preserved=True,source_fabrication_credited=False)
        elif op=='CLEAN_STORE':details.update(cleanup_observed=True,custody='safe_hold_no_specimen_moved' if role is None else 'quarantined_storage' if scenario in ('short_input','base_slip','occluded_after','damage') else 'retained_storage')
        elif op=='HOLD_DIRECTION':details.update(direction_state='unresolved',physical_request_issued=False,source_conflicts_resolved=False)
        receipt=dict(id=rid,event_id=eid,operation_id=op,binding=b,sequence=n,origin='independent_synthetic_fixture_registry',details=details)
        receipt['raw_record_hash']=digest(receipt);receipts[rid]=receipt
        events.append(dict(event_id=eid,operation_id=op,specimen_id=b['specimen_id'],evidence_id=rid))
    result=dict(schema_version='actuator_metrology_fixture.v1',episode_id=episode_id,branch_id=branch,scenario=scenario,variant=variant,mode='offline_synthetic_contract_only',production_authority=False,physical_execution=False,numerical_reproduction=False,whole_paper_complete=False,source_conflicts_preserved=list(CONFLICTS),source_conflicts_resolved=False,calibrations=calibrations,frames=frames,receipts=receipts,terminal='safe_direction_hold' if branch=='DIRECTION_HOLD' else 'safe_quarantined' if scenario in ('short_input','base_slip','occluded_after','damage') else 'synthetic_measurement_complete')
    # Namespace every identity by the complete evaluator-owned fixture selection.
    # The human-readable episode remains a separate field; reused episode labels
    # cannot make a trace from a different branch/scenario/variant replayable.
    instance_id='fixture_'+digest([episode_id,branch,scenario,variant])
    def qualify(value,key=None):
        if type(value) is dict:
            out={qualify(k):qualify(v,k) for k,v in value.items()}
            if key=='binding':out['fixture_instance_id']=instance_id
            return out
        if type(value) is list:return [qualify(v) for v in value]
        if type(value) is str:
            if key=='episode_id':return value
            if key=='event_id':return instance_id+'_'+value
            if value.startswith(episode_id):return instance_id+value[len(episode_id):]
        return value
    result=qualify(result);events=qualify(events)
    result['fixture_instance_id']=instance_id
    for record in list(result['frames'].values())+list(result['receipts'].values()):
        record['raw_record_hash']=digest({k:v for k,v in record.items() if k!='raw_record_hash'})
    return result,events


def _validate(bundle,events):
    errors=[];values=[]
    def check(ok,message):
        if not ok: errors.append(message)
    if type(bundle) is not dict or type(events) is not list:return ['outer schema'],values
    expected,expected_events=fixture(bundle.get('branch_id'),bundle.get('scenario'),bundle.get('variant'),bundle.get('episode_id'))
    check(strict_equal(bundle,expected),'evaluator fixture altered, mistyped, stale or unqualified')
    check(len(events)==len(expected_events),'missing or extra operations')
    branch=bundle['branch_id'];scenario=bundle['scenario'];ep=bundle['episode_id']
    receipts=bundle['receipts'];frames=bundle['frames'];calibrations=bundle['calibrations'];seen=set();seen_frames=set();states={}
    for n,event in enumerate(events):
        if type(event) is not dict or set(event)!={'event_id','operation_id','specimen_id','evidence_id'}:
            errors.append('actor measurement or schema injection');continue
        check(n<len(expected_events) and strict_equal(event,expected_events[n]),'event order, identity or replay')
        eid=event['event_id'];rid=event['evidence_id'];op=event['operation_id'];specimen=event['specimen_id']
        if any(type(x) is not str for x in [eid,rid,op,specimen]):errors.append('actor ID type');continue
        check(eid not in seen,'event replay');seen.add(eid)
        o=receipts.get(rid)
        if type(o) is not dict:errors.append('missing independent receipt');continue
        check(o['event_id']==eid and o['operation_id']==op and o['binding']['specimen_id']==specimen,'receipt actor binding')
        check(o['raw_record_hash']==digest({k:v for k,v in o.items() if k!='raw_record_hash'}),'receipt content hash')
        role=o['binding']['specimen_role'];d=o['details'];s=states.setdefault(specimen,dict(docked=False,fixed=False,before=None,input=False,after=None,measured=False,released=False,unloaded=False,retrieved=False,inspected=False,archive=False,closed=False,quarantine=False,calibration=None))
        if op=='DOCK_SPECIMEN':s['docked']=True
        elif op=='VERIFY_BASE':check(s['docked'] and d['base_fixed'] is True and d['output_free'] is True,'base/output independent state');s['fixed']=True
        elif op=='CALIBRATE_IMAGE':check(s['fixed'],'calibration before fixed base');s['calibration']=d['calibration_id']
        elif op in ('CAPTURE_BEFORE','CAPTURE_AFTER'):
            f=frames.get(d['frame_id']);check(f is not None,'frame missing')
            if f is None:continue
            check(strict_equal(f['binding'],o['binding']),'frame lineage mismatch')
            check(f['raw_record_hash']==digest({k:v for k,v in f.items() if k!='raw_record_hash'}),'frame hash')
            check(f['id'] not in seen_frames,'frame replay');seen_frames.add(f['id'])
            check(s['fixed'] and s['calibration']==f['binding']['calibration_id'] and f['camera_pose_current'] is True,'stale camera/mount/calibration')
            check(f['base_fixed'] is True and f['output_free'] is True,'base moved or output constrained')
            if op=='CAPTURE_BEFORE':check(f['unloaded'] is True and f['all_nodes_visible'] is True and not s['input'],'invalid baseline');s['before']=f
            else:
                check(s['input'] and s['before'] is not None,'after frame before verified input')
                check(f['timestamp_tick']>s['before']['timestamp_tick'],'stale capture timestamp')
                if d['quality_pass'] is True:check(f['all_nodes_visible'] is True,'occluded successful frame');s['after']=f
                else:check(scenario=='occluded_after','unexpected quality failure')
        elif op=='VERIFY_INPUT':
            check(s['before'] is not None and s['fixed'],'input before baseline/base')
            c=calibrations[s['calibration']];v=d['measured_input_vector_mm'];projection=sum(x*y for x,y in zip(v,c['t_in']));transverse=abs(v[0]*c['t_in'][1]-v[1]*c['t_in'][0])
            passed=abs(projection-c['input_target_mm'])<=c['input_tolerance_mm'] and transverse<=c['transverse_tolerance_mm'] and d['base_fixed'] is True and d['output_free'] is True
            check(passed is d['input_pass'],'false caliper/base state');s['input']=passed
        elif op=='MEASURE_NODES':
            check(s['before'] is not None and s['after'] is not None and s['input'],'measurement without pair/input')
            c=calibrations[s['calibration']];bf=s['before'];af=s['after']
            check(set(bf['nodes'])==set(af['nodes'])==set(sum(GROUPS.values(),[])),'node identity/cardinality')
            s['di']=mean_delta(bf['nodes'],af['nodes'],c['node_groups']['input'],c['matrix_mm_per_pixel'])
            s['do']=mean_delta(bf['nodes'],af['nodes'],c['node_groups']['output'],c['matrix_mm_per_pixel'])
            db=mean_delta(bf['nodes'],af['nodes'],c['node_groups']['base'],c['matrix_mm_per_pixel'])
            check(math.hypot(*db)<=c['base_drift_tolerance_mm'],'base image drift')
            check(abs(sum(x*y for x,y in zip(s['di'],c['t_in']))-c['input_target_mm'])<=c['input_tolerance_mm'],'image input conflicts with calibrated observation')
            s['measured']=True
        elif op=='COMPUTE_EFFICIENCY':
            check(s['measured'] and not s['quarantine'],'analysis without valid measurements')
            c=calibrations[s['calibration']];ratio=project_ratio(s['di'],s['do'],c['t_in'],c['t_out'])
            check(d['n']==2 and d['source_outcome_used'] is False and type(d['value']) is float and math.isclose(d['value'],ratio,abs_tol=1e-12),'signed efficiency mismatch or source oracle')
            values.append({'specimen_role':role,'signed_displacement_ratio':ratio,'synthetic_only':True})
        elif op=='RELEASE_INPUT':s['released']=True;s['input']=False
        elif op=='VERIFY_UNLOADED':check(s['released'] and d['unloaded'] is True and d['supported'] is True,'release acknowledgement substituted for unloaded state');s['unloaded']=True
        elif op=='UNFIX_BASE':check(s['unloaded'] and s['fixed'] and d['supported'] is True,'unsafe base release');s['fixed']=False
        elif op=='RETRIEVE_SPECIMEN':check(not s['fixed'] and s['unloaded'] and d['custody_complete'] is True,'unsafe retrieval');s['docked']=False;s['retrieved']=True
        elif op=='INSPECT_SPECIMEN':check(s['retrieved'],'inspection before retrieval');s['inspected']=True
        elif op=='QUARANTINE':check(d['reuse_permitted'] is False,'quarantine reuse');s['quarantine']=True
        elif op=='ARCHIVE':check(d['raw_records_preserved'] is True and d['failed_attempts_preserved'] is True,'archive missing failure/raw records');s['archive']=True
        elif op=='CLEAN_STORE':
            check(s['archive'] and d['cleanup_observed'] is True,'unobserved cleanup/archive')
            if branch!='DIRECTION_HOLD':check(s['unloaded'] and s['retrieved'] and s['inspected'] and not s['fixed'] and not s['docked'],'unsafe lifecycle closure')
            s['closed']=True
    check(all(s['closed'] for s in states.values()) and len(states)==(1 if branch=='DIRECTION_HOLD' else 2),'incomplete matched controls or closure')
    if branch=='DIRECTION_HOLD':check(not values and not frames and not calibrations,'hold emitted acquisition')
    if scenario in ('short_input','base_slip','occluded_after'):check(not values and all(s['quarantine'] for s in states.values()),'failed metrology produced efficiency or escaped quarantine')
    return sorted(set(errors)),values


def validate(bundle,events):
    try:
        errors,values=_validate(bundle,events)
        return dict(accepted=not errors,errors=errors,synthetic_measurements=values if not errors else [],scope='offline_contract_only',physical_validated=False,whole_paper_complete=False)
    except (ValueError,TypeError,KeyError,AttributeError,IndexError,OverflowError,RecursionError):
        return dict(accepted=False,errors=['malformed contract fails closed'],synthetic_measurements=[],scope='offline_contract_only',physical_validated=False,whole_paper_complete=False)
