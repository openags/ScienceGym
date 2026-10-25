"""Bind author comparisons to the tested asset revision and browser captures.

No automated or owner acceptance is granted. Resource associations identify
review obligations; they do not supply manipulation bindings to an actor.
"""
import json
from pathlib import Path
from geometry_tools import HERE, ROOT, sha, write_json


def build():
    paths=[HERE/'preparation_review_inputs.json',HERE/'supply_sources.json',
           HERE/'supplies.json',HERE/'supply_checks.json',HERE/'scene.json',
           HERE/'readiness.json',ROOT/'viewer/lab_review_v1/VISUAL_VERIFICATION.json',Path(__file__)]
    notes,sources,supplies,checks,scene,readiness,visual=[json.loads(p.read_text()) for p in paths[:-1]]
    assert checks['checks_passed'] and checks['supplies_sha256']==sha(HERE/'supplies.json')
    assert visual['passed']
    for item in visual['source_files']:
        assert sha(ROOT/item['path'])==item['sha256'],item['path']
    captures={Path(c['path']).stem:c for c in visual['captures']}
    items=[]
    for note in notes['items']:
        key=note['source_record'];model=next(i for i in supplies['items'] if i['id']==key)
        source=next(i for i in sources['items'] if i['id']==key)
        assert sha(ROOT/model['geometry']['path'])==model['geometry']['sha256']
        instances=[a for a in scene['assets'] if a.get('source_record')==key]
        views=[];obligations=[]
        for a in instances:
            assert sha(ROOT/a['geometry'])==a['geometry_sha256']
            for direction in ['closed','front','back','side','top']:
                c=captures[a['id']+'_'+direction]
                assert sha(ROOT/c['path'])==c['sha256']
                views.append(dict(asset_id=a['id'],view=direction,**c))
        for s in readiness['manual_step_requirements']:
            if set(s['resource_requirements']) & set(model['resources']):
                obligations.append(dict(step_id=s['step_id'],interface_id=s['interface_id'],
                    scope='Resource association only; exact tool applicability and part/contact mapping remain open',
                    manipulation_binding=None,qualified=False))
        items.append(dict(**note,geometry=model['geometry'],catalogue_facts=source['facts'],
            local_inferences=source['inferred'],limitations=source['limits'],
            instances=[dict(asset_id=a['id'],path=a['geometry'],sha256=a['geometry_sha256'],station=a['station']) for a in instances],
            model_views=views,resource_associated_review_obligations=obligations,
            owner_acceptance=False,interaction_qualified=False))
    write_json(HERE/'preparation_review.json',dict(schema_version=1,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in paths],
        reviewed=notes['reviewed'],reviewer=notes['reviewer'],scope=notes['scope'],
        reuse=notes['reuse'],search_log=notes['search_log'],decisions=notes['decisions'],items=items))
    print(json.dumps(dict(reviewed_types=len(items),instances=sum(len(i['instances']) for i in items),
        pinned_model_views=sum(len(i['model_views']) for i in items),owner_acceptance=False)))


if __name__=='__main__':build()
