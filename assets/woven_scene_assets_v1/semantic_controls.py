"""Original caller-owned symbolic record guard. Never hardware control or evidence.

Reconstructed from retained author commands after local workspace loss. Local
claims bind instance, revision, exact sample/configuration/holder context, action
and payload. They are not credentials, signatures or evidence. Methods store
labels only; no geometry moves and no service is actuated. Python callers own
this object; this is not a security boundary against edits to private attributes
or executable code. No field proves physical truth. Fabrication, chemistry,
drying, plasma, coating, loading and SEM remain permanently disabled. No force,
stress, strain, energy, images or solver results are produced. Tetrakaidecahedron
geometry is held and not selectable. No source code is used.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
import copy, hashlib, json, uuid
class GuardError(ValueError):pass
class PhysicalExecutionUnavailable(GuardError):pass
BINDING_FIELDS=frozenset({'sample_id','sample_version','carrier_id','holder_id','configuration_id','configuration_version','topology'})
ACTION_FIELDS=MappingProxyType({
 'register_custody':frozenset({'custody_record_id'}),
 'dock':frozenset({'docking_record_id'}),
 'bind_services':frozenset({'fabrication_receipt_id','development_receipt_id','cpd_receipt_id','coating_receipt_id','plasma_route','plasma_receipt_id','service_status'}),
 'mount_fixture':frozenset({'fixture_id','alignment_record_id','qualification_record_id','fixture_status'}),
 'bind_records':frozenset({'run_id','record_set_id','force_displacement_record_id','sem_image_record_id','timebase_record_id','calibration_record_id','record_status'}),
 'disconnect':frozenset({'disconnect_record_id','disconnect_status'}),
 'retrieve':frozenset({'return_record_id','unload_record_id','return_status'}),
})
TARGET_FIELDS=MappingProxyType({'register_custody':'carrier_id','dock':'holder_id','bind_services':'holder_id','mount_fixture':'fixture_id','bind_records':'record_set_id','disconnect':'holder_id','retrieve':'carrier_id'})
SYMBOLS=MappingProxyType({'bind_services':('service_status','external_receipt_ids_only'),'mount_fixture':('fixture_status','disabled_symbolic_claim'),'bind_records':('record_status','external_record_ids_only'),'disconnect':('disconnect_status','disconnected_symbolic_claim'),'retrieve':('return_status','unloaded_symbolic_claim')})
STATES=MappingProxyType({'register_custody':({'CUSTODY'},'CUSTODY'),'dock':({'CUSTODY'},'DOCKED'),'bind_services':({'DOCKED'},'SERVICES_BOUND'),'mount_fixture':({'SERVICES_BOUND'},'FIXTURE_DISABLED'),'bind_records':({'FIXTURE_DISABLED'},'RECORDS_BOUND'),'disconnect':({'DOCKED','SERVICES_BOUND','FIXTURE_DISABLED','RECORDS_BOUND'},'DISCONNECTED'),'retrieve':({'DISCONNECTED'},'CUSTODY')})
def _str(v,k):
 if type(v) is not str or not v.strip():raise GuardError(k+' requires a nonempty plain string')
def _int(v,k,minimum=1):
 if type(v) is not int or v<minimum:raise GuardError(k+' requires a plain integer')
def _digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
@dataclass(frozen=True)
class Claim:
 instance:str;revision:int;sample_id:str;sample_version:int;context_hash:str;action:str;target_id:str;payload_hash:str;claim_id:str
class WovenFixture:
 def __init__(self,sample_id:str,sample_version:int=1):
  _str(sample_id,'sample_id');_int(sample_version,'sample_version')
  self._instance=uuid.uuid4().hex;self._sample_id=sample_id;self._sample_version=sample_version;self._revision=0;self._state='CUSTODY';self._records={};self._issued={};self._used_runs=set();self._used_record_ids=set()
 def snapshot(self):
  return copy.deepcopy({'instance':self._instance,'revision':self._revision,'sample_id':self._sample_id,'sample_version':self._sample_version,'state':self._state,'records':self._records,'scope':'caller_owned_untrusted_local_metadata_only','claims_are_evidence':False,'physical_execution':False,'geometry_coupling':False,'energy_enabled':False,'fabrication_enabled':False,'chemistry_enabled':False,'cpd_enabled':False,'plasma_enabled':False,'coating_enabled':False,'loading_enabled':False,'sem_enabled':False,'scientific_outputs':None,'tetrakaidecahedron_status':'CONFLICT_HOLD'})
 def _validate(self,action,record):
  if type(record) is not dict or set(record)!=BINDING_FIELDS|ACTION_FIELDS[action]:raise GuardError('exact record fields required')
  for k,v in record.items():
   if k in ('sample_version','configuration_version'):_int(v,k)
   else:_str(v,k)
  if (record['sample_id'],record['sample_version'])!=(self._sample_id,self._sample_version):raise GuardError('sample identity/version mismatch')
  if record['topology'] not in ('BCC','CUBIC'):raise GuardError('only unconflicted BCC/CUBIC metadata; other topology held')
  if action!='register_custody':
   custody=self._records.get('register_custody')
   if custody is None or any(record[k]!=custody[k] for k in BINDING_FIELDS):raise GuardError('custody/configuration/holder/topology mismatch')
  if action in SYMBOLS:
   k,v=SYMBOLS[action]
   if record[k]!=v:raise GuardError('explicit symbolic-only disposition required')
  if action=='bind_services':
   if record['plasma_route'] not in ('not_required','required_external'):raise GuardError('explicit plasma branch required')
   if (record['plasma_route']=='not_required') != (record['plasma_receipt_id']=='NOT_APPLICABLE'):raise GuardError('plasma branch receipt mismatch')
   ids=[record[k] for k in ('fabrication_receipt_id','development_receipt_id','cpd_receipt_id','coating_receipt_id','plasma_receipt_id')]
   if len(ids)!=len(set(ids)):raise GuardError('distinct service receipt IDs required')
  if action=='bind_records':
   ids=[record[k] for k in ('record_set_id','force_displacement_record_id','sem_image_record_id','timebase_record_id','calibration_record_id')]
   if len(set(ids))!=5 or set(ids)&self._used_record_ids or record['run_id'] in self._used_runs:raise GuardError('distinct fresh paired external run/record IDs required')
 def claim(self,action,target_id,record):
  if self._state=='QUARANTINE':raise GuardError('terminal quarantine')
  _str(action,'action');_str(target_id,'target_id')
  if action not in ACTION_FIELDS:raise GuardError('unknown metadata action')
  self._validate(action,record)
  if target_id!=record[TARGET_FIELDS[action]]:raise GuardError('target mismatch')
  c=Claim(self._instance,self._revision,self._sample_id,self._sample_version,_digest(self.snapshot()),action,target_id,_digest(record),uuid.uuid4().hex);self._issued[c.claim_id]=c;return c
 def apply(self,action,record,claim):
  _str(action,'action')
  if action not in ACTION_FIELDS:raise GuardError('unknown metadata action')
  allowed,state=STATES[action]
  if self._state not in allowed:raise GuardError('state precondition failed')
  self._validate(action,record)
  if type(claim) is not Claim:raise GuardError('typed issued claim required')
  _int(claim.revision,'claim revision',0);_int(claim.sample_version,'claim sample_version')
  for k in ('instance','sample_id','context_hash','action','target_id','payload_hash','claim_id'):_str(getattr(claim,k),k)
  expected=(self._instance,self._revision,self._sample_id,self._sample_version,_digest(self.snapshot()),action,record[TARGET_FIELDS[action]],_digest(record))
  actual=(claim.instance,claim.revision,claim.sample_id,claim.sample_version,claim.context_hash,claim.action,claim.target_id,claim.payload_hash)
  if actual!=expected or self._issued.get(claim.claim_id)!=claim:raise GuardError('unissued, stale, replayed, cross-instance or mismatched claim')
  detached=copy.deepcopy(record)
  if action=='register_custody':self._records={}
  if action=='retrieve':self._records={'register_custody':self._records['register_custody']}
  if action=='dock':self._records.pop('retrieve',None)
  self._records[action]=detached
  if action=='bind_records':
   self._used_runs.add(record['run_id']);self._used_record_ids.update(record[k] for k in ('record_set_id','force_displacement_record_id','sem_image_record_id','timebase_record_id','calibration_record_id'))
  self._issued.clear();self._state=state;self._revision+=1;return self.snapshot()
 def record_manifest(self):
  if self._state!='RECORDS_BOUND':raise GuardError('current paired records required')
  return copy.deepcopy({'sample_id':self._sample_id,'sample_version':self._sample_version,'records':self._records,'scope':'unverified_external_identifiers_only','claims_are_evidence':False,'scientific_outputs':None,'physical_execution':False,'energy_enabled':False})
 def quarantine(self):
  if self._state!='QUARANTINE':self._state='QUARANTINE';self._revision+=1;self._issued.clear()
  return self.snapshot()
 def request_physical_service(self,*args,**kwargs):raise PhysicalExecutionUnavailable('No fabrication, chemistry, pressure, plasma, coating, loading, SEM, solver, geometry or hardware adapter exists')
