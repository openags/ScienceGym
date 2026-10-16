# Directional cooling: reconstruction pilot v3

This is a reviewable reconstruction of the entire reported physical program in
[Bhatia et al. (2018)](https://doi.org/10.1038/s41467-018-07293-9), not a completed
robot experiment or an accepted gold-standard example.

Start with the [complete manipulation dossier](MANIPULATION_REVIEW.md), [TASK_DESIGN.md](TASK_DESIGN.md), the [portable package](package.json),
the [source inventory](source_inventory.json) and the [open review gates](review.json).
The [3D revision](../../assets/cooling_scene_assets_v2/README.md) contains original
metric geometry and rendered inspection views. Historical v2 and its frozen viewer
records remain unchanged; this revision does not add another paper to the count.

The contract contains 64 operation definitions and 352 observable reference steps
(200 manipulation steps and 152 context/check/process steps)
across 11 physical branch definitions. A deliberately synthetic work order expands
them to 365 planned occurrences, including transport, repetitions, optical specimen
lineage and configuration restoration. **365 is a fixture-dependent planning count,
not an experiment count.** No observations or successful robot attempts are supplied.

```bash
python3 tasks/directional_cooling_operations_v3/rebuild.py
python3 tasks/directional_cooling_operations_v3/validate.py
python3 -m unittest discover -s tasks/directional_cooling_operations_v3/tests -v
```

Python 3 and `jsonschema` are required for validation; the authoring scripts
otherwise use the standard library. `operations.schema.json` checks the serialized
operation contract, while `validate.py` checks cross-file semantics. The
authoring scripts produce portable JSON; `planner.py` also implements
a limited symbolic transition checker and an actor-input allowlist. There is no
device driver, observation verifier, robot controller or dynamics simulation.
Reference JSON is trusted author/evaluator material and must not be loaded as an
actor instruction bundle. Qualified cards must come from a trusted loader; the
allowlist does not sanitize arbitrary free-text content. Qualified episode inputs and remaining geometry are
listed explicitly; missing values are not assigned hidden execution defaults.

The October 17 revision adds explicit contact/tool/support/recovery fields to every
manipulation step, a source-to-action crosswalk, exact geometry variant links,
USB-TC channel/polarity/transition requirements, and seven source-related thermal
map locations. It corrects angular-reference ordering and supplies block drilling,
bath filling, reference/sample exchanges and supported underside access.

`interaction_contracts.json` lists 33 interfaces: 20 have partial named geometry
and 13 have no geometry. Neither category is interaction-qualified. See the
per-interface gaps and `review.json` rather than treating step counts as acceptance.
The previous published review is retained in `review_history/2026-10-15/`.
Step IDs are scoped to the reconstruction revision and content hashes; earlier
observations must never be attached to a replaced step definition.
