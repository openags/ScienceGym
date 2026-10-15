"""Executed by build_scene.py in its Blender authoring namespace.

Device envelopes and task interfaces; all unmeasured details remain inferred.
Photos/manuals were inspected before authoring. No vendor mesh is embedded.
"""

def rounded_housing(name,size,pos,mat):
    return box(name,size,pos,mat,bevel=min(size)*.12)

def cary(xyz):
    root('AGILENT_CARY_5000',xyz)
    # Manufacturer W1020 D710 H380 mm. Asymmetric sample bay matches product photo.
    box('base',(1.020,.710,.055),(0,0,.0275),DARK,bevel=.012)
    rounded_housing('monochromator_housing',(.60,.70,.325),(-.21,0,.2175),CASE)
    rounded_housing('detector_housing',(.19,.70,.325),(.415,0,.2175),CASE)
    box('rear_bridge',(.23,.29,.30),(.205,.205,.205),CASE,bevel=.018)
    box('sample_floor',(.23,.41,.008),(.205,-.14,.060),DARK,'accessory_mount')
    for x in [.095,.315]:box('sample_bay_wall',(.008,.41,.24),(x,-.14,.18),DARK)
    # Open/removed parts are explicit; no opaque solid fills the sample bay.
    lid=rounded_housing('sample_lid',(.22,.24,.035),(.205,.10,.42),DARK)
    lid['state']='open_review_pose';lid['joint']='hinge_about_local_X; limits require qualification'
    door=box('sample_front_door',(.22,.018,.25),(.205,-.40,.08),DARK,'openable_panel',.015)
    door.rotation_euler.x=math.radians(65);door['state']='open_review_pose'
    cylinder('DRA2500_body',.075,.155,(.205,-.15,.148),DARK,'removable_optical_accessory')
    port=ring('DRA2500_sample_port',.024,.035,.007,(.205,-.226,.17),PE,'sample_port')
    port.rotation_euler.x=math.pi/2
    cylinder('DRA2500_port_plug',.024,.008,(.205,-.31,.07),WHITE,'removable_reference_plug')
    ring('DRA2500_top_port',.022,.029,.005,(.205,-.15,.228),BRUSH,'optical_port')
    label('identity','Agilent  Cary 5000',(-.47,-.354,.278),.018,DARK)
    box('power_recess',(.065,.005,.035),(-.40,-.354,.100),DARK,'electrical_interface')
    for x in [-.422,-.385]:cylinder('power_indicator',.004,.002,(x,-.358,.10),GREEN,'indicator',(math.pi/2,0,0))
    for y in [-.23,.23]:
        for x in [-.43,.43]:box('foot',(.08,.08,.008),(x,y,.004),DARK)
    for i in range(14):box('right_vent',(.001,.008,.055),(.511,.05+i*.015,.12),DARK,bevel=0)


def nicolet(xyz):
    root('THERMO_NICOLET_6700',xyz)
    # Overall size is a declared reconstruction envelope, not measured vendor CAD.
    box('base',(.69,.655,.055),(0,0,.0275),DARK,bevel=.015)
    rounded_housing('left_optics',(.17,.65,.185),(-.26,0,.15),PE)
    rounded_housing('right_optics',(.235,.65,.185),(.2275,0,.15),PE)
    rounded_housing('rear_optics',(.285,.30,.195),(-.0325,.1775,.1525),PE)
    for i in range(20):box('rear_cover_rib',(.002,.24,.001),(-.31+i*.032,.18,.2505),CASE,bevel=0)
    box('sample_compartment_floor',(.285,.34,.006),(-.0325,-.1525,.061),DARK,'accessory_mount')
    for x in [-.17,.105]:box('sample_compartment_wall',(.01,.34,.16),(x,-.1525,.14),DARK)
    holder=box('sample_bay_lid',(.27,.20,.025),(-.0325,.015,.29),DARK,'openable_panel',.012)
    holder['state']='open_review_pose'
    label('identity','Thermo  Nicolet 6700',(.12,-.329,.12),.012,DARK)
    for x in [-.26]:
        for y in [-.12,-.23]:cylinder('top_optics_cap',.029,.009,(x,y,.247),DARK,'service_cap')
    for i in range(5):
        cylinder('scan_key_'+str(i),.006,.002,(.145+i*.032,-.10,.245),BLUE,'push_button')
    cylinder('front_detector_access',.026,.008,(.14,-.330,.11),CASE,'service_cap',(math.pi/2,0,0))
    # Chosen DTGS IntegratIR hypothesis: 3-inch sphere and 18-mm upward sample port.
    box('IntegratIR_base',(.20,.24,.008),(-.0325,-.14,.070),BRUSH,'removable_optical_accessory')
    cylinder('IntegratIR_sphere_housing',.044,.085,(-.0325,-.14,.1165),DARK,'integrating_sphere')
    ring('IntegratIR_18mm_sample_port',.009,.015,.004,(-.0325,-.14,.161),BRUSH,'sample_port')
    cylinder('IntegratIR_gold_reference',.013,.004,(-.10,-.24,.08),material('gold_reference',(.75,.50,.13),1,.25),'removable_reference')
    cylinder('IntegratIR_reference_cap',.015,.008,(-.13,-.24,.083),DARK,'removable_cap')
    cylinder('IntegratIR_selector',.009,.012,(-.0325,-.193,.105),DARK,'detented_knob',(math.pi/2,0,0))
    box('IntegratIR_detector_connector',(.032,.012,.012),(.035,-.14,.10),DARK,'electrical_port')
    wire('IntegratIR_detector_cable',[(.05,-.14,.10),(.078,-.12,.08),(.08,-.02,.085),(.08,.03,.12)],DARK,.002)
    cylinder('IntegratIR_purge_port',.003,.012,(-.075,-.16,.10),BRUSH,'gas_port',(0,math.pi/2,0))


def tracker(xyz):
    root('EKO_STR_32G',xyz)
    # Mount is selected for reconstruction; the STR-32G is not the tripod STR-22G.
    box('selected_mount_plate',(.34,.28,.012),(0,0,.006),BRUSH)
    cylinder('azimuth_mount',.060,.045,(0,0,.0345),CASE,'rotary_mount')
    box('body',(.270,.19,.185),(0,0,.145),CASE,bevel=.008)
    box('top_cover',(.270,.19,.008),(0,0,.241),BRUSH)
    for x in [-.127,.127]:
        for y in [-.088,.088]:cylinder('cover_fastener',.004,.008,(x,y,.249),BRUSH)
    for x in [-.145,.145]:
        cylinder('elevation_flange_'+str(x),.060,.012,(x,0,.15),BRUSH,'rotary_flange',(0,math.pi/2,0))
        for i in range(6):
            theta=i*math.pi/3
            cylinder('flange_M8_'+str(x)+'_'+str(i),.004,.003,(x+(.008 if x>0 else -.008),.048*math.sin(theta),.15+.048*math.cos(theta)),DARK,'mounting_hole',(0,math.pi/2,0))
    box('GPS_housing',(.067,.065,.012),(0,-.025,.255),BLUE,'GPS_sensor',.005)
    cylinder('GPS_sensor',.012,.003,(0,-.025,.263),DARK)
    wire('sun_sensor_arm',[(.148,0,.15),(.18,-.04,.10),(.18,-.08,.10)],BRUSH,.005)
    cylinder('sun_sensor',.012,.045,(.18,-.09,.11),CASE,'sun_sensor',(math.pi/2,0,0))
    for x in [-.07,0,.07]:cylinder('rear_connector_'+str(x),.008,.008,(x,.098,.09),DARK,'electrical_port',(math.pi/2,0,0))
    label('identity','EKO STR-32G',(-.09,-.096,.19),.015,DARK)


cary((-.5,2.05,0))
nicolet((.55,2.05,0))
tracker((1.25,1.0,0))
