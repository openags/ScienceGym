"""Check default walking commands against a retained full sensor recording.

This regression does not execute physics or qualify loaded walking.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from quasistatic_walking import QuasistaticWalker


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('recording');p.add_argument('output');a=p.parse_args()
    run,out=map(lambda x:Path(x).resolve(),[a.recording,a.output]);out.mkdir(parents=True,exist_ok=False)
    contract=json.loads((run/'contract.json').read_text())
    paths=[Path(k) for k in contract['source_hashes'] if k.endswith('controller_model/world.xml')]
    assert len(paths)==1 and sha(paths[0])==contract['source_hashes'][str(paths[0])]
    model=mujoco.MjModel.from_xml_path(str(paths[0]));data=mujoco.MjData(model)
    actor=QuasistaticWalker(model,data,contract['initial_xy_m'],contract['goal_xy_m'])
    sensors=dict(np.load(run/'sensor_observations.npz'));trace=dict(np.load(run/'trace.npz'))
    source=out/'source';source.mkdir()
    for n in ['check_loaded_walking_hooks.py','quasistatic_walking.py','balance.py','conic_balance.py','observations.py']:
        shutil.copyfile(Path(__file__).parent/n,source/n)
    maximum=0.;failure=None;count=0
    for i,t in enumerate(sensors['time_s']):
        obs={k:v[i] for k,v in sensors.items()};obs['depth']=None
        torque,_=actor.torque(obs)
        assert abs(trace['time'][i]-t)<1e-10
        error=float(np.max(abs(torque-trace['ctrl'][i])));maximum=max(maximum,error);count+=1
        if error>1e-10:
            failure='Default walking changed at packet '+str(i);break
    report=dict(scope=__doc__,passed=failure is None and count==len(sensors['time_s']),
        failure=failure,compared_packets=count,expected_packets=len(sensors['time_s']),maximum_torque_error_nm=maximum,
        recording_contract_sha256=sha(run/'contract.json'),recording_sensors_sha256=sha(run/'sensor_observations.npz'),
        recording_trace_sha256=sha(run/'trace.npz'),source_sha256={f.name:sha(f) for f in source.iterdir()},qualified_carry=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed']:raise SystemExit(1)


if __name__=='__main__':main()
