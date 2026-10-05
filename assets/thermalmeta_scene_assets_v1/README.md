# Thermal meta-device service-boundary scene

Original paired ScienceGym3D assets for Li, Sigmund and Zhang, *Analytical realization of complex thermal meta-devices*, Nature Communications 15, 5527 (2024), DOI [10.1038/s41467-024-49630-1](https://doi.org/10.1038/s41467-024-49630-1).

This is an editable, static training/review design. It is not a scientific reproduction, thermal solver, live robot controller or approved experiment. Default state is **HOLD_UNQUALIFIED**. All real fabrication, casting, thermal/wet/electrical work stays inside closed qualified-service boundaries.

## Contents

- `geometry/thermalmeta_lab.blend`: natively compressed editable Blender scene with fonts, materials, mesh parts, logical asset groups and 25 canonical evidence anchors
- `geometry/thermalmeta_lab.glb`: portable glTF binary, with mesh text and object metadata
- `previews/`: three genuine Cycles CPU renders, never image-generated or source screenshots
- `scene_binding_contract.json`: exact 20-stage task/scene mapping, A01–A10 groups and all six family/orientation view states
- `scene_guards.py`: side-effect-free, fail-closed static metadata controls; outputs no commands and grants no physical permission
- `contact_contract.json`, `scene_manifest.json`, `review/`: inspectable geometry, support and audit records
- Source-review factual snapshots, attribution and project Apache-2.0 license

Open the Blender file or import the GLB in a standard glTF viewer. The editable scene uses metre units and Z-up coordinates. GLB uses its standard Y-up representation, verified on reimport to Blender. Clear panels use portable alpha blending as an illustrative approximation of the native transparent shader, with no optical-physics claim. A source envelope mesh for every view is exactly nominal 0.12 × 0.12 × 0.0045 m, within floating-point tolerance. Carrier dimensions, fixture shapes, robot links, grasp datums and clearances are independently authored illustrations and **not qualified physical interfaces**. Even nominal source dimensions have no supplied manufacturing tolerances.

## Scientific and identity boundaries

Three clear semantic families appear as original flower, four-lobed and heart silhouettes. Their outlines, contour decoration and layout were authored without tracing publisher art, CAD or source masks. They do not encode a qualified transformation-thermotics geometry. X and Y are separately labeled condition views of the same synthetic specimen identity per family, not six independent specimens or an n=6 result. Source physical replication counts remain unknown.

The source reports profiles along the imposed direction for cloak and concentrator and transverse for rotator. Numbering K1/R1/C1 for X and K2/R2/C2 for Y is an **authored visual selector**, not a verified source label-to-orientation pairing. The condition frame and profile-direction relation are explicit in the binding contract.

All arrows are static orientation labels. There are no heat maps, numerical heat-flow telemetry, measured temperatures, acquired datasets or simulated physical outputs. Reported source targets, 37 °C context and a 45-minute waiting interval are not commands, safe-release criteria or performance thresholds.

Open source issues remain held: metric 2-norm versus squared ratio; mapping residual index; cloak feature label 3.0 versus curve endpoint 2.5; physical-unit and absolute-flux scaling; plus the accepted review's label, iteration and boundary-condition cautions. No solver or source arrays were used. Blank analysis panels are intentionally blank of data.

## Service custody and static controls

P01–P20 retain source-review stage IDs. Service stages are request/receipt metadata interfaces only. A failed or aborted run does not release custody. Retrieval, orientation change, reseating, storage and disposal require independently evidenced zero energy, cool/dry state, supported carrier and accepted custody. Scene icons, elapsed time, a stop request or a complete-looking JSON object do not establish real safety.

To inspect a metadata request locally, pipe a JSON object with stage_id, anchor_id, action and optional evidence into `python3 scene_guards.py`. Allowed actions are inspect_geometry, inspect_condition, register_evidence and propose_service_request. Unknown fields and physical-action requests are rejected. Proposing a service request returns a hold; it dispatches nothing. This code performs schema/identity checks only, not receipt authentication.

Run `python3 -m unittest discover -s tests -v` for authored hostile guard tests. The separate independent checks are in `review/`; their public reports state the exact scope. To regenerate original geometry and CPU previews with Blender 4.3, run `blender -b --python geometry/build_scene.py`, then `python3 sanitize_previews.py`. The build invokes both the full fixed-buffer native sanitizer and the portable clear-panel normalization helper automatically. The native sanitizer requires Python zstandard. Sanitization never resaves the cleaned file through Blender: a later native save can reintroduce UI history and must be sanitized again. Run Blender in background with `geometry/verify_scene.py` to reopen the native file, verify the six source envelopes and static support contacts, and reimport the GLB to compare canonical anchor positions and metadata. All fit, load, grasp, motion and hazard-zone qualification remains outside these tests.

## Rights and export

Original project code, procedural geometry, material definitions, labels and renders follow the existing project Apache-2.0 license. See `LICENSES/ATTRIBUTION.md` for separate source attribution. No publisher source files, scientific code, source CAD, figures, arrays or movie frames are distributed, and publisher material is never relicensed here. The sanitized export includes only its explicit allowlist. No GitHub write was performed.

## Strict native metadata cleanup

The final native file has passed schema-sized inspection of all 21,306 fixed character buffers (61 inspected string-field classes), including complete post-NUL padding. All 47 path-related/UI asset-selector buffers have approved empty, built-in or intentional relative values with zero padding. Unused UI paths/search selectors were cleared. The original CPU preview pixels remain unchanged; the public sanitation record proves exact equality outside approved string buffers and preservation of all non-UI active strings. The independent follow-up establishes deep scene equivalence, so this metadata-only correction does not claim a new render or scientific execution.
