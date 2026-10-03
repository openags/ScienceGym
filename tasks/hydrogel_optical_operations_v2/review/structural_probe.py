"""Independent deletion and invalid-value tests of required synthetic record fields."""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hydrogel_contract_structural',ROOT/'tests/contract.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
rows=[]
def probe(name,fn,selected=None):
 x,y=c.fixture(selected)
 try:fn(x,y);errors=c.validate(x,y);actual='reject' if errors else 'accept'
 except Exception as e:actual='exception';errors=[type(e).__name__+': '+str(e)]
 rows.append({'name':name,'expected':'reject','actual':actual,'passed':actual=='reject','diagnostic':errors[:3]})
base,ev=c.fixture()
for field in next(iter(base['jobs'].values())):
 probe('delete_job_'+field,lambda x,y,k=field:next(iter(x['jobs'].values())).pop(k))
 probe('null_job_'+field,lambda x,y,k=field:next(iter(x['jobs'].values())).__setitem__(k,None)) if field not in ['optical_release_specimen_id','optical_release_version','optical_release_record_id'] else None
for field in ev[0]:
 probe('delete_event_'+field,lambda x,y,k=field:y[0].pop(k))
 if field!='public_note':probe('null_event_'+field,lambda x,y,k=field:y[0].__setitem__(k,None))
for field in c.load('lineage_contract.json')['required_keys']+['allocation_key']:
 probe('delete_lineage_'+field,lambda x,y,k=field:next(iter(x['lineage'].values())).pop(k))
 probe('null_lineage_'+field,lambda x,y,k=field:next(iter(x['lineage'].values())).__setitem__(k,None))
for field,value in [('version',0),('substrate_id',''),('cover_id',''),('chamber_id',''),('development_card_revision','obsolete'),('geometry_hash',True),('dose_map_hash',True),('orientation_map_hash',True),('thermal_history','omitted')]:
 probe('invalid_lineage_'+field,lambda x,y,k=field,v=value:next(iter(x['lineage'].values())).__setitem__(k,v))
probe('invented_job_in_lineage',lambda x,y:next(iter(x['lineage'].values()))['service_job_ids'].append('nonexistent_job'))
probe('missing_allocation_provenance',lambda x,y:next(iter(x['condition_allocations'].values())).pop('condition_origin'))
probe('source_allocation_provenance',lambda x,y:next(iter(x['condition_allocations'].values())).__setitem__('condition_origin','source_reported'))
probe('three_d_unreserved_allocation',lambda x,y:next(l for l in x['lineage'].values() if l['allocation_key'].startswith('THREE_D|')).__setitem__('allocation_role','unreserved'),['THREE_D'])
probe('three_d_wrong_resist',lambda x,y:next(l for l in x['lineage'].values() if l['allocation_key'].startswith('THREE_D|')).__setitem__('resist_material','DEGRAD_INX_N100'),['THREE_D'])
receipt={'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Required-field synthetic-record structural mutation tests only','contract_sha256':hashlib.sha256((ROOT/'tests/contract.py').read_bytes()).hexdigest(),'cases':rows,'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows)}
(ROOT/'review/structural_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'cases':len(rows),'passed':receipt['passed'],'failed':receipt['failed']}))
for r in rows:
 if not r['passed']:print(r['name'],r['actual'],r['diagnostic'])
sys.exit(bool(receipt['failed']))
