# Verification: nine-family task explorer

Updated 2026-10-03. Source task files are pinned to public ScienceGym commit `293e32da790303c1a17131e036235f69a5f342e0`.

## Checks performed

- **68 Python tests pass with zero skips**, with `SCIENCEGYM_TASKS` explicitly bound to this checkout. The 21 independent EmVP viewer regressions cover exact operation/configuration/dependency/context/evidence mapping, per-condition route and gate fidelity, null input counts, absent fields, comparison dimensions, no SVG adjacency arrows and malformed-dispatch rejection
- Earlier-eight-family semantic fingerprints match exactly. All 32 earlier generated JSON, JavaScript, SVG and Markdown files differ from the starting checkout only by full/short source commit pin replacements
- Mocked-DOM tests cover all **191 routes/configurations and 10,062 displayed operation/template occurrences**, including every EmVP configuration, repeated cage operation selection, immutable data under repeated clicks, search, tabs, source evidence, conditional dependencies and malformed hashes
- EmVP membership views and all 19 generated configuration SVGs have **no inferred chronological adjacency arrows**. The dependency view retains 44 source template edges and six explicitly conditional groups containing 25 edges, plus the instantiation and per-occurrence rules. No condition-specific edge is silently promoted to an unconditional rule
- The same mocked-DOM suite passes against exported single-file HTML; no browser or real DOM is involved
- Full rebuild and `--only emvp` rebuild are byte-identical, including the complete nine-family manifest and release checksums. Release-manifest inventory, sizes and SHA-256 values are tested
- The EmVP default, mixed-cage and printed-hardness SVGs were rendered with Inkscape and their actual pixels inspected. All 19 configuration labels, separate cage conditions, absence of adjacency arrows and unknown-count/within-specimen labels are preserved. Default and hardness outputs are 1440 × 2320 pixels; the complete cage view is 1440 × 5664 pixels. These are static diagram renders, not browser screenshots
- Repository-root `scripts/verify_release.py` passes all **9/9 static check groups**, including verifier regressions, English hygiene, JavaScript syntax, both existing embodied-player mocked-DOM suites and all **220 image-hash assertions** over 71 frames / 75 unique images
- The unchanged EmVP package's contract suite passes **44 public tests**. Its one optional external primary-source-byte check is explicitly skipped in this integration run because no source cache was supplied; the published package records its earlier full-source verification separately
- All 283 protected task, embodied-player/image and LICENSE files are byte-identical to the integration input. No full source packet, paper image or third-party asset is added

## Representation counts

Nine paper families, **191 route/configuration records and 1,320 operation definitions**. EmVP adds **19 configurations, 53 reusable templates, five practical families, 15 comparison packages and 30 unresolved input gates**. Its **482 displayed template occurrences** include separately displayed cage condition routes. These are display positions, not executed repetitions, acquisition events, independent specimens or successes.

Prismatic retains 12 configurations, 49 templates, seven practical families, source-declared nested coverage and independent campaign dispatch. Earlier family loop and navigation semantics are unchanged. Unknown cardinalities stay unresolved; no unknown loop is expanded into invented iterations or successful empty work.

## Scope and verification limits

This is a read-only author/evaluator logical inspector of published task-design contracts. It does not implement an actor projection, loader, evaluator execution, physical simulation, scientific solver, new 3D storyboard or robot controller. It does not certify scientific correctness, practical safety, reproduction or feasibility.

Actual browser file/localhost access was previously denied. No retry, alternative browser, hosting route or security change was attempted. Real-browser rendering, responsive/touch layout, focus and browser Back/Forward behavior remain unverified. Mock hash-change tests and static SVG pixel inspection do not establish browser interaction coverage. The added navigation scrolling and statistics wrapping are statically inspected CSS, not browser-tested layout.

## Reproduction

Run from the repository root:

```sh
python3 -B viewer/task_explorer_v1/build.py --tasks tasks
SCIENCEGYM_TASKS=tasks python3 -B -m unittest discover -s viewer/task_explorer_v1/tests -v
node --check viewer/task_explorer_v1/app.js
node viewer/task_explorer_v1/tests/test_app.js
python3 -B scripts/verify_release.py
```

For optional single-file export and task-package checks, supply output paths outside the repository:

```sh
python3 -B viewer/task_explorer_v1/export_standalone.py --output /path/to/scratch/ScienceGym-Task-Explorer.html
node viewer/task_explorer_v1/tests/test_app.js /path/to/scratch/ScienceGym-Task-Explorer.html
python3 -B tasks/emvp_operations_v2/tests/run_validation.py --report-dir /path/to/scratch/emvp-validation
```

Static SVG pixel inspection uses Inkscape's CLI exporter, not a browser. No remote writes or task-source edits are part of this integration. Root LICENSE, task JSON, workflows and both embodied players remain unchanged.
