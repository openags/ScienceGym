"""Pure in-memory static-scene guard examples, NOT a device or security controller.

All receipts are explicitly constructed test evidence. They are never laboratory
evidence, authenticated service receipts, calibrated states, or motion permission.
There is deliberately no hardware/physics/renderer binding in this module.
"""
from dataclasses import dataclass, field

class GuardHold(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise GuardHold(message)

@dataclass(frozen=True)
class TestReceipt:
    epoch: str
    carrier_id: str | None = None
    mode: str | None = None
    spatial_sensor_id: str | None = None
    purpose: str = 'authored_semantic_test'

    def validate(self):
        require(self.purpose == 'authored_semantic_test', 'Only labeled test receipts are accepted')
        require(isinstance(self.epoch, str) and bool(self.epoch.strip()), 'Epoch identity is required')
        require(self.mode in {None, 'analog', 'photon_count'}, 'Unknown detector mode')
        require(self.carrier_id is None or self.carrier_id in {'CU-E','CU-C','CU-N','CU-U','SI-STAR','BLANK','REFERENCE'}, 'Unknown receipt carrier')
        require(self.spatial_sensor_id is None or (isinstance(self.spatial_sensor_id,str) and bool(self.spatial_sensor_id.strip()) and self.spatial_sensor_id==self.spatial_sensor_id.strip()), 'Spatial sensor identity must be nonblank')

@dataclass
class GuardedStaticScene:
    """A review-only state ledger. Physical execution remains permanently false."""
    epoch: str = 'unconfigured'
    mode: str | None = None
    carrier: str | None = None
    door_closed: bool = True
    energy_safe: bool = False
    lease: str | None = None
    diagnostic_sensor_id: str | None = None
    history: list = field(default_factory=list)
    quarantined: set = field(default_factory=set)
    failed_records: list = field(default_factory=list)
    used_epochs: set = field(default_factory=set)
    physical_execution_enabled: bool = field(default=False, init=False)

    def _held(self):
        require(self.physical_execution_enabled is False, 'Physical execution is never available')

    def configure(self, receipt):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(self.lease is None, 'Configuration cannot change under a lease')
        require(receipt.mode is not None, 'Explicit detector mode required')
        require(receipt.epoch not in self.used_epochs and receipt.epoch != 'unconfigured', 'Configuration epoch must be fresh and cannot be reused')
        self.used_epochs.add(receipt.epoch)
        self.epoch=receipt.epoch; self.mode=receipt.mode; self.diagnostic_sensor_id=receipt.spatial_sensor_id
        self.energy_safe=False
        self.history.append(('test_configuration',self.epoch,self.mode))

    def record_safe_access(self, receipt):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(self.lease is None, 'Active acquisition/motion prevents access')
        require(receipt.epoch==self.epoch, 'Stale safe-access epoch')
        self.energy_safe=True; self.history.append(('test_safe_access',self.epoch))

    def set_door(self, closed):
        self._held(); require(type(closed) is bool, 'Explicit Boolean door state required')
        require(self.lease is None, 'Door may not change under a lease')
        if not closed: require(self.energy_safe, 'Opening needs same-epoch safe-access test receipt')
        self.door_closed=closed; self.history.append(('static_door',closed))

    def load(self, carrier_id, receipt):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(carrier_id in {'CU-E','CU-C','CU-N','CU-U','SI-STAR','BLANK','REFERENCE'}, 'Unknown carrier')
        require(carrier_id not in self.quarantined, 'Quarantined carrier cannot be selected')
        require(self.carrier is None, 'Exclusive dock occupancy')
        require(self.lease is None and self.energy_safe and not self.door_closed, 'Load requires safe open unleased dock')
        require(receipt.epoch==self.epoch and receipt.carrier_id==carrier_id, 'Identity/epoch mismatch')
        self.carrier=carrier_id; self.history.append(('static_load',carrier_id,self.epoch))

    def unload(self, receipt):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(self.carrier is not None, 'Empty dock')
        require(self.lease is None and self.energy_safe and not self.door_closed, 'Unload requires safe open unleased dock')
        require(receipt.epoch==self.epoch and receipt.carrier_id==self.carrier, 'Identity/epoch mismatch')
        old=self.carrier; self.carrier=None; self.history.append(('static_unload',old,self.epoch)); return old

    def reserve_acquisition(self, branch, receipt, *, dynamic_plan_id=None, grid=None, source_rate_hz=None):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(branch in {f'B{i:02}' for i in range(1,9)}, 'Unknown branch')
        require(self.lease is None, 'Exclusive acquisition/motion/configuration lease')
        require(self.door_closed, 'Acquisition requires closed enclosure state')
        require(self.carrier not in self.quarantined, 'Quarantined carrier cannot be acquired')
        require(receipt.epoch==self.epoch and receipt.mode==self.mode, 'Stale/incompatible detector epoch')
        if branch=='B01':
            require(self.carrier is None and receipt.carrier_id is None, 'Mapping branch requires object-removed empty dock and no receipt carrier')
            require(self.diagnostic_sensor_id and receipt.spatial_sensor_id==self.diagnostic_sensor_id, 'Spatial sensor receipt required; bucket detector is insufficient')
        elif branch in {'B02','B03'}:
            require(self.mode=='analog' and self.carrier in {'CU-E','CU-C','CU-N','CU-U'}, 'Copper analog branch requires copper and analog mode')
        elif branch=='B08':
            require(self.mode=='photon_count' and self.carrier=='SI-STAR', 'Silicon branch requires silicon and photon mode')
        else:
            require(self.mode=='photon_count' and self.carrier in {'CU-E','CU-C','CU-N','CU-U'}, 'Copper photon branch requires copper and photon mode')
        if self.carrier is not None: require(receipt.carrier_id==self.carrier, 'Acquisition carrier identity mismatch')
        if branch=='B03': require(isinstance(dynamic_plan_id,str) and bool(dynamic_plan_id.strip()), 'Dynamic plan remains an external qualification dependency')
        if source_rate_hz is not None:
            require(branch=='B03' and self.mode=='analog' and ((grid==(16,16) and source_rate_hz==10) or (grid==(32,32) and source_rate_hz==2.5)), 'Source video rate cannot be reassigned to another branch/grid')
        self.lease='acquisition:'+branch; self.energy_safe=False
        self.history.append(('test_acquisition_reservation',branch,self.epoch))

    def release(self, receipt, *, failed=False, failure_id=None):
        self._held(); require(type(receipt) is TestReceipt, 'Typed test receipt required'); receipt.validate()
        require(self.lease is not None and receipt.epoch==self.epoch, 'Matching active lease and epoch required')
        require(receipt.mode==self.mode and receipt.carrier_id==self.carrier, 'Release detector/carrier identity mismatch')
        require(type(failed) is bool, 'Failure status must be Boolean')
        if failed:
            require(isinstance(failure_id,str) and bool(failure_id.strip()), 'Failure identity required')
            self.failed_records.append({'id':failure_id,'lease':self.lease,'epoch':self.epoch,'carrier':self.carrier})
        self.history.append(('test_release',self.lease,failed)); self.lease=None

    def quarantine(self, carrier_id):
        self._held(); require(carrier_id in {'CU-E','CU-C','CU-N','CU-U','SI-STAR','BLANK','REFERENCE'}, 'Unknown carrier')
        require(self.lease is None, 'Cannot alter custody while leased')
        self.quarantined.add(carrier_id); self.history.append(('quarantine_hold',carrier_id))

    def physical_action(self, *args, **kwargs):
        raise GuardHold('Physical actions, open-beam alignment, live acquisition and device I/O are not implemented')

    def outcome(self):
        return {'physical_execution_enabled':False,'scientific_success':False,'raw_measurements_acquired':False,'converted_paper_credit':0,'status':'static_semantic_example_only','failed_records':list(self.failed_records)}
