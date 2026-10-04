# Laser control scene assets, v1

Original static companion to `modulation_free_laser_stabilization` / `laser_control_operations_v2`, based on the roles in [Nature Communications 15, DOI 10.1038/s41467-024-46319-3](https://www.nature.com/articles/s41467-024-46319-3).

## What is included

- Editable `geometry/laser_control_lab.blend`, containing metric apparatus and a separate explanatory display scene
- `geometry/laser_control_lab.glb`: ten stable semantic groups, 46 canonical task anchors plus two visual grasp anchors, and 44 task-operation role bindings
- `geometry/laser_pic_display.glb`: separately labelled 1000× planar footprint reference
- Three actual Blender CPU Cycles renders: overview, package handling, and nominal-footprint display
- Original generator, materials, explicit dimension/provenance metadata, caller-owned symbolic guards, tests and independent review

The nominal PIC extent is 0.95 × 0.48 mm (0.456 mm²), represented by a zero-thickness reference plane. It is not a fabricated die. The display plane is 0.95 × 0.48 m. Its 1000× scale does not apply to typography, furniture or floating role labels. No source circuit, ring, coupling-region CAD or die thickness is reconstructed. The source’s 220 nm silicon cross-section and 100 nm SOI process label remain distinct factual annotations.

## Source fidelity and boundaries

The apparatus has original generic closed foundry/PCB services, a separately sealed PIC package, an empty carrier, closed alignment interface, open-loop calibration role, three distinct disabled DFB modules, TIA/PID record panel, capped comb-reference heterodyne service and separate FPGA in-loop records. Both chip heaters are off. The final paper’s comb-reference measurement is represented; the older review’s delayed self-heterodyne arrangement is not. SiN appears only as a numerical-study label.

All dimensions, placements, fibers, cables, ports, tolerances and grasp poses other than the declared source footprint reference are authored and unqualified. The package and carrier are separated; no fit is asserted. Fifteen carrier/clamp meshes reuse the prior original Apache-2.0 AFM asset family without scaling or topology changes and receive zero new unique-asset credit. Ten groups, three DFB instances, repeated components, file variants and renders are not ten new independent assets.

The task-binding snapshot intentionally preserves the exact plan-time bytes. Its `asset_available: false` fields describe the initial plan, not the delivered file inventory; asset availability is documented by this package and its validation receipts. Static role bindings do not upgrade task operation executability.

## Functional limits

This is static geometry and untrusted caller-owned metadata. All laser energy, heaters, controller execution and hardware IO remain disabled in every local state. No method moves Blender geometry, enables a laser, aligns optics, changes PID settings, performs calibration, acquires a signal, runs a solver or returns scientific outcomes. Scene appearance and local claims never establish physical safety or qualification. In-loop error is relative to the cavity and is not independent absolute laser noise.

`semantic_controls.py` documents the API. Exact, typed records and single-use locally issued claims bind instance, revision, sample/version, configuration, action, target and payload. Stored labels for external qualification and acquisition remain unverified identifiers. A Python caller can edit code/private state; these guards are not cryptographic authentication or a hardware safety system. Every `request_physical_service` call raises `PhysicalExecutionUnavailable`.

## Rebuild and verify

From this directory:

1. `blender -b -t 2 --python geometry/build_scene.py`
2. `python write_contracts.py`
3. `blender -b geometry/laser_control_lab.blend --python tests/verify_blend.py`
4. `blender -b --python tests/verify_glb_import.py`
5. `python -m unittest discover -s tests -v`
6. After actual visual inspection and independent review, `python export_package.py`

The generator uses built-in Blender Bfont and CPU Cycles. It requires no external source images, linked libraries, downloaded geometry or textures. Rebuilding changes artifact bytes and invalidates existing review/checksum receipts; regenerate validation and obtain a fresh review before export. Only the exact `EXPORT_ALLOWLIST.json` entries are public. Source documents, publisher pixels, local build logs, Blender backups, caches and private evaluator data are excluded.

## License

Original geometry and code: Apache-2.0. Source article attribution and built-in font notice are in `LICENSES/`. The article’s CC BY 4.0 notice does not establish rights to third-party artwork; none is redistributed here. No vendor CAD equivalence, scientific reproduction, physical readiness or whole-paper completion is claimed.
