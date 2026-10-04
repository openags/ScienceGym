# Original varactor laboratory scene assets

Original editable static scene paired with the **quantum paraelectric varactor measurement DESIGN task**. Source: [Quantum paraelectric varactors for radiofrequency measurements at millikelvin temperatures](https://doi.org/10.1038/s41928-024-01214-z), Nature Electronics (2024).

## Delivered

- `geometry/varactor_lab.blend`: two metric scenes, editable mesh primitives, separate materials and editable text
- `geometry/varactor_lab.glb`: 12 original laboratory role groups; 65 stable symbolic anchors; all 80 operations bound
- `geometry/varactor_reference_display.glb`: an isolated, uniformly 100× nominal device-reference display
- `evidence/overview.png`, `handling.png`, `dimensions.png`: actual Blender Cycles CPU renders
- `asset_inventory.json`, `affordances.json`, `operation_bindings.json`: auditable identity/geometry/anchor contracts
- `states.json`, `semantic_controls.py`: a local label-review state machine that never enables physical execution
- `review/`: source-to-asset comparison, actual native reopen and GLB reimport checks, render and sanitation receipts

## What the geometry means

The workbench, carriers, grasp tabs, equipment enclosures, sample dock, ports, record cards and instruments are original generic shapes at authored room scale. They are not vendor CAD, calibrated interfaces, safe robot poses or replicas of the paper's laboratory.

Nominal reference solids represent 3 × 3 × 0.5 mm substrate envelopes. The STO display is the **shared-chip quantum-dot-use** reference with two square 120 × 120 µm pads and about 2 mm source-reported separation. Their axial placement is authored. The separate-chip fixed-load characterization instead uses 100 µm circular pads; that branch remains citation-only here. The KTO solid is an **unpatterned envelope reference**, and is not the STO QD device topology. Nominal Ti/Au 5/60 nm layer dimensions are dimensional metadata/reference solids, not resolved metrology or validated contacts. They are not visually thickness-exaggerated. The 100× companion scene uses one uniform enlargement, including thickness. The 25 µm Au wire diameter reference uses an arbitrary straight length; it is not a bond loop or toolpath.

The five functional blocks on the generic circuit case are metadata roles, not a circuit netlist. Source/drain electrode and CNT geometry are unbuilt. The drain reference pertains to SQD; the DQD branch has a single source electrode. Fixed-load, SQD and DQD lineages remain distinct; the 20 pF series capacitor and JPA are DQD-only metadata. No source data, curves, fitting code or sensitivity achievement is included. `variants.json` links the same physical STO varactor pair across SQD and DQD while preserving different device ancestry, circuit/calibration revisions, source-reported inductors, branch-specific bias tees and safe-release requirements.

## Safety and scope

All fabrication, heating, growth, lithography, deposition, lift-off, bonding, cryogenics, vacuum, magnetic field, RF/DC, transfer and acquisition services are closed, permanently disabled proxies. A record label is never an observation, calibration, qualification, safe-isolation proof or permission to remove a sample. Qualified external safe-release records are required by the task contract, and this asset package cannot issue or establish them. No live control API, scientific solver, electromagnetic/thermal simulation, motion, contact or force model is implemented.

The task-binding snapshot preserves the frozen pre-build ID contract, including its initial pending status; delivered static availability is established by the inventory, operation bindings and validation reports. Whole-paper task DESIGN coverage and 80 symbolic bindings are not whole-paper execution. Source discrepancies remain explicit holds; see `review/source_comparison.json`. Source figure/CAD/code/data files are excluded. Original geometry is released under Apache-2.0; source attribution and bundled Blender font notice are in `LICENSES/`.

## Reproduce and verify

From the package directory, with Blender 4.3.2 and Python 3.12:

1. `python write_contracts.py`
2. `blender -b -t 6 --python geometry/build_scene.py`
3. `python complete_bindings.py`
4. `blender -b --python tests/verify_blend.py`
5. `blender -b --python tests/verify_glb_import.py`
6. `python sanitize_metadata.py`
7. `python -m unittest discover -s tests -p 'test_*.py' -v`
8. `python export_package.py`

The public ZIP is built only from `EXPORT_ALLOWLIST.json`. The manifest covers every public file except itself. Logs, backup files, raw papers, source pictures, private paths and scratch material are excluded. Re-rendered compressed bytes may vary across Blender/platform builds; the included receipts hash the delivered artifact bytes.
