"""Check source bindings and prove that deliberate layout faults are rejected."""
import copy
import json
import tempfile
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_layout import inspect


def validate():
    scene=json.loads((HERE/'scene.json').read_text())
    inventory=json.loads((HERE/'inventory.json').read_text())
    contract=json.loads((HERE/'acceptance_contract.json').read_text())
    checks=[]
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        if not value:raise AssertionError(name)
    check('source_inventory_pinned',sha(ROOT/inventory['source_inventory']['path'])==inventory['source_inventory']['sha256'])
    source=json.loads((ROOT/inventory['source_inventory']['path']).read_text())
    for row in inventory['items']:
        if row.get('source_pointer'):
            value=source
            for part in row['source_pointer'].strip('/').split('/'):
                value=value[int(part)] if isinstance(value,list) else value[part]
            check('source_row_'+row['id'],value==row['source_value'])
        for candidate in row['candidate_artifacts']:
            check('candidate_'+row['id']+'_'+candidate['path'],sha(ROOT/candidate['path'])==candidate['sha256'])
    check('inventory_count',len(inventory['items'])==inventory['required_records']==60)
    check('room_details_pinned',scene['room_details_sha256']==sha(HERE/'room_details.py'))
    check('room_builder_pinned',scene['room_builder_sha256']==sha(HERE/'room_architecture.py'))
    check('current_scene_pinned',contract['current_scene']['sha256']==sha(HERE/'scene.json'))
    check('no_inferred_owner_acceptance',contract['owner_acceptance']['decision']=='pending' and all(g['status']=='open' for g in contract['gates']))
    check('no_new_manipulation_authority',not contract['new_manipulation_development_allowed'] and not scene['manipulation_development_allowed'])
    for gate in contract['gates']:
        for evidence in gate['evidence']:check('gate_evidence_'+gate['id']+'_'+evidence['path'],sha(ROOT/evidence['path'])==evidence['sha256'])
    for identity,expected in [('eko_ms402',[.16,.16,.108]),('hobo_u30',[.1805,.118,.189])]:
        actual=trimesh.load(HERE/'geometry'/f'{identity}.glb',force='scene').extents
        check('drawing_dimensions_'+identity,np.allclose(actual,expected,atol=.0001))
    body=json.loads((HERE/'body_envelope.json').read_text())
    check('body_evidence_hash',scene['envelope']['body_evidence']['sha256']==sha(HERE/'body_envelope.json'))
    check('body_provisional_radius_covers_sampled_record',body['maximum_sampled']['radial_extent_m']<=scene['envelope']['transit_radius_m'])
    for p in body['source_artifacts']:check('body_source_'+p['path'],sha(ROOT/p['path'])==p['sha256'])
    original=inspect(quiet=True);check('base_layout',original['passed'])
    faults=[]
    # Separate independent faults exercise spatial predicates, not just schema.
    for name,expected in [('low_header','headroom_main'),('blocked_route','corridor_main'),('small_support','support_cary'),('overlapping_fixture','assets_and_authored_fixtures_separated'),('opening_obstruction','external_opening_cary_lid')]:
        bad=copy.deepcopy(scene)
        if name=='low_header':bad['obstacles'].append(dict(id='injected_low_header',role='test',bounds_m=[[5,4,2.0],[7,4.1,2.15]]))
        elif name=='blocked_route':bad['obstacles'].append(dict(id='injected_crate',role='test',bounds_m=[[5.8,5,.0],[6.2,5.4,1.9]]))
        elif name=='small_support':next(s for s in bad['support_surfaces'] if s['id']=='cary_bench')['xy_bounds_m']=[2.2,8.6,2.3,8.7]
        elif name=='overlapping_fixture':
            next(a for a in bad['assets'] if a['id']=='heater')['position_m']=[9.7,2.7,.9]
        else:
            sweep=next(s for s in original['opening_states'] if s['id']=='cary_lid')['sweep_bounds_m'];center=(np.array(sweep[0])+sweep[1])/2
            bad['obstacles'].append(dict(id='injected_cover_obstacle',role='test',bounds_m=[(center-.01).tolist(),(center+.01).tolist()]))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'scene.json';write_json(p,bad);record=inspect(p,Path(tmp)/'result.json',quiet=True)
        failed=[c['name'] for c in record['checks'] if not c['passed']]
        check('reject_'+name,not record['passed'] and expected in failed)
        faults.append(dict(fault=name,expected_failure=expected,observed_failures=failed))
    record=dict(passed=True,checks=checks,negative_cases=faults,scene_sha256=sha(HERE/'scene.json'),
        validator_sha256=sha(__file__),layout_checker_sha256=sha(HERE/'check_layout.py'),
        scope='Source identity and meaningful negative layout cases; no asset, full-body or safe-use acceptance')
    write_json(HERE/'review_verification.json',record)
    print(json.dumps(dict(passed=True,checks=len(checks),negative_cases=len(faults)),indent=2))


if __name__=='__main__':validate()
