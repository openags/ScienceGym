"""Local illustrative state guards. No network, device I/O, physics or calibration."""
from dataclasses import dataclass, asdict
@dataclass
class State:
    carrier: str='docked'
    clamp: str='closed'
    contact: str='released'
    optics: str='CFG_PARALLEL_MITUTOYO'
    configuration_revision: int=1
    physical_calibration_valid: bool=False
    mode: str='static_demo_only'

def transition(s,event):
    n=State(**asdict(s))
    if event=='open_clamp':
        if n.contact!='released': raise ValueError('Release required before handling')
        n.clamp='open'
    elif event=='grasp_carrier':
        if n.clamp!='open' or n.contact!='released':raise ValueError('Open clamp and released contact required')
        n.carrier='held'
    elif event=='dock_carrier':
        if n.carrier!='held' or n.clamp!='open':raise ValueError('Held carrier and open clamp required')
        n.carrier='docked'
    elif event=='close_clamp':
        if n.carrier!='docked':raise ValueError('Dock carrier first')
        n.clamp='closed'
    elif event=='illustrative_contact':
        if n.carrier!='docked' or n.clamp!='closed':raise ValueError('Dock and clamp required')
        n.contact='illustrative_contact'
    elif event=='release':n.contact='released'
    elif event=='lateral_step':
        if n.contact!='released':raise ValueError('Release required before lateral move')
    elif event in ['CFG_PARALLEL_MITUTOYO','CFG_CHARACTERIZATION_OLYMPUS']:
        if n.contact!='released':raise ValueError('Release required before optics change')
        if n.optics!=event:n.configuration_revision+=1
        n.optics=event
    else:raise ValueError('Unknown semantic event')
    n.physical_calibration_valid=False
    return n
if __name__=='__main__':
    import json
    s=State();log=[]
    for e in ['open_clamp','grasp_carrier','dock_carrier','close_clamp','illustrative_contact','release','lateral_step','CFG_CHARACTERIZATION_OLYMPUS']:
        s=transition(s,e);log.append({'event':e,'state':asdict(s)})
    print(json.dumps({'mode':'static_demo_only','sensor_receipt':False,'journal':log},indent=2))
