# Wetting transitions: original whole-paper task design

An independent English task-design package for Gerber et al., Nature Communications 10, 4776 (2019), DOI 10.1038/s41467-019-12093-w.

The design accounts for 16 routes and 74 operation contracts across commercial silicone preparation, custody/ageing, mechanics/rheology, macroscopic and microscopic drying, phase-study lineage, reference inference, traction interpretation and safe closeout. Ten source conflicts/scope cautions and 25 qualification gaps remain explicit and branch-local.

This is not runnable laboratory automation, a physical simulator or scientific reproduction. Cadmium-containing fiducial preparation is an unmodeled external sealed-receipt boundary. No synthesis, ink handling or high-voltage deposition controls are supplied. All hardware and inverse-model services remain unimplemented. Original static scene assets do not qualify physical geometry or robot motion.

The complete main XML and 15-page written SI were reviewed upstream; all main/SI figures were inspected. The movie was only sampled and workbook numerical contents remain unread. Source media and prose are excluded.

Only agent_visible.json is actor-facing. Read TASK_DESIGN.md, source_access_audit.json, source_conflicts.json and RELEASE_BOUNDARY.json before use. Source values are references, never success constants.

Offline checks (Python standard library only):

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

The finite tests validate synthetic bookkeeping and explicitly bounded arithmetic only. Whole-paper design coverage is one paper-level design, not 16 papers or 74 experiments; it contributes zero validated runnable whole-paper tasks.

Verification: 87 author test methods, 40 independently authored hostile-test methods, 64 finite synthetic fixtures and 70 static checks pass. The separately reviewed 40-member static asset archive is pinned in asset_binding_plan.json. Source/qualification holds remain unresolved for real implementation.
