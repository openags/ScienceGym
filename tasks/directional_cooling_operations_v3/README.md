# Directional cooling: reconstruction pilot v3

This is a reviewable reconstruction of the entire reported physical program in
[Bhatia et al. (2018)](https://doi.org/10.1038/s41467-018-07293-9), not a completed
robot experiment or an accepted gold-standard example.

Start with [TASK_DESIGN.md](TASK_DESIGN.md), the [portable package](package.json),
the [source inventory](source_inventory.json) and the [open review gates](review.json).
The [3D revision](../../assets/cooling_scene_assets_v2/README.md) contains original
metric geometry and rendered inspection views. Historical v2 and its frozen viewer
records remain unchanged; this revision does not add another paper to the count.

The contract contains 63 operation definitions and 248 observable reference steps
across 11 physical branch definitions. A deliberately synthetic work order expands
them to 364 planned occurrences, including transport, repetitions, optical specimen
lineage and configuration restoration. **364 is a fixture-dependent planning count,
not an experiment count.** No observations or successful robot attempts are supplied.

```bash
python3 tasks/directional_cooling_operations_v3/authoring.py
python3 tasks/directional_cooling_operations_v3/assemble_package.py
python3 tasks/directional_cooling_operations_v3/planner.py
python3 tasks/directional_cooling_operations_v3/validate.py
python3 -m unittest discover -s tasks/directional_cooling_operations_v3/tests -v
```

Python 3 and `jsonschema` are required for validation; the three authoring scripts
otherwise use the standard library. `operations.schema.json` checks the serialized
operation contract, while `validate.py` checks cross-file semantics. The three
authoring scripts produce portable JSON; `planner.py` also implements
a limited symbolic transition checker and an actor-input allowlist. There is no
device driver, observation verifier, robot controller or dynamics simulation.
Reference JSON is trusted author/evaluator material and must not be loaded as an
actor instruction bundle. Qualified cards must come from a trusted loader; the
allowlist does not sanitize arbitrary free-text content. Qualified episode inputs and remaining geometry are
listed explicitly; missing values are not assigned hidden execution defaults.
