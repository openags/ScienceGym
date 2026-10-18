"""Source-sized A25 with a removable lid and physical AC150 front controls."""
import json,math
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from world import World,HERE,TOP,vec
from bath_assets import DEVICES,visuals

CENTER=np.array([.52,.15,.30])
LID_PARK=np.array([.33,-.30,TOP+.020])


def build(path,case='nominal'):
 if case not in {'nominal','missing_handle','blocked_key'}:raise ValueError(case)
 w=World();w.root.find('option').attrib.update(timestep='.001',solver='Newton',iterations='200',tolerance='1e-10',impratio='10',noslip_iterations='0')
 w.root.find("actuator/general[@name='actuator8']").attrib.update(gainprm='1 0 0',biasprm='0 0 0',ctrlrange='-40 40')
 # A floor pedestal supports the heavy instrument through an actual bench
 # cutout. The bath is not embedded in a solid tabletop.
 bench=w.w.find("geom[@name='bench']");w.w.remove(bench)
 for name,lo,hi in [('left',[-.23,-.67],[.35,.67]),('right',[.70,-.67],[1.13,.67]),('front',[.35,-.67],[.70,-.15]),('rear',[.35,.43],[.70,.67])]:
  lo,hi=np.array(lo),np.array(hi);w.box(w.w,'bench_'+name,[*(hi-lo)/2,.04],[*(lo+hi)/2,TOP-.04],[.72,.75,.78,1])
 stand=w.body('bath_floor_stand',[*CENTER[:2],0],False);w.box(stand,'bath_stand_top',[.155,.26,.010],[0,0,.290],[.16,.23,.28,1])
 for x in [-.125,.125]:
  for y in [-.215,.215]:w.box(stand,f'bath_stand_leg_{x}_{y}',[.012,.012,.14],[x,y,.14],[.16,.23,.28,1])
 card=json.loads((DEVICES['thermo_a25_ac150']/'interfaces.json').read_text());catalog=json.loads((HERE/'geometry/thermo_a25_ac150/catalog.json').read_text())['parts']
 partnames=[p['id'] for p in catalog];keys=[i for i in card['interfaces'] if i['kind']=='push_button'];omitted=list(card['lid_parts'])
 for key in keys:
  name=key['id'].removeprefix('AC150_');omitted.extend(n for n in partnames if n=='key_'+name or n.startswith('key_legend_'+name))
 bath=w.body('bath',CENTER,False);visuals(w,bath,'thermo_a25_ac150',exclude=omitted)
 # The exposed work region retains the published opening and depth.
 w.box(bath,'bath_lower_body',[.1365,.2415,.1575],[0,0,.1575],[0,0,0,0])
 for side in [-1,1]:w.box(bath,'bath_reservoir_side_'+str(side),[.025,.2415,.100],[side*.1115,0,.415],[0,0,0,0])
 w.box(bath,'bath_reservoir_front',[.0865,.01875,.100],[0,-.22275,.415],[0,0,0,0]);w.box(bath,'bath_reservoir_rear',[.0865,.04025,.100],[0,.20125,.415],[0,0,0,0])
 w.box(bath,'bath_bridge',[.1025,.1035,.002],[0,.0835,.517],[0,0,0,0])
 w.box(bath,'bath_head',[.0825,.0995,.1065],[0,.085,.6425],[0,0,0,0])
 w.box(bath,'bath_head_mount',[.066,.0735,.0085],[0,.085,.5275],[0,0,0,0])
 # Mass is derived from the exported folded lid and the declared densities.
 lid_part=next(p for p in catalog if p['id']=='bath_lid');lid_mesh=trimesh.load(HERE/'geometry/thermo_a25_ac150'/lid_part['file'],force='mesh');lid_mass=abs(float(lid_mesh.volume))*8000
 lid=w.body('bath_lid',CENTER);visuals(w,lid,'thermo_a25_ac150',only=[p for p in card['lid_parts'] if p!='lid_handle' or case!='missing_handle'],prefix='lid')
 w.box(lid,'lid_roof',[.1025,.095,.0005],[0,-.115,.5185],[0,0,0,0],mass=str(lid_mass*.65))
 for x in [-.1015,.1015]:w.box(lid,'lid_edge_x_'+str(x),[.001,.095,.0015],[x,-.115,.5165],[0,0,0,0],mass=str(lid_mass*.10))
 for y in [-.209,-.021]:w.box(lid,'lid_edge_y_'+str(y),[.1005,.001,.0015],[0,y,.5165],[0,0,0,0],mass=str(lid_mass*.075))
 # Exact convex wedges preserve the arched handle's open grip region.
 handle_part=next(p for p in catalog if p['id']=='lid_handle');handle_mesh=trimesh.load(HERE/'geometry/thermo_a25_ac150'/handle_part['file'],force='mesh');handle_mass=abs(float(handle_mesh.volume))*1350
 for i in range(0 if case=='missing_handle' else 24):
  vertices=[]
  for y in [-.116,-.100]:
   for r in [.050,.058]:
    for a in [i*math.pi/24,(i+1)*math.pi/24]:vertices.extend([r*math.cos(a),y,.519+r*.75*math.sin(a)])
  name='lid_handle_segment_'+str(i);ET.SubElement(w.assets,'mesh',name=name,vertex=vec(vertices));ET.SubElement(lid,'geom',name=name,type='mesh',mesh=name,mass=str(handle_mass/24),rgba='0 0 0 0',friction='1.4 .01 .006',condim='6',solref='.004 1',solimp='.99 .99 .0001')
 grip=next(i for i in card['interfaces'] if i['id']=='bath_lid_grip')['center_m'];ET.SubElement(lid,'site',name='bath_lid_grasp',pos=vec(grip),size='.002')
 # Park coordinates describe the lid body datum; its local lowest face is
 # 515 mm above that datum. The stand contacts the folded rim, not the grip.
 park=LID_PARK-np.array([0,-.115,.515]);parking=w.body('lid_stand',[*LID_PARK[:2],TOP],False)
 for x in [-.090,.090]:w.box(parking,'lid_parking_rail_'+str(x),[.006,.10,.010],[x,0,.010],[.10,.32,.40,1])
 for key in keys:
  name=key['id'].removeprefix('AC150_');bodyname='bath_key_'+name;p=np.array(key['center_m']);body=ET.SubElement(bath,'body',name=bodyname,pos=vec(p));travel=key['selected_travel_m']
  stop=.0001 if case=='blocked_key' and name=='standby' else travel
  ET.SubElement(body,'joint',name=bodyname+'_travel',type='slide',axis='0 1 0',range=f'0 {stop}',stiffness='800',damping='1',springref='0',solreflimit='.002 1',solimplimit='.999 .999 .0001')
  mesh=trimesh.load(HERE/'geometry/thermo_a25_ac150'/next(x['file'] for x in catalog if x['id']=='key_'+name),force='mesh');radius=float(max(mesh.extents[[0,2]])/2)
  w.cylinder(body,bodyname+'_cap',radius,.0005,[0,0,0],[0,0,0,0],mass='.003',euler='1.57079632679 0 0')
  visuals(w,body,'thermo_a25_ac150',prefix=bodyname,only=[n for n in partnames if n=='key_'+name or n.startswith('key_legend_'+name)],origin=p)
  key.update(physical_body=bodyname,world_center_m=(CENTER+p).tolist(),travel_m=travel)
 # A selected offset pusher clears the lid and bath rim during the grip.
 hand=w.root.find(".//body[@name='hand']");ET.SubElement(hand,'site',name='bath_pusher_tcp',pos='.150 0 .1515',size='.002')
 tool=ET.SubElement(hand,'body',name='button_probe')
 w.box(tool,'bath_pusher_bracket',[.079,.005,.005],[.075,0,.075],[.15,.25,.32,1],mass='.060')
 ET.SubElement(tool,'geom',name='bath_pusher_shaft',type='capsule',fromto='.150 0 .075 .150 0 .150',size='.0015',mass='.010',rgba='.3 .35 .4 1')
 for mesh in w.assets.findall('mesh'):
  if mesh.get('file','').startswith('thermo_a25_ac150/'):mesh.set('inertia','shell')
 w.save(path)
 return dict(case=case,bath_origin_m=CENTER.tolist(),lid_closed_body_m=CENTER.tolist(),lid_park_body_m=park.tolist(),lid_grip_local_m=grip,
             lid_placement_reference_local_m=[0,-.115,.515],lid_closing_clearance_offset_m=[0,-.0005,0],lid_grip_relaxation_N=1.,
             lid_steel_mass_kg=lid_mass,lid_handle_mass_kg=handle_mass,selected_densities_kg_m3={'lid_stainless':8000,'handle_polymer':1350},keys=keys,
             source_work_area=card['work_area'],initial_state='Lid closed; fixed bath retained on floor pedestal; selected controller energized in standby',
             scope='Lid and physical front keys only; filling, bath load/probes, wiring and thermal calibration remain separate',whole_paper_validated=False)
