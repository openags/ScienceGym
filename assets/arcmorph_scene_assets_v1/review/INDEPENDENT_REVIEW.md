# Independent Arc-Morph asset review

Reviewed 4 October 2026. **PASS_WITH_EXPLICIT_STATIC_SCOPE**

## Decision and scope

The current files pass review as an original static scene/interface prototype, with explicit physical and scientific execution holds. This is not approval of a working robot task, fabricated specimen, folding model, metrology system or reproduction of the paper. No public ZIP was reviewed in this report.

## Independently verified

- Native Blender file reopened with Blender 4.3.2: 38/38 checks pass
- GLB parsed and imported into a fresh Blender scene: 18/18 checks pass
- 104 unique semantic/package test methods pass, including 13 independently authored adversarial methods
- Exact A01–A12 roots, R00–R30 bindings, 62 primary/control anchors and four contextual fixture anchors resolve
- All 20 native family/state combinations have 24 panels and 38 identified interior creases, correct shared-edge adjacency and a connected panel graph; the GLB retains five default states
- 48 native text objects remain editable; GLB lettering is portable mesh geometry
- Source requirement/fact snapshots are byte-identical to the accepted inputs
- All three 1920 × 1280 PNGs were opened and their actual pixels inspected; post-sanitization hashes match the render receipt

The native contains 1725 objects and 1593 meshes. GLB reimport contains 780 objects, 702 meshes and 15 visual materials. No image textures, external mesh libraries, embedded scripts, drivers, rigid-body world or deformable-physics modifiers were found.

## Review findings and repairs

R26/R27 initially selected the corner-loading base. They now use the separate rigid-demo support. The paired contract review also refined the released-output R06 target and quantitative R13 fixture scope. Primary/control anchors and asset memberships now agree across scene and metadata.

Initial metadata used stale world matrices for newly created anchors and hidden alternate-state objects. Those objects are now evaluated before inventory and surface-bound capture. The independent verifier reveals hidden collections only in memory to measure them; it does not save changes. The native retains the intended hidden defaults.

Adversarial checks initially accepted missing attachment/job identity, a corner mount for quantitative capture, reused lens identity, changed prepared qualification/dimensional identity, or truthy unknown support. The repaired controls reject these cases. The tests retain positive synthetic examples and explicit numeric/identity/history guards. This remains a record-consistency model, not security isolation or evidence authentication.

## Units, dimensions and source limits

Native units and exported geometry use metres. The authored PP generator spans are 420 × 360 mm; the actual default panel-surface extent is about 425.5 × 384 × 40 mm. The 40 mm is authored embedding height, not sheet thickness. Source width 428.78 mm and nominal sheet thickness 1 mm remain separately labeled. Cardstock thickness 0.35 mm is authored.

C01 remains unresolved: Methods 383.63 mm versus figure 383.65 mm. Separate geometric reference bars retain both lengths and forbid fabrication use. No source value is silently selected. PP1 maps to task family PP. The five displayed design roles and their alternatives do not imply five independent experimental specimens.

## Pixel and provenance review

The overview shows the whole original scene and prominent scope warning. The handling image exposes carriers, gripper, folding support and all five representative templates. The metrology image shows the empty fixture, sliders/plates/spacers, two rulers, target and distinct front/side camera housings. Their geometric viewing directions are orthogonal, but this establishes no optical calibration.

The images are coherent, visibly path-traced studio renders. Moderate sample noise remains. No missing-texture artifact or copied publisher artwork was apparent. Procedural build inspection and texture/library checks support the declared original provenance; they cannot prove every aspect of prior authoring history. Apache-2.0 and the Blender-font notice are included, with publisher rights kept separate.

## Retained holds

- Representative panel graphs are not source-pattern reconstructions or validated rigid-fold solutions; non-planar quads and static damage cues remain illustrative
- No qualified grasps, collisions, robot trajectories, fabrication/load safety, live device control or scientific oracle
- No measured image pair, uncertainty-qualified calibration, source raw-archive review or physical experiment
- Default-state screenshots do not show every hidden alternative; those 15 alternatives were reopened and checked geometrically
- Packaging and public archive validation must be completed separately

Machine-readable details and artifact hashes are in independent_review.json; native and GLB results are in native_verification.json and glb_import_verification.json.
