"""Offline synthetic bookkeeping only. No device, geometry, physics or metric API.

The checks establish finite structural invariants, never physical safety or truth.
All fixture receipts carry explicit synthetic labels. External observations are
not accepted by this demonstration engine and must not be synthesized here.
"""
from copy import deepcopy
import hashlib
import json
import re

FAMILIES = ('CLOAK', 'ROTATOR45', 'CONCENTRATOR18')
CONDITIONS = frozenset('COND_%s_%s' % (f, o) for f in FAMILIES for o in ('X', 'Y'))
PREP_STAGES = ('design', 'materials', 'lattice', 'intermediate', 'specimen')
NUMERICAL_BRANCHES = frozenset('B%02d' % i for i in range(5, 11))

class Held(ValueError):
    """Reject a synthetic transition while preserving custody; may route to a hold/release state."""

def require(ok, reason):
    if not ok:
        raise Held(reason)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def fixture_receipt(receipt_id, **fields):
    """Create a labeled test token, never a service certificate or observation."""
    payload = dict(receipt_id=receipt_id, evidence_class='synthetic_bookkeeping_fixture',
                   issuer_role='fictional_qualified_service', valid=True, **fields)
    payload['content_hash'] = digest(payload)
    return payload

def check_receipt(receipt):
    require(isinstance(receipt, dict), 'receipt must be a mapping')
    require(receipt.get('evidence_class') == 'synthetic_bookkeeping_fixture', 'only synthetic fixtures accepted')
    require(receipt.get('issuer_role') == 'fictional_qualified_service', 'wrong fixture issuer')
    require(receipt.get('valid') is True, 'invalid fixture receipt')
    require(isinstance(receipt.get('receipt_id'), str) and receipt['receipt_id'].strip(), 'receipt ID missing')
    h = receipt.get('content_hash')
    require(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h), 'content hash missing')
    payload = {k: v for k, v in receipt.items() if k != 'content_hash'}
    require(h == digest(payload), 'fixture receipt hash mismatch')


def verify_preparation(chain):
    require(isinstance(chain, list) and len(chain) == 5, 'five preparation receipts required')
    for record in chain:
        check_receipt(record)
    require([x.get('record_type') for x in chain] == list(PREP_STAGES), 'preparation order/type mismatch')
    common = ('paper_id', 'sample_family_id', 'design_id', 'design_revision', 'specimen_id', 'service_job_id')
    base = chain[0]
    require(base.get('paper_id') == 'thermalmeta-2024-49630', 'wrong paper')
    require(base.get('sample_family_id') in FAMILIES, 'unknown family')
    for key in common:
        require(isinstance(base.get(key), str) and base[key], 'missing lineage identity')
        require(all(record.get(key) == base[key] for record in chain), 'cross-family, stale or wrong-object lineage')
    require(len({x['receipt_id'] for x in chain}) == 5, 'duplicate preparation receipt')
    require(len({x.get('object_id') for x in chain}) == 5 and all(x.get('object_id') for x in chain), 'object identity collision')
    for i, record in enumerate(chain):
        require(record.get('parent_id') == (None if i == 0 else chain[i-1]['object_id']), 'missing or wrong parent')
        require(isinstance(record.get('material_lot_ids'), list) and record['material_lot_ids'] and all(isinstance(v, str) and v for v in record['material_lot_ids']), 'missing material lot list')
    require(chain[-1].get('lattice_parent_id') == chain[2]['object_id'], 'wrong lattice parent')
    require(chain[-1].get('intermediate_parent_id') == chain[3]['object_id'], 'wrong intermediate parent')
    expected_core = 'PDMS' if base['sample_family_id'] == 'CLOAK' else 'background_encapsulant'
    require(chain[3].get('core_assignment') == expected_core and chain[4].get('core_assignment') == expected_core, 'wrong core material')
    require(chain[-1].get('safe_release') is True and chain[-1].get('dry_ambient') is True, 'incoming service release missing')
    require(base.get('geometry_qualification') is True, 'unqualified geometry token')
    return deepcopy(chain[-1])


class SymbolicEpisode:
    """Read/write in-memory test ledger. No filesystem or hardware side effects."""
    def __init__(self, plan):
        require(isinstance(plan, list) and plan, 'approved synthetic plan required')
        self.plan = deepcopy(plan)
        self.specimens = {}
        self.used_receipts = set()
        self.used_objects = set()
        self.runs = {}
        self.completed_slots = set()
        self.failures = []
        self.active = None
        self.state = 'READY'
        self.custody = 'handler'
        self.admin_closed = False
        self.closed = False
        self.controls = None
        self.analysis = None
        self.numerical_ledger = None
        self.mounted = None
        self.calibration = None
        require(len({x.get('slot_id') for x in plan}) == len(plan), 'duplicate plan slot')
        for slot in plan:
            require(slot.get('approved') is True, 'unapproved plan slot')
            require(slot.get('condition_id') in CONDITIONS, 'unknown condition')
            require(isinstance(slot.get('specimen_id'), str) and slot['specimen_id'], 'specimen slot missing')
            require(slot.get('repeat_kind') in ('base', 'technical', 'independent'), 'repeat identity missing')
            require(isinstance(slot.get('slot_id'), str) and slot['slot_id'], 'slot identity missing')
        by_id = {s['slot_id']: s for s in plan}
        bases = [(s['condition_id'], s['specimen_id']) for s in plan if s['repeat_kind'] != 'technical']
        require(len(set(bases)) == len(bases), 'same specimen/condition mislabeled as independent or base')
        for slot in plan:
            if slot['repeat_kind'] != 'base':
                parent = by_id.get(slot.get('replicate_of_slot_id'))
                require(parent is not None and parent['repeat_kind'] == 'base', 'repeat must reference base slot')
                require(parent['condition_id'] == slot['condition_id'], 'repeat condition differs')
                if slot['repeat_kind'] == 'technical':
                    require(parent['specimen_id'] == slot['specimen_id'], 'technical repeat cannot claim new specimen')
                else:
                    require(parent['specimen_id'] != slot['specimen_id'], 'independent repeat requires distinct specimen')

    def _open(self):
        require(not self.closed and not self.admin_closed, 'episode closed to new work')

    def _new_receipt(self, receipt):
        check_receipt(receipt)
        require(receipt['receipt_id'] not in self.used_receipts, 'reused receipt ID')

    def receive(self, chain):
        self._open()
        require(self.custody == 'handler' and self.active is None and self.mounted is None, 'service custody or mount blocks receiving')
        record = verify_preparation(chain)
        require(record['specimen_id'] not in self.specimens, 'specimen ID already exists; revision needs explicit new identity')
        require(not ({x['receipt_id'] for x in chain} & self.used_receipts), 'preparation receipt reused')
        require(not ({x['object_id'] for x in chain} & self.used_objects), 'preparation object reused across specimens')
        self.specimens[record['specimen_id']] = record
        self.used_objects.update(x['object_id'] for x in chain)
        self.used_receipts.update(x['receipt_id'] for x in chain)

    def calibrate(self, receipt):
        self._open()
        require(self.custody == 'handler' and self.active is None and self.mounted is None, 'calibration requires no active service custody or mount')
        self._new_receipt(receipt)
        for key in ('calibration_id','reference_id','configuration_id','uncertainty_contract_id'):
            require(isinstance(receipt.get(key), str) and receipt[key], 'calibration field missing')
        require(receipt.get('current') is True and receipt.get('bracketing_valid') is True, 'calibration invalid or expired')
        self.calibration = deepcopy(receipt)
        self.used_receipts.add(receipt['receipt_id'])

    def mount(self, slot_id, receipt):
        self._open()
        require(self.custody == 'handler' and self.active is None and self.mounted is None, 'release/retrieval required before mounting')
        self._new_receipt(receipt)
        require(self.calibration is not None, 'calibration missing')
        slot = next((x for x in self.plan if x['slot_id'] == slot_id), None)
        require(slot is not None and slot_id not in self.completed_slots, 'slot unknown or complete')
        spec = self.specimens.get(slot['specimen_id'])
        require(spec is not None, 'specimen preparation missing')
        expected = 'COND_%s_%s' % (spec['sample_family_id'], receipt.get('orientation'))
        require(slot['condition_id'] == expected == receipt.get('condition_id'), 'wrong family/orientation')
        require(receipt.get('specimen_id') == slot['specimen_id'], 'wrong specimen mounted')
        require(receipt.get('calibration_id') == self.calibration['calibration_id'], 'wrong calibration mount')
        for key in ('zero_energy','dry_ambient','qualified_fit','registered_transform','supported_carrier'):
            require(receipt.get(key) is True, 'unqualified mounting condition: '+key)
        require(isinstance(receipt.get('mount_id'),str) and receipt['mount_id'], 'mount ID missing')
        self.mounted = dict(slot=deepcopy(slot), receipt=deepcopy(receipt), specimen=deepcopy(spec))
        self.state = 'MOUNTED'
        self.used_receipts.add(receipt['receipt_id'])

    def handoff(self, run_id, receipt):
        self._open()
        require(self.state == 'MOUNTED' and self.custody == 'handler' and self.active is None, 'mount/handoff sequence invalid')
        self._new_receipt(receipt)
        require(isinstance(run_id,str) and run_id and run_id not in self.runs, 'duplicate or missing run ID')
        require(receipt.get('run_id') == run_id, 'handoff run mismatch')
        require(receipt.get('mount_id') == self.mounted['receipt']['mount_id'], 'handoff mount mismatch')
        require(receipt.get('specimen_id') == self.mounted['specimen']['specimen_id'], 'handoff specimen mismatch')
        # Custody becomes service-owned before checking uncertain acceptance.
        # Even an indeterminate acceptance cannot permit handler retrieval.
        self.active = run_id
        self.runs[run_id] = deepcopy(self.mounted)
        self.runs[run_id].update(status='service_pending', release=None, observation=None)
        self.mounted = None
        self.custody = 'service'
        self.used_receipts.add(receipt['receipt_id'])
        if receipt.get('interlocks_valid') is not True or receipt.get('acceptance') != 'accepted':
            self.stop('indeterminate service acceptance')
            return 'P15'
        self.state = 'P11'
        return self.state

    def observe(self, stage, receipt):
        self._open()
        require(self.custody == 'service' and self.active is not None, 'service has no active run')
        expected = {'P11':'P12', 'P12':'P13', 'P13':'P14'}.get(self.state)
        try:
            require(stage == expected, 'out-of-order observation')
            self._new_receipt(receipt)
            require(receipt.get('run_id') == self.active, 'observation run mismatch')
            if stage == 'P12':
                allowed = {'receipt_id','evidence_class','issuer_role','valid','content_hash','run_id','dataset_id','timebase','configuration_id','stream_integrity','boundary_metadata','data_origin'}
                require(set(receipt) <= allowed, 'unexpected transient payload; metadata only')
                require(receipt.get('data_origin') == 'synthetic_metadata_only', 'source/reference data cannot be transient observation')
                require(receipt.get('configuration_id') == self.calibration['configuration_id'], 'transient camera configuration mismatch')
                for key in ('dataset_id','timebase','configuration_id'):
                    require(isinstance(receipt.get(key),str) and receipt[key], 'transient metadata missing')
                require(receipt.get('stream_integrity') is True and receipt.get('boundary_metadata') is True, 'invalid transient evidence')
                self.runs[self.active]['transient'] = deepcopy(receipt)
            if stage == 'P13':
                allowed = {'receipt_id','evidence_class','issuer_role','valid','content_hash','run_id','qualified_stable','drift_contract','uncertainty_valid','elapsed_minutes','data_origin'}
                require(set(receipt) <= allowed, 'unexpected stability payload; metadata only')
                require(receipt.get('data_origin') == 'synthetic_metadata_only', 'source/reference data cannot establish stability')
                require(receipt.get('qualified_stable') is True and receipt.get('drift_contract') is True and receipt.get('uncertainty_valid') is True, 'elapsed time alone is not stability')
            if stage == 'P14':
                run = self.runs[self.active]
                allowed = {'receipt_id','evidence_class','issuer_role','valid','content_hash','run_id','dataset_id','condition_id','calibration_id','profile_direction','masks_registered','transform_registered','measured_boundaries_present','ambient_present','uncertainty_valid','data_hash_valid','data_origin'}
                require(set(receipt) <= allowed, 'unexpected registered payload; metadata only')
                require(receipt.get('dataset_id') == run['transient']['dataset_id'], 'registered dataset lineage mismatch')
                rule = 'transverse' if run['specimen']['sample_family_id'] == 'ROTATOR45' else 'parallel'
                require(receipt.get('profile_direction') == rule, 'wrong profile direction')
                require(receipt.get('condition_id') == run['slot']['condition_id'], 'registered condition mismatch')
                require(receipt.get('calibration_id') == self.calibration['calibration_id'], 'registered calibration mismatch')
                for key in ('masks_registered','transform_registered','measured_boundaries_present','ambient_present','uncertainty_valid','data_hash_valid'):
                    require(receipt.get(key) is True, 'registered observation field missing: '+key)
                require(receipt.get('data_origin') == 'synthetic_metadata_only', 'source/reference data cannot be observed')
                self.runs[self.active]['observation'] = deepcopy(receipt)
        except Held as error:
            self.stop(str(error))
            raise
        self.used_receipts.add(receipt['receipt_id'])
        self.state = stage
        self.runs[self.active]['status'] = 'acquired' if stage == 'P14' else 'in_progress'
        return stage

    def stop(self, reason):
        require(self.custody == 'service' and self.active is not None, 'no service-owned run')
        require(isinstance(reason,str) and reason.strip(), 'stop reason required')
        self.failures.append(dict(run_id=self.active, from_state=self.state, reason=reason))
        self.runs[self.active]['status'] = 'failed'
        self.state = 'P15'
        return self.state

    def release(self, receipt):
        require(self.custody == 'service' and self.active is not None, 'no service custody to release')
        require(self.state in ('P14','P15','SERVICE_CUSTODY_HOLD'), 'release allowed after terminal capture or requested stop only')
        try:
            self._new_receipt(receipt)
            require(receipt.get('run_id') == self.active, 'release run mismatch')
            require(receipt.get('specimen_id') == self.runs[self.active]['specimen']['specimen_id'], 'release specimen mismatch')
            for key in ('zero_energy','cool','dry','supported_carrier','receiver_accepts','condition_assessed'):
                require(receipt.get(key) is True, 'release condition missing: '+key)
        except Held:
            self.state = 'SERVICE_CUSTODY_HOLD'
            raise
        self.runs[self.active]['release'] = deepcopy(receipt)
        self.used_receipts.add(receipt['receipt_id'])
        self.state = 'RELEASED'
        # Physical custody transfers only at the separate retrieval record.

    def retrieve(self):
        require(self.state == 'RELEASED' and self.active is not None, 'matching safe release required')
        run = self.runs[self.active]
        require(run['release'] is not None, 'missing release')
        if run['status'] == 'acquired':
            self.completed_slots.add(run['slot']['slot_id'])
            run['status'] = 'released_valid_synthetic'
        self.custody = 'handler'
        self.active = None
        self.state = 'READY' if not self.admin_closed else 'ADMIN_INCOMPLETE_RELEASED'

    def reconcile_controls(self, receipt):
        self._open()
        require(self.custody == 'handler' and self.active is None and self.mounted is None, 'finish custody first')
        self._new_receipt(receipt)
        require(receipt.get('matched') is True and receipt.get('independent_identity') is True, 'unmatched controls')
        require(receipt.get('data_origin') == 'synthetic_metadata_only', 'simulated/reference controls rejected')
        require(receipt.get('denominator_safe') is True, 'near-zero or unknown reference denominator')
        require(receipt.get('covers_conditions') == sorted(CONDITIONS), 'control matrix incomplete')
        self.controls = deepcopy(receipt)
        self.used_receipts.add(receipt['receipt_id'])

    def assess(self, receipt):
        self._open()
        require(self.controls is not None, 'controls missing')
        require(self.custody == 'handler' and self.active is None, 'finish custody first')
        self._new_receipt(receipt)
        require(receipt.get('claim_kind') == 'synthetic_contract_pass_only', 'scientific result claim prohibited')
        require(receipt.get('source_holds_preserved') is True, 'source holds cannot be silently resolved')
        require(receipt.get('numerical_computation_performed') is False, 'no metric or physics computation allowed')
        require(receipt.get('uncertainty_contract_present') is True, 'uncertainty contract missing')
        self.analysis = deepcopy(receipt)
        self.used_receipts.add(receipt['receipt_id'])

    def register_numerical(self, ledger):
        self._open()
        require(self.analysis is not None, 'assessment bookkeeping missing')
        require(isinstance(ledger,dict) and set(ledger) == NUMERICAL_BRANCHES, 'numerical branch coverage missing')
        require(all(x == 'unexecuted' for x in ledger.values()), 'numerical results cannot be invented')
        self.numerical_ledger = deepcopy(ledger)

    def close(self, success=False, archive_valid=False, dispositions_valid=False):
        require(not self.closed, 'already closed')
        if not success:
            self.admin_closed = True
            return {'status':'administrative_incomplete','open_service_obligation':self.custody == 'service','scientific_success':False}
        self._open()
        require(self.custody == 'handler' and self.active is None and self.mounted is None, 'custody or unretrieved mount prevents success')
        require({x['slot_id'] for x in self.plan} == self.completed_slots, 'required run slots missing')
        require({x['condition_id'] for x in self.plan} == CONDITIONS, 'six-cell matrix incomplete')
        require(self.controls is not None and self.analysis is not None and self.numerical_ledger is not None, 'analysis/controls/branch ledger missing')
        require(archive_valid is True and dispositions_valid is True, 'archive or safe disposition missing')
        self.closed = True
        self.state = 'CLOSED_SYNTHETIC'
        return {'status':'symbolic_contract_complete','scientific_success':False,'paper_design_units':1,'experiments_performed':0}
