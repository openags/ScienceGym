# Cold-programmed shape morphing: ScienceGym task design

Independent, original whole-paper robot-task contracts for Yue et al., *Cold-programmed shape-morphing structures based on grayscale digital light processing 4D printing*, Nature Communications 14, 5519 (2023), DOI [10.1038/s41467-023-41170-4](https://doi.org/10.1038/s41467-023-41170-4).

This is a static design package. It does not implement robot motion, chemical processing, UV exposure, physical simulation, device control or scientific replication. Closed, qualified services own chemical preparation, printing, thermal/mechanical actuation and liquid-metal filling. The task describes custody, safe loading interfaces, approvals, readbacks and evidence requirements around those services.

The full main article and 20-page textual supplement were inspected, including five main figures, twelve supplementary figures and two tables. Movie descriptions were read; eight actual movies, source-data workbook and peer-review correspondence were not read. Source completeness and hardware readiness are separate. Unread motion evidence, missing geometry, unsupported operating details and missing qualification remain gates.

Material preparation, fabrication, tensile/DMA characterization, shape-memory and hinge cycling, all demonstrated shape families, electronics, micro-pipe and alternative-resin work are in scope. Constitutive modeling, numerical fitting, FEA and analytical hinge theory have separate nonphysical dispositions. Speculative applications and suggested future post-treatment are excluded.

Only `agent_visible.json` is actor-public. All other files are author/evaluator material. No publisher files, source text dumps or copied figure pixels belong to the export.

Read TASK_DESIGN.md, STATUS.json and VERIFICATION.json for final scope and check results. Tests are static and synthetic-bookkeeping checks only.

## Package inventory

76 reusable operation definitions, 32 physical branches, six separate numerical/analytical dispositions, 19 unresolved gates, 24 transport contracts and seven loop types. Static and synthetic tests are included; independent review history is preserved in review/.

Run `python3 -B tests/verify_package.py`, `python3 -B -m unittest discover -s tests -v` and `python3 -B tests/verify_export.py` from this directory.
