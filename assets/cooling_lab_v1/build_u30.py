"""Source-guided U30 enclosure and interfaces; static inspection candidate."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from shapely.geometry import Polygon
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review,cad_mesh
from build_weather_assets import cable_mesh

WHITE=[222,223,211];DARK=[33,37,37];STEEL=[169,179,185];BRASS=[164,134,63]
BOTTOM=10.7;TOP=188.7;HINGE=(-86.3,10.)


def box(size,centre):return cq.Workplane('XY').box(*size).val().translate(centre)
def cyl(r,h,start,axis=(0,0,1)):return cq.Solid.makeCylinder(r,h,cq.Vector(*start),cq.Vector(*axis))
def rounded_xz(w,h,d,centre,r):
    return cq.Workplane('XY').box(w,d,h).edges('|Y').fillet(r).val().translate(centre)


def enclosure(g):
    body=rounded_xz(159,178,104.1,(0,62.05,99.7),9)
    cavity=rounded_xz(153,172,105,(0,58.6,99.7),6)
    body=body.cut(cavity)
    # One through-slot and one retained factory knockout in the selected
    # five-port configuration; an expander is not silently installed.
    body=body.cut(box((110,12,10),(-3,29,12)))
    body=body.cut(box((110,12,8),(-3,47,15.2)))
    body=body.cut(cyl(4,10,(65,38,8)))
    for x in [-62,56]:
        body=body.fuse(cyl(4.5,6,(x,20.5,BOTTOM)))
        body=body.cut(cyl(2.55,9,(x,20.5,9)))
        insert=cyl(2.5,6,(x,20.5,BOTTOM)).cut(cyl(1.95,8,(x,20.5,10)))
        solid(g,'channel_insert_'+str(x),insert,BRASS,metal=.7,role='selected_thread_envelope')
    for x in [-59,59]:
        for z in [25.4,174.]:
            body=body.fuse(cyl(5,4,(x,114.1,z),(0,1,0)))
            body=body.cut(cyl(1.8,7,(x,112.3,z),(0,1,0)))
    for x in [-61,61]:
        for z in [91,172]:
            body=body.fuse(cyl(4.5,58.3,(x,53,z),(0,1,0)))
            body=body.cut(cyl(2.55,9,(x,52,z),(0,1,0)))
            insert=cyl(2.5,8,(x,53,z),(0,1,0)).cut(cyl(1.55,10,(x,52,z),(0,1,0)))
            solid(g,'logger_case_insert_'+str(x)+'_'+str(z),insert,BRASS,metal=.7,role='selected_thread_envelope')
    # Authored battery bay supports the selected sealed package from below;
    # its position follows the manufacturer's replacement-access diagram.
    body=body.fuse(box((108,55.2,2),(0,83.7,31)))
    for x in [-53,53]:body=body.fuse(box((2,55.2,18.5),(x,83.7,22.95)))
    for x in [-56,56]:
        body=body.fuse(cyl(4.5,53.2,(x,58.1,79.5),(0,1,0)))
        body=body.cut(cyl(1.65,10,(x,57.1,79.5),(0,1,0)))
    door=rounded_xz(159,178,7.5,(0,5.75,99.7),9)
    door=door.cut(rounded_xz(153,172,8,(0,9,99.7),6))
    for x in [-51,51]:
        door=door.fuse(box((2.5,2,166),(x,1,99.7)))
        for z in [52,146]:door=door.fuse(box((23,2,2.5),(x+np.sign(x)*12,1,z)))
    for index,z in enumerate([50,145]):
        for lo,hi in [(-17,-7),(7,17)]:
            barrel=cyl(4,hi-lo,(*HINGE,z+lo)).cut(cyl(1.6,hi-lo+2,(*HINGE,z+lo-1)))
            web=box((8,8,hi-lo),(-82,14,z+(lo+hi)/2))
            body=body.fuse(barrel.fuse(web).cut(cyl(1.6,hi-lo+2,(*HINGE,z+lo-1))))
        barrel=cyl(4,13.6,(*HINGE,z-6.8)).cut(cyl(1.6,16,(*HINGE,z-8)))
        web=box((10,6,13.6),(-82,6,z))
        door=door.fuse(barrel.fuse(web).cut(cyl(1.6,16,(*HINGE,z-8))))
        solid(g,'hinge_pin_'+str(index+1),cyl(1.5,35,(*HINGE,z-17.5)),STEEL,metal=.8,role='hinge_pin')
        # An ordinary selected pivoting clasp: the front lip traps the door
        # hook until the clasp swings outward. Local profile is inferred.
        axis=(84.3,12.5)
        stem=box((6,5,6),(82,12.5,z)).fuse(cyl(2.5,6,(*axis,z-3)))
        body=body.fuse(stem.cut(cyl(1.1,8,(*axis,z-4))))
        door=door.fuse(box((7,4,12),(82,4,z)))
        # A selected 0.2 mm hook/lip gap permits rigid release without the
        # small interference that a zero-gap rotating lip otherwise creates.
        clasp=box((2.5,12,26),(89.05,9,z)).fuse(box((5.5,1.3,12),(87.55,1.15,z)))
        clasp=clasp.fuse(box((2.5,3.2,12),(89.05,3.4,z)))
        for lo,hi in [(-12,-8),(8,12)]:
            ear=cyl(2.5,hi-lo,(*axis,z+lo)).fuse(box((6,5,hi-lo),(87.3,12.5,z+(lo+hi)/2)))
            clasp=clasp.fuse(ear.cut(cyl(1.1,hi-lo+2,(*axis,z+lo-1))))
        clasp=clasp.cut(cyl(1.6,8,(85,7,z+9),(1,0,0)))
        solid(g,'latch_clasp_'+str(index+1),clasp,WHITE,role='inferred_pivoting_latch')
        solid(g,'latch_pin_'+str(index+1),cyl(1.,25,(*axis,z-12.5)),STEEL,metal=.8,role='latch_pin')
    solid(g,'outer_case',body,WHITE,role='outer_case')
    solid(g,'hinged_door',door,WHITE,role='hinged_door')
    gasket=rounded_xz(156.5,175.5,.4,(0,9.8,99.7),7.75).cut(rounded_xz(153.5,172.5,2,(0,9.8,99.7),6.25))
    solid(g,'door_perimeter_gasket',gasket,DARK,role='inferred_silicone_gasket')
    g.label('model_text','U30',.027,.015,[-.034,.0019,.164],WHITE,DARK)
    g.label('device_text','DATA LOGGER',.066,.018,[0,.0019,.137],WHITE,DARK)


def cable_channel(g):
    # The slit stops before the left end, leaving one continuous rubber hinge.
    shape=(cq.Workplane('XY',origin=(-3,29,BOTTOM)).rect(110,12).workplane(offset=6)
        .rect(109,10).loft(combine=True).val())
    shape=shape.cut(box((109.1,.05,10),(-2.45,29,13.7)))
    holes=[(-48,3.2)]+[(x,2.) for x in [-32,-18,-4,10,24,38]]
    for x,r in holes:shape=shape.cut(cyl(r,10,(x,29,9)))
    solid(g,'primary_split_rubber_channel',shape,DARK,role='inferred_EPDM_channel')
    for i,(x,r) in enumerate(holes):
        plug=cyl(r-.05,5.8,(x,29,10.8)).fuse(cyl(.6,16,(x,29,3.8)))
        solid(g,'unused_channel_plug_'+str(i+1),plug,DARK,role='inferred_rubber_plug')
    bar=box((126,5,2),(-3,20.5,9.7))
    for x in [-62,56]:bar=bar.cut(cyl(2.1,5,(x,20.5,7)))
    solid(g,'primary_channel_retaining_bar',bar,STEEL,metal=.75,role='inferred_channel_bar')
    for x in [-62,56]:
        shaft=cyl(1.9,7,(x,20.5,8.7));solid(g,'channel_screw_'+str(x),shaft,STEEL,metal=.8,role='selected_thread_envelope')
        knob=cyl(4.8,8.7,(x,20.5,0))
        for a in np.arange(12)*2*np.pi/12:knob=knob.cut(cyl(.6,10,(x+4.8*np.cos(a),20.5+4.8*np.sin(a),-.5)))
        knob=knob.cut(box((6,.8,1.2),(x,20.5,.5)))
        solid(g,'channel_thumb_knob_'+str(x),knob,DARK,role='inferred_thumb_head')
    vent=cyl(5.4,1.2,(65,38,9.5)).fuse(cyl(3.9,3,(65,38,10.7))).cut(cyl(3.2,6,(65,38,8.5)))
    solid(g,'vent_frame',vent,DARK,role='inferred_vent_frame')
    solid(g,'vent_membrane',cyl(3.2,.2,(65,38,10.8)),[169,174,164],role='inferred_vent_membrane')


def logger_module(g):
    # The sealed factory logger is a distinct removable assembly. Its local
    # component profiles are inferred, not a claim to reproduce its circuitry.
    base=rounded_xz(134,93,10,(0,48,131.5),5)
    base=base.cut(rounded_xz(131,90,12,(0,45.5,131.5),3.5))
    # Selected integral carriers support the external factory interfaces.
    # They are inferred construction, not an exact electronic-board layout.
    base=base.fuse(box((20,24,1.5),(56,32,69.65))).fuse(box((1.9,2,20.2),(65.05,44.1,79.)))
    base=base.fuse(box((12,15,7),(55,36.5,81.5)))
    left_carrier=box((16,14,24),(-57,37,73)).cut(box((8.1,2.2,5.1),(-57,31.05,73)))
    base=base.fuse(left_carrier)
    cover=rounded_xz(134,93,23,(0,31.5,131.5),5)
    cover=cover.cut(rounded_xz(130,89,24,(0,34,131.5),3))
    cover=cover.cut(box((10.4,9.4,9.2),(55,24.5,82.5)))
    centres=[-36,-18,0,18,36]
    for index,x in enumerate(centres):
        # Real downward-facing keyed mouth; its local clearance is selected
        # against the separately sourced 6P6C plug, not an Onset OEM drawing.
        jack=box((16,15,19),(x,29.5,77.5))
        jack=jack.cut(box((10.1,9,16),(x,30,75)))
        jack=jack.cut(box((3.7,5,11.7),(x,24,72.85)))
        cover=cover.cut(box((16.2,15.2,6),(x,29.5,86)))
        for pin in range(6):
            px=x+(pin-2.5)*1.02
            jack=jack.cut(box((.55,.6,8.4),(px,34.5,78.7)))
            solid(g,'sensor_jack_'+str(index+1)+'_contact_'+str(pin+1),box((.35,.2,8),(px,34.4,78.7)),BRASS,metal=.8,role='inferred_factory_contact')
        solid(g,'sensor_jack_'+str(index+1),jack,DARK,role='inferred_RJ12_receptacle')
    # Clear module fastening points are separate from the outer door hinge.
    for x in [-61,61]:
        for z in [91,172]:
            base=base.cut(cyl(1.65,66,(x,19,z),(0,1,0)))
            cover=cover.cut(cyl(1.8,26,(x,19,z),(0,1,0)))
            screw=cyl(1.5,39,(x,20,z),(0,1,0)).fuse(cyl(2.8,2,(x,18,z),(0,1,0)))
            screw=screw.cut(box((3.5,1.1,.65),(x,18.4,z))).cut(box((.65,1.1,3.5),(x,18.4,z)))
            solid(g,'logger_mount_screw_'+str(x)+'_'+str(z),screw,STEEL,metal=.8,role='selected_factory_fastener')
    for z in [158,164,170]:
        cover=cover.cut(cyl(1.35,5,(-20,19,z),(0,1,0)))
        solid(g,'inactive_status_lens_'+str(z),cyl(1.3,2,(-20,20,z),(0,1,0)),[39,57,42],role='inactive_indicator')
    # The NRC illustration has a ribbed feature below the status strip and
    # a distinct cover over the unused analog expansion opening. Its exact
    # material, internal purpose and local dimensions remain unverified.
    cover=cover.fuse(rounded_xz(42,38,1.5,(-30,19.25,135),3))
    for z in np.arange(119,152,3):cover=cover.fuse(box((36,1,1.1),(-30,18,z)))
    cover=cover.cut(box((32,7,44),(42,21.5,143)))
    blank=rounded_xz(42,52,3,(42,18.5,143),2)
    for x in [24,60]:
        cover=cover.fuse(cyl(2.5,5,(x,22,143),(0,1,0)))
        cover=cover.cut(cyl(1.3,10,(x,18,143),(0,1,0)))
        blank=blank.cut(cyl(1.35,5,(x,16,143),(0,1,0)))
        screw=cyl(1.25,8,(x,17,143),(0,1,0)).fuse(cyl(2.1,1.5,(x,15.5,143),(0,1,0)))
        screw=screw.cut(box((2.6,.9,.5),(x,15.8,143))).cut(box((.5,.9,2.6),(x,15.8,143)))
        solid(g,'analog_blank_screw_'+str(x),screw,STEEL,metal=.8,role='selected_factory_fastener')
    solid(g,'unused_analog_port_cover',blank,[177,187,183],role='inferred_factory_blank_cover')
    for name,z in [('LOG',170),('ALARM',164),('SENSOR',158)]:
        g.label('status_'+name+'_text',name,.022,.004,[-.004,.0199,z*.001],[195,206,201],DARK)
    solid(g,'logger_rear_tray',base,DARK,role='factory_logger_tray')
    g.add('logger_clear_cover',cad_mesh(cover),[190,208,206],alpha=155,role='factory_logger_cover')
    board=box((115,1.6,76),(0,49,132))
    solid(g,'internal_board_visual_envelope',board,[34,93,65],role='nonfunctional_factory_visual_envelope')
    # A modest board layout explains visible construction behind the cover;
    # these package envelopes are not simulated electronics or measured BOM.
    for i,(x,z,w,h) in enumerate([(-38,148,28,25),(-36,115,22,14),(9,154,25,18),(18,120,28,24)]):
        solid(g,'internal_package_visual_'+str(i+1),box((w,3,h),(x,46.7,z)),DARK,role='nonfunctional_factory_visual_envelope')
    solid(g,'sensor_port_carrier',box((100,27.9,1.6),(0,36.05,87.8)),[34,93,65],role='inferred_factory_port_carrier')
    solid(g,'usb_carrier_board',box((18,23,1.6),(55,31.5,71.2)),[34,93,65],role='inferred_factory_port_carrier')


def battery(g):
    # HRB-U30-S100 capacity and rear location are sourced. The unpublished
    # 102 x 50 x 94 mm package is an explicit local envelope hypothesis.
    solid(g,'sealed_battery_body',box((102,50,92),(0,83.1,78)),[69,73,72],role='inferred_sealed_battery_package')
    solid(g,'sealed_battery_lid',box((102,50,2),(0,83.1,125)),DARK,role='inferred_sealed_battery_lid')
    for index,x in enumerate([-35,35]):
        solid(g,'battery_terminal_insulator_'+str(index+1),box((8,8,2),(x,83.1,127)),[151,39,32] if index==0 else DARK,role='inferred_terminal_insulator')
        solid(g,'battery_terminal_'+str(index+1),box((4.8,.8,6),(x,83.1,131)),BRASS,metal=.8,role='inferred_battery_terminal')
    bar=box((120,3,9),(0,56.6,79.5))
    for x in [-56,56]:
        bar=bar.cut(cyl(1.7,5,(x,54.1,79.5),(0,1,0)))
        screw=cyl(1.5,11,(x,55.1,79.5),(0,1,0)).fuse(cyl(2.8,2,(x,53.1,79.5),(0,1,0)))
        screw=screw.cut(box((3.5,1.1,.65),(x,53.5,79.5))).cut(box((.65,1.1,3.5),(x,53.5,79.5)))
        solid(g,'battery_bar_screw_'+str(x),screw,STEEL,metal=.8,role='selected_thread_envelope')
    solid(g,'battery_retaining_bar',bar,STEEL,metal=.75,role='inferred_battery_retainer')


def mini_usb(g):
    # A source-dimensioned Mini-B interface reconstruction. GCT USB2066 is a
    # historical drawing reference, not an asserted Onset factory component.
    profile=Polygon([(-2.935,.5),(2.935,.5),(2.935,1.85),(3.45,2.35),(3.45,3.6),(-3.45,3.6),(-3.45,2.35),(-2.935,1.85)])
    def extrusion(poly,length,start=0):
        return cq.Workplane('XZ').polyline(list(poly.exterior.coords)[:-1]).close().extrude(-length).val().translate((0,start,0))
    shell=extrusion(profile.buffer(.4,resolution=8),9.2).cut(extrusion(profile,9.4,-.1))
    for side in [-1,1]:
        for y in [2.5,8.3]:shell=shell.fuse(box((1.95,2,.4),(side*3.975,y,.2)))
    shell=shell.cut(box((4.4,1.9,.7),(0,8.45,.25)))
    # Three selected integral tongues retain their rear sheet roots.
    for x,w in [(-2.5,.55),(0,1.6),(2.5,.55)]:
        for dx in [-w/2,w/2]:shell=shell.cut(box((.15,3.6,1),(x+dx,2.9,3.7)))
        shell=shell.cut(box((w+.15,.15,1),(x,1.1,3.7)))
    dielectric=extrusion(profile.buffer(-.05),3.35,5.85).fuse(box((4.6,5.35,1.2),(0,3.175,1.4)))
    for i in range(5):
        x=(i-2)*.8
        dielectric=dielectric.cut(box((.45,9.2,.6),(x,5.0,2.05)))
        dielectric=dielectric.cut(box((.45,3.6,2.1),(x,7.7,1.15)))
        contact=(cq.Workplane('YZ').polyline([(.5,1.8),(6.8,1.8),(8.7,.15),(9.4,.15),(9.4,.4),(8.8,.4),(6.9,2.05),(.5,2.05)])
            .close().extrude(.4).val().translate((x-.2,0,0)))
        solid(g,'usb_contact_'+str(i+1),contact.translate((55,20,72)),BRASS,metal=.8,role='inferred_Mini_B_contact')
    solid(g,'usb_mini_b_shell',shell.translate((55,20,72)),STEEL,metal=.8,role='source_dimensioned_Mini_B_interface')
    solid(g,'usb_mini_b_dielectric',dielectric.translate((55,20,72)),DARK,role='inferred_Mini_B_dielectric')


def power_interfaces(g):
    # Two-cavity front headers follow the manual photographs. Pitch, keying
    # and contacts are selected hypotheses; no OEM connector is identified.
    for prefix,z in [('external_power',82),('battery_input',65)]:
        body=box((10.5,8,6),(-57,26,z))
        for i,x in enumerate([-59.1,-54.9]):
            body=body.cut(box((3.5,6.1,3.5),(x,24.95,z)))
            solid(g,prefix+'_pin_'+str(i+1),box((.64,5,.64),(x,25.5,z)),BRASS,metal=.8,role='inferred_factory_contact')
        solid(g,prefix+'_header',body,WHITE,role='inferred_two_pole_header')
    holder=box((8,6,5),(-57,29,73)).cut(box((4.9,2.1,.9),(-57,27.05,73)))
    solid(g,'ground_tab_holder',holder,DARK,role='inferred_ground_interface')
    solid(g,'ground_connection_tab',box((4.8,10,.8),(-57,23,73)),BRASS,metal=.8,role='inferred_ground_interface')
    relay=box((10.2,9,9),(55,24.5,82.5))
    for i,x in enumerate([52.46,57.54]):
        relay=relay.cut(cyl(1.2,6,(x,25.7,77)))
        relay=relay.cut(cyl(1.4,6,(x,19.5,84.5),(0,1,0)))
        screw=cyl(1.3,4.8,(x,20.2,84.5),(0,1,0)).cut(box((2.3,.8,.5),(x,20.4,84.5)))
        solid(g,'unused_relay_terminal_screw_'+str(i+1),screw,STEEL,metal=.8,role='inferred_unused_relay_terminal')
    solid(g,'unused_relay_terminal_block',relay,[46,108,69],role='inferred_unused_relay_terminal')


def battery_lead(g):
    """Continuous selected insulated leads, with real terminal and plug voids."""
    plug=box((9.6,6,5.2),(-57,19,65))
    routes=[]
    for i,(x,finish,side_x,top,lower,color) in enumerate([(-35,-59.1,-73.5,142,61,[148,39,33]),(35,-54.9,-70.,149,69,DARK)]):
        boot=box((8,4,10),(x,83.1,133)).fuse(cyl(1.5,1,(x,83.1,138)))
        boot=boot.cut(box((5.3,1.3,6.3),(x,83.1,131.05))).cut(cyl(1.25,5.2,(x,83.1,134)))
        solid(g,'battery_spade_boot_'+str(i+1),boot,color,role='inferred_factory_wire_terminal')
        terminal=box((5.1,1.1,6),(x,83.1,131)).cut(box((4.85,.85,6.1),(x,83.1,130.95)))
        solid(g,'battery_female_spade_'+str(i+1),terminal,BRASS,metal=.8,role='inferred_factory_wire_terminal')
        nose=box((3.3,5,3.3),(finish,24.5,65))
        plug=plug.fuse(nose).cut(box((1.2,7.2,1.2),(finish,23.5,65)))
        plug=plug.cut(cyl(1.25,4.2,(finish,15.9,65),(0,1,0)))
        contact=box((1.1,7,1.1),(finish,23.5,65)).cut(box((.70,7.1,.70),(finish,23.55,65)))
        solid(g,'battery_plug_contact_'+str(i+1),contact,BRASS,metal=.8,role='inferred_factory_wire_terminal')
        nodes=np.array([[x,83.1,137],[x,83.1,141],[side_x+10,83.1,top],[side_x,60,112],[side_x,35,lower],[side_x+8,10,lower],[finish,16,65],[finish,20,65]],float)
        directions=np.array([[0,0,1],[0,0,1],[-1,-.2,-.3],[0,0,-1],[0,-1,0],[1,0,0],[0,1,0],[0,1,0]],float)
        directions/=np.linalg.norm(directions,axis=1)[:,None]
        handles=([(1.3,1.3),(17.836,5.985),(16.6,14.44),(8.738,30),(5.581,14.624),(5.138,4.097),(1.3,1.3)] if i==0 else
            [(1.3,1.3),(30,30),(22.976,15.312),(7.128,28.883),(5.581,14.624),(6.057,3.957),(1.3,1.3)])
        pieces=[]
        for j,(a,b) in enumerate(zip(nodes[:-1],nodes[1:])):
            la,lb=handles[j];c=a+directions[j]*la;d=b-directions[j+1]*lb;t=np.linspace(0,1,101)[:,None]
            curve=(1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*b
            pieces.append(curve if j==0 else curve[1:])
        path=np.vstack(pieces)*.001
        g.add('battery_insulated_lead_'+str(i+1),cable_mesh(path,.0012,[directions[0],directions[-1]]),color,role='authored_factory_lead_pose')
        routes.append(dict(id='battery_insulated_lead_'+str(i+1),points_m=path.tolist(),radius_m=.0012,
            measured_length_m=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum()),source_length_known=False))
    solid(g,'battery_two_pole_plug',plug,WHITE,role='inferred_two_pole_plug')
    return routes


def mast_mount(g):
    """Ordinary two-plate mounting kit; unpublished local profiles inferred."""
    half_spacing=52.324/2;rod_radius=7.9375/2
    mast_y=147.;arc_y=mast_y+20.5+.1-(half_spacing-rod_radius)
    for index,(plate_z,fix_z,bolt_z) in enumerate([(12.4,25.4,2.4),(187.,174.,197.)],1):
        prefix='mount_'+str(index)+'_'
        outline=[(-70,-18),(70,-18),(75,-13),(75,13),(70,18),(-70,18),(-75,13),(-75,-13)]
        plate=(cq.Workplane('XZ').polyline(outline).close().extrude(-3).val()
            .translate((0,118.1,plate_z)))
        for x in [-59,59]:
            plate=plate.cut(cyl(1.7,5,(x,117.1,fix_z),(0,1,0)))
            plate=plate.cut(cyl(3,2.8,(x,119.3,fix_z),(0,1,0)))
            screw=cyl(1.5,6,(x,113.3,fix_z),(0,1,0)).fuse(cyl(2.8,1.8,(x,119.3,fix_z),(0,1,0)))
            screw=screw.cut(box((3.5,1.1,.65),(x,120.7,fix_z))).cut(box((.65,1.1,3.5),(x,120.7,fix_z)))
            solid(g,prefix+'case_screw_'+str(x),screw,STEEL,metal=.8,role='inferred_mount_fastener')
        for x in [-half_spacing,half_spacing]:
            # Keyhole-like slots follow the source photograph. The wall
            # mounting centre spacing is sourced; slot profile is selected.
            plate=plate.cut(cyl(6.75,5,(x,117.1,bolt_z),(0,1,0)))
            toward_case=1 if index==1 else -1
            plate=plate.cut(box((8.4,5,8),(x,119.6,bolt_z+4*toward_case)))
        solid(g,prefix+'plate',plate,STEEL,metal=.8,role='inferred_source_mount_plate')
        wire=cq.Wire.assembleEdges([
            cq.Edge.makeLine(cq.Vector(-half_spacing,108.7,bolt_z),cq.Vector(-half_spacing,arc_y,bolt_z)),
            cq.Edge.makeThreePointArc(cq.Vector(-half_spacing,arc_y,bolt_z),cq.Vector(0,arc_y+half_spacing,bolt_z),cq.Vector(half_spacing,arc_y,bolt_z)),
            cq.Edge.makeLine(cq.Vector(half_spacing,arc_y,bolt_z),cq.Vector(half_spacing,108.7,bolt_z))])
        plane=cq.Plane(origin=(-half_spacing,108.7,bolt_z),normal=(0,1,0),xDir=(1,0,0))
        ub=cq.Workplane(plane).circle(rod_radius).sweep(wire).val()
        solid(g,prefix+'u_bolt',ub,STEEL,metal=.85,role='inferred_source_mount_u_bolt')
        xs=np.linspace(-32,32,257)
        back=np.minimum(135,mast_y-np.sqrt(np.maximum(0,20.55**2-xs**2)))
        outline=[(-32,121.1),(32,121.1)]+list(zip(xs[::-1],back[::-1]))
        saddle=cq.Workplane('XY').polyline(outline).close().extrude(14).val().translate((0,0,bolt_z-7))
        for side,x in [('left',-half_spacing),('right',half_spacing)]:
            saddle=saddle.cut(cyl(4.2,20,(x,120,bolt_z),(0,1,0)))
            washer=cyl(8,1.5,(x,116.6,bolt_z),(0,1,0)).cut(cyl(4.25,3,(x,116,bolt_z),(0,1,0)))
            solid(g,prefix+'washer_'+side,washer,STEEL,metal=.8,role='inferred_mount_fastener')
            nut=cq.Workplane('XY').polygon(6,12.7/np.cos(np.pi/6)).extrude(6.4).val().cut(cyl(4.1,8,(0,0,-.5)))
            nut=nut.rotate((0,0,0),(1,0,0),-90).translate((x,110.2,bolt_z))
            solid(g,prefix+'nut_'+side,nut,STEEL,metal=.8,role='inferred_mount_fastener')
        solid(g,prefix+'saddle',saddle,STEEL,metal=.8,role='inferred_source_mount_saddle')
    return dict(mast_axis_xy_m=[0,.147],selected_mast_diameter_m=.041,
        plate_centres_m=[[0,.1196,z] for z in [.0124,.187]],
        u_bolt_axes_z_m=[.0024,.197],selected_leg_centre_spacing_m=.052324,
        selected_rod_diameter_m=.0079375,selected_nut_AF_m=.0127,
        datum_limit='2.06 inch wall-mount hole spacing reused as a selected U-bolt leg spacing; source does not give a full kit engineering drawing. Nominal 1-5/8 inch pipe designation is not treated as a measured pipe diameter.',
        load_qualified=False)


def build():
    g=Geometry();enclosure(g);cable_channel(g);logger_module(g);battery(g);mini_usb(g);power_interfaces(g);leads=battery_lead(g)
    mounting=mast_mount(g)
    geometry=export_review(g,'onset_u30_nrc_enclosure_candidate')
    paths=[Path(__file__),HERE/'u30_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py',HERE/'build_weather_assets.py']
    record=dict(schema_version=1,status='unaccepted_static_U30_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        configuration='Manual-described five primary ports, optional analog and expander absent',
        hinge_axis_m=[-.0863,.010,0],door_parts=['hinged_door','model_text','device_text'],
        latch_axes_m=[[.0843,.0125,z] for z in [.050,.145]],
        sensor_jack_centres_m=[[x*.001,.030,.068] for x in [-36,-18,0,18,36]],
        selected_battery_package_m=[.102,.050,.094],
        selected_jack_geometry_m=dict(body_width=.016,body_depth=.015,body_height=.019,throat_width=.0101,throat_depth=.009,latch_notch_end_z=.0787),
        battery_leads=leads,mounting=mounting,
        missing_parts=[],
        staged_in_lab=False,initial_stock_credit=False,weatherproof_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'u30_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],status=record['status'])))


if __name__=='__main__':build()
