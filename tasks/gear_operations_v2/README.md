# Gear metamaterials robot-task design

Original whole-paper design for Nature Materials DOI 10.1038/s41563-022-01269-3. Start with [TASK_DESIGN.md](TASK_DESIGN.md).

- 18 physical branch templates, 19 specimen families, eight preparation routes and 69 operations
- Seven numerical branches remain separate; measured hysteresis and controls are included
- Complete written-source audit plus sampled video review, not full-motion inspection
- Explicit material/geometry conflicts and qualified-input gates; no physical execution or simulation

## Inspect

- Source: `provenance.json`, `source_access_audit.json`, `source_conflicts.json`, `coverage_matrix.json`
- Physical design: `branches.json`, `operations.json`, `dependencies.json`, `station_contracts.json`, `material_cards.json`
- Inputs and integrity: `episode_input_contract.json`, `unknown_parameters.json`, `lineage_contract.json`, `control_packages.json`, `asset_needs.json`
- Evaluation boundaries: `agent_visible.json`, `evaluator_reference.json`, `source_outcomes.json`, `mock_contract.json`, `nonmanual_scope.json`
- Release/checks: `STATUS.json`, `VERIFICATION.json`, `RELEASE_BOUNDARY.json`, `EXPORT_ALLOWLIST.json`, `independent_review/`

## Verify locally

Run from this package directory:

```sh
python -B verify_package.py
python -B -m unittest discover -s tests -v
python -B independent_review/check_static.py
python -B independent_review/probe_adversarial.py
python -B independent_review/probe_structural_mutations.py
```

Schema identifier: `gear_paper_task.v1`. It is a package-local authored contract, not a claim of universal runtime compatibility. The synthetic checker validates bookkeeping only; actor projection, trusted logger, assets, robot motion and physical calibration remain unimplemented.

Independent review passed 85 static checks, 40 targeted adversarial probes and 1,178 generated deletion/order mutations across all 18 branches. The author suite passed 65 tests. These are task-contract and synthetic bookkeeping checks only.
