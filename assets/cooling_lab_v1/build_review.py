"""Derive a dimensioned plan and review records from the exact authored scene."""
import json
import html
from geometry_tools import HERE, ROOT, sha, write_json


def floorplan(scene):
    # SVG maps physical metres directly; positive Y points up on the plan.
    scale=31; x0=245; y0=730
    X=lambda x:x0+x*scale;Y=lambda y:y0-y*scale
    elements=['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="820" viewBox="0 0 800 820">',
      '<rect width="800" height="820" fill="#f9fbf6"/>',
      '<style>text{font-family:Arial,"Noto Sans CJK SC",sans-serif;fill:#284c42} .small{font-size:10px}.label{font-size:12px;font-weight:600}.dim{font-size:12px;fill:#557567}</style>',
      '<text x="34" y="30" font-size="19" font-weight="600">ScienceGym · 实验室尺寸与空间设计</text>',
      '<text x="34" y="50" class="small">单位：m · 房间、家具及通道均为设计值 · 未通过全场景验收</text>']
    def rectangle(bounds,fill,stroke,opacity=1):
        x1,y1,x2,y2=bounds
        elements.append(f'<rect x="{X(x1):.2f}" y="{Y(y2):.2f}" width="{(x2-x1)*scale:.2f}" height="{(y2-y1)*scale:.2f}" fill="{fill}" stroke="{stroke}" opacity="{opacity}"/>')
    for z in scene['zones']:
        rectangle(z['bounds_m'],z['color'],'#b3c7b9')
        x1,y1,x2,y2=z['bounds_m'];elements.append(f'<text x="{X((x1+x2)/2)}" y="{Y(y2)+15}" text-anchor="middle" class="label">{html.escape(z["label"])}</text>')
    for o in scene['obstacles']:
        a,b=o['bounds_m']
        if a[2]>=scene['envelope']['transit_height_m']:continue
        rectangle([a[0],a[1],b[0],b[1]],'#536e68' if o['role'].startswith('wall') else '#a6b8ae','#758f80')
    for c in scene['corridors']:
        coords=' '.join(f'{X(x)},{Y(y)}' for x,y in c['points_m'])
        elements.append(f'<polyline points="{coords}" fill="none" stroke="#459c79" stroke-width="{c["width_m"]*scale}" opacity=".20"/>')
    for s in scene['spaces']:
        x,y=s['center_m']
        if s['kind']=='turn':
            elements.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{s["radius_m"]*scale}" fill="#428fc4" opacity=".24"/>')
            elements.append(f'<text x="{X(x)}" y="{Y(y)}" class="small" text-anchor="middle">Ø 2.4</text>')
        else:
            w,d=s['size_m'];rectangle([x-w/2,y-d/2,x+w/2,y+d/2],'#daa644','#bd9139',.22)
    for a in scene['assets']:
        if a['id']=='g1':continue
        lo,hi=a['normalized_bounds_m'];p=a['position_m'];rectangle([lo[0]+p[0],lo[1]+p[1],hi[0]+p[0],hi[1]+p[1]],'#245e62','#fff')
    labels=[('Cary 5000',2.5,8.4),('Nicolet 6700',9.5,8.4),('A25 / RTD',2.5,5.8),('2425 ×2 / DAQ',9.9,5.8),
      ('装配 / 夹具',2.5,3),('构型 / 加热片',9.5,3),('白色装置',2.5,15.8),('黑色装置',9.5,15.8),('STR-32G / MS-56',2.5,18.1),('U30 / MS-402',9.5,18.1),
      ('ProtoMAX（选定设备）',-2.8,3.8),('涂覆 / 抽排设计',-3,7.5)]
    for text,x,y in labels:elements.append(f'<text x="{X(x)}" y="{Y(y)-12}" text-anchor="middle" class="small">{html.escape(text)}</text>')
    for a,b,label in [((0,-1.6),(12,-1.6),'12.0'),((-6,-1.6),(0,-1.6),'6.0'),((-7.2,0),(-7.2,10),'10.0'),((13.1,12),(13.1,20),'8.0'),((0,21),(12,21),'12.0')]:
        elements.append(f'<path d="M{X(a[0])} {Y(a[1])} L{X(b[0])} {Y(b[1])}" stroke="#557567" fill="none"/>')
        for x,y in [a,b]:elements.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="2" fill="#557567"/>')
        elements.append(f'<text x="{X((a[0]+b[0])/2)+5}" y="{Y((a[1]+b[1])/2)-5}" class="dim">{label} m</text>')
    elements+=['<text x="34" y="790" class="small">绿色：通行预留　蓝色：转身预留　橙色：双臂作业预留　深色：设备和设施</text>','</svg>']
    (HERE/'floorplan.svg').write_text('\n'.join(elements)+'\n')


def review():
    scene=json.loads((HERE/'scene.json').read_text());floorplan(scene)
    risk_rows=[
      ('SPACE','人形机器人与携物空间',f"按 G1 官方模型的限定通行姿态采样和官方手部关节链范围，将检查半径设为 {scene['envelope']['transit_radius_m']:.2f} m，另加 0.10 m 设计余量；腕部安装沿用官方变换；该检查不覆盖行走与全部姿态。",'真实腕部安装、相机外形、完整身体姿态、携物与行走包络、制动和跌倒影响范围。'),
      ('LOAD','重型仪器与支撑','Cary 与 Nicolet 采用独立台架，实际模型按原比例放置。','91 kg Cary、69 kg Nicolet 及附件的台架承载、稳定性、固定和楼板载荷评估。'),
      ('WET','湿式校准与电气','A25 采用低台与独立接液盘；电测仪器在相邻干台，未虚构已接通管线。','真实排液路径、接液盘容量、溢流、线缆布置及设备手册要求的间距。'),
      ('CHEMICAL','加工与涂覆隔离','独立加工间已放入选定 ProtoMAX 几何，涂覆间有抽排设施设计。','水刀工艺、夹持、安全联锁、供水排液与磨料服务尚未实现；涂料与清洗材料 SDS、抽排和废物设施仍待审查。'),
      ('EGRESS','门、通道与应急','主入口和室外入口有明确通道，门扇打开后占用范围已建模，设置应急控制位置。','真实门系统、应急设备选型与位置、线路、安全功能和所在地要求审查。'),
      ('OUTDOOR','室外测量条件','放置白色和黑色装置、跟踪器及新建辐射传感器候选模型。','日照遮挡与天空视角、天气传感器套件、桅杆固定、防水供电和布线；当前开放地面不是论文屋顶复刻。'),
      ('FIDELITY','来源与设备真实性','每个导入模型都有来源文件、哈希和单位变换；新资产有厂家图纸位置及推断记录；G1 与 Inspire FTP 双手已采用官方几何。','全部资产逐项与实物资料对照，补齐未建工具、附件和材料，验证手部接触、驱动和载荷参数。'),
      ('SERVICE','维护与设备开闭','Cary 顶盖、Nicolet 上盖、A25 盖板和 U30 外盖可作几何状态检查。','完整安装手册维护距离；Nicolet 内部滑窗、全部线缆弯曲半径与机械连接复核。'),
      ('ROBOT_SERVICE','机器人电池与服务','南侧普通检查台放置一块备用 G1 电池和断开的 V1.0 图册充电器；与湿区、涂覆间分开；服务站位与横向通道共用，不得占道存放。','检查台不代表充电场所已合格。电池更换接近性、接头版本、普通工具、充电位置与监护、散热及材料隔离仍待验证。'),
      ('SITE','场地条件与合规','当前场景是明确标注的新设计虚拟实验室，所有安全结论均保持未验收。','实际场地地点和适用要求、工程人员对结构/电气/通风/消防的专项审查。')]
    items=[dict(id=k,title=title,status='open',status_label='待审查',current_design=current,remaining=remaining) for k,title,current,remaining in risk_rows]
    write_json(HERE/'risk_register.json',dict(schema_version=1,scope='Scene-design risks and evidence gaps; not hardware safety certification',items=items,
      references=[dict(url='https://www.iso.org/standard/51528.html',scope='ISO 12100 official abstract inspected; full standard not reviewed'),
      dict(url='https://ehs-library.stanford.edu/manual/laboratory-standard-design-guidelines/laboratory-design-considerations',scope='Site-specific laboratory design reference, not a universal legal minimum'),
      dict(path='assets/cary_5000_v1/sources.json'),dict(path='assets/nicolet_6700_v1/sources.json'),dict(path='assets/thermo_a25_ac150_v1/sources.json'),dict(path='assets/cooling_lab_v1/resource_followup.json')],
      safety_accepted=False,site_jurisdiction=None))
    inventory=json.loads((HERE/'inventory.json').read_text());by_resource={}
    for a in scene['assets']:
        for resource in a.get('resource_ids',[a['resource_id']]):by_resource.setdefault(resource,[]).append(a)
    for row in inventory['items']:
        linked=by_resource.get(row['id'],[])
        row['authored_scene_components']=[dict(id=c['id'],parts=c['parts'],basis=c['basis']) for c in scene['authored_components'] if row['id'] in c['resource_ids']]
        row['scene_instances']=[dict(id=a['id'],station=a['station'],geometry=a['geometry'],sha256=a['geometry_sha256']) for a in linked]
        row['instance_allocation']={'modeled_instances':len(linked),'required_instance_count_accepted':False}
        if linked:
            row['scene_placement']='modeled_candidate_pending_review'
            row['instance_allocation']={'modeled_instances':len(linked),'required_instance_count_accepted':False}
            for a in linked:
                candidate=dict(path=a['source_artifact']['path'],sha256=a['source_artifact']['sha256'])
                row['candidate_artifacts']=[old for old in row['candidate_artifacts'] if old['path']!=candidate['path']]+[candidate]
            row['discovery_status']='candidate_linked_for_review'
            row['candidate_scope_note']='Exact scene instances bound below; source fidelity and complete instance allocation remain unaccepted.'
        elif row['authored_scene_components']:
            row['scene_placement']='partially_authored_pending_completeness_review'
        else:
            row['scene_placement']='not_placed'
            if row.get('requirement_role')=='superseded_embodiment_reference':row['candidate_scope_note']='Historical candidate retained for provenance; no current laboratory instance or execution authority.'
    inventory.update(status='scene_draft_inventory_pending_completeness_review',whole_lab_scene_exists=True,
                     scene_artifact=dict(path='assets/cooling_lab_v1/scene.json',sha256=sha(HERE/'scene.json')),
                     inventory_completeness_accepted=False,owner_asset_scene_acceptance=None)
    write_json(HERE/'inventory.json',inventory)
    contract=json.loads((HERE/'acceptance_contract.json').read_text())
    contract['room']['dimensions_m']={'main':[12,10,3.4],'fabrication':[6,5,3.4],'coating':[6,5,3.4],'outdoor':[12,8,None]}
    contract['room']['dimensions_basis']='Authored design proposal, subject to equipment and spatial review'
    contract['current_scene']={'path':'assets/cooling_lab_v1/scene.json','sha256':sha(HERE/'scene.json'),'status':'draft_not_accepted'}
    policy=json.loads((HERE/'pilot_contract.json').read_text())
    selected_resources=set(policy['robot']['resource_ids'])
    embodied_resources=set(next(a for a in scene['assets'] if a['id']=='g1')['resource_ids'])
    contract['clearance_policy']['current_exact_hand_geometry_available']=selected_resources<=embodied_resources
    contract['clearance_policy']['current_hand_geometry_scope']='Selected official G1 / Inspire FTP source geometry is present; contact, actuator, payload and full-body motion qualification remain open.'
    contract['clearance_policy']['hand_geometry_evidence']=[dict(path=p,sha256=sha(ROOT/p)) for p in ['assets/unitree_g1_inspire_v1/selection.json','assets/unitree_g1_inspire_v1/SOURCE.json','assets/unitree_g1_inspire_v1/VERIFICATION.json']]
    evidence={
        'LAB-01':['assets/cooling_lab_v1/inventory.json','assets/cooling_lab_v1/readiness.json','assets/cooling_lab_v1/pilot_contract.json'],
        'LAB-02':['assets/cooling_lab_v1/outdoor_assets.json','assets/cooling_lab_v1/scene.json','assets/cooling_lab_v1/resource_followup.json','assets/cooling_lab_v1/appearance_review.json','assets/unitree_dex5s_reconstruction_v1/model.json','assets/cooling_lab_v1/ordinary_tools.json','assets/cooling_lab_v1/waterjet.json','assets/cooling_lab_v1/stock_sources.json'],
        'LAB-03':['assets/cooling_lab_v1/scene.json','assets/cooling_lab_v1/risk_register.json'],
        'LAB-04':['assets/cooling_lab_v1/floorplan.svg','assets/cooling_lab_v1/layout_checks.json'],
        'LAB-05':['assets/cooling_lab_v1/layout_checks.json','assets/unitree_g1_inspire_v1/space.json','assets/cooling_lab_v1/workspace_checks.json'],
        'LAB-06':['assets/cooling_lab_v1/risk_register.json'],
        'LAB-07':['viewer/lab_review_v1/index.html','viewer/lab_review_v1/main.js','viewer/lab_review_v1/render_batches.js','assets/cooling_lab_v1/scene.json'],
        'LAB-08':[]}
    evidence['LAB-02']+=['assets/realsense_cameras_v1/model.json','assets/realsense_cameras_v1/VERIFICATION.json']
    evidence['LAB-02']+=['assets/g1_sensor_rig_v1/SOURCE.json','assets/g1_sensor_rig_v1/rig.json','assets/g1_sensor_rig_v1/fit_checks.json']
    evidence['LAB-02']+=['assets/g1_sensor_rig_v1/adapter.json','assets/g1_sensor_rig_v1/hardware_sources.json','assets/cooling_lab_v1/supplies.json','assets/cooling_lab_v1/supply_sources.json','assets/cooling_lab_v1/supply_checks.json']
    evidence['LAB-02']+=['assets/cooling_lab_v1/preparation_review_inputs.json']
    evidence['LAB-07']+=['viewer/lab_review_v1/sensors.js']
    evidence['LAB-02']+=['assets/omega_5tc_v1/model.json','assets/omega_5tc_v1/VERIFICATION.json']
    evidence['LAB-02']+=['assets/unitree_g1_inspire_v1/SOURCE.json','assets/unitree_g1_inspire_v1/VERIFICATION.json','assets/unitree_g1_inspire_v1/selection.json','assets/unitree_g1_inspire_v1/integration.json','assets/unitree_g1_inspire_v1/collision.json']
    # Readiness is derived from the newly reconciled inventory, before pinning.
    from build_readiness import build as build_readiness
    build_readiness()
    contract['pilot_constraints']={'path':'assets/cooling_lab_v1/pilot_contract.json','sha256':sha(HERE/'pilot_contract.json')}
    for gate in contract['gates']:
        gate['evidence']=[dict(path=p,sha256=sha(ROOT/p),scope='Partial evidence; gate remains open') for p in evidence[gate['id']]]
    write_json(HERE/'acceptance_contract.json',contract)


if __name__=='__main__':review()
