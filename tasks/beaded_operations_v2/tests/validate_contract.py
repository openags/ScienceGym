#!/usr/bin/env python3
"""Bounded static contract checks. These tests do not execute a robot or experiment."""
import json, pathlib, hashlib
P=pathlib.Path(__file__).resolve().parents[1]
report=[]
def load(n):return json.loads((P/n).read_text())
def check(name,ok):
 if not ok:raise AssertionError(name)
 report.append({'check':name,'status':'pass'})
def nodes(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from nodes(v)
 elif isinstance(x,list):
  for v in x:yield from nodes(v)
O=load('operations.json');B=load('branches.json');R=load('routes.json');E=load('provenance.json');U=load('unknown_parameters.json')
ops={o['id']:o for o in O['operations']}; bs={b['id']:b for b in B['branches']};rs={r['id']:r['tree'] for r in R['routes']};es={e['id'] for e in E['evidence']};us={u['id'] for u in U['unknown_parameters']}
check('all exported JSON parses',all(load(str(f.relative_to(P))) is not None for f in P.rglob('*.json') if f.name not in ['EXPORT_ALLOWLIST.json']))
check('operation count and unique IDs',len(ops)==O['operation_count']==70)
check('family and branch counts',len(B['families'])==B['family_count']==13 and len(bs)==B['branch_count']==22)
check('route IDs match branch IDs',set(bs)==set(rs) and R['route_count']==22)
check('evidence IDs unique',len(es)==len(E['evidence'])==25)
check('unknown gates unique and no fabricated defaults',len(us)==35 and all(u['default'] is None and not u['blocks_design'] for u in U['unknown_parameters']))
check('operation evidence and unknown references',all(set(o['evidence_ids'])<=es and set(o['unknown_parameter_ids'])<=us for o in ops.values()))
check('branch references resolve',all(set(b['operation_ids'])<=set(ops) and set(b['evidence_ids'])<=es and set(b['required_input_ids'])<=us for b in bs.values()))
check('route operation references resolve',all(n.get('operation_id') in ops for t in rs.values() for n in nodes(t) if n.get('type')=='operation'))
check('mandatory robot embodiment fields',all(all(k in o for k in ['actor','source_workstation','target_workstation','manipulated_objects','tools','actions','preconditions','postconditions']) for o in ops.values()))
check('every hands-on operation belongs to mobile robot',all(o['actor']=='mobile_manipulator_robot' for o in ops.values() if o['kind']=='hands_on'))
check('device handoffs explicit',all(o['device_handoff'] and o['device_handoff']['robot_setup'] in ops and o['device_handoff']['robot_unload'] in ops for o in ops.values() if o['kind']=='device_process'))
check('no physical feasibility claim',all(not any(o['feasibility'].values()) for o in ops.values()))
check('loops never have unknown successful empty defaults',all('semantics' in n and (n.get('values') is not None or n.get('values_from')) for t in rs.values() for n in nodes(t) if n.get('type')=='loop'))
check('preparation origin selected in every leaf route',all(any(n.get('loop_id')=='required_prepared_parts' for n in nodes(rs[i])) for i in bs if i!='WHOLE_PAPER_PRACTICAL'))
check('drilled bead preparation is mandatory source role','acetal_bead_lots_with_matched_drilled_holes' in bs['SHELL_SIZE_CONTROL']['required_preparation_roles'])
check('service load/process/unload and supplied receipt both represented',all({'SERVICE_LOAD','SERVICE_PROCESS','SERVICE_RECEIVE','PART_RECEIVE','APPARATUS_INSTALL'}<=set(b['operation_ids']) for b in bs.values()))
check('friction has one weight and one sensor end',any(n.get('operation_id')=='PULLEY_ROUTE' and n['bindings'].get('hanging_mass_end_count')==1 and n['bindings'].get('end_role_map')=={'A':'hanging_mass_via_pulley','B':'tester_sensor_grip_via_pulley'} for n in nodes(rs['FIXED_RING_FRICTION'])))
check('shell per-end masses are separate',all(any(n.get('operation_id')=='PULLEY_ROUTE' and n['bindings'].get('hanging_mass_end_count')==2 for n in nodes(rs[i])) for i in ['SHELL_NITINOL','SHELL_NYLON']))
check('friction and axial rates not conflated',bs['FIXED_RING_FRICTION']['source_condition_constraints']['source_pull_speed']=={'value':30,'unit':'mm/s'} and bs['ELASTOMERIC_COLUMN']['source_condition_constraints']['speed']=={'value':30,'unit':'mm/min'} and bs['SMA_BEAM_BENDING']['source_condition_constraints']['speed']=={'value':30,'unit':'mm/min'})
chain=next(n for n in nodes(rs['CHAIN_DILATION']) if n.get('loop_id')=='chain_cells')
check('chain order and cycle semantics',chain['values']==list(range(1,16)) and chain['order']=='ascending_from_free_end_required' and any(n.get('loop_id')=='cycles' and n['values']==[1,2,3] for n in nodes(chain)))
check('CT and mechanical chain counts separate',bs['CT_CHAIN8']['source_condition_constraints']['cells']==8 and bs['CHAIN_DILATION']['source_condition_constraints']['cells']==15)
check('friction and dilation ring sets separate',bs['FIXED_RING_FRICTION']['source_condition_constraints']['ring_n']==[3,4,5,6] and bs['SINGLE_RING_DILATION']['source_condition_constraints']['ring_n']==[3,4,5])
check('SMA explicit program operation','SMA_PROGRAM' in bs['SMA_BEAM_BENDING']['operation_ids'])
statecycles=next(n for n in nodes(rs['SMA_BEAM_BENDING']) if n.get('loop_id')=='state_cycles')
check('SMA cycles allocated without per-specimen multiplication',statecycles.get('values') is None and 'cycle_ids' in statecycles['values_from'] and 'count_from' not in statecycles and 'campaign' in bs['SMA_BEAM_BENDING']['source_condition_constraints']['cycle_total_scope'])
ax=next(n for n in nodes(rs['THREAD_MODULUS']) if n.get('loop_id')=='axial_trials')
check('axial trial IDs allocated across coupons',ax.get('values') is None and 'axial_trial_ids' in ax['values_from'])
check('cone n4 cycles not copied to other defect n',bs['CONE_N4_INVERSION']['source_condition_constraints']['central_n']==4 and next(n for n in nodes(rs['CONE_N4_INVERSION']) if n.get('loop_id')=='cone_cycles')['values']==[1,2,3,4])
check('source conflicts preserved',len(load('source_conflicts.json')['conflicts'])==7 and bs['SHELL_NYLON']['source_condition_constraints']['diameter_mm'] is None and bs['CATENARY_RECONFIGURATION']['source_condition_constraints']['thread_material'] is None)
check('no source byte validation falsely asserted',all(not s['locally_byte_complete'] and s['current_source_sha256'] is None for s in E['sources']))
check('CT guarded-service boundary explicit',ops['CT_SCAN']['kind']=='device_process' and 'No scan without qualified guarded service' in load('evaluator_reference.json')['invariants'])
check('SMA safe touch prerequisites',{'power_off_confirmed','cool_state_confirmed'}<=set(ops['SMA_DISCONNECT']['preconditions']))
check('human demonstration is not human-loading protocol',bs['SHELL_TENSION_DEMO']['source_condition_constraints']['human_load_prohibited'] is True)
check('source outcomes withheld from actor','source_outcomes.json' in load('RELEASE_BOUNDARY.json')['withhold'])
check('whole campaign dispatch exactly covers leaves',set(rs['WHOLE_PAPER_PRACTICAL']['selected_branch_ids'])==set(bs)-{'WHOLE_PAPER_PRACTICAL'})
check('part transfers use part identity rather than sample placeholder',all(n.get('bindings',{}).get('object_ids_from','').startswith('part_card.') for t in rs.values() for a in nodes(t) if a.get('loop_id')=='required_prepared_parts' for n in nodes(a) if n.get('operation_id')=='MOVE'))
check('prepared assembly inputs use actual-location batch collection',all(any(n.get('loop_id')=='assembly_component_batches' for n in nodes(rs[i])) for i in bs if i not in ['WHOLE_PAPER_PRACTICAL','THREAD_MODULUS']))
check('analysis preserves physical location',all(o.get('physical_sample_transfer') is False and 'preserve_last_physical_sample_location' in o.get('location_semantics','') for o in ops.values() if o['kind']=='analysis'))
# Tiny allocation validator exercises actual count semantics without generating sensor data.
def valid_sma(blocks):
 ids=[i for b in blocks for i in b['cycle_ids']]
 return len(ids)==len(set(ids)) and all(b['state'] in ['off','on'] for b in blocks) and {s:sum(len(b['cycle_ids']) for b in blocks if b['state']==s) for s in ['off','on']}=={'off':9,'on':12}
check('split SMA allocation accepted',valid_sma([{'state':'off','cycle_ids':list(range(1,5))},{'state':'off','cycle_ids':list(range(5,10))},{'state':'on','cycle_ids':list(range(10,22))}]))
check('multiplied SMA totals rejected',not valid_sma([{'state':'off','cycle_ids':list(range(18))},{'state':'on','cycle_ids':list(range(18,42))}]))
check('duplicate cycle IDs rejected',not valid_sma([{'state':'off','cycle_ids':[1]*9},{'state':'on','cycle_ids':[2]*12}]))
if (P/'EXPORT_ALLOWLIST.json').exists():
 a=load('EXPORT_ALLOWLIST.json')
 check('export files exist and contain no source binaries',all((P/f).is_file() and pathlib.Path(f).suffix in ['.md','.json','.py'] and not pathlib.Path(f).name.startswith('.') for f in a['allowlist']))
 check('export excludes local builder and source pixels','.build_package.py' not in a['allowlist'] and not any(x.endswith(('.pdf','.png','.jpg','.html')) for x in a['allowlist']))
result={'status':'passed','checks_passed':len(report),'checks':report,'scope':'static package contracts and allocation logic only','physical_execution_performed':False,'source_byte_verification':False}
(P/'tests'/'validation_report.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'tests'/'VALIDATION_REPORT.md').write_text('# Static validation\n\n'+str(len(report))+' checks passed. No robot, physical experiment, simulator, CAD, source-byte audit or device-safety validation was performed.\n\n'+''.join('- '+r['check']+'\n' for r in report))
v=load('VERIFICATION.json');v.update(status='static_contract_checks_passed',checks_passed=len(report),report='tests/validation_report.json');(P/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n')
print(str(len(report))+' static checks passed')
