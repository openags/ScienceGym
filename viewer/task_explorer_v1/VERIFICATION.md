# Verification: seven-family task explorer

Updated 2026-10-02. Source task files are pinned to public ScienceGym commit ebf366bde7d8b8fd0899165d168a9f8f7c43c8ca.

## Checks performed

- 17 Python tests: operation references, lossless pooling, JSON/JS equality, source hashes, SVG structure, local links, route ordering, actions/states/recovery, microscopy obligations, acoustic loops, repeated diSPIM IDs, and perovskite unknowns/service/condition fidelity
- Node mocked-DOM checks select all 160 routes with 9,144 displayed operation occurrences, including repeated IDs, search, tabs, malformed hashes and textual partial-order predicates
- JavaScript syntax checks and deterministic generation
- SVG renders are static graphics. Actual browser interaction, responsive layout and keyboard focus remain unverified

## Representation counts

Seven paper families, 160 route/branch records and 1,218 operation definitions. Perovskite contributes 40 templates and 752 action definitions. Nested condition/replicate loops are not expanded into successful experiments. Microscopy includes explicitly identified inspector navigation actions.

## Scope

These checks concern faithful display of reviewed authored task specifications, not independent scientific source verification, physical execution, robot feasibility or experimental reproduction. No new paper has been converted by adding this adapter. No real browser execution is claimed. The earlier browser file/localhost restrictions remain respected.

## Reproduction

Run from this folder:

```sh
python3 build.py --tasks ../../tasks
SCIENCEGYM_TASKS=../../tasks python3 -m unittest discover -s tests -v
node --check app.js
node tests/test_app.js
```
