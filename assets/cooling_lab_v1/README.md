# Directional-cooling laboratory review

Current phase: asset and scene development. No owner acceptance, whole-body
clearance, sensor-only manipulation or complete paper campaign is claimed.

Serve the repository root and open `/viewer/lab_review_v1/index.html`.
The linked `/viewer/lab_review_v1/ftir.html` compares two accessory installation
candidates against the instrument, with separate floor, mounting hardware,
cover and extraction controls. It retains failed fit results; it is not an
accepted operating configuration or robot animation.
The existing local server uses port 8769. The scene contains the complete
official G1 29DoF + Inspire FTP geometry, three ordinary tool types and a
selected OMAX ProtoMAX waterjet. Geometry sliders and the 87 per-point static
access postures are inspection tools, not physics-controlled robot actions.

The native G1 D435i supplies nominal head RGB and ideal geometric depth
inspection views; the two D405 wrist views use an unaccepted mounting
candidate. The original Unitree STEP collar is undersized for this G1 wrist.
The current derivative retains the official camera arms and replaces both
collar halves, without rescaling the robot or cameras. Exact triangle checks
screen rigid clearance at sampled finger configurations and all 87 station
postures. Compliant lining, preload, retention and cables remain unresolved, so
these attachments are hidden by default and do not count as an installation.
The viewer can display them for fit review, and records separate attachment
conflicts at each station pose. D455 remains an optional bench reference.
Camera previews retain scene occluders even when the reviewer isolates an asset
or hides walls. They are ideal pinhole renderings, not calibrated observation
streams. See `assets/g1_sensor_rig_v1/README.md` for provenance and limits.

Eight Omega 5TC probes are staged separately, with catalogue-sized conductors
and inferred stored cable shape. They have no flexible or electrical model.

## Rebuild

Use the pinned geometry dependencies in `requirements.txt`; the existing
`/tmp/sciencegym-sim-venv` also contains Playwright for browser verification.

```bash
OPENBLAS_NUM_THREADS=1 /tmp/sciencegym-sim-venv/bin/python assets/cooling_lab_v1/rebuild_review.py
```

After serving the repository, include the local browser executable for visual
checks and refreshed screenshots:

```bash
OPENBLAS_NUM_THREADS=1 /tmp/sciencegym-sim-venv/bin/python assets/cooling_lab_v1/rebuild_review.py \
  --browser /tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell
```

The rebuild runs source asset generators, the scene generator, static layout
checks, inventory/readiness reconciliation, source verification and negative
policy tests in dependency order. Browser checks are optional only for a
nonvisual rebuild; a changed review release needs renewed visual evidence.
The pinned L200/M STEP/PDF are fetched into an ignored local cache when absent;
existing files are verified without a network request. A changed upstream hash
fails instead of silently selecting another version. Other source bundles must
already be present. The rebuild cannot silently switch robot models.

## Central support from manufacturer CAD

The linked `/viewer/lab_review_v1/lift.html` inspects a selected Thorlabs L200/M
mini metric jack from the official 12298-E0W STEP and revision H drawing. It
retains all 86 source solids, the 101.6 × 76.2 mm plates, 16 links, actual plate
bores/edge slots and the hex adjuster. Its source pose is 21.336 mm high, consistent
with the drawing's rounded 21.3 mm retracted height. The 47.8 mm extended height
is a drawing fact; no invented extended CAD or jack actuation is supplied.

`assets/thorlabs_l200_v1/sources.json` pins both official files and separates
manufacturer facts from this candidate choice. The paper's exact jack identity
is unknown. STEP/PDF and derived GLBs remain in ignored local directories because
no open redistribution license was established. The fetch/conversion recipe,
measurements and original review renders are included in the repository.
For this separate inspection alone, run:

```bash
python assets/thorlabs_l200_v1/fetch_sources.py
OPENBLAS_NUM_THREADS=1 python assets/thorlabs_l200_v1/build.py
OPENBLAS_NUM_THREADS=1 python assets/thorlabs_l200_v1/check.py
OPENBLAS_NUM_THREADS=1 python assets/cooling_lab_v1/build_apparatus_stock.py
OPENBLAS_NUM_THREADS=1 python assets/cooling_lab_v1/check_apparatus_mounting.py
python viewer/lab_review_v1/check_lift.py --browser <chromium-executable>
```

Four bearing blocks initially had collinear T-junctions in the tessellation.
Fourteen edge subdivisions close those seams using existing vertices, with no
moved vertices, filled physical holes or material-volume change. The original
four failed meshes remain locally reproducible negative fixtures. Hard-edge
normal splits preserve flat plate surfaces in the renderer; those intentional
render seams are distinguished from physical openings. All 86 delivered solids
are closed, and actual ray tests check each plate's 29 bores and six edge slots.
Bounding-box replacements and a genuine missing-face mesh fail the corresponding
geometry expectations. Source changes or missing local CAD prevent the browser
from displaying an unverified model.

The three completed-state reference configurations now include the source-scale
jack and a nominal central mounting. Four measured M3 source centers at
X ±37.4904 / Y ±12.4968 mm connect a 6 mm acrylic base using M3×10 socket-head
screws and 9 mm OD large washers; a 170 × 170 × 5 mm aluminum platform uses
M3×8 ISO 10642 countersunk screws. Actual 3.4 mm through-holes and 6.72 mm
countersinks are modeled. The acrylic has straight holes, not countersinks.
The source plate thickness at these holes is 5.588 mm; nominal insertion is
3.188 mm below and 3 mm above. Threads are major-diameter envelopes, not helical
contact geometry. Small tessellation overlaps at those declared interfaces are
recorded, never interpreted as force or thread qualification.

`apparatus_mount_sources.json` separates catalogue facts and selected mounting
inferences. `apparatus_mount_checks.json` checks actual exported vertices, holes,
support planes, sockets and nonmating jack intersections. The thermal and
reflector components move together to preserve their relative height. Legacy
disconnected sensor placeholders are removed; real probes remain staged.
Two loose jacks and 24 individual mounting pieces are separate initial stock;
a fourth aluminum raw plate reserves both platforms. The inspection page can
switch to the actual mounting core, hiding the thermal stack and outer frame.

All full apparatus/prepared composites containing the manufacturer's CAD are now
ignored local build outputs, as is the dedicated mounting inspection GLB. A fresh
clone must run the rebuild before displaying them; there is no fallback to the
old placeholder mechanism. The original historical input bundle is unchanged.
Top screw access needs the thermal stack absent; underside screws need a
supported state with the bottom accessible. Physical threads, preload, acrylic
stress, loads, frame/upright/track mechanics, film/shield retention, tools and
cables remain open. These are static candidates awaiting asset acceptance.

The first shelf placement was too deep: all three selected stock approaches
could reach the palm target but intersected the shelf with a shoulder link.
`lift_stock_access_rejected.json` retains those observed failures. Moving the
stock 300 mm toward the aisle keeps it on the shelf and yields clear candidates
under the same static screen. The failure poses are replayed against the real
shelf geometry; neither placement establishes a pickup or continuous path.
It adds no campaign-success or installed-equipment credit. The top-plate slider
is an exploded inspection, not the jack's travel or a robot operation.

## Review artifacts

- `pilot_contract.json`: owner choices and future qualification targets.
- `scene.json`, `inventory.json`: exact models, placement, references and resource
  groups. Counts indicate candidate geometry, not accepted inventory completeness.
- `readiness.json`: manual-step resource crosswalk, compound resource decomposition,
  branch definitions and blockers. Quantity allocation is still incomplete.
- `ordinary_tools_sources.json`: inspected catalog facts and authored assumptions.
- `waterjet_sources.json`, `stock_sources.json`: selected fabrication-machine
  evidence, source conflicts, paper-derived sheet thickness and stock inferences.
- `angular_accessory_sources.json`: inspected Harrick stage/base and Spectra-Tech
  catalogue evidence, including the Nicolet 6700 optical direction. These define
  the two bench-staged candidates in `angular_accessories.json`. Outer scale,
  local mechanisms, mirror curvature/positions and mounting remain inferred.
  `angular_accessory_checks.json` tests real mask openings and 54 sampled rigid
  inspection states. No installed, optically aligned or robot-operated state is
  qualified. The HRS stage includes its required base; its sloped mirror is solid.
  `angular_mount_followup.json` records the separate instrument-floor and ordinary
  mounting-hardware investigation, without assuming cross-brand compatibility.
  `angular_appearance_review.json` pins 14 browser views and records source matches,
  visible differences and remaining dimensional/mechanical hypotheses.
  The Spectra-Tech schematic labels M4 as the specimen/reference surface. The
  rejected extra-mirror topology is preserved in `angular_topology_rejected.json`.
  Its replacement has four independent mirrors and a removable M4 reference in
  the actual holder. M3 and M4 share an explicitly inferred 105-degree carrier,
  with extended faces instead of mirrors centred on one initial ray hit.
  The rejected perpendicular rotor remains in `angular_rotor_rejected.json`.
  Actual-triangle tracing checks 594 selected parallel rays at 66 angles from
  20 to 85 degrees, including intervening parts, front faces and the exit.
  Missing-reference, blocked-port and full-width-stop counterexamples fail.
  These probes do not establish the manufacturer's beam, focus or linkage.
- `ftir_mount_sources.json`, `ftir_mounts.json`: manufacturer floor dimensions
  and optical/cover datums, a separate factory-floor candidate and two ordinary
  mounting hypotheses with 38 hardware parts. The original staged assets stay
  unchanged. `ftir_mount_checks.json` retains the Spectra-Tech closed-cover and
  driver-access failures, and the Harrick ray-offset/alignment collision.
  Both revised adapters clear 25 nominal open-bay vertical samples. The previous
  purge-outlet conflict remains in `ftir_mount_rejected_purge.json` and its exact
  GLB; it must still fail. An audit pass is not an installation pass.
  `viewer/lab_review_v1/FTIR_MOUNT_VERIFICATION.json` pins 16 actual installation
  views and independent mesh-transform checks. Rebuild with `build_ftir_mounts.py`
  then `check_ftir_mounts.py`; run `viewer/lab_review_v1/check_ftir.py --browser
  <chromium-executable>` against the same localhost server for browser evidence.
- `assets/unitree_g1_inspire_v1/space.json`: source-derived body/hand bound
  at 129 restricted static poses, with exact official wrist transforms.
- `workspace_checks.json`: 87 separately tested palm-position targets, including staged supply approaches, two heater instances and two angular-accessory approaches, with proposed camera-clearance screening; records
  candidate joint coordinates, position errors, external obstacle conflicts and
  self-penetrations under the provisional collision model.
  Orientation, grasping, target-device internals, balance and paths are excluded.
  The Cary keyhole datum is preserved separately from an authored 80 mm upper
  palm approach; neither it nor the other approach offsets is a grasp frame.
- `hand_envelope.json`: historical H2/Dex5 sensitivity record, unused for G1.
- `acceptance_contract.json`: eight open review gates and their exact-revision
  evidence. Comments in the browser are not acceptance receipts.

Manufacturer images/documents are linked and hashed where locally inspected,
not redistributed. Instrument reconstructions are original; the selected G1,
hands and cameras use licensed official source meshes. The G1 integration
retains source inertials and wrist transforms but has provisional contact and
actuator parameters. Review view names follow asset axes, not calibrated photographs.

The active implementation plan is
`docs/pilots/DIRECTIONAL_COOLING_IMPLEMENTATION.md`. Existing Panda task inputs
and privileged-state body tests are historical references only.

The latest selection is G1 29DoF + Inspire FTP, under the owner's Unitree-body /
open-hand instruction. The lab now places that complete source-derived combination; H2 and Dex5-S
remain unplaced historical inventory references.
The official integrated candidate can be inspected at
`viewer/robot_resource_review_v1/index.html`. The 66 inventory rows include
three superseded robot/hand references; these are not additional required robots.
The active scope is 63 resource groups / 147 component needs. The viewer keeps
three historical choices in a separate filter and excludes them from current
missing-asset counts. Of 63 active groups, 62 have partial geometry and one
have none; this is not a completeness percentage.

## Added ordinary supplies and collar revision

The scene now contains 74 placed instances. `supplies.json` binds twenty-eight
additional reconstruction types: ST-450, AA.SA.T.6 tweezers, Wiha 26015,
Bürkle 7102-2000, the source-identified ambient RTD, eight separate K-connector
pairs in an ordinary tray, three film-stock types, masking tape, unmachined
copper stock, a Rubbermaid 1997206 cart, a Justrite 09100 wipes can,
OMAX 317864 workholding, Knipex 78 03 125 cutters, Noga RB1000/S10 deburring
and Pomona 5908A meter leads, plus detached G1 battery and charger candidates, flat-white/black ColorMaster
stock cans and a PELCO 16032 silver-paste candidate bottle, plus separate copper,
aluminum, foam, acrylic, PE-tube and aluminum-tube stock.
`supply_sources.json` separates manufacturer facts, paper facts, selected
quantities, local inferences and unresolved functionality. `supply_checks.json`
checks the actual meshes: catalogue envelopes, open cup and cart cavities,
vented probe, six-foot lead, connector containment, stock thickness and grounded
wheels. These checks do not promote staged stock to a completed manual step.
The waste-can lid has a 60-degree geometry inspection state; pedal coupling and
self-closing are not simulated. The cart's carried route and tipping model remain
open. These supplies cover only part of the compound resource requirements.

The south-side ordinary service bench has a dedicated viewer shortcut. A spare
G1 battery follows the official 2024 V1.0 dimensional views, with separate latch
paddles and recessed connector envelopes. The disconnected charger follows that
manual's envelope; current official ratings differ, and the matching hardware
revision and terminal geometry remain unresolved. Both remain inspection assets.
The shared approach area is part of the south cross-aisle and cannot be used for
storage. This bench does not establish a qualified charging location, autonomous
battery replacement or a complete robot-service facility. Ordinary service tools
and the charging/service method are still missing.

Three coating-stock candidates now occupy the coating preparation bench:
ColorMaster flat-white/black cans and a PELCO 16032 silver-paste bottle. The
manufacturer photographs and catalogue references constrain their profiles;
their dimensions remain explicit hypotheses, displayed as such in the viewer.
The caps are separate hollow parts with exploded inspection views. The silver
bottle has an open mouth and nominal stock volume from 25 g / 2.25 g/ml.
Thread engagement, snap fit, spray/dispensing, material compatibility and cure
are unqualified. The paper identifies neither paint SKU nor silver-paste brand.
Manufacturer artwork is not embedded; labels are original identification text.
The review canvas uses supersampling instead of MSAA after an observed
SwiftShader depth artifact on cylindrical labels. Normal depth tests and
foreground occlusion remain enabled; sensor target resolution is unchanged.
The exact ColorMaster flat-white SDS, ordinary application tool and accepted
coating/adhesive allocation remain missing. Adding these models does not close
the consumable, ventilation or waste-handling acceptance requirements.

The D405 rig has a new explicitly authored G1 collar, retained official camera
arms and standard fastener meshes. Original source parts remain as failure
fixtures. Positive rigid clearance and camera screw insertion are checked;
lining, preload, cable routing and dynamic loads remain open. See
`assets/g1_sensor_rig_v1/README.md` for scope and reproducible CAD construction.

The access screen uses separate rack shelves and uprights, retains stock obstacles,
and excludes only the target device interior under its stated review scope.
Route checks still reserve each entire rack footprint. Film stock is staged on
the middle shelf; tape and copper are near the accessible bench edge. The wipes
can target is a selected release approach above its rim, not a low rim grasp or
a demonstrated pedal/lid/disposal sequence.

`readiness.json` combines `staged_supply_bindings.json` with optical-accessory,
jack and frame stock records to bind forty-two component needs to actual scene
instances and named parts. Film sheets and connector pairs are counted
individually; the same two tweezers are explicitly shared across handling roles.
`readiness.json` pins these geometry identities and exposes staged quantities
separately from still-unallocated campaign requirements. The inspector shows
these counts and all resource associations for multi-purpose assets.

The preparation assets retain separately inspectable parts: five catalogue-length
clamp arms with actual post bores, four posts, four T-nuts with through-holes,
two cutter levers, and a replaceable-blade deburring-tool reconstruction.
The clamp post, bore, thread and rail dimensions remain explicit local hypotheses.
The deburring holder uses the catalogue's 12 mm hexagon; its unreported length
and blade curvature are inferred. The cutter's 0.2 mm minimum soft-wire capacity
does not establish suitability for the finest thermocouple conductor.

Two staged meter-lead assets contain eight separate 48-inch leads in total,
each measured between its moulded cable entries. Straight plug bodies add
2.7 inches at each end and include open insulating shrouds, recessed contacts,
spring leaves, grip guards and strain relief. The separated coiled poses are
authored inspection geometry. No plug mating, cable settling, bending mechanics,
electrical circuit or heater-side adaptor is qualified. The four workholding
T-nuts also satisfy a staged accessory-fastener binding; they are shared
inventory, not four additional nuts or cooler-frame fasteners.

`preparation_review_inputs.json` records preparation and robot-service searches, reference
views actually inspected, failed downloads, rights and unresolved discrepancies.
After browser verification, `build_preparation_review.py` produces
`preparation_review.json`, pinning the exact geometry, front/back/side/top and
oblique model captures, source facts and resource-associated review obligations.
The inspector links this comparison for each new asset. Associations are not
accepted operation-to-part bindings. Missing reference views and all acceptance
decisions remain explicit; CAD download listings are not downloaded CAD.

`campaign_allocation.json` accounts for all 147 active component requirements
and the eleven branches. Seventeen core equipment/probe components and thirteen stock
components have explicit selected quantities; the other 117 retain
unknown required quantities. These
counts describe allocation work, not asset completeness. The paired power branch
now has two separately staged KHR-2/2-P candidates, `heater_white` and `heater`,
and two separate 2425 instances. Compatibility, mounting and wiring remain open.

The white and black apparatus keep their identity through the selected tracked,
fixed and restored configurations. Their completed-state meshes, the separate
fixed-configuration display and the alternative D455 reference are excluded from
initial-stock credit. Final optical specimen formats, fixed-conversion connecting
hardware, manufacturing tools, services and repeat/reset consumption remain open.
`check_allocation.py` rejects duplicate unit counts and display-as-stock claims;
it also reproduces the previous missing-second-heater deficit. The interactive
review at `viewer/lab_review_v1/allocation.html` filters by branch, component and
unallocated demand, and rejects a report whose source hashes have changed.

`stock_cutplan.json` reserves 63 cut envelopes or witness regions on 28 actual
stock sheets/blanks, eight hollow-tube sections and four purchased profiles. It measures the selected apparatus
meshes, keeps 1 mm edge/cut allowances, and separately reserves fresh nano-PE
for white-apparatus restoration and film stock for optical witnesses. The
allocation page displays each sheet to scale. These envelopes are not executable
tool paths or fabricated outputs; final sample holders and machining processes
remain unqualified. Six stock categories are separate inspectable scene assets.

The old 300 × 250 × 3 mm acrylic could not produce the selected 305 × 280 × 6 mm
base; two 350 × 300 × 6 mm plates now reserve the pair. Three 500 × 300 × 12 μm
metallized-PET candidates replace the undersized 160 mm squares. Goodfellow
ES30-MZ-000112 / 579-110-25 supplies the nominal candidate specification, not
proof of the paper's Mylar identity or optical equivalence. The derived custom
apparatus foil uses the same nominal gauge, complete base coverage and inferred
3 mm overlap seams. The legacy Blender input stays immutable. The mounting
record explicitly lists replaced, added, removed and vertically translated
parts; remaining apparatus vertices retain exact float32 export values. Film attachment,
load paths, flexure and optical performance remain unresolved.

`check_stock_cutplan.py` rejects the retained old acrylic/Mylar/LDPE stock and
overlapping reservations, checks thickness against actual output meshes, hollow
tube diameters, nominal foil coverage and the listed foil size lower bound.
The first coarse foil mesh intersected the substrate by about 1.9 μm; that
actual failed mesh remains in `foil_mesh_rejected.json`. The current nine wraps
have no FCL triangle intersections with their substrates after circumscribed
tessellation and a recorded sub-micron export allowance. This numerical allowance
is separate from film thickness and does not model adhesive or compliant contact.
`stock_cut_checks.json` records dimensional evidence only. Ordinary machining
tools, coatings, adhesives and repeated-run consumption still need allocation
before a complete asset review can be accepted.

The loose heater access points are palm approaches 100 mm above the thin parts,
not pickup contacts. The former 40 mm approaches produced wrist/bench overlap
and shoulder/torso penetration. Both failed poses remain in
`heater_access_rejected.json` and are replayed by the review validator. Targeted
workspace diagnostics can use `check_workspace.py --targets <ids> --output
<separate-path>`; they cannot overwrite or substitute for the complete report.

The current frame is inspectable at `viewer/lab_review_v1/frame.html`. Its
nominal 20-2020 cross-sections replace overlapping boxes; 305 mm inner spacing,
base-side placement and outboard uprights follow the paper's topology. Public
dimensions constrain the ordinary fasteners and adhesive feet. Bridge plates,
split clamps, reflector backing plates, bore lobes and undimensioned blends
are authored selections, not vendor CAD or confirmed historical parts.
The selected 395 mm tracks fit the existing 400 mm stock after shifting their
cut reservations to a 2 mm starting margin; the 1 mm edge allowance remains.

`check_apparatus_frame.py` checks exported solids, actual holes, nominal bearing
planes and solid intersections. The sharp T-nut envelope failed against the
diagonal web; `frame_sharp_tnut_rejected.json` retains its real failed mesh.
An explicitly inferred deep-side chamfer resolves nominal interference, but
does not establish manufacturer tolerances or physical compatibility. The
checker uses Manifold solid intersection volumes because FCL reported large
depths for coincident planar contacts. Tiny screw/thread/seat tessellation
intersections are separately recorded without force or installation credit.
Ordinary machining/tool and reset allocation are still incomplete;
clamp mechanics, adhesion, reflector travel, cover support and cable routing
remain open before the complete scene can be submitted for owner acceptance.

`frame_stock.json` separates 95 initial-stock units from the completed references:
four purchased 340 mm profile lengths, four uncut 250 mm upright tubes, three
aluminum blanks and 84 ordinary fastener/pad units. The eight pads include
separate inferred release liners, giving 92 hardware meshes. Screw resting
poses use actual geometry and a uniform-density assumption; long screws lie
low instead of standing on their heads. This is a static placement hypothesis,
not a settled physical state or demonstrated pickup.

The three blanks reserve 20 bridge, clamp and reflector-carriage outputs.
Upper carriage plates require facing the selected 4 mm raw plate to 3.75 mm;
the cut plan records raw and finished thickness separately. Cut outlines do
not establish drilling, threads, clamp slots, facing or workholding. The four
upright tube reservations preserve actual output length plus cutting allowance.
Hardware units and part bindings are distinct; negative checks reject a missing
T-nut and a duplicated physical part instead of counting either as sufficient.

The first machining-stock placement overlapped the existing aluminum-tube
stock. `frame_stock_layout_rejected.json` and its retained world-space GLB
preserve that observed overlap independently of later scene rebuilds. Moving
the machining blanks 390 mm left removes it while retaining shelf support.
`frame_stock_checks.json` checks nominal quantities, exported solid geometry,
rigid hardware shape preservation, resting envelopes and the failed layout.
These three stock assets are inspectable individually in the main viewer and
their reservations appear in the allocation page. They add no assembly,
campaign-success or asset-acceptance credit.
