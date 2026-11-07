"""Source-sized, independently movable cooler layers in one persistent world.

The extended edge jaws, parking nests and assembly alignment pins are explicit
robot tooling inferences. Nothing is welded to the payload or teleported at
runtime. Hollow parts use open collision rings, never convex mesh hulls.
"""
import json
import xml.etree.ElementTree as ET
import numpy as np
from world import World, TOP, vec
from source_parts import moving_part,fixed_frame

CENTER=np.array([.48,.12,TOP])
STACK_PLANE=.0705
PARTS={
    # Selected 25 kg/m3 XPS plus a foil-wrap allowance, about 1.4 g per disk.
    # Density and wrap mass remain inferred, not measured historical values.
    'foam_lower':dict(radius=.025,height=.025,z=.0125,mass=.0014,park=[.32,-.25],grasp=[0,0,.004],width=.050),
    'foam_upper':dict(radius=.025,height=.025,z=.0375,mass=.0014,park=[.43,-.25],grasp=[0,0,.004],width=.050),
    'emitter':dict(radius=.025,height=.0005,z=.05025,mass=.0088,park=[.56,-.25],grasp=[0,0,-.0001],width=.050),
    'pe_tube':dict(inner=.038,radius=.051,height=.057,z=.0285,mass=.197,park=[.69,-.24],grasp=[0,-.0445,.020],width=.013),
    'shield':dict(inner=.070,radius=.076,height=.057,z=.0349,mass=.424,park=[.35,-.42],grasp=[0,-.073,-.010],width=.006),
    'aperture':dict(inner=.025,radius=.076,height=.001,z=.0639,mass=.0437,park=[.56,-.43],grasp=[0,-.0505,0],width=.051),
}


def build(path):
    w=World()
    w.root.find('option').set('impratio','10')
    w.root.find('option').set('noslip_iterations','3')
    ET.SubElement(w.root,'size',memory='256M')
    # Same gripper joints and +/-40 N actuator bound; switch its controller
    # interface to force so a thin wall can receive a controlled clamp load.
    # Position-only closure at a 6 mm wall supplied too little normal force.
    w.root.find("actuator/general[@name='actuator8']").attrib.update(
        gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    # Replaceable extended tips keep the stock finger bodies above thin parts.
    # Their 3 mm vertical edge pad permits side contact with the 0.5 mm disk.
    # Mass/inertia includes an inferred 10 g tip per finger.
    w.root.find(".//site[@name='tcp']").set('pos','0 0 .1484')
    for side in ['left_finger','right_finger']:
        finger=w.root.find(".//body[@name='"+side+"']")
        inertial=finger.find('inertial')
        inertial.set('mass','.025')
        inertial.set('pos','0 .003 .028')
        inertial.set('diaginertia','0.000025 0.000025 0.000001')
        w.box(finger,side+'_edge_stem',[.006,.004,.018],[0,.005,.070],rgba=[.17,.23,.28,1],mass='.009')
        w.box(finger,side+'_edge_tip',[.006,.003,.0015],[0,.003,.090],rgba=[.06,.48,.55,1],mass='.001',
              friction='1.4 .01 .006',condim='6')
    base=w.body('assembly_base',CENTER,False)
    fixed_frame(w,base)
    # The previously authored visual stack floated the 57 mm shield 6.4 mm
    # above its support. These visible, explicit inferred shims carry its load.
    # The PE height is itself an inference; this is a selected robot fixture,
    # not a claim that these shims existed in the historical apparatus.
    for i in range(3):
        a=np.pi/6+i*2*np.pi/3
        w.cylinder(base,'shield_height_shim_'+str(i),.002,.0032,
                   [.073*np.cos(a),.073*np.sin(a),STACK_PLANE+.0032],[.06,.4,.52,1])
    for i in range(6):
        a=i*np.pi/3
        w.cylinder(base,'shield_alignment_pin_'+str(i),.002,.010,
                   [.0785*np.cos(a),.0785*np.sin(a),STACK_PLANE+.010],[.06,.4,.52,1])
    w.ring(base,'alignment',.0256,.029,.006,STACK_PLANE+.003,rgba=[.06,.4,.52,1])
    for i in range(4):
        a=np.pi/4+i*np.pi/2
        w.cylinder(base,'alignment_pin_'+str(i),.0015,.018,[.0275*np.cos(a),.0275*np.sin(a),STACK_PLANE+.018],rgba=[.06,.4,.52,1])
    targets={}
    # The stack grasp must stay above the foam. A raised regrasp support lets
    # the robot recenter its edge pads after removal, without airborne grasp
    # attachment, payload pose edits, or pinching the foam under the disk.
    regrasp_pos=np.array([.48,-.055,TOP+STACK_PLANE+.05025])
    regrasp=w.body('emitter_regrasp_stand',[.48,-.055,TOP],False)
    w.cylinder(regrasp,'emitter_regrasp_support',.016,(STACK_PLANE+.05)/2,
               [0,0,(STACK_PLANE+.05)/2],[.06,.4,.52,1])
    for name,p in PARTS.items():
        park=np.array([*p['park'],TOP+.012+p['height']/2])
        nest=w.body(name+'_stand',[*p['park'],TOP],False)
        # Supports are below the part; the jaws can reach its allowed rim.
        if 'inner' in p:
            for i in range(3):
                a=np.pi/6+i*2*np.pi/3;r=(p['inner']+p['radius'])/2
                w.cylinder(nest,name+'_parking_support_'+str(i),min(.004,(p['radius']-p['inner'])/3),.006,
                           [r*np.cos(a),r*np.sin(a),.006],[.16,.23,.29,1])
        else:w.cylinder(nest,name+'_parking_support',p['radius']*.65,.006,[0,0,.006],[.16,.23,.29,1])
        b=w.body(name,park)
        color=[.5,.28,.40,1] if name.startswith('foam') else [.88,.87,.82,1] if name in ['emitter','pe_tube'] else [.67,.70,.74,1]
        if 'inner' in p:w.ring(b,name+'_wall',p['inner'],p['radius'],p['height'],rgba=color,mass=p['mass'])
        else:w.cylinder(b,name+'_solid',p['radius'],p['height']/2,rgba=color,mass=str(p['mass']))
        if name=='emitter':
            w.cylinder(b,'emitter_paint',.025,.00003,[0,0,.00028],[.91,.91,.88,1],mass='0',contype='0',conaffinity='0')
        moving_part(w,b,name)
        ET.SubElement(b,'site',name=name+'_grasp',pos=vec(p['grasp']),size='.001')
        targets[name]=dict(park=park.tolist(),assembled=(CENTER+[0,0,STACK_PLANE+p['z']]).tolist(),
                           support='foam_lower' if name=='foam_upper' else 'foam_upper' if name=='emitter' else 'shield' if name=='aperture' else 'assembly_base')
        if name=='emitter':targets[name]['regrasp']=regrasp_pos.tolist()
    # Source visual context, kept outside the robot's working volume.
    daq=w.body('source_usb_tc',[.22,.48,TOP],False)
    w.original(daq,'MCC_USB_TC',prefix='continuous_daq')
    w.save(path)
    return targets
