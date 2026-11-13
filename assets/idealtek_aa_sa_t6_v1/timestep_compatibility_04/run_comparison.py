"""Execute the preregistered component timestep comparison; no robot credit."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
contract = json.loads((HERE / 'contract.json').read_text())
source = BASE / contract['source_revision']
candidate = BASE / contract['comparison_revision']
baseline_run = BASE / contract['baseline_fixture']
run = BASE / contract['candidate_fixture']

# The comparison may change the timestep only. This is checked before execution.
old = ET.parse(source / 'tool.xml')
new = ET.parse(candidate / 'tool.xml')
old.getroot().find('option').set('timestep', str(contract['candidate_timestep_s']))
assert ET.tostring(old.getroot()) == ET.tostring(new.getroot())
for mesh in (source / 'meshes').glob('*.stl'):
    assert mesh.read_bytes() == (candidate / 'meshes' / mesh.name).read_bytes()
for filename, args, log in [
    ('check_passive_contact.py', [candidate, run], 'contact.log'),
    ('review_passive_hold.py', [candidate, run], 'hold.log'),
]:
    with (HERE / log).open('x') as stream:
        result = subprocess.run([sys.executable, '-B', str(BASE / filename), *map(str, args)],
                                stdout=stream, stderr=subprocess.STDOUT)
    print(filename, 'exit', result.returncode, flush=True)

reference = json.loads((baseline_run / 'review.json').read_text())
observed = json.loads((run / 'review.json').read_text())
hold = json.loads((run / 'hold_quality_review.json').read_text())
def held_gap(report):
    rows = [r['gap_m'] for r in report['observations'] if 4.5 <= r['time_s'] <= 5.5]
    assert rows
    return sum(rows) / len(rows)

gap_error = abs(held_gap(reference) - held_gap(observed))
force_error = max(abs(observed['force_peaks_n'][k] / v - 1)
                  for k, v in reference['force_peaks_n'].items())
checks = dict(only_timestep_changed=True,
              contact_checks_passed=observed['passed'], hold_checks_passed=hold['passed'],
              held_gap_agrees=gap_error <= contract['acceptance']['maximum_absolute_held_gap_difference_m'],
              peak_force_agrees=force_error <= contract['acceptance']['maximum_relative_peak_force_difference'])
result = dict(passed=all(checks.values()), checks=checks,
              absolute_held_gap_difference_m=gap_error, maximum_relative_peak_force_difference=force_error,
              candidate_minimum_gap_m=observed['minimum_gap_m'],
              candidate_maximum_penetration_m=observed['maximum_intended_penetration_m'],
              candidate_hold_excursion_m=hold['hold_gap_excursion_m'],
              qualified_robot_manipulation=False, full_robot_integrator_changed=False,
              scope=contract['scope'],
              source_hashes={str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [Path(__file__), HERE / 'contract.json', candidate / 'tool.xml',
                                       run / 'review.json', run / 'hold_quality_review.json']})
with (HERE / 'review.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps(result), flush=True)
if not result['passed']:
    raise SystemExit(1)
