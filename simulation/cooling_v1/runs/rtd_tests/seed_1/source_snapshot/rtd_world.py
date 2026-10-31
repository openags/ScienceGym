"""Manufacturer-sized RTD, drilled copper bore and an attached flexible cable."""
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP,vec
from device_assets import visuals

PARK=np.array([.36,-.26,TOP+.025])
TARGET=np.array([.52,.13,TOP+.0438])


def cable_points():
    start=np.array([0,0,.1222]);end=np.array([.29,-.18,-.022])
    # Smooth routed lead from the probe exit down to an initially coiled
    # cable on the bench. This is a selected staging pose, not a source fact.
    a=start+[.10,0,.02];b=end+[-.10,0,.04]
    route=np.array([(1-u)**3*start+3*(1-u)**2*u*a+3*(1-u)*u*u*b+u**3*end for u in np.linspace(0,1,18)])
    length=float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum());remaining=3.6576-length
    radius=.09;pitch=.007;segments=100
    def coil(turns):
        u=np.linspace(0,turns,segments+1);theta=-np.pi/2+2*np.pi*u
        return np.c_[.29+radius*np.cos(theta),-.09+radius*np.sin(theta),-.022+pitch*u]
    low,high=0.,12.
    for _ in range(60):
        mid=(low+high)/2
        if np.linalg.norm(np.diff(coil(mid),axis=0),axis=1).sum()<remaining:low=mid
        else:high=mid
    return np.vstack([route,coil((low+high)/2)[1:]])


def build(path,bore_diameter=.0066):
    w=World();w.root.find('option').attrib.update(timestep='.001',impratio='5',noslip_iterations='0',iterations='100')
    # Keep sleep disabled for the elasticity-plugin cable: this engine build
    # raised mj_wakeIsland on the initial forward pass with sleep enabled.
    # The failed run is retained in the workcell history.
    ext=ET.SubElement(w.root,'extension');ET.SubElement(ext,'plugin',plugin='mujoco.elasticity.cable')
    actuator=w.root.find("actuator/general[@name='actuator8']")
    actuator.attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    probe=w.body('rtd',PARK)
    visual=ET.SubElement(probe,'body',name='rtd_source_geometry',euler='0 -1.57079632679 0')
    visuals(w,visual,'omega_pm_rtd',only=['immersion_sheath','closed_tip','thread_core','thread_crest_visual','hex_grip','cable_transition','strain_relief'])
    w.cylinder(probe,'rtd_sheath',.003175,.0381,[0,0,.0381],rgba=[0,0,0,0],mass='.012')
    w.cylinder(probe,'rtd_thread_envelope',.0106,.0075,[0,0,.0837],rgba=[0,0,0,0],mass='.025')
    verts=[]
    for z in [.0912,.0972]:
        for i in range(6):
            theta=i*np.pi/3;verts.extend([.0146647*np.cos(theta),.0146647*np.sin(theta),z])
    ET.SubElement(w.assets,'mesh',name='rtd_hex_collision',vertex=vec(verts))
    ET.SubElement(probe,'geom',name='rtd_hex',type='mesh',mesh='rtd_hex_collision',mass='.016',rgba='0 0 0 0',friction='1 .005 .0001')
    w.cylinder(probe,'rtd_transition',.0048,.0095,[0,0,.1067],rgba=[0,0,0,0],mass='.009')
    ET.SubElement(probe,'site',name='rtd_grasp',pos='0 0 .0942',size='.001')
    points=cable_points()
    composite=ET.SubElement(probe,'composite',prefix='rtd_lead_',type='cable',vertex=vec(points.flatten()),initial='none')
    plugin=ET.SubElement(composite,'plugin',plugin='mujoco.elasticity.cable')
    for k,v in [('twist','1e6'),('bend','1e7'),('flat','false')]:ET.SubElement(plugin,'config',key=k,value=v)
    ET.SubElement(composite,'joint',kind='main',damping='.00005')
    ET.SubElement(composite,'geom',type='capsule',size='.002',density='1300',rgba='.025 .03 .035 1',friction='.3 .001 .0001',condim='3')
    stand=w.body('rtd_stand',[*PARK[:2],TOP],False)
    w.ring(stand,'rtd_stand_rim',.0035,.018,.008,z=.0972,rgba=[.1,.4,.5,1])
    for i in range(3):
        a=i*2*np.pi/3
        w.cylinder(stand,'rtd_stand_post_'+str(i),.003,.0466,[.014*np.cos(a),.014*np.sin(a),.0466],[.1,.4,.5,1])
    w.cylinder(stand,'rtd_stand_foot',.024,.003,[0,0,.003],[.1,.4,.5,1])
    block=w.body('calibration_block',[.52,.13,TOP+.04],False)
    hole=bore_diameter/2;half=.04;height=.08
    # Four rectangular wall pieces surround a thin circular bore insert.
    # The source does not specify block size or clearance; both are explicit
    # fixture selections. No convex mesh fills the insertion corridor.
    bore_outer=.006
    for sign in [-1,1]:
        w.box(block,'copper_x'+str(sign),[(half-bore_outer)/2,half,height/2],[sign*(half+bore_outer)/2,0,height/2],[.65,.34,.16,1])
        w.box(block,'copper_y'+str(sign),[bore_outer,(half-bore_outer)/2,height/2],[0,sign*(half+bore_outer)/2,height/2],[.65,.34,.16,1])
    w.ring(block,'copper_bore',hole,bore_outer,height-.002,z=(height+.002)/2,rgba=[.65,.34,.16,1],mass=.05)
    w.box(block,'bore_floor',[bore_outer,bore_outer,.001],[0,0,.001],[.65,.34,.16,1])
    pedestal=w.body('block_pedestal',[.52,.13,TOP],False)
    w.box(pedestal,'block_pedestal_top',[.045,.045,.02],[0,0,.02],[.16,.23,.3,1])
    w.save(path)
    return dict(probe_diameter_m=.00635,immersion_length_m=.0762,bore_diameter_m=hole*2,
                park_m=PARK.tolist(),target_m=TARGET.tolist(),cable_centerline_length_m=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),
                cable_segments=len(points)-1,bend_Pa=1e7,twist_Pa=1e6,
                inferred=['block envelope','bore clearance','fitting envelope and mass','effective cable density and stiffness','staging route'],
                source_asset='assets/omega_pm_rtd_v1',whole_calibration_validated=False)
