"""Inspectable occurrence expansion and symbolic invariants, NOT a robot runtime.

The compiler emits obligations and expected states, never observation receipts.
The included work order is explicitly a software test fixture. Its invented
setpoints, repeats and dates are not qualified operating inputs.
"""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/(name+'.json')).read_text())

class PlanError(ValueError):pass

def require(condition,message):
    if not condition:raise PlanError(message)

def actor_projection(episode):
    allowed=read('agent_visible')['allowed_input_fields']
    # Filter named trusted fields recursively. Qualified cards still require a
    # trusted origin; this is not a sanitizer for arbitrary free-text payloads.
    forbidden=set(read('agent_visible')['excluded_fields'])
    def clean(v):
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in forbidden}
        if isinstance(v,list):return [clean(x) for x in v]
        return copy.deepcopy(v)
    return {k:clean(episode[k]) for k in allowed if k in episode}

def scientific_metrics(voltage,current,diameter_m,gti,dni,solar_frame):
    require(all(math.isfinite(x) for x in (voltage,current,diameter_m,gti,dni)),'nonfinite measurement')
    require(diameter_m>0,'nonpositive emitter diameter')
    require(solar_frame=='sun_normal','GTI-DNI needs common sun-normal geometry')
    return {'heater_power_W_m2':voltage*current/(math.pi*(diameter_m/2)**2),
            'diffuse_W_m2':gti-dni}

def validate_state(s,acquisition=False):
    require(s['supported'],'payload is unsupported')
    require(s['film_layers'] in (0,2),'cover must have two distinct layers')
    if acquisition:
        require(s['location']=='WS_OUTDOOR','outdoor acquisition at wrong station')
        require(s['qc_revision']==s['assembly_revision'],'stale assembly inspection')
        require(s['film_layers']==2,'missing cover')
        require(s['probe_calibration'] is not None,'missing probe calibration')

def initial_states():return {x['id']:copy.deepcopy(x) for x in read('initial_state')['objects']}

def witness_state(wid,parents):
    return {'id':wid,'location':'WS_STOCK','supported':True,'configuration':'witness_'+wid[2:],
            'assembly_revision':0,'qc_revision':None,'film_layers':0,'heater_output':False,
            'probe_calibration':None,'parent_material_lots':parents,'specimen_ready':False}

def transition(states,event):
    """Advance expected symbolic state only. Evidence validation is not implemented."""
    oid=event['operation_id'];payloads=event.get('payload_ids',[])
    for pid in payloads:
        require(pid in states,'unknown payload '+pid)
        s=states[pid];validate_state(s)
        if oid=='MOVE':
            require(s['location']==event['origin'],'transfer origin mismatch')
            require(not s['heater_output'],'cannot move an energized assembly')
            require(event['destination']!=event['origin'],'empty transfer')
            s['location']=event['destination'];continue
        station=event['station_id']
        require(station in ('WS_RECORDS','WS_ACTIVE') or station==s['location'],'payload teleported to station')
        if oid in ('FILM','FIXED_SWAP','RESTORE_TRACKED','HEATER_ATTACH','MAP_ATTACH','TC_ATTACH'):
            s['assembly_revision']+=1;s['qc_revision']=None
        if oid=='FILM':s['film_layers']=2;s['configuration']='tracked_nanoporous'
        if oid=='FIXED_SWAP':s['film_layers']=2;s['configuration']='fixed_LDPE'
        if oid=='RESTORE_TRACKED':s['film_layers']=2;s['configuration']='tracked_nanoporous'
        if oid in ('ASSEMBLY_QC','FIXED_QC'):
            require(s['film_layers']==2,'cannot accept incomplete cover')
            s['qc_revision']=s['assembly_revision']
        if oid=='TC_ATTACH':
            require(event.get('calibration_id'),'calibration identity missing')
            s['probe_calibration']=event['calibration_id']
        if oid=='WITNESS_CUT':
            s['specimen_ready']=pid not in ('W_white','W_black')
            if pid in ('W_nanoporous_PE','W_LDPE'):s['film_layers']=2
        if oid=='COAT_UNLOAD' and pid.startswith('W_'):s['specimen_ready']=True
        if oid in ('OPT_SCAN','ANGLE_SCAN'):require(s.get('specimen_ready',False),'optical specimen not physically prepared')
        if oid in ('LID_BASELINE','STAG_LOG','PID_STEP','MAP_LOG','TRACK_ADJUST','BAND_CHECK'):
            validate_state(s,True)
        if oid=='TRACK_ADJUST':require(s['configuration']=='tracked_nanoporous','fixed band cannot be tracked')
        if oid=='BAND_CHECK':require(s['configuration']=='fixed_LDPE','fixed-band configuration missing')
        if oid=='PID_STEP':
            require(s.get('heater_installed',False),'heater not installed')
            require(event.get('duration_s')==300,'PID plateau must be 300 s')
            s['heater_output']=True
        if oid in ('HEATER_OFF','STOP_SAFE'):s['heater_output']=False
        if oid=='HEATER_ATTACH':s['heater_installed']=True
        if oid=='HEATER_REMOVE':
            require(not s['heater_output'],'heater removal requires output off')
            s['heater_installed']=False;s['assembly_revision']+=1;s['qc_revision']=None
        if oid=='MAP_LOG':
            require(not s.get('heater_installed',False),'mapping includes an unreported heater')
            require(s['configuration']=='tracked_nanoporous','map uses wrong assembly configuration')
            sensors=event.get('sensor_ids',[])
            require(len(sensors)==7 and len(set(sensors))==7,'map needs seven distinct sensor identities')
            require(event.get('duration_s')==3600,'map window must be one hour')
        validate_state(s)

def fixture():
    return {'record_kind':'symbolic_planner_test_fixture_not_qualified_episode',
        'optical_repeats':1,'calibration_setpoints_C':[0,10,20],
        'pid_targets_K_relative_ambient':[-1,0,1],
        'tracking_occurrences_per_day_session':2,
        'note':'These numbers exercise nonempty loops only. They are not extracted from the paper and must not be used to run hardware.',
        'qualified_for_execution':False}

def compile_reference(order):
    require(order.get('record_kind')=='symbolic_planner_test_fixture_not_qualified_episode','compiler accepts explicitly labeled test work orders only')
    require(not order.get('qualified_for_execution',True),'fixture cannot certify execution')
    for name in ('optical_repeats','tracking_occurrences_per_day_session'):
        require(type(order.get(name)) is int and order[name]>0,'empty or invalid loop '+name)
    for name in ('calibration_setpoints_C','pid_targets_K_relative_ambient'):
        v=order.get(name);require(isinstance(v,list) and len(v)>0,'empty loop '+name)
        require(all(type(x) in (int,float) and math.isfinite(x) for x in v),'invalid target')
    require(order['pid_targets_K_relative_ambient']==sorted(set(order['pid_targets_K_relative_ambient'])),'PID targets must be distinct and increasing')
    ops={o['id']:o for o in read('operations')['operations']}
    states=initial_states();events=[];leaf='BUILD_PAIR';session='construction'
    def emit(oid,payload=(),station=None,**params):
        nonlocal events
        op=ops[oid];station=station or op['location_id'];payload=list(payload)
        if station=='WS_OPTICAL_ACTIVE':station='WS_FTIR'
        if station not in ('WS_RECORDS','WS_ACTIVE','WS_TRANSFER'):
            for pid in payload:
                origin=states[pid]['location']
                if origin!=station:
                    emit('MOVE',[pid],'WS_TRANSFER',origin=origin,destination=station,
                         transfer_support='identified_retained_carrier',condition='support and isolation observed before release')
        event={'id':'OCC-%04d'%(len(events)+1),'operation_id':oid,'branch_id':leaf,
               'session_id':session,'payload_ids':payload,'station_id':station,
               'record_kind':'planned_obligation_not_observation','attempts':[],
               'required_step_ids':[s['id'] for s in op['reference_steps']],**params}
        event['required_iteration_contracts']=copy.deepcopy(op.get('iteration_contracts',[]))
        if oid=='MOVE':event['required_step_ids']=[s['id'] for s in ops['MOVE']['reference_steps']]
        transition(states,event);events.append(event)
        return event
    emit('PLAN');emit('STOCK',['white','black']);emit('TRACK_DESIGN')
    for pid in ('white','black'):
        for oid in ('MACHINE_PARTS','FAB_LOAD','FAB_RUN','FAB_UNLOAD','COAT_LOAD'):emit(oid,[pid])
        # One COAT_RUN occurrence contains three apply/wait sub-occurrences;
        # do not repeat its complete three-coat procedure three times.
        emit('COAT_RUN',[pid],coat_iterations=[{'coat_index':i,'apply_step':'COAT_RUN.02','wait_step':'COAT_RUN.03','record_kind':'planned_suboccurrence'} for i in (1,2,3)])
        for oid in ('COAT_UNLOAD','LAYOUT','BASE','EMITTER','FILM','SHIELD','REFLECTOR','ASSEMBLY_QC'):emit(oid,[pid])
    leaf='CALIBRATE';session='calibration'
    emit('CAL_BLOCK_PREP',block_id='CAL_BLOCK',hole_roles=['REF_RTD','TC_W','TC_B']+['TC_MAP_%d'%i for i in range(1,7)])
    emit('CAL_MOUNT',probe_ids=['TC_W','TC_B']+['TC_MAP_%d'%i for i in range(1,7)])
    for i,value in enumerate(order['calibration_setpoints_C']):emit('CAL_ACQUIRE',setpoint_C=value,setpoint_index=i)
    emit('CAL_FIT');emit('CAL_UNLOAD')
    for pid in ('white','black'):
        emit('TC_ATTACH',[pid],calibration_id='PLANNED_CAL_'+pid);emit('ASSEMBLY_QC',[pid])
    leaf='OPT_HEMISPHERICAL';session='optical'
    parents={'W_white':['copper_stock_lot','white_paint_lot'],'W_black':['copper_stock_lot','black_paint_lot'],
             'W_aluminum':['reflector_aluminum_lot'],'W_nanoporous_PE':['Targray_film_lot'],'W_LDPE':['LDPE_film_lot']}
    emit('WITNESS_PREP',witness_ids=list(parents),parent_material_lots=parents)
    # Witnesses are new retained payloads, never renamed whole cooler assemblies.
    for material in ('white','black','aluminum','nanoporous_PE','LDPE'):
        wid='W_'+material
        states[wid]=witness_state(wid,parents[wid])
        emit('WITNESS_CUT',[wid])
        if material in ('white','black'):
            emit('COAT_LOAD',[wid]);emit('COAT_RUN',[wid],coat_iterations=[{'coat_index':i,'apply_step':'COAT_RUN.02','wait_step':'COAT_RUN.03','record_kind':'planned_suboccurrence'} for i in (1,2,3)]);emit('COAT_UNLOAD',[wid])
        for instrument,station in [('UVVIS','WS_UVVIS'),('FTIR','WS_FTIR')]:
            config=instrument+'_hemispherical';emit('OPT_REFERENCE',station=station,instrument=instrument,configuration_id=config)
            for rep in range(order['optical_repeats']):
                emit('OPT_MOUNT',[wid],station,configuration_id=config)
                emit('OPT_SCAN',[wid],station,configuration_id=config,reference_configuration_id=config,repeat_index=rep)
                emit('OPT_UNLOAD',[wid],station)
    emit('OPT_SUMMARY')
    leaf='OPT_ANGULAR';session='angular'
    for material in ('white','black'):
        wid='W_'+material
        for angle in (12,30,40,50,60,70,80):
            for polarization in ('s','p'):
                config='Harrick12' if angle==12 else 'SpectraTechVariable'
                config+='_%d_%s'%(angle,polarization)
                emit('ANGLE_MOUNT',[wid],configuration_id=config,angle_deg=angle,polarization=polarization)
                emit('ANGLE_REFERENCE',station='WS_FTIR',configuration_id=config,angle_deg=angle,polarization=polarization)
                for rep in range(order['optical_repeats']):emit('ANGLE_SCAN',[wid],configuration_id=config,reference_configuration_id=config,angle_deg=angle,polarization=polarization,repeat_index=rep)
                emit('OPT_UNLOAD',[wid],station='WS_FTIR')
    emit('OPT_SUMMARY')
    leaf='ENVIRONMENT';session='environment_setup'
    emit('ENV_SETUP');emit('SYNC');emit('ENV_LOG',stream='weather_solar_ambient',weather_cadence_s=300,other_cadences='required_inputs')

    def outdoor_start(ids,night=False,fixed=False):
        for oid in ('SITE_SETUP','ENV_SETUP','SYNC','ENV_LOG'):emit(oid,ids)
        if fixed:emit('BAND_CHECK',ids)
        emit('LID_BASELINE',ids,duration_s=300,within_session_interval=session,
             timing_basis='E_STAG' if leaf=='TRACKED_STAGNATION' else 'test_fixture_inference_requires_qualified_branch_timing')
        emit('LID_REMOVE',ids)
        if not night and not fixed:
            emit('TRACK_ADJUST',ids,scope='within_acquisition',iterations=order['tracking_occurrences_per_day_session'],
                 timing='fixture count only; event-driven times require qualified solar schedule')

    def close_session(ids):
        emit('STOP_SAFE',ids,station='WS_OUTDOOR');emit('UNMOUNT',ids,station='WS_OUTDOOR')

    leaf='TRACKED_STAGNATION';session='tracked_stagnation'
    outdoor_start(['white','black']);emit('STAG_LOG',['white','black'],duration_s=14400,baseline_included=True);close_session(['white','black'])
    leaf='PID_POWER';session='power'
    for pid in ('white','black'):emit('HEATER_ATTACH',[pid]);emit('ASSEMBLY_QC',[pid])
    outdoor_start(['white','black'])
    for oid in ('POWER_CHECK','PID_CONFIG','POWER_BASELINE'):emit(oid,['white','black'])
    for i,target in enumerate(order['pid_targets_K_relative_ambient']):
        emit('PID_STEP',['white','black'],target_index=i,target_K_relative_ambient=target,duration_s=300,independent_controller_ids=['SMU_W','SMU_B'])
        emit('STEP_SUMMARY',target_index=i,last_s=120)
    emit('HEATER_OFF',['white','black']);close_session(['white','black'])
    leaf='FIXED_LDPE';session='fixed_LDPE'
    for pid in ('white','black'):
        emit('HEATER_REMOVE',[pid]);emit('FIXED_SWAP',[pid]);emit('FIXED_QC',[pid])
    outdoor_start(['white','black'],fixed=True);emit('STAG_LOG',['white','black'],duration_s=14400,baseline_included=True,duration_basis='reconstruction_fixture_requires_qualified_fixed_run_window');close_session(['white','black'])
    leaf='MAP_CLEAR_DAY';session='restore_for_mapping'
    emit('RESTORE_TRACKED',['white']);emit('ASSEMBLY_QC',['white']);emit('MAP_ATTACH',['white']);emit('ASSEMBLY_QC',['white'])
    for leaf,night in [('MAP_CLEAR_DAY',False),('MAP_CLEAR_NIGHT',True),('MAP_HAZY_NOON',False)]:
        session=leaf.lower();outdoor_start(['white'],night=night)
        emit('MAP_CONDITION',['white'],condition=leaf)
        emit('MAP_LOG',['white'],duration_s=3600,baseline_included=True,sensor_ids=['TC_W']+['TC_MAP_%d'%i for i in range(1,7)])
        emit('MAP_SUMMARY',condition=leaf);close_session(['white'])
    session='campaign_closeout'
    emit('COMPARE')
    for pid in list(states):
        emit('STOP_SAFE',[pid],station=states[pid]['location']);emit('UNMOUNT',[pid],station=states[pid]['location']);emit('ARCHIVE',[pid])
    emit('RESET');emit('REPORT')
    return {'schema_version':'sciencegym.directional_cooling.v3','record_kind':'symbolic_reference_plan_not_execution',
            'input':order,'occurrences':events,'expected_final_state':states,
            'counts':{'operation_definitions_used':len({e['operation_id'] for e in events}),'planned_occurrences':len(events),'physical_attempts':0,'physical_successes':0},
            'plan_limitations':['Transport is bound for registered payloads; tool and fixture micro-transfers still require robot-level binding','Tracking iterations are overlapping obligations, not a timed continuous controller','The plan checker does not validate contact mechanics, optical processing or scientific observations']}

def verify_plan(plan):
    require(plan['record_kind']=='symbolic_reference_plan_not_execution','execution claim in symbolic plan')
    states=initial_states();refs=set();ids=set();coat={};branches=set();seen=set()
    ops={o['id']:o for o in read('operations')['operations']}
    angular_setup={};angular_references={}
    for event in plan['occurrences']:
        require(event['id'] not in ids,'duplicate occurrence');ids.add(event['id'])
        oid=event['operation_id'];branches.add(event['branch_id']);seen.add(oid)
        require(oid in ops,'unknown operation')
        require(event.get('required_step_ids')==[s['id'] for s in ops[oid]['reference_steps']], 'omitted, duplicated or reordered step obligations')
        require(event.get('required_iteration_contracts')==ops[oid].get('iteration_contracts',[]), 'missing or changed manual iteration scope')
        require(event.get('attempts')==[],'plan includes fabricated attempts')
        if oid=='WITNESS_PREP':
            for wid in event['witness_ids']:
                require(wid not in states,'witness identity reused')
                require(event.get('parent_material_lots',{}).get(wid),'missing witness material parents')
                states[wid]=witness_state(wid,event['parent_material_lots'][wid])
        if oid=='COAT_RUN':
            require([x['coat_index'] for x in event['coat_iterations']]==[1,2,3],'three distinct coats required')
        if oid=='ANGLE_MOUNT':
            refs={x for x in refs if x[1]!=event['station_id']}
            angular_setup[event['station_id']]=(event.get('configuration_id'),event.get('angle_deg'),event.get('polarization'))
            angular_references.pop(event['station_id'],None)
        if oid=='ANGLE_REFERENCE':
            config=(event.get('configuration_id'),event.get('angle_deg'),event.get('polarization'))
            require(config==angular_setup.get(event['station_id']),'angular reference differs from physically set angle/polarization')
            angular_references[event['station_id']]=config
        if oid=='ANGLE_SCAN':
            config=(event.get('configuration_id'),event.get('angle_deg'),event.get('polarization'))
            require(config==angular_setup.get(event['station_id'])==angular_references.get(event['station_id']), 'angle/polarization changed after reference')
        if oid in ('OPT_REFERENCE','ANGLE_REFERENCE'):refs.add((event.get('configuration_id'),event['station_id']))
        if oid in ('OPT_SCAN','ANGLE_SCAN'):
            require(event['configuration_id']==event['reference_configuration_id'],'stale optical reference')
            require((event['configuration_id'],event['station_id']) in refs,'optical reference not acquired in plan')
        transition(states,event)
    expected={b['id'] for b in read('branches')['branches']}
    require(branches==expected,'missing selected physical branch')
    require(seen=={o['id'] for o in read('operations')['operations']},'operation omitted from walkthrough')
    optical=[e for e in plan['occurrences'] if e['operation_id']=='OPT_SCAN']
    expected_optical={(m,station,r) for m in ('white','black','aluminum','nanoporous_PE','LDPE') for station in ('WS_UVVIS','WS_FTIR') for r in range(plan['input']['optical_repeats'])}
    actual_optical=[(e['payload_ids'][0][2:],e['station_id'],e['repeat_index']) for e in optical]
    require(len(actual_optical)==len(expected_optical) and set(actual_optical)==expected_optical,'incomplete or duplicated optical condition')
    angular=[e for e in plan['occurrences'] if e['operation_id']=='ANGLE_SCAN']
    expected_angular={(m,a,p,r) for m in ('white','black') for a in (12,30,40,50,60,70,80) for p in ('s','p') for r in range(plan['input']['optical_repeats'])}
    actual_angular=[(e['payload_ids'][0][2:],e['angle_deg'],e['polarization'],e['repeat_index']) for e in angular]
    require(len(actual_angular)==len(expected_angular) and set(actual_angular)==expected_angular,'incomplete or duplicated angular condition')
    maps=[e['branch_id'] for e in plan['occurrences'] if e['operation_id']=='MAP_LOG']
    require(sorted(maps)==sorted(['MAP_CLEAR_DAY','MAP_CLEAR_NIGHT','MAP_HAZY_NOON']),'missing or duplicated map condition')
    plateaus=[e for e in plan['occurrences'] if e['operation_id']=='PID_STEP']
    require([e['target_K_relative_ambient'] for e in plateaus]==plan['input']['pid_targets_K_relative_ambient'],'missing or reordered PID plateau')
    require(all(set(e['payload_ids'])=={'white','black'} and len(set(e['independent_controller_ids']))==2 for e in plateaus),'paired power requires separate controllers')
    require(states==plan['expected_final_state'],'final state differs from replay')
    require(all(not s['heater_output'] and s['supported'] and s['location']=='WS_ARCHIVE' for s in states.values()),'incomplete closeout')
    return {'passed':True,'kind':'symbolic_checks_only','planned_occurrences':len(ids),'physical_successes':0}

if __name__=='__main__':
    p=compile_reference(fixture());result=verify_plan(p)
    (HERE/'reference_plan.json').write_text(json.dumps(p,indent=2)+'\n')
    print(json.dumps(result))
