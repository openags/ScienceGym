# Independent review: actuator static scene assets

**Verdict: PASS for static content and explicit export policy. No remaining content blocker.**

Reviewed 4 October 2026. Package: `actuator_scene_assets_v1`; paired interface: `actuator_metrology_operations_v2`; source DOI: [10.1038/s41467-020-17947-2](https://www.nature.com/articles/s41467-020-17947-2).

This review inspects actual files and pixels independently of the builder's receipts. It does not qualify physical execution, fabrication, calibration, simulation, scientific results, licensing or patent status. Exact reviewed payload hashes are in `INDEPENDENT_REVIEW.json`.

## Evidence and results

- Opened all three actual 1600 × 1100 PNGs. The overview exposes the static apparatus and direction HOLD; sample handling shows an empty carrier; the measurement view exposes the original generic lattice, visual targets, authored ruler and 5 mm reference. No source image overlays or performance values appear. Some text is cropped or occluded in the close-ups and render grain is visible; combined coverage is adequate for the declared static scope.
- Read the native Blend and independently imported both GLBs in Blender 4.3.2. **691 independent native/GLB/reuse checks passed**. The native file has two disjoint scenes, editable FONT labels, metre-authored geometry, no source textures, linked libraries, embedded scripts, animation, rigid-body mechanics or drivers. Both GLBs have embedded buffers, no images, textures, animation, external URI dependency or required extension. Portable labels are meshes.
- Main and explanatory geometry remain separate. Every lattice component is exactly 10× in the display scene; the native 0.005 m reference becomes 0.050 m. Display typography/furniture are separately authored presentation sizes. These values are geometry units, not a physical calibration. The reference represents a source magnitude only: there is no commanded input, deformation or motion.
- Independently matched **32 operation bindings**, **30 canonical anchors**, and all **47 scene anchors** against the current task binding plan and actual native objects. Bindings are complete visual-role metadata, not functioning service adapters.
- Re-ran **31 standard-library tests**, all passing, and **547 additional adversarial semantic checks**, all passing. Coverage includes malformed identities/types, incomplete/extra cards, direction acknowledgement without reviewed disposition, cross-instance/stale/reused/wrong-context claims, calibration context, image/run identity, repeated lifecycle run reuse, defensive copies, unloading before unfix, and quarantine. Every one of the 32 service names rejects across lifecycle states. Pair manifests emit null displacements and efficiency. Claims remain untrusted caller-owned symbolic markers; these tests establish no real-world truth or authentication.

## Source fidelity and scientific boundaries

Only the specified local source evidence was consulted for figure/method interpretation: main XML/text, SI text/page renders, Fig 2, and Movie 2/3 contact sheets. No evidence file is copied into the deliverable.

The methods support NinjaFlex TPU, nominal 0.4 mm nozzle, the 0.8× layer relation (derived 0.32 mm), fixed bottom holder, caliper-aided 5 mm input, and before/after camera imagery. The scene uses only their generic roles and the labelled static magnitude. Lattice topology, dimensions, extrusion, apparatus shapes, contacts, target locations, optics and robot coordinates are original unqualified choices. No exact source geometry, source algorithm, FEM/DEM/CNN, image acquisition or scientific output is claimed.

The source evidence confirms that main-body Fig 2/SI Fig 3 direction references disagree with captions/arrows, and figure-to-movie pointers disagree with Movie 2/3 content. The SI1/SI3 physical-results pointer and out-of-scope force-panel pointer discrepancies remain separately disclosed. All four conflicts remain unresolved, source-to-scene mapping is null, and direction defaults to HOLD. Selecting a local reviewed branch cannot erase the source conflict. The printed-result angular exponent is not established; task n=2 is a benchmark choice. Source code terms and the disclosed patent application do not establish commercial fabrication clearance; current patent status remains unverified.

## Reuse and publication boundary

The original AFM Blend was opened and its SHA-256 independently matched. All **15 original meshes** were compared to both the extraction and final scene: vertices, faces, relative placement, rotation, scale and modifiers are retained. Root placement and materials are presentation changes. The two reused carrier/clamp families receive **zero new unique-asset credit**. The carrier is empty; physical fit is not asserted. Semantic groups, repeated cells, labels, renders and exports do not count as independent new assets.

The package records Apache-2.0 original work, article attribution with third-party exceptions, and Blender font provenance. This is a disclosure/provenance check, not a legal opinion. No source-file hash occurs among the export payload; code inspection and native/GLB dependency inspection find no copied source code, figure geometry, textures or embedded research pixels. The original generic diamond lattice visibly differs from the paper's human/machine structures.

The 36-name allowlist excludes source evidence, logs, caches and Blender backups. The initial first-freeze manifest bootstrap defect was reported and fixed. An isolated exporter smoke test passed first-run manifest creation, byte-identical repeat output, exact 36-member boundary, ZIP CRC, all 35 manifest entries and symlink rejection.

## Freeze boundary

This review approves the reviewed content and export policy before final freezing. Because the ZIP embeds these review files, the final ZIP's checksum, exact member set, manifest and byte equality are verified separately after freeze, without altering this embedded report. Final release still requires that post-freeze check. Any changed reviewed payload hash invalidates the corresponding content approval and requires re-review.
