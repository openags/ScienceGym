"""Build an inspectable, authored robot laboratory at physical scale.

This scene is a design review candidate. Source device models are retained
without scaling. Missing instruments are listed, not replaced by fake shells.
"""
import json
import math
import numpy as np
from geometry_tools import Geometry, HERE, ROOT, imported_scene, sha, write_json, transform
from room_architecture import build_room
from room_details import LaboratoryGeometry

TEAL=[89,107,112]; STEEL=[151,165,170]; WHITE=[225,232,228]
DARK=[46,62,67]; WOOD=[164,143,106]; GRAY=[188,198,195]
g=LaboratoryGeometry(); placements=[]; obstacles=[]; surfaces=[]; states=[]; components=[]


def component(key,prefixes,resources,support=None,check_separation=False):
    parts=[p for p in g.parts if any(p['id'].startswith(prefix) for prefix in prefixes)]
    if not parts:raise ValueError('Empty authored component '+key)
    bounds=np.array([p['bounds_m'] for p in parts])
    components.append(dict(id=key,parts=[p['id'] for p in parts],resource_ids=resources,
        bounds_m=[bounds[:,0].min(axis=0).tolist(),bounds[:,1].max(axis=0).tolist()],
        support=support,check_separation=check_separation,status='authored_candidate_pending_review',
        basis='Original design dimensions; no claim of manufacturer product or accepted load rating'))


def obstacle(key, bounds, role):
    obstacles.append(dict(id=key,bounds_m=bounds,role=role))


def box(key,size,center,color,role='furniture',blocking=False):
    g.box(key,size,center,color,role)
    if blocking:
        center=np.array(center);half=np.array(size)/2
        obstacle(key,[(center-half).tolist(),(center+half).tolist()],role)


def bench(key,x,y,width=2.4,depth=1.2,height=.85):
    box(key+'_worktop',[width,depth,.05],[x,y,height-.025],DARK,'worktop')
    for xx in [x-width/2+.10,x+width/2-.10]:
        for yy in [y-depth/2+.10,y+depth/2-.10]:
            box(key+'_leg_'+str(xx)+'_'+str(yy),[.06,.06,height-.08],[xx,yy,(height-.08)/2+.025],TEAL)
            g.cylinder(key+'_foot_'+str(xx)+'_'+str(yy),.045,.025,[xx,yy,.0125],DARK)
    box(key+'_back_stretcher',[width-.14,.05,.09],[x,y+depth/2-.10,.25],TEAL)
    for xx in [x-width/2+.1,x+width/2-.1]:box(key+'_side_stretcher_'+str(xx),[.05,depth-.20,.09],[xx,y,.25],TEAL)
    if y < 10 and key != 'bath_stand':
        # Cabinet pedestals remain inside the existing bench footprint; the
        # centre stays open for an approach. Drawer travel is not qualified.
        for side in [-1,1] if width > 2 else [-1]:
            cx=x+side*(width/2-.37);cy=y+.02;cw=.48;cd=depth-.24
            for sx in [-1,1]:
                box(key+'_cabinet_'+str(side)+'_side_'+str(sx),[.018,cd,height-.17],[cx+sx*(cw/2-.009),cy,(height-.17)/2+.10],[208,213,210],'cabinet')
            box(key+'_cabinet_'+str(side)+'_back',[cw-.036,.018,height-.17],[cx,cy+cd/2-.009,(height-.17)/2+.10],[208,213,210],'cabinet')
            for z in [.109,height-.079]:
                box(key+'_cabinet_'+str(side)+'_deck_'+str(z),[cw-.036,cd-.018,.018],[cx,cy-.009,z],[208,213,210],'cabinet')
            box(key+'_cabinet_'+str(side)+'_recess',[cw-.036,.006,height-.20],[cx,cy-cd/2+.02,(height-.20)/2+.12],[34,42,43],'cabinet')
            box(key+'_plinth_'+str(side),[cw-.06,cd-.06,.10],[cx,cy,.05],DARK,'cabinet')
            for i,(bottom,top) in enumerate([(.12,.37),(.38,.60),(.61,height-.075)]):
                if top<=bottom:continue
                box(key+'_drawer_'+str(side)+'_'+str(i),[cw-.018,.018,top-bottom],[cx,cy-cd/2-.012,(bottom+top)/2],[208,213,210],'cabinet')
                g.tube(key+'_handle_'+str(side)+'_'+str(i),[[cx-.12,cy-cd/2-.025,top-.05],[cx-.12,cy-cd/2-.05,top-.05],[cx+.12,cy-cd/2-.05,top-.05],[cx+.12,cy-cd/2-.025,top-.05]],.007,[77,95,98])
                for dx in [-.12,.12]:
                    g.cylinder(key+'_handle_rosette_'+str(side)+'_'+str(i)+'_'+str(dx),.012,.004,[cx+dx,cy-cd/2-.024,top-.05],[167,174,177],axis=(0,1,0),metal=.85)
                g.screw(key+'_drawer_screw_'+str(side)+'_'+str(i),[cx+cw/2-.035,cy-cd/2-.022,top-.04],.0025)

    box(key+'_upper_back_rail',[width-.14,.04,.07],[x,y+depth/2-.1,height-.09],TEAL)
    for xx in [x-width/2+.1,x+width/2-.1]:
        for yy in [y-depth/2+.1,y+depth/2-.1]:
            g.cylinder(key+'_leveling_bolt_'+str(xx)+'_'+str(yy),.012,.045,[xx,yy,.0475],[157,163,166],metal=.9)
            g.screw(key+'_frame_screw_'+str(xx)+'_'+str(yy),[xx,yy-.031,height-.12],.0045)
    if key=='robot_service_bench':
        # This bench backs onto the south wall; drawers and handles must face
        # the north aisle. Rotate the actual parts, not only a review label.
        t=transform([2*x,2*y,0],np.pi)
        for p in g.parts:
            if p['id'].startswith(key+'_'):
                m=g.scene.geometry[p['id']];m.apply_transform(t);p['bounds_m']=m.bounds.tolist()
    surfaces.append(dict(id=key,xy_bounds_m=[x-width/2,y-depth/2,x+width/2,y+depth/2],top_m=height,
                         load_rating_kg=None,basis='Authored furniture; load capacity requires structural review'))
    obstacle(key,[[x-width/2,y-depth/2,0],[x+width/2,y+depth/2,height]],'bench_conservative_occupied_volume')


def shelf(key,x,y,width=1.5,depth=.55):
    for dx in [-width/2,width/2]:
        for dy in [-depth/2,depth/2]:box(key+'_upright_'+str(dx)+'_'+str(dy),[.04,.04,1.9],[x+dx,y+dy,.95],TEAL)
    for i,z in enumerate([.18,.65,1.1,1.55,1.9]):
        box(key+'_shelf_'+str(i),[width+.04,depth+.04,.035],[x,y,z],GRAY)
        surfaces.append(dict(id=key+'_shelf_'+str(i),xy_bounds_m=[x-width/2,y-depth/2,x+width/2,y+depth/2],top_m=z+.0175,load_rating_kg=None))
    obstacle(key,[[x-width/2-.02,y-depth/2-.02,0],[x+width/2+.02,y+depth/2+.02,1.93]],'storage')


def walls():
    return build_room(g, box, obstacle)


def asset(key,label,path,position,*,prefix=None,z_up=False,station='',resource='',note='',source_path=None,origin_xy=None):
    scene=imported_scene(path,prefix=prefix,z_up=z_up)
    bounds=scene.bounds.copy(); normalization=np.eye(4)
    normalization[:3,3]=[-(bounds[0,0]+bounds[1,0])/2,-(bounds[0,1]+bounds[1,1])/2,-bounds[0,2]]
    if origin_xy is not None:normalization[:2,3]=-np.asarray(origin_xy)
    scene.apply_transform(normalization)
    dest=HERE/'geometry'/('prepared_'+key+'.glb');dest.write_bytes(scene.export(file_type='glb',include_normals=True if '/supply_' in path else None))
    # Original authoring coordinates are Z-up before this normalization.
    part_names=list(scene.graph.nodes_geometry)
    entry=dict(id=key,label=label,resource_id=resource,station=station,
      geometry=str(dest.relative_to(ROOT)),geometry_sha256=sha(dest),position_m=position,yaw_rad=0,
      normalized_bounds_m=scene.bounds.tolist(),source_artifact=dict(path=path,sha256=sha(ROOT/path)),
      source_prefix=prefix,source_was_z_up=z_up,normalization_matrix=normalization.tolist(),scale=[1,1,1],
      normalization_basis='Recorded free-base XY; mesh minimum Z' if origin_xy is not None else 'Mesh XY bounding-box center; mesh minimum Z',
      part_count=len(part_names),part_names=part_names,status='待资产与场景验收',note=note,
      sources=source_path,review_scope='Existing source-based reconstruction; import proves neither product fidelity nor hardware qualification')
    placements.append(entry)
    return entry


def furniture():
    for key,x,y,w,d,h in [('cary_bench',2.5,8.7,2.6,1.2,.85),('ftir_bench',9.5,8.7,2.6,1.2,.85),
        ('assembly_white',2.9,3.0,2.4,1.2,.90),('assembly_black',9.5,3.0,2.4,1.2,.90),
        ('calibration_dry',1.1,5.8,1.6,.9,.85),('bath_stand',2.9,5.75,.8,.7,.45),
        ('electrical_bench',10.1,5.8,2.4,1.0,.85),
        ('robot_service_bench',8.35,.43,1.5,.6,.85),
        ('fabrication_fixture',-4.3,.65,2.1,1.1,.90),('coating_prep',-4.3,6.4,2.1,1.1,.90),
        ('outdoor_white',2.5,15.8,1.2,1.0,.90),('outdoor_black',9.5,15.8,1.2,1.0,.90),
        ('weather_service',9.5,18.6,1.3,.8,.9),('tracker_support',2.5,18.6,1.3,.8,.9)]:bench(key,x,y,w,d,h)
    shelf('raw_stock',1.3,.45);shelf('specimens',10.7,.45)
    shelf('fabrication_storage',-4.7,3.8,1.4,.55)
    shelf('coating_storage',-4.7,9.0,1.4,.55)
    # Custom spray/extraction enclosure with a real opening and exhaust duct.
    for key,size,pos in [('base',[1.6,.85,.06],[-4.5,8,.87]),('back',[1.6,.04,1.1],[-4.5,8.42,1.45]),
        ('left',[.04,.85,1.1],[-5.28,8,1.45]),('right',[.04,.85,1.1],[-3.72,8,1.45]),
        ('roof',[1.6,.85,.04],[-4.5,8,2.02])]:box('coating_enclosure_'+key,size,pos,GRAY,'authored_extraction_enclosure')
    # Support the enclosure down to the floor; connect the design duct to a
    # ceiling collar. Neither the stand nor the duct has an engineered rating.
    for x in [-5.20,-3.80]:
        for y in [7.66,8.34]:
            box('coating_enclosure_stand_'+str(x)+'_'+str(y),[.06,.06,.80],[x,y,.43],TEAL,'authored_extraction_enclosure')
            g.cylinder('coating_enclosure_foot_'+str(x)+'_'+str(y),.045,.03,[x,y,.015],DARK)
        box('coating_enclosure_side_rail_'+str(x),[.06,.74,.06],[x,8,.81],TEAL)
    box('coating_enclosure_back_rail',[1.46,.06,.07],[-4.5,8.34,.25],TEAL)
    g.cylinder('coating_exhaust_duct',.13,1.31,[-4.5,8.2,2.675],STEEL,role='exhaust_design')
    box('coating_exhaust_ceiling_collar',[.34,.34,.025],[-4.5,8.2,3.3175],GRAY,'ceiling_fixture')
    for i in range(13):box('exhaust_baffle_'+str(i),[1.45,.02,.018],[-4.5,8.385,1.0+i*.065],DARK,'exhaust_design')
    obstacle('coating_enclosure',[[-5.3,7.55,0],[-3.7,8.45,3.33]],'unqualified_extraction_design')
    # Spill tray surrounds bath stand; no live wiring is routed through it.
    for key,size,pos in [('base',[.92,.84,.015],[2.9,5.75,.008]),('front',[.92,.025,.06],[2.9,5.33,.03]),
        ('rear',[.92,.025,.06],[2.9,6.17,.03]),('left',[.025,.84,.06],[2.45,5.75,.03]),('right',[.025,.84,.06],[3.35,5.75,.03])]:
        box('bath_spill_'+key,size,pos,[92,126,145],'spill_tray')
    for x,y in [(4.2,.65),(7.8,9.2)]:
        box('emergency_post_'+str(x),[.10,.10,1.1],[x,y,.55],GRAY,'emergency_design',True)
        g.cylinder('emergency_stop_'+str(x),.035,.025,[x,y-.065,1.05],[182,39,41],axis=(0,1,0),role='emergency_design')
    # Original stock and fixtures, with selected dimensions explicitly authored.
    for i,(color,z,thickness) in enumerate([([181,105,67],.19775,.0005),(STEEL,.19875,.0015)]):
        box('stock_sheet_'+str(i),[.30,.25,thickness],[1.05,.45,z],color,'raw_stock')
    box('foam_stock_sheet',[.30,.25,.025],[1.05,.45,.6800],[202,145,162],'raw_stock')
    box('acrylic_stock_sheet',[.30,.25,.003],[1.05,.45,.6940],[178,201,205],'raw_stock')
    for i in range(3):g.ring('pe_tube_stock_'+str(i),.038,.051,.057,[1.6+i*.12,.45,.696],[221,221,201],role='raw_stock')
    # Owner's 2026-10-24 constraint excludes robot-specific jigs and carriers.
    # Historical geometry remains in Git; ordinary tools are imported separately.
    # The stack is checked as one supported group, not three floating plates.
    component('stock_plate_stack',['stock_sheet_'],['consumables:consumable_01','consumables:consumable_02'],'raw_stock_shelf_0',True)
    component('foam_acrylic_stock_stack',['foam_stock_','acrylic_stock_'],['consumables:consumable_04','consumables:consumable_10'],'raw_stock_shelf_1',True)
    component('pe_stock',['pe_tube_stock_'],['consumables:consumable_03'],'raw_stock_shelf_1',True)
    component('room_shell',['indoor_floor','annex_floor','wall_','door_','window_','ceiling_','outdoor_access_path'],['facility:ROOM'])
    component('bench_frames',[s['id']+'_' for s in surfaces if '_shelf_' not in s['id']],['facility:BENCHES'])
    component('storage',['raw_stock_','specimens_','fabrication_storage_','coating_storage_'],['facility:STORAGE','tools:storage_supports'])
    component('robot_service_inspection_bench',['robot_service_bench_'],['facility:ROBOT_SERVICE'])
    component('extraction_enclosure',['coating_enclosure_','coating_exhaust_','exhaust_baffle_'],['facility:COATING','tools:coating_station'])
    component('overhead_services',['service_tray_','light_'],['facility:UTILITIES'])
    component('spill_tray',['bath_spill_'],['facility:WET_SERVICES'])
    obstacle('bath_spill_tray',next(c['bounds_m'] for c in components if c['id']=='spill_tray'),'floor_spill_containment')
    component('emergency_positions',['emergency_'],['facility:SAFETY'])
    component('outdoor_supports',['outdoor_floor','outdoor_white_','outdoor_black_','weather_service_','tracker_support_'],['facility:OUTDOOR'])


def devices():
    base='assets/'
    configs=[
      ('cary','Agilent Cary 5000 + 分离式扩展舱','cary_5000_v1','cary_5000',[2.35,8.50,.85],'cary_bench','equipment:UVVIS'),
      ('dra','Cary DRA-2500 积分球附件','cary_internal_dra_2500_v1','cary_internal_dra_2500',[3.35,8.50,.85],'cary_bench','accessory:DRA_2500'),
      ('nicolet','Thermo Nicolet 6700','nicolet_6700_v1','nicolet_6700',[9.20,8.47,.85],'ftir_bench','equipment:FTIR'),
      ('pike','PIKE IntegratIR DTGS（选定重构）','pike_integratir_dtgs_v1','pike_integratir_dtgs',[10.22,8.55,.85],'ftir_bench','accessory:INTEGRATIR'),
      ('bath','ARCTIC A25 + AC150（选定重构）','thermo_a25_ac150_v1','thermo_a25_ac150',[2.9,5.68,.45],'bath_stand','equipment:BATH'),
      ('dmm','Keithley 2000','keithley_2000_v1','keithley_2000',[.8,5.8,.85],'calibration_dry','equipment:DMM'),
      ('rtd','Omega P-M 参考 RTD','omega_pm_rtd_v1','omega_pm_rtd',[1.35,5.7,.85],'calibration_dry','equipment:REF_RTD'),
      ('smu_white','Keithley 2425 · 白色装置通道','keithley_2425_v1','keithley_2425',[9.4,5.55,.85],'electrical_bench','equipment:SMU'),
      ('smu_black','Keithley 2425 · 黑色装置通道','keithley_2425_v1','keithley_2425',[10.0,5.55,.85],'electrical_bench','equipment:SMU'),
      ('daq','Measurement Computing USB-TC','mcc_usb_tc_v1','mcc_usb_tc',[10.7,5.41,.85],'electrical_bench','equipment:DAQ'),
      ('heater','Omega KHR-2/2-P','omega_khr_2_2_p_v1','omega_khr_2_2_p',[9.0,2.7,.90],'assembly_black','equipment:HEATER')]
    for key,label,folder,stem,position,station,resource in configs:
        asset(key,label,base+folder+'/geometry/'+stem+'.glb',position,station=station,resource=resource,source_path=base+folder+'/sources.json')
    tc=json.loads((ROOT/'assets/omega_5tc_v1/model.json').read_text())
    for i in range(8):
        asset('tc_'+str(i+1).zfill(2),'Omega 5TC-TT-K-36-36 · 探头 '+str(i+1),tc['geometry']['path'],
          [8.55+(i%4)*.20,3.1+(i//4)*.23,.9],z_up=True,station='assembly_black',resource='equipment:TC',
          source_path='assets/omega_5tc_v1/sources.json',
          note='目录标称 1 m、36 AWG / 0.13 mm 导体。卷线姿态、护套和局部端头尺寸为推断；尚未装接，无柔性线缆、电路或温度测量实现。')
    for key,label,prefix,position,station in [
        ('cooler_white','白色辐射冷却装置','COOLER_WHITE__',[2.5,15.8,.9],'outdoor_white'),
        ('cooler_black','黑色辐射冷却装置','COOLER_BLACK__',[9.5,15.8,.9],'outdoor_black'),
        ('cooler_fixed','固定遮阳带构型','COOLER_FIXED_BAND__',[10.2,2.64,.90],'assembly_black'),
        ('tracker','EKO STR-32G 跟踪器（待复核）','EKO_STR_32G__',[2.5,18.6,.9],'tracker_support')]:
        asset(key,label,'assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb',position,prefix=prefix,
              station=station,resource='equipment:SOLAR_TRACKER' if key=='tracker' else 'equipment:COOLER',
              note='从历史场景按原始部件 ID 提取；装置细节仍需逐项对照。',source_path='assets/cooling_scene_assets_v2/equipment_research.json')
    for key,label,position,station,resource in [
        ('eko_ms56','EKO MS-56 直射辐射计（待安装）',[2.9,18.5,.9],'tracker_support','equipment:DNI'),
        ('eko_ms402','EKO MS-402 总辐射计（待安装）',[9.9,18.6,.9],'weather_service','equipment:GTI'),
        ('hobo_u30','HOBO U30 记录器外壳与内部布局',[9.2,18.6,.9],'weather_service','equipment:WEATHER')]:
        asset(key,label,'assets/cooling_lab_v1/geometry/'+key+'.glb',position,z_up=True,station=station,resource=resource,
              note='本轮按厂家图纸重构；传感器布线、安装支架和历史选件尚未定型。',source_path='assets/cooling_lab_v1/outdoor_assets.json')
    robot_folder=ROOT/'assets/unitree_g1_inspire_v1'
    a=asset('g1','宇树 G1 + Inspire FTP 双手 · 官方完整模型','assets/unitree_g1_inspire_v1/geometry/g1_inspire_ftp_zero.glb',[6,3,0],z_up=True,
        station='circulation',resource='robot:G1_29DOF',source_path='assets/unitree_g1_inspire_v1/SOURCE.json',origin_xy=[0,0],
        note='按官方腕部关系安装左右五指手；零关节角静态姿态。手指滑块遵循官方联动，仅作几何检查；站立、负载和操作尚未合格。')
    a['resource_ids']=['robot:G1_29DOF','robot:INSPIRE_FTP_LEFT','robot:INSPIRE_FTP_RIGHT','robot:HEAD_RGBD']
    k=json.loads((robot_folder/'kinematics.json').read_text())
    states.append(dict(id='g1_hands_inspection',asset='g1',kind='joint_tree',parts=[n for n in a['part_names'] if any('_'+finger+'_' in n for finger in ['thumb','index','middle','ring','little'])],kinematics=k,
        kinematics_source=dict(path='assets/unitree_g1_inspire_v1/kinematics.json',sha256=sha(robot_folder/'kinematics.json')),
        label='双手联动几何检查（6 独立坐标 / 手）',basis=k['scope']))
    cameras=json.loads((ROOT/'assets/realsense_cameras_v1/model.json').read_text())
    for key,kind,label,x,resource in [
      ('camera_head','d455','RealSense D455 · 备选参考',2.30,'reference:D455'),
      ('camera_wrist_left','d405','RealSense D405 · 左腕 RGB 候选',2.50,'robot:WRIST_RGB_LEFT'),
      ('camera_wrist_right','d405','RealSense D405 · 右腕 RGB 候选',2.62,'robot:WRIST_RGB_RIGHT')]:
        record=next(i for i in cameras['items'] if i['id']==kind)
        asset(key,label,record['geometry']['path'],[x,2.66,.9],z_up=True,station='assembly_white',resource=resource,
          source_path='assets/realsense_cameras_v1/sources.json',
          note='官方 ROS 原尺寸相机网格。另有保留官方相机臂的 G1 适配抱环与标准紧固件，刚性间隙已检查；衬垫预紧、线缆与观察流仍待完成。D455 为备选，头部使用原生 D435i。')
    ordinary=json.loads((HERE/'ordinary_tools.json').read_text())
    for key,kind,label,pos,station,resource in [
      ('caliper','mitutoyo_530_104','Mitutoyo 530-104 游标卡尺',[3.25,2.50,.9],'assembly_white','tools:caliper'),
      ('driver','wiha_26100','Wiha 26100 普通精密螺丝刀',[2.95,2.50,.9],'assembly_white','tools:fastener_driver'),
      ('tray_white','buerkle_4208_0022','Bürkle 4208-0022 普通托盘 · A',[3.4,2.8,.9],'assembly_white','tools:supported_carrier'),
      ('tray_black','buerkle_4208_0022','Bürkle 4208-0022 普通托盘 · B',[9.7,2.7,.9],'assembly_black','tools:supported_carrier')]:
        record=next(i for i in ordinary['items'] if i['id']==kind)
        a=asset(key,label,record['geometry']['path'],pos,z_up=True,station=station,resource=resource,
          source_path='assets/cooling_lab_v1/ordinary_tools_sources.json',
          note='普通目录工具的选定重构；局部结构含推断，尚未证明抓持、测量或所有任务的兼容性。')
        if key=='caliper':states.append(dict(id='caliper_slide',asset=key,kind='slide',parts=record['geometry']['moving_parts'],axis=[1,0,0],maximum=.130,label='卡尺张开 · 20–150 mm',basis='Manufacturer measuring range; selected 20 mm initial gap; geometric inspection only'))
    supplies=json.loads((HERE/'supplies.json').read_text())
    for key,kind,pos,station in [
      ('wire_stripper','jonard_st450',[9.05,6.10,.85],'electrical_bench'),
      ('terminal_driver','wiha_26015',[9.22,6.10,.85],'electrical_bench'),
      ('fine_cutter','knipex_7803125',[11.02,6.10,.85],'electrical_bench'),
      ('meter_leads_white','pomona_5908a',[9.58,6.12,.85],'electrical_bench'),
      ('meter_leads_black','pomona_5908a',[10.10,6.12,.85],'electrical_bench'),
      ('workholding_kit','omax_317864',[-4.40,1.05,.90],'fabrication_fixture'),
      ('deburring_tool','noga_rb1000',[-3.95,1.10,.90],'fabrication_fixture'),
      ('g1_spare_battery','unitree_g1_battery_v10',[7.97,.48,.85],'robot_service_bench'),
      ('g1_disconnected_charger','unitree_g1_charger_v10',[8.58,.48,.85],'robot_service_bench'),
      ('tweezers_white','idealtek_aa_sa_t6',[2.00,3.35,.9],'assembly_white'),
      ('tweezers_black','idealtek_aa_sa_t6',[9.10,3.50,.9],'assembly_black'),
      ('fill_jug','buerkle_7102_2000',[1.74,6.08,.85],'calibration_dry'),
      ('ambient_rtd','omega_ambient_rtd',[9.58,18.78,.9],'weather_service'),
      ('tc_transition_kit','omega_smpw_cc_kit',[10.65,6.10,.85],'electrical_bench'),
      ('nano_pe_stock','nano_pe_stock',[.80,.53,1.1175],'raw_stock_shelf_2'),
      ('ldpe_stock','ldpe_stock',[1.30,.53,1.1175],'raw_stock_shelf_2'),
      ('mylar_stock','mylar_stock',[1.80,.53,1.1175],'raw_stock_shelf_2'),
      ('masking_tape','masking_tape',[-4.3,6.80,.90],'coating_prep'),
      ('coating_white_stock','krylon_51502',[-4.00,6.80,.90],'coating_prep'),
      ('coating_black_stock','krylon_51602',[-3.80,6.80,.90],'coating_prep'),
      ('silver_paste_stock','pelco_16032',[-4.65,6.80,.90],'coating_prep'),
      ('calibration_block_stock','calibration_copper_stock',[-4.8,1.10,.90],'fabrication_fixture'),
      ('utility_cart','rubbermaid_1997206',[3.80,.45,0],'cart_parking'),
      ('oily_waste_can','justrite_09100',[-3.20,9.30,0],'coating_waste_parking')]:
        record=next(i for i in supplies['items'] if i['id']==kind)
        a=asset(key,record['label'],record['geometry']['path'],pos,z_up=True,station=station,resource=record['resources'][0],source_path='assets/cooling_lab_v1/supply_sources.json',
          note='厂家参数约束或明确标注设计值的重构；详情见来源对照。当前为待用陈列，数量、操作接触和完整方法仍待验收。')
        a['resource_ids']=record['resources'];a['source_record']=kind
        if 'inspection' in record.get('details',{}):
            states.append(dict(id=key+'_cap',asset=key,**record['details']['inspection']))
        if key in ['utility_cart','oily_waste_can']:
            bounds=np.array(a['normalized_bounds_m'])+pos
            obstacle(station,bounds.tolist(),'ordinary_movable_floor_asset')
            surfaces.append(dict(id=station,xy_bounds_m=[bounds[0,0],bounds[0,1],bounds[1,0],bounds[1,1]],top_m=0,load_rating_kg=None,basis='Selected floor parking position, not a transport route'))
        if key=='oily_waste_can':states.append(dict(id='waste_lid',asset=key,kind='hinge',parts=['lid'],axis=[1,0,0],pivot_m=[0,.145,.388],maximum=-np.pi/3,label='收集桶盖打开 · 60°',basis='Manufacturer maximum opening; inferred hinge. Pedal coupling and self-closing are not simulated'))
    waterjet=json.loads((HERE/'waterjet.json').read_text())
    a=asset('waterjet','OMAX ProtoMAX · 选定水刀设备',waterjet['geometry']['path'],[-2.8,3.8,0],z_up=True,
      station='fabrication_waterjet',resource='equipment:WATERJET',source_path='assets/cooling_lab_v1/waterjet_sources.json',
      note='论文未报告水刀型号；这是本 demo 的选定设备。厂家尺寸约束与结构图重构，工艺、配套服务、夹持和安全联锁尚未实现。')
    bounds=np.array(a['normalized_bounds_m'])+np.array(a['position_m'])
    obstacle('fabrication_waterjet',bounds.tolist(),'selected_machine_occupied_volume')
    surfaces.append(dict(id='fabrication_waterjet',xy_bounds_m=[bounds[0,0],bounds[0,1],bounds[1,0],bounds[1,1]],top_m=0,load_rating_kg=None,basis='Floor support; 340 kg operating-load suitability not qualified'))
    states.append(dict(id='waterjet_lid',asset='waterjet',label='ProtoMAX 透明罩打开（几何假设）',**waterjet['inspection']))
    # Opening states are geometry inspection transforms, never robot actions.
    nico=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    hinge=next(i for i in nico['interfaces'] if i['id']=='sample_cover')
    states.append(dict(id='nicolet_cover',asset='nicolet',kind='hinge',parts=hinge['parts'],axis=hinge['axis'],
        pivot_m=hinge['pivot_m'],maximum=hinge['selected_open_angle_rad'],label='Nicolet 上盖打开',basis='Existing asset interface; local geometry inferred'))
    cary=json.loads((ROOT/'assets/cary_5000_v1/interfaces.json').read_text())
    states.append(dict(id='cary_lid',asset='cary',kind='slide',parts=cary['sliding_lid_parts'],axis=[0,1,0],maximum=.305,label='Cary 顶盖滑开',basis='Existing selected .305 m travel; geometric review only'))
    bath=json.loads((ROOT/'assets/thermo_a25_ac150_v1/interfaces.json').read_text())
    states.append(dict(id='bath_lid',asset='bath',kind='slide',parts=bath['lid_parts'],axis=[0,0,1],maximum=.25,label='A25 盖板抬起',basis='Authored inspection displacement; no support-transfer or robot claim'))
    states.append(dict(id='u30_door',asset='hobo_u30',kind='hinge',parts=['outer_door','door_raised_center','door_reinforcing_rib_-0.057','door_reinforcing_rib_0.057','door_identification','door_model'],axis=[0,0,1],pivot_m=[-.086,-.05,0],maximum=-1.6,label='U30 外盖打开',basis='Diagram-derived hinge and authored open angle; latches are not actuated'))


def build():
    room=walls();furniture();devices()
    hand_envelope=json.loads((ROOT/'assets/unitree_g1_inspire_v1/space.json').read_text())
    architecture=g.export('laboratory_structure')
    corridors=[dict(id='main',label='室内主通道',points_m=[[6,-1.2],[6,10.8]],width_m=2.0),
      dict(id='yard',label='室外连接通道',points_m=[[6,10.8],[6,19.2]],width_m=2.0),
      dict(id='cross_south',label='装配前方横向通道',points_m=[[2.9,1.6],[6,1.6],[9.5,1.6]],width_m=1.6),
      dict(id='cross_optics',label='光学工位前方通道',points_m=[[2.5,7.25],[6,7.25],[9.5,7.25]],width_m=1.6),
      dict(id='fab_access',label='加工间通道',points_m=[[6,4.5],[.90,4.5],[.90,2.5],[-2.2,2.4]],width_m=1.6),
      dict(id='coat_access',label='涂覆间通道',points_m=[[6,7.25],[4,7.25],[.90,7.3],[-2.2,7.5]],width_m=1.6),
      dict(id='outdoor_cross',label='室外装置前方通道',points_m=[[2.5,14.2],[6,14.2],[9.5,14.2]],width_m=1.6)]
    spaces=[dict(id='turn_main',kind='turn',center_m=[6,5],radius_m=1.2,label='主通道转身预留'),
      dict(id='turn_yard',kind='turn',center_m=[6,15.8],radius_m=1.2,label='室外转身预留')]
    spaces.append(dict(id='work_waterjet',kind='work',center_m=[-2.8,2.3],size_m=[2.2,1.6],label='水刀前方静态作业预留'))
    spaces.append(dict(id='service_waterjet',kind='service',center_m=[-2.8,4.62],size_m=[1.1,.40],label='水刀后方服务空间设计'))
    spaces.append(dict(id='robot_service_staging',kind='work',center_m=[8.35,1.6],size_m=[1.5,1.6],label='机器人服务检查预留；与南侧横向通道共用，禁止占道存放'))
    for key,x,y in [('assembly_white',2.9,1.6),('assembly_black',9.5,1.6),('cary_bench',2.5,7.3),('ftir_bench',9.5,7.3),
      ('wet_calibration',2.4,4.5),('electrical_bench',10.1,4.5),('outdoor_white',2.5,14.2),('outdoor_black',9.5,14.2)]:
        spaces.append(dict(id='work_'+key,kind='work',center_m=[x,y],size_m=[2.2,1.6],label=key+' 双臂作业预留'))
    zones=[
      dict(id='main_lab',label='室内装配与测量 · 12 × 10 m',bounds_m=[0,0,12,10],color='#dce8e1'),
      dict(id='fabrication',label='隔离加工间 · 6 × 5 m',bounds_m=[-6,0,0,5],color='#e6e0d4'),
      dict(id='coating',label='隔离涂覆间 · 6 × 5 m',bounds_m=[-6,5,0,10],color='#e7ddd4'),
      dict(id='outdoor',label='开放测量区 · 12 × 8 m',bounds_m=[0,12,12,20],color='#d4e3d5')]
    manifest=dict(schema_version=1,sensor_rig=dict(path='assets/g1_sensor_rig_v1/rig.json',sha256=sha(ROOT/'assets/g1_sensor_rig_v1/rig.json')),status='scene_draft_for_review_not_accepted',units='m',axes='+Z up; +X right; +Y plan up',
      coordinate_basis='Authored room layout; not the historical laboratory. Real assets imported without scale changes.',
      architecture=architecture,room_design=room,room_builder_sha256=sha(HERE/'room_architecture.py'),room_details_sha256=sha(HERE/'room_details.py'),assets=placements,authored_components=components,zones=zones,obstacles=obstacles,support_surfaces=surfaces,
      reference_comparisons={
        'eko_ms56':dict(dimensions_label='轴向 217 mm；筒体 Ø55 mm；腰部 Ø38 mm',model_scope='模型包围盒包含雨帽与接头，不能拿总包围盒代替筒体直径；轮廓转折和小零件含推断。',sources=[dict(label='厂家手册 · PDF 第 21 页尺寸图',url='https://dex.cz/uploads/2017/04/ms-56_manual.pdf#page=21')]),
        'eko_ms402':dict(dimensions_label='遮阳罩 Ø160 mm；总高 108 mm；支脚 16 mm',model_scope='采用无通风 MS-402；罩壳、双玻璃穹顶和调平脚分件，局部曲面含推断。',sources=[dict(label='厂家手册 · PDF 第 24 页尺寸图',url='https://dex.cz/uploads/2017/05/Pyranometer_Manual_MS.pdf#page=24')]),
        'hobo_u30':dict(dimensions_label='规格表 181 × 118 × 189 mm；图纸 180.6 × 118.1 × 188.7 mm',model_scope='按规格表重构，标注文字为原创排版；锁扣、壳体局部与历史通讯选件仍待核实。',sources=[dict(label='厂家手册 · PDF 第 72 页尺寸图',url='https://www.onsetcomp.com/sites/default/files/resources-documents/12269-M%20U30%20Station%20RC%20Manual.pdf#page=72')])},
      corridors=corridors,spaces=spaces,inspection_states=states,
      envelope=dict(transit_radius_m=hand_envelope['selected_body_hand_radius_m'],transit_height_m=hand_envelope['transit_height_m'],turn_radius_m=1.20,margin_m=.10,
        basis='G1 source geometry at 129 restricted static transit poses, with an all-angle triangle-inequality hand bound relative to source wrists. Additional 0.10 m planar margin. Cameras, loads, walking and balance remain unqualified.',
        body_evidence=dict(path='assets/unitree_g1_inspire_v1/space.json',sha256=sha(ROOT/'assets/unitree_g1_inspire_v1/space.json')),
        hand_evidence=dict(path='assets/unitree_g1_inspire_v1/space.json',sha256=sha(ROOT/'assets/unitree_g1_inspire_v1/space.json')),
        exact_hand_qualified=False,walking_or_balance_validated=False),
      dimensions_basis='All room, furniture, clearance and route dimensions are authored design values. Equipment source dimensions remain unchanged.',
      pilot_contract=dict(path='assets/cooling_lab_v1/pilot_contract.json',sha256=sha(HERE/'pilot_contract.json')),
      required_missing_assets=['Qualified G1/Inspire collision, actuator, load and tactile model (source integration present)','Exact 12-degree Harrick and variable-angle Spectra-Tech accessories',
        'G1 mounting, cable routing and calibration for the three staged camera candidates',
        'Ambient RTD radiation shield and mount (vented source-identified probe is staged)','Thermocouple extension leads, dynamic/termination models and strain relief (8 connector pairs are staged)','Qualified waterjet setup, guarding/interlocks/services and remaining fabrication tools',
        'Weather sensor suite, mast, power and data routes','Remaining ordinary tools, coating/cleaning supplies and waste hardware','Validated equipment mounts, supports and engineering services'],
      blocked_claims=['Whole asset inventory complete','Whole-body dynamic reach or manipulation','Robot/human safety separation','Outdoor solar/weather exposure fidelity','Bench/floor structural adequacy','Site regulatory compliance'],
      owner_acceptance=None,manipulation_development_allowed=False,builder_sha256=sha(__file__),geometry_tools_sha256=sha(HERE/'geometry_tools.py'))
    for key,model,page,dimensions in [('camera_head','D455',144,'124 × 29 × 26 mm（宽 × 高 × 深）'),
      ('camera_wrist_left','D405',146,'42 × 42 × 23 mm（宽 × 高 × 深）'),('camera_wrist_right','D405',146,'42 × 42 × 23 mm（宽 × 高 × 深）')]:
        photo='2024/04/depth_camera_d455_article_740px.jpg' if model=='D455' else '2022/04/D405v2-scaled.png'
        manifest['reference_comparisons'][key]=dict(dimensions_label=dimensions,
          model_scope='保留厂家机械网格，镜片和光学外观另加独立推断层。D455 源网格非闭合；两种模型均不作为已合格的碰撞、惯性或标定模型。',
          sources=[dict(label=model+' 厂家外观照片',url='https://www.realsenseai.com/wp-content/uploads/'+photo),
                   dict(label='厂家尺寸图 · PDF 第 '+str(page)+' 页',url='https://realsenseai.com/wp-content/uploads/2025/09/Intel-RealSense-D400-Series-Datasheet-October-2025.pdf#page='+str(page)),
                   dict(label='官方 ROS 模型 · 已固定版本',url='https://github.com/realsenseai/realsense-ros/tree/7a87097c499e3b0b69518d54a8e7a9ac1924e87c/realsense2_description')])
    for a in placements:
        if a['id'] in manifest['reference_comparisons']:continue
        record=json.loads((ROOT/a['sources']).read_text())
        if a.get('source_record'):
            item=next(i for i in record['items'] if i['id']==a['source_record'])
            dimensions={
                'omax_317864':'3 根长压臂 203.2 mm；2 根中压臂 152.4 mm；4 根立柱及 4 个 T 形螺母。立柱、孔和螺纹局部尺寸为推断。',
                'knipex_7803125':'标称长度 125 mm；头宽 13.5 mm；刃口长 9 mm。握柄外形与闭合姿态为重构。',
                'noga_rb1000':'六角柄对边 12 mm；S10 刀杆 Ø3.2 mm。柄长与刀刃曲线为推断。',
                'pomona_5908a':'每根线两端出线口间长 1219.2 mm；线缆外径 3.6576 mm；每个直插头另长 68.58 mm。每件资产含 4 根断开的引线。',
                'unitree_g1_battery_v10':'V1.0 图册壳体 120 × 182 × 80 mm；两侧卡舌伸出量为推断，计入实际包围盒。',
                'unitree_g1_charger_v10':'V1.0 图册壳体 154 × 60 × 36 mm；线缆和未核实端头不包含在壳体尺寸内。',
                'krylon_51502':'外径 66 mm、带盖高度 208 mm 为选定推断值；未取得厂家尺寸图。照片提供外形比例，净含量 340 g 不能换算成罐体尺寸。',
                'krylon_51602':'外径 66 mm、带盖高度 208 mm 为选定推断值；未取得厂家尺寸图。照片提供外形比例，净含量 340 g 不能换算成罐体尺寸。',
                'pelco_16032':'瓶身外径约 32 mm、带盖高度约 63 mm 为照片相对尺度推断；照片中的 75 mm 配样台仅作辅助参考，透视误差未消除。'}
            manifest['reference_comparisons'][a['id']]=dict(dimensions_label=dimensions.get(item['id']),dimensions_kind='inferred' if item['id'] in ['krylon_51502','krylon_51602','pelco_16032'] else 'catalogue_or_paper',model_scope='已知参数与推断分开记录。推断：'+'；'.join(item['inferred'])+'。限制：'+'；'.join(item['limits']),sources=[dict(url=s['url'],label='厂家／论文依据',scope=s['locator']) for s in item['sources']])
            continue
        sources=record.get('sources') or record.get('source_documents') or record.get('source_records') or []
        if not sources and record.get('equipment'):
            resource=a['resource_id'].split(':')[-1]
            selected=next((e for e in record['equipment'] if e['id']==resource),{})
            ids=selected.get('researched_source_ids',[])
            inventory_path=(ROOT/a['sources']).parent/record['source_inventory']
            sources=[s for s in json.loads(inventory_path.read_text())['sources'] if s.get('id') in ids]
        links=[]
        for s in sources:
            if not isinstance(s,dict):continue
            url=s.get('url')
            if not url and s.get('repository'):url=s['repository']+'/tree/'+s['commit']+'/'+s['path']
            if not url:continue
            links.append(dict(url=url,label='来源资料 · '+str(s.get('id') or s.get('document') or s.get('path') or '厂家参考'),scope=s.get('locator') or s.get('review') or 'Existing source record; follow linked ledger for its inspected scope'))
        if links:manifest['reference_comparisons'][a['id']]=dict(model_scope='按已有来源记录重构；局部尺寸、选件和历史实物一致性仍待逐项验收。',sources=links[:4])
    write_json(HERE/'scene.json',manifest)
    print(json.dumps(dict(assets=len(placements),structural_parts=len(g.parts),zones=len(zones)),indent=2))


if __name__=='__main__':build()
