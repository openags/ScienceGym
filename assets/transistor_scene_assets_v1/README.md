# Transistor custody and closed-service laboratory

Original editable static assets synchronized to `transistor_operations_v2` and the source paper [Three-dimensional integrated metal-oxide transistors](https://www.nature.com/articles/s41928-024-01205-0). This package makes carriers, specimen identity, PCB handoff, closed instrument boundaries and distinct logical inverter configurations inspectable. It does not execute laboratory operations or simulate scientific physics.

## Deliverables

- `geometry/transistor_operations_lab.blend`: three editable scenes with native FONT labels, six apparatus groups, 30 named metadata anchors, native-thickness layer reference and a separate explanatory display
- `geometry/transistor_operations_lab.glb`: self-contained, metric-authored generic apparatus
- `geometry/transistor_layer_ledger_display.glb`: separate equal-thickness 72-layer ledger and ordinary/independent inverter terminal-map cards
- Three actual 1600 × 1100 Cycles CPU renders: overview, sample handling and equipment close-up
- Complete 44-operation visual-role bindings, explicit six-station mapping, static metadata guards, positive/negative tests, native/GLB checks and independent review

Apparatus groups are retained sample carrier, closed packaging/PCB handoff, closed probe/readout, closed gate-bias controls, closed fabrication/metrology/thermal services, and identity/custody storage. Group IDs do not equate to the six task station IDs; `operation_bindings.json` records the exact mappings and HIGHK, thermal, long-term and destructive-section handoff requirements.

## Scale and scientific boundaries

The apparatus scene uses authored metres. Its room layout, generic equipment shells, PCB dimensions, connector positions, retention geometry and anchor poses are original, unqualified design choices. Metres do not establish fit, clearance, safety, grasp compatibility or calibration. Blender is right-handed Z-up; standard glTF exports use Y-up and preserve metre scale. There are no collision meshes, contact parameters, robot trajectories or device adapters.

The tiny unpatterned chip envelope refers to the paper's 20 × 20 mm substrate example containing four ten-stack systems. This is not the footprint of one active device. Its thickness follows the Table S1 reference. The 200 mm ruler is authored metric context. Sample and PCB labels are illustrative identities, never extra scientific specimens or source population replication.

Open the separate `NATIVE_LAYER_REFERENCE_METRES` Blender scene to inspect 72 source-thickness objects: Si + SiO2 + 60 active layers + nine interstack buffers + one final cap. SI Table S1 sums to 528.7 µm including the 525 µm substrate and 2 µm oxide. Each unpatterned square lamina uses an authored 20 mm lateral visualization envelope. It is not a lithography mask, a complete cross-section, electrically continuous material or validated circuit geometry. Source/drain slabs do not imply a short or a connection. Nanometre-scale local dimensions are preserved near the local origin; this scene is not exported to either GLB.

The `DISPLAY_ONLY_NOT_TO_SCALE` scene deliberately uses 3 mm bars and 1.5 mm separation to show layer order. There is no common magnification factor and bar thicknesses do not encode physical ratios. Its cards show logical terminal names only. The second GLB is display-only; it cannot be used to derive native geometry or a PCB netlist.

All ten source conflicts C01–C10 remain unresolved and gated. In particular, C01 retains both 25 nm and 50 nm interstack statements. Table S1 supplies the reference drawing, not a selected fabrication setting. Every buffer/cap execution default remains null. Printed formula, cohort, sign, caption, roughness-label and leakage discrepancies are not corrected by the scene or static controls. No source metrics, current, voltage, temperature, gain, mobility, leakage, images or scientific outcomes are emitted.

## Logical maps and fixture semantics

The ordinary Fig4 map has driver BG/TG = VIN/VIN and load BG/TG = VDD/VOUT. The independently biased S31 map has driver BG/TG = VBG/VTG1 and load BG/TG = VOUT/VTG2. Both retain driver source/drain = GND/VOUT and load source/drain = VOUT/VDD. The maps are separate and are not interchanged. The source's parallel-load branch stays a qualification requirement; the static fixture does not invent its missing complete gate/pad map. Unknown terminals are not assumed floating.

`semantic_controls.py` is a caller-owned, local symbolic fixture with no authentication or hardware authority. It keeps specimen, version, carrier, PCB, chip, cohort, architecture and stack identity. Static safe-zero and continuity markers have exact identity/revision/context binding. A deenergize intent alone is insufficient. Rewiring consumes a fresh safe-zero marker and invalidates continuity. Record creation consumes current continuity evidence and emits metadata only. Stale, reused, cross-instance, wrong-map and incomplete markers are rejected. Acknowledging a conflict cannot resolve it. All physical service requests remain blocked.

The saved scene is an illustrative retained-carrier pose. It is not a live readback or an automatic rendering of the fixture reset state. The fixture starts in retained storage with unknown terminal labels and no evidence. It does not move Blender objects. It cannot implement layer fabrication, specimen-changing services, thermal aging, packaging, physical retention release or measurement.

## Provenance, reuse and counting

Fifteen carrier/clamp meshes are reused from the original Apache-2.0 AFM package through its exact self-contained component extraction already used by the sucrose package. The source mesh vertices, faces, local transforms and modifiers are retained; only root placement and appearance differ. `geometry/reused_carrier_components.json` records source part IDs and the exact AFM Blend hash. These two reused families receive zero new unique-asset credit.

All remaining geometry, labels, scripts and renderings are original authored material. Generic helper code follows the original sucrose scene conventions. The 72 native laminae, 72 display bars, repeated parts, six semantic groups, exports and renders are not independent new asset families. No claim of a new paper, new task or new unique-asset count is made.

The source article is CC BY 4.0, subject to third-party exceptions. Factual values and circuit-role interpretations are attributed; no source figures, publisher pixels, PDFs, extracted prose, source screenshots, vendor CAD, logos or copied equipment geometry are redistributed. Original work is Apache-2.0. See `LICENSES/ATTRIBUTION.md` and the Blender font notice.

## Reproduce and verify

Blender 4.3.2, CPU Cycles; Python 3.11+ for stdlib tests. No external assets or downloads are required. The native file contains editable FONT labels; GLBs contain mesh labels and no external resources. Rebuilding overwrites generated geometry, inventory, anchor metadata and render receipts, so refreeze after verification.

```sh
blender -b -t 8 --python geometry/build_scene.py -- overview sample_handling equipment_closeup
python -m unittest discover -s tests -v
blender -b -t 4 geometry/transistor_operations_lab.blend --python tests/verify_blend.py
blender -b -t 4 --python tests/verify_glb_import.py
python export_package.py
```

The source-task SHA-256 records in `task_binding_snapshot.json` make synchronization inspectable. Actual final review and test receipts are under `review/`. Small labels are most readable in the close-ups or native editable scene. Only the exact `EXPORT_ALLOWLIST.json` is public; the deterministic frozen ZIP excludes source materials, author logs, private audit files, caches and Blender backups.
