# R01 source-scene inspection evidence

This is a bounded, static inspection of the supplied first-party authored R01 proxy scene. It is not a new scene, a robot episode, a digital twin of reported apparatus, or a physical validation. The original scene file is unchanged and is not included in this evidence folder.

## Source and resolution

- Source package asset: `assets/r01_complete_route_scene.blend`, 15,113,204 bytes
- Source SHA256: `bbcf496ca4c1eaa16a56db472e54d944a8d54bc19c7e00073afe32fe9e6ca915`
- Inspected with Blender 4.3.2 using CPU only, without running the source builder, animation, physics, a robot controller, or an external simulator
- Actual source scene: 963 objects, including 952 meshes, 8 cameras and 3 area lights
- All 215 names declared for `WS_TEST` in `station_parts.json` resolve to actual scene objects bearing that station property; no declared names are missing
- The mounted specimen comprises 173 independent meshes: two plates and nine cells, each with three rings and sixteen rods
- The scene contains simultaneous, distinct stage-prop copies. These are not one specimen occupying several stations and are not an executable initial state

`source_inventory.json` contains full records for the 215 resolved `WS_TEST` objects, plus the complete 963-object name/type/visibility list and record hashes. It records source metadata and builder hashes, exact object names, custom properties, local/world matrices, measured mesh bounds, unit settings, lights and existing cameras. No source vertices are republished. `ws_test_object_names.json` is a small convenience index.

## Units, frames and scale

The source Blender scene uses metric units, metre length display and `scale_length = 1`. The reused mesh input declares right-handed, Z-up metre coordinates. The station sidecar locates `WS_TEST` at `[10.15, 2.25, 0]` metres with an authored yaw of -90 degrees.

All 215 `WS_TEST` meshes have their vertices baked in station coordinates and their object origins at the same station origin. There are no object parents. Consequently, Blender `matrix_local` equals `matrix_world` for these objects; an object origin does not identify its own surface center, grasp point, contact point or camera optical frame. `matrix_in_authored_station_frame` and `authored_station_local_bounds` are explicitly derived from the sidecar station transform. Matrices are row arrays acting on column vectors; angles in the matrix inventory are radians.

The mounted specimen's measured authored station-local envelope is approximately 0.065 × 0.065 × 0.072 metres. The source metadata separately declares that same reference envelope while identifying detailed joints as authored approximations. This is agreement between authored geometry and a source-sidecar statement, not independent physical metrology. No explicit display magnification factor is declared, so `display_scale_multiplier` remains null. Object transforms and measured display bounds are recorded without claiming gripper compatibility.

The visible bench top is an authored size reference: 1.50 × 0.85 × 0.055 metres. Its dimensions and exact source geometry bounds are in the inventory; it is not a calibrated ruler.

## Fixed human-review render

`ws_test_review.png` is a newly selected orthographic human-review viewpoint at `[7.0, 0.3, 2.9]`, aimed at `[10.15, 2.25, 1.03]`, with orthographic scale 2.6. It is not a robot camera, robot eye pose or sensor observation. The camera prop already in the source is ordinary static mesh geometry.

The render shows the press, small mounted array, source guard, panel, carrier, sidebox and camera prop in their actual source placement. All source geometry remains present. No source mesh is moved, enlarged, hidden, deleted, replaced or presented through an X-ray effect. No visibility overrides were needed. The source guard's authored shader transparency is unchanged. Geometry outside the camera frustum remains in the scene and may affect lighting or shadows. The image cannot establish robot line of sight, readability, safe access or manipulation feasibility.

The three original area lights and the original world, materials and exposure are retained. The complete camera, lighting, source visibility and render-setting changes are in `render_receipt.json`. Rendering uses Cycles CPU, four threads, 24 samples, fixed seed 0, no denoising, no adaptive sampling, 1400 × 1100 pixels and an opaque RGB PNG. Only PNG text/EXIF/time metadata is stripped after rendering; the pixel data is not edited.

Two renders at the unchanged camera and unchanged scene produced byte-identical PNGs after metadata removal. The repeat is recorded in the receipt; the duplicate `ws_test_review_repeat.png` need not be published. This establishes repeatability of this run, not a guarantee across Blender versions or hardware. The receipt also verifies unchanged source-file hash, object transforms, source mesh data, source visibility and lighting.

No collision, contact, grasp, reachability, force, guard-interlock, robot sensing, manufacturing-success or scientific-measurement validation was performed. The visible controls, carrier, guard, fixture and camera are static authored proxies. Missing functional and dimensional evidence remains a separate gate.

## Reproduce

Obtain the authorized source package separately. Keep its `assets`, `inputs`, metadata, sidecars and source scripts together. Set `R01_SOURCE` to its `assets/r01_complete_route_scene.blend`, and run this from the repository root with Blender 4.3.2 available:

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
  --python scene_bindings/r01_mount_observe_retrieve_v1/source_evidence/inspect_source.py \
  -- --source "$R01_SOURCE" \
  --out scene_bindings/r01_mount_observe_retrieve_v1/source_evidence \
  --render --repeat 2
```

Omit `--render --repeat 2` for inventory only. The script rejects a scene with a different SHA256, rejects evidence output inside the source package, and never saves the source Blend. It explicitly selects CPU rendering and stops on unexpected rigid-body configuration. Source package paths in the JSON are relative; local source locations and PNG metadata are not published.

The optional `--reveal-hidden` mode is not used for this evidence. If requested for another inspection, it only clears mesh hiding flags and lists every change; it never hides geometry. Collection-level rendering exclusions cause a reported blocker instead of a silent override.

Per-mesh hashes encode actual mesh-local vertex coordinates as little-endian float64, preceded by vertex/polygon counts, then each polygon's vertex count, material index, smooth-shading flag and uint32 vertex indices. Record hashes use sorted-key compact ASCII JSON. The whole source-file SHA256 remains the primary provenance pin.
