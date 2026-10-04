# Arc-Morph: original representative robot-laboratory assets

This package contains 12 original asset groups, five representative design families, 31 source-route operation bindings, an editable Blender scene, a portable GLB, and three genuine CPU path-traced images. It is an authored static asset and interface prototype. It does not reproduce the paper's specimen geometry or validate physical folding, robot motions, metrology, scientific outcomes, or equipment safety.

## Source and originality

Factual roles are taken from McInerney et al., *Coarse-grained fundamental forms for characterizing isometries of trapezoid-based origami metamaterials*, Nature Communications 16, 1823 (2025), DOI [10.1038/s41467-025-57089-x](https://www.nature.com/articles/s41467-025-57089-x). The accepted review read the main article and written supplement; this authoring consumes that review. The underlying 728.4 MB archive, raw images and code were not inspected. No publisher figure, traced pattern, photograph, CAD or original source code is included.

The four cardstock family roles are Arc-Miura, extended Arc-Miura, Archimedean spiral and lemniscate. Their CS1–CS4 meshes are deliberately original representative panel/crease embeddings, not replicas or mathematically established rigid-fold solutions. PP1 is an original polypropylene-role template and maps to task family PP. The five displayed design exemplars and their static alternatives do not assert experimental sample counts.

## What is delivered

- A01 records and allocation console
- A02 separate stock identities and supported pickup
- A03 retained flat/folded carriers and illustrative robotic gripper
- A04 closed fabrication role, dual-purpose input/safe-output inspection dock, job/receipt-token slot and reject compartment
- A05 five family exemplars with explicit panel/crease IDs; four static states per family
- A06 broad-support folding bench, removable support and rounded tool
- A07 rigid fixture: 3 sample sliders, 2 plate sliders, 2 L-shaped plates, PMMA-role spacers and 2 mm nominal bolt references
- A08 frontal camera and A09 independent lateral camera
- A10 two independent rulers, tape, authored checkerboard and separate source dimension references
- A11 guarded qualitative corner fixture plus separate benign rigid-demo support
- A12 rest inspection and quarantine with history-preserving semantics

The native scene keeps editable text and 20 static specimen-state assemblies. Only the illustrative-folded state is shown initially; alternate collections are named STATIC_VARIANT.<family>.<state>, hidden by default. They can be inspected by revealing one collection and hiding that family's default state. These snapshots are independently generated embeddings, not a folding animation or trajectory. The damaged example is a visual cue, not a damage detector. The qualified state is unavailable until external qualification.

geometry/arcmorph_lab.glb contains the default display, with text converted to meshes; hidden alternative specimen states stay in the editable native file. It intentionally excludes render cameras/lights, the infinite studio floor and disabled collision proxies. The three images in evidence are studio renderings: overview, handling and metrology. They are not front/side scientific captures or source raw data.

## Dimensions and holds

Scene units are metres. Equipment sizes, spatial layout, grips, supports, crease geometry and contact clearances are original nominal design choices. All physical-qualified poses are null. The authored PP generator uses nominal width/depth inputs of 420 × 360 mm, with nominal 1 mm sheet thickness. The deliberately warped representative surface has different actual X/Y bounds, recorded in specimen_topology.json; these are not a fabrication footprint. Cardstock thickness is an authored 0.35 mm; width/depth generator inputs are recorded in asset_metadata.json, and actual representative surface bounds in specimen_topology.json.

Source-known values remain separate: PP reported width 428.78 mm, nominal thickness 1 mm, nominal bolt diameter 2 mm. The source's 383.63 mm Methods versus 383.65 mm Fig.4A length is unresolved conflict C01. Separate dimension-reference bars preserve both readings; neither is selected as a fabrication dimension. Factual dimensions do not supply missing tolerances or a qualified physical drawing. The source analytical example parameters do not seed these physical templates.

## Interaction and evidence contract

Roots ASSET.A01–ASSET.A12 and ANCHOR.R00.primary/control through ANCHOR.R30.primary/control are stable selectors. R06 remains at the fabrication dock after a trusted safe-release receipt; its selector does not move custody to the later rest station. Additional fixture-specific release anchors distinguish corner loading from the qualitative rigid support. operation_bindings.json lists exact target meshes. Affordances name broad carrier contact candidates, tool handles, optics and specimen exclusions, and unqualified hidden AABB proxies. No anchor, label, visible grip or guard is permission to act physically.

semantic_controls.py is a pure in-memory authored guard model. Its tests exercise qualified-input holds, per-edge completion records, C01 handling, exclusive mount leases, loaded-transport rejection, calibration revisions, paired-record scope, separate release branches, history retention and closeout. Passing these tests proves only the implemented semantic checks. It does not prove real controller isolation, trusted receipts, actual images, safe robot motion or physical observation truth.

All guards require external qualified inputs and real evidence before a future runtime could act. The native scene has no rigid-body or cloth world, motors, joint physics, device I/O, motion drivers or folded-state solver. Visible scales and orthogonal camera-role housings do not establish calibrated optics. No loading magnitude, settling threshold, measurement tolerance or recovery interval is invented. Qualitative shear remains qualitative; eight source rigid configurations are not eight independent specimens.

## Rebuild and inspect

Run Blender 4.3 or newer: blender --background --threads 8 --python geometry/build_scene.py. Outputs resolve relative to the package. --no-render rebuilds geometry only. Run Python tests with python3 -m unittest discover -s tests. Native and GLB review scripts are in tests; actual reopening/import results and the independent review are in review. Build and review logs, local backups and Python caches are excluded from the public archive.

Original geometry and authoring code are Apache-2.0. Blender's font notice is included for text converted into portable geometry. See LICENSES/ATTRIBUTION.md. Shared conventions from the earlier original wetting laboratory package informed the packaging and disabled-affordance scheme; no external mesh was reused.
