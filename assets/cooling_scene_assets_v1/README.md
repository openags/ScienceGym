# Original directional cooling scene assets v1

Original metric geometry and a bounded semantic demonstration for the task
`directional_cooling_operations_v2`, based on Bhatia et al. (2018),
[Passive directional sub-ambient daytime radiative cooling](https://www.nature.com/articles/s41467-018-07293-9),
DOI 10.1038/s41467-018-07293-9.

**This is an assets-and-state demonstration, not a reproduced cooling device or an executable scientific task.**
No thermal, radiative, optical, electrical, DAQ, PID, robot, collision or contact
backend is supplied. No event establishes device success, safe physical release,
measured cooling, valid spectra, calibration, or a completed task operation.

## What is built

The inventory contains **8 distinct asset roots and 438 child parts**. Native
parts include meshes, curves and text objects. They are not 438 collidable
meshes or 438 independent assets. Re-exporting two roots in the handling module
does not increase the count.

- `cooling.lab_bench`: original metric assembly display bench
- `cooling.white`, `cooling.black`: independent paired white/black device displays
- `cooling.handling_fixture`: original reusable carrier, seating dock, two clamps,
  spacer ring and separately identified exploded film displays
- `cooling.backside_inspection`: flipped source-size copper coupon, authored
  heater/probe envelopes, and six separate extra probe displays in a rack
- `cooling.logger_power`: authored protected logger and isolated-output console
  envelopes, distinct ARM/STOP controls and F+/S+/S-/F- visual port identities
- `cooling.optical_bench`: authored integrating-sphere silhouette, sample port,
  reference tray and variable-angle fixture; not vendor CAD
- `cooling.scale_reference`: 200 mm ruler and explicit unresolved-height plaque

There are two paired device display instances. The flipped coupon, exploded
films and torn state are inspection/variant geometry, not additional experimental
samples with scientific provenance.

The carrier/dock/clamps are a **new authored interface**. Primitive helper code
idioms were adapted from the original AFM asset generator, but no AFM geometry,
physical properties, shared mounting standard or compatibility result is inherited.

## Files and inspection

- `geometry/build_scene.py`: editable original geometry/material generator
- `geometry/cooling_operations_lab.blend`: native metric scene with text, curves,
  modifiers, cameras, lights and hidden lower-film torn variant
- `geometry/cooling_operations_lab.glb`: static whole-scene exchange snapshot
- `geometry/cooling_handling_module.glb`: static export of the handling-fixture and
  backside-inspection roots; those same roots are also in the whole-scene export
- `asset_inventory.json`: every root and child ID, transform, dimension and source tag
- `asset_metadata.json`: units, dimensions, provenance, authored choices, scope and gates
- `affordances.json`: 20 explicit interaction-region descriptions and authored local frames
- `operation_bindings.json`: all 56 task operation IDs, including 29 partial
  visual/semantic bindings and 27 explicit not-built entries; **0 fully implemented operations**
- `states.json`: default state, exact event/operation catalog and forbidden-claim boundary
- `semantic_controls.py`: dependency-free, guarded Python state demonstration
- `geometry/apply_demo_state.py`: native Blender pose/readback binding
- `materials/materials.json`: procedural appearance resources, all unmeasured
- `evidence/overview.png`, `sample_handling.png`, `equipment_closeup.png`: rendered views
- `review/render_receipt.json`: actual render tool/settings/timing receipt
- `tests/test_package.py`: portable package, dimension, binding and state-contract checks
- `tests/verify_blend.py`: native Blender dimension and bound-pose checks
- `LICENSES/`: Apache-2.0 text, attribution and Blender built-in font notice

Open the `.blend` in Blender 4.3+ and choose `CAM.overview`,
`CAM.sample_handling` or `CAM.equipment_closeup`. The source is configured for
CPU Cycles rendering; no GPU or denoiser dependency is needed. The recorded
render receipt describes what was actually run. Evidence images are original
renders, not copied source-paper figures. Pixel review and native tests are
separate from generating a render receipt.

GLB files omit the studio floor and hidden torn variant. They contain static
baseline geometry and metadata extras, not Python logic or animated state
transitions. Import conversion must preserve metres and account for glTF Y-up
versus native Blender Z-up. Native `(x,y,z)` maps to glTF `(x,z,-y)`.

## Scale and source evidence

Source references were used for facts, not imported CAD or pixels. Full SI text
and the source-reading addendum were inspected for this contract. The authoring
record additionally documents direct inspection of SI construction/sensor
schematics. Main written reading is inherited from the 3 October audit; no new
main-figure pixel review or exact source reconstruction is claimed.

Source-supported dimensions, from SI Note 2 (p13), are retained in metres:

- Copper emitter: 50 mm diameter, 0.5 mm thick
- Insulation: two layers, each 50 mm diameter and 25 mm thick
- Solid PE support: 76 mm ID, 102 mm OD; displayed 52 mm height is authored
- Aluminum film ring: 107 mm ID, 127 mm OD, 6.4 mm thick
- Nanoporous PE: two separately identified sheets, each **16 micrometres** thick
- Shield: 140 mm ID, 152 mm OD, 57 mm height; 50 mm diameter top aperture
- Direct-solar reflector disk: 60 mm diameter
- Main Methods reports 1.5 mm aluminum track stock; its displayed straight path is authored

The four films in the paired white/black displays use **1× physical thickness**.
The two exploded handling-inset films alone use **50× thickness**, displaying
0.8 mm for a 16 micrometre target. Their diameter is not enlarged. Film trim,
display tabs, separation poses, plate/disk thicknesses, mounts, gaps, base,
instrument envelopes and cable routes are authored choices. Display tabs are
identity accents, not qualified physical grasp tabs. The painted overlay is
one authored visual layer; it does not reconstruct the three source paint coats
or establish their thickness.

Two important gates remain open:

1. **Reflector height:** SI Figure 1a2 labels 100 mm, while SI Note 2 and the main
   text describe approximately 150 mm above the emitter. The physical target
   height remains null. The scene displays 150 mm and shows both alternatives;
   this is not a resolution of the datum/version conflict
2. **Sensor positions:** SI Figure 5 provides schematic positions, and Note 5
   describes six extra sensors. A qualified coordinate-indexed installation and
   tolerance map is unavailable. Six probes are shown in an authored rack;
   rack coordinates must not be mistaken for source installation positions

The source-size upper insulation envelope includes an authored 1.2 mm deep,
23 mm radius heater-clearance recess. Each paired assembly also has an authored
9.3 mm support pedestal and 3.5 mm shield adapter. Ring/cover mounting datums
provide visible separation from the emitter and heater. These are original
clearance simplifications, not reported source features, historical assembly
coordinates or validated thermal/contact interfaces.

Appearance shaders do not establish material composition, optical properties,
thermal conductivity, measured surface finish or a validated physical model.
Mass, friction, compliance, film tension and attachment properties remain unknown.

## Interaction and state contract

The native default has a docked carrier, closed clamps, intact films, parked
lids, an idle demo logger, unqualified optical configuration, no mounted reference,
centered reflector display, and physical/geometry qualification false.

`State` is a dataclass. `transition(state, event)` returns a new state without
mutating its input; invalid states, unsupported events and guard failures raise
`ValueError`. `validate(state)` enforces the bounded demo state and never permits
physical execution or geometry qualification. There is no clock or device I/O.

- `open_clamp` / `close_clamp`: one state moves both clamp levers about their
  displayed pivots; opening requires an idle logger and docked carrier
- `grasp_carrier` / `dock_carrier`: guarded held/docked states, with a 100 mm
  authored lift for visual inspection; no robot, grasp or travel route
- `remove_lower_film`, `remove_upper_film`, `replace_lower_film`,
  `replace_upper_film`: require an idle, supported, released fixture. Replacement
  of a non-intact film increments only that component's revision
- `tear_lower_film`: lower handling film only, native intact-to-torn visual state;
  damage preserves identity. Upper film supports intact/removed, with no torn variant
- `cover_apertures` / `uncover_apertures`: a shared state moves both separately
  identified paired lids; no independent per-device control API or baseline timing
- `reflector_left`, `reflector_center`, `reflector_right`: both authored reflector
  assemblies shift by -60/0/+60 mm. No qualified path or solar-shadow result
- `arm_logger` / `stop_logger`: `armed_demo` or `idle` readback only. Arming requires
  docked/closed/intact state. No data is acquired and no heater is energized
- `select_uvvis`, `select_ftir_sphere`, `select_ftir_angle`, `mount_reference`,
  `unload_optical`: demo configuration and authored reference-disk placement.
  Selection requires no mounted reference; mounting requires a selected configuration

Film events affect only the handling inset, not the paired 1× device films.
The component revision counter is a demonstration identity mechanism, not a
historical material lineage or immutable operation receipt.

The two clamp levers share one state; their 90° authored pose change is not a
qualified joint/load specification. Other frame origins are explicit in
`affordances.json`: annular meshes and several curves have world-space vertices
baked into their local mesh, so object origins need not equal component centers.
Visual meshes are separate from collision semantics: **no collision proxies,
simulation contacts, gripper limits or physical safety interlocks are supplied**.

Example local state and native inspection commands:

```sh
cd cooling_scene_assets_v1
python semantic_controls.py
python -m unittest discover -s tests -v
blender -b geometry/cooling_operations_lab.blend --python tests/verify_blend.py
blender -b geometry/cooling_operations_lab.blend --python geometry/apply_demo_state.py -- open_clamp grasp_carrier
blender -b geometry/cooling_operations_lab.blend --python geometry/apply_demo_state.py -- open_clamp tear_lower_film
```

Without `--save`, native demo changes exist only in the Blender process. Add
`--save` after the event list to write `geometry/cooling_demo_state.blend`; it is
an optional local artifact, not the canonical baseline export. The binder is
absolute/idempotent within the loaded native scene. Start from the canonical
`.blend`, not a converted GLB or a hand-edited scene.

To rebuild all canonical geometry and renders (this overwrites the generated
assets/evidence):

```sh
blender -b --python geometry/build_scene.py
```

Passing camera names after `--` renders only those views. The generator writes
its receipt for that invocation; a partial render run is not an all-view receipt.
Blender is required for native generation/binding tests, but portable package
and Python semantic tests use the standard library.

## Task bindings and remaining scope

Every named object in a partial binding resolves to inventory. All operation IDs
come from the exact base task, whose operations file hash is pinned in metadata.
The station aliases `WS_ACTIVE` and `WS_OPTICAL_ACTIVE` are not new physical
stations. A future optical operation must bind an actual UVVIS or FTIR station
and preserve instrument/configuration lineage; shared display geometry is not
permission to switch station without a MOVE operation.

No physical operation is complete. Not-built scope includes fabrication/coating
services, calibration bath, outdoor weather/solar/ambient instrumentation,
fixed-band/LDPE replacement geometry, archive/quarantine/waste services,
qualified sensor coordinates, historical tracks/CAD, physical film mechanics,
DAQ/PID and analysis pipelines. Record keeping, qualification, measurement,
electrical isolation and thermal safety require later implementations and
qualified inputs. Source-reported outcomes are not authored task results.

Tests establish file and schema consistency, explicit dimensions, names,
source boundaries, guard behavior and native authored poses. They do not
validate scientific performance, optical/thermal equations, electrical safety,
robot reachability, contact stability or end-to-end execution. There is no claim
of manufacturer certification, AFM compatibility or exact reproduction.

## Rights and references

Original authored package files are provided under Apache-2.0. See
[`LICENSES/ATTRIBUTION.md`](LICENSES/ATTRIBUTION.md) for per-file coverage,
helper-code provenance and the built-in Blender font notice. No publisher PDF,
source photographs, source figure pixels, vendor CAD, logos or external textures
are redistributed.

- [Main article](https://www.nature.com/articles/s41467-018-07293-9)
- [Supplementary Information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-018-07293-9/MediaObjects/41467_2018_7293_MOESM1_ESM.pdf), especially Note 2 / Figure 1 and Note 5 / Figure 5
- Source publication license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

The retained SI PDF SHA-256 is
`61f8587c1b34a45072fac9b25591b89f1a1b00b212b61e9c29c41e2e73a340b3`.
Reference dimensions and the source's reported results remain distinct from
original display geometry and any future qualified execution data.
