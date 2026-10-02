# Public task-specification export

ScienceGym develops long-horizon robot experimental task families from scientific papers. The core artifacts here are task goals, operation sequences, dependencies, object lineage, controls, evaluator references, recovery rules, and explicitly unresolved source requirements. Scene and asset reconstruction belongs to Hooke; this snapshot records interfaces to those supporting artifacts rather than bundling them.

## Included

Four authored task-design packages: chiral metamaterials, microscopy (Deconwolf), semiconductor fibres, and thermoelectric device work. These are paper-grounded design specifications and semantic/mock contracts. They are not four runnable environments, physical robot trials, complete experimental reproductions, or a certified benchmark release. Public evaluator files are reference specifications; a future evaluation harness must keep them separate from agent-facing input.

## Deliberately absent

- Publisher main text, supplements, extracted full text, original videos, source screenshots, manufacturer CAD, source datasets and credentials
- Scene/asset binaries, static viewers, simulator dependencies, controllers, prior demo bundles and manuscript drafts
- Original delivery allowlists and historical check reports whose hashes or asset-availability checks referred to the complete authoring workspace

Paths into scenes/, assets/, research/, materials_routes/ and other absent directories describe supporting artifacts from the original workspace. They are not provided by this snapshot and are not automatically downloaded. A successful export-integrity check does not establish that these dependencies exist.

## Provenance and transformations

DOIs, public source URLs, source-page/figure locators, original-source SHA-256 values, source-reported facts, authored assumptions, unknowns, and task semantics are retained. Original machine-root prefixes have been replaced with source-archive:/// or asset-archive:/// locator schemes. These schemes deliberately do not resolve to a server or local directory. Their remaining path components identify the historical archive layout without naming a current machine. Obtain any needed originals separately from lawful cited sources and verify their pinned bytes; do not treat a locator as a bundled file.

The four main task-design documents carry an explicit export-scope notice. The microscopy README clarifies that referenced models are absent. One internal Git-delivery flag has been removed. Scientific provenance and unknown-parameter records remain unchanged apart from locator replacement.

Source-file hashes and preserved-draft hashes inside task provenance refer to historical source bytes. EXPORT_MANIFEST.json contains the current hashes for this public snapshot. It lists covered files explicitly and does not claim coverage of a repository README or other files added later. The manifest cannot hash itself. No local Git history or original-source archive is included.

## Verification

Run python3 scripts/verify_export.py from any directory using Python 3.9+. It checks only the files listed in EXPORT_MANIFEST.json, their size/SHA-256 values, JSON syntax, and absence of machine-root paths in that manifest scope. It does not run task contracts, robots, simulators, biological or material experiments, source-byte retrieval, or scientific validation.

## Rights

This snapshot contains authored descriptions and factual source locators, not the cited publications or publisher media. Third-party publications and omitted assets retain their own terms. An article's license is not a license for the entire repository. The thermoelectric package records a CC BY-NC-ND source and limits its included reuse to newly authored factual task descriptions. No blanket license or third-party rights clearance is asserted by this export.
