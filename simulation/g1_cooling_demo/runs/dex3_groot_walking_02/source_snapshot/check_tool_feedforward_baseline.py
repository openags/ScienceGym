"""Check that opt-in approach feedforward preserves a recorded pickup policy.

This is a host-side regression diagnostic, not isolated execution, a fresh
physics run, a visual-approach result, or repeated skill qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import shutil

import mujoco
import numpy as np

from dex3_tool_actor import ToolActor
from verify_tool_grasp import difference


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output');a=p.parse_args()
    run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    result=json.loads((run/'result.json').read_text())
    for name,key in [('sensors.npz','sensors_sha256'),('responses.pkl','responses_sha256')]:
        assert sha(run/name)==result[key]
    prior=json.loads((run/'policy_source/tool_prior.json').read_text())
    assert not prior.get('approach_velocity_feedforward',False)
    model=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));actor=ToolActor(model,prior)
    snapshot=out/'source';snapshot.mkdir()
    for name in ['check_tool_feedforward_baseline.py','dex3_tool_actor.py','balance.py','conic_balance.py','observations.py','verify_tool_grasp.py']:
        shutil.copyfile(Path(__file__).parent/name,snapshot/name)
    sensors=dict(np.load(run/'sensors.npz'));responses=pickle.loads((run/'responses.pkl').read_bytes())
    maximum=0.;failure=None;compared=0
    for i,expected in enumerate(responses):
        response=actor.update({k:v[i] for k,v in sensors.items()})
        error=difference(expected,{k:v for k,v in response.items() if k!='events'})
        maximum=max(maximum,error);compared+=1
        if error>1e-10:
            failure='Default policy changed at packet '+str(i);break
    if failure is None:
        maximum=max(maximum,difference(json.loads((run/'events.json').read_text()),response['events']))
    report=dict(scope=__doc__,passed=failure is None and maximum<=1e-10 and compared==len(responses),
                failure=failure,compared_packets=compared,expected_packets=len(responses),
                maximum_response_error=maximum if np.isfinite(maximum) else None,
                recording=str(run),recorded_result_sha256=sha(run/'result.json'),
                source_sha256={f.name:sha(f) for f in snapshot.iterdir()},
                approach_or_physics_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
