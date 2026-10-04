# Sucrose enclosed metrology service

Original, editable generic apparatus for `sucrose_metrology_operations_v2`, with stable six-group bindings to [the source paper](https://www.nature.com/articles/s41467-026-72281-3). This is a static scene and local metadata fixture, not an executable laboratory or validated scientific simulation.

## Deliverables

- `geometry/sucrose_operations_lab.blend`: two editable scenes, editable labels, materials, camera views and six main asset groups
- `geometry/sucrose_operations_lab.glb`: metric-authored apparatus, with stable group/anchor names and custom properties
- `geometry/sucrose_volume_lineage_display.glb`: separate, non-proportional explanatory cards
- Three 1600 × 1100 Cycles CPU renders: overview, retained-cartridge service close-up and volume-lineage display
- Per-part inventory, 31 authored anchors, operation bindings, dimension ledger, static-state guards and test/review receipts

The main groups are standards bench, reference station, cartridge service, sealed optical enclosure, custody records and qualification hold panel. The syringe pump is a closed generic proxy. The optical enclosure has logical beam-profile, speckle and dark-frame record channels but no internal optical construction, beam paths, images or source controls.

## Scale, state and scientific boundaries

All apparatus dimensions, appearance, port placement, collision envelopes and anchor poses are authored and unqualified. Metres make editing consistent; they do not establish a fit to real equipment. There is no vendor CAD or exact vendor appearance. Blender uses Z-up; the standard glTF export uses Y-up and retains metres.

The source's nominal 22 µL chamber and approximately 300 pL optically interrogated region are separate factual labels. Neither is the unknown total required handling volume. No internal chamber geometry or proportional volume model is supplied. The explanatory display has equal-size cards and explicitly does not encode relative volume. Microscopic SPP dimensions are metadata facts only; no SPP plate surface, channel layout or source-traced geometry is built.

The source has a forty-fold discrepancy between 2 cc/min and approximately 50 µL/min. No value is selected, averaged or offered as a pump setting. Default state is a blocking flow hold. All pump requests and real acquisition requests fail. A fixture acknowledgement can only enable authored metadata examples and never resolves the source disagreement or enables a device.

The saved scene shows a retained, docked illustrative cartridge pose. The static state fixture starts in a separate, explicitly undocked reset state. Neither is a hardware readback. The cartridge must be docked for a clamp cycle or sample switch. Undocking invalidates any pending clamp observation. Every sample switch requires a fresh CLAMP and separate mock VERIFY_CLAMP observation. Each successful switch consumes the observation; directly re-verifying an already consumed cycle is rejected. It checks every sample, aliquot, setup version, plate, wavelength profile, reference, calibration, distinct frame-role ID and run ID as a nonempty string; changing setup, plate or wavelength invalidates fixture calibration. It produces no measurements or images.

No real laser operation, fluid physics, synthetic speckle, robot control, collision backend, calibrated optics, refractive-index results, qualified handling tolerances or physical calibration is implemented. Precision is never presented as absolute accuracy.

## Reuse and rights

Fifteen carrier/clamp meshes are reused from two original Apache-2.0 AFM asset families. Their topology, local dimensions and modifier parameters are preserved, translated to the new dock and recolored. `geometry/reused_carrier_components.json` records source part IDs and the exact source Blend hash. These two families receive zero new unique-asset credit. Six scene groups, repeated vials, individual mesh parts and two exports must not be counted as independent assets.

The sucrose paper is CC BY-NC-ND 4.0. No source figures, art, CAD, text dumps, PDFs or source-derived renderings are copied, traced, adapted, embedded or included. Factual roles are expressed through independently authored generic geometry. Original code, geometry and renderings are Apache-2.0; see `LICENSES/`.

## Reproduce and inspect

Use Blender 4.3.2 with CPU Cycles. No external installation or internet access is required. The included reusable mesh data makes generation self-contained; the optional extraction script is only for auditing original AFM provenance and requires that original package.

```
blender -b -t 8 --python geometry/build_scene.py -- overview cartridge_service volume_lineage
python -m unittest discover -s tests -v
blender -b geometry/sucrose_operations_lab.blend --python tests/verify_blend.py
python semantic_controls.py
python export_package.py
```

Native labels remain editable FONT objects; GLB exports use mesh labels. Apparatus and display scenes are exported separately. Only `EXPORT_ALLOWLIST.json` may be shared. The frozen ZIP manifest excludes logs, private source materials, caches and Blender backups.
