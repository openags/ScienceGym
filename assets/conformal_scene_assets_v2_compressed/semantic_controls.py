"""Pure in-memory static examples. Test receipts have no physical authenticity.
No device calls, motion, timing, camera acquisition or scientific solver exist.
"""
from dataclasses import dataclass, field
from copy import deepcopy

class GuardRejected(ValueError): pass

def require(condition, message):
    if not condition: raise GuardRejected(message)

@dataclass
class StaticSceneGuard:
    physical_execution_enabled: bool = field(default=False, init=False)
    epoch: int = 0
    specimen: str | None = None
    carrier: str | None = None
    branch: str | None = None
    treatment_revision: str | None = None
    preparation: dict = field(default_factory=dict)
    receipts: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    armed: bool = False
    unloaded: bool = True
    quarantined: bool = False
    faulted: bool = False
    docked: bool = False
    run_ids: set = field(default_factory=set)
    run_id: str | None = None

    def prepare(self, *, specimen, geometry_revision, build_receipt, fixture_receipt,
                treatment_revision, contact_service_receipt=None):
        require(not self.armed and not self.docked, 'Preparation requires idle supported state')
        require(all(isinstance(x,str) and x for x in [specimen,geometry_revision,build_receipt,fixture_receipt,treatment_revision]), 'Missing versioned preparation lineage')
        require(treatment_revision=='none' or (isinstance(contact_service_receipt,str) and bool(contact_service_receipt)), 'Treatment needs an identified qualified-service receipt; never dispense unknown powder')
        self.specimen=specimen;self.treatment_revision=treatment_revision
        self.preparation={'specimen':specimen,'geometry':geometry_revision,'build':build_receipt,'fixture':fixture_receipt,'treatment':treatment_revision,'contact_service':contact_service_receipt}
        self.events.append(('test_preparation',deepcopy(self.preparation)))

    def dock(self, *, specimen, carrier, branch, grasp_zone, supported):
        require(not self.docked and not self.armed and not self.faulted and not self.quarantined,'Dock is leased or specimen is held')
        require(specimen==self.specimen and self.preparation.get('specimen')==specimen,'Fresh matching preparation required')
        require(branch in {'B02','B03'},'Only documented physical branch roles may dock')
        require(bool(carrier) and supported is True,'Supported serialized carrier required')
        require(grasp_zone in {'carrier.handle_left','carrier.handle_right'},'No hinge, pad or free-specimen grasp')
        self.carrier=carrier;self.branch=branch;self.epoch+=1;self.receipts.clear();self.docked=True
        self.events.append(('test_dock',specimen,carrier,branch,self.epoch))

    def record_test_receipt(self, *, kind, specimen, carrier, branch, epoch, test_only, fields):
        require(test_only is True,'This accepts illustrative test receipts only')
        require(self.docked and not self.faulted and not self.quarantined and not self.armed,'Cannot qualify current state')
        require((specimen,carrier,branch,epoch)==(self.specimen,self.carrier,self.branch,self.epoch),'Stale or wrong receipt identity/epoch')
        required={
          'mechanics':{'commissioned_limits','calibrated_loadcell','contact_zero','fixture_locked','safe_stop_policy'},
          'camera':{'scale_distortion','focus_visibility','reference_frame','pad_identity_mask'},
          'sync':{'clock_mapping','capture_ready','buffer_ready','load_unload_tags'},
          'plan':{'frozen_repeat_policy','order_policy','recovery_policy','stopping_policy'},
        }
        require(kind in required,'Unknown receipt kind')
        require(isinstance(fields,dict) and all(fields.get(k) is True for k in required[kind]),'Incomplete qualification flags')
        self.receipts[kind]={'epoch':epoch,'specimen':specimen,'branch':branch,'carrier':carrier,'fields':deepcopy(fields)}
        self.events.append(('test_receipt',kind,epoch))

    def arm_static(self, *, run_id, visual_guard_closed):
        require(self.docked and not self.armed and not self.faulted and not self.quarantined,'Static arm state invalid')
        require(visual_guard_closed is True,'Illustrative guard state must be closed')
        require(bool(run_id) and run_id not in self.run_ids,'Unique run ID required')
        require(set(self.receipts)=={'mechanics','camera','sync','plan'},'All four current qualification receipts required')
        require(all(x['epoch']==self.epoch and x['specimen']==self.specimen and x['branch']==self.branch and x['carrier']==self.carrier for x in self.receipts.values()),'Qualification state became stale')
        self.run_id=run_id;self.run_ids.add(run_id);self.armed=True;self.unloaded=False
        self.events.append(('test_static_armed',run_id,self.epoch))
        return {'static_only':True,'physical_permission':False}

    def finish_static(self, *, unloaded, disarmed, recovery_ok):
        require(self.armed,'Nothing statically armed')
        require(unloaded is True and disarmed is True,'Safe-state receipt required')
        self.armed=False;self.unloaded=True
        if recovery_ok is not True:self.quarantined=True
        self.receipts.clear() # Neither success nor unload reuses calibration/reset receipts.
        self.events.append(('test_finish',self.run_id,recovery_ok))

    def change_fixture(self, *, next_branch, specimen, treatment_revision):
        require(self.docked and not self.armed and self.unloaded and not self.faulted and not self.quarantined,'Isolate and recover before changing fixtures')
        require(next_branch in {'B02','B03'} and next_branch!=self.branch,'Distinct documented branch required')
        changed=(specimen!=self.specimen or treatment_revision!=self.treatment_revision)
        self.epoch+=1;self.receipts.clear();self.branch=next_branch;self.docked=False;self.carrier=None
        if changed:self.preparation.clear();self.specimen=specimen;self.treatment_revision=treatment_revision
        self.events.append(('test_fixture_change',next_branch,changed,self.epoch))
        return {'preparation_reentry_required':changed,'docking_reentry_required':True,'physical_permission':False}

    def fault(self, reason):
        require(isinstance(reason,str) and bool(reason),'Fault reason required')
        self.faulted=True;self.quarantined=True;self.armed=False;self.receipts.clear();self.epoch+=1
        # Do not falsely assert that stopping software makes physical machinery safe.
        self.unloaded=False;self.events.append(('test_fault',reason,self.epoch))

    def closeout(self, *, safe_state_receipt, disposition):
        require(safe_state_receipt is True,'Qualified safe-state service receipt required; never assume unload')
        require(disposition in {'storage','quarantine'},'Explicit disposition required')
        require(not (self.quarantined or self.faulted) or disposition=='quarantine','Failed specimens cannot be returned to storage')
        self.armed=False;self.unloaded=True;self.docked=False
        self.events.append(('test_closeout',disposition))
        return {'evidence_events':deepcopy(self.events),'physical_permission':False,'scientific_validation':False}

    def execute_physical(self, *args, **kwargs):
        raise GuardRejected('No hardware or physical execution interface exists')


def analysis_guard(*, mode, physical_or_numerical, interior_targets_used, det_f_positive,
                   global_injectivity_verified, normalization_nonzero, closed_boundary,
                   conventions_reviewed, source_conflicts_resolved):
    require(mode in {'fit','boundary_inference'},'Separate analysis mode required')
    require(physical_or_numerical in {'physical','numerical'},'Separate evidence domain required')
    require(det_f_positive is True,'Positive det(F) required; det(C) cannot establish orientation')
    require(normalization_nonzero is True,'Zero displacement cannot normalize residual')
    require(conventions_reviewed is True and source_conflicts_resolved is True,'Source formula and reference conventions require review')
    if mode=='boundary_inference':
        require(interior_targets_used is False,'Boundary inference may not fit interior targets')
        require(closed_boundary is True,'Closed, qualified boundary required')
    return {'static_check_only':True,'global_geometry_status':'qualified_external_receipt' if global_injectivity_verified is True else 'unverified','scientific_success':False}
