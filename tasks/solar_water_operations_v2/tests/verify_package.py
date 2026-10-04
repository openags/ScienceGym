from contract import *
ops=load('operations.json')['operations'];assert len(ops)==34 and len({x['id'] for x in ops})==34
assert len(BRANCHES)==15
known={x['id'] for x in load('unknown_parameters.json')['parameters']}
for b in BRANCHES.values():
 assert set(b['unknown_parameter_ids'])<=known
 assert set(b['conflict_ids'])<=set(CONFLICTS)
 assert set(b['depends_on'])<=set(BRANCHES)
 assert b['physical_execution_implemented'] is False
for b in BRANCHES:
 assert all(x['operation_id'] in {o['id'] for o in ops} for x in plan_for(b))
for n in ['STATUS.json','coverage_matrix.json','RELEASE_BOUNDARY.json']:assert load(n)['full_paper_complete'] is False
c,e=fixture();print(json.dumps(validate(c,e),indent=2))
print('Static package references and full bounded synthetic fixture passed')
