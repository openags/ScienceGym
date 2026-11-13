"""Source-based Nicolet cover; all unmeasured mechanical values are selected."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP,vec
from optical_assets import DEVICES,visuals

CENTER=np.array([.58,.12,TOP])


def build(path,case='nominal',timestep=.001):
    card=json.loads((DEVICES['nicolet_6700']/'interfaces.json').read_text())
    lid_card=next(i for i in card['interfaces'] if i['id']=='sample_cover')
    slider_card=next(i for i in card['interfaces'] if i['id']=='sample_access_slider')
    pivot=np.array(lid_card['pivot_m']);cx=card['sample_bay']['center_xy_m'][0]
    if timestep not in {.001,.0005}:raise ValueError('Unsupported optical refinement timestep')
    w=World();w.root.find('option').attrib.update(timestep=str(timestep),solver='Newton',iterations='200',tolerance='1e-10',impratio='10',noslip_iterations='0')
    w.root.find("actuator/general[@name='actuator8']").attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    instrument=w.body('nicolet',CENTER,False)
    visuals(w,instrument,'nicolet_6700',exclude=card['cover_parts'])
    # Convex shell sections preserve the open bay and its access corridor.
    w.box(instrument,'nicolet_base',[.346,.3275,.020],[0,0,.030],[0,0,0,0])
    for name,xlo,xhi in [('left',-.346,cx-.119),('right',cx+.119,.346)]:
        yz=[(-.3275,.050),(-.3275,.160),(-.302,.184),(-.255,.205),(-.060,.215),(.020,.252),(.3275,.252),(.3275,.050)]
        points=[[x,y,z] for x in [xlo,xhi] for y,z in yz];name='nicolet_'+name+'_shell'
        ET.SubElement(w.assets,'mesh',name=name,vertex=vec(np.asarray(points).ravel()))
        ET.SubElement(instrument,'geom',name=name,type='mesh',mesh=name,rgba='0 0 0 0')
    w.box(instrument,'nicolet_rear',[.119,.17675,.099],[cx,.15075,.149],[0,0,0,0])
    w.box(instrument,'nicolet_front',[.119,.002,.092],[cx,-.292,.146],[0,0,0,0])
    w.box(instrument,'nicolet_bay_floor',[.105,.130,.002],[cx,-.160,.048],[0,0,0,0])
    for x in [cx-.107,cx+.107]:w.box(instrument,'nicolet_bay_wall_'+str(x),[.002,.1295,.100],[x,-.1595,.150],[0,0,0,0])
    lid=ET.SubElement(instrument,'body',name='spectrometer_lid',pos=vec(pivot))
    ET.SubElement(lid,'joint',name='spectrometer_lid_hinge',type='hinge',axis='1 0 0',range='-.0001 0' if case=='locked_hinge' else '-1.5 0',frictionloss='.30',damping='.02',
                  solreflimit='.004 1',solimplimit='.99 .99 .0001',solreffriction='.004 1',solimpfriction='.99 .99 .0001')
    slider_parts=set(slider_card['parts']);handle_parts={n for n in card['cover_parts'] if n.startswith('lid_handle_')}
    cover_parts=set(card['cover_parts'])-slider_parts-(handle_parts if case=='missing_handle' else set())
    visuals(w,lid,'nicolet_6700',prefix='nicolet_cover_visual',only=cover_parts,origin=pivot)
    def cover_box(name,half,position,density='1200'):
        w.box(lid,name,half,np.array(position)-pivot,[0,0,0,0],density=density,friction='1.0 .01 .006',condim='6',solref='.004 1',solimp='.99 .99 .0001')
    for side in [-1,1]:cover_box('spectrometer_lid_side_'+str(side),[.02175,.134,.001],[cx+side*.09675,-.160,.251])
    cover_box('spectrometer_lid_front',[.075,.018,.001],[cx,-.276,.251])
    cover_box('spectrometer_lid_rear',[.075,.066,.001],[cx,-.092,.251])
    cover_box('spectrometer_lid_front_lip',[.1185,.002,.006],[cx,-.292,.244])
    for side in [-1,1]:cover_box('spectrometer_lid_skirt_'+str(side),[.002,.132,.006],[cx+side*.1165,-.160,.244])
    if case!='missing_handle':
        for side in [-1,1]:cover_box('spectrometer_handle_post_'+str(side),[.004,.009,.004],[cx+side*.038,-.296,.247])
        ET.SubElement(lid,'geom',name='spectrometer_handle_bar',type='capsule',fromto=vec(np.r_[np.array([cx-.038,-.306,.247])-pivot,np.array([cx+.038,-.306,.247])-pivot]),
                      size='.004',density='1200',rgba='0 0 0 0',friction='1.0 .01 .006',condim='6',solref='.004 1',solimp='.99 .99 .0001')
    ET.SubElement(lid,'site',name='spectrometer_lid_grasp',pos=vec(np.array(lid_card['grasp_center_m'])-pivot),size='.001')
    slider_center=np.array([cx,-.208,.248]);slider=ET.SubElement(lid,'body',name='sample_slider',pos=vec(slider_center-pivot))
    # A selected 0.6 N passive track resistance exceeds this 43 g window's
    # gravity load at every cover angle. The earlier 0.2 N trial let the
    # window slide open; it failed the cover-cycle initial-state return.
    # This unmeasured resistance is an explicit model assumption.
    ET.SubElement(slider,'joint',name='sample_slider_travel',type='slide',axis='0 1 0',range='0 .104',frictionloss='.6',damping='.1',solreflimit='.004 1',solimplimit='.99 .99 .0001',solreffriction='.004 1',solimpfriction='.99999 .99999 .0001')
    visuals(w,slider,'nicolet_6700',prefix='nicolet_slider_visual',only=slider_parts,origin=slider_center)
    w.box(slider,'sample_slider_pane',[.079,.054,.001],[0,0,0],[0,0,0,0],density='1200')
    w.box(slider,'sample_slider_tab',[.0475,.003,.0015],[0,-.039,.003],[0,0,0,0],density='1200')
    # Adjacent-body filtering must not hide window/frame interference.
    contact=w.root.find('contact')
    if contact is None:contact=ET.SubElement(w.root,'contact')
    for frame in lid.findall('geom'):
        if not frame.get('name','').startswith('spectrometer_lid_'):continue
        for moving in ['sample_slider_pane','sample_slider_tab']:
            ET.SubElement(contact,'pair',geom1=frame.get('name'),geom2=moving,condim='3',friction='.3 .3 .001 .0001 .0001',solref='.004 1',solimp='.99 .99 .0001')
    # Coplanar mesh legends use shell inertia; physical mass is carried only
    # by named contact geometry, never duplicated by visual parts.
    for mesh in w.assets.findall('mesh'):
        if mesh.get('file','').startswith('nicolet_6700/'):mesh.set('inertia','shell')
    w.save(path)
    return dict(case=case,instrument_origin_m=CENTER.tolist(),hinge_origin_m=(CENTER+pivot).tolist(),
        local_grasp_from_hinge_m=(np.array(lid_card['grasp_center_m'])-pivot).tolist(),selected_open_angle_rad=-1.35,
        selected_hinge_friction_Nm=.30,selected_slider_friction_N=.6,selected_cover_density_kg_m3=1200,selected_grip_N=12.,
        selected_slider_friction_solimp=[.99999,.99999,.0001],
        timestep_s=timestep,
        scope='Bare instrument cover access and recovery only. Sliding sample door, accessory changes, detector cables and sample handling are separate obligations.',
        source='Nicolet user guide printed pp. 51, 91-93; hinge location, masses, friction and handle dimensions inferred.',whole_paper_validated=False)
