"""Strict original structural checks; no physical or scientific validation."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
class ValidationError(ValueError):pass
def read(name):
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise ValidationError('duplicate key')
   out[k]=v
  return out
 return json.loads((ROOT/name).read_text(),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValidationError('nonfinite JSON')))
def verify():
 checks=[]
 def check(ok,name):
  if not ok:raise ValidationError(name)
  checks.append(name)
 for p in ROOT.rglob('*.json'):read(p.relative_to(ROOT).as_posix())
 ops=read('operations.json')['operations'];branches=read('branches.json')['branches'];stations=read('station_contracts.json')['stations'];unknowns=read('unknown_parameters.json')['unknowns'];facts=read('source_parameters.json')['facts'];binding=read('asset_binding_plan.json');by_op={o['id']:o for o in ops}
 check([o['id'] for o in ops]==[f'R{i:02}' for i in range(1,23)],'22 unique ordered operations')
 check([b['id'] for b in branches]==[f'B{i:02}' for i in range(1,9)],'eight unique mandatory branches')
 check([s['id'] for s in stations]==[f'S{i:02}' for i in range(1,6)],'five stations')
 check([u['id'] for u in unknowns]==[f'U{i:02}' for i in range(1,15)],'14 unresolved cards')
 check(len(read('controls_and_repeats.json')['controls'])==12,'12 controls')
 check(len(read('coverage_matrix.json')['coverage'])==14,'14 whole-paper coverage records')
 check(len(read('source_conflicts.json')['items'])==10,'ten source conflicts')
 check(len(facts)==22,'22 source fact/review records')
 seen=set()
 for o in ops:
  check(set(o['depends_on'])<=seen,o['id']+' dependency order');seen.add(o['id'])
  check(bool(o['substeps']) and bool(o['inputs']) and bool(o['outputs']) and bool(o['entry_guards']) and bool(o['failure_closeout']),o['id']+' complete route fields')
  check(set(o['source_anchors'])<={f['id'] for f in facts},o['id']+' known source anchors')
  check(o['physical_execution_qualified'] is False and o['runtime']=='unimplemented',o['id']+' no physical runtime')
 for b in branches:
  check(b['required_for_whole_paper_design'] is True and set(b['operations'])<=set(by_op),b['id']+' mandatory known operations')
  check(b['execution_status']=='HOLD_QUALIFICATION' and b['condition_slot_provenance']=='source_reference_not_hardware_command',b['id']+' bounded source slots')
 expected={'B01':4,'B02':8,'B03':2,'B04':10,'B05':9,'B06':15,'B07':4,'B08':3}
 for b in branches:check(len(b['condition_slots'])==expected[b['id']],b['id']+' condition counts')
 bs={b['id']:b for b in branches}
 check(bs['B03']['detector_mode']=='analog' and bs['B03']['condition_slots'][0]['grid']==[16,16] and bs['B03']['condition_slots'][0]['source_rate_reference_Hz_approx']==10,'10 Hz source reference is analog 16x16')
 check(bs['B03']['condition_slots'][1]['source_rate_reference_Hz_approx']==2.5 and bs['B03']['movie_playback_is_acquisition_time'] is False,'32x32 and playback distinction')
 check(bs['B05']['detector_mode'] is None and bs['B05']['required_gap']=='U14' and all(x['exposure_policy'] is None for x in bs['B05']['condition_slots']),'B05 missing mode and exposure remain explicit')
 check(bs['B01']['detector_mode']=='spatial_diagnostic' and bs['B01']['full_set_SFG_established'] is False,'spatial sensor and limited SFG scope')
 check(all(u['physical_default'] is None and u['resolved'] is False for u in unknowns),'no fabricated numeric defaults or closed gaps')
 check(all(set(u['operation_ids'])<=set(by_op) for u in unknowns),'unknown operation binding')
 check(binding['asset_pack_id']=='midinfrared_scene_assets_v1','named paired scene')
 check([x['operation_id'] for x in binding['operation_bindings']]==list(by_op),'all operation bindings')
 for b in binding['operation_bindings']:
  op=b['operation_id'];check(b['asset_ids']==by_op[op]['asset_ids'],op+' asset membership equality')
  check(b['root_node_ids']==['ASSET.'+x for x in b['asset_ids']],op+' canonical roots')
  check(b['anchor_ids']==['ANCHOR.'+op+'.primary','ANCHOR.'+op+'.control'],op+' anchor convention')
  check(b['physical_qualified'] is False,op+' nominal binding only')
  if 'primary_asset_id' in b:check(b['primary_asset_id'] in b['asset_ids'] and bool(b['primary_target']) and bool(b['control_target']),op+' concrete target selectors')
 check({a for b in binding['operation_bindings'] for a in b['asset_ids']}=={f'A{i:02}' for i in range(1,14)},'all 13 asset families used')
 if binding['status']=='frozen_nominal_pairing':
  check(len(binding['final_asset_hashes'])>=5,'final semantic asset hash pins')
  check(all(re.fullmatch('[0-9a-f]{64}',x['sha256']) and type(x['bytes']) is int and x['bytes']>0 for x in binding['final_asset_hashes']),'asset hash formats')
 actor=read('agent_visible.json');check(actor['permitted_actor_message_fields']==['event_id','operation_id','evidence_id'],'actor exact proposal surface')
 check(read('evaluator_reference.json')['isolation_implemented'] is False,'isolation gap explicit')
 check(read('RELEASE_BOUNDARY.json')['validated_runnable_whole_paper_tasks']==0,'zero runnable tasks')
 for k in ['whole_paper_execution_complete','physical_execution','physical_simulation','scientific_reproduction','source_data_reanalysis','source_files_exported','exact_geometry_validated','hardware_safety_qualified','repository_changes','remote_writes']:check(read('RELEASE_BOUNDARY.json')[k] is False,k+' false')
 check(read('source_access_audit.json')['sources'][0]['pages']==9 and read('source_access_audit.json')['sources'][1]['pages']==12,'accepted main/SI scope')
 check(all(x['source_file_exported'] is False for x in read('source_access_audit.json')['sources']),'no source export')
 check(read('controls_and_repeats.json')['authored_repeat_plan']['number_of_independent_runs'] is None,'repeats not invented')
 check(read('lineage_contract.json')['required_entities'] and read('lineage_contract.json')['raw_record_fields'],'lineage and raw schema')
 check({t['id'] for t in read('transport_routes.json')['transfers']}=={f'T{i:02}' for i in range(1,7)},'six preparation/sample transfer routes')
 return {'passed':True,'structural_checks':len(checks),'physical_execution':False,'physical_simulation':False,'validated_runnable_whole_paper_tasks':0}
if __name__=='__main__':
 try:print(json.dumps(verify(),indent=2))
 except (ValidationError,KeyError,TypeError,OSError,ValueError) as e:print(str(e));sys.exit(1)
