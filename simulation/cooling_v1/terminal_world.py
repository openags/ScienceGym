"""USB-TC wire workcell with a physical gripper, driver and passive lead clip.

Commercial geometry comes from the sourced USB-TC reconstruction. The needle
jaws, offset motorized driver, staging supports and spring clip are selected
robot fixtures. The 24 AWG extension has its complete selected 0.6 m length;
the fine-wire transition and electronics remain separate interfaces.
"""
import json
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from world import World,TOP,vec
from extended_device_assets import DEVICES,visuals
from terminal_mechanism import add_terminal,add_driver,WIRE_DIAMETER,WIRE_DENSITY

CENTER=np.array([.48,.12,TOP+.08])
PARK=np.array([.36,-.18,TOP+.085])


def add_inertial_boxes(body,boxes):
    """Add the selected jaw masses to the source finger's physical inertia."""
    old=body.find('inertial');m0=float(old.get('mass'));p0=np.fromstring(old.get('pos'),sep=' ')
    quat=np.fromstring(old.get('quat','1 0 0 0'),sep=' ');rotation=np.empty(9);mujoco.mju_quat2Mat(rotation,quat);rotation=rotation.reshape(3,3)
    inertia=rotation@np.diag(np.fromstring(old.get('diaginertia'),sep=' '))@rotation.T
    records=[(m0,p0,inertia)]
    for mass,half,pos in boxes:
        a,b,c=np.asarray(half)*2;records.append((mass,np.array(pos),np.diag([b*b+c*c,a*a+c*c,a*a+b*b])*mass/12))
    mass=sum(r[0] for r in records);center=sum(m*p for m,p,I in records)/mass;tensor=np.zeros((3,3))
    for m,p,I in records:
        d=p-center;tensor+=I+m*(np.dot(d,d)*np.eye(3)-np.outer(d,d))
    old.attrib.clear();old.attrib.update(mass=str(mass),pos=vec(center),
        fullinertia=vec([tensor[0,0],tensor[1,1],tensor[2,2],tensor[0,1],tensor[0,2],tensor[1,2]]))


def build(path,pin=3,clamp=True,bit=True,timestep=.0001):
    w=World();w.root.find('option').attrib.update(timestep=str(timestep),solver='Newton',iterations='200',tolerance='1e-10',
        noslip_iterations='3',noslip_tolerance='1e-12',impratio='1')
    ET.SubElement(w.root,'size',memory='256M')
    w.root.find("actuator/general[@name='actuator8']").attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
    # Source finger datum 58.4 mm + needle pad centre 87 mm. Centre the
    # cylinder on the pad rather than grasping near its lower edge.
    hand=w.root.find(".//body[@name='hand']");hand.find("site[@name='tcp']").set('pos','0 0 .1454')
    ET.SubElement(hand,'site',name='driver_tcp',pos='-.035 0 .1984',size='.001',rgba='.8 .2 .1 1')
    for side in ['left_finger','right_finger']:
        body=w.root.find(f".//body[@name='{side}']")
        pieces=[(.0025,[.003,.0012,.013],[0,.0012,.069]),(.00024,[.003,.00025,.005],[0,.00025,.087])]
        add_inertial_boxes(body,pieces)
        for index,(mass,size,pos) in enumerate(pieces):
            w.box(body,side+'_needle_'+str(index),size,pos,[.18,.24,.28,1],mass=str(mass),
                friction='1.2 .0002 .0001',condim='6',solref='.002 1',solimp='.9999 .9999 .00001')
    mount=ET.SubElement(hand,'body',name='driver_mount',pos='-.035 0 .1984',quat='0 1 0 0')
    w.cylinder(mount,'driver_handle',.007,.014,[0,0,.050],[.12,.32,.40,1],mass='.035')
    w.cylinder(mount,'driver_bracket_rail',.003,.034,[0,0,.085],[.32,.35,.38,1],mass='.012')
    w.box(hand,'driver_bracket_plate',[.024,.008,.004],[-.0175,0,.082],[.32,.35,.38,1],mass='.012')
    add_driver(w,mount,bit=bit)
    device=w.body('mcc_usb_tc',CENTER,False)
    card=json.loads((DEVICES['mcc_usb_tc']/'interfaces.json').read_text())
    selected=next(t for t in card['terminals'] if t['pin']==pin)
    visuals(w,device,'mcc_usb_tc',exclude=[selected['parts'][n] for n in ['screw','shank','clamp']])
    w.box(device,'daq_lower_housing',[.0615,.0414,.0065],[0,0,.0065],rgba=[0,0,0,0])
    w.box(device,'daq_upper_housing',[.0565,.0309,.01128],[0,0,.02428],rgba=[0,0,0,0])
    for side in [-1,1]:w.box(device,'daq_endcap_'+str(side),[.003,.0418,.01128],[side*.059,0,.02428],rgba=[0,0,0,0])
    for t in card['terminals']:
        active=t['pin']==pin
        cfg=add_terminal(w,device,pin=t['pin'],visual=active,clamp=clamp if active else True)
        if active:configuration=cfg
        else:
            # Unselected terminals are initially open and mechanically fixed
            # in this run. Their passages and head counterbores remain open.
            for suffix in ['_screw','_plate']:
                body=device.find("body[@name='"+cfg['prefix']+suffix+"']")
                for joint in body.findall('joint'):body.remove(joint)
            for eq in list(w.root.find('equality')):
                if eq.get('name','').startswith(cfg['prefix']+'_'):w.root.find('equality').remove(eq)
    riser=w.body('daq_riser',[*CENTER[:2],TOP],False)
    w.box(riser,'daq_riser_top',[.065,.045,.004],[0,0,.076],[.15,.22,.27,1])
    for x in [-.05,.05]:
        for y in [-.032,.032]:w.box(riser,'daq_riser_leg_'+str(x)+'_'+str(y),[.004,.004,.036],[x,y,.036],[.15,.22,.27,1])
    axis=np.array(configuration['insertion_axis'],float);entry=CENTER+configuration['wire_entry_m']
    inserted=entry-axis*.025;inserted[2]=CENTER[2]+configuration['wire_floor_m']+WIRE_DIAMETER/2
    wire=w.body('wire',PARK)
    conductor_mass=WIRE_DENSITY*np.pi*(WIRE_DIAMETER/2)**2*.006
    jacket_mass=(WIRE_DENSITY*np.pi*(WIRE_DIAMETER/2)**2+1300*np.pi*(.00065**2-(WIRE_DIAMETER/2)**2))*.036
    ET.SubElement(wire,'geom',name='wire_bare',type='cylinder',fromto=vec(np.r_[axis*.024,axis*.030]),size=str(WIRE_DIAMETER/2),mass=str(conductor_mass),
        rgba='.67 .64 .43 1',friction='.5 .00001 .000001',solref='.0005 1',solimp='.9999 .9999 .00001',condim='3')
    ET.SubElement(wire,'geom',name='wire_jacket',type='cylinder',fromto=vec(np.r_[axis*(-.012),axis*.024]),size='.00065',mass=str(jacket_mass),
        rgba='.68 .08 .035 1',friction='.5 .00001 .000001',solref='.002 1',solimp='.9999 .9999 .00001',condim='3')
    ET.SubElement(wire,'site',name='wire_grasp',pos='0 0 0',size='.0003')
    ET.SubElement(wire,'site',name='wire_tip',pos=vec(axis*.030),size='.0002')
    # Complete selected extension length: 42 mm rigid terminal-end segment
    # and a 558 mm attached edge-length string, with no bending/torsion model.
    z=TOP+.00065-PARK[2]
    route=np.array([[0,-.012,0],[0,-.060,z],[.16,-.060,z],[.16,.080,z],[0,.080,z]])
    route[:,1]*=axis[1]
    total=float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum());route[-1,0]+=total-.558
    points=[route[0]]
    for a,b in zip(route,route[1:]):
        n=max(1,int(np.ceil(np.linalg.norm(b-a)/.02)));points.extend(a+(b-a)*u for u in np.linspace(0,1,n+1)[1:])
    points=np.asarray(points);length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
    flex=ET.SubElement(wire,'flexcomp',name='wire_extension',type='direct',dim='1',point=vec(points.ravel()),
        element=' '.join(f'{i} {i+1}' for i in range(len(points)-1)),radius='.00065',mass=str(jacket_mass/.036*length),rgba='.65 .07 .025 1')
    ET.SubElement(flex,'pin',id='0');ET.SubElement(flex,'edge',equality='true',damping='.001',solref='.0005 1',solimp='.9999 .9999 .00001')
    ET.SubElement(flex,'contact',selfcollide='auto',condim='3',friction='.3 .00001 .000001',solref='.0005 1',solimp='.9999 .9999 .00001')
    stand=w.body('wire_stand',[*PARK[:2],TOP],False)
    for index,s in enumerate([-.009,.012]):
        pos=axis*s;pos[2]=(PARK[2]-TOP-.00065)/2
        w.box(stand,'wire_stand_support_'+str(index),[.004,.001,pos[2]],pos,[.12,.35,.42,1])
    clip_centers=[inserted+axis*s for s in [.015,.0215]]
    # Two passive support points prevent the attached tail rotating the end
    # upward after the terminal opens. Each point remains separately sprung.
    for index,clip_center in enumerate(clip_centers):
        clip=w.body('wire_retaining_fixture_'+str(index),[*clip_center[:2],TOP],False)
        height=clip_center[2]-TOP
        w.box(clip,'wire_clip_base_'+str(index),[.004,.0015,(height-.00065)/2],[0,0,(height-.00065)/2],[.12,.35,.42,1])
        for side in [-1,1]:
            suffix=str(index)+'_'+str(side)
            leaf=ET.SubElement(clip,'body',name='wire_clip_leaf_'+suffix,pos=vec([side*.00095,0,height]))
            ET.SubElement(leaf,'joint',name='wire_clip_open_'+suffix,type='slide',axis=vec([side,0,0]),range='0 .0015',stiffness='2000',damping='.1',springref='0',armature='0',
                      solreflimit='.0005 1',solimplimit='.9999 .9999 .00001')
            ET.SubElement(leaf,'geom',name='wire_clip_contact_'+suffix,type='capsule',fromto='0 -.001 0 0 .001 0',size='.00035',mass='.0005',rgba='.4 .43 .46 1',
                friction='.5 .00001 .000001',solref='.0005 1',solimp='.9999 .9999 .00001',condim='3')
    # Text legends are zero-thickness visual surfaces. Explicit shell inertia
    # permits their import; all such visual geoms have zero physical mass.
    for mesh in w.assets.findall('mesh'):
        if mesh.get('file','').startswith('mcc_usb_tc/'):mesh.set('inertia','shell')
    w.save(path)
    return dict(terminal=configuration,timestep_s=timestep,entry_m=entry.tolist(),screw_center_m=(CENTER+configuration['screw_center_m']).tolist(),
        wire_park_m=PARK.tolist(),wire_inserted_grasp_m=inserted.tolist(),wire_grip_N=4.,wire_pull_grip_N=4.,bare_length_m=.006,
        wire_pull_force_N=1.,wire_pull_hold_s=.3,wire_pull_travel_limit_m=.002,wire_pull_stop_N=1.5,
        extension_length_m=length+.042,clip_center_m=clip_centers[0].tolist(),clip_centers_m=[p.tolist() for p in clip_centers],selected_clip_stiffness_N_m=2000,
        selected_insulation_jaw_contact_time_constant_s=.002,needle_pad_center_tcp_m=.1454,
        grasp_radial_limit_m=.003,grasp_axial_limit_m=.0025,grasp_axis_angle_limit_rad=.1,
        initial_wire_state='supported in remote staging stand',driver_initial_state='installed offset power tool',
        selected_active_pin=pin,unselected_terminals='geometric open interfaces, fixed at initial open state',
        inferences=['24 AWG extension geometry and 0.6 m length','rigid 42 mm terminal-end segment and zero-bending string tail',
                    'needle jaws, offset power tool, retained DAQ riser, parking stand and passive wire clip',
                    'ideal thread/captive-plate mechanism with selected friction; no hardware qualification'],whole_paper_validated=False)
