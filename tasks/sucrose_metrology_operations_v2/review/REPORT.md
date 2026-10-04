# Independent sucrose metrology contract review

**PASS for the bounded task contract. No blocking task-package finding.**

This review covers seven original nonbiological branches, three fixed optical profiles, synthetic record validation, static interface metadata and a 39-file original-text export. It does not approve physical work, authenticate instrument receipts, implement PCA, validate optical physics, establish numerical performance, or complete the source paper.

## Independently rerun evidence

- All 17 author test methods passed, with the static package and fixed export checks passing
- An independently authored adversarial runner passed 5,871 positive traces: every ordered nonempty selection of the six non-hold branches across all three profiles, plus the three profile-specific hold fixtures
- All 887 independent negative cases were rejected. Coverage includes missing/replayed/reordered events, actor observation injection, cross-profile and cross-episode registries, parent-bottle/aliquot/reference/run/mount/calibration lineage, missing qualification cards, typed state substitutions, tare/mass/mixing/filter/custody receipt failures, stale clamp/exchange/frame receipts, unsupported reference freshness, nonfinite/out-of-domain values, test leakage, dark-channel substitution, source-flow authority escalation, unsafe teardown and scientific-claim inflation
- All 46 independent export cases passed their expected outcomes, including the pristine baseline, deletion of every listed file, unlisted files, unexpected directories, symlinks, self-consistently listed forbidden source extensions, machine paths and nonfinite JSON

The independent runner is review/adversarial_review.py after integration. These tests validate the authored contract, not observations from a real laboratory.

## Source fidelity and source-completeness boundaries

The reviewer checked the source packet's access ledger against the publisher article, the 18-page SI text and its three page-contact sheets. The packet distinguishes written-source coverage from unavailable raw-data replay. The required source basis remains the article and SI, not a title/abstract-only conversion. Cited papers, the underlying dataset, native hardware/CAD and main figures 2-4 pixels are not claimed independently inspected. No equations were independently rederived and no numerical plot digitization was performed.

The source [article](https://www.nature.com/articles/s41467-026-72281-3) supports the aqueous preparation, renewed reference measurements, distinct imaging roles, interpolation and precision interpretation used here. Its two incompatible flow descriptions remain unresolved. The [SI](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-72281-3/MediaObjects/41467_2026_72281_MOESM1_ESM.pdf) supports treating wavelength-dependent bias, environmental drift and repeatability separately. Neither supplies the missing qualifications needed for the proposed physical services. The reduced synthetic sampling schedule is plainly authored, rather than represented as a replication of the paper's schedule.

The review confirms that the task retains all eight annotated source conflicts. The source's CC BY-NC-ND license is recorded. Inspected task payloads contain original prose, JSON and code, without publisher PDFs, images, extracted full text, adapted artwork or numerical source datasets. This is an inspection of the delivered content, not a global plagiarism search or a legal opinion.

## Contract meaning and limits

The default fixture is held and has no service clearance. Measurement fixtures set production authority and physical execution to false, retain the unresolved flow conflict and use only a logical fixture service receipt. Numeric pump commands are absent. A passing fixture cannot authorize or demonstrate physical fluid exchange.

The validator is deliberately closed-world: it checks against an authored canonical episode. It validates that exact synthetic trace, and rejects noncanonical values even when another value might be physically plausible. It is not a general laboratory-data validator. The caller supplies evaluator-side observations; possession of that interface is not production authentication. Replay/order rejection is within a submitted trace, not a persistent cross-invocation replay ledger. These limits must remain visible in downstream use.

Preparation, reference, calibration and dependent acquisition share immutable synthetic identity links. The task requires a current clamp command followed by an independent observation before each switch. Transfer clears prior flow/bubble clearance, and acquisition requires the new exchange and bubble receipts. Calibration is train-only, profile-local and invalidated before final retrieval. Dark records remain a distinct channel, and no precision result becomes an accuracy claim or pass threshold.

## Paired assets

The task binding plan and paired scene snapshot match byte-for-byte: 37 operation IDs, six groups and 31 anchors. No task interface or geometry change is needed for this review.

Two separate paired-scene gaps were identified: reuse of a clamp observation after switching (ASSET-CLAMP-REPLAY), and switching while undocked. The builder corrected the implemented metadata guard to require a docked cartridge and a fresh, one-use clamp-command/observation cycle. Independent recheck passed all 19 targeted conditions, and all 38 scene-package test methods passed. A complete new cycle permits the next metadata switch and clears the prior reference; repeat use, direct re-verification, command-only transfer and stale observations after undock/redock are blocked. Pump and physical acquisition remain blocked. These checks cover this implemented subset, not equivalence to the complete task evaluator. Approval of the newly frozen scene archive remains the separate scene review responsibility.

## Integration requirement

The original report, machine-readable audit and independent runner were authored outside the task packet before integration. After replacing pending review placeholders and updating status, the author must regenerate the exact allowlist hashes and rerun author, independent, static and export checks. A future payload change needs review proportional to its scope. The scene archive must retain the corrected guard and the separate scene reviewer must verify its new archive hash.
