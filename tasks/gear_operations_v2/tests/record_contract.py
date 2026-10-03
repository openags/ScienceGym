"""Static design and synthetic bookkeeping validator. No physics or trusted logger."""
import json
import math
import pathlib
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=['provenance','source_access_audit','source_conflicts','unknown_parameters','operations','branches','station_contracts','material_cards','coverage_matrix','dependencies','lineage_contract','agent_visible','evaluator_reference','episode_input_contract','nonmanual_scope','control_packages','source_outcomes','mock_contract','RELEASE_BOUNDARY']
def load_packet():return {f:json.loads((ROOT/(f+'.json')).read_text()) for f in FILES}
def req(ok,why):
 if not ok:raise ValueError(why)
def integer(x,minimum=1):return type(x) is int and x>=minimum
def reference(x):return isinstance(x,str) and x.startswith('synthetic:') and len(x)>10

def validate_design(p):
 ops=p['operations']['operations'];branches=p['branches']['branches']
 oi={x['id']:x for x in ops};bi={x['id']:x for x in branches}
 req(len(oi)==len(ops) and len(bi)==len(branches),'duplicate design ID')
 ev={x['id'] for x in p['provenance']['evidence']};unknown={x['id'] for x in p['unknown_parameters']['parameters']};stations={x['id']:x for x in p['station_contracts']['stations']};families={x['id']:x for x in p['material_cards']['specimen_families']}
 for o in ops:
  for f in ['actor','station_id','objects','tool','interface','preconditions','action','device_process','postconditions','completion_evidence','translation_kind','failure_and_recovery','ownership']:req(o.get(f),f'missing operation field {f}')
  req(o['station_id'] in stations,'unknown station')
  req(set(o['source_evidence_ids'])<=ev,'unknown evidence')
  req(set(o['unknown_input_ids'])<=unknown,'unknown gate')
 for route in p['branches']['preparation_routes'].values():
  for step in route:
   req(step['op_id'] in oi,'unknown preparation operation')
   if step['op_id']=='TRANSFER':req(step.get('destination_station') in stations,'unbound transport destination')
 for b in branches:
  req(b['specimen_family_id'] in families,'unknown family')
  req(b['preparation_route_id'] in p['branches']['preparation_routes'],'unknown preparation route')
  req(set(b['source_evidence_ids'])<=ev and set(b['required_input_ids'])<=unknown,'unknown branch reference')
  ids=[s['op_id'] for s in b['per_condition_operations']]
  req(set(ids)<=set(oi),'unknown branch operation')
  req(not b['condition_transition']['label_only_change_allowed'],'label-only phase change')
  req(b['repeat_count'] is None and b['independent_specimen_count'] is None,'invented source repeat count')
  if b['mode'] in ['compression','tension','finite_shear','diagonal_shear']:
   req(all(i in ids for i in ['MOUNT_QC','ZERO','ACQ_ARM','LOAD_CYCLE','ACQ_CLOSE','UNLOAD','RELEASE_FIXTURE','POST_INSPECT']),'missing mechanical closure')
   req(any(i.startswith('ANALYZE_') for i in ids),'missing mechanical analysis')
  if b['mode']=='actuation':req(all(i in ids for i in ['MOTOR_MOUNT','MOTOR_CONNECT','MOTOR_HOME','ACT_ACQ_ARM','MOTOR_RUN','MOTOR_STOP','ACT_ACQ_CLOSE','ACT_RELEASE','ANALYZE_ACT']),'missing motor interface')
  if b['id'].startswith('MICRO_PLANET'):req({'U_MICRO_GEOM','U_PLANET_CAD'}<=set(b['required_input_ids']),'missing micro geometry gate')
 req(families['F_MICRO_TAIJI_BUILD']['array_shape']==[5,6] and families['F_MICRO_TAIJI_COMP']['array_shape']==[4,4] and families['F_MICRO_TAIJI_ACT']['array_shape']==[5,5],'micro-Taiji sizes merged')
 req(families['F_TAIJI_VIDEO1']['array_shape']==[4,4] and families['F_TAIJI_PLUS']['array_shape']==[5,5],'macro video/main sizes merged')
 req(bi['MICRO_TAIJI_ACT']['motor_configuration']['array_positions_1_based']==[[1,1],[1,4],[4,1],[4,4]],'micro motor positions')
 req(stations['WS_OBSERVE']['physical_location'] is False and stations['WS_OBSERVE']['specimen_movement']=='none','observation teleport')
 req(all(oi[x]['actor']=='qualified_service' for x in ['IMPACT_LOAD','IMPACT_GUARD','IMPACT_RUN','IMPACT_SAFE','IMPACT_UNLOAD']),'unguarded impact actor')
 req(bi['IMPACT']['conditions']['source_angles_deg']==[0,7.5,15,22.5,30],'incomplete source impact conditions')
 req(bi['IMPACT']['specimen_family_id']=='F_IMPACT' and families['F_IMPACT']['material_card_id']=='M_IMPACT_RESIN','impact material conflation')
 mats={x['id']:x for x in p['material_cards']['cards']}
 micro=mats['M_MICRO_RESIN']['source_facts']['planetary']
 req(micro['sun_radius_mm_by_source']=={'main':0.6,'si_table_1':1.2} and micro['planet_radius_mm_si_table_1_unresolved']==0.06,'silently repaired radii')
 req(mats['M_TAIJI_METAL']['source_facts']['main_name']=='copper' and mats['M_TAIJI_METAL']['source_facts']['si_name']=='brass (copper alloy)','metal wording erased')
 req(p['evaluator_reference']['first_cycle_in_modulus_fit'] is False,'initial cycle fitted')
 req('not between-specimen SD' in p['source_outcomes']['modulus_error_bars'],'error bar semantics')
 req(p['evaluator_reference']['finite_shear_quantity']=='generalized_finite_shear_stiffness_G_prime','finite/periodic shear conflation')
 req(any(x['id']=='DAMPING_ANALYSIS' and x['required_for_whole_paper'] for x in p['nonmanual_scope']['analysis_branches']),'measured damping omitted')
 covered={x for row in p['coverage_matrix']['rows'] for x in row['task_branch_ids']};req(set(bi)<=covered,'uncovered branch')
 locs={r['source_locator'] for r in p['coverage_matrix']['rows']};req(all(f'SI Fig. {i}' in locs for i in range(1,24)),'missing SI figure')
 req({'SI Table 1','SI Table 2'}<=locs,'missing SI table')
 req(p['source_access_audit']['full_motion_videos_inspected'] is False,'full-motion overclaim')
 req(len(p['source_access_audit']['videos'])==5 and all(x['frames_inspected']==8 and not x['full_motion_review'] for x in p['source_access_audit']['videos']),'sampled video boundary')
 req('source_outcomes.json' in p['agent_visible']['not_loaded_into_actor'] and not p['agent_visible']['loader_implemented'],'actor boundary')
 req(all(p['RELEASE_BOUNDARY'][k] is False for k in ['physical_execution','feasibility_validated','scientific_replication','physics_simulation','robot_runtime','publication_performed']),'release overclaim')
 return True

def fixture(branch_id,p=None):
 """Authored toy receipt set, not an executed or measured science record."""
 p=p or load_packet();b=next(x for x in p['branches']['branches'] if x['id']==branch_id)
 f=next(x for x in p['material_cards']['specimen_families'] if x['id']==b['specimen_family_id'])
 ops={x['id']:x for x in p['operations']['operations']};steps=p['branches']['preparation_routes'][b['preparation_route_id']]+b['per_condition_operations'];events=[];location='WS_STOCK'
 for n,s in enumerate(steps):
  o=ops[s['op_id']]
  if s['op_id']=='TRANSFER':location=s['destination_station']
  events.append(dict(op_id=s['op_id'],occurrence_id=f'synthetic:{branch_id}:{n}',specimen_id='synthetic:S1',specimen_version=1,phase_version=1,condition_id='synthetic:C1',attempt_id='synthetic:A1',actor=o['actor'],location=location,receipt=f'synthetic:receipt:{n}',status='complete',destination_station=s.get('destination_station')))
 gates={g:{'closed':True,'qualification_id':'synthetic:Q1','evidence_type':'certified_geometry' if g in ['U_CAD','U_PLANET_CAD','U_MICRO_GEOM'] else ('material_certificate' if g=='U_MATERIAL' else 'qualified_card')} for g in b['required_input_ids']}
 return dict(record_kind='synthetic_bookkeeping',branch_id=branch_id,specimen={'id':'synthetic:S1','family_id':f['id'],'material_card_id':f['material_card_id'],'array_shape':f['array_shape'],'version':1,'terminal_before':False,'component_material_bindings':dict(f['component_material_bindings']),'component_material_certificates':{role:'synthetic:material-cert' for role in f['component_material_bindings']}},conditions=[{'id':'synthetic:C1','actual_phase_deg':0,'requested_phase_deg':0,'phase_measured':True,'qualified_tolerance_deg':0.01}],gates=gates,cycles=2,independent_specimen_count=1,events=events,calibration={'valid':True,'specimen_version':1,'fixture_mode':b['mode'],'id':'synthetic:cal'},mount={'version':1,'phase_version':1,'fixture_mode':b['mode']},raw={'ref':'synthetic:raw','namespace':'synthetic_bookkeeping','intended_modality':'measured','immutable':True},analysis={'initial_cycle_excluded':True,'fit_cycle_ids':[2],'fit_intervals':[[0.7,0.9]],'error_bar_kind':'fit_window_variability','quantity':'generalized_finite_shear_stiffness_G_prime' if b['mode']=='finite_shear' else 'branch_specific','preserve_oscillations':True},guard={'approved_service':True,'fresh_arm_token':True,'exclusion_clear':True,'mass_secured_on_release':True,'safe_release_token':True},impact_count=1,terminal_after=b['mode']=='guarded_impact',force_magnitude_inferred_from_person=False)

def validate_record(r,p=None):
 p=p or load_packet();bi={x['id']:x for x in p['branches']['branches']};req(r.get('record_kind')=='synthetic_bookkeeping','not a synthetic record; hardware verification unsupported')
 req(r.get('branch_id') in bi,'unknown branch');b=bi[r['branch_id']]
 fam={x['id']:x for x in p['material_cards']['specimen_families']}[b['specimen_family_id']];s=r['specimen']
 req(reference(s.get('id')) and integer(s.get('version')),'invalid specimen identity/version')
 req(s['family_id']==fam['id'] and s['array_shape']==fam['array_shape'],'specimen family/shape mismatch')
 req(s['material_card_id']==fam['material_card_id'],'material mismatch')
 req(not s['terminal_before'],'terminal specimen reuse')
 req(s.get('component_material_bindings')==fam['component_material_bindings'],'component material mismatch')
 req(all(reference(s.get('component_material_certificates',{}).get(role)) for role in fam['component_material_bindings']),'missing component material certificate')
 req(integer(r['independent_specimen_count']),'invalid independent count')
 req(isinstance(r['conditions'],list) and len(r['conditions'])>0,'empty conditions')
 req(len({c['id'] for c in r['conditions']})==len(r['conditions']),'duplicate condition')
 # Toy record exercises one condition per attempt. Campaign check covers all conditions.
 req(len(r['conditions'])==1,'one synthetic attempt must bind one condition')
 c=r['conditions'][0]
 req(all(type(c.get(k)) in [int,float] and math.isfinite(c[k]) for k in ['actual_phase_deg','requested_phase_deg','qualified_tolerance_deg']),'nonfinite phase value')
 req(c['qualified_tolerance_deg']>=0 and abs(c['actual_phase_deg']-c['requested_phase_deg'])<=c['qualified_tolerance_deg'],'phase outside qualified tolerance')
 if b['mode']=='guarded_impact':req(c['requested_phase_deg'] in b['conditions']['source_angles_deg'],'unreported impact condition')
 for g in b['required_input_ids']:
  q=r['gates'].get(g,{});req(q.get('closed') is True and reference(q.get('qualification_id')),'unresolved gate '+g)
  if g in ['U_CAD','U_PLANET_CAD','U_MICRO_GEOM']:req(q.get('evidence_type')=='certified_geometry','dimensional gate lacks certified geometry')
  if g=='U_MATERIAL':req(q.get('evidence_type')=='material_certificate','material gate evidence')
  if g not in ['U_CAD','U_PLANET_CAD','U_MICRO_GEOM','U_MATERIAL']:req(q.get('evidence_type')=='qualified_card','wrong operating gate evidence')
 events=r['events'];req(len({e['occurrence_id'] for e in events})==len(events),'duplicate occurrence')
 req(all(reference(e.get('receipt')) and reference(e.get('occurrence_id')) and e.get('status')=='complete' for e in events),'missing completed receipt')
 req(len({e['receipt'] for e in events})==len(events),'reused receipt identity')
 req(all(reference(e.get('attempt_id')) for e in events) and len({e['attempt_id'] for e in events})==1,'missing/cross-attempt identity')
 req(all(e['specimen_id']==s['id'] and e['specimen_version']==s['version'] and e['phase_version']==r['mount']['phase_version'] for e in events),'stale event identity/version')
 req(all(e['condition_id']==r['conditions'][0]['id'] for e in events),'condition crossed')
 ops={x['id']:x for x in p['operations']['operations']};stations={x['id']:x for x in p['station_contracts']['stations']}
 required=Counter(x['op_id'] for x in p['branches']['preparation_routes'][b['preparation_route_id']]+b['per_condition_operations']);got=Counter(e['op_id'] for e in events)
 req(all(got[k]>=n for k,n in required.items()),'missing required operation')
 req(all(k in required and (k=='IMAGE' or n==required[k]) for k,n in got.items()),'unexpected operation repetitions')
 # The synthetic fixture declares one recipe. Respect its causal handling order;
 # derived analysis may commute after its sealed raw parent, and in-situ images may repeat.
 def physical_key(step):return (step['op_id'],step.get('destination_station') if step['op_id']=='TRANSFER' else None)
 planned=p['branches']['preparation_routes'][b['preparation_route_id']]+b['per_condition_operations']
 is_handling=lambda x:x['op_id']!='IMAGE' and not x['op_id'].startswith('ANALYZE_')
 req([physical_key(e) for e in events if is_handling(e)]==[physical_key(e) for e in planned if is_handling(e)],'declared handling recipe causal order violated')
 location='WS_STOCK'
 for e in events:
  req(e['op_id'] in ops,'unknown event operation');o=ops[e['op_id']]
  req(e['actor']==o['actor'],'actor substitution')
  if e['op_id']=='TRANSFER':
   req(e.get('destination_station') in stations,'unbound transfer');location=e['destination_station']
  elif stations[o['station_id']]['physical_location']:
   req(location==o['station_id'],'missing physical transfer')
  req(e['location']==location,'observation teleport or location inconsistency')
 def ix(op):return next((i for i,e in enumerate(events) if e['op_id']==op),None)
 for before,after in [('MICRO_BOX','BASEPLATE_RELEASE'),('FAB_RUN','FAB_RELEASE'),('SUPPORT_CLEAR','INCOMING_QC'),('MOTOR_HOME','ACT_ACQ_ARM'),('ACT_ACQ_ARM','MOTOR_RUN'),('MOTOR_RUN','MOTOR_STOP'),('MOTOR_STOP','ACT_ACQ_CLOSE'),('ACT_ACQ_CLOSE','ACT_RELEASE'),('IMPACT_GUARD','IMPACT_RUN'),('IMPACT_RUN','IMPACT_SAFE'),('IMPACT_SAFE','IMPACT_UNLOAD'),('ZERO','ACQ_ARM'),('ACQ_ARM','LOAD_CYCLE'),('LOAD_CYCLE','ACQ_CLOSE'),('ACQ_CLOSE','UNLOAD'),('UNLOAD','RELEASE_FIXTURE')]:
  if ix(before) is not None and ix(after) is not None:req(ix(before)<ix(after),'dependency order violated')
 # Enforce causal prerequisites without requiring one complete reference-route ordering.
 causal=[('PLAN','RECEIVE'),('RECEIVE','MATERIAL_ACCEPT'),('MATERIAL_ACCEPT','FAB_STAGE'),('DESIGN_BIND','FAB_STAGE'),('FAB_STAGE','FAB_RUN'),('FAB_RELEASE','INCOMING_QC'),('INCOMING_QC','ASSEMBLY_QC'),('ASSEMBLY_QC','PHASE_SET'),('ASSEMBLY_QC','FIXTURE_SELECT'),('ASSEMBLY_QC','MOTOR_MOUNT'),('ASSEMBLY_QC','IMPACT_LOAD'),('PHASE_SET','MOUNT_QC'),('PHASE_SET','MOTOR_HOME'),('PHASE_SET','IMPACT_GUARD'),('FIXTURE_SELECT','MOUNT_QC'),('COMP_SEAT','MOUNT_QC'),('TENSION_CLAMP','MOUNT_QC'),('SHEAR_PIN','MOUNT_QC'),('SOFT_GROOVE','MOUNT_QC'),('MOUNT_QC','ZERO'),('CALIBRATE','ZERO'),('MOTOR_MOUNT','MOTOR_CONNECT'),('MOTOR_CONNECT','MOTOR_HOME'),('RELEASE_FIXTURE','POST_INSPECT'),('ACT_RELEASE','POST_INSPECT'),('RELEASE_FIXTURE','CLEAN'),('ACT_RELEASE','CLEAN'),('IMPACT_UNLOAD','CLEAN'),('CLEAN','STORE')]
 for before,after in causal:
  if ix(before) is not None and ix(after) is not None:req(ix(before)<ix(after),'causal prerequisite order violated')
 for analyze,raw in [('ANALYZE_Y','ACQ_CLOSE'),('ANALYZE_SHEAR','ACQ_CLOSE'),('ANALYZE_SOFT','ACQ_CLOSE'),('ANALYZE_ACT','ACT_ACQ_CLOSE'),('ANALYZE_IMPACT','IMPACT_RUN')]:
  if ix(analyze) is not None:req(ix(raw) is not None and ix(raw)<ix(analyze),'analysis before raw acquisition')
 req(r['calibration']['valid'] is True and r['calibration']['specimen_version']==s['version'] and reference(r['calibration'].get('id')),'invalid calibration')
 req(r['mount']['version']==s['version'] and r['mount']['fixture_mode']==b['mode'] and r['calibration']['fixture_mode']==b['mode'],'stale/wrong fixture mount')
 if any(e['op_id']=='PHASE_SET' for e in events):req(r['conditions'][0]['phase_measured'] is True,'unmeasured phase command')
 req(r['raw']['namespace']=='synthetic_bookkeeping' and r['raw']['intended_modality']=='measured' and r['raw']['immutable'] is True and reference(r['raw'].get('ref')),'modeled or mutable physical parent')
 req(not r['force_magnitude_inferred_from_person'],'body-weight force inferred')
 if b['mode'] in ['compression','tension','finite_shear','diagonal_shear']:
  req(integer(r['cycles'],2),'need post-initial cycles')
  a=r['analysis'];req(a['initial_cycle_excluded'] is True and a['fit_cycle_ids'] and len(set(a['fit_cycle_ids']))==len(a['fit_cycle_ids']) and all(integer(c,2) and c<=r['cycles'] for c in a['fit_cycle_ids']),'initial/invalid cycle fitting')
  req(a['fit_intervals'] and all(isinstance(v,list) and len(v)==2 and all(type(t) in [int,float] and math.isfinite(t) for t in v) and v[0]<v[1] for v in a['fit_intervals']),'empty/invalid slope windows')
  req(a['error_bar_kind']=='fit_window_variability','replicate-SD shortcut')
 if b['mode']=='finite_shear':req(r['analysis']['quantity']=='generalized_finite_shear_stiffness_G_prime','periodic shear substitution')
 if b['mode']=='diagonal_shear':req(r['analysis']['preserve_oscillations'] is True,'physical slips deleted')
 if b['mode']=='guarded_impact':
  req(all(v is True for v in r['guard'].values()) and set(r['guard'])=={'approved_service','fresh_arm_token','exclusion_clear','mass_secured_on_release','safe_release_token'},'impact guard incomplete')
  req(integer(r['impact_count']) and r['impact_count']==got['IMPACT_RUN']==1 and r['terminal_after'] is True,'impact reuse or missing quarantine')
 return True

def validate_campaign(c,p=None):
 p=p or load_packet();req(c.get('kind')=='synthetic_bookkeeping','campaign must be synthetic')
 req(c.get('scope') in ['selected_branch_episode','whole_paper_physical_execution'],'invalid campaign scope')
 req(c.get('records') and isinstance(c['records'],list),'empty campaign')
 for r in c['records']:validate_record(r,p)
 identity={}
 for r in c['records']:
  s=r['specimen'];signature=(s['family_id'],s['material_card_id'],tuple(s['array_shape'] or []),tuple(sorted(s['component_material_bindings'].items())))
  req(s['id'] not in identity or identity[s['id']]==signature,'cross-family specimen identity reuse')
  identity[s['id']]=signature
 all_impacts=[r for r in c['records'] if r['branch_id']=='IMPACT']
 req(len({r['specimen']['id'] for r in all_impacts})==len(all_impacts),'reused impact specimen in campaign scope')
 req(len({e['occurrence_id'] for r in c['records'] for e in r['events']})==sum(len(r['events']) for r in c['records']),'campaign occurrence collision')
 if c['scope']=='whole_paper_physical_execution':
  expected=set(p['evaluator_reference']['whole_paper_requires']['physical_branch_ids']);req({r['branch_id'] for r in c['records']}==expected,'whole-paper branch omission')
  allocation=c.get('allocation',{})
  req(set(allocation)==expected and all(isinstance(v,list) and v and len(set(v))==len(v) for v in allocation.values()),'missing/invalid campaign allocation')
  for branch,conditions in allocation.items():req({r['conditions'][0]['id'] for r in c['records'] if r['branch_id']==branch}==set(conditions),'condition allocation omission')
  req(set(c.get('analysis_ids',[]))>=set(p['evaluator_reference']['whole_paper_requires']['analysis_ids']),'missing measured damping or comparison')
  req(set(c.get('control_package_ids',[]))>=set(p['evaluator_reference']['whole_paper_requires']['control_package_ids']),'missing whole-paper controls')
  impacts=[r for r in c['records'] if r['branch_id']=='IMPACT'];req({r['conditions'][0]['requested_phase_deg'] for r in impacts}=={0,7.5,15,22.5,30},'incomplete impact angle coverage')
  req(len({r['specimen']['id'] for r in impacts})==len(impacts),'reused impact specimen')
 req(c.get('claim')=='synthetic_contract_acceptance_only','synthetic execution overclaim')
 return True


def campaign_fixture():
 p=load_packet();records=[];allocation={}
 for b in p['branches']['branches']:
  angles=[0,7.5,15,22.5,30] if b['id']=='IMPACT' else [0]
  for i,angle in enumerate(angles):
   r=fixture(b['id'],p);suffix=b['id']+':'+str(i);sid='synthetic:specimen:'+suffix;cid='synthetic:condition:'+suffix
   r['specimen']['id']=sid;r['conditions'][0].update(id=cid,actual_phase_deg=angle,requested_phase_deg=angle)
   for e in r['events']:e['specimen_id']=sid;e['condition_id']=cid;e['occurrence_id']+=':'+str(i)
   records.append(r);allocation.setdefault(b['id'],[]).append(cid)
 return {'kind':'synthetic_bookkeeping','scope':'whole_paper_physical_execution','records':records,'allocation':allocation,'analysis_ids':['DAMPING_ANALYSIS','COMPARISON_ARCHIVE'],'control_package_ids':['CP_TAIJI_FRAME','CP_PLANETARY','CP_SOFT_FRAME','CP_DAMP','CP_IMPACT'],'claim':'synthetic_contract_acceptance_only'}
