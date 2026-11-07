"""One persistent cooler world: six rigid layers plus a deformable cover."""
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP
from continuous_world import build as build_layers,CENTER,STACK_PLANE
from source_parts import moving_part
from membrane import sheet


def build(path):
    targets=build_layers(path)
    w=World();w.root=ET.parse(path).getroot();w.w=w.root.find('worldbody');w.assets=w.root.find('asset')
    w.mesh_names={m.get('file').removeprefix('equipment/'):m.get('name') for m in w.assets.findall('mesh') if m.get('file','').startswith('equipment/')}
    w.root.find('option').attrib.update(timestep='.0005',noslip_iterations='1',iterations='100')
    # Native automatic sleep only; no body is initialized asleep. Contact
    # wakes an island automatically. Acceptance uses an all-awake observer.
    ET.SubElement(w.root.find('option'),'flag',sleep='enable')
    # Leave the horizontal cover-gripper corridor clear. The rigid-only
    # fixture's centred regrasp pedestal occupied the Panda hand envelope.
    regrasp=w.root.find("worldbody/body[@name='emitter_regrasp_stand']")
    regrasp.set('pos',f'.58 -.04 {TOP}')
    targets['emitter']['regrasp'][:2]=[.58,-.04]
    park=np.array([.19,-.26,TOP+.1432]);target=CENTER+[0,0,STACK_PLANE+.057+.0032]
    stand=w.body('cover_stand',[*park[:2],TOP],False)
    for i in range(3):
        angle=np.pi/2+i*2*np.pi/3
        pos=[.0585*np.cos(angle),.0585*np.sin(angle),.070]
        w.cylinder(stand,'cover_stand_post_'+str(i),.003,.070,pos,[.06,.4,.52,1])
        w.cylinder(stand,'cover_stand_foot_'+str(i),.007,.002,[*pos[:2],.002],[.06,.4,.52,1])
    cover=w.body('cover',park)
    w.ring(cover,'spacer_wall',.0535,.0635,.0064,mass=np.pi*(.0635**2-.0535**2)*.0064*2700)
    moving_part(w,cover,'cover')
    props=[sheet(cover,'cover_lower',-.003208),sheet(cover,'cover_upper',.003208)]
    w.cylinder(cover,'bonded_mass',.0001,.0001,mass=str(sum(p['mass_on_parent_kg'] for p in props)),contype='0',conaffinity='0',rgba=[0,0,0,0])
    ET.SubElement(cover,'site',name='cover_grasp',pos='0 -.0595 0',size='.001')
    # Explicit selected clearance: the 0.25 mm collision envelopes on each
    # film must not intersect the aperture underside. This adds 0.5 mm to
    # the inferred shield shims; source-sized shield and plate stay unchanged.
    for geom in w.root.findall(".//geom"):
        if geom.get('name','').startswith('shield_height_shim_'):
            p=np.fromstring(geom.get('pos'),sep=' ');p[2]+=.00025
            geom.set('pos',' '.join(map(str,p)));geom.set('size','.002 .00345')
    for name in ['shield','aperture']:targets[name]['assembled'][2]+=.0005
    targets['cover']=dict(park=park.tolist(),assembled=target.tolist(),support='pe_tube',film_properties=props)
    w.save(path)
    return targets
