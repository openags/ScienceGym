# Verification: eight-family task explorer

Updated 2026-10-03. Source task files are pinned to public ScienceGym commit `e27d456e2fe99bec9100cc37f7bcd68485504c2b`.

## Checks performed

- **47 Python tests pass with zero skips**, with `SCIENCEGYM_TASKS` explicitly bound to this checkout. Source-bound tests cover all eight families, complete prismatic operation/branch/dependency/context equality, nested material/target and thickness/target obligations, unknown cycle/program counts, conditional recovery, independent campaign dispatch and negative schema mutations
- Earlier-seven-family semantic fingerprints match exactly. All 28 earlier generated JSON, JavaScript, SVG and Markdown files differ from the starting checkout only by full/short source commit pin replacements
- Mocked-DOM tests select all **172 routes/configurations and 9,580 displayed operation/template occurrences**, including every prismatic configuration, all 49 templates, conditional QUARANTINE, nested loops, selection, repeated IDs/clicks, search, tabs and malformed hashes
- Prismatic UI and every configuration's generated SVG have **no inferred chronological adjacency arrows**. The dependency panel displays the source's 46 template edges; all eight additional semantic dependency predicates remain available
- The same mocked-DOM suite passes against the exported single-file HTML; no browser or real DOM is involved
- Full rebuild and `--only prismatic` rebuild are byte-identical, including the complete eight-family manifest and release checksums. The release-manifest inventory, sizes and SHA-256 values are tested
- Static SVGs for cube and thickness configurations were rendered with Inkscape and their actual pixels inspected: nested groups, all configuration labels, unknown-count labels, and conditional recovery are legible without clipping. Cube output is 1440 × 2852 pixels; thickness output is 1440 × 2244 pixels
- Repository-root `scripts/verify_release.py` passes all **9/9 static check groups**, including verifier regressions, English hygiene, JavaScript syntax, both existing embodied-player mocked-DOM suites and all **220 image-hash assertions** over 71 frames / 75 unique images
- The unchanged prismatic package's contract suite passes **40 public tests**, with its one optional external primary-source-byte check explicitly skipped because no external source directory was supplied

## Representation counts

Eight paper families, **172 route/configuration records and 1,267 operation definitions**. Prismatic adds **12 configurations, 49 reusable templates and seven practical families**. Its 436 displayed template occurrences include the eleven configurations and their repeated appearances under the independent campaign view, plus conditional recovery. These are display occurrences, not executed repetitions, specimens or successes.

Perovskite retains 40 templates and 752 action definitions. Microscopy retains explicitly identified inspector navigation actions. Unknown cardinalities remain unresolved; no unknown loop is expanded into invented iterations or successful empty work.

## Scope and verification limits

This is a read-only author/evaluator logical inspector of published task-design contracts. It does not implement an actor projection, loader, evaluator execution, physical simulation, scientific solver, new 3D storyboard or robot controller. It does not certify scientific correctness, practical safety, reproduction or feasibility.

Actual browser file/localhost access was previously denied. No retry, alternative browser, hosting route or security change was attempted. Real-browser rendering, responsive/touch layout, focus and browser Back/Forward behavior remain unverified. Mock hash-change tests and static SVG pixel inspection do not establish browser interaction coverage. No source PDFs, paper images or other third-party assets are redistributed.

## Reproduction

Run from the repository root:

```sh
python3 -B viewer/task_explorer_v1/build.py --tasks tasks
SCIENCEGYM_TASKS=tasks python3 -B -m unittest discover -s viewer/task_explorer_v1/tests -v
node --check viewer/task_explorer_v1/app.js
node viewer/task_explorer_v1/tests/test_app.js
python3 -B scripts/verify_release.py
python3 -B tasks/prismatic_operations_v2/tests/test_prismatic_contract.py
```

For single-file export checks, supply an output path inside your scratch directory:

```sh
python3 -B viewer/task_explorer_v1/export_standalone.py --output /path/to/scratch/ScienceGym-Task-Explorer.html
node viewer/task_explorer_v1/tests/test_app.js /path/to/scratch/ScienceGym-Task-Explorer.html
```

Static SVG pixel inspection uses Inkscape's CLI exporter, not a browser. No remote writes or task-source edits are part of this integration. Root LICENSE, task JSON, workflows and both embodied players remain unchanged.
