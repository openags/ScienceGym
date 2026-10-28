"""Summarize the two completed physical attempts without changing their reports."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent;BASE = HERE.parents[1];ROOT = BASE.parents[1]


def main():
    output = HERE/'push_attempts_01_02.json'
    if output.exists():raise FileExistsError(output)
    rows = [];deps = [Path(__file__)];traces = []
    for name in ['ftir_slider_01', 'ftir_slider_02']:
        run = BASE/'runs'/name
        result = json.loads((run/'result.json').read_text())
        physical = json.loads((run/'physical_slider_review.json').read_text())
        isolation = json.loads((run/'isolation_verification.json').read_text())
        rows.append(dict(run=name,status=result['status'],failure=result['failure'],
            seconds=result['simulated_seconds'],states=physical['states'],physical_passed=physical['passed'],
            isolation_passed=isolation['passed'],failed_physical_checks=[k for k,v in physical['checks'].items() if not v],
            maximum_slider_travel_m=physical['maximum_slider_travel_m'],final_slider_travel_m=physical['final_slider_travel_m'],
            pad_driven_displacement_m=physical['pad_driven_displacement_m'],pad_contact_time_s=physical['pad_contact_time_s'],
            maximum_replay_position_error=physical['maximum_replay_position_error'],
            maximum_replay_velocity_error=physical['maximum_replay_velocity_error'],
            minimum_sole_normal_load_n=physical['minimum_sole_normal_load_n'],
            maximum_body_tilt_rad=physical['maximum_body_tilt_rad']))
        deps += [run/p for p in ['result.json','physical_slider_review.json','isolation_verification.json',
                                'trace.npz','source_snapshot/ftir_slider_actor.py','source_snapshot/balance.py']]
        traces.append(dict(np.load(run/'trace.npz')))
    count = int(np.searchsorted(traces[0]['time'],44.94))
    prefix = {key:bool(np.array_equal(traces[0][key][:count],traces[1][key][:count]))
              for key in ['time','qpos','qvel','ctrl']}
    report = dict(attempts=rows,physical_passes=sum(r['physical_passed'] for r in rows),
        qualified_skills=0,qualified_paper_branches=0,
        identical_precontact_prefix=dict(states=count,through_time_s=float(traces[0]['time'][count-1]),checks=prefix),
        comparison='Attempt 02 models the preload at the fingertip instead of the wrist; the common precontact execution remains identical. Both physical attempts fail.',
        next_hypothesis='A separate attempt 03 projects preload perpendicular to the free slider axis; it is not included in these completed results.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        scope='Two nominal development attempts from authored standing setup, with complete failures retained. No walking, full-cover opening, sample exchange or reliability qualification.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows),flush=True)


if __name__ == '__main__':main()
