"""Select the continuous reachable cover branch; revise free-arm endpoints."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

candidate=HERE/'previews/lid_contact_blend_rejected_02.json'
data=json.loads(candidate.read_text())
inputs=json.loads((HERE/'previews/manipulation_approach_inputs.json').read_text())['frames']
paths={};updates={}
for name,record in data['paths'].items():
    branch='forward' if name.startswith('open_') else 'backward'
    knots=record[branch];errors=record[branch+'_errors']
    maximum_position=max(e['error'] for e in errors);maximum_rotation=max(e['rotationError'] for e in errors)
    maximum_step=max(abs(a['q'][n]-b['q'][n]) for a,b in zip(knots,knots[1:]) for n in a['q'])
    assert maximum_position<.0003 and maximum_rotation<.004 and maximum_step<.15,(name,maximum_position,maximum_rotation,maximum_step)
    paths[name]=dict(knots=knots,selected_continuation=branch,maximum_position_error_m=maximum_position,
                     maximum_orientation_error_rad=maximum_rotation,maximum_joint_step_rad=maximum_step)
    for suffix,knot in [('entry',knots[0]),('exit',knots[-1])]:
        key=name+'_'+suffix;target=inputs[key]['target']['joints']
        if any(abs(value-target.get(joint,0))>1e-8 for joint,value in knot['q'].items()):updates[key]=knot['q']
out=dict(scope='Reachable continuous cover IK seeds only; revised free-arm endpoints and independent whole-scene checks remain required',
         source_sha256=data['source_sha256'],candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),
         generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),selected_continuous=True,
         paths=paths,endpoint_updates=updates)
(HERE/'lid_contact_paths.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(paths=list(paths),endpoint_updates=list(updates))),flush=True)
