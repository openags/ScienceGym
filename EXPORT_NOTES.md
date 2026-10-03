# Public task-specification export

This note describes the original seven-package export. Later standalone-presentation wording updates do not refresh its historical EXPORT_MANIFEST.json receipt; use the root README and current release checks for the expanded repository.

ScienceGym develops long-horizon robot experimental task families from scientific papers. The core artifacts here are task goals, operation sequences, dependencies, object lineage, controls, evaluator references, recovery rules, and explicitly unresolved source requirements. This snapshot records laboratory scene and asset interfaces; the supporting scene and asset implementations are not bundled.

## Included

Seven authored task-design packages: chiral metamaterials, microscopy (Deconwolf), semiconductor fibres, thermoelectric devices, diSPIM microscopy, helical acoustic metamaterials, and perovskite solar modules. These are paper-grounded design specifications and semantic/mock contracts. They are not seven runnable environments, physical robot trials, complete experimental reproductions, or a certified benchmark release. Public evaluator files are reference specifications; a future evaluation harness must keep them separate from agent-facing input.

## Deliberately absent

- Publisher main text, supplements, extracted full text, original videos, source screenshots, manufacturer CAD, source datasets and credentials
- Editable source scene/model binaries, physics engines, robot controllers, prior demo bundles and manuscript drafts; the logical viewer and rendered R01 storyboard are included
- Original delivery allowlists and historical check reports whose hashes or asset-availability checks referred to the complete authoring workspace

Paths into scenes/, assets/, research/, materials_routes/ and other absent directories describe supporting artifacts from the original workspace. They are not provided by this snapshot and are not automatically downloaded. A successful export-integrity check does not establish that these dependencies exist.

## Provenance and transformations

DOIs, public source URLs, source-page/figure locators, original-source SHA-256 values, source-reported facts, authored assumptions, unknowns, and task semantics are retained. Original machine-root prefixes have been replaced with source-archive:/// or asset-archive:/// locator schemes. These schemes deliberately do not resolve to a server or local directory. Their remaining path components identify the historical archive layout without naming a current machine. Obtain any needed originals separately from lawful cited sources and verify their pinned bytes; do not treat a locator as a bundled file.

The task-design documents carry an explicit export-scope notice. The microscopy README clarifies that referenced models are absent. One internal Git-delivery flag has been removed. Scientific provenance and unknown-parameter records remain unchanged apart from locator replacement.

Source-file hashes and preserved-draft hashes inside task provenance refer to historical source bytes. EXPORT_MANIFEST.json contains the current hashes for this public snapshot. It lists all files covered by this snapshot explicitly, including the README and LICENSE. The manifest cannot hash itself. No original-source archive or private development history is included in these files. The repository retains its existing public Git history.

## Verification

Run python3 scripts/verify_export.py from any directory using Python 3.9+. It checks only the files listed in EXPORT_MANIFEST.json, their size/SHA-256 values, JSON syntax, and absence of machine-root paths in that manifest scope. It does not run task contracts, robots, simulators, biological or material experiments, source-byte retrieval, or scientific validation.

## Rights

This snapshot contains authored descriptions and factual source locators, not the cited publications or publisher media. Third-party publications and omitted assets retain their own terms. An article's license is not a license for the entire repository. The thermoelectric package records a CC BY-NC-ND source and limits its included reuse to newly authored factual task descriptions. The project retains its original Apache-2.0 LICENSE. That license does not relicense third-party sources or establish third-party rights clearance.

## English edition

Task narratives and structured descriptions have been translated into English. Task IDs, source identifiers, numeric values and source-versus-authored distinctions are preserved. The microscopy guide is now GUIDE.md. English-only checking detects CJK text and decoded JSON values; it does not certify scientific or translation accuracy.

The diSPIM and acoustic English schemas rename language-tagged descriptive keys from `_zh` to `_en`; this is an explicit schema change, not a change to task/evidence identifiers or numeric values.

The embodied R01 visual package includes authored task illustrations and licensed G1 model renders, with a separate retained model notice. These additions do not include publisher source media or real robot execution. The perovskite package is a task-design reference without a corresponding visual environment in this snapshot.
