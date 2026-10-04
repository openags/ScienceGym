"""Static source-boundary and cross-reference verification; no source acquisition."""
from pathlib import Path
import json,re
from contract import fixture,validate,BRANCHES,SCENARIOS
ROOT=Path(__file__).resolve().parents[1]

def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate JSON key '+k)
        result[k]=v
    return result

def read(path):return json.loads(path.read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def verify(root=ROOT):
    errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    docs={}
    for p in root.glob('*.json'):
        try:docs[p.name]=read(p)
        except Exception as e:errors.append(str(e))
    required=['branches.json','operations.json','asset_binding_plan.json','source_conflicts.json','unknown_parameters.json','evidence_map.json','RELEASE_BOUNDARY.json','agent_visible.json','control_packages.json','analysis_contracts.json','coverage_matrix.json','material_cards.json','lineage_contract.json']
    for name in required:check(name in docs,'missing '+name)
    if errors:return errors
    branches=docs['branches.json']['branches'];ops=docs['operations.json']['operations'];assets=docs['asset_binding_plan.json']['scene_assets'];conflicts=docs['source_conflicts.json']['conflicts'];unknowns=docs['unknown_parameters.json']['unknown_parameters'];evidence=docs['evidence_map.json']['evidence']
    bids={b['id'] for b in branches};oids={o['id'] for o in ops};aids={a['asset_id'] for a in assets};cids={c['id'] for c in conflicts};uids={u['id'] for u in unknowns};eids={e['id'] for e in evidence}
    check(len(bids)==len(branches)==15,'15 design/hold branches');check(len(oids)==len(ops)==32,'32 operation inventory');check(len(aids)==len(assets)==7,'seven stable asset groups')
    check(cids=={'C_DIRECTION_CROSSREF','C_MOVIE_POINTERS','C_PHYSICAL_RESULTS_POINTER','C_FORCE_PANEL_POINTER'},'source conflict inventory')
    for b in branches:
        check(set(b['operation_ids'])<=oids,'branch operation ref '+b['id']);check(set(b['depends_on'])<=bids,'dependency ref '+b['id']);check(set(b['source_evidence_ids'])<=eids,'branch evidence ref '+b['id']);check(set(b['unknown_parameter_ids'])<=uids,'branch unknown ref '+b['id'])
        check(b['physical_execution_implemented'] is False and b['numerical_execution_implemented'] is False,'execution overclaim')
    for o in ops:check(set(o['asset_ids'])<=aids and set(o['source_evidence_ids'])<=eids,'operation cross-reference '+o['id']);check(o['device_command_implemented'] is False,'device command overclaim')
    for a in assets:check(set(a['bind_operation_ids'])<=oids,'asset operation ref');check(a['physical_geometry_validated'] is False,'physical scene geometry overclaim')
    check(set(x for a in assets for x in a['bind_operation_ids'])==oids,'unbound operations')
    for c in conflicts:check(c['resolved'] is False and c['qualification_gate'] is True,'source conflict silently repaired')
    check(docs['source_conflicts.json']['default_direction_state']=='UNRESOLVED_HOLD','no default direction hold')
    rb=docs['RELEASE_BOUNDARY.json']
    for k in ['whole_paper_complete','real_actuation_implemented','physical_simulation_run','numerical_reproduction_run','source_complete_for_robot_execution','publisher_assets_included','author_code_included','source_dataset_included','external_writes_performed_by_task_author','qualifies_for_full_paper_target_count']:check(rb[k] is False,'release overclaim '+k)
    av=docs['agent_visible.json']
    for k in ['source_outcomes_exposed','can_declare_measurement_success','can_declare_service_qualification','can_submit_raw_observations','physical_implementation']:check(av[k] is False,'actor authority/oracle '+k)
    mat=docs['material_cards.json']['cards'][0];check(mat['nozzle_diameter_mm']==0.4 and mat['layer_fraction_of_nozzle']==0.8 and mat['derived_layer_height_mm']==0.32,'material source parameters')
    metric=docs['analysis_contracts.json']['analyses'][0];check(metric['metric_n']==2 and metric['source_physical_n'] is None and metric['negative_output_preserved'] is True,'metric exponent/sign boundary')
    controls={x['id']:x for x in docs['control_packages.json']['controls']};check(controls['SCALING']['bond_counts']==[172,271,392,543,694,885] and controls['SCALING']['source_total_runs']==600 and controls['SCALING']['executed_runs']==0,'source scaling boundary');check(controls['FORCE']['evaluation_gauge_stiffness']==10 and controls['FORCE']['visualization_gauge_stiffness']==0.01,'force evaluation versus visualization');check(controls['CNN']['split_unit']=='simulation_run' and controls['CNN']['source_image_count']==1163733,'run split/dataset boundary')
    cv=docs['coverage_matrix.json'];check(len(cv['main_sections'])==21 and len(cv['main_figures'])==7 and len(cv['supplement_pages'])==4 and len(cv['movies'])==3,'whole-paper source inventory');check(cv['whole_paper_execution'] is False and cv['completed_real_experiments']==0,'coverage completion inflation')
    for b in BRANCHES:
        for s in SCENARIOS if b!='DIRECTION_HOLD' else ['valid']:
            c,e=fixture(b,s);check(validate(c,e)['accepted'],'fixture rejected '+b+' '+s)
    for p in root.rglob('*'):
        if p.is_symlink():errors.append('symlink forbidden '+p.name)
        if p.is_file() and p.suffix in ('.json','.md','.py'):
            text=p.read_text();check(not re.search('[\u3400-\u9fff]',text),'non-English CJK text '+p.name)
            check(('/'+'workspace/'+'shared/') not in text and ('/'+'workspace/'+'scratch/') not in text,'private filesystem path '+p.name)
    return errors
if __name__=='__main__':
    errors=verify();print(json.dumps(dict(passed=not errors,errors=errors,scope='static bounded task contract only'),indent=2));raise SystemExit(bool(errors))
