# Bianisotropic acoustic metasurface task family

Source-grounded whole-paper task-design draft for [Li et al., Nature Communications 9, 1342 (2018)](https://doi.org/10.1038/s41467-018-03778-9).

Start with [TASK_DESIGN.md](TASK_DESIGN.md). The package contains 42 operation templates, 14 selectable design branches, 12 source-coverage families, 18 unresolved input groups and seven comparison/control packages. It uses the local `bianisotropic_paper_task.v1` schema, not a repository-wide executable task standard.

Only the 60-degree panel was physically tested in the paper. The 70/80-degree designs, ideal GSL comparisons, viscous-loss comparison, four-probe retrieval and topology comparisons are computational branches. The four-probe method was implemented in COMSOL, not a reported physical impedance-tube experiment.

## Inspect the package

- Sources and scope: `provenance.json`, `source_access_audit.json`, `coverage_matrix.json`, `source_conflicts.json`
- Robot and instrument work: `operations.json`, `dependencies.json`, `station_contracts.json`, `branches.json`
- Materials, custody and controls: `material_cards.json`, `lineage_contract.json`, `control_packages.json`
- Missing inputs and assets: `unknown_parameters.json`, `episode_input_contract.json`, `asset_needs.json`
- Visibility and evaluation: `agent_visible.json`, `RELEASE_BOUNDARY.json`, `evaluator_reference.json`, `mock_contract.json`
- Reference-only facts: `geometry_tables.json`, `source_outcomes.json`
- Verification and export: `tests/`, `VERIFICATION.json`, `EXPORT_ALLOWLIST.json`, `EXPORT_SCOPE.md`

## Run static checks

From this package directory, with Python 3.9 or later:

```sh
python3 -B -m unittest discover -s tests -v
```

Optional source-byte verification is available only when the reviewer already holds the two lawfully obtained private source files named `main.pdf` and `si.pdf`:

```sh
BIANISOTROPIC_SOURCE_DIR=PATH_TO_PRIVATE_SOURCE_PACKET python3 -B -m unittest discover -s tests -v
```

No source files are downloaded by the test. Without that environment variable, one optional source-byte test is skipped. Tests check JSON, references, source distinctions, visibility and synthetic bookkeeping invariants. They do not execute a printer, robot, acoustic solver, optimizer or scientific simulation, and do not authenticate raw records.

## Readiness

Main article and required SI are source-complete for this design scope. Robot/asset bindings, CAD, qualified operating cards, raw experimental data, numerical models, calibrated instruments and trusted event infrastructure are absent. This is not a validated physical reproduction or execution-ready environment. Reported efficiencies are reference evidence, never automatic task acceptance thresholds.

Attribution: Junfei Li, Chen Shen, Ana Díaz-Rubio, Sergei A. Tretyakov and Steven A. Cummer, Nature Communications 9, 1342 (2018), DOI 10.1038/s41467-018-03778-9. Main article is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to credit-line exceptions. New robot/evaluator prose is independently authored; no author endorsement is implied. Publisher PDFs, source text and figure images are not bundled.
