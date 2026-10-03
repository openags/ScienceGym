# Prismatic metamaterials task family

Reviewed task-design draft for DOI [10.1038/s41467-019-13319-7](https://www.nature.com/articles/s41467-019-13319-7)

Start with [TASK_DESIGN.md](TASK_DESIGN.md). The package contains 49 reusable operation templates, seven practical source families and 12 selectable configurations. It covers cardboard, PLA/Mylar compression, truncated-tetrahedron reach/release, cube hinges, finite-array thickness/boundary comparisons, SI6 selected configurations and the text-reported pneumatic demonstration.

- Scientific audit: `independent_source_audit/audit.json`
- Coverage and branches: `coverage_matrix.json`, `branches.json`
- Manipulation/dependencies: `operations.json`, `dependencies.json`
- Actor/evaluator boundary: `agent_visible.json`, `RELEASE_BOUNDARY.json`, `evaluator_reference.json`
- Source gaps and controls: `unknown_parameters.json`, `control_packages.json`
- Static test report: `tests/` (see its current report for actual pass/fail scope)

This is a task-design deliverable, not an executable simulator. No robot/hardware, physical simulation or scientific solver was run. No CAD, specimen counts, physical loading settings or measured results were invented. Missing execution inputs are preserved as blockers. Source files are not bundled.

Source attribution: Agustin Iniguez-Rabago, Yun Li and Johannes T. B. Overvelde, Nature Communications 10, 5577 (2019). Publisher article is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to any credit-line exceptions. New robot and evaluation contracts are independently authored interpretations; no author endorsement is implied.
