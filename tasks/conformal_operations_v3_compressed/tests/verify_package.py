"""Structural and semantic checks of the authored design, not physical validation."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
class PackageError(ValueError):pass
def read(name,root=ROOT):return json.loads((Path(root)/(name if name.endswith('.json') else name+'.json')).read_text())
def verify(root=ROOT):
 root=Path(root);checks=[]
 def need(ok,msg):
  if not ok:raise PackageError(msg)
  checks.append(msg)
 def r(n):return read(n,root)
 ops=r('operations')['operations'];branches=r('branches')['branches'];facts=r('source_parameters')['facts'];gaps=r('unknown_parameters')['unknowns'];conflicts=r('source_conflicts')['conflicts'];assets=r('asset_binding_plan')['operation_bindings'];stations=r('station_contracts')['stations'];controls=r('controls_and_repeats')['controls']
 for rows,prefix,n,label in [(ops,'R',16,'operations'),(branches,'B',9,'branches'),(facts,'F',28,'facts'),(gaps,'U',16,'gaps'),(conflicts,'C',5,'conflicts'),(stations,'S',8,'stations'),(controls,'K',9,'controls')]:need([x['id'] for x in rows]==[f'{prefix}{i:02}' for i in range(1,n+1)],'exact '+label+' IDs')
 opids={o['id'] for o in ops};factids={f['id'] for f in facts};gapids={u['id'] for u in gaps};stationids={s['id'] for s in stations}
 for o in ops:
  need(o['classification']=='authored_robot_translation','authored '+o['id']);need(o['runtime']=='unimplemented' and o['physical_execution_qualified'] is False,'runtime boundary '+o['id']);need(o['service_request_is_completion'] is False,'request boundary '+o['id'])
  for k in ['inputs','outputs','entry_guards','observations_to_record','source_anchors','execution_gaps','substeps','asset_ids']:need(type(o[k]) is list and len(o[k])>0,'operation content '+o['id']+' '+k)
  need(bool(o['failure_closeout']),'failure closeout '+o['id']);need(set(o['source_anchors'])<=factids,'source refs '+o['id']);need(set(o['execution_gaps'])<=gapids,'gap refs '+o['id']);need(set(o['depends_on'])<=opids,'dependency refs '+o['id']);need(all(x<o['id'] for x in o['depends_on']),'design DAG '+o['id']);need(set(o['station'].split('+'))<=stationids,'station refs '+o['id'])
 need(len({a for o in ops for a in o['asset_ids']})==12,'all 12 asset families')
 for b in branches:
  need(set(b['route_operations'])<=opids and set(b['source_anchors'])<=factids,'branch refs '+b['id']);need(b['required_for_whole_paper_design'] is True,'branch required '+b['id'])
 need([b['id'] for b in branches if b['classification']=='physical_experiment']==['B02','B03'],'only two physical experiments')
 for b in branches:
  if b['id'] in ('B04','B05','B07','B08'):need(b['execution_status']=='DOCUMENTED_UNEXECUTED','nonmanual '+b['id'])
 for bid,stroke,speed in [('B02',20,.1),('B03',40,.2)]:
  c=next(b for b in branches if b['id']==bid)['source_reference_cycle'];need(c=={'stroke_mm':stroke,'speed_mm_s':speed,'frames':400,'acquisition_fps':1,'playback_fps':30,'hardware_command':False,'safety_threshold':False},'source cycle distinct from commands '+bid)
 for u in gaps:
  need(u['physical_default'] is None and u['execution_blocking'] is True and u['resolution_requires_independent_evidence'] is True,'gap boundary '+u['id']);need(u['operation_ids']==[o['id'] for o in ops if u['id'] in o['execution_gaps']],'gap coverage '+u['id'])
 for c in conflicts:need(bool(c['source_a']) and bool(c['source_b']) and bool(c['treatment']),'preserved conflict '+c['id'])
 need(conflicts[-1]['reported_Pa_m3']==125 and abs(conflicts[-1]['arithmetic_result_Pa_m3']-15.663459025787105)<1e-12,'C05 printed and scalar check both retained')
 need(r('analysis_contracts')['implemented_scientific_solver'] is False,'no scientific solver');need(r('analysis_contracts')['no_silent_source_correction'] is True,'conflicts not silently resolved')
 need(r('analysis_contracts')['boundary_inference']['detF_positive_required'] is True and r('analysis_contracts')['boundary_inference']['global_injectivity_requires_separate_qualified_check'] is True,'orientation and global geometry separate')
 need(r('analysis_contracts')['literature_99_percent_is_global_pass_threshold'] is False and r('analysis_contracts')['ideal_alpha_interval_is_safety_limit'] is False,'no source target/safety threshold')
 cov=r('coverage_matrix');need([x['branch_id'] for x in cov['coverage']]==[b['id'] for b in branches],'all branches covered');need(set(cov['notes'])==set(str(i) for i in range(1,11)),'all ten SI notes');need(len(cov['figures'])==7,'main and grouped SI figure scope')
 for row in cov['coverage']:need(row['missing_parameters_explicit'] is True,'coverage gaps '+row['branch_id'])
 rep=r('controls_and_repeats');need(rep['frames_are_not_independent_specimens'] is True,'frames not n');need(rep['repeat_policy']['must_be_frozen_before_outcomes'] is True,'prospective repeats')
 for k in ['independent_specimens','runs_per_condition','cycle_order','recovery_criterion','stopping_rule']:need(rep['repeat_policy'][k] is None,'unresolved repeat input '+k)
 for s in stations:need(s['commissioned'] is False,'uncommissioned station '+s['id'])
 need(r('preparation_routes')['request_is_completion'] is False and r('preparation_routes')['service_internal_instructions'] is None,'closed fabrication scope')
 need(r('transport_routes')['no_hinge_or_pad_grip'] is True,'supported grip');need(len(r('transport_routes')['transfers'])==6,'preparation and final transfers')
 need(r('lifecycle_contract')['failure_closeout_from_any_operation'] is True and r('lifecycle_contract')['failure_requires_analysis_success'] is False,'failure bypasses scientific success')
 need(r('operations')['global_failure_transition']['from']=='any operation including R01 and R12-R15','failure route includes analysis and planning')
 need(r('recovery_boundaries')['safe_request_is_safe_observation'] is False,'safe observation required')
 for k in ['physical_runtime_available','actor_cannot_self_authorize','null_blocks_execution']:need(r('episode_input_contract')[k] is (False if k=='physical_runtime_available' else True),'episode '+k)
 need(r('agent_visible')['permitted_actor_message_fields']==['event_id','operation_id','evidence_id'],'actor fields');need(r('evaluator_reference')['actor_visible_allowlist']==['agent_visible.json'],'actor visibility');need(r('evaluator_reference')['filesystem_isolation_implemented'] is False and r('evaluator_reference')['sensor_authentication_implemented'] is False,'security limits explicit')
 access=r('source_access_audit');need(len(access['sources'])==5 and len(access['media'])==3,'source/access inventory')
 need(next(x for x in access['sources'] if x['id']=='MAIN')['page_count']==9,'main page scope');need(next(x for x in access['sources'] if x['id']=='SI')['page_count']==16,'SI page scope')
 for m in access['media']:need(m['decode_all_frames_succeeded'] is True and len(m['sampled_frame_numbers'])==5 and m['exported'] is False,'sampled movie boundary '+m['id'])
 archives=access['data_code_archive_status'];need(len(archives['archives'])==6 and all(x['contents_read'] is False for x in archives['archives']),'archives unread');need(archives['source_code_executed'] is False and archives['final_journal_figure_equivalence_verified'] is False,'version/code boundary')
 need(r('source_outcomes')['visibility']=='evaluator_reference_only' and all(x['not_for_agent_target'] for x in r('source_outcomes')['outcomes']),'source outcomes evaluator only')
 boundary=r('RELEASE_BOUNDARY');need(boundary['paper_level_designs']==1 and boundary['validated_runnable_whole_paper_tasks']==0,'paper count boundary')
 for k in ['whole_paper_execution_complete','physical_execution','physical_simulation','scientific_reproduction','source_data_reanalysis','source_files_exported','exact_geometry_validated','hardware_safety_qualified','repository_changes','remote_writes']:need(boundary[k] is False,'release '+k)
 need([x['operation_id'] for x in assets]==[o['id'] for o in ops],'all operation asset bindings')
 for x,o in zip(assets,ops):need(x['asset_ids']==o['asset_ids'] and x['root_node_ids']==['ASSET.'+a for a in x['asset_ids']] and x['anchor_ids']==['ANCHOR.'+o['id']+'.primary','ANCHOR.'+o['id']+'.control'],'asset interface '+o['id'])
 need(r('asset_binding_plan')['status'] in ('awaiting_asset_freeze','frozen_nominal_pairing'),'pairing status')
 result={'passed':True,'checks_passed':len(checks),'paper_designs':1,'operations':16,'branches':9,'physical_experimental_branches':2,'source_facts':28,'execution_gaps':16,'source_conflicts':5,'physical_execution':False,'physical_simulation':False,'validated_runnable_whole_paper_tasks':0}
 return result
if __name__=='__main__':
 try:print(json.dumps(verify(),indent=2))
 except (PackageError,OSError,KeyError,ValueError) as e:print(str(e));sys.exit(1)
