"""Bind paper step instances to existing physical objects in a live world.

These bindings do not initialize, reset, clone or teleport the execution world.
Preparation and earlier operations remain explicit campaign obligations.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np
from control import ExecutionFailure
from world import HERE

TASK=HERE.parents[1]/'tasks/directional_cooling_operations_v3'
BINDINGS={
    'BASE.03':dict(body='foam_upper',required=['foam_lower'],method='rigid_transfer'),
    'EMITTER.02':dict(body='emitter',required=['foam_lower','foam_upper'],method='rigid_transfer'),
    'EMITTER.03':dict(body='pe_tube',required=['foam_lower','foam_upper','emitter'],method='rigid_transfer'),
    'SHIELD.02':dict(body='cover',required=['foam_lower','foam_upper','emitter','pe_tube'],method='cover_transfer'),
    'SHIELD.03':dict(body='shield',required=['foam_lower','foam_upper','emitter','pe_tube','cover'],method='rigid_transfer'),
    'SHIELD.04':dict(body='aperture',required=['foam_lower','foam_upper','emitter','pe_tube','cover','shield'],method='rigid_transfer'),
}


@dataclass
class SceneBinding:
    robot: object
    targets: dict
    instance_id: str
    payload_id: str='white'
    station_id: str='WS_ASSEMBLY'
    previous_receipt_sha256: str|None=None


def state_sha(robot):
    digest=hashlib.sha256()
    for value in [robot.data.qpos,robot.data.qvel,robot.data.ctrl,np.array([robot.data.time])]:digest.update(np.asarray(value,dtype='<f8').tobytes())
    return digest.hexdigest()


def supported(context,name,where='assembled'):
    p=context.targets[name];support=p['support'] if where=='assembled' else name+'_stand'
    if name=='cover':return context.robot.check_cover(np.array(p[where]),support)
    return context.robot.check_supported(name,p[where],support)


def execute(context,occurrence,step_id):
    if step_id not in BINDINGS:raise ExecutionFailure('No executable paper-step binding: '+step_id)
    if occurrence['operation_id']!=step_id.split('.')[0] or step_id not in occurrence['required_step_ids']:
        raise ExecutionFailure('Step does not belong to this occurrence')
    if occurrence['station_id']!=context.station_id:raise ExecutionFailure('Occurrence requires a different physical station')
    if occurrence['payload_ids']!=[context.payload_id] or context.payload_id!='white':
        raise ExecutionFailure('This scene binds exactly one white apparatus; another identity requires its own physical objects')
    specification=BINDINGS[step_id];name=specification['body'];robot=context.robot
    bodies=[name]+specification['required']
    ids=[robot.model.body(body).id for body in bodies]
    if len(set(ids))!=len(ids):raise ExecutionFailure('Distinct part roles alias the same physical body')
    for required in specification['required']:supported(context,required)
    supported(context,name,'park')
    start_time=float(robot.data.time);start_step=robot.physics_steps;start_event=len(robot.timeline);before=state_sha(robot)
    if specification['method']=='cover_transfer':robot.grip_cover();robot.put_cover(np.array(context.targets[name]['assembled']))
    else:robot.transfer(name,context.targets[name]['assembled'],context.targets[name]['support'])
    for required in specification['required']+[name]:supported(context,required)
    if robot.physics_steps<=start_step:raise ExecutionFailure('Binding produced no physical execution')
    receipt=dict(schema_version='sciencegym.physical_step.v1',status='executed_in_bound_scene',
                 occurrence_id=occurrence['id'],step_id=step_id,branch_id=occurrence['branch_id'],session_id=occurrence['session_id'],
                 scene_instance_id=context.instance_id,payload_id=context.payload_id,station_id=context.station_id,
                 objects=[dict(role=body,body_id=int(i),instance_id=context.instance_id+'::'+body) for body,i in zip(bodies,ids)],
                 time_start_s=start_time,time_end_s=float(robot.data.time),physics_step_start=start_step,physics_step_end=robot.physics_steps,
                 event_start=start_event,event_end=len(robot.timeline),before_state_sha256=before,after_state_sha256=state_sha(robot),
                 previous_receipt_sha256=context.previous_receipt_sha256,
                 source_operations_sha256=hashlib.sha256((TASK/'operations.json').read_bytes()).hexdigest(),
                 binding_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 campaign_qualified=False,
                 qualification_limit='This receipt does not discharge predecessor operations, material qualification or omitted campaign occurrences')
    encoded=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode();receipt['receipt_sha256']=hashlib.sha256(encoded).hexdigest()
    context.previous_receipt_sha256=receipt['receipt_sha256']
    return receipt


def compile_plan():
    operations=json.loads((TASK/'operations.json').read_text())['operations']
    manual={s['id']:s for op in operations for s in op['reference_steps'] if s['capability']=='manipulation'}
    if not set(BINDINGS)<=set(manual):raise ValueError('Runtime registry contains a stale paper step ID')
    plan=json.loads((TASK/'reference_plan.json').read_text());rows=[]
    for occurrence in plan['occurrences']:
        for step in occurrence['required_step_ids']:
            if step not in manual:continue
            binding=BINDINGS.get(step)
            applicable=bool(binding and occurrence['station_id']=='WS_ASSEMBLY' and occurrence['payload_ids']==['white'])
            rows.append(dict(occurrence_id=occurrence['id'],branch_id=occurrence['branch_id'],session_id=occurrence['session_id'],
                             step_id=step,payload_ids=occurrence['payload_ids'],station_id=occurrence['station_id'],
                             binding=dict(module='step_runtime',entrypoint='execute',**binding) if applicable else None,
                             status='bound_not_executed' if applicable else 'unbound',campaign_qualified=False,
                             reason=None if applicable else 'Missing implementation or distinct payload/station objects'))
    report=dict(schema_version='sciencegym.physical_plan.v1',status='incomplete',whole_paper_validated=False,
                implemented_definitions=len(BINDINGS),required_definitions=len(manual),required_occurrences=len(rows),
                bound_occurrences=sum(r['binding'] is not None for r in rows),qualified_campaign_occurrences=0,
                input_sha256={n:hashlib.sha256((TASK/n).read_bytes()).hexdigest() for n in ['operations.json','reference_plan.json']},
                binding_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),occurrences=rows)
    (HERE/'execution_plan.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    result=compile_plan();print(json.dumps({k:v for k,v in result.items() if k not in ['occurrences','input_sha256']},indent=2))
