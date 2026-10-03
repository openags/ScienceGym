# Independent static validation report

Verified 2026-10-03. Scope: the sanitized public prismatic task-design package for DOI 10.1038/s41467-019-13319-7.

## Results

- **Default public run:** 41 tests discovered, 40 passed, 1 explicitly skipped, 0 failures/errors
- **Optional source-byte run:** 41 tests discovered, 41 passed, 0 skipped, 0 failures/errors
- The only default skip is source-byte verification. Publisher source files are intentionally not bundled
- The same standalone Python test file runs unchanged against the sanitized export. It uses only the Python standard library and does not read embedded host paths

Run from the package root:

```sh
python tests/test_prismatic_contract.py
```

Optionally supply a lawful local source directory containing the basenames listed in `provenance.json`:

```sh
python tests/test_prismatic_contract.py --source-dir PATH
```

The optional check fails if a requested file is missing or its length/hash differs. Without that explicit argument, only provenance/audit metadata consistency is checked. Ordinary discovery is also supported:

```sh
python -m unittest discover -s tests -v
```

## Checked contracts

- Strict JSON, duplicate/nonfinite rejection, unique IDs and evidence/unknown/operation/branch/family/station/control references
- 49 operation templates and 46 dependency edges; acyclic template graph and dependency-closed branch subsets
- Seven source-supported hands-on families, 12 configurations, separate numerical/outlook scope, and complete operation coverage including conditional quarantine
- One selected actor goal; evaluator graphs, test fixtures and source outcomes excluded from the declared actor projection
- Null-gated episode cards; no source-gap completion by zero/default/empty loop or numerical-model settings
- Chronological last-five selection, paired loading/unloading, consistent specimen/version/run/condition/fixture/calibration, and rejection of backfilling invalid final cycles
- Distinct loaded reachability, actuation removal and post-release outcomes; no stability inferred from a held pose
- Mylar/elastomer and 50/125 micrometre controls; explicit Cartesian material-target coverage
- Eight unique 2×2×2 array unit slots, distinct from independent specimens; finite boundary/long-period classes preserved
- SI6 displayed Arabic identifiers 1–11 and 1–15; no interpretation as historical specimen counts or exhaustive state counts
- Pneumatic program/mapping/pressure gates; no inferred 00/01/10/11 truth table or four-program completion
- Append-only failed attempts/raw records, retry links, object/parent lineage and version history
- Artifact existence, source metadata consistency, retained source disagreements, and no hard-coded paper-outcome success criteria

## Adversarial testing

The suite includes eight checker/record-fixture tests and eleven tests that mutate actual package data. Covered failures include dangling/cyclic dependencies, actor oracle leakage, missing/mixed final cycles, erased attempt history, duplicate array units, dropped material conditions, changed SI6 labels, invented pneumatic commands, flattened Cartesian coverage and hard-coded source-result acceptance.

The static fixture helpers validate bookkeeping examples only. They are not the future runtime evaluator and do not manufacture scientific data.

## Review finding and correction

The initial cube and array comparison loops did not explicitly encode condition-target nesting. The author added typed loop expansion, a two-material-by-eight-target cube grid, per-thickness eight-slot array preparation, per-class finite-array target schedules, and explicit conditional quarantine. Regression tests now reject flattening the material-target grid.

## Limits

No hardware, robot episode, physical simulation, scientific solver, CAD reconstruction or new measurement was run. Actor/evaluator separation is a checked authoring contract; an actual runtime loader is not implemented. Physical feasibility and qualified geometry, materials, interfaces, settings and observation cards remain future requirements. These results establish static design integrity, not experimental reproduction.

## Public export allowlist recommendation

Include authored JSON contracts, `README.md`, `TASK_DESIGN.md`, `EXPORT_SCOPE.md`, this report, `tests/test_prismatic_contract.py`, the machine-readable report, and the authored source-audit JSON/README. Preserve citations, exact source locators and hashes. Exclude publisher HTML/PDF/image/movie bytes, inspection renders, absolute host paths, caches, bytecode, build/export scripts with local paths, and runtime secrets. Retain the actor-release restriction independently of public authoring access.
