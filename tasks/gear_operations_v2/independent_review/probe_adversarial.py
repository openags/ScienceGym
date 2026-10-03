#!/usr/bin/env python3
"""Independent adversarial mutations of toy bookkeeping records; no physics."""
import copy, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import record_contract as rc

def run():
 results=[]
 def probe(name,branch,mutation):
  record=rc.fixture(branch)
  mutation(record)
  try:
   rc.validate_record(record)
  except (ValueError,TypeError,KeyError) as exc:
   results.append({'name':name,'rejected':True,'reason':str(exc),'exception':type(exc).__name__})
  else:
   results.append({'name':name,'rejected':False,'reason':'invalid record accepted'})
 def event(r,op):return next(x for x in r['events'] if x['op_id']==op)
 def move_after(r,op,after):
  ev=event(r,op);r['events'].remove(ev);idx=r['events'].index(event(r,after));r['events'].insert(idx+1,ev)
  ev['location']=event(r,after)['location']
 def analysis_before_acquisition(r):
  ev=event(r,'ANALYZE_Y');r['events'].remove(ev);r['events'].insert(0,ev);ev['location']='WS_STOCK'
 def replay_impact(r):
  ev=copy.deepcopy(event(r,'IMPACT_RUN'));ev['occurrence_id']='synthetic:replayed-impact';r['events'].insert(r['events'].index(event(r,'IMPACT_RUN'))+1,ev)
 probe('cross_attempt_event','TAIJI_PLUS',lambda r:event(r,'LOAD_CYCLE').update(attempt_id='synthetic:OTHER'))
 probe('analysis_before_raw_acquisition','TAIJI_PLUS',analysis_before_acquisition)
 probe('mount_qc_after_loading','TAIJI_PLUS',lambda r:move_after(r,'MOUNT_QC','ACQ_CLOSE'))
 probe('phase_set_after_loading','TAIJI_PLUS',lambda r:move_after(r,'PHASE_SET','POST_INSPECT'))
 probe('duplicate_impact_execution_with_unique_receipt','IMPACT',replay_impact)
 probe('impact_load_after_release_execution','IMPACT',lambda r:move_after(r,'IMPACT_LOAD','IMPACT_RUN'))
 probe('gear_insertion_after_frame_closure','TAIJI_PLUS',lambda r:move_after(r,'GEAR_INSERT','FRAME_CLOSE'))
 probe('planet_insertion_after_transmission_join','STEEL_PLANET_COMP',lambda r:move_after(r,'PLANET_INSERT','TRANSMISSION_JOIN'))
 probe('phase_registration_after_assembly_acceptance','TAIJI_PLUS',lambda r:move_after(r,'PHASE_REGISTER','ASSEMBLY_QC'))
 def stale_mesh(r):
  meshes=[e for e in r['events'] if e['op_id']=='MESH_CHECK'];ev=meshes[-1];r['events'].remove(ev);r['events'].insert(r['events'].index(event(r,'PHASE_SET')),ev)
 probe('condition_mesh_receipt_precedes_phase_change','TAIJI_PLUS',stale_mesh)
 probe('boolean_impact_count','IMPACT',lambda r:r.update(impact_count=True))
 probe('infinite_fit_window','TAIJI_PLUS',lambda r:r['analysis'].update(fit_intervals=[[-float('inf'),float('inf')]]))
 probe('duplicate_fit_cycle_identity','TAIJI_PLUS',lambda r:r['analysis'].update(fit_cycle_ids=[2,2]))
 probe('nonfinite_actual_phase','TAIJI_PLUS',lambda r:r['conditions'][0].update(actual_phase_deg=float('nan')))
 probe('unqualified_requested_actual_phase_difference','TAIJI_PLUS',lambda r:r['conditions'][0].update(actual_phase_deg=179,requested_phase_deg=0))
 probe('missing_raw_artifact_reference','TAIJI_PLUS',lambda r:r['raw'].update(ref=''))
 probe('string_immutable_flag','TAIJI_PLUS',lambda r:r['raw'].update(immutable='false'))
 probe('boolean_geometry_qualification_id','MICRO_PLANET_COMP',lambda r:r['gates']['U_MICRO_GEOM'].update(qualification_id=True))
 probe('nongeometry_gate_wrong_evidence','TAIJI_PLUS',lambda r:r['gates']['U_LOAD'].update(evidence_type='untrusted_note'))
 probe('boolean_component_certificate','TAIJI_PLUS',lambda r:r['specimen'].update(component_material_certificates={k:True for k in r['specimen']['component_material_bindings']}))
 probe('missing_calibration_identity','TAIJI_PLUS',lambda r:r['calibration'].update(id=None))
 probe('missing_attempt_identity_everywhere','TAIJI_PLUS',lambda r:[e.update(attempt_id=None) for e in r['events']])
 probe('reused_receipt_identity','TAIJI_PLUS',lambda r:event(r,'STORE').update(receipt=event(r,'CLEAN')['receipt']))
 for field in ['approved_service','fresh_arm_token','exclusion_clear','mass_secured_on_release','safe_release_token']:
  probe('guard_false_'+field,'IMPACT',lambda r,field=field:r['guard'].update({field:False}))
  probe('guard_string_'+field,'IMPACT',lambda r,field=field:r['guard'].update({field:'true'}))
  probe('guard_missing_'+field,'IMPACT',lambda r,field=field:r['guard'].pop(field))
 def campaign():
  records=[];allocation={}
  for b in rc.load_packet()['branches']['branches']:
   for i,angle in enumerate([0,7.5,15,22.5,30] if b['id']=='IMPACT' else [0]):
    r=rc.fixture(b['id']);suffix=f"{b['id']}:{i}";r['specimen']['id']=f'synthetic:{suffix}'
    r['conditions'][0]['actual_phase_deg']=angle;r['conditions'][0]['requested_phase_deg']=angle;r['conditions'][0]['id']='synthetic:condition:'+suffix
    allocation.setdefault(b['id'],[]).append(r['conditions'][0]['id'])
    for e in r['events']:e['specimen_id']=r['specimen']['id'];e['occurrence_id']+=':'+suffix;e['condition_id']=r['conditions'][0]['id']
    records.append(r)
  return {'kind':'synthetic_bookkeeping','scope':'whole_paper_physical_execution','records':records,'allocation':allocation,'analysis_ids':['DAMPING_ANALYSIS','COMPARISON_ARCHIVE'],'control_package_ids':['CP_TAIJI_FRAME','CP_PLANETARY','CP_SOFT_FRAME','CP_DAMP','CP_IMPACT'],'claim':'synthetic_contract_acceptance_only'}
 c=campaign();rc.validate_campaign(c)
 first=next(r for r in c['records'] if r['branch_id']=='TAIJI_PLUS');second=next(r for r in c['records'] if r['branch_id']=='MICRO_TAIJI_COMP')
 second['specimen']['id']=first['specimen']['id']
 for e in second['events']:e['specimen_id']=first['specimen']['id']
 try:rc.validate_campaign(c)
 except (ValueError,KeyError,TypeError) as exc:results.append({'name':'cross_family_specimen_id_reuse_campaign','rejected':True,'reason':str(exc),'exception':type(exc).__name__})
 else:results.append({'name':'cross_family_specimen_id_reuse_campaign','rejected':False,'reason':'one specimen ID accepted for incompatible family and dimensions'})
 r1=rc.fixture('IMPACT');r2=copy.deepcopy(r1)
 for ev in r2['events']:ev['occurrence_id']+=':reused'
 selected={'kind':'synthetic_bookkeeping','scope':'selected_branch_episode','records':[r1,r2],'claim':'synthetic_contract_acceptance_only'}
 try:rc.validate_campaign(selected)
 except (ValueError,TypeError,KeyError) as exc:results.append({'name':'selected_campaign_terminal_impact_reuse','rejected':True,'reason':str(exc),'exception':type(exc).__name__})
 else:results.append({'name':'selected_campaign_terminal_impact_reuse','rejected':False,'reason':'same terminal impact instance accepted twice in selected scope'})
 return {'scope':'Independent adversarial synthetic bookkeeping probes only','total':len(results),'rejected':sum(r['rejected'] for r in results),'accepted_invalid':sum(not r['rejected'] for r in results),'results':results}

if __name__=='__main__':
 d=run();print(json.dumps(d,indent=2));raise SystemExit(bool(d['accepted_invalid']))
