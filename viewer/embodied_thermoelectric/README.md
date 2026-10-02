# Thermoelectric PAIRED_TWO: embodied visual storyboard

A mobile Unitree G1 visual actor follows one bounded main route through the existing 16-station thermoelectric laboratory: raw P and N constituents → separately processed parent batches → two distinct P legs and two distinct N legs → one two-pair module → four thermal-boundary chapters → data review → archive and cleanup.

Open `index.html` for the offline interactive player. It reads `manifest.js`, which embeds the frame metadata and full BSD model notice. `overview.jpg` and `keyframes_contact_sheet.jpg` provide static review. `frame_manifest.json` contains the same public task metadata. Forty-five static/kinematic illustrated keyframes map all 66 operation occurrences in the selected PAIRED_TWO reference route; grouped micro-operations and condition repeats are identified in `loop_coverage.json`. The images illustrate intended before/after states, not completed real or simulated experiments.

## Evidence and boundaries

- [Public English task source at pinned commit](https://github.com/openags/ScienceGym/blob/2f926a9d2c2b8a0c71e8939feaa6ca5696e14c27/tasks/thermoelectric_operations_v2/)
- Source paper DOI: [10.1038/s41586-026-10223-1](https://doi.org/10.1038/s41586-026-10223-1)
- External scene input: `thermoelectric_scene_v3` (not distributed here); input blend and source-manifest hashes are retained in the render receipt and `external_inputs.json`
- This is PAIRED_TWO only. The B melt-before-mill, segmented-joining, contact-scan, computational and literature branches are excluded
- No source-paper photographs or vendor CAD were imported. The existing laboratory and apparatus shapes are first-party authored proxies, with previously declared first-party SPEX/module reuse

## Source facts kept separate from authored geometry

P retains MgAgSb + 0.625 wt% C18H36O2 (additive isomer unknown). N retains Mg3.2In0.02Sb0.595Bi1.4Te0.005, including Mg excess, In and Te. P has Sb interface roles; N has stainless-steel interface roles. The two material phases retain separate work orders and parent lineages.

P source leg envelopes are 3.3 × 3.3 × 6.6 mm; N envelopes are 2.9 × 2.9 × 6.6 mm. Leg and module visuals remain at an explicit 20× linear scale rather than being unified into the same-sized block. Container and billet proxy dimensions are authored/unknown and do not acquire a scientific 20× scale claim. Orange highlights indicate the active target, not a change of material identity. P cutting parallel to the pressing axis is source-supported; N direction stays unknown. The prior asset's AlN envelope, copper layout and visual interface partitions are authored geometry, not measured source dimensions. No joining method or Ga–In use is asserted for the two-pair module.

Raw materials are the only sample state visible at the start. The original powder, billet, loose-leg, assembled-module, mounted-PEM and unrelated branch display copies are hidden until their corresponding illustrated stage. The assembled module reuses one visual instance as it travels; the old independent PEM module remains hidden throughout. P1/N1/P2/N2 identities are retained through assembly, measurement and archive. Quantity, mass balance and physical processing yield remain unknown.

## What was aggregated

`loop_coverage.json` explicitly maps all 66 source operation occurrences to frames. Setup, interlock, handoff, cooling and cleanup groups are stage summaries; closed powder handling at WS_POWDER and transfer to WS_DIE are aggregated into each material’s stack frame, so there are 12 primary camera stations covering 13 workstation roles; process intervals and detailed finger motions are omitted. Four individual leg placements are shown. Station changes show the robot and numbered supported carrier at authored dock keyframes, not continuous validated travel paths.

The same module appears at source thermal-boundary targets Th = 373, 473, 573, 593 K with Tc = 293 K. Each chapter represents an inner current/acquisition/history loop whose current grid and count are unknown. No scientific records, calibration, achieved temperatures, maxima or efficiencies were generated. The record file is an empty schema, not a data set. P = I × V and η = P/(P + Qc) remain conditional on real compatible channels; raw mV is never silently treated as W.

## Rendering and rights

The corrected G1 importer uses original XML pos/quat transforms as stored joint bases, with static authored joint rotations. It does not load or step MuJoCo, execute a policy, or run a controller. Both scene and view-layer denoising are disabled. CPU Cycles renders use 32 samples; inspection insets use 24. Local shots hide unrelated foreground stations for readability; the overview preserves all 16 stations. Insets use the same active scene object with robot/guide/cover/contact occluders hidden only for inspection.

The G1 visual geometry is Copyright (c) 2016-2023 HangZhou YuShu TECHNOLOGY CO.,LTD. (Unitree Robotics), used under BSD-3-Clause; the full notice is retained in `licenses/Unitree_G1_BSD3.txt`. No endorsement is implied. Source STL/XML and laboratory assets are read in place and not duplicated into this deliverable. New image derivatives, manifests, scripts and the license notice are the package contents.

No physics, robot execution, contact/collision/reachability validation, chemical/thermal/electrical processing, milling/sintering/cutting, vacuum operation or scientific acquisition took place. Closure is a storyboard closure, not demonstrated equipment safety or experimental success.

## Rebuild

Rebuilding is optional. The player and all 45 rendered frames work immediately without external assets. For a visual rebuild, first supply the external source roots and dependencies documented in `EXTERNAL_INPUTS.md`, then run:

1. `python scripts/make_manifest.py`
2. `blender -b --threads 8 --python scripts/build_visual.py -- --overview`
3. `python scripts/annotate_frames.py`
4. `python scripts/finalize_package.py`

`THERMO_SCENE`, `G1_ASSETS` and `THERMO_TASKS` can override the existing source scene, G1 assets and English task locations. The render receipt preserves the original source and image hashes. `provenance/original_render_SHA256SUMS.txt` records the original 63-file render package; its old text/script hashes intentionally differ from this portable export. The export-level `PUBLIC_FILE_MANIFEST.json`, `SHA256SUMS` and `EXPORT_RECEIPT.json` identify the exact public files. The 45 frame JPEGs, overview and contact sheet remain byte-identical to the original frozen images. No remote publication or upload is performed by this package.

## Public export checks

The export is English-only and contains no machine-specific workspace paths. All published image hashes match the original freeze. Python scripts compile, JavaScript syntax checks pass, and the generic player's mocked-DOM controls test passes. These are packaging/UI checks; they do not add browser, physical, scientific or robot validation.

Only the original SHA256SUMS allowlist, the generic player files and explicit public-export documentation/receipts are included. No raw publisher sources, G1 XML/STLs, laboratory geometry, raw PNG intermediates or duplicated review image tree are bundled. `model_license` embeds the complete BSD-3-Clause notice as well as retaining the license file.
