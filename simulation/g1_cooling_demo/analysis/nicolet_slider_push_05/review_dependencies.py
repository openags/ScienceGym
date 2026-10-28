"""Resolve retained evidence pins against current files or frozen source copies."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = BASE.parents[1]


def main():
    output = HERE/'dependency_review.json'
    if output.exists():
        raise FileExistsError(output)
    cache = {}

    def sha(path):
        path = path.resolve()
        if path not in cache:
            cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return cache[path]

    records = []
    reports = sorted(HERE.glob('*.json'))
    for report in reports:
        data = json.loads(report.read_text())
        for name, expected in data.get('source_hashes', {}).items():
            path = ROOT/name
            resolved = path if path.is_file() and sha(path) == expected else None
            if resolved is None and path.suffix == '.py':
                candidates = sorted((BASE/'runs').glob('ftir_*/source_snapshot/'+path.name)) + sorted(HERE.glob('*.py'))
                resolved = next((p for p in candidates if sha(p) == expected), None)
            records.append(dict(report=str(report.relative_to(ROOT)), declared_source=name,
                                expected_sha256=expected,
                                resolved_source=None if resolved is None else str(resolved.relative_to(ROOT)),
                                retained_revision=resolved is not None and resolved != path,
                                passed=resolved is not None))
    runs = []
    for name in ['ftir_slider_06', 'ftir_slider_07', 'ftir_approach_01']:
        run = BASE/'runs'/name
        result = json.loads((run/'result.json').read_text())
        physical = json.loads((run/'physical_slider_review.json').read_text())
        checks = {'reviewed_trace_unchanged':sha(run/'trace.npz') == physical['trace_sha256'],
                  'reviewed_world_unchanged':sha(run/'world.xml') == physical['model_sha256']}
        for name, expected in result['source_sha256'].items():
            checks['snapshot_'+name] = sha(run/'source_snapshot'/name) == expected
        runs.append(dict(run=run.name, passed=all(checks.values()), checks=checks))
    report = dict(passed=all(r['passed'] for r in records+runs), dependencies=records, runs=runs,
                  reviewer_sha256=sha(Path(__file__)),
                  scope='Integrity of completed evidence inputs and frozen source revisions. Does not convert failed physical trials or diagnostic sensor fixtures into qualified executions.')
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], dependencies=len(records),
                         retained_revisions=sum(r['retained_revision'] for r in records),
                         failed=[r for r in records if not r['passed']], runs=[(r['run'], r['passed']) for r in runs])), flush=True)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
