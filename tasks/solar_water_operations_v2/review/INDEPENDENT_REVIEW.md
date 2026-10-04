# Independent bounded-design review

DOI: 10.1038/s41893-020-0566-x  
Review date: 4 October 2026

## Decision

Passed for the stated bounded nonbiological physical-design scope. No substantive design blockers remain from this review. This is not approval for physical execution, a complete reproduction of the paper, or a sanitation/potability claim.

Nineteen independent contract tests pass. The author contract suite was independently rerun: 48 tests pass. The current all-route fixture contains 15 jobs and 808 synthetic bookkeeping events. No hardware, actual elapsed physical exposure, scientific measurements, numerical source reproduction, or physics simulation was executed.

## Findings resolved and retested

1. **Material handoff and assembly intake.** Initially, a dependency release could merely hash a child's unrelated inventory. An intermediate revision listed downstream assemblies without admitting their coupons into the assembly batch. Explicit target-bound release manifests now match registered input identities through receipt, assembly service and each downstream route. Assembly operations identify their independent batch carrier, invalidate calibration after the service return, and register/recalibrate the returned setup.
2. **Cross-episode replay.** An actor sequence from episode A initially passed against episode B. Event IDs now incorporate the episode identity; observations and raw receipts retain that identity. The independent replay test rejects the cross-episode sequence.
3. **Bifacial energy-record timing.** Rear-flux acquisition initially preceded illumination configuration and protection checks. It now occurs during the current guarded exposure, with active illumination and current interlocks.
4. **Author test entrypoint.** Direct invocation initially omitted the additional test class. The entrypoint was moved to the end; direct invocation now runs all 48 tests.

## Independent checks

The 19 tests in `review/test_independent_contracts.py` cover:

- Exact parent-release/input identity across every individually selected route and assembly intake coverage
- Service-return recalibration, changed surface-state identity after cleaning, and independent safe-state clearance before retrieval
- Episode-bound evidence, cross-episode replay rejection and rejection of actor-supplied scientific results
- Geometry-matched dark/light records with replacement-water identities
- Active guarded bifacial rear-flux acquisition and separate condensate-versus-evaporation record schemas
- Ten explicit horizontal material/source-condition cases with actual station setpoints unresolved
- Fourteen unresolved source conflicts, including the hour/second and angle-reference discrepancies
- The effective-enthalpy hypothesis remaining separate from a scientific truth score
- Acquisition time separated from slowed video playback, unresolved geometry/equipment values, and rejection of excluded/unknown branches

Run the independent suite with:

`PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s review -p 'test_independent_contracts.py' -v`

## Source-grounding review

The supplied source audit was read, together with relevant actual main-paper and written-SI physical text: optical and wetting characterization; transfer-force interpretation; dark mass-loss and enthalpy assumptions; horizontal and orientation-dependent evaporation; bifacial rear illumination; and fixed outdoor geometry. Specific locators are recorded in the accompanying JSON.

This reviewer did not independently repeat the prior audit's complete 55-page visual inspection or video-frame review. The source audit's full-reading claim remains attributed to that audit. No source figures, images, videos, report reproductions or extracted text are part of this review deliverable.

Control fields now distinguish source facts/reported assumptions, authored guards/task labels, and unresolved actual settings; this field-level provenance is retained in receipts. The physical source dimensions used in the controls are literature metadata, with explicit qualification gates. Source hour/second and angle conflicts remain unresolved. Effective enthalpy remains a model-dependent inference assuming equal heat input; equal ambient conditions are not presented as an independent heat-flux measurement. No source outcome is a required success threshold.

## Limits that remain intentional

- All biological operations are excluded. Unknown environmental material and contaminated-water handling are outside this design
- Fabrication and hazardous chemistry remain closed qualified-service boundaries, without operational recipes
- Caller-owned synthetic fixture context is not production authentication or independent physical authority. Actor/evaluator separation is a declared schema boundary, not a deployed access-control system
- Real geometry, calibrated tolerances, force/exposure limits, current station qualifications, material acceptance criteria and hardware adapters remain unresolved
- Synthetic ordering/receipt checks do not establish scientific reproducibility, independent replicate uncertainty, mechanism validity, contaminant removal, disinfection, or drinking-water safety
- The final export allowlist and its digest require a separate freeze check. No publication was performed in this review

The accompanying JSON binds the reviewed substantive files by SHA-256. Subsequent substantive edits require rerunning the relevant tests.
