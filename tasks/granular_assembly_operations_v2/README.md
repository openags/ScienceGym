# Anti-repellent granular assembly task family

Start with [TASK_DESIGN.md](TASK_DESIGN.md).

Whole-paper experimental task-design draft for Bae et al., Nature Communications (2024), [DOI 10.1038/s41467-024-54976-7](https://doi.org/10.1038/s41467-024-54976-7).

The human-like mobile robot performs sample preparation, fabrication handling, transport, device setup/loading/unloading, measurements and cleanup. Instrument-owned processes and unresolved source inputs stay separate. This is not an executed experiment, controller, physics model or robot-feasibility claim.

- Physical fabrication, surface/collision controls, dry assembly, geometry, image-linked authentication, stability and material/size/shape variants
- Source parameters, explicit gates, sample lineage, condition-specific routes and actor/evaluator boundaries
- Whole-paper scope includes separately labeled synthetic analyses and literature context
- Main/SI inspected; historical movies and data unread, with requiredness audited
- Original factual contracts only; publisher source assets excluded and repository LICENSE unchanged

The package has 26 configurations, 42 operation templates and 31 explicit input gates. The author suite passes 35 checks; the independent contract suite passes 23. Independent review passes at the source-bounded design level.

Validation: `python -B tests/run_validation.py` and `python -B independent_review/check_contracts.py`. Read `independent_review/REPORT.md` for the exact audit scope and limits.
