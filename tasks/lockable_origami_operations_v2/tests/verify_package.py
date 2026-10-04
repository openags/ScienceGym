"""Read-only structural checks of original task design; not scientific validation."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('duplicate JSON key '+k)
        d[k]=v
    return d
def read(p):return json.loads(Path(p).read_text(),object_pairs_hook=no_duplicates,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite '+v)))
def verify(root=ROOT):
    root=Path(root);errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    try:
        docs={p.name:read(p) for p in root.glob('*.json') if p.name!='EXPORT_ALLOWLIST.json'}
        b=docs['branches.json']['branches'];ops=docs['operations.json']['operations'];ev=docs['evidence_map.json']['evidence'];bid={x['id'] for x in b};oid={x['id'] for x in ops};eid={x['id'] for x in ev};assets=docs['asset_binding_plan.json']['scene_assets'];aid={x['asset_id'] for x in assets}
        check(len(b)==len(bid)==30,'30 unique design routes');check(len(ops)==len(oid)==60,'60 unique operations');check(len(ev)==len(eid)==110,'110 unique evidence locators')
        check(len(assets)==len(aid)==11,'11 unique asset groups');check(sum(len(a['required_anchor_ids']) for a in assets)==53,'53 semantic anchors')
        check(set(docs['agent_visible.json']['allowed_operations'])==oid,'actor operation set');check(docs['evaluator_reference.json']['actor_visible_allowlist']==['agent_visible.json'],'actor projection')
        for x in b:
            check(set(x['source_evidence_ids'])<=eid,'unresolved branch evidence '+x['id']);check(set(x['operation_ids'])<=oid,'unresolved branch operations '+x['id']);check(x['design_covered'] is True and x['physical_executed'] is False and x['numerical_executed'] is False,'branch execution boundary '+x['id'])
        for o in ops:
            check(set(o['source_evidence_ids'])<=eid,'unresolved operation evidence '+o['id']);check(set(o['asset_ids'])<=aid,'unresolved operation asset '+o['id']);check(set(o['branch_ids'])<=bid,'unresolved operation branch '+o['id']);check(o['device_command_implemented'] is False and o['physical_execution_authority'] is False,'operation execution boundary '+o['id'])
        bound=[o for a in assets for o in a['bind_operation_ids']];check(set(bound)==oid and len(bound)==len(set(bound)),'exact one-group operation binding')
        for a in assets:
            check(a['physical_geometry_validated'] is False,'asset geometry boundary')
            check(len(a['required_anchor_ids'])==len(set(a['required_anchor_ids'])),'duplicate anchor within group')
        for c in docs['source_conflicts.json']['conflicts']:
            check(set(c['branch_ids'])<=bid and set(c['source_evidence_ids'])<=eid,'unresolved source conflict '+c['id'])
        check(len(docs['source_conflicts.json']['conflicts'])==11,'eleven conflicts/scopes')
        cov=docs['coverage_matrix.json']
        for key,n in [('main_figures',6),('supplementary_notes',11),('supplementary_figures',14),('supplementary_tables',3),('supplementary_videos',12)]:
            check(len(cov[key])==n,'source coverage '+key)
            for refs in cov[key].values():check(bool(refs) and set(refs)<=bid,'empty/unresolved coverage '+key)
        audit=docs['source_access_audit.json'];check(audit['main_read']['visual_figures']==list(range(1,7)),'main figures');check(audit['si_read']['pdf_pages']==37,'SI pages');check(audit['movie_read']['continuous_playback'] is False,'movie scope')
        check(audit['movie_read']['numerical_movies']==list(range(4,11)),'numeric movie separation')
        status=docs['STATUS.json'];check(status['operation_count']==60 and status['design_route_count']==30,'status counts');check(status['whole_paper_execution_complete'] is False,'status execution boundary')
        for key in ['full_paper_execution_eligible','whole_paper_complete','qualifies_for_full_paper_execution_count','scientific_reproduction_run','physical_geometry_validated']:check(status[key] is False,'status gate '+key)
        boundary=docs['RELEASE_BOUNDARY.json']
        for key in ['whole_paper_execution_complete','physical_execution','numerical_execution','scientific_reproduction','source_files_exported','exact_geometry_validated']:check(boundary[key] is False,'release boundary '+key)
        check(boundary['validated_runnable_whole_paper_tasks']==0,'zero executable tasks')
        for p in root.rglob('*'):
            if p.is_file() and p.suffix in ('.json','.md','.py'):
                text=p.read_text();check(('/'+'workspace/') not in text and ('/'+'root/') not in text and ('sediment'+':/'+'/') not in text,'private path exported '+p.name)
        return errors
    except (OSError,ValueError,KeyError,TypeError) as e:return errors+['package unreadable: '+str(e)]
if __name__=='__main__':
    errors=verify();print(json.dumps({'passed':not errors,'errors':errors},indent=2));sys.exit(bool(errors))
