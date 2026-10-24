"""A selected passive, manually released solar-track carriage.

Paper dimensions are the 60 mm horizontal reflector and 1.5 mm track stock.
The captured guide, spring brake and 1:1 cam linkage are explicit fixture
inferences. Two passive sliders plus a polynomial joint constraint represent
the machined guide; the robot is the only actuator. No carriage pose commands
or attachment welds are used during execution.
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from world import World,TOP,vec

TASK=Path(__file__).resolve().parents[2]/'tasks/directional_cooling_operations_v3'
EMITTER=np.array([.48,.16,TOP+.12])
DISK_Z=EMITTER[2]+.15


def build(path,brake_enabled=True,release_blocked=False):
    solar=json.loads((TASK/'selected_solar_path.json').read_text())
    points=np.array([r['position_m'] for r in solar['samples']]);x0=float(points[0,0]);y0=float(points[0,1])
    # MuJoCo joint equality supports a quartic. Check the approximation
    # against every ephemeris point before constructing the physical guide.
    coefficients=np.polynomial.polynomial.polyfit(points[:,0]-x0,points[:,1]-y0,4)
    residual=float(np.max(abs(np.polynomial.polynomial.polyval(points[:,0]-x0,coefficients)-(points[:,1]-y0))))
    if residual>1e-5:raise ValueError('Selected guide exceeds 10 micrometre fit allowance')
    w=World();w.root.find('option').attrib.update(timestep='.001',impratio='10',noslip_iterations='2',iterations='100')
    w.root.find("actuator/general[@name='actuator8']").attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    rail=w.body('track',EMITTER,False);height=.15-.008
    # A contiguous visual and collision ribbon, separate convex segments.
    # All brake surfaces are real contact geometry with friction.
    samples=np.linspace(points[-1,0]-.025,points[0,0]+.025,101)
    ys=y0+np.polynomial.polynomial.polyval(samples-x0,coefficients)
    for i in range(len(samples)-1):
        a=np.array([samples[i],ys[i]]);b=np.array([samples[i+1],ys[i+1]]);delta=b-a;center=(a+b)/2
        w.box(rail,'track_ribbon_'+str(i),[np.linalg.norm(delta)/2+.00002,.003,.00075],
              [*center,height],[.58,.62,.66,1],euler=vec([0,0,np.arctan2(delta[1],delta[0])]),friction='.8 .001 .0001')
    # The declared datum is measured from the emitter, not from the table.
    stand=w.body('track_support',[*EMITTER[:2],TOP],False)
    for sign in [-1,1]:
        x=sign*.105;y=float(y0+np.polynomial.polynomial.polyval(x-x0,coefficients))
        w.cylinder(stand,'support_rod_'+str(sign),.007,(DISK_Z-TOP-.008)/2,[x,y,(DISK_Z-TOP-.008)/2],[.4,.45,.5,1])
        w.box(stand,'support_foot_'+str(sign),[.018,.018,.003],[x,y,.003],[.14,.22,.28,1])
        w.box(stand,'track_end_clamp_'+str(sign),[.006,.006,.0025],[x,y,DISK_Z-TOP-.010],[.14,.22,.28,1])
    emitter=w.body('emitter_datum',EMITTER,False)
    w.cylinder(emitter,'emitter_datum_surface',.025,.00025,[0,0,-.00025],rgba=[.93,.93,.9,1])
    w.cylinder(emitter,'emitter_pedestal',.025,.060,[0,0,-.060],[.15,.23,.29,1])
    carriage=w.body('carriage',[EMITTER[0]+x0,EMITTER[1]+y0,DISK_Z-.003],False)
    for name,axis,limits in [('carriage_x','1 0 0',[-.166,.003]),('carriage_y','0 1 0',[-.015,.003])]:
        ET.SubElement(carriage,'joint',name=name,type='slide',axis=axis,range=vec(limits),damping='.1',frictionloss='.002')
    for sign in [-1,1]:
        w.box(carriage,'carriage_bridge_side_'+str(sign),[.00075,.012,.0015],[sign*.00525,0,-.0015],[.12,.2,.27,1],mass='.00375')
        w.box(carriage,'carriage_bridge_end_'+str(sign),[.0045,.0015,.0015],[0,sign*.0105,-.0015],[.12,.2,.27,1],mass='.00375')
    # Clear the rail under the bridge. The passive guide coordinates enforce
    # capture; underside skids and the spring shoe describe the real assembly.
    for sign in [-1,1]:
        w.box(carriage,'guide_cheek_'+str(sign),[.006,.0015,.004],[0,sign*.007,-.003],[.2,.28,.34,1],mass='.002')
    w.cylinder(carriage,'reflector_disk',.03,.0005,[0,0,.003],[.83,.86,.89,1],mass='.00763')
    # Narrow grasp pedestal above the disk; the upper optical face is never
    # used as the grasping surface.
    w.cylinder(carriage,'grasp_mount_stem',.003,.0065,[0,0,.0095],[.23,.3,.35,1],mass='.001')
    w.box(carriage,'grasp_fixed_face',[.005,.002,.016],[0,-.007,.032],[.08,.42,.49,1],mass='.011')
    w.box(carriage,'grasp_web',[.005,.008,.0015],[0,0,.016],[.08,.42,.49,1],mass='.003')
    ET.SubElement(carriage,'site',name='carriage_grasp',pos='0 -.0015 .032',size='.001')
    lever=ET.SubElement(carriage,'body',name='retainer_button',pos='0 .007 .032')
    ET.SubElement(lever,'joint',name='retainer_travel',type='slide',axis='0 -1 0',range='-.003 .0001' if release_blocked else '-.003 .004',damping='.2')
    w.box(lever,'retainer_button_face',[.005,.002,.012],rgba=[.8,.4,.08,1],mass='.006')
    for sign in [-1,1]:
        w.cylinder(lever,'retainer_guide_'+str(sign),.0005,.006,[sign*.003,-.006,-.004],[.55,.6,.64,1],euler='1.57079632679 0 0',mass='.0002')
    brake=ET.SubElement(carriage,'body',name='brake_shoe')
    ET.SubElement(brake,'joint',name='brake_lift',type='slide',axis='0 0 1',range='-.003 .004',damping='.2',stiffness='1000' if brake_enabled else '0',springref='-.003')
    # Track top is DISK_Z - 7.25 mm, shoe bottom shares that datum at q=0.
    w.box(brake,'brake_pad',[.004,.002,.001],[0,0,-.00325],[.12,.13,.15,1],mass='.003',friction='.8 .001 .0001',condim='4')
    equality=w.root.find('equality')
    ET.SubElement(equality,'joint',name='captured_track_profile',joint1='carriage_y',joint2='carriage_x',polycoef=vec(coefficients),solref='.002 1',solimp='.9999 .9999 .00001')
    ET.SubElement(equality,'joint',name='passive_release_cam',joint1='brake_lift',joint2='retainer_travel',polycoef='0 1 0 0 0',solref='.002 1',solimp='.9999 .9999 .00001')
    # The default soft joint stop compressed by millimetres under the test
    # grip, letting a deliberately blocked retainer appear to release. Use a
    # stiff, declared stop model and verify maximum stop penetration offline.
    for name in ['carriage_x','carriage_y','retainer_travel','brake_lift']:
        w.root.find(f".//joint[@name='{name}']").attrib.update(solreflimit='.002 1',solimplimit='.9999 .9999 .00001')
    w.save(path)
    return dict(source_solar_path_sha256=hashlib.sha256((TASK/'selected_solar_path.json').read_bytes()).hexdigest(),
                emitter_origin_m=EMITTER.tolist(),reflector_height_m=.15,reflector_diameter_m=.06,
                track_thickness_m=.0015,guide_reference_xy_m=[x0,y0],guide_coefficients=coefficients.tolist(),
                max_guide_fit_error_m=residual,brake_stiffness_N_m=1000 if brake_enabled else 0,brake_preload_m=.003,
                selected_cam_ratio=1.,robot_only_actuation=True,whole_paper_validated=False,
                brake_enabled=brake_enabled,release_blocked=release_blocked,
                limitations=['Captured-guide and cam joint relations are selected ideal mechanism models',
                             'Fixture dimensions, friction, spring and grasp pedestal are inferred',
                             'Internal guide bushings and release cam use ideal joint relations; wear and elastic fixture deflection are not modeled',
                             'This world starts with track and disk mounted; it cannot qualify their installation'])
