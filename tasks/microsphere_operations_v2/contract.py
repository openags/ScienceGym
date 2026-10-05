"""Original offline evidence-ledger contract. No device APIs, physics, or sensor generation.

A trusted evaluator supplies receipt records. This is a finite software boundary,
not cryptographic authentication or permission to operate any laboratory device.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
from pathlib import Path

ALL_BRANCHES = ('E01','E02','E03','E04','C01','C02','C03','E05','C04','N01','N02','N03','N04')
TARGETS = ('E01','E02','E03','E04')
PHYSICAL_STAGES = frozenset(('R02','R03','R04','R05','R06','R07','R08','R09'))
STATES = frozenset(('CONTRACT_REVIEWED','HELD','UNRUN','SOURCE_CONTEXT_ONLY'))
HEX = re.compile(r'[0-9a-f]{64}\Z')
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z')

class ContractError(ValueError):
    pass

def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError) as exc:
        raise ContractError('Noncanonical JSON') from exc

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def require(condition, message):
    if not condition:
        raise ContractError(message)

def exact(obj, fields):
    require(type(obj) is dict and set(obj) == set(fields), 'Unexpected or missing fields')

def token(value):
    require(type(value) is str and TOKEN.fullmatch(value) is not None, 'Invalid identifier')

def sha(value):
    require(type(value) is str and HEX.fullmatch(value) is not None, 'Invalid record hash')

def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), 'Incomplete or unexpected scope')

def identifiers(value, fields):
    for field in fields:
        token(value[field])


def load_contract(root):
    root = Path(root)
    operations = json.loads((root/'operations.json').read_text())['operations']
    require([r['id'] for r in operations] == [f'R{i:02}' for i in range(1,14)], 'Route inventory drift')
    bindings = json.loads((root/'shared_binding_contract.json').read_text())
    by_id = {r['route_id']:r for r in bindings['route_bindings']}
    for op in operations:
        require(op['id'] in by_id, 'Missing route binding')
        require(op['asset_ids'] == by_id[op['id']]['asset_ids'], 'Route asset drift')
        require(op['branch_ids'] == by_id[op['id']]['branch_ids'], 'Route branch drift')
        require([op['station']] == by_id[op['id']]['station_ids'], 'Station drift')
        require(op['device_command_implemented'] is False and op['physical_execution_authority'] is False, 'Actuation prohibited')
    return operations, digest(bindings)


class EvidenceLedger:
    """Actor proposes exactly two IDs; evaluator-owned receipts are copied on entry.

    Every rejected action is retained. Stage attempts are bounded to two. Holds
    are first-class final dispositions. Digital acceptance is never a scientific
    pass and cannot turn on physical execution.
    """
    def __init__(self, root, campaign_id, epoch, frozen_plan_id, trusted_receipts):
        for value in (campaign_id, epoch, frozen_plan_id): token(value)
        self._operations, self._semantic_digest = load_contract(root)
        self._ops = {x['id']:x for x in self._operations}
        require(type(trusted_receipts) is dict, 'Receipt map required')
        self._receipts = json.loads(canonical(trusted_receipts))
        for key, receipt in self._receipts.items():
            token(key)
            require(type(receipt) is dict and receipt.get('receipt_id') == key, 'Receipt identity mismatch')
        self._campaign = campaign_id
        self._epoch = epoch
        self._plan = frozen_plan_id
        self._done = {}
        self._history = []
        self._attempts = {}
        self._used = set()
        self._closed = False

    @property
    def history(self): return copy.deepcopy(self._history)

    @property
    def completed(self): return copy.deepcopy(self._done)

    @property
    def physical_execution_enabled(self): return False

    @property
    def design_complete(self): return self._closed and len(self._done) == 13

    def _record(self, proposal, accepted, reason):
        event = {'index':len(self._history), 'proposal':copy.deepcopy(proposal), 'accepted':accepted, 'reason':reason, 'prior_event_hash':digest(self._history[-1]) if self._history else None}
        self._history.append(event)

    def propose(self, action):
        try:
            canonical(action)
            exact(action, ('operation_id','evidence_id'))
            identifiers(action, ('operation_id','evidence_id'))
            oid, eid = action['operation_id'], action['evidence_id']
            require(not self._closed, 'Ledger already closed')
            require(oid in self._ops, 'Unknown operation')
            require(oid not in self._done, 'Stage already dispositioned')
            self._attempts[oid] = self._attempts.get(oid, 0) + 1
            require(self._attempts[oid] <= 2, 'Digital attempt budget exhausted')
            op = self._ops[oid]
            require(all(d in self._done for d in op['depends_on']), 'Missing dependency disposition')
            require(eid in self._receipts, 'Receipt not independently supplied')
            require(eid not in self._used, 'Receipt replay')
            r = copy.deepcopy(self._receipts[eid])
            self._validate_common(r, op)
            if r['status'] == 'ACCEPTED':
                try:
                    self._validate_payload(oid, r['payload'])
                    self._validate_results(oid, r)
                except (KeyError, TypeError, IndexError, AttributeError) as exc:
                    raise ContractError('Malformed or unavailable evidence') from exc
            else:
                exact(r['payload'], ('reason','safe_state_receipt_id'))
                identifiers(r['payload'], ('reason','safe_state_receipt_id'))
                require(all(s in {'HELD','UNRUN','SOURCE_CONTEXT_ONLY'} for s in r['branch_results'].values()), 'Hold cannot claim reviewed experiment')
                require(oid != 'R13', 'Final closeout requires complete archive evidence')
            if oid == 'R13': self._closed = True
            self._done[oid] = {'receipt_hash':digest(r),'receipt':r,'digital_status':r['status'],'physical_execution':False}
            self._used.add(eid)
            self._record(action, True, 'Digital receipt disposition accepted; no physical execution')
            return copy.deepcopy(self._done[oid])
        except (ContractError, KeyError, TypeError, IndexError, AttributeError) as exc:
            # Invalid JSON values are represented without persisting executable objects.
            try: safe = json.loads(canonical(action))
            except ContractError: safe = {'invalid_proposal':True}
            self._record(safe, False, str(exc))
            raise ContractError(str(exc)) from exc

    def _validate_common(self, r, op):
        exact(r, ('receipt_id','operation_id','campaign_id','epoch','frozen_plan_id','semantic_core_sha256','origin','qualification_refs','status','branch_results','input_receipt_hashes','payload','physical_execution'))
        identifiers(r, ('receipt_id','operation_id','campaign_id','epoch','frozen_plan_id'))
        require(r['operation_id'] == op['id'], 'Receipt operation mismatch')
        require((r['campaign_id'],r['epoch'],r['frozen_plan_id']) == (self._campaign,self._epoch,self._plan), 'Stale or foreign campaign/epoch/plan')
        require(r['semantic_core_sha256'] == self._semantic_digest, 'Semantic core drift')
        require(r['origin'] in {'independent_fixture','external_qualified_record'}, 'Source reports and actor outputs are not observations')
        require(r['physical_execution'] is False, 'No physical release supported')
        require(r['status'] in {'ACCEPTED','HOLD','UNRUN'}, 'Unknown receipt status')
        keys(r['branch_results'], op['branch_ids'])
        require(all(v in STATES for v in r['branch_results'].values()), 'Unknown branch status')
        keys(r['input_receipt_hashes'], op['depends_on'])
        require(r['input_receipt_hashes'] == {d:self._done[d]['receipt_hash'] for d in op['depends_on']}, 'Dependency hash mismatch')
        keys(r['qualification_refs'], op['unresolved_input_refs'])
        for value in r['qualification_refs'].values():
            if value is not None: token(value)
        if r['status'] == 'ACCEPTED':
            require(all(v is not None for v in r['qualification_refs'].values()), 'Unqualified accepted stage')
            if op['id'] in PHYSICAL_STAGES:
                require(all(self._done[d]['digital_status']=='ACCEPTED' for d in op['depends_on']), 'Held dependency cannot release downstream service')
        # Holdings stay local. A service can have a held branch alongside accepted
        # records only if the payload itself preserves that exact branch status.

    def _validate_results(self, oid, r):
        p = r['payload']
        if oid in {'R01','R05','R10'}:
            expected = {b:'SOURCE_CONTEXT_ONLY' for b in self._ops[oid]['branch_ids']}
        elif oid == 'R12':
            expected = {b:'UNRUN' for b in self._ops[oid]['branch_ids']}
        elif oid == 'R09':
            expected = {'C01':'CONTRACT_REVIEWED'}
        elif oid == 'R06':
            expected = {b:p[b]['status'] for b in TARGETS}
            expected['C01']='CONTRACT_REVIEWED'
        elif oid == 'R13':
            expected = p['branch_dispositions']
            require(expected == self.final_branch_dispositions(), 'Closeout promotes or drops prior branch status')
        else:
            expected = {b:p[b]['status'] for b in self._ops[oid]['branch_ids']}
        require(r['branch_results'] == expected, 'Branch results disagree with evidence')

    def final_branch_dispositions(self):
        stages={'E01':'R11','E02':'R11','E03':'R11','E04':'R11','C01':'R11','C02':'R10','C03':'R10','C04':'R10','E05':'R10','N01':'R12','N02':'R12','N03':'R12','N04':'R12'}
        return {b:self._done[s]['receipt']['branch_results'][b] for b,s in stages.items() if s in self._done}

    def _validate_payload(self, oid, p):
        getattr(self, '_'+oid)(p)

    def _R01(self, p):
        exact(p, ('doi','rights_scope','main_pages','si_pages','dedup_receipt_id','source_version_id','publisher_exports','repeat_policy_id','metric_policy_id','exclusion_policy_id'))
        require(p['doi']=='10.1038/ncomms1211' and p['rights_scope']=='original_only', 'Wrong source or rights scope')
        require(type(p['main_pages']) is int and p['main_pages']==6 and type(p['si_pages']) is int and p['si_pages']==7, 'Incomplete source coverage')
        require(p['publisher_exports'] is False, 'Publisher export prohibited')
        identifiers(p, ('dedup_receipt_id','source_version_id','repeat_policy_id','metric_policy_id','exclusion_policy_id'))

    def _R02(self, p):
        keys(p, TARGETS)
        for branch, row in p.items():
            exact(row, ('specimen_id','material_id','state_id','container_id','lot_id','surface_identity','identity_receipt_id','status'))
            identifiers(row, ('specimen_id','material_id','state_id','container_id','lot_id'))
            require(row['material_id']=={'E01':'M02','E02':'M03','E03':'M04','E04':'M05'}[branch], 'Material branch mismatch')
            require(row['status'] in {'HELD','CONTRACT_REVIEWED'}, 'Invalid target status')
            if row['status']=='HELD':
                require(row['identity_receipt_id'] is None, 'Held identity must not appear certified')
            else:
                identifiers(row, ('surface_identity','identity_receipt_id'))
                require(row['surface_identity'] != 'unresolved', 'Missing target identity')
        require(len({r['specimen_id'] for r in p.values()})==4, 'Duplicate target identity')

    def _R03(self, p):
        keys(p, TARGETS)
        inventory=self._done['R02']['receipt']['payload']
        for branch, row in p.items():
            exact(row, ('specimen_id','parent_state_id','state_id','closed_service_job_id','certificate_id','geometry_certificate_id','surface_condition_id','roi_map_id','status'))
            if row['status']=='HELD':
                require(inventory[branch]['status']=='HELD', 'Unexpected preparation hold policy')
                require(row['specimen_id']==inventory[branch]['specimen_id'], 'Held specimen drift')
                require(all(row[k] is None for k in row if k not in {'specimen_id','status'}), 'Held preparation invents qualification')
                continue
            require(row['status']=='CONTRACT_REVIEWED' and inventory[branch]['status']=='CONTRACT_REVIEWED','Unqualified preparation identity')
            identifiers(row, tuple(k for k in row if k!='status'))
            require(row['specimen_id']==inventory[branch]['specimen_id'] and row['parent_state_id']==inventory[branch]['state_id'], 'Preparation lineage mismatch')
            require(row['state_id']!=row['parent_state_id'], 'Preparation must create child state')

    def _measurement(self, r, modality, mode=None):
        exact(r, ('record_id','specimen_id','state_id','roi_id','calibration_id','frame_id','raw_record_sha256','modality','mode','focus_receipt_id','detector_scale_receipt_id','data_quality_receipt_id','outcome','origin'))
        identifiers(r, ('record_id','specimen_id','state_id','roi_id','calibration_id','frame_id','focus_receipt_id','detector_scale_receipt_id','data_quality_receipt_id'))
        sha(r['raw_record_sha256'])
        require(r['modality']==modality and r['mode']==mode, 'Measurement mode mismatch')
        require(r['frame_id']==('FRAME_SEM' if modality=='SEM' else 'FRAME_DETECTOR'), 'Measurement frame mismatch')
        require(r['origin'] in {'independent_fixture','external_qualified_record'}, 'Source or rendered record is not measured evidence')
        require(r['outcome'] in {'not_assessed','unresolved','resolved','invalid'}, 'Unrecognized outcome')
        if r['origin']=='independent_fixture': require(r['outcome']=='not_assessed', 'Fixture cannot generate scientific outcome')

    def _R04(self, p):
        keys(p, TARGETS)
        prep=self._done['R03']['receipt']['payload']
        for branch,row in p.items():
            exact(row, ('status','reference','post_service_state_id','perturbation_receipt_id'))
            require(row['status']==prep[branch]['status'],'Reference status drift')
            if row['status']=='HELD':
                require(row['reference'] is None and row['post_service_state_id'] is None and row['perturbation_receipt_id'] is None,'Held reference must be absent');continue
            self._measurement(row['reference'],'SEM')
            identifiers(row, ('post_service_state_id','perturbation_receipt_id'))
            ref=row['reference']
            require(ref['specimen_id']==prep[branch]['specimen_id'] and ref['state_id']==prep[branch]['state_id'],'Reference lineage mismatch')
            require(row['post_service_state_id']!=ref['state_id'],'SEM exposure needs explicit child-state identity')

    def _R05(self, p):
        exact(p, ('sphere_lots','sil_controls','star_sphere_diameter_um','contained_stock_receipt_id'))
        require(type(p['sphere_lots']) is list and len(p['sphere_lots'])==5,'Sphere conditions missing')
        require([x['nominal_diameter_um'] for x in p['sphere_lots']]==[1,3,4.74,10,50],'Sphere sizes conflated')
        for row in p['sphere_lots']:
            exact(row, ('lot_id','nominal_diameter_um','distribution_certificate_id','chemistry_certificate_id'))
            require(type(row['nominal_diameter_um']) in (int,float),'Invalid nominal size')
            identifiers(row, ('lot_id','distribution_certificate_id','chemistry_certificate_id'))
        require(len({x['lot_id'] for x in p['sphere_lots']})==5,'Sphere lots conflated')
        keys(p['sil_controls'], ('SIL_0p5mm','SIL_2p5mm'))
        for lid,obj in [('SIL_0p5mm',80),('SIL_2p5mm',40)]:
            row=p['sil_controls'][lid]
            exact(row, ('material_id','objective_magnification','compatibility_receipt_id'))
            require(type(row['objective_magnification']) is int and row['objective_magnification']==obj,'Objective control distinction lost')
            require(row['material_id']==('M06' if obj==80 else 'M07'),'SIL identity mismatch')
            token(row['compatibility_receipt_id'])
        require(p['star_sphere_diameter_um'] is None,'Source star sphere diameter is unreported')
        token(p['contained_stock_receipt_id'])

    def _R06(self, p):
        keys(p, (*TARGETS,'C01'))
        refs=self._done['R04']['receipt']['payload']
        for branch in TARGETS:
            row=p[branch]
            exact(row, ('status','specimen_id','baseline_state_id','child_state_id','contact_receipt_id','sphere_lot_id','coverage_receipt_id','bare_state_id'))
            require(row['status']==refs[branch]['status'],'Assembly status drift')
            require(row['specimen_id']==self._done['R02']['receipt']['payload'][branch]['specimen_id'],'Assembly specimen identity drift')
            if row['status']=='HELD':
                require(all(row[k] is None for k in row if k not in {'status','specimen_id'}),'Held assembly cannot fabricate state');continue
            identifiers(row, tuple(k for k in row if k!='status'))
            require(row['specimen_id']==refs[branch]['reference']['specimen_id'],'Assembly specimen mismatch')
            require(row['baseline_state_id']==refs[branch]['post_service_state_id'],'Assembly baseline mismatch')
            require(row['child_state_id']!=row['baseline_state_id'] and row['bare_state_id']==row['baseline_state_id'],'Lost pre-alteration bare state')
            require(row['sphere_lot_id'] in {s['lot_id'] for s in self._done['R05']['receipt']['payload']['sphere_lots']},'Unqualified sphere lot')
        c=p['C01'];exact(c, ('bare_specimen_id','bare_state_id','matched_specimen_receipt_id','sil_0p5_contact_receipt_id','sil_2p5_contact_receipt_id','sil_0p5_child_state_id','sil_2p5_child_state_id'))
        identifiers(c, tuple(c))
        require(c['bare_state_id']!=p['E03']['child_state_id'],'Coated state cannot stand in for bare comparator')
        require(len({c['bare_state_id'],c['sil_0p5_child_state_id'],c['sil_2p5_child_state_id'],p['E03']['child_state_id']})==4,'Control states must remain distinct')

    def _optical(self,p,branches,mode):
        keys(p,branches); assembly=self._done['R06']['receipt']['payload']
        for branch,row in p.items():
            exact(row, ('status','optical','object_frame','virtual_frame','registration_receipt_id'))
            require(row['status']==assembly[branch]['status'],'Optical status drift')
            if row['status']=='HELD': require(row['optical'] is None and row['registration_receipt_id'] is None,'Held optical evidence must be absent');continue
            self._measurement(row['optical'],'optical',mode)
            require(row['optical']['specimen_id']==assembly[branch]['specimen_id'] and row['optical']['state_id']==assembly[branch]['child_state_id'],'Optical lineage mismatch')
            require(row['object_frame']=='FRAME_OBJECT' and row['virtual_frame']=='FRAME_VIRTUAL','Object/virtual planes conflated')
            token(row['registration_receipt_id'])

    def _R07(self,p): self._optical(p,('E01','E02'),'transmission')
    def _R08(self,p): self._optical(p,('E03','E04'),'reflection')

    def _R09(self,p):
        keys(p,('bare','SIL_0p5mm','SIL_2p5mm'))
        focus=[];assembly=self._done['R06']['receipt']['payload']['C01']
        for condition,row in p.items():
            exact(row,('optical','objective_magnification','contact_receipt_id','matched_specimen_receipt_id'))
            self._measurement(row['optical'],'optical','reflection')
            require(type(row['objective_magnification']) is int and row['objective_magnification']==(40 if condition=='SIL_2p5mm' else 80),'Control objective mismatch')
            identifiers(row,('contact_receipt_id','matched_specimen_receipt_id'))
            focus.append(row['optical']['focus_receipt_id'])
            require(row['matched_specimen_receipt_id']==assembly['matched_specimen_receipt_id'],'Control equivalence receipt mismatch')
            if condition!='bare':
                prefix='sil_0p5' if condition=='SIL_0p5mm' else 'sil_2p5'
                require(row['optical']['specimen_id']==assembly['bare_specimen_id'] and row['optical']['state_id']==assembly[prefix+'_child_state_id'],'SIL contact state mismatch')
                require(row['contact_receipt_id']==assembly[prefix+'_contact_receipt_id'],'SIL contact receipt mismatch')
            if condition=='bare':
                require(row['optical']['state_id']==assembly['bare_state_id'] and row['optical']['specimen_id']==assembly['bare_specimen_id'],'Bare control lineage mismatch')
        require(len(set(focus))==3,'Controls require independent focus records')

    def _R10(self,p):
        keys(p,('C02','C03','C04','E05'))
        for branch,row in p.items():
            exact(row,('evidence_class','status','new_data','limitation'))
            require(row['evidence_class']==('illustrated_array_unqualified_processing' if branch=='C04' else 'text_only'),'Source evidence class promoted')
            require(row['status']=='SOURCE_CONTEXT_ONLY' and row['new_data'] is False,'Claim inventory is not new observation')
            token(row['limitation'])

    def _R11(self,p):
        keys(p,(*TARGETS,'C01'))
        for branch,row in p.items():
            exact(row,('status','optical_record_id','reference_record_id','correspondence','equivalence_receipt_id','limitation_id','metric_policy_id','uncertainty_receipt_id','reviewer_id','resolution_certified'))
            require(row['resolution_certified'] is False,'No resolution certification in this task')
            if row['status']=='HELD':
                require(row['optical_record_id'] is None and row['reference_record_id'] is None,'Held comparison must remain missing');continue
            require(row['status']=='CONTRACT_REVIEWED','Invalid comparison status')
            identifiers(row,('optical_record_id','reference_record_id','equivalence_receipt_id','limitation_id','metric_policy_id','uncertainty_receipt_id','reviewer_id'))
            require(row['metric_policy_id']==self._done['R01']['receipt']['payload']['metric_policy_id'],'Metric policy changed after plan freeze')
            origin_branch='E03' if branch=='C01' else branch
            source_op='R07' if origin_branch in ('E01','E02') else 'R08'
            optical=self._done[source_op]['receipt']['payload'][origin_branch]['optical'] if branch!='C01' else self._done['R09']['receipt']['payload']['bare']['optical']
            reference=self._done['R04']['receipt']['payload'][origin_branch]['reference']
            require(optical is not None and reference is not None,'Missing measured pairing')
            require(row['optical_record_id']==optical['record_id'] and row['reference_record_id']==reference['record_id'],'Record pairing mismatch')
            require(row['correspondence'] in {'exact_state_ROI','documented_equivalence'},'Unqualified correspondence')
            if row['correspondence']=='exact_state_ROI':
                require(all(optical[k]==reference[k] for k in ('specimen_id','state_id','roi_id')),'Exact pairing is not exact')
            # Different specimen/state/ROI is allowed only as a separately qualified,
            # explicitly limited equivalence. It never becomes exact correspondence.

    def _R12(self,p):
        keys(p,('N01','N02','N03','N04'))
        for row in p.values():
            exact(row,('status','source_method_receipt_id','code_run','simulation_run','generated_data'))
            require(row['status']=='UNRUN' and row['code_run'] is False and row['simulation_run'] is False and row['generated_data'] is False,'Model branches must remain unrun')
            token(row['source_method_receipt_id'])

    def _R13(self,p):
        exact(p,('archive_receipt_hashes','branch_dispositions','specimen_dispositions','safe_state_receipt_id','containment_receipt_id','service_release_id','failure_event_hashes','scientific_execution_complete'))
        require(set(self._done)=={f'R{i:02}' for i in range(1,13)},'Closeout requires all stage dispositions')
        require(p['archive_receipt_hashes']=={k:v['receipt_hash'] for k,v in self._done.items()},'Archive omits or alters evidence')
        keys(p['branch_dispositions'],ALL_BRANCHES)
        require(all(v in STATES for v in p['branch_dispositions'].values()),'Invalid final branch disposition')
        require(p['scientific_execution_complete'] is False,'Design closeout is not scientific execution')
        keys(p['specimen_dispositions'],TARGETS)
        for row in p['specimen_dispositions'].values():
            exact(row,('specimen_id','destination_id','disposition'))
            if self._done['R02']['digital_status']=='ACCEPTED':
                identifiers(row,('specimen_id','destination_id'))
                require(row['disposition'] in {'archive','return','quarantine'},'Invalid specimen disposition')
            else:
                require(row['specimen_id'] is None and row['destination_id'] is None and row['disposition']=='not_received','Unreceived specimens require explicit missing identities')
        identifiers(p,('safe_state_receipt_id','containment_receipt_id','service_release_id'))
        if self._done['R02']['digital_status']=='ACCEPTED':
            inventory=self._done['R02']['receipt']['payload']
            require(all(p['specimen_dispositions'][b]['specimen_id']==inventory[b]['specimen_id'] for b in TARGETS),'Closeout specimen identity drift')
            require(all(p['specimen_dispositions'][b]['disposition']=='quarantine' for b in TARGETS if p['branch_dispositions'][b]=='HELD'),'Held specimens must remain quarantined')
        require(p['failure_event_hashes']==[digest(e) for e in self._history if not e['accepted']],'Failure history omitted or altered')
