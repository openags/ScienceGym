"""Local metadata-only review guard. It cannot authorize or actuate hardware."""
from dataclasses import dataclass,field
ALLOWED_RECORD_KEYS=frozenset({'sample_id','source_design_record','lot_record','preparation_receipt','assembly_receipt','module_record','circuit_record','thermal_record','isolation_record','calibration_record','acquisition_record','analysis_record','custody_record'})
FORBIDDEN=frozenset({'enable_rf','enable_dc','enable_magnet','ramp_field','cooldown','warmup','pump_vacuum','open_cryostat','transfer_sample','deposit_metal','expose_resist','dispense_solvent','grow_nanotube','heat_sample','wire_bond','acquire_data','fit_source_model','unlock_execution'})
@dataclass
class ReviewGuard:
 state:str='HOLD'
 record_labels:dict=field(default_factory=dict)
 def __post_init__(self):
  if self.state!='HOLD' or self.record_labels:raise ValueError('Initialize empty and held')
 @property
 def energy_enabled(self):return False
 @property
 def physical_execution(self):return False
 @property
 def evidence_verified(self):return False
 def apply(self,action,records=None):
  if not isinstance(action,str):raise ValueError('Action must be a known string')
  if action in FORBIDDEN:raise PermissionError('Permanently disabled; independent qualified external service required')
  if action=='attach_record_labels' and self.state=='HOLD':
   if not isinstance(records,dict) or not records or not set(records)<=ALLOWED_RECORD_KEYS:raise ValueError('Known nonempty labels only')
   if any(not isinstance(v,str) or not v.strip() or len(v)>160 for v in records.values()):raise ValueError('Short nonempty strings only')
   self.record_labels=dict(records);self.state='RECORDS_ATTACHED'
  elif action=='request_review' and self.state=='RECORDS_ATTACHED':self.state='REVIEW_REQUESTED'
  elif action=='clear_record_labels' and self.state in ('RECORDS_ATTACHED','REVIEW_REQUESTED'):self.record_labels={};self.state='HOLD'
  else:raise ValueError('Unavailable metadata transition')
  return {'state':self.state,'record_labels':dict(self.record_labels),'energy_enabled':False,'physical_execution':False,'evidence_verified':False,'safe_to_remove_sample':False}
