# Acoustic wavefront task family

Original ScienceGym whole-paper robot task-design contracts for Xie et al., *Wavefront modulation and subwavelength diffractive acoustics with an acoustic metasurface*, Nature Communications 5, 5553 (2014), DOI [10.1038/ncomms6553](https://doi.org/10.1038/ncomms6553).

Status: source-complete design with execution gates. Complete five-page main and five-page official SI were inspected. No physical simulation, acoustic solver, robot, apparatus or public write was run. This package is independent ScienceGym work.

- 69 reusable operations, with physical manipulation, device-autonomous processes and analysis explicitly distinguished
- 10 physical routes, 8 numerical/theoretical dispositions, 14 supported transport routes and 7 symbolic loops
- 15 unresolved input gates, without guessed defaults
- Immutable sample/array/run lineage, conditional acceptance, source conflicts and actor/evaluator separation
- Original static verifier plus adversarial synthetic-bookkeeping tests

Read [TASK_DESIGN.md](TASK_DESIGN.md) for the complete workflow and [EXPORT_SCOPE.md](EXPORT_SCOPE.md) for rights and delivery limits. The exact local review file boundary is [EXPORT_ALLOWLIST.json](EXPORT_ALLOWLIST.json). Source files and source figure pixels are excluded.

## Checks

From this directory with Python 3.9 or newer:

```sh
python3 -B tests/verify_package.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

These check original contracts, references, source-condition semantics, gate closure, export hygiene and synthetic record rejection. They do not establish robot feasibility, apparatus safety, acoustic performance, authentic device receipts or whole-paper execution. No third-party dependency is needed.

## Files

- operations, branches, dependencies, state and transport contracts describe the operator/device boundary and physical routes
- provenance, coverage, source outcomes/conflicts/access audit and nonmanual scope retain paper coverage and evidence boundaries
- episode inputs, materials, assets, controls and unknowns define what must be supplied before execution
- agent_visible is the sole static actor-allowlisted file; author/evaluator documents must not be passed wholesale to an actor
- lineage, evaluator and mock contracts explain trusted observations and test limits

All package documents other than the actor-public schema are authoring/review material. No runtime loader, real sensor backend, simulator, geometry assets or execution command is supplied.
