"""A robot handles the bonded outer annulus of the deformable two-sheet cover."""
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP,vec
from source_parts import moving_part
from membrane import sheet

PARK=np.array([.34,-.20,TOP+.1432])
TARGET=np.array([.48,.14,TOP+.1307])
SIDE=np.array([[1.,0,0],[0,0,1.],[0,-1.,0]])


def build(path):
    w=World()
    # Retain elliptic Coulomb friction; omit the expensive no-slip
    # postprocessor after comparing recorded-state support and cloth strain.
    w.root.find('option').attrib.update(timestep='.0005',impratio='10',noslip_iterations='0',iterations='100')
    ET.SubElement(w.root,'size',memory='256M')
    support=w.body('tube_support',[.48,.14,TOP],False)
    w.cylinder(support,'support_base',.08,.03525,[0,0,.03525],[.2,.25,.3,1])
    w.ring(support,'tube_wall',.038,.051,.057,.099,rgba=[.85,.85,.80,1])
    stand=w.body('cover_stand',[.34,-.20,TOP],False)
    w.cylinder(stand,'stand_base',.08,.009,[0,0,.009],[.2,.25,.3,1])
    for i in range(3):
        a=np.pi/2+i*2*np.pi/3
        w.cylinder(stand,'stand_post_'+str(i),.003,.07,[.0585*np.cos(a),.0585*np.sin(a),.07],[.2,.25,.3,1])
    body=w.body('cover',PARK)
    w.ring(body,'spacer_wall',.0535,.0635,.0064,mass=np.pi*(.0635**2-.0535**2)*.0064*2700)
    moving_part(w,body,'cover')
    props=[sheet(body,'cover_lower',-.003208),sheet(body,'cover_upper',.003208)]
    w.cylinder(body,'bonded_mass',.0001,.0001,mass=str(sum(p['mass_on_parent_kg'] for p in props)),contype='0',conaffinity='0',rgba=[0,0,0,0])
    ET.SubElement(body,'site',name='cover_grasp',pos='0 -.063 0',size='.001')
    w.save(path)
    return props
