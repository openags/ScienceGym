# Embedded Extrusion-Volumetric Printing task family

Reviewable paper-level design for Tisato et al., Nature Communications 16, 6730 (2025), DOI [10.1038/s41467-025-62057-6](https://doi.org/10.1038/s41467-025-62057-6).

Start with [TASK_DESIGN.md](TASK_DESIGN.md).

- 19 configurations across 5 physical families
- 53 operation templates, 15 comparison packages and 30 explicit input gates
- Materials, installed-printer qualification, positive/negative branches, aligned transfer, washing, characterization, controls and lineage
- Explicit source gaps, source conflicts, actor/evaluator boundaries and independent tests
- Source PDFs and publisher pixels excluded from export

This is a source-bounded task-design package, not an executed robot experiment, physics/scientific simulator or reconstruction of missing hardware. Printing takes minutes; no multiday protocol is claimed. No remote publication or license changes were performed.

Validation: see `independent_review/REPORT.md` and `independent_source_audit/README.md` for actual scope. Run `python -B tests/run_validation.py` from the package root. The optional source check requires an explicitly supplied lawful source directory.
