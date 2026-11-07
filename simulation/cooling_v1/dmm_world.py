"""Keithley 2000 front-panel controls with passive physical button travel."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from world import World,HERE,TOP,vec
from device_assets import visuals,DEVICES

CENTER=np.array([.48,.21,TOP+.14])


def build(path):
    w=World();w.root.find('option').attrib.update(impratio='5',noslip_iterations='1')
    # The pusher is an explicitly selected task tool, mounted in the tool
    # flange. It has no actuator and can only press through arm motion.
    hand=w.root.find(".//body[@name='hand']")
    hand.find("site[@name='tcp']").set('pos','0 0 .1515')
    tool=ET.SubElement(hand,'body',name='button_probe')
    ET.SubElement(tool,'geom',name='pusher_shaft',type='capsule',fromto='0 0 .100 0 0 .150',size='.0015',mass='.008',rgba='.25 .32 .38 1')
    device=w.body('keithley_2000',CENTER,False)
    card=json.loads((DEVICES['keithley_2000']/'interfaces.json').read_text())
    selected=[i for i in card['interfaces'] if i.get('axis')==[0,1,0] and i['kind'] in ['push_button','latched_push_button']]
    omitted=['key_'+i['id'] for i in selected]+['text_'+i['id'] for i in selected]+['input_selector']
    visuals(w,device,'keithley_2000',exclude=omitted)
    # Source-sized housing. The front is built from strips around its
    # controls so no broad collision slab traps a moving button.
    w.box(device,'housing_top',[.1025,.1725,.00075],[0,-.0015,.10325],rgba=[0,0,0,0])
    w.box(device,'housing_floor',[.1025,.1725,.00075],[0,-.0015,.01575],rgba=[0,0,0,0])
    for sign in [-1,1]:w.box(device,'housing_side_'+str(sign),[.00075,.1725,.043],[sign*.10175,-.0015,.0595],rgba=[0,0,0,0])
    w.box(device,'display_collision',[.083,.002,.02325],[-.0236,-.1805,.0807],rgba=[0,0,0,0])
    w.box(device,'panel_backstop',[.083,.001,.020],[-.0236,-.176,.034],rgba=[0,0,0,0])
    for i in selected:
        name='button_'+i['id'];p=np.array(i['center_m']);travel=i['travel_m']
        body=ET.SubElement(device,'body',name=name,pos=vec(p))
        ET.SubElement(body,'joint',name=name+'_travel',type='slide',axis='0 1 0',range=f'0 {travel}',damping='2',stiffness='600',springref='0')
        radius=.0035 if i['id'] in ['SHIFT','LOCAL','POWER'] else .0045 if i['id'].startswith('RANGE') or i['id']=='AUTO' else .0052
        # Interface depth is an inferred tactile model, separately declared
        # from manufacturer panel coordinates and published exterior size.
        w.cylinder(body,name+'_cap',radius,.0015,[0,.0015,0],[.08,.09,.08,1],mass='.003',euler='1.57079632679 0 0')
        body.find('geom').set('rgba','0 0 0 0')
        visuals(w,body,'keithley_2000',prefix=name,only=['key_'+i['id'],'text_'+i['id']]+(['input_selector'] if i['id']=='input_selector' else []),origin=p)
        i['physical_body']=name;i['world_center_m']=(CENTER+p).tolist()
    # Model-specific physical jack bores remain open for later lead insertion.
    for i in card['interfaces']:
        if i.get('kind')!='banana_socket' or i['axis']!=[0,1,0]:continue
        mount=ET.SubElement(device,'body',name='jack_'+i['id'],pos=vec(i['entry_m']),euler='-1.57079632679 0 0')
        w.ring(mount,'jack_wall_'+i['id'],.002,.0042,.012,z=.006,rgba=[0,0,0,0],mass=.01)
    # Raised stand gives the front-facing Panda approach sufficient clearance.
    riser=w.body('meter_riser',[*CENTER[:2],TOP],False)
    w.box(riser,'meter_riser_top',[.125,.19,.006],[0,0,.134],[.14,.22,.29,1])
    for x in [-.10,.10]:
        for y in [-.15,.15]:w.box(riser,'meter_riser_leg_'+str(x)+'_'+str(y),[.009,.009,.064],[x,y,.064],[.14,.22,.29,1])
    # Select a force-interface gripper actuator to match HardwareRobot.
    actuator=w.root.find("actuator/general[@name='actuator8']")
    actuator.attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    w.save(path);return selected
