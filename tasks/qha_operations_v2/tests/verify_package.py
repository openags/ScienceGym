"""Static authored package validation; no science or hardware execution."""
from pathlib import Path
import json,hashlib,sys

def validate(root):
 root=Path(root);n=0
 def check(x,m):
  nonlocal n;n+=1
  if not x:raise ValueError(m)
 def J(f):return json.loads((root/f).read_text())
 source=J('source_packet_reference.json')
 for f in source['retained_files']:
  b=(root/f['path']).read_bytes();check(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'source annotation mutated '+f['path'])
 check(len(J('source_facts.json')['facts'])==29,'29 facts required')
 check(len(J('source_conflicts.json')['items'])==18,'18 conflicts required')
 check(len(J('source_outcomes_reference.json')['outcomes'])==14,'14 outcomes required')
 check(len(J('unknown_inputs.json')['items'])==20,'20 unknowns required')
 check(all(x['value'] is None for x in J('unknown_inputs.json')['items']),'unknown default invented')
 route=J('route_proposal.json')['steps'];ops=J('operations.json')['operations'];ids=[f'R{i:02d}'for i in range(15)]
 check([x['id']for x in route]==ids==[x['id']for x in ops],'complete route missing')
 b=J('shared_binding_contract.json');bindings={r['route_id']:r for r in b['route_bindings']};check(set(bindings)==set(ids),'scene route binding incomplete')
 check(len(b['assets'])==11,'eleven asset groups required')
 anchors={a['anchor_id']for x in b['assets']for a in x['anchors']};check(len(anchors)==32,'32 unique anchors required')
 check(all(a['mode']=='evidence_only' and a['physical_actuation_enabled'] is False for x in b['assets']for a in x['anchors']),'physical anchor enabled')
 check({x['id'] for x in J('station_contracts.json')['stations']}=={f'ST{i:02d}'for i in range(1,9)},'station dropped')
 for a,o in zip(route,ops):
  for key in ['id','depends_on','stations','unresolved_inputs','required_evidence','guards','failure_closeout']:check(a[key]==o[key],'route field changed '+a['id']+key)
  check(o['asset_ids']==bindings[o['id']]['asset_ids'],'asset IDs mismatch')
  check(o['anchor_ids']==bindings[o['id']]['target_anchor_ids'],'anchor IDs mismatch')
  check(set(o['anchor_ids'])<=anchors,'unknown anchor')
  check(o['physical_execution_enabled'] is False,'operation enabled')
  check(o['action_interface']=={'allowed_keys':['operation_id','evidence_ids'],'numeric_or_hardware_arguments_allowed':False},'hardware interface')
 check(next(o for o in ops if o['id']=='R14')['depends_on']==['R03'],'closeout improperly gated on analysis')
 check(b['identity_invariants']['subarray_nominal_ohms_approx']==109 and b['identity_invariants']['whole_device_nominal_ohms_approx']==219,'topology conflated')
 check(b['identity_invariants']['physical_chip_count']==1 and b['identity_invariants']['elements_per_subarray']==118 and b['identity_invariants']['total_elements']==236,'chip identity/count changed')
 check(J('measurement_contract.json')['new_measurements']==[],'invented new observation')
 check(J('measurement_contract.json')['numeric_measurement_generator'] is False,'scientific generator enabled')
 check(J('analysis_holds.json')['resolutions']==[] and J('analysis_holds.json')['approved_algorithms']==[],'analysis silently resolved')
 check({'AH_ALLAN_INPUT','AH_ALLAN_ERROR','AH_LOOP'}<={x['id'] for x in J('analysis_holds.json')['holds']},'printed equation holds missing')
 check(all(x is None for x in J('repeat_contract.json')['unit_counts'].values()),'replicate count invented')
 check(J('device_lease_contract.json')['initial_leases']==[],'actual leases invented')
 graph=J('cross_device_measurements.json')['source_graph'];check(len(graph['direct_edges'])==5 and len(graph['nodes'])==4 and graph['connected_graph_independent_cycle_count']==2 and graph['simple_closed_loop_count']==3,'graph semantics wrong')
 boundary=J('release_boundary.json');check(boundary['validated_runnable_whole_paper_tasks']==0 and boundary['hardware_actions']==0 and boundary['physical_simulations']==0 and boundary['physical_execution_enabled'] is False,'overclaimed execution')
 actor=J('agent_visible.json');check(actor['source_context_in_actor_view'] is False and actor['physical_execution_enabled'] is False,'actor contamination')
 check('source_outcomes_reference.json' not in json.dumps(actor),'outcomes leaked to actor view')
 check(J('coverage_map.json')['written_main_pages']==list(range(1,10)) and J('coverage_map.json')['written_SI_pages']==list(range(1,5)),'source coverage missing')
 check(J('workflow.json')['actual_started_jobs']==[] and J('workflow.json')['actual_closed_jobs']==[],'physical history fabricated')
 return {'status':'PASS','checks':n,'physical_execution_enabled':False,'scope':'static metadata only'}
if __name__=='__main__':
 print(json.dumps(validate(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]),indent=2))
