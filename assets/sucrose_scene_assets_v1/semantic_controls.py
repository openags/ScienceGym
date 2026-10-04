"""Local static scene guard. No I/O, hardware, fluid physics, optics or measured outputs.
Mock acknowledgements never resolve source conflict or authorize physical execution.
"""
from dataclasses import dataclass,field,asdict
import json

class Hold(RuntimeError):pass

def valid_id(value):
    return isinstance(value,str) and bool(value.strip())

@dataclass
class StaticSceneState:
    cartridge_docked: bool=False
    retention_closed: bool=False
    inlet_isolated: bool=True
    inlet_isolation_verified: bool=False
    inlet_clamp_cycle: int=0
    inlet_verified_cycle: int|None=None
    inlet_consumed_cycle: int=0
    sample_id: str|None=None
    aliquot_id: str|None=None
    setup_version: str='AUTHORED_SCENE_V1'
    plate_id: str='UNQUALIFIED_PLATE'
    wavelength_profile_id: str='UNQUALIFIED_WAVELENGTH'
    reference_id: str|None=None
    fixture_calibration_id: str|None=None
    fixture_calibration_context: tuple|None=None
    fixture_acknowledged: bool=False
    calibration_epoch: int=0
    flow_hold: bool=True
    flow_conflict_id: str='FLOW_40X'
    physical_execution: bool=False
    source_flow_resolved: bool=False
    journal: list=field(default_factory=list)

    def _record(self,action):
        self.journal.append({'action':action,'origin':'authored_static_fixture','physical_execution':False,'source_flow_resolved':False})

    def _invalidate(self):
        self.fixture_calibration_id=None
        self.fixture_calibration_context=None
        self.calibration_epoch+=1

    def dock(self):
        if self.cartridge_docked:raise Hold('ALREADY_DOCKED')
        self.cartridge_docked=True;self._record('DOCK_CARTRIDGE')

    def retain(self):
        if not self.cartridge_docked:raise Hold('CARTRIDGE_NOT_DOCKED')
        self.retention_closed=True;self._record('RETAIN_CARRIER_STATIC')

    def release_retention(self):
        if not self.inlet_isolated:raise Hold('INLET_NOT_ISOLATED')
        self.retention_closed=False;self._record('RELEASE_RETENTION_STATIC')

    def undock(self):
        if self.retention_closed:raise Hold('RETENTION_CLOSED')
        if not self.inlet_isolated:raise Hold('INLET_NOT_ISOLATED')
        self.cartridge_docked=False;self.inlet_isolation_verified=False;self.inlet_verified_cycle=None;self.inlet_consumed_cycle=self.inlet_clamp_cycle;self._invalidate();self._record('UNDOCK')

    def isolate_inlet(self):
        if not self.cartridge_docked:raise Hold('CARTRIDGE_NOT_DOCKED')
        self.inlet_isolated=True;self.inlet_isolation_verified=False;self.inlet_clamp_cycle+=1;self.inlet_verified_cycle=None;self._record('CLAMP')

    def verify_clamp(self,*,observed_closed):
        if not self.cartridge_docked:raise Hold('CARTRIDGE_NOT_DOCKED')
        if type(observed_closed) is not bool:raise Hold('INVALID_CLAMP_OBSERVATION')
        if self.inlet_clamp_cycle<=self.inlet_consumed_cycle:raise Hold('FRESH_CLAMP_CYCLE_REQUIRED')
        self.inlet_isolation_verified=observed_closed and self.inlet_isolated
        self.inlet_verified_cycle=self.inlet_clamp_cycle if self.inlet_isolation_verified else None
        self._record('VERIFY_CLAMP_FIXTURE_OBSERVATION_ONLY')
        if not self.inlet_isolation_verified:raise Hold('CLAMP_NOT_VERIFIED')

    def switch_sample(self,sample_id,aliquot_id):
        if not self.cartridge_docked:raise Hold('CARTRIDGE_NOT_DOCKED')
        if not self.inlet_isolated:raise Hold('INLET_NOT_ISOLATED')
        if not self.inlet_isolation_verified or self.inlet_verified_cycle!=self.inlet_clamp_cycle or self.inlet_clamp_cycle<=self.inlet_consumed_cycle:raise Hold('CLAMP_NOT_VERIFIED')
        if not valid_id(sample_id) or not valid_id(aliquot_id):raise Hold('MISSING_SAMPLE_OR_ALIQUOT')
        self.sample_id=sample_id;self.aliquot_id=aliquot_id;self.reference_id=None
        self.inlet_consumed_cycle=self.inlet_clamp_cycle;self.inlet_isolation_verified=False;self.inlet_verified_cycle=None
        self._record('SWITCH_SAMPLE_IDENTITY_ONLY')

    def change_setup(self,*,plate_id=None,wavelength_profile_id=None,setup_version=None):
        updates=[('plate_id',plate_id),('wavelength_profile_id',wavelength_profile_id),('setup_version',setup_version)]
        if any(value is not None and not valid_id(value) for _,value in updates):raise Hold('INVALID_CONFIGURATION_ID')
        changed=False
        for key,value in updates:
            if value is not None and value!=getattr(self,key):setattr(self,key,value);changed=True
        if changed:self._invalidate();self._record('INVALIDATE_CALIBRATION')

    def bind_reference(self,reference_id):
        if not valid_id(self.sample_id) or not valid_id(reference_id):raise Hold('MISSING_REFERENCE_LINEAGE')
        self.reference_id=reference_id;self._record('BIND_REFERENCE_FIXTURE')

    def acknowledge_fixture_service(self):
        self.fixture_acknowledged=True;self._record('ACK_FIXTURE_ONLY')
        return {'status':'FIXTURE_ONLY','source_flow_resolved':False,'pump_enabled':False}

    def bind_fixture_calibration(self,calibration_id):
        if not self.fixture_acknowledged or not valid_id(self.reference_id) or not valid_id(calibration_id):raise Hold('FIXTURE_PREREQUISITES_MISSING')
        self.fixture_calibration_id=calibration_id;self.fixture_calibration_context=(self.setup_version,self.plate_id,self.wavelength_profile_id);self._record('BIND_CALIBRATION_FIXTURE')

    def request_pump(self,*args,**kwargs):
        raise Hold('FLOW_40X_UNRESOLVED_NO_DEVICE_ADAPTER')

    def request_acquisition(self):
        raise Hold('NO_PHYSICAL_ACQUISITION_ADAPTER')

    def fixture_pair(self,*,run_id,beam_frame_id,speckle_frame_id):
        if not self.cartridge_docked or not self.retention_closed:raise Hold('CARTRIDGE_NOT_RETAINED')
        if not self.fixture_acknowledged:raise Hold('FIXTURE_NOT_ACKNOWLEDGED')
        if not all(valid_id(v) for v in [self.sample_id,self.aliquot_id,self.setup_version,self.plate_id,self.wavelength_profile_id,self.reference_id,self.fixture_calibration_id,run_id,beam_frame_id,speckle_frame_id]):raise Hold('INCOMPLETE_LINEAGE')
        if self.fixture_calibration_context!=(self.setup_version,self.plate_id,self.wavelength_profile_id):raise Hold('CALIBRATION_CONTEXT_MISMATCH')
        if beam_frame_id==speckle_frame_id:raise Hold('FRAME_ROLE_ID_COLLISION')
        self._record('FIXTURE_PAIR_METADATA')
        return {'origin':'authored_fixture_not_measurement','sample_id':self.sample_id,'aliquot_id':self.aliquot_id,'setup_version':self.setup_version,'plate_id':self.plate_id,'wavelength_profile_id':self.wavelength_profile_id,'reference_id':self.reference_id,'calibration_id':self.fixture_calibration_id,'calibration_epoch':self.calibration_epoch,'frame_pair':{'beam_frame_id':beam_frame_id,'speckle_frame_id':speckle_frame_id},'run_id':run_id,'physical_execution':False,'source_flow_resolved':False,'pump_enabled':False,'measurement_value':None,'image_data':None}

if __name__=='__main__':
    s=StaticSceneState();s.dock();s.retain();s.isolate_inlet();s.verify_clamp(observed_closed=True);s.switch_sample('FIXTURE_SAMPLE','FIXTURE_ALIQUOT');s.bind_reference('FIXTURE_REFERENCE');s.acknowledge_fixture_service();s.bind_fixture_calibration('FIXTURE_CALIBRATION');receipt=s.fixture_pair(run_id='FIXTURE_RUN',beam_frame_id='FIXTURE_BEAM',speckle_frame_id='FIXTURE_SPECKLE')
    print(json.dumps({'state':asdict(s),'fixture_receipt':receipt},indent=2))
