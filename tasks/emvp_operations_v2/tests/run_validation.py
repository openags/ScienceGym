#!/usr/bin/env python3
"""Run static stdlib tests; write portable receipts for the exact tested snapshot.

No network, third-party execution, simulation, physical control, source-text
extraction or artifact publishing occurs. Optional source reads only hash bytes.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

import test_emvp_contract as contract


def portable(text):
    # Tracebacks are retained without revealing the local review environment.
    text = text.replace(str(contract.ROOT.resolve()), '<package>')
    if contract.SOURCE_DIR:
        text = text.replace(str(contract.SOURCE_DIR.resolve()), '<external-source>')
    return text


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'test': test.id(), 'status': 'passed'})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({'test': test.id(), 'status': 'skipped', 'reason': portable(reason)})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({'test': test.id(), 'status': 'failed', 'detail': portable(self._exc_info_to_string(err, test))})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({'test': test.id(), 'status': 'error', 'detail': portable(self._exc_info_to_string(err, test))})

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.records.append({'test': subtest.id(), 'status': 'failed', 'detail': portable(self._exc_info_to_string(err, test))})


def fingerprint(paths):
    return {path.relative_to(contract.ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, help='Explicit external source cache for hash verification only; source bytes are never exported')
    parser.add_argument('--report-dir', type=Path, default=contract.ROOT / 'independent_review')
    options = parser.parse_args()
    contract.SOURCE_DIR = options.source_dir.resolve() if options.source_dir else None
    inspected = set(contract.ROOT.glob('*.json')) | set(contract.ROOT.glob('*.md'))
    inspected |= {p for p in (contract.ROOT / 'independent_source_audit').glob('*') if p.is_file()}
    checkers = set((contract.ROOT / 'tests').glob('*.py'))
    before = fingerprint(inspected | checkers)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(contract.ROOT / 'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
    after = fingerprint(inspected | checkers)
    stable = before == after
    if not stable:
        result.records.append({'test': 'snapshot_unchanged_during_validation', 'status': 'failed', 'detail': 'Package changed while tests ran; rerun against a stable snapshot'})
    success = result.wasSuccessful() and stable
    log = portable(stream.getvalue())
    if not stable:
        log += '\nFAILED: package changed during validation\n'
    print(log, end='')
    options.report_dir.mkdir(parents=True, exist_ok=True)
    source_rows = [row for row in result.records if row['test'].endswith('test_optional_source_bytes_sha256')]
    source_status = source_rows[0]['status'] if source_rows else 'not run'
    report = {
        'schema_version': 'emvp_independent_validation.v2',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Independent static package assertions and synthetic record-integrity adversarial fixtures only',
        'outcome': 'passed' if success else 'failed',
        'counts': {'run': result.testsRun, 'passed': sum(row['status'] == 'passed' for row in result.records), 'failures': len(result.failures) + int(not stable), 'errors': len(result.errors), 'skipped': len(result.skipped)},
        'source_byte_verification': source_status,
        'source_byte_location': 'Explicit external source directory; not bundled' if options.source_dir else 'No external directory supplied',
        'snapshot_stable_during_validation': stable,
        'execution': {'stdlib_only': True, 'network': False, 'third_party_code': False, 'scientific_simulation': False, 'hardware_execution': False, 'new_scientific_measurements': False, 'remote_publication': False},
        'limitations': [
            'Structural consistency and specified bookkeeping rules do not establish physical feasibility or scientific truth',
            'Synthetic record validators are illustrative integrity checks, not a schema-complete runtime loader or acquisition authenticator',
            'Source semantics remain grounded in the separate source audit; optional source-byte hashing verifies identity only',
            'Synthetic numbers are checker examples, never operating settings',
            'Actor isolation is checked on the declared static projection only; runtime loader, observation backend, controller and task runner are not implemented',
            'Public manifest integrity is checked only when an EXPORT_ALLOWLIST.json exists in the tested root; draft mode does not claim exporter execution',
        ],
        'tests': result.records,
        'inspected_file_sha256': {name: digest for name, digest in before.items() if not name.startswith('tests/')},
        'checker_file_sha256': {name: digest for name, digest in before.items() if name.startswith('tests/')},
    }
    (options.report_dir / 'validation_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (options.report_dir / 'validation_log.txt').write_text(log, encoding='utf-8')
    counts = report['counts']
    lines = ['# Independent EmVP static validation', '', f"Result: **{report['outcome'].upper()}**", '',
             f"{counts['run']} tests run; {counts['passed']} passed; {counts['failures']} failures; {counts['errors']} errors; {counts['skipped']} skipped.", '',
             '## Scope', '', 'Standard-library-only static design checks and synthetic record-integrity fixtures. No installation, third-party execution, scientific simulation, physical experiment, hardware control or publication.', '',
             '## Checks', '',
             '- All 19 configuration DAGs, three separately dispatched cage paths, references, source coverage and scoped material/operation gates',
             '- Control comparison axes, ordered observation states, finite-input requirements and explicit nonmanual boundaries',
             '- Declared actor/evaluator separation, independent evidence requirements and no measured-outcome reward oracle',
             '- Qualified supplied hardware/geometry, transfer/orientation and flush-before-postcure',
             '- Source seconds and minutes-scale print durations, exact row labels, unresolved chip identity and separate clocks',
             '- Needle/design/measured diameters, printed hardness versus cast tensile and pre-cure oozing distinctions',
             '- Raw/derived context, sample lineage, append-only attempts, honest counts and tailored recovery semantics',
             '- Authored text-only export boundary; exact manifest validation when an exported package is tested', '',
             '## Boundaries', '', *[f'- {item}' for item in report['limitations']],
             f'- Source-byte hash verification: {source_status}', '', '## Failures and skips', '']
    issues = [row for row in result.records if row['status'] != 'passed']
    lines += [f"- {row['test']}: {row['status']}" + (f" ({row['reason']})" if row.get('reason') else '') for row in issues] or ['None']
    lines += ['', 'validation_report.json contains per-test outcomes and exact snapshot/checker fingerprints. validation_log.txt contains assertion details.', '']
    (options.report_dir / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
