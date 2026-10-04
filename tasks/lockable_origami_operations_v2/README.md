# Lockable flat-foldable origami metamaterials

Independently reviewed original whole-paper task-design draft for [Jamalimehr et al., Nature Communications (2022)](https://doi.org/10.1038/s41467-022-29484-1). Thirty scientific design routes and sixty symbolic operation definitions retain fabrication, paperboard characterization, configuration, mechanical tests, controls and separate analytical/numerical work.

This package is not runnable laboratory automation. All machine services, robot motions, physical simulation and scientific solvers are unimplemented. Static scene bindings do not qualify geometry, contact or manipulation. Whole-paper DESIGN coverage does not imply whole-paper execution or replication.

Read TASK_DESIGN.md, source_access_audit.json, source_conflicts.json and RELEASE_BOUNDARY.json. Only agent_visible.json may enter actor context; all other files are evaluator/auditor material.

Run offline checks from this directory:

    python3 -B -m unittest discover -s tests -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

The package schema is lockable_origami_task.v1; it is an original inspection format, not a hardware API.

Independent review passed with explicit scope limits: 64 author test methods and 52 independent test methods. All 143 finite synthetic fixtures remain bookkeeping examples. The original paired static asset archive is pinned by asset_binding_plan.json; its earlier immutable snapshot retains its initial availability flags.
