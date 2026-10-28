"""Refresh static review evidence without rebuilding a running physics input.

This updates author review pins and reruns static/symbolic checks. It never
grants whole-paper, equipment, hardware or independent-review acceptance.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from episode_inputs import load
from validate import validate

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REVISION='2026-10-19.selected-inputs.1'


def refresh():
    packet=load()
    package=json.loads((HERE/'package.json').read_text())
    package['reconstruction_revision']=REVISION
    package['scope']['core_deliverable']='Paper-derived robot manipulation tasks with explicit physical actions, state observations and causal instrument context'
    package['supporting_artifacts'].update(selected_simulation_inputs='selected_reconstruction.json',
        selected_input_loader='episode_inputs.py',selected_solar_geometry='selected_solar_path.json')
    package['scope']['excluded_or_incomplete_work']=['Missing per-occurrence physical bindings and remaining manipulation assets',
        'Complete branch execution and equipment fidelity remain unaccepted',
        'Scientific result agreement is outside manipulation acceptance']
    (HERE/'package.json').write_text(json.dumps(package,indent=2)+'\n')
    review=json.loads((HERE/'review.json').read_text())
    review.update(date='2026-10-19',reconstruction_revision=REVISION,
        scope='Author static manipulation review including explicit selected inputs; bounded simulation records remain separate from complete branch acceptance',
        accepted_as_gold_standard=False,accepted_as_manipulation_template=False,scale_to_1000_authorized_by_this_review=False)
    messages={
        'PTR-02':'109 explicit input fields across 14 cards select geometry, fixtures, channels and operating context. Remaining wire, optical, fabrication and carrier interfaces still need complete physical implementations.',
        'PTR-04':'Every manipulation definition retains its contact/tool/support/observation/recovery contract. Selected missing values are concrete and labeled as inferences; most occurrence bindings remain unimplemented.',
        'PTR-07':'Actor projection excludes reference manipulation artifacts. Bounded workcells have independent trace observations; full-campaign observation and recovery execution remain incomplete.',
        'PTR-08':'Keithley 2000 and 2425, Omega P-M RTD and KHR-2/2-P reconstructions have manufacturer sources and geometry checks. Other equipment and complete interface fidelity remain unaccepted.'}
    for gate in review['gates']:
        if gate['id'] in messages:gate['status']='changes_required';gate['remaining']=messages[gate['id']]
        if gate['id'] in {'PTR-02','PTR-04','PTR-06'}:
            gate['evidence']=list(dict.fromkeys(gate['evidence']+['selected_reconstruction.json','episode_inputs.py','selected_solar_path.json']))
    names=list(review['reviewed_inputs_sha256'])+['selected_reconstruction.json','episode_inputs.py','selected_solar_path.json','agent_visible.json']
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    review['reviewed_inputs_sha256']={name:sha(HERE/name) for name in dict.fromkeys(names)}
    (HERE/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    counts=validate();runs=[]
    for args,log in [([sys.executable,'-m','unittest','discover','-s',str(HERE/'tests'),'-v'],'pilot-tests.txt'),
                     ([sys.executable,'-B',str(ROOT/'scripts/verify_release.py')],'release-regression.txt')]:
        result=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (HERE/'verification'/log).write_text(result.stdout)
        if result.returncode:raise RuntimeError('Static regression failed; see verification/'+log)
        runs.append(dict(command=args,result='passed',log='verification/'+log))
    old=json.loads((HERE/'VERIFICATION.json').read_text())
    old.update(date_utc=datetime.now(timezone.utc).isoformat(),counts=counts,reconstruction_revision=REVISION,
        selected_inputs=dict(cards=len(packet['selected_parameter_cards']),fields=sum(map(len,packet['selected_parameter_cards'].values())),
                             solar_commands=packet['selected_solar_path']['command_count'],hardware_qualified=False),
        physical_execution_validated=False,equipment_fidelity_accepted=False,independent_review=False,
        checks=[dict(command='validate.py',result='passed',scope='Static package, symbolic plan, authored geometry and reviewed-input pins'),
                dict(command='episode_inputs.load',result='passed',scope='Selected values, provenance and solar-input consistency'),*runs])
    old['limitations']=['This report validates the authored package and selected inputs, not complete physical branches',
        'Legacy interface geometry counts remain distinct from newer bounded commercial-device reconstructions',
        'Full object lineage, station handoffs and all manipulation occurrence observations remain incomplete']
    (HERE/'VERIFICATION.json').write_text(json.dumps(old,indent=2)+'\n')
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p!=HERE/'MANIFEST.sha256']
    (HERE/'MANIFEST.sha256').write_text(''.join(sha(p)+'  '+str(p.relative_to(HERE))+'\n' for p in sorted(paths)))
    print(json.dumps(dict(static_checks='passed',selected_inputs=old['selected_inputs'],whole_paper_validated=False),indent=2))


if __name__=='__main__':refresh()
