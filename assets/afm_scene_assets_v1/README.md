# Cantilever-free AFM operations lab

An original, editable 3D asset package for `afm_metrology_operations_v2`, based on Cao et al. (2021), [DOI 10.1038/s41467-020-20612-3](https://doi.org/10.1038/s41467-020-20612-3).

## What exists

- Original parametric `.blend` with editable geometry, camera views, procedural materials and text labels
- Portable apparatus `.glb` and a separate, clearly magnified microassembly `.glb`
- CPU-rendered overview, probe-assembly close-up and sample-handling view
- Two distinct configurations: parallel imaging with 10× Mitutoyo / NA 0.28; characterization with inverted 10× Olympus / NA unreported
- Retained sample carriers, clamp states, docking locators, translation-stage visual components, probe perimeter mount, sensor/control placeholders, grasp/access proxy and a 100 mm authored ruler
- Stable asset and part IDs, operation mappings, per-part metric dimensions, source classifications and static state guards

## Scientific and dimensional boundary

This is an original authored approximation, not vendor CAD, a calibrated replica or a photorealistic truth claim. Instrument envelopes, mounts, carriers, silicon-pattern motifs and access clearances are authored. The experimental whole-array span is unresolved: the main text states about 0.5 mm while Discussion says 5 mm. We infer neither a correction nor a qualified full-array footprint.

The 49-cone subset illustrates the reported 15 µm hexagonal spacing. Its 6 µm height, 3 µm base radius and 100 nm tip-radius parameter come from a numerical model, not fabrication metrology. The tip is simplified as a truncated cone. It is not the reported 1088-position array. The cylindrical detail uses SI-reported 6 µm height, 3–8 µm radius range and 14 µm backing; positions and radius allocation are authored.

Native microscopic parts use metres. The separate explainer enlarges cone/cylinder features 1000×; support slabs, target relief and exploded gaps are authored display geometry. Do not interpret these as source dimensions. Silicon motifs are iconographic and not traceable TGXYZ02 geometry. No manufacturer logos, CAD, photos or source figures are bundled.

## Open and reproduce

Tested with Blender 4.3.2 on Linux, Cycles CPU. The installed build lacks OpenImageDenoise, so renders use 160 samples without denoising.

```
blender geometry/afm_operations_lab.blend
blender -b -t 8 --python geometry/build_scene.py -- overview equipment_closeup sample_handling
python -m unittest discover -s tests -v
blender -b geometry/afm_operations_lab.blend --python tests/verify_blend.py
python semantic_controls.py
blender -b geometry/afm_operations_lab.blend --python geometry/apply_demo_pose.py -- held
blender -b geometry/afm_operations_lab.blend --python geometry/apply_demo_pose.py -- docked
```

The Blender file retains editable text; exports convert labels into mesh. The apparatus GLB excludes the magnified display and studio floor. Blender uses Z-up; glTF uses Y-up after the standard exporter transform. Metres are retained. Root IDs and child local-to-parent transforms are listed in `asset_inventory.json`.

## Interface readiness

`semantic_controls.py` guards a toy carrier/clamp/contact sequence and invalidates any physical-calibration claim across optical configuration changes. `apply_demo_pose.py` positions the authored demonstration carrier and clamp arms. These are local static/kinematic tools only. They do not command a device, generate sensor receipts, validate gripper contact or perform a calibration. No rigid-body physics, contact model, collision validation, material simulation or robot reachability is implemented.

The overview shows a deliberately raised inspection pose. Gaps and working distances are not qualified optical settings. Orange geometry marks the authored gripper/access proxy, teal marks authored carrier interfaces. Front controls have semantic identities only. Do not treat the painted indicators as hardware readbacks.

## Evidence and redistribution

`EXPORT_ALLOWLIST.json` is the only publication list. It excludes source archives, private papers, original source figures, temporary logs and Blender backup files. `MANIFEST.sha256` records allowed file hashes. `review/independent_review.*` describes external verification and limitations. All original code, geometry, material definitions, metadata and renders follow Apache-2.0; attribution is in `LICENSES/`.
