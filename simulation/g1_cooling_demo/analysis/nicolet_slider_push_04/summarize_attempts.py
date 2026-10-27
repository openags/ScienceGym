"""Summarize completed slider trials with unchanged physical acceptance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]


def main():
    output = HERE/'push_attempts_01_05.json'
    if output.exists():
        raise FileExistsError(output)
    rows = []
    deps = [Path(__file__)]
    for number in range(1, 6):
        run = BASE/f'runs/ftir_slider_{number:02d}'
        result = json.loads((run/'result.json').read_text())
        physical = json.loads((run/'physical_slider_review.json').read_text())
        isolation = json.loads((run/'isolation_verification.json').read_text())
        events = result['actor_last_output']['events']
        solution = next(e['solution'] for e in events if 'solution' in e)
        rows.append(dict(run=run.name, command_status=result['status'], failure=result['failure'],
                         seconds=result['simulated_seconds'], candidate=solution['candidate']['id'],
                         physical_passed=physical['passed'], isolation_passed=isolation['passed'],
                         failed_checks=[k for k, v in physical['checks'].items() if not v],
                         **{k:physical[k] for k in ['states', 'maximum_slider_travel_m',
                             'final_slider_travel_m', 'pad_driven_displacement_m', 'pad_contact_time_s',
                             'maximum_replay_position_error', 'maximum_replay_velocity_error',
                             'minimum_sole_normal_load_n', 'maximum_body_tilt_rad']}))
        deps.extend(run/n for n in ['result.json', 'physical_slider_review.json', 'isolation_verification.json',
                                   'source_snapshot/ftir_slider_actor.py', 'source_snapshot/balance.py'])
    report = dict(attempts=rows, physical_passes=sum(r['physical_passed'] for r in rows),
                  qualified_skills=0, qualified_paper_branches=0,
                  source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
                  scope='Five nominal development attempts with different controllers/hand candidates, all failures retained. One successful attempt is not a reliability campaign, walking integration, full cover opening or a complete paper branch.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(rows), flush=True)


if __name__ == '__main__':
    main()
