"""Regress the pose-only contact-acquisition bypass found in physical run 05."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]
sys.path.insert(0, str(BASE))
from ftir_slider_actor import motion_ready


def main():
    output = HERE/'contact_acquisition_regression.json'
    if output.exists():
        raise FileExistsError(output)
    checks = {}
    rows = []
    deps = [Path(__file__), BASE/'ftir_slider_actor.py']
    for run in ['04', '05']:
        path = BASE/f'runs/ftir_slider_{run}/actor_monitor.jsonl'
        retained = [json.loads(line) for line in path.read_text().splitlines()]
        seek = [r for r in retained if r['policy_state'] == 'seek_contact']
        # Conservative reconstruction from the retained 10 Hz monitor. The
        # runtime updates at 100 Hz; these samples do not replace replay.
        last = seek[-1]
        above = [r for r in seek if r['time_s'] >= last['time_s']-.20001]
        confirmed = len(above) >= 3 and all(r['touch']['filtered_distal_index_n'] > .2 for r in above)
        # A perfect commanded pose is the adversarial case: it previously
        # bypassed missing touch once the bounded search time elapsed.
        ready = motion_ready('seek', 1., 0., 0., confirmed)
        expected = run == '04'
        checks[f'retained_{run}_acquisition'] = ready == expected
        rows.append(dict(run=run, last_sensor_time_s=last['time_s'],
                         last_filtered_load_n=last['touch']['filtered_distal_index_n'],
                         recent_sensor_confirmed=confirmed,
                         ready_at_perfect_commanded_pose=ready, expected_ready=expected))
        deps.append(path)
    checks['expired_pose_only_search_rejected'] = not motion_ready('seek', 1., 0., 0., False)
    checks['lost_contact_rejected'] = not motion_ready('seek', .9, 0., 0., False)
    checks['confirmed_touch_before_deadline'] = motion_ready('seek', .9, .001, .001, True)
    checks['free_space_still_requires_pose'] = not motion_ready('pose', 1., .006, 0., False)
    checks['free_space_reached_pose'] = motion_ready('pose', 1., .001, .001, False)
    report = dict(passed=all(checks.values()), checks=checks, retained_cases=rows,
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope='Regression of the phase-entry predicate using retained tactile observations and adversarial pose convergence. Full execution with the revised guard is still required.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
