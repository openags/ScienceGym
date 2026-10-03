# Ring-origami task-design draft

Start with [TASK_DESIGN.md](TASK_DESIGN.md). This is an authored whole-paper design for DOI 10.1038/s41467-023-42323-1, with 14 physical branch templates, three preparation routes and 59 reusable operations. It is not executable or physically validated.

- Routes: `branches.json`, `operations.json`, `dependencies.json`
- Grounding: `provenance.json`, `coverage_matrix.json`, `source_access_audit.json`, `source_conflicts.json`, `nonmanual_scope.json`
- Execution requirements: `material_cards.json`, `station_contracts.json`, `control_packages.json`, `episode_input_contract.json`, `unknown_parameters.json`
- Integrity: `lineage_contract.json`, `agent_visible.json`, `evaluator_reference.json`, `source_outcomes.json`, `mock_contract.json`
- Release: `RELEASE_BOUNDARY.json`, `EXPORT_ALLOWLIST.json`, `EXPORT_SCOPE.md`, `VERIFICATION.json`

The source packet remains incomplete: all movies, the movie-description document and Source Data workbook are uninspected. Movie 9 assembly choreography is a specific gate. Both thick resin/TPU specimens and paper-element arrays are covered.

Run static tests with `python -m unittest discover -s tests -v`. These check design consistency and selected anti-shortcut invariants, not robotic feasibility, physics, fabrication or the original paper's findings.

Independent review: `independent_review/REPORT.md` records 48/48 independent checks and an independent 10/10 author-suite rerun. Run its checks with `python -B independent_review/check_contracts.py`.
