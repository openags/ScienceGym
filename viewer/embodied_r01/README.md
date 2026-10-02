# Chiral R01 embodied visual task demonstration

This package is a **Blender CPU static-pose storyboard**, not a robot execution, policy rollout, physical simulation, contact validation, scientific reproduction, or original laboratory reconstruction.

It places licensed Unitree G1 visual geometry in the existing authored laboratory and exposes the equipment, current specimen state, manipulated/carried object, and before/after task conditions for the R01 reference sequence.

## Open the visual task

Download this folder and open `index.html` in a browser. Select a step or play the sequence to inspect the robot, active apparatus, manipulated objects and intended specimen states. All images and task data are local; no server, installation or network service is needed.

![R01 stock collection](frames/01_FAB01.jpg)

[Assembly](frames/09_ASM04.jpg) · [Loading and specimen inspection](frames/19_LOAD.jpg) · [Archive](frames/24_ARCHIVE.jpg) · [Whole laboratory](overview.jpg)

## Deliverables
- `overview.jpg`: annotated starting state with raw-stock cassette, empty build tray, mobile robot, equipment, and intended lab route
- `frames/01_FAB01.jpg` through `frames/26_CLEAN02.jpg`: 26 annotated reference-operation keyframes
- `frame_manifest.json`: operation-linked replay data, object IDs, intended pre/post state, pose/camera metadata and coverage limits
- `render_receipt.json`: renderer, lineage-visibility audit, source hash, no-physics declarations
- `scripts/build_visual.py`: reproducible authored static scene/pose construction using the existing source assets; no dynamics libraries are invoked
- `scripts/annotate_frames.py`: deterministic English captions and same-object inspection panels

## Exact coverage
The 26 R01 reference operations are represented. Lower-layer and upper-layer loops are shown as layer-completion states: **the 18 individual pick/place actions are not individually animated or validated**. Compound operations have representative visual moments plus intended pre/post captions. Transitions are an authored route, not collision-checked locomotion. A screen-space magnifier renders the same specimen in its current world state; it does not add a duplicate specimen to the lab.

Only the R01 rubber branch is covered. The two loadings are an authored task choice. Geometry at the loading frames is simple illustrative axial scaling; it does not predict force, buckling mode, twist, or recovery. No scientific result is measured by this visualization. The manufacturer, model, fabrication process, detailed joining method and real process parameters remain unknown.

The initial state contains raw stock and an empty build tray. Downstream half-unit/assembled stage copies from the original all-stage scene are hidden. Eighteen half-unit visual identities are exposed only after a mock completion event, then replaced by one assembled representation of `obj.R01.001`. That specimen remains the same identity through both task cycles, retrieval and archive.

## Rights and attribution
Lab, apparatus and specimen visuals reuse first-party authored geometry from the existing `chiral_scene_v3_r01` package. The source paper supplies the referenced task/scientific facts, not copied images or apparatus CAD. No new papers, publisher media or proprietary manufacturer imagery were downloaded.

Robot visual meshes: Copyright (c) 2016-2023 HangZhou YuShu TECHNOLOGY CO., LTD. (Unitree Robotics). BSD-3-Clause license retained in `licenses/Unitree_G1_BSD3.txt`. Existing local G1 description states that it derives from the public Unitree description, with MuJoCo Menagerie edits. Only mesh and XML body-transform data are read; no MuJoCo physics, gait, policy or controller is loaded or run. Robot poses are authored illustrations, not proof of Unitree motion capabilities or endorsement.

## Reproduction and verification

The viewer is self-contained after downloading this folder. `node test_player.js` tests player state transitions using a mocked DOM; it does not test real browser layout or robotics.

Rebuilding the images additionally requires Blender 4.3.2, Pillow, the original authored R01 `.blend` scene/input package and the separately licensed G1 XML/STL resources. Those heavyweight source assets are not bundled here. Set `SCIENCEGYM_SCENE_ROOT` and `SCIENCEGYM_G1_ROOT` to those directories, optionally `SCIENCEGYM_TASKS_ROOT` and `SCIENCEGYM_RENDER_OUT`, then run `blender -b -t 8 --python scripts/build_visual.py` and `python scripts/annotate_frames.py`. Font locations can be supplied with `SCIENCEGYM_FONT` and `SCIENCEGYM_BOLD_FONT`. These environment-variable adapters were syntax-checked; the recorded final render used the original local source locations.

The first rendering pass had a collapsed-joint transform import error and is obsolete. The included images use the corrected XML transforms. All 26 final frame files are readable, match the intended reference-operation IDs and have a single declared sample lineage. Layer-level placement views summarize repeated picks; those picks are not individually animated. Contact, collision, reachability, controller execution and scientific results are not validated. Actual browser visual QA was unavailable; player controls were tested with a mocked DOM.

`frame_manifest.json` records source evidence and authored state choices. Its `source-archive:///` locator is a nonresolving reference, not a download endpoint. The original task JSON is linked at an immutable public commit. Static pose/image checks do not certify that a physical robot can perform the task.
