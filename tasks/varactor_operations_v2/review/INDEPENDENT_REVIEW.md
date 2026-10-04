# Independent task-contract review

Verdict: PASS for original whole-available-paper DESIGN and bounded offline contracts only. No known open blocker remains in the reviewed design or implementation. This release contributes zero validated runnable whole-paper tasks.

## What was reviewed

The reviewer inspected the source handoff, evidence/route/conflict/parameter ledgers, complete extracted main scientific text and all three Methods subsections, the supplied supplementary text, and SI pages 3 and 5 as images. Complete main/SI visual coverage relies on the separately supplied source-auditor record. This reviewer does not independently claim inspection of every main figure pixel.

The design has 28 routes, 80 operation IDs, 12 asset groups, 65 anchors and 49 evidence locators. Its families represent STO/KTO fabrication; CNT SQD/DQD preparation; assembly; cryogenic and RF calibration; fixed-load characterization; reflection, loss and model studies; SQD and DQD readout; field checks; hysteresis; stability; and authored safe closure, custody and cleanup. All 12 source conflicts and interpretation limits are retained. References and future projections do not become additional performed experiments.

## Findings fixed and retested

- IR01: One physical STO varactor pair is now explicitly shared across SQD/DQD reconfiguration. Device, module, circuit and calibration revisions change; prior sweep history persists. Replacement IDs or stale calibration are rejected
- IR02: The repeated 215 MHz KTO tick is preserved separately from the SI Figure 4 absent-panel conflict. It cannot supply an exact lower frequency boundary
- IR03: Metadata-only circuit cards preserve SQD/DQD bias-tee values, substrate classes, model inductance versus part code, and DQD-only series capacitance/JPA. Circuit substitutions are rejected
- IR04: Phase classification now requires nonempty string calibration IDs. Equal null, empty, boolean, numeric or container values cannot establish current phase lineage
- IR05: Numeric underflow cannot silently produce zero capacitance/sensitivity, and invalid derived arithmetic is rejected consistently
- IR06: JPA pairs now bind carrier/acquisition plans, comparison region and baseline in addition to device, transition, calibration-related and history fields
- IR07: Manifest freezing rejects a symlink destination before writing. The external target remains unchanged
- IR08: ZIP creation rejects symlink destinations and linked ancestors before opening output
- IR09: An invalid extra-file tree is rejected before an existing manifest can be rewritten
- IR10: Unlisted empty directories are rejected; only allowlist-derived directories are accepted

- IR11: Field and dual-frequency scans now retain the SQD-circuit context of Figure 4, current baseline and CNT_SQD preparation ancestry, with complex-reflection/phase mode and no charge-sensitivity credit
- IR12: Assembly-only fixtures consume verified prepared ancestry before die attachment and receive no raw-fabrication credit
- IR13: STO/KTO comparison bundles now contain distinct, consistent specimen/material identities through fabrication or prepared ancestry and raw comparison records. A self-rehashed constituent-collision mutation is rejected

## Verification results

All 59 independent tests pass: 38 source/design/runtime/card tests and 21 export tests. The independent run also passed all 54 author contract tests and the structural verifier. All 160 registered finite fixtures were checked while asserting that physical execution, scientific reproduction, whole-campaign completion and production authentication remain false.

Negative coverage includes actor-injected values, forged/self-rehashed registries, revision substitution, replay, missing or reordered occurrences, prepared-input fabrication credit, held/damaged closure, stale phase, mismatched JPA pairs, changed shared specimens, circuit substitution, invalid numeric/unit/bandwidth inputs, mismatched hysteresis coordinates, incomplete/reversed time series, hash and path mutations, injected files, symlinks, special files, ZIP duplicates, oversized/empty entries, binary payloads and private-path payloads. Symlink negatives verify that protected outside sentinels were not modified.

The exact allowlist contains 45 members including its manifest. The JSON review records hashes of the reviewed implementation and independent tests. The exact final release directory and ZIP still require their own verifier run after manifest freeze; any later edit requires refreeze and rerun. This design/code review cannot substitute for that final artifact gate.

## Interpretation limits

The evaluator accepts finite public synthetic fixtures, not authenticated laboratory evidence. A generic receipt or arithmetic example does not demonstrate a measurement, service qualification, whole campaign, circuit fit or scientific reproduction. Physical processes, robot operation, exact contact/geometry, the full circuit solver, finite-element inversion, source-data reproduction and real uncertainty qualification remain unimplemented.

Source results are reference context, never task-success constants. Main/SI pages, source art, author code, author CAD and private acquisition paths are excluded. Scientific source license and patent rights remain distinct. Whole-available-paper DESIGN coverage does not create whole-paper execution credit.
