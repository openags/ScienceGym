# Directional cooling reconstruction pilot

This pilot revises Bhatia et al., *Passive directional sub-ambient daytime radiative cooling*, Nature Communications 9, 5001 (2018), [DOI 10.1038/s41467-018-07293-9](https://doi.org/10.1038/s41467-018-07293-9). It is the first application of the paper-to-robot workflow and equipment reconstruction standard to an existing ScienceGym family. The historical `directional_cooling_operations_v2` task and `cooling_scene_assets_v1` assets retain their original records.

## Selection

The existing 44-family index was inspected. Directional cooling was selected for a complete, locally obtainable eight-page article and 25-page supplement; explicit dimensions and apparatus photographs; named commercial instruments; and a varied physical program spanning fabrication, coating, thin-film assembly, calibration, spectroscopy, outdoor paired measurements, configuration changes and cleanup. The publisher lists no experiment movie dependency. Historical raw measurements are author-request-only and are not available for exact reanalysis.

The pilot represents the entire reported physical program, with theoretical modeling and proposed applications classified separately. Its sample and weather conditions cannot be reduced to one favorable demonstration. New robot handling and missing manufacturing details are reconstructed choices with explicit provenance, rather than additional source claims.

## Work and acceptance

1. Reinspect the article, all supplement text and all experimental figures; save source identities, byte hashes, locators and discrepancies.
2. Reconstruct physical operations from starting stock through every experimental branch, with resource allocation, state transitions, observations, recovery and final disposition.
3. Identify instruments and accessories separately; inspect official manuals, product images, dimensional resources and available CAD before geometry authoring.
4. Build a revised metric apparatus and device assets, with removable/movable parts and operation-to-part bindings. Compare source and reconstructed views.
5. Validate package structure and causal walkthroughs, exercise meaningful negative cases, review visual evidence and retain separate design, geometry and execution decisions.

## Initial findings from renewed source inspection

- The supplement's apparatus drawing includes a 30.5 cm frame span that was absent from the earlier material card. Its measurement endpoints must be recorded rather than treated as every base dimension.
- The rooftop photograph shows paired apparatus, individual foil-covered bases and support stands, a separate protected DAQ enclosure, ambient radiation shield and weather station. They are distinct physical objects.
- The thermal-map illustration supplies sensor surface/radial relationships, although exact attachment coordinates and tolerances are not manufacturing specifications. Those relationships can support explicit inferred placement instead of a disconnected probe rack.
- The source identifies the Cary 5000 with DRA-2500, Nicolet 6700 with PIKE IntegratIR and separate angular accessories, USB-TC, Keithley 2000 and 2425, Thermo A25, EKO instruments and HOBO U30. Generic optical and logger consoles lose those identities and interfaces.
- The source retains a nominal 15 cm reflector height in text and a 10 cm dimension in the supplement drawing. The revised reconstruction must name its selected datum/geometry and preserve the unresolved historical discrepancy.

Review of this pilot does not certify the other 43 families. Dataset totals must count this as a revision of the existing cooling DOI, not a new paper.

## Reviewable implementation

The [v3 task package](../../tasks/directional_cooling_operations_v3/README.md)
contains 64 operation definitions, 352 observable reference steps, all 11 physical
branch definitions, source/inference records and a fixture-dependent 365-occurrence
symbolic walkthrough. The [v2 asset revision](../../assets/cooling_scene_assets_v2/README.md)
contains editable metric geometry, a GLB export, named parts and inspection renders.
The [conversion review](../../tasks/directional_cooling_operations_v3/review.json)
and [visual review](../../assets/cooling_scene_assets_v2/VISUAL_REVIEW.md) retain open
gates; this is an initial review revision, not an accepted gold-standard release.

## Current focus

The owner's latest instruction establishes **asset and laboratory scene
acceptance first**. Current work is inventory reconciliation, manufacturer-
grounded asset reconstruction, indoor/outdoor scene layout, safe-use review
and sufficient space for the complete humanoid. New manipulation-sequence
development resumes only after the owner accepts the concrete asset/scene
revision. Existing operation definitions remain requirements for identifying
assets and interfaces; geometric access checks may proceed during scene work.

Use the [laboratory acceptance gates](../contributing/REVIEW_CHECKLIST.md#laboratory-scene-review-before-pilot-manipulation-development),
[asset inventory](../../assets/cooling_lab_v1/inventory.json) and
[phase record](../../assets/cooling_lab_v1/acceptance_contract.json).
The inventory captures 43 existing resource rows plus explicitly authored
infrastructure/robot requirements; grouped rows still need decomposition and
instance allocation. A new [interactive laboratory review](../../viewer/lab_review_v1/index.html)
now places 19 device/body instances in an authored four-zone scene. Original
geometry supplies benches, shelves, fixtures, carriers, spill containment and
unqualified extraction/control designs. These are not load-rated commercial
furniture or certified engineering services. No owner acceptance is recorded.

The room shell now includes six actual glazed wall openings, framed double-door
portals with wall headers, 600 × 1200 mm ceiling infill panels at a 3.33 m
underside, recessed lights and diffuser grilles replacing selected grid cells, wall raceways with capped service plates,
and bench cabinet pedestals. Floor texture and signs are original generated
assets. These are authored design details; the lights and grilles do not
constitute an illumination or ventilation design. Door geometry and overhead
solids stay in the checks when the viewer uses a visual cutaway. Static routes
are checked against a 2.10 m standing-height probe; the lowest door header is
2.20 m. The interface opens inside the room at a 1.65 m eye height. Drag to
look, use arrows/WASD to move the observation point, or choose a room preset.
Viewpoint collision guards only prevent browsing through registered obstacles;
they are not a robot navigation controller or whole-body motion validation.

Furniture now has 1.5 mm edge breaks (2 mm at worktops), separate cabinet
carcass panels and drawer gaps, handle rosettes, screw heads, leveling bolts
and rubber feet. Windows have glazing beads; door handles have standoffs and
hinge barrels. These details preserve the declared outer furniture dimensions.
The authored sRGB palette is converted to linear glTF colour factors. Seeded
normal and metallic/roughness maps distinguish resin, paint, rubber and brushed
metal appearances; they are visual design choices, not measured material or
chemical-resistance data. See the [appearance review](../../assets/cooling_lab_v1/appearance_review.json)
for provenance, manufacturer-photo spot checks and remaining discrepancies.

The renderer recovers missing normals without changing triangle positions.
This fixes absent received shadows on imported geometry. Approximate indoor
reflection lighting and fixture-positioned preview lamps improve surface
readability; they are not a photometric reproduction. Renderer-only batching
reduces 4,007 mesh draws to 276 while checking unchanged triangle counts and
bounds (tolerance 1e-5 m). Independently movable covers retain their original
node identifiers. The [pixel regression](../../viewer/lab_review_v1/RENDER_VERIFICATION.json)
compares shadow reception on/off under unchanged lighting and confirms the
original view is restored. These images and checks do not establish fidelity.

The main indoor area is 12 × 10 m; fabrication and coating annexes are each
6 × 5 m; an open ground-level measurement area is 12 × 8 m. This is a proposed
robot laboratory, not the paper's original rooftop/room reconstruction.
Main circulation is 2 m wide; other declared routes are at least 1.6 m,
with 2.4 m diameter turning reservations. These are design values. An audit
of 401 samples of the existing H2 unloaded-body recording found a maximum
radial extent of 0.642905 m about the free-base XY position. Layout checks use
a 0.65 m probe plus 0.10 m authored margin; exact Dex5-S Pro geometry, loads,
walking, stopping and other joint configurations remain unqualified.

The EKO MS-56, unventilated MS-402 and HOBO U30 now have separate source-based
candidate geometry. Their [source and dimension ledger](../../assets/cooling_lab_v1/outdoor_assets.json)
records the inspected manufacturer drawings, hashes, inferred local dimensions
and unresolved historical variants. The UI links directly to the relevant
drawing pages. Manufacturer photographs/PDFs are not redistributed. Imported
earlier assets retain their original physical dimensions and source hashes.
All device models still require individual product-fidelity review.

The [layout report](../../assets/cooling_lab_v1/layout_checks.json) checks
corridors, overhead clearance, working/turning areas, supports, asset/fixture separation and sampled
external opening sweeps. Cary, Nicolet, A25 and U30 opening states can be
inspected in the browser; they are geometric state changes, not robot actions.
Internal instrument contacts are not checked by these opening sweeps.
The [risk register](../../assets/cooling_lab_v1/risk_register.json) retains
load, utility, ventilation, service, outdoor and site-application gaps.
Missing exact hands, angular accessories, sensors/wiring, fabrication machinery,
tools, consumables, waste and robot service provisions prevent full acceptance.

To reproduce this review from the repository root, use a Python environment
with `assets/cooling_lab_v1/requirements.txt` installed and a Chromium executable:

```sh
python assets/cooling_lab_v1/check_body_envelope.py
python assets/cooling_lab_v1/build_outdoor.py
python assets/cooling_lab_v1/build_lab.py
python assets/cooling_lab_v1/check_layout.py
python assets/cooling_lab_v1/build_review.py
python assets/cooling_lab_v1/validate_review.py
python simulation/cooling_v1/serve.py --port 8769
# In a second terminal, substitute the installed Chromium path:
python viewer/lab_review_v1/check_browser.py --browser /path/to/chromium
python viewer/lab_review_v1/check_rendering.py --browser /path/to/chromium
```

The validator deliberately lowers a header into the standing envelope, blocks
a route, shrinks an instrument support, overlaps a device with a carrier, and
obstructs a cover sweep; all five faults
must be rejected. Browser checks exercise visible open-state changes, views,
measurement, inventory filters, revision-bound comment export, mobile layout
and stale-scene rejection. GLB bytes are SHA-256 checked before display.
These software checks do not close any of the eight laboratory acceptance gates.

As of 23 October 2026 the final executor is a Unitree humanoid with its own
arms and Unitree Dex5-S Pro hands, following the
[embodiment requirements](../PROJECT_VISION.md#humanoid-execution-target).
Existing Panda recordings are historical component tests. The humanoid
body now has a [standing and unloaded bilateral wrist-motion foundation](../../simulation/humanoid_v1/index.html).
Its official H2 meshes, physical trace, torque replay, five test cases and
continuous video are retained in `simulation/humanoid_v1`. Exact Dex5-S Pro
hand integration and every migrated manipulation remain unqualified; none
of the historical Panda receipts counts as a humanoid manipulation episode.

The pilot is being polished as one complete paper-derived manipulation task chain.
The [manipulation dossier](../../tasks/directional_cooling_operations_v3/MANIPULATION_REVIEW.md)
shows all 200 manual steps alongside the experimental conditions and checks that
connect them. Each manual step identifies its object/interface, tool, retained
support, observable completion and recovery. Scientific-result agreement and
robot execution are separate validation questions.

The October 17 pass corrects calibration preparation and terminal compatibility,
angular reference ordering, apparatus disassembly/reassembly and thermal-map
probe placement. Source-based terminal geometry now uses exact numbered pin IDs;
the fixed-band variant has two nominal 50 micrometre LDPE layers. Remaining
interface gaps are itemized, and the earlier review remains preserved.

The October 19 contact workbench adds robot records for
six rigid layers, a prebonded two-film cover, a full-length cabled RTD, physical
multimeter button actuation, 241 installed-reflector adjustments and a cabled
source-meter plug. The [visual workbench](../../simulation/cooling_v1/sample.html)
shows the full recordings and links their evidence. Its
[reproduction instructions](../../simulation/cooling_v1/README.md) include the
local server and lossless trace archives. Keithley 2000/2425, Omega P-M RTD and
KHR-2/2-P assets have separate source, part, interface and geometry records.

The cover record is rejected by the added triangle/solid audit: its earlier
force/position checks missed film penetration into the PE tube. The other
records establish bounded physical capabilities. Subsequently, two complete
seven-layer Panda assembly/recovery recordings passed 192 independent checks
each. Frame and film preparation, paired apparatus, station handoffs and
remaining instrument work are still incomplete. Humanoid execution requires
fresh qualification of all operations. No complete branch or new paper is
counted from these records.
