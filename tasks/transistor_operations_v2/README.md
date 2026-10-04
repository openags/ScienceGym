# Three-dimensional integrated metal-oxide transistors

Original English ScienceGym whole-paper task design for Yuvaraja et al., Nature Electronics 7, 768–776 (2024), DOI [10.1038/s41928-024-01205-0](https://doi.org/10.1038/s41928-024-01205-0).

The nine-page article and complete 53-page written supplement are covered by 24 branch designs across 17 source route groups, 44 operation templates and a 72-layer inventory. Preparation and fabrication, failed controls, packaging, metrology, electrical acquisition, stress histories, inverter reconfiguration, readout and cleanup remain separately traceable. Numerical analysis is a distinct, unimplemented dependency.

All ten audited source conflicts remain qualification gates, including the 25/50 nm buffer discrepancy and the printed ON/OFF, mobility and subthreshold-swing equations. No source value is silently repaired or promoted to a robot success target. Ordinary and independently biased inverter netlists remain distinct.

## Start here

- TASK_DESIGN.md explains scope, complete route coverage and limitations
- branches.json lists available operations; lifecycle_contract.json and tests/contract.py define their safe causal order
- control_packages.json preserves source conditions without inventing missing settings
- source_conflicts.json and unknown_parameters.json identify the qualification gates
- coverage_matrix.json accounts for every main/SI page, figure inventory, table and section
- VERIFICATION.json and review/INDEPENDENT_REVIEW.md report the actual verification scope

## Offline checks

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

The synthetic fixture retains all 90 ordered inverter pairs and named control cases while reducing population samples. Its clock is virtual. Its payload hashes protect synthetic bookkeeping records, which contain no scientific measurements. No real robot actuation, physics simulation, numerical reproduction or scientific replication occurred.

Only agent_visible.json is actor-facing. EXPORT_ALLOWLIST.json pins the exact original-file export. Publisher PDFs, source prose, images, raw experimental data and private input files are absent. External publication belongs to the separately authorized parent workflow.
