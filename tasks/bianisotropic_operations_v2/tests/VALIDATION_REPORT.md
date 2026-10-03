# Validation report

Date: 2026-10-03. Python: 3.12.14.

- Standard package command: 49 tests run; 48 passed, one optional source-byte test skipped; zero failures/errors
- With the supplied private source directory: 49 tests passed; zero skips/failures/errors
- A separate reviewer independently reran all 49 tests with source-byte verification and found no remaining substantive concern in the stated design-only scope
- Exact case IDs and core contract hashes are in `validation_report.json`; final payload hashes are in `../EXPORT_ALLOWLIST.json`

Run from the package root:

```sh
python3 -B -m unittest discover -s tests -v
BIANISOTROPIC_SOURCE_DIR=PATH_TO_PRIVATE_SOURCE_PACKET python3 -B -m unittest discover -s tests -v
```

The optional directory is an already authorized private copy containing `main.pdf` and `si.pdf`. No source download is performed. A plain export deliberately skips its source-byte test.

Checks include strict JSON, IDs/references/dependency closure, source scope, 19 factual geometry rows, outcome/denominator distinctions, source-media and machine-path exclusion, actor whitelist behavior, nine-period identity/order, thermal/motion release, complete four-record scans, canonical raw lineage, current blank/sample installation context, source/frame/phase compatibility, matched numerical controls, complete GA records, and station-scoped cleanup. Retrieval fixtures check both probe conditioning and the transformed interface pressure/normalized-velocity matrix; these are small synthetic algebra tests, not a sound-field simulation.

Seven review findings across two passes were resolved and regression-tested. The review receipt describes their scope and resolution.

No robot, printer, DAQ, acoustic solver, optimizer or scientific experiment was run. The fixtures cannot authenticate events, establish mechanical feasibility, validate calibration or prove replication. A favorable source percentage is never an acceptance oracle.
