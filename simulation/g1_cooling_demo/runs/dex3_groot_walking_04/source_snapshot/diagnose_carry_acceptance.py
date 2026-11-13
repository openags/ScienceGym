"""Attribute a failed carrying verdict using retained independent samples.

The full 100 microsecond physics verdict remains authoritative. The retained
one millisecond samples localize a failure; they cannot replace that verdict.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from build_tool_station import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    run=a.run.resolve();out=a.output.resolve()
    result=json.loads((run/'result.json').read_text())
    contract=json.loads((run/'contract.json').read_text())
    review=json.loads((run/'physical_review.json').read_text())
    events=json.loads((run/'events.json').read_text())
    assert sha(run/'contract.json')==result['contract_sha256']
    assert sha(run/'trace.npz')==result['trace_sha256']==review['source_trace_sha256']
    assert sha(run/'source_snapshot/verify_tool_grasp.py')==review['verifier_sha256']
    phases=[e for e in events if 'phase' in e];starts={e['phase']:e['time_s'] for e in phases}
    s=np.load(run/'physical_samples.npz')['samples'];limits=contract['physical_acceptance']
    loaded=(s[:,3]>limits['minimum_each_opposing_finger_load_n'])&(s[:,4]>limits['minimum_thumb_load_n'])&(s[:,6]>limits['minimum_each_opposing_finger_load_n'])
    height=s[:,1]>=limits['minimum_actual_tool_lift_m'];unsupported=s[:,5]<.01
    in_carry=(s[:,0]>=starts.get('carry_preload',starts['carry_raise']))&(s[:,0]<starts['lower'])
    bad=np.flatnonzero(in_carry&~(loaded&height&unsupported))
    groups=np.split(bad,np.flatnonzero(np.diff(bad)>1)+1) if len(bad) else []
    intervals=[]
    for ids in groups:
        t=float(s[ids[0],0]);phase=next(e['phase'] for e in reversed(phases) if e['time_s']<=t)
        intervals.append(dict(start_s=t,last_sample_s=float(s[ids[-1],0]),sample_count=len(ids),phase=phase,
            unloaded_samples=int(np.sum(~loaded[ids])),below_height_samples=int(np.sum(~height[ids])),
            supported_samples=int(np.sum(~unsupported[ids])),minimum_height_m=float(s[ids,1].min()),
            minimum_finger_forces_n=s[ids][:,[3,4,6]].min(0).tolist()))
    window=contract['carry_contract']['minimum_native_loaded_before_lift_s']
    bad_pre=s[(s[:,0]>=starts['lift']-window)&(s[:,0]<starts['lift'])&~loaded]
    trace=np.load(run/'trace.npz');times=trace['time'];q=trace['qpos'];origin=q[0,:2].copy()
    locations=[]
    for label,t in [('initial',0.),('initial_standing',2.),('approach',starts['approach']),
                    ('carry_raise',starts['carry_raise']),('carry_align',starts['carry_align']),
                    ('release',starts['release']),('final',float(times[-1]))]:
        i=int(np.argmin(abs(times-t)));delta=q[i,:2]-origin
        locations.append(dict(label=label,time_s=float(times[i]),base_xy_delta_m=delta.tolist(),distance_m=float(np.linalg.norm(delta))))
    trace.close();del q
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'build_tool_station.py']:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    report=dict(scope=__doc__,failed_checks=[k for k,v in review['checks'].items() if not v],
        carry_predicate_failures_at_one_ms=intervals,prelift_failed_one_ms_samples=bad_pre.tolist(),
        sample_columns=['time_s','height_m','tip_gap_m','index_force_n','thumb_force_n','support_force_n','middle_force_n'],
        base_return_diagnostic=locations,authoritative_carry_metrics=review['carry_metrics'],
        interpretation='Height, native finger contact and initial standing drift are separate obligations. Changing the release alone cannot repair these other failed checks.',
        controller_inputs_modified=False,acceptance_changed=False,
        source_result_sha256=sha(run/'result.json'),source_review_sha256=sha(run/'physical_review.json'),
        source_samples_sha256=sha(run/'physical_samples.npz'),source_trace_sha256=result['trace_sha256'],
        source_sha256={f.name:sha(f) for f in out.glob('*.py')})
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(intervals=intervals,base_locations=locations)),flush=True)


if __name__=='__main__':main()
