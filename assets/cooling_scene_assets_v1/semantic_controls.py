"""Guarded local state demo. No clock, network, device I/O, thermal model or robot API.
This program cannot issue scientific completion evidence or energize a heater.
"""
from dataclasses import dataclass, asdict, field

@dataclass
class State:
    carrier: str = 'docked'
    clamp: str = 'closed'
    lower_film: str = 'intact'
    upper_film: str = 'intact'
    lower_film_revision: int = 1
    upper_film_revision: int = 1
    lid: str = 'parked'
    logger: str = 'idle'
    optical_config: str = 'unqualified'
    optical_sample: str = 'none'
    reflector_pose: str = 'center'
    geometry_qualified: bool = False
    physical_execution: bool = False
    mode: str = 'static_semantic_demo'

def validate(s):
    enums={'carrier':{'docked','held_demo'},'clamp':{'open','closed'},'lower_film':{'intact','removed','torn_demo'},'upper_film':{'intact','removed'},'lid':{'parked','closed'},'logger':{'idle','armed_demo'},'optical_config':{'unqualified','uvvis','ftir_sphere','ftir_angle'},'optical_sample':{'none','authored_reference_demo'},'reflector_pose':{'left','center','right'}}
    for key, values in enums.items():
        if getattr(s,key) not in values:raise ValueError('Invalid demonstration state: '+key)
    for k in ['lower_film_revision','upper_film_revision']:
        if type(getattr(s,k)) is not int or getattr(s,k)<1:raise ValueError('Invalid component revision')
    if s.carrier=='held_demo' and s.clamp!='open':raise ValueError('Held carrier cannot be clamped')
    if s.logger=='armed_demo' and (s.carrier!='docked' or s.clamp!='closed' or s.lower_film!='intact' or s.upper_film!='intact'):raise ValueError('Invalid armed demo state')
    if s.optical_sample!='none' and s.optical_config=='unqualified':raise ValueError('Unconfigured reference placement')
    if s.mode!='static_semantic_demo' or s.physical_execution or s.geometry_qualified:
        raise ValueError('This demo cannot assert physical qualification')
    return s

def transition(state, event):
    validate(state)
    s=State(**asdict(state))
    if event=='stop_logger':s.logger='idle'
    elif event=='arm_logger':
        if s.carrier!='docked' or s.clamp!='closed' or s.lower_film!='intact' or s.upper_film!='intact':
            raise ValueError('Dock, retention and intact film states required')
        s.logger='armed_demo'
    elif event=='open_clamp':
        if s.logger!='idle':raise ValueError('Stop demo logger before handling')
        if s.carrier!='docked':raise ValueError('Clamp belongs to dock')
        s.clamp='open'
    elif event=='close_clamp':
        if s.carrier!='docked':raise ValueError('Seat carrier before closing clamp')
        s.clamp='closed'
    elif event=='grasp_carrier':
        if s.clamp!='open' or s.carrier!='docked' or s.logger!='idle':raise ValueError('Open clamp and idle docked carrier required')
        s.carrier='held_demo'
    elif event=='dock_carrier':
        if s.carrier!='held_demo' or s.clamp!='open':raise ValueError('Held carrier and open clamp required')
        s.carrier='docked'
    elif event in ('remove_lower_film','remove_upper_film','replace_lower_film','replace_upper_film','tear_lower_film'):
        if s.logger!='idle' or s.carrier!='docked' or s.clamp!='open':raise ValueError('Idle, supported, released fixture required')
        field_name='lower_film' if 'lower' in event else 'upper_film'
        if event.startswith('remove_'):setattr(s,field_name,'removed')
        elif event.startswith('replace_'):
            if getattr(s,field_name)=='intact':raise ValueError('Remove old film before replacement')
            setattr(s,field_name,'intact');setattr(s,field_name+'_revision',getattr(s,field_name+'_revision')+1)
        else:
            if s.lower_film!='intact':raise ValueError('Only an intact film can be torn')
            s.lower_film='torn_demo'
    elif event in ('cover_apertures','uncover_apertures'):
        if s.carrier!='docked':raise ValueError('Docked demonstration state required')
        s.lid='closed' if event=='cover_apertures' else 'parked'
    elif event in ('reflector_left','reflector_center','reflector_right'):
        s.reflector_pose=event.split('_')[1]
    elif event in ('select_uvvis','select_ftir_sphere','select_ftir_angle'):
        if s.optical_sample!='none':raise ValueError('Unload before changing configuration')
        s.optical_config=event.removeprefix('select_')
    elif event=='mount_reference':
        if s.optical_config=='unqualified' or s.optical_sample!='none':raise ValueError('Select empty demonstration configuration first')
        s.optical_sample='authored_reference_demo'
    elif event=='unload_optical':s.optical_sample='none'
    else:raise ValueError('Unsupported semantic event; no thermal, acquisition or output command exists')
    s.geometry_qualified=False;s.physical_execution=False
    return validate(s)

EVENT_TO_OPERATION={
 'open_clamp':'UNMOUNT','close_clamp':'LAYOUT','grasp_carrier':'MOVE','dock_carrier':'MOVE',
 'remove_lower_film':'FILM','remove_upper_film':'FILM','replace_lower_film':'FILM','replace_upper_film':'FILM','tear_lower_film':'ASSEMBLY_QC',
 'cover_apertures':'LID_BASELINE','uncover_apertures':'LID_REMOVE','arm_logger':'STAG_LOG','stop_logger':'STOP_SAFE',
 'reflector_left':'TRACK_ADJUST','reflector_center':'TRACK_ADJUST','reflector_right':'TRACK_ADJUST',
 'select_uvvis':'OPT_REFERENCE','select_ftir_sphere':'OPT_REFERENCE','select_ftir_angle':'ANGLE_MOUNT','mount_reference':'OPT_REFERENCE','unload_optical':'OPT_UNLOAD'}

if __name__=='__main__':
    import json
    s=State();log=[]
    for event in ['open_clamp','remove_lower_film','replace_lower_film','grasp_carrier','dock_carrier','close_clamp','cover_apertures','arm_logger','uncover_apertures','reflector_left','stop_logger','select_ftir_angle','mount_reference','unload_optical']:
        s=transition(s,event);log.append({'event':event,'operation_id':EVENT_TO_OPERATION[event],'state':asdict(s),'physical_receipt':False})
    print(json.dumps({'scope':'static_bound_state_only','sensor_data':None,'electrical_output':None,'journal':log},indent=2))
