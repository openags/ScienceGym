# Quantum paraelectric varactors: whole-paper task-design draft

Original English design based on [Apostolidis et al., Nature Electronics 7, 760-767 (2024)](https://doi.org/10.1038/s41928-024-01214-z). The package represents the full available reported route: crystal and nanotube device fabrication, assembly, cryogenic calibration, fixed-load STO/KTO characterization, SQD/DQD readout, magnetic-field comparison, hysteresis, stability and separate model studies.

There are 28 scientific design routes, 80 symbolic operation definitions and 12 static asset groups with 65 semantic anchors. This is not runnable laboratory automation. Cleanroom, chemical, growth, beam, bonding, cryogenic, magnetic, RF/DC and cleanup services are unimplemented qualified external boundaries. No robot motion, exact geometry, physical simulation, circuit solver or scientific reproduction is validated.

Only agent_visible.json is actor-facing. All other files are evaluator/auditor material. Read TASK_DESIGN.md, source_access_audit.json, source_conflicts.json and RELEASE_BOUNDARY.json before using the package. Source results are context, never pass constants. All supplied source text and ten figures were inspected by the independent source auditor; the main representation was full JATS, not a main PDF.

Run offline checks from this directory:

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

The finite fixtures only test bookkeeping, scoped evidence matching and declared arithmetic. Their public records are not authenticated laboratory evidence. Whole-paper DESIGN coverage does not imply whole-paper execution or replication.

Independent review passes for the stated design/offline scope: 66 author test methods, 59 independent test methods and 160 finite synthetic fixtures. The separately reviewed 37-member static asset archive is pinned in asset_binding_plan.json. None of these checks establishes hardware safety, physical execution or scientific reproduction.
