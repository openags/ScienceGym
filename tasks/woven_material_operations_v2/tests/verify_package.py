"""Structural/source-boundary checks; no physical or numerical solver execution."""
from pathlib import Path
import json
from contract import FIXTURE_IDS,fixture,evaluate
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('duplicate JSON key '+k)
            out[k]=v
        return out
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('invalid constant '+x)))
def verify(root=ROOT):
    root=Path(root);errors=[];checks=0
    def check(ok,msg):
        nonlocal checks
        checks+=1
        if not ok:errors.append(msg)
    try:
        ops=read(root/'operations.json')['operations'];oi=[o['id'] for o in ops];assets=read(root/'asset_binding_plan.json')['scene_assets'];ai=[a['asset_id'] for a in assets];branches=read(root/'branches.json')['branches'];bi=[b['id'] for b in branches];ev=read(root/'evidence_map.json')['entries'];ei=[e['id'] for e in ev];si=[s['id'] for s in read(root/'source_access_audit.json')['source_ids']]
        check(len(oi)==len(set(oi))==48,'48 unique operations');check(len(ai)==len(set(ai))==11,'11 unique assets');check(len(bi)==len(set(bi))==24,'24 unique branches');check(len(ei)==len(set(ei)),'unique evidence');check(all(e['source_id'] in si and e.get('locator') for e in ev),'resolved evidence')
        check(sorted(op for a in assets for op in a['bind_operation_ids'])==sorted(oi),'exact operation/asset parity')
        for a in assets:check(a['physical_geometry_validated'] is False and len(a['required_anchor_ids'])==len(set(a['required_anchor_ids'])),'asset qualification '+a['asset_id'])
        for o in ops:
            check(o['asset_ids']==[a['asset_id'] for a in assets if o['id'] in a['bind_operation_ids']],'asset map '+o['id']);check(o['device_command_implemented'] is False and o['physical_execution_authority'] is False,'hardware authority '+o['id']);check(all(o.get(k) for k in ('precondition','required_output','failure','source_evidence_ids','branch_ids')),'operation contract '+o['id']);check(set(o['source_evidence_ids'])<=set(ei),'operation evidence '+o['id']);check(set(o['branch_ids'])<=set(bi),'operation branches '+o['id'])
        for b in branches:
            check(b['design_covered'] is True and b['physical_executed'] is False and b['numerical_executed'] is False,'completion '+b['id']);check(all(b.get(k) for k in ('required_inputs','design_sequence','required_outputs','interpretation_limit')),'branch contract '+b['id']);check(set(b['source_evidence_ids'])<=set(ei),'branch evidence '+b['id']);check(any(b['id'] in o['branch_ids'] for o in ops),'branch operations '+b['id'])
        conflicts=read(root/'source_conflicts.json')['items'];ci={c['id'] for c in conflicts};check({'TETRA_STRAND_COUNT','CUBIC_MODULAR_RULE','PATTERN_AXIS_ORDER','FAILURE_VARIABLE','CONTINUUM_SUPPORT','PLASMA_COATING_ORDER','PATTERN_PARAMETER_MAP','RADIUS_EXAMPLE','NORMALIZATION','GRADIENT_UNITS','SIZE_SCOPE'}<=ci,'source conflicts')
        for c in conflicts:check(set(c['source_evidence_ids'])<=set(ei),'conflict evidence '+c['id'])
        check(next(b for b in branches if b['id']=='TETRAKAIDECAHEDRON_HOLD')['execution_class']=='conflict_hold','tetra scoped hold');check(all(next(b for b in branches if b['id']==t)['execution_class']=='closed_qualified_service' for t in ('TENSION_BCC','TENSION_CUBIC')),'BCC/cubic unheld')
        cov=read(root/'coverage_matrix.json');check(cov['supplementary_pages_read']==22 and len(cov['main_figures'])==5 and len(cov['supplementary_notes'])==5 and len(cov['supplementary_figures'])==17 and len(cov['supplementary_videos'])==5,'full written coverage')
        for group in ('main_figures','supplementary_notes','supplementary_figures','supplementary_videos'):
            for v in cov[group].values():check(set(v if type(v) is list else [v])<=set(bi),'coverage mapping')
        actor=read(root/'agent_visible.json');check(actor['allowed_operations']==sorted(oi),'actor operations');check(all(actor[k] is False for k in ('source_outcomes_exposed','can_declare_measurement','can_declare_service_qualification','can_supply_physical_observation','physical_implementation')),'actor authority');check(not any(t in json.dumps(actor) for t in ('source_outcomes.json','contract.py','0.0377','fixture','8/3','7/3')),'actor leakage')
        for name in ('RELEASE_BOUNDARY.json','STATUS.json'):
            d=read(root/name);check(d['whole_paper_design_accounted_for'] is True and d['whole_paper_execution_complete'] is False and d['full_paper_execution_eligible'] is False,'completion boundary '+name)
        out=read(root/'source_outcomes.json');check(out['visibility']=='evaluator_reference_only' and out['completion_thresholds'] is False,'outcome target boundary');p=read(root/'provenance.json');check(p['doi']=='10.1038/s41467-026-68298-3' and p['source_license']=='CC BY-NC-ND 4.0' and p['source_files_exported'] is False,'rights')
        routes=read(root/'preparation_routes.json')['routes'];support=next(x for x in routes if x['id']=='FULL_SUPPORT');check(support['source_order_between_plasma_and_coating']=='unspecified' and support['requires_external_order_card'] is True,'partial order');check(next(x for x in routes if x['id']=='PREPARED')['preparation_credit'] is False,'prepared credit')
        for fid in FIXTURE_IDS:
            f=fixture(fid);r=evaluate(f['events'],f['receipts'],fid);check(r['contract_passed'] and not r['physical_execution'] and not r['numerical_solver_execution'],'fixture '+fid)
        for p in root.rglob('*.json'):
            if '__pycache__' not in p.parts:read(p);check(True,'strict JSON')
        for p in root.rglob('*'):
            if p.is_file() and p.suffix in ('.json','.md','.py'):
                t=p.read_text();check(not any(x in t for x in ('/'+'workspace/','/'+'tmp/','/'+'home/')),'private path '+p.name)
    except (KeyError,TypeError,ValueError,OSError,StopIteration) as exc:errors.append('invalid package: '+str(exc))
    return dict(passed=not errors,checks=checks,errors=errors)
if __name__=='__main__':
    r=verify();print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
