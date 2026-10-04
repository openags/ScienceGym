# Actuator metrology static laboratory

Original editable scene for the [Automatic design of mechanical metamaterial actuators](https://www.nature.com/articles/s41467-020-17947-2) workflow, synchronized to `actuator_metrology_operations_v2`. The scene contains a generic diamond lattice, fixed holder, parked displacement stage, camera, ruler, visual target markers, empty carrier, closed fabrication service, records console and source-conflict hold panel.

## Deliverables

- `geometry/actuator_metrology_lab.blend`: two editable scenes with native FONT labels
- `geometry/actuator_metrology_lab.glb`: metre-authored generic apparatus with seven stable semantic asset groups
- `geometry/actuator_measurement_display.glb`: a separate 10× explanatory lattice and 5 mm reference gauge
- Three actual 1600 × 1100 Cycles CPU renders: overview, sample handling and measurement close-up
- Identity-bound metadata guards, complete task-operation and canonical-anchor bindings, source/geometry boundary ledger, native and portable checks, independent review and a frozen exact-allowlist ZIP

## What is known, and what is authored

The paper reports NinjaFlex TPU, a nominal 0.4 mm nozzle, layer thickness 0.8 times nozzle diameter (derived 0.32 mm), a fixed bottom holder, manually imposed 5 mm input using a caliper and camera images before/after input. Only the 5 mm magnitude is drawn as a labelled reference distance. It is a static marker, never an applied displacement or calibration. No source efficiencies or output movement are rendered.

The 6 × 4 diamond grid, 14 mm pitch, 1.4 mm beams, 4 mm extrusion, base, apparatus envelopes, ruler, camera optics, stage, contacts and marker positions are original unqualified design choices. They are not the paper's optimized structure, source node coordinates, print-ready CAD, a material model, a validated mechanism or a geometric reconstruction. There is one representative specimen. No deformation, optimization, FEM/DEM, neural-network code, force, contact, image acquisition or efficiency calculation is implemented.

Blender uses right-handed Z-up; glTF uses standard Y-up, in metres. The specimen's upright XZ plane and local vertical gauge do not select a source input or output axis. Source-to-scene axis mapping remains null. Authored metric units are not calibrated physical dimensions or qualified robot poses. No collision meshes, dynamics, trajectories or hardware adapters exist.

The `DISPLAY_ONLY_10X` scene enlarges the same generic lattice geometry and 5 mm reference gauge by 10×. The latter becomes 50 mm in authored display coordinates. Furniture and typography are presentation dimensions, outside that factor. Display geometry is not another specimen or a physical apparatus. The native-size lattice remains in `ACTUATOR_AUTHORED_METRIC`; the two GLBs stay separate.

## Source discrepancies stay visible

The main body calls Fig 2 orthogonal and Supplementary Fig 3 anti-parallel. Fig 2's caption and inspected arrows show anti-parallel input-down/output-up; Supplementary Fig 3's arrows show orthogonal input-down/output-left. The figure-to-movie cross-references also conflict with the observed movie content: Movie 2 is orthogonal and Movie 3 anti-parallel. These records are retained separately, without relabeling the source. Direction defaults to HOLD and needs experiment-specific review plus explicit coordinate maps.

Two further source pointer discrepancies are retained: the Methods physical-results pointer names Supplementary Fig 1 although printed results appear in SI Fig 3, and force-scan prose names Fig 5c where the caption separates stiffness (5c) and input force (5d). The force branch is outside this scene's scope.

The source exponent n for the printed efficiencies is not established. The task's n=2 is a benchmark choice, not evidence of the paper's exact calculation. This asset package computes no efficiency and emits no scientific outcome.

## Metadata-only guards

`semantic_controls.py` models caller-owned local identity/record transitions. It binds specimen/version, design, carrier, fixture, camera, direction and axis cards, calibration ID/revision, image-pair identity and run ID. Single-use symbolic claims reject stale, cross-instance, wrong-kind and wrong-context reuse. A release intent is insufficient to unfix; a fresh matching unloaded claim is required. Acknowledging a discrepancy cannot substitute for a reviewed branch disposition. The underlying source conflicts remain unresolved even after a local branch is selected.

Claims are untrusted caller-created markers, not authentication, calibration, sensor results, physical qualification or safety evidence. A registered pair produces an identity manifest only, with null displacements and null efficiency. Physical, fabrication, camera, motor and scientific-service requests always reject. Controls do not move the saved scene, which is an illustrative mounted pose rather than a live state readback.

## Reuse, provenance and licensing

Fifteen original carrier/clamp meshes are preserved at native scale from the Apache-2.0 AFM package using the existing self-contained component extraction. Their vertices, faces, transforms and modifiers are retained, with root placement/material appearance changed. The displayed carrier is empty; no physical fit is asserted. `geometry/reused_carrier_components.json` records the exact original Blend hash. These two families receive zero new unique-asset credit. Seven semantic groups, repeat cells, labels, exports and renders are not seven independently new assets.

All other geometry, explanatory artwork and scripts are original authored work. Generic helper conventions are adapted from the original transistor/sucrose scenes. No author algorithm/code, source figure geometry, images, movie frames, PDFs, vendor CAD, logos or copied source prose are redistributed. Source facts are attributed under the article's CC BY 4.0 notice, subject to third-party exceptions. Original work is Apache-2.0; Blender font notice is included. The source code has separate research-only terms and is not used. The article discloses a patent application; current patent status is unverified, and no commercial fabrication or intellectual-property clearance is claimed.

## Reproduce and verify

Blender 4.3.2, Cycles CPU; Python 3.11+ standard-library tests. Native labels remain editable; GLB labels are portable meshes. No external textures, fonts, linked libraries or downloads are needed.

```sh
blender -b -t 8 --python geometry/build_scene.py -- overview sample_handling measurement
python write_contracts.py
python -m unittest discover -s tests -v
blender -b -t 4 geometry/actuator_metrology_lab.blend --python tests/verify_blend.py
blender -b -t 4 --python tests/verify_glb_import.py
python export_package.py
```

Rebuilding overwrites generated assets, inventories and receipts; refreeze only after review. `EXPORT_ALLOWLIST.json` is the entire public boundary. Source evidence, work logs, caches and Blender backups are excluded. Checks establish static metadata and file integrity, never physical or scientific validity.
