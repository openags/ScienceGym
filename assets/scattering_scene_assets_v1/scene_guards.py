"""Pure-data visualization guards. No hardware imports, endpoints or actuation methods."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
CONTRACT=json.loads((ROOT/'asset_binding_contract.json').read_text())
OPERATIONS={x['operation_id']:set(x['anchor_ids']) for x in CONTRACT['operation_bindings']}
FAMILIES={'M1':'GROOVE_M1','M2':'GROOVE_M2','M3':'GROOVE_M3'}
SAFETY=('acoustic_off','beam_safe','motion_safe','support_safe')

def evaluate(request):
    """Return a static review result; never emit physical commands or qualify receipts."""
    base={'physical_execution_enabled':False,'hardware_commands':[], 'scientific_physics_implemented':False}
    def hold(reason):return dict(base,status='HOLD_QUALIFICATION',reason=reason,visual_change=False)
    if not isinstance(request,dict):return hold('MALFORMED_REQUEST')
    allowed_fields={'physical_execution_enabled','operation_id','anchor_id','action','evidence_kind','claims_real_observation','branch_id','science_type','coordinate_mapping_status','family_id','supported','custody_holder','occupancy','retained_lease','configuration_epoch','calibration_configuration_epoch','observed_safe_fixture','command_ack_only','auto_retry','force_newtons','pressure_field'}
    if set(request)-allowed_fields:return hold('UNSUPPORTED_REQUEST_FIELD')
    if request.get('physical_execution_enabled') is not False:return hold('PHYSICAL_EXECUTION_FORBIDDEN')
    op,anchor=request.get('operation_id'),request.get('anchor_id')
    if not isinstance(op,str) or op not in OPERATIONS:return hold('UNKNOWN_OPERATION')
    if not isinstance(anchor,str) or anchor not in OPERATIONS[op]:return hold('UNBOUND_OPERATION_ANCHOR')
    action=request.get('action')
    if action=='inspect_anchor':return dict(base,status='STATIC_REVIEW_ONLY',visual_change=False,anchor_id=anchor)
    if action!='set_synthetic_visual_state':return hold('ACTION_NOT_STATIC_VISUALIZATION')
    if request.get('evidence_kind')!='synthetic_fixture':return hold('VISUAL_EVIDENCE_MUST_BE_SYNTHETIC')
    if request.get('claims_real_observation') is not False:return hold('SYNTHETIC_IS_NOT_OBSERVED_EVIDENCE')
    branch=request.get('branch_id')
    branch_types={**{f'P{i:02}':'preparation_source_review' for i in range(1,4)},**{f'B{i:02}':'experimental_source_review' for i in range(1,6)},**{f'A{i:02}':'numerical_source_review' for i in range(1,5)}}
    if not isinstance(branch,str) or branch not in branch_types:return hold('UNKNOWN_OR_MISSING_BRANCH')
    if request.get('science_type')!=branch_types[branch]:return hold('SCIENCE_BRANCH_TYPE_MISMATCH')
    experimental={f'B{i:02}' for i in range(1,6)};numerical={f'A{i:02}' for i in range(1,5)}
    route_branches={'R01':experimental|{'P01','P02','P03'},'R02':experimental,'R03':experimental|{'P01'},'R04':experimental|{'P02'},'R05':experimental|{'P03'},'R06':experimental|{'P03'},'R07':experimental,'R08':experimental,'R09':experimental,'R10':experimental,'R11':numerical,'R12':experimental|{'P03'},'R13':experimental|{'P01'},'R14':set(branch_types)}
    if branch not in route_branches[op]:return hold('BRANCH_ROUTE_MISMATCH')
    if branch in numerical and not anchor.startswith('AS11.'):return hold('NUMERICAL_REVIEW_CANNOT_HANDLE_SPECIMENS')
    for field in ('custody_holder','retained_lease','configuration_epoch','calibration_configuration_epoch'):
        if not isinstance(request.get(field),str) or not request[field].strip():return hold('MISSING_OR_MALFORMED_'+field.upper())
    if request.get('coordinate_mapping_status')!='explicit_synthetic_test_mapping':return hold('COORDINATE_MAPPING_UNQUALIFIED')
    if anchor.startswith(('AS02.','AS03.')):
        design=anchor.split('.')[1]
        if request.get('family_id')!=FAMILIES[design]:return hold('DESIGN_FAMILY_MISMATCH')
        required_design={'B01':'M1','B02':'M1','B03':'M1','B04':'M2','B05':'M3'}.get(branch)
        if required_design and design!=required_design:return hold('BRANCH_DESIGN_MISMATCH')
    if request.get('supported') is not True:return hold('UNSUPPORTED_OBJECT')
    if request.get('custody_holder') is None or request.get('occupancy')!='known_synthetic':return hold('UNKNOWN_CUSTODY_OR_OCCUPANCY')
    if not request.get('retained_lease'):return hold('MISSING_RETAINED_LEASE')
    if not request.get('configuration_epoch') or request.get('configuration_epoch')!=request.get('calibration_configuration_epoch'):return hold('STALE_CALIBRATION_EPOCH')
    observed=request.get('observed_safe_fixture',{})
    if not isinstance(observed,dict) or not all(observed.get(k) is True for k in SAFETY):return hold('INDEPENDENT_SAFE_STATE_MISSING')
    if request.get('command_ack_only'):return hold('COMMAND_ACK_IS_NOT_SAFE_STATE')
    if request.get('auto_retry'):return hold('BLIND_RETRY_FORBIDDEN')
    if request.get('force_newtons') is not None or request.get('pressure_field') is not None:return hold('UNIMPLEMENTED_SCIENTIFIC_QUANTITY')
    return dict(base,status='SYNTHETIC_VISUAL_STATE_ONLY',visual_change=True,anchor_id=anchor,retained_lease=request['retained_lease'],qualification='NO_REAL_QUALIFICATION_CONFERRED')
