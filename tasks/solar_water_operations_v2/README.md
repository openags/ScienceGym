# Solar-water physical measurement task

Original bounded nonbiological task design for Singh et al., Nature Sustainability (2020), DOI [10.1038/s41893-020-0566-x](https://doi.org/10.1038/s41893-020-0566-x).

15 branches and 34 operation templates cover qualified prefabricated coupons, clean-water assemblies, physical optics/wicking/thermal/mass measurements, orientation, clean-water condensation bookkeeping and benign-only qualified maintenance. All 14 source conflicts are preserved. Biological operations are excluded. Fabrication and hazardous chemistry are closed qualified-service boundaries without recipes.

This is not full-paper-complete coverage and must not be counted as such. No water safety, pathogen efficacy, validated mechanism, actual robot execution, physical simulation or scientific reproduction is claimed.

Start with TASK_DESIGN.md, branches.json, lifecycle_contract.json, source_conflicts.json, coverage_matrix.json and VERIFICATION.json. Only agent_visible.json is actor-facing. All numerical outcomes are literature annotations, never robot success targets.

Offline checks:

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

The synthetic fixture has no scientific measurement values or physical time. Its caller-owned context is not authenticated authority. Production station adapters, geometry, qualification values and independent experimental evidence remain absent.

EXPORT_ALLOWLIST.json pins the exact original-file export. No source assets are included. External publication belongs to the separately authorized parent workflow.
