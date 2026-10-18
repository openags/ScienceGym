"""Source-meter socket and a selected cable plug with passive spring contacts.

The device envelope and port positions use the manufacturer reconstruction.
The plug, contact leaves and cable stiffness are explicit task selections,
not a vendor-qualified mating connector or an electrical measurement model.
"""
import json
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP,vec
from extended_device_assets import DEVICES,visuals

CENTER=np.array([.46,.22,TOP+.12])
PARK=np.array([.38,-.27,TOP+.070])


def build(path,port='force_hi',bore_radius=.002,spring=True):
    # The light metal contact leaves require a smaller step than the arm.
    # A retained 0.5 ms trial became unstable in leaf 3 at 6.5 ms; 0.1 ms
    # resolves the selected passive spring without adding fictitious mass.
    w=World();w.root.find('option').attrib.update(timestep='.0001',impratio='10',iterations='120',noslip_iterations='0')
    actuator=w.root.find("actuator/general[@name='actuator8']");actuator.attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    device=w.body('keithley_2425',CENTER,False);visuals(w,device,'keithley_2425')
    parts=json.loads((DEVICES['keithley_2425']/'parts.json').read_text())
    for p in parts:
        if p['id'] in ['top_shell','bottom_shell','side_shell_-1','side_shell_1','display_bezel','key_panel']:
            w.box(device,'collision_'+p['id'],np.array(p['dimensions_m'])/2,p['location_m'],rgba=[0,0,0,0])
    sockets=[i for i in json.loads((DEVICES['keithley_2425']/'interfaces.json').read_text())['interfaces'] if i['kind']=='banana_socket' and i['axis']==[0,1,0]]
    selected=next(i for i in sockets if i['id']==port)
    for i in sockets:
        mount=ET.SubElement(device,'body',name='jack_'+i['id'],pos=vec(i['entry_m']),euler='-1.57079632679 0 0')
        w.ring(mount,'jack_wall_'+i['id'],bore_radius,.0065,.012,z=.006,rgba=[0,0,0,0],mass=.01)
        for g in mount.findall('geom'):
            g.set('friction','.5 .001 .0001');g.set('solref','.002 1');g.set('solimp','.99 .999 .0001')
    riser=w.body('meter_riser',[*CENTER[:2],TOP],False)
    w.box(riser,'riser_top',[.125,.19,.006],[0,0,.114],[.14,.22,.29,1])
    for x in [-.10,.10]:
        for y in [-.15,.15]:w.box(riser,'riser_leg_'+str(x)+'_'+str(y),[.009,.009,.054],[x,y,.054],[.14,.22,.29,1])
    plug=w.body('plug',PARK)
    w.cylinder(plug,'plug_grip',.006,.015,[0,0,0],[.65,.025,.018,1],euler='1.57079632679 0 0',mass='.006')
    w.cylinder(plug,'pin_core',.0015,.009,[0,.024,0],[.62,.64,.66,1],euler='1.57079632679 0 0',mass='.002')
    w.cylinder(plug,'plug_tail',.0025,.004,[0,-.019,0],[.14,.15,.16,1],euler='1.57079632679 0 0',mass='.001')
    ET.SubElement(plug,'site',name='plug_grasp',pos='0 0 0',size='.001')
    ET.SubElement(plug,'site',name='plug_tip',pos='0 .033 0',size='.0005')
    for n in range(4):
        angle=n*np.pi/2;radial=np.array([np.cos(angle),0,np.sin(angle)])
        leaf=ET.SubElement(plug,'body',name='plug_leaf_'+str(n),pos=vec(radial*.0019))
        ET.SubElement(leaf,'joint',name='leaf_compression_'+str(n),type='slide',axis=vec(radial),range='-.0006 0',stiffness='2500' if spring else '0',damping='.2',springref='0',solreflimit='.001 1',solimplimit='.999 .999 .00001')
        ET.SubElement(leaf,'geom',name='spring_contact_'+str(n),type='capsule',fromto='0 .018 0 0 .030 0',size='.0002',mass='.00005',rgba='.7 .72 .74 1',friction='.5 .001 .0001',solref='.002 1',solimp='.99 .999 .0001')
    # A full selected 0.6 m lead; only the first vertex is fixed to its plug.
    # End routing and zero bending stiffness are selected staging/model limits.
    route=np.array([[0,-.023,0],[0,-.075,-.068],[.23,-.075,-.068],[.23,.045,-.068],[.07,.045,-.068]])
    cumulative=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route,axis=0),axis=1))]
    route[-1,0]+=(cumulative[-1]-.6);cumulative=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route,axis=0),axis=1))]
    # Preserve corners instead of shortening them by uniform interpolation.
    points=[route[0]]
    for a,b in zip(route,route[1:]):
        count=max(1,int(np.ceil(np.linalg.norm(b-a)/.025)))
        points.extend(a+(b-a)*u for u in np.linspace(0,1,count+1)[1:])
    points=np.asarray(points)
    flex=ET.SubElement(plug,'flexcomp',name='plug_lead',type='direct',dim='1',point=vec(points.ravel()),element=' '.join(f'{i} {i+1}' for i in range(len(points)-1)),mass=str(1300*np.pi*.001**2*.6),radius='.001',rgba='.15 .025 .025 1')
    ET.SubElement(flex,'pin',id='0');ET.SubElement(flex,'edge',equality='true',damping='.001',solref='.002 1',solimp='.9999 .9999 .00001')
    ET.SubElement(flex,'contact',selfcollide='auto',condim='3',friction='.3 .001 .0001',solref='.0021 1',solimp='.99 .999 .0001')
    stand=w.body('plug_stand',[*PARK[:2],TOP],False)
    for sign in [-1,1]:
        w.box(stand,'plug_support_'+str(sign),[.007,.0005,.032],[0,sign*.014,.032],[.08,.35,.42,1])
        for side in [-1,1]:w.box(stand,'plug_side_'+str(sign)+'_'+str(side),[.002,.0005,.035],[side*.0085,sign*.014,.035],[.08,.35,.42,1])
    w.box(stand,'plug_stand_foot',[.018,.024,.003],[0,0,.003],[.08,.35,.42,1])
    w.save(path)
    return dict(port=port,entry_m=(CENTER+selected['entry_m']).tolist(),park_m=PARK.tolist(),insertion_depth_m=.010,
                cable_length_m=float(cumulative[-1]),bore_radius_m=bore_radius,spring_enabled=spring,
                selected_contact_leaf_stiffness_N_m=2500 if spring else 0,selected_free_pin_envelope_m=.0042,
                source_asset='assets/keithley_2425_v1',source_meter_output='off initial condition',
                electrical_continuity_validated=False,whole_paper_validated=False,
                inferences=['custom plug dimensions and four-leaf contact model','0.6 m lead, 2 mm jacket, no bending/torsion','staging stand and instrument riser','source output-off initial condition'])
