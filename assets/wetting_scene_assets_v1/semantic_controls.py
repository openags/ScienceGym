"""Strict local preview and record-label controls, never an equipment controller.
A label is not a receipt, observation, qualification, safe release or evidence.
"""
from dataclasses import dataclass, field
from types import MappingProxyType
SCENE_STATES=frozenset({'unprepared','processing_external','quarantined','age_hold','qualified_unpatterned','qualified_patterned','mounted','acquiring','partial_data','inference_hold','archived'})
VIEWS=frozenset({'overview','handling','dimensions'})
RECORD_KEYS=frozenset({'sample_id','material_record','age_record','pattern_receipt','calibration_record','acquisition_record','raw_archive','annotation_record','analysis_record','isolation_record','custody_record'})
FORBIDDEN=frozenset({'synthesize_quantum_dots','prepare_ink','nanoprint','set_high_voltage','enable_laser','move_stage','open_chamber','dispense_water','set_humidity','set_flow','cure_polymer','apply_load','oscillate_rheometer','grasp_film','grasp_tip','grasp_fiducial','remove_sample','verify_receipt','certify_age','declare_observation','declare_success','unlock_execution'})
@dataclass(slots=True)
class ReviewGuard:
 review_state: str = 'HOLD'
 preview_state: str = 'unprepared'
 view: str = 'overview'
 _labels: dict = field(default_factory=dict,repr=False)
 def __post_init__(self):
  if self.review_state!='HOLD' or self.preview_state!='unprepared' or self.view!='overview' or self._labels:raise ValueError('Initialize empty and held')
 @property
 def record_labels(self):return MappingProxyType(dict(self._labels))
 @property
 def physical_execution(self):return False
 @property
 def energy_enabled(self):return False
 @property
 def evidence_verified(self):return False
 @property
 def safe_to_remove_sample(self):return False
 def apply(self,action,*,value=None,records=None):
  if type(action) is not str:raise ValueError('Known string action required')
  if action in FORBIDDEN:raise PermissionError('Permanently disabled external service or forbidden contact')
  if action=='select_view':
   if records is not None or type(value) is not str or value not in VIEWS:raise ValueError('Known view only')
   self.view=value
  elif action=='preview_scene_state':
   if records is not None or type(value) is not str or value not in SCENE_STATES:raise ValueError('Known display-only state only')
   self.preview_state=value
  elif action=='attach_record_labels':
   if value is not None or self.review_state!='HOLD' or type(records) is not dict or not records or not set(records)<=RECORD_KEYS:raise ValueError('Held review and known nonempty labels required')
   if any(type(v) is not str or not v.strip() or len(v)>160 or any(ord(c)<32 for c in v) for v in records.values()):raise ValueError('Short printable string labels only')
   self._labels=dict(records);self.review_state='RECORDS_ATTACHED'
  elif action=='request_review':
   if value is not None or records is not None or self.review_state!='RECORDS_ATTACHED':raise ValueError('Attach labels first')
   self.review_state='REVIEW_REQUESTED'
  elif action=='request_safe_close':
   if value is not None or records is not None:raise ValueError('No fabricated closeout values')
   self.review_state='SAFE_CLOSE_REVIEW_REQUESTED'
  elif action=='clear_record_labels':
   if value is not None or records is not None:raise ValueError('No parameters allowed')
   self._labels={};self.review_state='HOLD'
  else:raise ValueError('Unknown or unavailable action')
  return {'review_state':self.review_state,'preview_state':self.preview_state,'preview_only':True,'view':self.view,'record_labels':dict(self._labels),'physical_execution':False,'energy_enabled':False,'evidence_verified':False,'safe_to_remove_sample':False,'scientific_success':False,'authority':'none'}
