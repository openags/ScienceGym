"""Caller-owned static metadata guard. No physical or scientific execution authority.
Claims are local symbolic test inputs, not calibration, authentication or sensor evidence.
No method moves Blender objects, performs deformation, produces images or computes efficiency.
"""
from dataclasses import dataclass, asdict
import copy, hashlib, json, uuid

class GuardError(ValueError): pass
class PhysicalExecutionUnavailable(GuardError): pass

@dataclass(frozen=True)
class Claim:
    instance: str
    revision: int
    specimen_id: str
    specimen_version: int
    context_hash: str
    kind: str
    claim_id: str

class MetrologyFixture:
    def __init__(self, specimen_id, specimen_version=1):
        if not isinstance(specimen_id,str) or not specimen_id.strip(): raise GuardError('specimen identity required')
        if type(specimen_version) is not int or specimen_version<1: raise GuardError('positive integer version required')
        self._instance=uuid.uuid4().hex; self._revision=0; self._specimen_id=specimen_id; self._specimen_version=specimen_version
        self._state='CUSTODY'; self._cards=None; self._before=None; self._after=None; self._consumed=set(); self._used_runs=set()
    def snapshot(self):
        return copy.deepcopy({'instance':self._instance,'revision':self._revision,'specimen_id':self._specimen_id,'specimen_version':self._specimen_version,'state':self._state,'cards':self._cards,'source_conflicts_resolved':False,'physical_execution':False,'scientific_outputs':None,'before':self._before,'after':self._after})
    def _context(self):
        return hashlib.sha256(json.dumps({'identity':[self._specimen_id,self._specimen_version],'state':self._state,'cards':self._cards,'before':self._before,'after':self._after},sort_keys=True).encode()).hexdigest()
    def claim(self, kind):
        if not isinstance(kind,str) or kind not in {'cards_reviewed','base_fixed','calibration_registered','before_image_registered','input_verified','after_image_registered','unloaded_verified','inspection_registered'}:raise GuardError('unknown claim kind')
        return Claim(self._instance,self._revision,self._specimen_id,self._specimen_version,self._context(),kind,uuid.uuid4().hex)
    def _consume(self, claim,kind):
        if not isinstance(claim,Claim):raise GuardError('typed local claim required')
        expected=(self._instance,self._revision,self._specimen_id,self._specimen_version,self._context(),kind)
        actual=(claim.instance,claim.revision,claim.specimen_id,claim.specimen_version,claim.context_hash,claim.kind)
        if actual!=expected or not isinstance(claim.claim_id,str) or not claim.claim_id or claim.claim_id in self._consumed:raise GuardError('stale, reused, wrong-instance, wrong-identity or wrong-context claim')
        self._consumed.add(claim.claim_id)
    def _transition(self, allowed,to,claim=None,kind=None):
        if self._state not in allowed:raise GuardError('state precondition failed')
        if kind:self._consume(claim,kind)
        self._state=to;self._revision+=1
        return self.snapshot()
    def register_cards(self, cards, claim):
        if self._state!='CUSTODY':raise GuardError('cards only in custody')
        required={'specimen_id','specimen_version','design_id','carrier_id','fixture_id','camera_id','direction_card_id','direction_disposition','axis_map_id','calibration_id','calibration_revision'}
        if type(cards) is not dict or set(cards)!=required or any(v is None or v=='' for v in cards.values()):raise GuardError('exact complete identity-bound cards required')
        if any(not isinstance(cards[k],str) or not cards[k].strip() for k in required-{'specimen_version','calibration_revision'}):raise GuardError('nonempty string card IDs and disposition required')
        if type(cards['specimen_version']) is not int:raise GuardError('integer specimen version required')
        if cards['specimen_id']!=self._specimen_id or cards['specimen_version']!=self._specimen_version:raise GuardError('card identity mismatch')
        if cards['direction_disposition'] not in {'reviewed_orthogonal_branch','reviewed_antiparallel_branch'}:raise GuardError('explicit reviewed branch disposition required; no acknowledgement-only resolution')
        if type(cards['calibration_revision']) is not int or cards['calibration_revision']<1:raise GuardError('positive calibration revision required')
        self._consume(claim,'cards_reviewed');self._cards=copy.deepcopy(cards);self._before=None;self._after=None;self._revision+=1
        return self.snapshot()
    def dock(self):
        if not self._cards:raise GuardError('direction HOLD and qualification cards missing')
        return self._transition({'CUSTODY'},'DOCKED')
    def fix_base(self,claim):return self._transition({'DOCKED'},'FIXED',claim,'base_fixed')
    def register_calibration(self,claim):return self._transition({'FIXED'},'REGISTERED',claim,'calibration_registered')
    def register_before(self, image_id, run_id, claim):
        if self._state!='REGISTERED' or not isinstance(image_id,str) or not image_id.strip() or not isinstance(run_id,str) or not run_id.strip() or run_id in self._used_runs:raise GuardError('fresh run and before image IDs required')
        self._consume(claim,'before_image_registered');self._before={'image_id':image_id,'run_id':run_id,'calibration_id':self._cards['calibration_id'],'calibration_revision':self._cards['calibration_revision']};self._used_runs.add(run_id);self._state='BEFORE';self._revision+=1;return self.snapshot()
    def register_input(self,claim):return self._transition({'BEFORE'},'INPUT_CLAIMED',claim,'input_verified')
    def register_after(self,image_id,run_id,claim):
        if self._state!='INPUT_CLAIMED' or not isinstance(image_id,str) or not image_id.strip() or not isinstance(run_id,str) or image_id==self._before['image_id'] or run_id!=self._before['run_id']:raise GuardError('distinct after image bound to same run required')
        self._consume(claim,'after_image_registered');self._after={'image_id':image_id,'run_id':run_id,'calibration_id':self._cards['calibration_id'],'calibration_revision':self._cards['calibration_revision']};self._state='PAIR_REGISTERED';self._revision+=1;return self.snapshot()
    def pair_manifest(self):
        if self._state!='PAIR_REGISTERED':raise GuardError('registered identity-bound pair required')
        return copy.deepcopy({'specimen_id':self._specimen_id,'specimen_version':self._specimen_version,'cards':self._cards,'before':self._before,'after':self._after,'scope':'untrusted local metadata only','displacements':None,'efficiency':None,'physical_execution':False})
    def release_intent(self):return self._transition({'INPUT_CLAIMED','PAIR_REGISTERED'},'RELEASE_INTENT')
    def verify_unloaded(self,claim):return self._transition({'RELEASE_INTENT'},'UNLOADED_CLAIMED',claim,'unloaded_verified')
    def unfix(self):return self._transition({'UNLOADED_CLAIMED'},'UNFIXED')
    def retrieve(self):return self._transition({'UNFIXED'},'CUSTODY')
    def inspect(self,claim):
        if self._state!='CUSTODY':raise GuardError('inspect in custody only')
        self._consume(claim,'inspection_registered');self._revision+=1;return self.snapshot()
    def quarantine(self):self._state='QUARANTINE';self._revision+=1;return self.snapshot()
    def request_physical_service(self,operation_id,*args,**kwargs):
        raise PhysicalExecutionUnavailable('No physical, camera, fabrication, solver, motor, deformation or scientific-measurement adapter: '+str(operation_id))
