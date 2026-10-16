"""Fail closed on broken references, missing roles and invalid symbolic plans."""
import json
import hashlib
import math
import struct
import jsonschema
from pathlib import Path
import planner
from validate_manipulation import validate_contract

HERE=Path(__file__).resolve().parent
ASSET=HERE.parents[1]/'assets/cooling_scene_assets_v2'
def check(ok,message):
    if not ok:raise ValueError(message)

def validate():
    package=planner.read('package');roles=package['artifact_roles']
    required={'narrative','source_inventory','coverage','resources','initial_state','operations','dependencies','branches_and_loops','reconstruction_inferences','lineage','controls_and_repeats','recovery','episode_inputs','asset_bindings','actor_projection','evaluator','unknown_inputs','verification'}
    check({r['role'] for r in roles}==required and len(roles)==18,'incomplete or duplicate artifact roles')
    for r in roles:
        check((HERE/r['path']).is_file(),'missing role file '+r['path'])
    for path in package.get('supporting_artifacts',{}).values():
        check((HERE/path).is_file(),'missing supporting artifact '+path)
    jsonschema.Draft202012Validator(planner.read('operations.schema')).validate(planner.read('operations'))
    ops=planner.read('operations')['operations'];byid={o['id']:o for o in ops}
    check(len(byid)==len(ops),'duplicate operation id')
    evidence=planner.read('provenance')['evidence'];unknown={u['id'] for u in planner.read('unknown_parameters')['unknowns']}
    inferences={i['id'] for i in planner.read('reconstruction_inferences')['inferences']}
    station_ids={s['id'] for s in planner.read('station_contracts')['stations']}
    stepids=set()
    for o in ops:
        check(o['location_id'] in station_ids,'unknown station '+o['id'])
        check(bool(o['preconditions']) and bool(o['postconditions']),'empty state predicates '+o['id'])
        check(bool(o['manipulated_objects']) and bool(o['tools_or_interfaces']),'missing resources '+o['id'])
        check(set(o['evidence_ids'])<=set(evidence),'unknown evidence '+o['id'])
        check(set(o['unknown_parameter_ids'])<=unknown,'unknown operating-input group')
        for s in o['reference_steps']:
            check(s['id'] not in stepids,'duplicate step id '+s['id']);stepids.add(s['id'])
            check(bool(s['action']) and bool(s['completion_observation']),'missing action observation')
            if s['basis']=='reconstruction_inference':check(s['inference_id'] in inferences,'untraced inference')
            else:check(s['source_id'] in planner.read('provenance')['source_ids'],'untraced external supplement')
        check(set(o['depends_on'])<=set(byid),'dangling dependency')
        for loop in o.get('iteration_contracts',[]):
            step_order=[s['id'] for s in o['reference_steps']]
            body=loop['body_step_ids']
            check(body and len(body)==len(set(body)) and set(body)<=set(step_order),'invalid iteration body')
            check([step_order.index(s) for s in body]==sorted(step_order.index(s) for s in body),'unordered iteration body')
    visiting=set();visited=set()
    def visit(i):
        check(i not in visiting,'cyclic operation dependency '+i)
        if i in visited:return
        visiting.add(i)
        for p in byid[i]['depends_on']:visit(p)
        visiting.remove(i);visited.add(i)
    for i in byid:visit(i)
    edges=planner.read('dependencies')['edges']
    check({(x['from'],x['to']) for x in edges}=={(p,o['id']) for o in ops for p in o['depends_on']},'stale dependency artifact')
    branches=planner.read('branches')['branches'];branchids={b['id'] for b in branches}
    check(len(branches)==11 and len(branchids)==11,'branch denominator changed without review')
    for b in branches:check(set(b['operation_ids'])<=set(byid),'dangling branch operation')
    covered=set()
    for item in planner.read('coverage_matrix')['items']:
        check(item['evidence_id'] in evidence,'missing coverage source')
        check(set(item['branch_ids'])<=branchids,'unknown coverage branch');covered.update(item['branch_ids'])
    check(covered==branchids,'physical branch not covered by source inventory')
    counts=planner.read('coverage_matrix')['denominators']
    check(counts['operation_definitions']==len(ops) and counts['reference_substeps']==len(stepids),'stale counts')
    check(not package['scope']['whole_paper_execution_validated'],'unearned execution claim')
    p=planner.read('reference_plan');result=planner.verify_plan(p)
    for e in p['occurrences']:
        check(e['operation_id'] in byid,'unknown planned operation')
        check(set(e['required_step_ids'])=={s['id'] for s in byid[e['operation_id']]['reference_steps']},'missing occurrence step obligations')
    parts=json.loads((ASSET/'parts.json').read_text())['parts'];partids={p['id'] for p in parts}
    manipulation=validate_contract(ops,planner.read('interaction_contracts'),planner.read('asset_bindings'),
        planner.read('daq_terminal_contract'),planner.read('sensor_installation'),parts,planner.read('manipulation_coverage'))
    check(len(parts)==len(partids),'duplicate geometry part id')
    check(all(all(math.isfinite(v) for v in p['bounds_m']+p['local_position_m']) for p in parts),'nonfinite geometry')
    glb=(ASSET/'geometry/cooling_pilot.glb').read_bytes();magic,version,length=struct.unpack('<4sII',glb[:12])
    check(magic==b'glTF' and version==2 and length==len(glb),'invalid glTF container')
    n,t=struct.unpack('<II',glb[12:20]);g=json.loads(glb[20:20+n]);nodes={x.get('name') for x in g['nodes']}
    binary_start=28+n;binary=glb[binary_start:]
    components={5120:(1,'b'),5121:(1,'B'),5122:(2,'h'),5123:(2,'H'),5125:(4,'I'),5126:(4,'f')}
    arities={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}
    for v in g['bufferViews']:
        check(v.get('buffer',0)==0 and v.get('byteOffset',0)+v['byteLength']<=len(binary),'buffer view outside binary')
    for a in g['accessors']:
        v=g['bufferViews'][a['bufferView']];size,fmt=components[a['componentType']]
        width=size*arities[a['type']];stride=v.get('byteStride',width)
        check(a.get('byteOffset',0)+max(0,a['count']-1)*stride+width<=v['byteLength'],'accessor exceeds view')
        if a['componentType']==5126:
            start=v.get('byteOffset',0)+a.get('byteOffset',0)
            check(all(math.isfinite(x) for i in range(a['count']) for x in struct.unpack_from('<'+fmt*arities[a['type']],binary,start+i*stride)),'nonfinite exported attribute')
    for mesh in g['meshes']:
        for primitive in mesh['primitives']:
            positions=g['accessors'][primitive['attributes']['POSITION']]
            if 'indices' in primitive:
                a=g['accessors'][primitive['indices']];v=g['bufferViews'][a['bufferView']];size,fmt=components[a['componentType']]
                start=v.get('byteOffset',0)+a.get('byteOffset',0)
                check(a['type']=='SCALAR' and a['componentType'] in (5121,5123,5125),'invalid index accessor')
                check(max(struct.unpack_from('<'+fmt*a['count'],binary,start),default=0)<positions['count'],'mesh index outside positions')
    roots={p['root'] for p in parts};check(roots<=nodes,'missing exported root')
    exported_meshes={x.get('name') for x in g['nodes'] if 'mesh' in x}
    check(partids<=exported_meshes,'export dropped authored geometry (including wires/labels): '+str(sorted(partids-exported_meshes)[:5]))
    bypart={p['id']:p for p in parts}
    ray_receipt=json.loads((ASSET/'geometry/interaction_checks.json').read_text())
    check(ray_receipt['native_sha256']==hashlib.sha256((ASSET/'geometry/cooling_pilot.blend').read_bytes()).hexdigest(),'geometry ray check belongs to another scene')
    check(ray_receipt['passed'] and ray_receipt['usb_shell_open'],'failed authored cavity checks')
    check(len(ray_receipt['terminal_checks'])==52 and all(c['wire_entry_axis_open'] and c['driver_slot_recess_m']>0 for c in ray_receipt['terminal_checks']),'incomplete authored terminal cavity checks')
    for ident,expected in {
        'COOLER_WHITE__emitter_copper':[.05,.05,.0005],
        'COOLER_WHITE__film_spacer':[.127,.127,.0064],
        'COOLER_WHITE__radiation_shield':[.152,.152,.057],
        'KEITHLEY_2425__chassis':[.213,.370,.089],
        'MCC_USB_TC__case':[.12852,.08839,.03556],
        'COOLER_FIXED_BAND__cover_lower':[.127,.127,.000050],
        'COOLER_FIXED_BAND__cover_upper':[.127,.127,.000050],
    }.items():check(all(abs(a-b)<1e-5 for a,b in zip(bypart[ident]['bounds_m'],expected)),'source dimension mismatch '+ident)
    # 10 micrometres accommodates beveled polygon bounds; not a manufacturing tolerance.
    for b in planner.read('asset_bindings')['bindings']:
        for part in b['part_selection']:
            check(part in partids,'dangling or ambiguous part binding '+part)
    review=planner.read('review');check(len(review['gates'])==8,'missing review gate')
    check({g['id'] for g in review['gates']}=={'PTR-%02d'%i for i in range(1,9)},'duplicate review gate')
    check(all(g['status'] in {'not_reviewed','pass','changes_required','not_applicable'} for g in review['gates']),'nonstandard review status')
    check(not review['accepted_as_gold_standard'],'open gates cannot certify gold standard')
    for path,expected in review['reviewed_inputs_sha256'].items():
        check(hashlib.sha256((HERE/path).read_bytes()).hexdigest()==expected,'review input changed: '+path)
    return {'package_roles':len(roles),'operations':len(ops),'reference_steps':len(stepids),'branches':len(branches),
            'planned_occurrences':result['planned_occurrences'],'asset_parts':len(parts),'export_roots':len(roots),
            'physical_successes':0,'equipment_fidelity_accepted':False,**manipulation}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
