"""Read-only structural and final-export verifier."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contract import ALL_BRANCHES, load_contract, digest
from exporter import inspect

def main():
    checks=0
    def check(ok,message):
        nonlocal checks
        if not ok:raise AssertionError(message)
        checks+=1
    ops,core=load_contract(ROOT)
    read=lambda n:json.loads((ROOT/n).read_text())
    check([b['id'] for b in read('branches.json')['branches']]==list(ALL_BRANCHES),'branch inventory')
    check([s['id'] for s in read('station_contracts.json')['stations']]==[f'ST{i:02}' for i in range(1,8)],'station inventory')
    check([u['id'] for u in read('unknown_inputs.json')['unknowns']]==[f'U{i:02}' for i in range(1,17)],'unknown inventory')
    check(all(u['status']=='unresolved' for u in read('unknown_inputs.json')['unknowns']),'physical qualifications changed')
    b=read('shared_binding_contract.json')
    check([a['asset_id'] for a in b['assets']]==[f'A{i:02}' for i in range(1,10)],'asset inventory')
    anchors=[a for root in b['assets'] for a in root['anchors']]
    check(len(anchors)==33 and len({a['anchor_id'] for a in anchors})==33,'anchor inventory')
    check(all(a['mode']=='evidence_only' and a['physical_actuation_enabled'] is False for a in anchors),'anchor authority')
    seen=set()
    for op in ops:
        check(set(op['depends_on'])<=seen,'DAG order')
        check(op['anchor_ids']==next(x for x in b['route_bindings'] if x['route_id']==op['id'])['target_anchor_ids'],'anchor binding')
        seen.add(op['id'])
    release=read('RELEASE_BOUNDARY.json')
    for key in ['physical_execution','physical_simulation','scientific_reproduction','source_reanalysis','source_files_exported','hardware_safety_qualified','exact_geometry_validated','github_writes']:
        check(release[key] is False,key)
    check(read('evaluator_reference.json')['source_outcomes_in_reward'] is False,'outcome leakage')
    if (ROOT/'task_core_manifest.json').exists():
        m=read('task_core_manifest.json');check(digest(m['files'])==m['core_sha256'],'task core digest')
        for item in m['files']:
            data=(ROOT/item['path']).read_bytes();check(len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],'task core file drift')
    if (ROOT/'asset_binding_plan.json').exists():
        a=read('asset_binding_plan.json');check(a['semantic_core_sha256']==core,'binding semantic digest')
        m=read('paired_scene_core_manifest.json');check(a['scene_core_sha256']==m['core_sha256'],'scene reference digest')
    if (ROOT/'DELIVERABLE_MANIFEST.json').exists():inspect(ROOT);checks+=1
    print(json.dumps({'structural_checks_passed':checks,'physical_execution':False,'scientific_reproduction':False}))
if __name__=='__main__':main()
