"""Whole-paper admission gate. Never substitute primitive tests for a campaign."""
import argparse
import hashlib
import json
from pathlib import Path
from world import HERE

TASK=HERE.parents[1]/'tasks/directional_cooling_operations_v3'
RELATED={
    'BASE.02':'assembly','BASE.03':'assembly','EMITTER.02':'assembly',
    'CAL_MOUNT.06':'probe','CAL_UNLOAD.02':'probe',
    'LID_BASELINE.01':'lid','LID_REMOVE.02':'lid','LID_REMOVE.03':'lid',
    'OPT_REFERENCE.03':'door','OPT_MOUNT.02':'door','OPT_MOUNT.07':'door',
    'OPT_UNLOAD.02':'door','OPT_UNLOAD.06':'door',
}


def audit():
    ops=json.loads((TASK/'operations.json').read_text())['operations']
    plan=json.loads((TASK/'reference_plan.json').read_text())
    interfaces={x['id']:x for x in json.loads((TASK/'interaction_contracts.json').read_text())['interfaces']}
    definitions={}
    for operation in ops:
        for step in operation['reference_steps']:
            if step['capability']!='manipulation':continue
            iface=interfaces[step['interaction']['interface_id']]
            definitions[step['id']]=dict(id=step['id'],operation=operation['id'],action=step['action'],
                interface=iface['id'],related_contact_fixture=RELATED.get(step['id']),
                executable_binding=None,validated_in_campaign=False,
                missing=['Concrete per-occurrence objects, tools, transforms and bounded action implementation',
                         'Complete step-specific observation predicates and dependency-state integration',
                         iface['remaining']])
    branches=[]
    for branch in json.loads((TASK/'branches.json').read_text())['branches']:
        occurrences=[o for o in plan['occurrences'] if o['branch_id']==branch['id']]
        manual=[sid for o in occurrences for sid in o['required_step_ids'] if sid in definitions]
        branches.append(dict(id=branch['id'],planned_occurrences=len(occurrences),
                             manipulation_occurrences=len(manual),validated_occurrences=0,
                             status='blocked',step_ids=list(dict.fromkeys(manual))))
    report=dict(status='blocked',whole_paper_validated=False,
        interpretation='Contact fixtures establish bounded capabilities only. No paper step is credited as fully executed.',
        required_manipulation_definitions=len(definitions),qualified_manipulation_definitions=0,
        required_branches=len(branches),validated_branches=0,
        inputs_sha256={n:hashlib.sha256((TASK/n).read_bytes()).hexdigest() for n in ['operations.json','reference_plan.json','interaction_contracts.json']},
        branches=branches,steps=list(definitions.values()))
    (HERE/'campaign_coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=audit()
    print(json.dumps({k:v for k,v in result.items() if k not in ['steps','branches','inputs_sha256']},indent=2))
    if args.check and result['status']!='passed':raise SystemExit(2)
