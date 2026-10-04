"""Offline structural and source-boundary checks for the original laser design."""
from pathlib import Path
import json
from contract import FIXTURE_IDS, fixture, evaluate
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    def no_duplicates(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('duplicate JSON key '+k)
            result[k]=v
        return result
    return json.loads(path.read_text(),object_pairs_hook=no_duplicates,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid constant '+x)))
def verify(root=ROOT):
    errors=[];checks=0
    def check(test,msg):
        nonlocal checks;checks+=1
        if not test:errors.append(msg)
    try:
        ops=read(root/'operations.json')['operations'];opids=[o['id'] for o in ops]
        plan=read(root/'asset_binding_plan.json');assets=plan['scene_assets'];aids=[a['asset_id'] for a in assets]
        check(len(opids)==44 and len(set(opids))==44,'44 unique operations')
        check(len(aids)==10 and len(set(aids))==10,'10 unique scene asset groups')
        binds=[o for a in assets for o in a['bind_operation_ids']]
        check(sorted(binds)==sorted(opids),'one asset binding per operation')
        for op in ops:
            check(op['asset_ids']==[a['asset_id'] for a in assets if op['id'] in a['bind_operation_ids']],'operation binding '+op['id'])
            check(op['device_command_implemented'] is False and op['physical_execution_authority'] is False,'hardware authority '+op['id'])
            check(all(op.get(k) for k in ('precondition','required_output','failure','source_evidence_ids')),'operation contract '+op['id'])
        branches=read(root/'branches.json')['branches'];ids=[b['id'] for b in branches]
        check(len(ids)==15 and len(set(ids))==15,'15 scientific design routes')
        check(set(ids)<=set(b for o in ops for b in o['branch_ids']), 'every scientific branch has operation bindings')
        for b in branches:
            check(b['design_covered'] is True and b['physical_executed'] is False and b['numerical_executed'] is False,'completion scope '+b['id'])
            check(all(b.get(k) for k in ('required_inputs','design_sequence','required_outputs','interpretation_limit')),'branch data contract '+b['id'])
        check(next(b for b in branches if b['id']=='SIN_NUMERICAL_EXAMPLE')['execution_class']=='design_only','SiN numerical only')
        coverage=read(root/'coverage_matrix.json')
        check(len(coverage['main_figures'])==6 and len(coverage['supplementary_notes'])==6 and len(coverage['supplementary_figures'])==8 and len(coverage['supplementary_tables'])==2 and coverage['supplementary_pages_read']==17,'full source coverage')
        check(all(coverage['main_figures'].values()) and all(coverage['supplementary_notes'].values()),'source-to-route coverage')
        boundary=read(root/'RELEASE_BOUNDARY.json');check(boundary['whole_paper_design_accounted_for'] is True and boundary['whole_paper_execution_complete'] is False,'design/execution boundary')
        actor=read(root/'agent_visible.json');check(sorted(actor['allowed_operations'])==sorted(opids),'actor operations')
        check(actor['source_outcomes_exposed'] is False and actor['can_declare_measurement'] is False and actor['can_declare_service_qualification'] is False and actor['can_supply_physical_observation'] is False,'actor outcome boundary')
        check(not any(t in json.dumps(actor) for t in ('4.28','400.3','240.3','140.1','source_outcomes.json','tests/contract.py','fixture')),'actor projection leak')
        check({'FINAL_VERSION_AUTHORITY','SIN_DENSITY','PROCESS_VS_THICKNESS','POWER_PLANES','BIAS_POWER_SCOPE'}<=set(x['id'] for x in read(root/'source_conflicts.json')['items']),'source caveats')
        so=read(root/'source_outcomes.json');check(so['visibility']=='evaluator_reference_only' and so['completion_thresholds'] is False,'source outcomes boundary')
        check(so['analysis_context']['independent_RBW_Hz']==200 and so['sin_model_parameters']['servo_BW_MHz']==1,'source analysis context')
        for fid in FIXTURE_IDS:
            f=fixture(fid);check(evaluate(f['events'],f['receipts'],fid)['contract_passed'],'synthetic lifecycle '+fid)
        for p in root.rglob('*.json'):
            if '__pycache__' not in p.parts:read(p);check(True,'JSON '+p.name)
        for p in root.rglob('*'):
            if p.is_file() and p.suffix in ('.json','.md','.py'):
                content=p.read_text();check(('/'+'workspace'+'/') not in content and ('/'+'root'+'/') not in content,'private path '+p.name)
    except (OSError,ValueError,KeyError,TypeError) as exc:errors.append('package error '+str(exc))
    return dict(passed=not errors,checks=checks,errors=errors,scope='design structure and authored synthetic contract only')
if __name__=='__main__':
    r=verify();print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
