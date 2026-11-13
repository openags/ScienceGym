"""Selected passive terminal mechanism for the source-specific USB-TC asset.

The manual supplies identities, the enclosure and 16--30 AWG range. Internal
thread pitch, captive pressure plate, friction and driver fit are engineering
selections. A hinge/slide equality represents an ideal helical thread, not an
actuator on the screw or a software attachment to the wire. Only contact from
the driver can rotate the screw; wire retention uses ordinary contact friction.
"""
import json
import xml.etree.ElementTree as ET
import numpy as np
from extended_device_assets import DEVICES,visuals
from world import vec

PITCH=.0005
FRICTION_TORQUE=.0004
# The task card selects 24 AWG K-compatible extension conductors; the 36 AWG
# probe itself is not treated as a qualified direct terminal connection.
WIRE_DIAMETER=.0005106
WIRE_DENSITY=8600.


def add_terminal(w,parent,pin=3,visual=True,friction=True,clamp=True):
    source=json.loads((DEVICES['mcc_usb_tc']/'interfaces.json').read_text())
    t=next(t for t in source['terminals'] if t['pin']==pin)
    prefix=f'terminal_{pin:02d}';entry=np.array(t['wire_entry_m']);axis=np.array(t['insertion_axis'])
    screw_origin=np.array(t['screw_center_m']);x,y,z=screw_origin
    side=-int(axis[1]);floor=entry[2]-t['entry_height_m']/2
    # Five rectangular walls retain the actual open entry; a convex hull of
    # the perforated insulator would silently close it.
    for sign in [-1,1]:
        w.box(parent,prefix+'_side_'+str(sign),[.0003625,.0041,.00345],
              [x+sign*(.00105+.0003625),y,.02125],rgba=[0,0,0,0])
    w.box(parent,prefix+'_floor',[.00105,.0041,(floor-.0178)/2],
          [x,y,(floor+.0178)/2],rgba=[0,0,0,0])
    # Shaft bore below a wider head counterbore. A solid roof would stop
    # the head after just 0.2 mm and could never clamp the selected wire.
    for sign in [-1,1]:
        w.box(parent,prefix+'_roof_side_'+str(sign),[.0002,.0041,.000375],
              [x+sign*.00085,y,.024325],rgba=[0,0,0,0])
        w.box(parent,prefix+'_roof_end_'+str(sign),[.001775,(.0041-.001775)/2,.00105],
              [x,y+sign*(.0041+.001775)/2,.02575],rgba=[0,0,0,0])
    for i in range(24):
        angle=2*np.pi*i/24;r=(.0014+.001775)/2
        w.box(parent,prefix+'_counterbore_'+str(i),[(.001775-.0014)/2,np.pi*r/24*1.02,.00105],
              [x+r*np.cos(angle),y+r*np.sin(angle),.02575],rgba=[0,0,0,0],euler=vec([0,0,angle]))
    w.box(parent,prefix+'_back',[.00105,.00065,.0012],
          [x,y-side*.00345,entry[2]],rgba=[0,0,0,0])
    screw=ET.SubElement(parent,'body',name=prefix+'_screw',pos=vec(screw_origin))
    ET.SubElement(screw,'joint',name=prefix+'_advance',type='slide',axis='0 0 1',range='-.0022 0',
                  damping='.01',solreflimit='.001 1',solimplimit='.9999 .9999 .00001')
    ET.SubElement(screw,'joint',name=prefix+'_turn',type='hinge',axis='0 0 1',limited='false',
                  damping='.000002',frictionloss=str(FRICTION_TORQUE if friction else 0),
                  solreffriction='.001 1',solimpfriction='.9999 .9999 .00001')
    # Exact circular base plus two circular-segment cheeks leave the measured
    # reconstructed 0.45 mm slot open. The selected bit is 0.32 mm thick.
    w.cylinder(screw,prefix+'_head_floor',.00128,.0003,[0,0,-.0001],rgba=[0,0,0,0],mass='.000032')
    for side_y in [-1,1]:
        angles=np.linspace(np.arcsin(.000225/.00128),np.pi-np.arcsin(.000225/.00128),17)
        xy=np.array([[.00128*np.cos(a),side_y*.00128*np.sin(a)] for a in angles])
        points=np.array([[*p,h] for h in [.0002,.0004] for p in xy])
        mesh=prefix+'_slot_cheek_'+str(side_y)
        ET.SubElement(w.assets,'mesh',name=mesh,vertex=vec(points.ravel()))
        ET.SubElement(screw,'geom',name=mesh,type='mesh',mesh=mesh,mass='.000006',rgba='0 0 0 0',
                      friction='.3 .00001 .000001',solref='.0005 1',solimp='.9999 .9999 .00001')
    # The captive plate translates with the screw but does not turn on the
    # conductor. This is a declared ideal bearing/capture constraint.
    plate=ET.SubElement(parent,'body',name=prefix+'_plate',pos=vec([x,side*.0365,.0236]))
    ET.SubElement(plate,'joint',name=prefix+'_plate_slide',type='slide',axis='0 0 1',limited='false',damping='.01')
    w.box(plate,prefix+'_pressure_plate',[.001,.0015,.0003],rgba=[0,0,0,0],mass='.00015',
          contype='1' if clamp else '0',conaffinity='1' if clamp else '0',
          solref='.0005 1',solimp='.9999 .9999 .00001',friction='.5 .00001 .000001')
    equality=w.root.find('equality')
    if equality is None:equality=ET.SubElement(w.root,'equality')
    ET.SubElement(equality,'joint',name=prefix+'_thread',joint1=prefix+'_turn',joint2=prefix+'_advance',
                  polycoef=vec([0,2*np.pi/PITCH,0,0,0]),solref='.0005 1',solimp='.9999 .9999 .00001')
    ET.SubElement(equality,'joint',name=prefix+'_captive_plate',joint1=prefix+'_plate_slide',joint2=prefix+'_advance',
                  polycoef='0 1 0 0 0',solref='.0005 1',solimp='.9999 .9999 .00001')
    if visual:
        visuals(w,screw,'mcc_usb_tc',prefix=prefix+'_visual',only=[t['parts'][n] for n in ['screw','shank']],origin=screw_origin)
        visuals(w,plate,'mcc_usb_tc',prefix=prefix+'_plate_visual',only=[t['parts']['clamp']],origin=[x,side*.0365,.0236])
    return dict(**t,prefix=prefix,wire_floor_m=floor,thread_pitch_m=PITCH,
                selected_thread_friction_Nm=FRICTION_TORQUE if friction else 0,
                selected_wire_diameter_m=WIRE_DIAMETER,
                selected_extension_AWG=24,selected_wire_density_kg_m3=WIRE_DENSITY,
                inference='Ideal helical thread and captive nonrotating plate; selected dimensions/friction, not measured USB-TC mechanics')


def add_driver(w,parent,prefix='driver',visual=True,bit=True):
    """Motorized bit inside a retained handle; no motor acts on the terminal."""
    rotor=ET.SubElement(parent,'body',name=prefix+'_rotor')
    ET.SubElement(rotor,'joint',name=prefix+'_spin',type='hinge',axis='0 0 1',limited='false',damping='.00001',armature='.0000001')
    w.cylinder(rotor,prefix+'_shaft',.0011,.018,[0,0,.0187],[.5,.52,.54,1] if visual else [0,0,0,0],mass='.002')
    w.box(rotor,prefix+'_bit',[.0011,.00016,.00035],[0,0,.00035],
          [.62,.64,.66,1] if visual else [0,0,0,0],mass='.00002',contype='1' if bit else '0',conaffinity='1' if bit else '0',
          solref='.0005 1',solimp='.9999 .9999 .00001',friction='.3 .00001 .000001')
    ET.SubElement(rotor,'site',name=prefix+'_tip',pos='0 0 0',size='.0001')
    actuators=w.root.find('actuator')
    if actuators is None:actuators=ET.SubElement(w.root,'actuator')
    ET.SubElement(actuators,'velocity',name=prefix+'_motor',joint=prefix+'_spin',kv='.001',
                  ctrlrange='-4 4',forcerange='-.003 .003')
    return rotor
