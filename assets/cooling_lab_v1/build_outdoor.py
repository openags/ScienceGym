"""Original geometry from inspected manufacturer drawings; inferred details marked.

No source PDF or product photograph is redistributed. These models remain
review candidates, with no weather, optical or ingress protection simulation.
"""
import numpy as np
from geometry_tools import Geometry, HERE, ROOT, write_json, sha

WHITE = [222, 229, 231]; GRAY = [125, 142, 148]; BLUE = [65, 141, 190]
BLACK = [30, 39, 43]; STEEL = [167, 178, 184]


def ms56():
    g = Geometry()
    # Drawing length 217 mm, diameter 55 mm, waist diameter 38 mm.
    # Axis +Y; front window faces -Y. Longitudinal profile stations are image estimates.
    g.profile('waisted_white_housing', [(.012, 0), (.0275, 0), (.0275, .045),
        (.019, .100), (.019, .125), (.0275, .158), (.0275, .194), (.022, .200), (0, .200), (0,.012),(.012,.012)],
        WHITE, axis=(0, 1, 0), position=(0, -.1085, .032))
    g.ring('front_blue_window_flange', .011, .0275, .004, [0, -.107, .032], BLUE, axis=(0,1,0))
    g.cylinder('quartz_window', .0108, .001, [0,-.109,.032], [106,151,170], axis=(0,1,0), alpha=170)
    g.ring('detector_aperture', .0032, .009, .001, [0,-.107,.032], BLACK, axis=(0,1,0))
    g.cylinder('rear_desiccant_cap', .021, .017, [0,.100,.032], BLACK, axis=(0,1,0))
    for i in range(24):
        a=i*np.pi/12
        g.cylinder('cap_grip_'+str(i),.001,.014,[.021*np.cos(a),.100,.032+.021*np.sin(a)],GRAY,axis=(0,1,0))
    for i in range(3):
        a=i*2*np.pi/3
        g.cylinder('front_retainer_'+str(i),.0018,.002,[.023*np.cos(a),-.110,.032+.023*np.sin(a)],STEEL,axis=(0,1,0),metal=.8)
    g.cylinder('signal_connector',.007,.016,[.018,.079,.010],GRAY,axis=(.7,0,-.7))
    g.ring('rain_cap_removable',.028,.0295,.025,[0,-.095,.032],BLACK,axis=(0,1,0))
    # Optional cap projects only over the existing front tube; no fake 10 m cable.
    return g.export('eko_ms56')


def ms402():
    g=Geometry()
    # Manufacturer Figure 7-1: diameter 160, total 108, body 65, leg 16 mm.
    g.cylinder('sensor_body',.045,.058,[0,0,.045],WHITE)
    g.profile('detachable_sun_screen',[(.028,.081),(.041,.081),(.080,.052),(.080,.047),(.076,.047),(.039,.077),(.028,.077)],WHITE)
    g.cylinder('absorber',.018,.002,[0,0,.081],BLACK)
    for name,radius,alpha in [('outer_glass_dome',.027,110),('inner_glass_dome',.021,100)]:
        theta=np.linspace(0,np.pi/2,33)
        points=[(radius*np.cos(t),.081+radius*np.sin(t)) for t in theta]+[(0,.081)]
        g.profile(name,points,[154,198,211],alpha=alpha)
    for i,(x,y) in enumerate([(-.040,0),(.040,0),(0,.038)]):
        g.cylinder('leveling_screw_'+str(i),.003,.016,[x,y,.008],STEEL,role='adjustable_support',metal=.7)
        g.cylinder('leveling_knob_'+str(i),.008,.004,[x,y,.018],BLACK)
    g.cylinder('side_signal_connector',.007,.026,[.058,0,.035],GRAY,axis=(1,0,0))
    g.cylinder('desiccant_cartridge',.010,.020,[-.050,0,.040],GRAY,axis=(1,0,0))
    for i in range(12):
        a=i*np.pi/6;g.cylinder('desiccant_grip_'+str(i),.001,.018,[-.050,.010*np.cos(a),.040+.010*np.sin(a)],BLACK,axis=(1,0,0))
    g.cylinder('spirit_level',.006,.004,[.030,.022,.071],[67,168,131])
    return g.export('eko_ms402')


def u30():
    g=Geometry(); w=.181; d=.118; h=.189
    # Authored 3 mm shell walls leave a visible cavity and separately named lid.
    g.box('enclosure_back',[w-.016,.003,h],[0,d/2-.0015,h/2],GRAY)
    for x in [-1,1]:g.box('enclosure_side_'+str(x),[.003,d-.008,h],[x*(w-.019)/2,.004,h/2],GRAY)
    for z in [.0015,h-.0015]:g.box('enclosure_end_'+str(z),[w-.016,d-.008,.003],[0,.004,z],GRAY)
    front=-d/2+.004
    g.rounded_panel('outer_door',w-.016,h-.004,.005,[0,front+.0025,h/2],.009,WHITE,role='hinged_door')
    g.rounded_panel('door_raised_center',.156,.177,.002,[0,front-.001,h/2],.007,WHITE,role='hinged_door')
    for x in [-.057,.057]:g.box('door_reinforcing_rib_'+str(x),[.002,.002,.165],[x,front-.003,.095],GRAY,role='hinged_door')
    g.label('door_identification','HOBO',.073,.028,[0,front-.0021,.115],WHITE,BLACK)
    g.label('door_model','U30',.035,.018,[-.021,front-.0021,.149],WHITE,BLACK)
    for z in [.048,.142]:
        g.cylinder('hinge_'+str(z),.004,.018,[-.086,-.050,z],STEEL,role='hinge')
        g.box('latch_'+str(z),[.009,.012,.021],[.086,-.049,z],BLACK,role='door_latch')
    g.box('inner_weather_cover',[.105,.004,.087],[-.018,-.010,.132],[180,172,104],alpha=210)
    g.box('sealed_battery',[.110,.060,.045],[0,.015,.032],BLACK)
    g.box('terminal_board',[.038,.005,.075],[.054,-.005,.132],[29,104,76])
    for i in range(5):
        x=-.047+i*.023
        g.box('smart_sensor_socket_'+str(i),[.017,.015,.014],[x,-.005,.072],BLACK,role='connector')
        g.cylinder('cable_entry_'+str(i),.004,.008,[x,-.020,.008],BLACK,role='cable_entry')
    g.box('cable_clamping_bar',[.125,.009,.009],[0,-.030,.011],STEEL)
    return g.export('hobo_u30')


def build():
    assets={'eko_ms56':ms56(),'eko_ms402':ms402(),'hobo_u30':u30()}
    sources=[
        dict(id='MS56_MANUAL',url='https://dex.cz/uploads/2017/04/ms-56_manual.pdf',author='EKO Instruments; distributor-hosted manufacturer manual',sha256='0fffca818e28f9de0e6553645a329caca1f2d5afd7ce1ce2618b94ff5b430895',inspected_pdf_pages=[9,20,21],figure='5-1 and 7-1',version_note='Cover says Version 4; running footer says Ver.3.',redistributed=False),
        dict(id='MS402_MANUAL',url='https://dex.cz/uploads/2017/05/Pyranometer_Manual_MS.pdf',author='EKO Instruments; distributor-hosted manufacturer manual',sha256='63a94e50ed2a355eb7f9c118123898edb87a74a32db539ee76aefe9e9d72e43c',inspected_pdf_pages=[12,13,24],figure='5-1 and 7-1; Table 7-3',redistributed=False),
        dict(id='U30_MANUAL',url='https://www.onsetcomp.com/sites/default/files/resources-documents/12269-M%20U30%20Station%20RC%20Manual.pdf',author='Onset Computer Corporation',sha256='7ed642a427925c0b89102947860a91a1060a48c980eb2f04b5e38f11ce1096d6',inspected_pdf_pages=[8,71,72],figure='Figure 1; printed pp.66-67',redistributed=False)]
    ledgers={
      'eko_ms56':dict(dimensions=dict(length_m=.217,body_diameter_m=.055,waist_diameter_m=.038),source='MS56_MANUAL Figure 7-1',inferred=['Profile transition positions scaled from the 217 mm drawing','Rain-cap wall, screws, connector and glass dimensions','Mounting adapter and full cable route remain unresolved'],variant='MS-56 retired model; not MS-57'),
      'eko_ms402':dict(dimensions=dict(sun_screen_diameter_m=.160,overall_height_m=.108,body_height_m=.065,leg_height_m=.016,fixing_pitch_m=.080),source='MS402_MANUAL Table 7-3',inferred=['Dome radii and shield slope scaled from dimensioned drawing','Third support position, connector and desiccant cartridge detail','Mounting and 10 m cable route remain unresolved'],variant='MS-402 unventilated; not MS-402F'),
      'hobo_u30':dict(dimensions=dict(width_m=.181,depth_m=.118,height_m=.189),source='U30_MANUAL printed pp.66-67',inferred=['Shell walls, door thickness, internal placement, rounded corners and latches from diagrams','Identification is original typesetting, not reproduced manufacturer artwork','Paper does not identify RC communication option or connected weather sensors','Mast support and wiring remain missing; installed weather station is incomplete'],variant='U30 enclosure reconstruction; RC family reference, exact historical variant unresolved')}
    write_json(HERE/'outdoor_assets.json',dict(status='source_based_candidates_pending_fidelity_review',date='2026-10-23',assets=assets,dimension_ledgers=ledgers,sources=sources,
        resource_search=dict(queries=['site.eko-instruments.com MS-56 CAD STEP','site.eko-instruments.com MS-402','site.onsetcomp.com U30 CAD drawing'],result='Manufacturer manuals/drawings obtained; no reusable exact CAD obtained in these searches.',official_retired_model='https://eko-instruments.com/retired-product/ms-56/'),
        license='Original authored geometry under project license. Manufacturer references remain external.',builder_sha256=sha(__file__),asset_acceptance=False))


if __name__=='__main__':build()
