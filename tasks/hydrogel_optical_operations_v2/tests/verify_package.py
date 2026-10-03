"""Read-only static package checks; no report regeneration."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent))
from contract import load,BRANCHES,closure
P=Path(__file__).resolve().parents[1]
errors=[]
for p in P.rglob('*.json'):
 try:json.loads(p.read_text())
 except Exception as exc:errors.append(str(p.relative_to(P))+': '+str(exc))
ops=load('operations.json')['operations'];evidence={x['id'] for x in load('provenance.json')['evidence']};uids={x['id'] for x in load('unknown_parameters.json')['unknowns']};opids={x['id'] for x in ops}
if len(opids)!=len(ops):errors.append('duplicate operation IDs')
for b in BRANCHES.values():
 if not set(b['operation_ids'])<=opids:errors.append('unknown operation')
 if not set(b['source_evidence_ids'])<=evidence:errors.append('unknown evidence')
 if not set(b['unknown_parameter_ids'])<=uids:errors.append('unknown parameter')
 if b['execution_ready'] is not False:errors.append('execution claim')
 for d in b['required_branch_ids']:
  if b['id'] in closure([d]):errors.append('dependency cycle')
for row in load('coverage_matrix.json')['coverage']:
 if not set(row['branch_ids'])<=set(BRANCHES):errors.append('coverage unknown branch')
access=load('source_access_audit.json')
if access['extended_data_images_inspected']!=0 or access['source_complete_for_entire_paper']:errors.append('source gap erased')
for p in P.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 if p.suffix in ['.md','.json','.py']:
  s=p.read_text()
  if any('\u4e00'<=c<='\u9fff' for c in s):errors.append('non-English prose '+p.name)
  if ('/'+'tmp'+'/') in s or ('/'+'workspace'+'/') in s:errors.append('private local path '+p.name)
print(json.dumps({'check':'static_package','passed':not errors,'errors':errors,'branches':len(BRANCHES),'operations':len(ops),'coverage':len(load('coverage_matrix.json')['coverage']),'no_execution_or_simulation':True},indent=2))
raise SystemExit(bool(errors))
