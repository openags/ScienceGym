"""Passive Cary main lid with a source-specific instrument and open rear slot."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from world import World,TOP,vec
from cary_assets import DEVICES,visuals

CENTER=np.array([.28,.51,TOP])

def build(path,case='nominal',timestep=.001):
 if case not in {'nominal','missing_pull','locked_slide'}:raise ValueError(case)
 if timestep not in {.001,.0005}:raise ValueError(timestep)
 card=json.loads((DEVICES['cary_5000']/'interfaces.json').read_text());cx=card['selected_bare_bay']['center_xy_m'][0]
 w=World();w.root.find('option').attrib.update(timestep=str(timestep),solver='Newton',iterations='200',tolerance='1e-10',impratio='10',noslip_iterations='0')
 w.root.find("actuator/general[@name='actuator8']").attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
 w.w.find("geom[@name='bench']").attrib.update(size='.85 .92 .04',pos='.50 .20 .70')
 instrument=w.body('cary',CENTER,False);fixed=set(card['main_parts'])-set(card['sliding_lid_parts'])
 visuals(w,instrument,'cary_5000',only=fixed)
 def box(name,half,p):w.box(instrument,name,half,p,[0,0,0,0])
 box('cary_plinth',[.510,.355,.015],[0,0,.015]);box('cary_lower_housing',[.510,.355,.05],[0,0,.08])
 yz=[(-.355,.130),(-.355,.280),(-.332,.319),(-.285,.359),(-.210,.380),(.325,.380),(.355,.350),(.355,.130)]
 for name,lo,hi in [('left',-.510,cx-.099),('right',cx+.099,.510)]:
  name='cary_'+name+'_optics';ET.SubElement(w.assets,'mesh',name=name,vertex=vec(np.array([[x,y,z] for x in [lo,hi] for y,z in yz]).ravel()));ET.SubElement(instrument,'geom',name=name,type='mesh',mesh=name,rgba='0 0 0 0')
 box('cary_rear_lower',[.099,.1025,.113],[cx,.2525,.243]);box('cary_slot_roof',[.099,.1025,.0065],[cx,.2525,.3695])
 for side in [-1,1]:box('cary_slot_side_'+str(side),[.002,.060,.0035],[cx+side*.097,.210,.3595])
 box('cary_slot_end',[.099,.0425,.0035],[cx,.3125,.3595]);box('cary_sample_floor',[.077,.250,.002],[cx,-.100,.138])
 # Beam windows remain actual open wall passages.
 for side in [-1,1]:
  x=cx+side*.079
  for name,half_y,half_z,y,z in [('front',.1305,.106,-.2195,.246),('rear',.1055,.106,.0445,.246),('bottom',.014,.0345,-.075,.1745),('top',.014,.0555,-.075,.2965)]:
   box('cary_bay_'+str(side)+'_'+name,[.002,half_y,half_z],[x,y,z])
 for side in [-1,1]:box('cary_lid_track_'+str(side),[.002,.270,.003],[cx+side*.095,-.080,.353])
 # Thin front-wall strips follow the source profile without filling the bay.
 outer=[(-.355,.035),(-.363,.070),(-.365,.210),(-.351,.315),(-.337,.354)]
 inner=[(-.349,.035),(-.357,.070),(-.359,.210),(-.345,.313),(-.331,.354)]
 for i in range(4):
  name='cary_front_wall_'+str(i);poly=[outer[i],outer[i+1],inner[i+1],inner[i]]
  ET.SubElement(w.assets,'mesh',name=name,vertex=vec(np.array([[x,y,z] for x in [cx-.094,cx+.094] for y,z in poly]).ravel()));ET.SubElement(instrument,'geom',name=name,type='mesh',mesh=name,rgba='0 0 0 0')
 pivot=np.array([cx,-.190,.3595]);lid=ET.SubElement(instrument,'body',name='cary_lid',pos=vec(pivot))
 ET.SubElement(lid,'joint',name='cary_lid_travel',type='slide',axis='0 1 0',range='0 .0001' if case=='locked_slide' else '0 .305',frictionloss='1.',damping='.5',solreflimit='.004 1',solimplimit='.99 .99 .0001',solreffriction='.004 1',solimpfriction='.99999 .99999 .0001')
 selected=set(card['sliding_lid_parts'])-({'sample_lid_pull'} if case=='missing_pull' else set());visuals(w,lid,'cary_5000',prefix='cary_lid_visual',only=selected,origin=pivot)
 def lid_box(name,half,center):w.box(lid,name,half,np.array(center)-pivot,[0,0,0,0],density='1200',friction='1 .01 .006',condim='6',solref='.004 1',solimp='.99 .99 .0001')
 lid_box('cary_lid_panel',[.094,.151,.0025],[cx,-.190,.3595])
 if case!='missing_pull':
  lid_box('cary_pull_floor',[.045,.0235,.001],[cx,-.275,.363])
  for side in [-1,1]:lid_box('cary_pull_side_'+str(side),[.006,.0235,.007],[cx+side*.039,-.275,.371])
  lid_box('cary_pull_front',[.033,.00725,.007],[cx,-.29125,.371]);lid_box('cary_pull_back',[.033,.00425,.007],[cx,-.25575,.371])
 ET.SubElement(lid,'site',name='cary_lid_grasp',pos=vec(np.array([cx,-.29125,.371])-pivot),size='.001')
 contact=w.root.find('contact')
 if contact is None:contact=ET.SubElement(w.root,'contact')
 for fixed_geom in instrument.findall('geom'):
  if fixed_geom.get('contype')=='0':continue
  for moving in lid.findall('geom'):
   if moving.get('contype')=='0':continue
   ET.SubElement(contact,'pair',geom1=fixed_geom.get('name'),geom2=moving.get('name'),condim='3',friction='.3 .3 .001 .0001 .0001',solref='.004 1',solimp='.99 .99 .0001')
 # The stock pads consist of several adjacent faces. Use explicit finite
 # face friction at the grip, avoiding a separate rolling/spinning wrench
 # at every pad vertex. Default mixed impedance allowed asymmetric 0.28 mm
 # compression and a force spike at reverse motion in the refinement run.
 jaw_pairs=0
 if case!='missing_pull':
  for side in ['left_finger','right_finger']:
   for i,g in enumerate(w.root.findall(".//body[@name='"+side+"']/geom")):
    if g.get('class')=='visual' or (g.get('contype')=='0' and g.get('conaffinity')=='0'):continue
    name=g.get('name') or side+'_cary_contact_'+str(i);g.set('name',name)
    ET.SubElement(contact,'pair',geom1=name,geom2='cary_pull_front',condim='3',friction='1.0 1.0 0 0 0',solref='.004 1',solimp='.99 .99 .0001');jaw_pairs+=1
 for mesh in w.assets.findall('mesh'):
  if mesh.get('file','').startswith('cary_5000/'):mesh.set('inertia','shell')
 w.save(path)
 return dict(case=case,instrument_origin_m=CENTER.tolist(),selected_slide_travel_m=.305,selected_slide_friction_N=1.,selected_slide_damping_Ns_m=.5,selected_lid_density_kg_m3=1200.,selected_pull_grip_width_m=.0145,selected_grip_N=8.,selected_finger_force_limit_N=20.,selected_jaw_contact_pairs=jaw_pairs,selected_jaw_condim=3,selected_jaw_solimp=[.99,.99,.0001],timestep_s=timestep,
             scope='Bare instrument main sliding-lid access and recovery. Front-wall removal, extension installation, accessory handling, optics and electronics remain separate.',
             source='Manufacturer Cary product photographs and legacy extension instructions; all local mechanism dimensions and resistance inferred.',whole_paper_validated=False)
