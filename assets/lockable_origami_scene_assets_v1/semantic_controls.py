"""Metadata-only review guard. It cannot authorize or actuate hardware."""
from dataclasses import dataclass, field
ALLOWED_RECORD_KEYS=frozenset({'sample_id','source_design_record','lot_record','cutting_receipt','bonding_receipt','mode_record','restraint_record','load_record','image_record','calibration_record','analysis_record'})
FORBIDDEN=frozenset({'laser_on','dispense_adhesive','fold_hardware','apply_load','cut_band_under_preload','acquire_DIC','unlock_execution','predict_force','validate_topology'})
@dataclass
class ReviewGuard:
    state: str = 'HOLD'
    record_labels: dict = field(default_factory=dict)
    def __post_init__(self):
        if self.state!='HOLD' or self.record_labels: raise ValueError('Initialize empty and held')
    @property
    def energy_enabled(self): return False
    @property
    def physical_execution(self): return False
    def apply(self,action,records=None):
        if action in FORBIDDEN: raise PermissionError('Permanently disabled: external qualified service required')
        if action=='attach_record_labels' and self.state=='HOLD':
            if not isinstance(records,dict) or not records or not set(records)<=ALLOWED_RECORD_KEYS: raise ValueError('Known nonempty labels only')
            if any(not isinstance(v,str) or not v.strip() or len(v)>160 for v in records.values()): raise ValueError('Short nonempty strings only')
            self.record_labels=dict(records);self.state='RECORDS_ATTACHED'
        elif action=='request_review' and self.state=='RECORDS_ATTACHED': self.state='REVIEW_REQUESTED'
        elif action=='clear_record_labels' and self.state in ('RECORDS_ATTACHED','REVIEW_REQUESTED'): self.record_labels={};self.state='HOLD'
        else: raise ValueError('Unavailable metadata transition')
        return {'state':self.state,'record_labels':dict(self.record_labels),'energy_enabled':False,'physical_execution':False,'evidence_verified':False}
