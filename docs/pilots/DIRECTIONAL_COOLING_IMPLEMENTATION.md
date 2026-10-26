# First-paper humanoid demo implementation

Owner choices updated on 24 October 2026, including the later open hand selection. This is the active execution plan for
the Bhatia directional-cooling pilot, not a completion receipt.

## Completion target

Cover all eleven existing physical branches and their shared preparation,
transfers, configuration changes, recovery and cleanup, using the selected
Unitree humanoid and its own articulated hands. Preserve the paper's source
facts, explicit reconstruction inferences and object lineage. Scientific-result
agreement and physical-hardware experiments are outside this demo's acceptance.

The machine-readable [pilot contract](../../assets/cooling_lab_v1/pilot_contract.json)
records the latest owner decisions: the body remains Unitree, while publicly
supported hands from other manufacturers are allowed. Select G1 29DoF rev 1.0
with Inspire FTP left/right for the current asset integration, based on the
[official resource audit](HUMANOID_RESOURCE_SELECTION.md). The actor must use
robot sensors; adaptations remain limited to added cameras and ordinary tools.
Robot-specific fixtures and added fiducials are excluded. The previous H2 /
Dex5-S assets and body evidence remain historical references.
Model acquisition and static inspection grant no manipulation qualification.
The owner's development authorization is recorded below.

## Delivery order and acceptance

On 26 October 2026 the owner explicitly authorized parallel scene and G1
manipulation development for the one-hour delivery sprint. The exact reply and
scope are retained in `assets/cooling_lab_v1/development_authorization.json`.
This supersedes the sequencing restriction below, but grants neither scene
acceptance nor manipulation qualification and does not change the full target.

1. **Assets and laboratory.** Decompose and allocate all required resources;
   reconstruct commercial equipment from inspected manufacturer sources;
   represent operational parts and access states; check complete humanoid,
   hand and carried-load geometry. Deliver a source/model comparison and a
   dimensioned interactive scene. Acceptance of this exact revision remains
   pending; the later authorization permits parallel manipulation development.
2. **Sensor-driven capabilities.** Add calibrated head RGB-D and bilateral wrist
   RGB observation models, plus evidenced proprioceptive/contact channels.
   Isolate the controller process from simulator truth and evaluator records.
   Implement perception, stable support, motion, tool use and manipulation
   with observable success and bounded recovery. The camera configuration is
   currently a proposal, not installed hardware or a simulated sensor receipt.
3. **Paper campaign.** Bind every manual step to concrete instances, perception
   and action interfaces. Preserve identity and state across stations and
   branches. Automatic device processes may be represented explicitly after
   robot setup; no manual work may disappear into a process receipt.
4. **Repeatable delivery.** Package reproducible runs, continuous videos,
   sensor and physics traces, independent verdicts and failure evidence. Extend
   the existing localhost review rather than claiming playback is a new run.

Engineering targets are 19 successes from 20 preregistered trials per required
skill, 9 from 10 per branch, and three consecutive complete campaigns without
human takeover. Declare source-based perturbation ranges before testing; retain
all failures. Missed grasps, slips, incomplete connections, blocked covers and
sensor failures must be recognized. These targets do not imply a statistical
guarantee of general reliability.

## ScienceGym manuscript after demo delivery

On 27 October 2026 (Asia/Singapore), the owner requested an illustrated
ScienceGym research manuscript **after completing the demo**. This is an
additional deliverable; manuscript preparation must not displace the current
demo repair and validation work. The current repository does not bundle a
ScienceGym manuscript. Its README mentions an earlier manuscript outside this
release, whose text and figures must be located and reviewed before reuse.

After the demo is complete, write a full manuscript with an editable source,
compiled PDF, references, and separately exportable figures. Explain the
paper-to-manipulation reconstruction method, evidence and inferred steps,
task and state representations, source-backed assets, humanoid execution,
controller/evaluator separation, and reproducible evaluation. Include a
system overview, a worked paper-to-task example, laboratory and asset figures,
an annotated operation sequence, and plots based on recorded outcomes.
Use actual traces for results and failures; the presentation film supplies
illustrations only. Do not claim 1,000 completed papers, qualified branches,
or success rates without the corresponding evidence. Venue-specific formatting
can follow once the manuscript and results exist. The owner has authorized
writing this paper, but has not requested journal/conference submission.

The manuscript package will be maintained under `manuscript/sciencegym/` once
writing starts, with `main.tex`, a bibliography, compiled PDF, and editable
figure sources. The planned figure set is:

1. ScienceGym system overview: paper evidence, reconstructed manipulation
   steps, task/state representation, sourced assets, execution and evaluation.
2. One worked reconstruction: an inspected paper passage or paraphrase linked
   to its operation chain, with inferred details distinguished from evidence.
3. Laboratory and commercial assets: dimensioned layout, robot access space,
   and source-to-model comparisons with source attribution.
4. A continuous demo sequence: actual rendered frames tied to timestamps,
   object identities and operation IDs, including grasp and release details.
5. Evaluation: plots generated from retained run records, covering the tested
   scope, trial counts, failures and recovery; untested claims remain explicit.
6. Failure analysis: examples such as contact errors or incorrect object-state
   transitions, together with the implemented corrections and their evidence.

Each figure and results table must identify its generating script, source
revision and input records so it can be rebuilt. Presentation frames and
measured simulation outcomes must be identified in their respective captions.
The introduction, related work, method, demo case study, evaluation, limitations
and conclusion should form a complete paper, rather than a collection of
project screenshots. The available results determine the paper's claims;
the intended future scale of 1,000 papers is not a completed dataset.

The presentation-film repair remains a prerequisite for this writing request.
The second development viewer now starts the Cary DRA and Nicolet IntegratIR
inside their instrument bays, with their own PTFE and gold standards at the
actual sphere ports. These are explicitly inferred initial configurations;
installation, detector cable mating, optical alignment and support stability
are not executed or qualified by their placement. The former flying specimen
into an empty instrument bay has been removed.

The two Nicolet cover phases now have a continuous arm solution and
collision-planned approach/withdrawal paths. Their
[`optical_07` sampled review](../../viewer/cooling_concept_v2/audits/optical_07/sampled_interaction_review.json)
checks 410 states at 0.1-second spacing, including phase boundaries: no sampled
robot/environment or unexpected self intersections, joint-limit or speed
failures, or sole penetration; maximum palm/pregrasp endpoint error is
0.198 mm. This is a geometric subtask result, not complete optical handling,
force/dynamics validation, full-film acceptance or branch qualification.
Earlier failed attempts remain available. The commercial cover's retention
at the selected 65-degree open angle is an unresolved mechanical inference.

The collision reviewers also now apply the instrument group's world transform
to static source parts that the viewer merges for rendering. Historical
aperture-cover and cart-room samples were rechecked after this fix and retained
their zero unexpected intersection counts. The historical lowered-idle
`idle_regression_04` revision was rejected for 108 robot/environment intersection
states during bench approach and withdrawal. Twenty collision-planned free-arm
paths now replace those transitions. A later aperture-cover IK branch jump
was resolved with continuous contact seeds and four revised path endpoints.
The independent [`approach_03` review](../../viewer/cooling_concept_v2/audits/approach_03/sampled_interaction_review.json)
checks 2,732 selected states at 0.1-second spacing: zero unexpected environment,
self or payload intersections, joint-limit/speed failures or sole penetration.
Its cart/room check covers 367 states. The two return-carrying routes omitted
by the original phase-name selection have a separate
[`return_01` review](../../viewer/cooling_concept_v2/audits/return_01/sampled_interaction_review.json):
207 states pass the same robot, payload and motion checks. Selection by action
is now available to avoid relying only on phase names. These are sampled
subtask reviews, not continuous-time, whole-film, contact-force or dynamics
qualification. Earlier failed attempts and their exact source snapshots remain.

The gold reference's initially protruding optical-face datum has been corrected
to a selected 0.05 mm recess behind the supporting shoulder. The manufacturer's
photograph establishes a central face within its holder, not this exact depth;
the dimension remains an explicit inference. Its installed source-mesh review
now reports no reference/port intersections. Screening 23 continuous left-arm
lift candidates yielded one 61-knot candidate without sampled intersections in
the stated planning region. That component began at a closed grasp and omitted
ankle meshes. It is now integrated with planned hand entry/exit, partial opening,
grasp closure, four grounded lateral steps, held-reference transfer, cap seating
and release. The complete source robot and laboratory were then checked in
[`reference_01`](../../viewer/cooling_concept_v2/audits/reference_01/sampled_interaction_review.json):
1,146 sampled states pass joint, sole, self, robot/environment and reference/
environment checks. Intended non-optical support contacts are bounded by
part identity, contact location, support height and a 1 micrometre tolerance;
the maximum reported numeric depths are 2.55 nm at the cap and 6.02 nm at the
port panel. Optical-face contacts are never waived. This is sampled geometry,
not force, balance, full optical procedure or film qualification.

A separate inferred protective-cap candidate supports the non-optical holder
shoulder while keeping the optical face 15.05 mm above its inner floor. Its
local 51-state hand-closure review reports no hand/cap/reference intersections;
the complete-asset candidate preserves the other 90 source parts exactly.
It is saved under `assets/pike_integratir_dtgs_v1/revisions/cap_support/` and
used by the development-only `viewer/cooling_concept_v2/runtime_scene.json`;
the original laboratory manifest and asset remain intact. Internal fit
dimensions are inferred, not manufacturer CAD or tolerances. The reviewers
now read and verify the manifest and geometry hashes frozen with each export.

The subsequent `reference_02` revision reorders the operation to match the
IntegratIR substitution method: retrieve the capped standard, place it on the
port, close the access for background, reopen, then remove and cap the standard
before specimen exchange. The standard starts and ends in protected storage.
Its [1,660 sampled states](../../viewer/cooling_concept_v2/audits/reference_02/sampled_interaction_review.json)
pass the independent joint, sole, self, robot/environment and reference/
environment checks. Background/sample scan controls and actual specimen
exchange are still placeholders, so this
sequence is not a completed optical measurement. The development timeline is
818.57 seconds long; no corresponding full movie has been rendered or accepted.

Reference/specimen
exchange, calibration, sensor installation, reflector locking and wiring
remain unfinished; no replacement full film or manuscript has been delivered.

## Laboratory contact integration

The G1 contact plant now imports the existing full laboratory instead of a
separate primitive workbench. All 81 base asset identities are accounted for:
G1 and the white tray are dynamic, and the other 79 assets remain fixed initial
obstacles. The original 6,537 environment parts retain their source triangles,
dimensions and placements. The actor receives only the authored architecture
as a static map, plus depth, encoders and IMU observations; loose equipment and
the target are absent from its model. The latest actor uses read-only bundles
and separate filesystem, PID and network namespaces. Active probes and a
forbidden-packet rejection test check this enforcement; sensor calibration
and general localization remain open.

Three 80.54-second runs exercise empty, preloaded-tool and isolated-actor tray
transport and return on the actual white assembly bench. The
[runtime guide and evidence](../../simulation/g1_cooling_demo/LABORATORY.md)
retain their source snapshots, recorded sensor inputs, physics trajectories,
independent replay and the failed first import attempt. Initial robot/tray
staging is explicit setup, not executed preparation. Non-convex equipment
cavities, device articulation, tool loading, locomotion, recovery and all eleven
paper branches remain unqualified. The separate clean long-horizon film is an
authored presentation and does not grant physical acceptance credit.

A separate 12-second unloaded walking trial now advances 1.957 m in the same
laboratory and transfers to stationary torque control at 6.602 s. It passes
independent replay, feet-only floor contact and stopping checks. The official
G1 29DoF velocity policy, training actuator assumptions, IMU heading correction,
rotating sole-wrench constraints and all seven development attempts are
recorded in the runtime guide. A subsequent joined attempt,
`simulation/g1_cooling_demo/runs/laboratory_mission_04`, ran walking, parking,
posture preparation and tray manipulation in one 99.162-second simulation.
Its independent evaluation **failed**: the tray returned 55.2 mm from its
source location, exceeding the 20 mm threshold, and hand/worktop contacts
were detected. Exact motor replay and payload containment passed. The run and
three earlier failed attempts remain available; this adds no qualified branch
or reliability credit. Carrying, navigation and complete campaign qualification
remain open.

## Implemented asset-phase changes

- The active constraint file and [readiness record](../../assets/cooling_lab_v1/readiness.json)
  connect 200 manual definitions, 33 interfaces and eleven branches to current
  resource requirements. Compound resources are decomposed, with unallocated
  quantities left visibly unknown. This is an author/reviewer artifact, not an
  actor instruction bundle or execution credit.
- The complete official G1/Inspire source model is now placed in the laboratory.
  The gravity-enabled floating-root MJCF retains source inertials, limits and
  wrist transforms, with 41 independent actuators and 12 mimic constraints.
  Palm collision components remove the initial zero-pose convex-hull artifact;
  finite short-run dynamics and source-frame checks are asset evidence only.
- The scene's bespoke film/emitter jigs and carriers were removed. Ordinary
  Mitutoyo 530-104, Wiha 26100 and Buerkle 4208-0022 candidates are source-linked.
  A small tray does not resolve heavy transport or delicate-film retention;
  the legacy specialized-tool requirements remain open.
- The review page displays policy, branch readiness, resource gaps, standardized
  asset views and geometric articulation. It keeps every new candidate unaccepted.
- The fabrication room now contains a selected OMAX ProtoMAX reconstruction,
  including its transparent opening lid, slat bed, stage, nozzle, hopper, cabinet,
  internal pump and ordinary laptop console. Manufacturer source discrepancies
  and inferred local dimensions remain visible. This machine is an authored
  selection, not the unidentified historical machine from the paper.
- Raw copper and track aluminum thicknesses were corrected to 0.5 and 1.5 mm
  from the task's source records. Foam and acrylic stock were added separately;
  stock plan sizes and acrylic thickness remain authored selections.
- New G1-specific bounds cover 129 restricted static poses: a 0.60 m body/hand
  radius plus 0.10 m route margin, with a 1.43 m height allowance. The source wrist transforms are retained. The 94-point station screen records
  each position-only IK result and external obstacle conflicts, including 24
  supply/service approaches. Shoulder alignment, unused-arm retraction and
  proposed-camera clearance are screened. The
  Cary mounting datum remains distinct from its authored 80 mm upper palm
  approach; finger contact and insertion remain open. Selected equipment/tools moved
  closer to bench fronts without changing source geometry dimensions.
  Two-hand coordination, loads, cameras, walking and balance remain unqualified.
- Three camera requirements remain separately inventoried. The head uses G1's
  native D435i optical frame. Two D405 units and an optional D455 bench reference
  retain pinned manufacturer mesh geometry. Official Unitree wrist STEP parts
  are now tessellated with their source roles verified against embedded CAD
  names. A finite clocking search moves the G1/FTP placement above each wrist,
  removing the observed pitch-housing conflict at sampled finger poses. Clamp
  interference is resolved with a separately labeled G1 collar derivative that
  retains the source camera arm. A 31.2 mm bore, matched bolt ears and explicit
  M3 screws, washers and nuts replace the incompatible source collar. Positive
  radial clearance, camera screw depth and discrete unfastened removal paths
  are checked; liner preload, cables and dynamic loads remain open. The
  original source mount is preserved and must still fail its regression cases.
  Station IK rejects attachment intersections with every robot link, including
  its parent wrist. No accepted installation or transit qualification follows.
- The browser renders head RGB / ideal axial depth and both candidate wrist RGB
  views from the current source kinematics. Camera frames are checked against
  MuJoCo. Cutaway, isolation and review labels cannot remove scene occluders
  from these images. Nominal catalogue FOV, uncalibrated extrinsics and opaque
  depth treatment remain explicit; no sensor noise, observation timing,
  controller process isolation or execution credit is claimed.
- Eight individually staged Omega 5TC-TT-K-36-36 probes use the catalogue's
  0.13 mm conductor diameter and nominal 1 m length. Coiled rest shape, jacket
  envelope, stripped ends and weld details are inferred. No cable mechanics,
  DAQ connection, strain-relief or temperature observation credit is claimed.

- Twenty-two additional supply/service types now have source ledgers, real
  openings and separate parts. They add a fine-wire stripping tool, ordinary
  tweezers, slotted driver, fill vessel, vented ambient RTD, eight K-connector
  pairs, thin raw films, masking stock, unmachined copper, a catalog cart and a
  separate wipes can. OMAX 317864 clamps, Knipex 78 03 125 cutters, Noga RB1000
  deburring and eight individual Pomona 5908A leads extend preparation and
  electrical stock. Local dimensions and material assumptions are explicit.
  Two angular-reflection candidates now include the Harrick HRS stage and its
  FTIR base, and the Spectra-Tech 500 rotary frame, four separate mirrors and
  the M4 sample/reference surface. The earlier extra M4 mirror plus separate
  specimen is retained as a rejected topology fixture. The former short-face
  perpendicular rotor is also retained because it misses the finite reference.
  A selected 105-degree tandem candidate uses extended M3 and reference faces,
  with two edge stops that leave the grazing-angle exit clear. It passes 594
  actual-triangle diagnostic rays across 66 angles, including all obstructions;
  optical calibration and the manufacturer's exact mechanism remain unresolved.
  Source aperture sizes/ranges are distinct from inferred dimensions. They are
  staged on the optical bench; Nicolet mounts, retention and optical alignment
  remain open. Geometry sliders inspect the selected rigid carrier; they do not
  implement robot manipulation or a calibrated optical instrument.
  The scene has 81 instances; compound requirements and full campaign quantities
  remain incomplete. Forty-nine component requirements now bind to named staged
  units, including individual sheets and eight connector pairs. Shared tools
  remain the same physical instances. Staged assets are not executed preparation
  operations.
  Clamp installation/force and wire-tool compatibility remain unresolved.
- The [unified inventory](../../assets/cooling_lab_v1/laboratory_inventory.json)
  reconciles base, installed-weather and partial-preparation views into 118
  review identities, including one site design. U30, cart, sensor leads and
  removed parts keep their identities; two temporary ties are additional stock,
  separate from the fourteen retained ties and their cutoffs. The explicit
  installation needs now include separate ordinary applicators, a 300-wipe pack
  and an inferred 3 L grease-wipe reservation. Sixteen needs retain one missing
  clean-packaging collection point; full trial/reset budgets remain open.
  Two packaging films and every reserved wipe retain identities. One separate 85 g silicone
  tube is selected for the EPDM channel, with two conflicting manufacturer
  density scenarios sharing one identity. The silicone door gasket is excluded;
  cable-jacket compatibility and application remain unqualified. These additions
  preserve every original component and deficit; they grant no initial-state
  or task credit. The same allocation page displays and filters these records.
- The [campaign allocation](../../assets/cooling_lab_v1/campaign_allocation.json)
  covers all 154 component requirements and eleven branches, with selected
  quantities for 69 components, 77 unresolved quantity/specification requirements,
  and eight non-stock output/configuration/frame/calibration requirements. All
  154 still require completion and acceptance. The
  [quantity policy](../../assets/cooling_lab_v1/component_quantity_policy.json)
  adds 32 explicit selections with remaining conditions, including shared tools,
  containers, optical subassemblies and the selected robot components. One G1
  retains distinct body/left-hand/right-hand part bindings without extra stock;
  the head frame does not supply a separately modeled D435i. Two independent
  heater candidates match the paired power requirement.
  Completed apparatus meshes and the fixed-configuration display are references,
  not prebuilt starting stock. The selected pair is reused by identity. The
  [stock cut plan](../../assets/cooling_lab_v1/stock_cutplan.json) reserves 75
  envelopes on 40 sheets/blanks, eight tube sections, four purchased profiles and six angle cuts
  using actual apparatus meshes.
  Copper, aluminum, foam, acrylic and hollow-tube stock are separately inspectable.
  The former undersized acrylic/Mylar and insufficient LDPE remain as rejected
  evidence. Selected 12 μm foil now agrees between stock and custom apparatus;
  the manufacturer's candidate is not identified as the paper's original Mylar.
  Manufacturing tools, remaining connecting hardware, optical specimen formats, services and
  reset/consumption budgets still need allocation. The [interactive review](../../viewer/lab_review_v1/allocation.html)
  exposes these limits and exact source versions; no new controller is introduced.
  In particular, the cutter's stated 0.2 mm minimum soft wire exceeds the
  finest thermocouple conductor. The meter leads have full entry-to-entry
  lengths and open shrouds, but no heater-side adaptor or electrical circuit.
  Detached G1 battery/charger candidates and an ordinary service inspection
  bench extend the scene. The 2024 manual constrains their case dimensions;
  local geometry, connector details and charger revision remain explicit gaps.
  No charging, autonomous battery replacement or complete service facility is
  qualified. The approach shares the south cross-aisle and must stay clear.
  Flat-white/black ColorMaster stock cans and a PELCO 16032 silver-paste
  candidate add three capped units at the coating bench. Package scales are
  explicit hypotheses; removable hollow caps and an open bottle mouth provide
  inspection geometry. No spraying, adhesive application or material
  compatibility is qualified. Exact paper SKU/brand, complete SDS coverage,
  ordinary dispensing tools and campaign allocation remain open.

- The selected Thorlabs L200/M central-support candidate now has a pinned
  official STEP/drawing, a reproducible local download/conversion and a
  [source-CAD inspector](../../viewer/lab_review_v1/lift.html). All 86 solids,
  actual plate bores/slots and the 16 links are retained at source scale.
  Four raw tessellation seams are corrected by 14 edge subdivisions without
  moving vertices or filling physical holes; their failed meshes are retained.
  This is a selected substitute for the unidentified paper support. The three
  reference configurations now include a nominal mounting with actual base and
  platform holes, four M3×10 underside screws/large washers and four M3×8
  ISO 10642 platform screws. Two loose jacks and 24 ordinary mounting pieces
  are initial stock; a separate 5 mm aluminum plate reserves both platforms.
  The [mounting checks](../../assets/cooling_lab_v1/apparatus_mount_checks.json)
  preserve nominal thread-envelope intersections and unresolved load, preload,
  acrylic stress, tool access and cover connections. Legacy disconnected
  probe placeholders are removed. The actual core is inspectable in the browser;
  the upper thermal/reflector group follows the corrected source height.
  The first stock placement caused shoulder/shelf overlaps. Those poses remain
  replayed failure fixtures; the three stock groups move 300 mm toward the aisle
  and are checked again with the same robot and collision screen.
  Manufacturer CAD and every composite containing it stay in ignored local cache/geometry directories;
  the repository distributes source pins, code and review evidence.

- The [frame inspector](../../viewer/lab_review_v1/frame.html) now shows the
  actual selected base, two 20-2020 nominal profiles, outboard hollow uprights,
  ordinary bridge plates, split clamps, T-nuts and reflector clamp plates.
  Rails follow the 305 mm inner span shown in SI Figure 1, with the acrylic
  below their tops. Nominal slots and central bores replace overlapping box
  geometry. Commercial identities, public dimensions and original machining
  choices are separated in the [source ledger](../../assets/cooling_lab_v1/apparatus_frame_sources.json).
  The track span is now 395 mm, with actual upper-clamp holes; its selected
  curve and the paper's conflicting reflector-height statements remain open.
  Flat underside connections and four ordinary feet keep screw heads clear
  of the support plane. The reflector uses two screw-clamped backing plates,
  with countersinks continuing through the thin disk into its upper plate.
  The [frame checks](../../assets/cooling_lab_v1/apparatus_frame_checks.json)
  inspect exported solids and use solid-intersection volume to distinguish
  coplanar contacts from intersections; FCL contact depth alone was misleading
  on coincident faces. A sharp T-nut envelope intersected the diagonal web;
  that actual failed mesh is retained. Its inferred 0.25 mm edge break needs
  manufacturer CAD/metrology confirmation before product-fit acceptance.
  Clamp deformation, thread/seat forces, preload, tolerances, adhesion,
  complete reflector travel, manufacturing-tool/reset allocation and robot assembly
  remain unqualified. This is still asset work before owner acceptance.

- [Frame starting stock](../../assets/cooling_lab_v1/frame_stock.json) now adds
  three separate scene assets with 95 units: four 340 mm purchased profile
  lengths, four uncut 250 mm upright tubes, three raw aluminum blanks and 84
  fastener/pad units. Eight inferred release liners remain with the pads.
  Actual geometry supplies low resting poses for the long screws; settling,
  pickup and retention are still unqualified. Twenty custom bridge, clamp and
  carriage outputs have reserved cut envelopes; upper carriage plates require
  facing 4 mm raw stock to 3.75 mm. Drilling, tapping, slots and workholding
  remain manufacturing requirements. A retained world-space failure mesh
  records the initial overlap with existing aluminum-tube stock; the blanks
  moved 390 mm left. Independent checks reject duplicated physical members
  and an omitted T-nut. These quantities do not include failed trials or resets
  and do not convert completed display assemblies into starting stock.

- An [isolated cover review](../../viewer/lab_review_v1/cover.html) now compares
  a membrane-supported ring hypothesis with retained legacy failures. Published
  tube/ring diameters, 16 micrometre film and 57 mm shield height are preserved;
  a 51 mm PE support, film drape and 58 micrometre adhesive are explicit choices.
  All 29 candidate solids have positive closed geometry. The 205 geometric
  checks include actual film-normal gauge, contact connectivity, solid overlap
  and section-hole checks. The browser retains 25 views. Neither membrane
  equilibrium nor adhesion is qualified. The legacy invalid coating, copper
  winding and floating shield remain available for comparison. Actual section
  faces resolve misleading open-clipping interference without altering the
  physical meshes. Three ordinary angle-stock connections now use six M3×6
  screws and three washers; a separate adhesive annulus joins the aperture.
  The selected platform grows to 180 mm square while retaining the jack bores.
  Its previous 170 mm size fails the foot-support counterexample. Nominal thread
  faceting intersections remain explicit, with no preload or physical retention
  claim. All three laboratory display configurations now use the candidate,
  with 50 μm LDPE in the fixed configuration and separate white/black coating
  appearances. Thirty-one independent stock units include raw angle, eighteen
  hardware pieces and twelve lined adhesive sheets for initial, fixed,
  restoration and aperture attachments. Actual angle-cut containment and
  film-normal gauge are checked. A retained failed world-coordinate export
  demonstrates why thin meshes need local vertices and separate translations;
  the prepared scene also checks for foil/substrate intersections. Ordinary
  tools, adhesion, physical retention, reset stock and owner acceptance remain open.

- A separate FTIR installation review now adds the 206 × 252 mm floor candidate
  and 38 ordinary mounting parts. Thermo site guide 269-158000 supplies the floor
  dimensions, focus offsets, approximately 90 mm optical height and approximately
  190 mm cover clearance; thickness, attachment pattern and adapters remain
  hypotheses. The original source instrument and bench-staged accessories are
  preserved. A rear adapter relief and relocated screw remove the sampled purge
  outlet insertion conflict, with the rejected geometry retained as a regression
  fixture. Both assemblies clear 25 nominal open-bay vertical samples, excluding
  hands, forces and balance. The Spectra-Tech candidate still exceeds nominal
  closed-cover clearance by 16 mm and blocks one driver approach. The inferred
  Harrick front-fold ray is displaced by 60 mm; shifting it into alignment
  collides with the instrument. Neither candidate is mounting-qualified, and an
  open-cover inspection does not authorize measurement with the cover open.

- Four ordinary fastening tools are now separate, allocated bench instances:
  Wiha 2 / 2.5 / 3 mm hex drivers and an 8 mm Stahlwille combination wrench.
  The existing PH00 and slotted precision drivers retain their identities but
  now use the inspected 120 mm overall / 40 mm blade catalog dimensions and
  photo-guided grip orientation. PH00 shaft diameter is corrected to 2 mm.
  The slotted tool's catalog 0.25 mm tip conflicts with the current photograph's
  0.23 mm marking; this remains explicit, with no terminal-fit claim. Socket
  checks and four new palm approaches do not establish grasping or tightening.

## Historical compatibility and remaining work

`selected_reconstruction.json` in the existing task package still selects Panda
and custom tools. It is historical evidence and must not become the humanoid
runtime input. The 20-second H2 foundation reads privileged simulator state and
does not qualify sensor-only manipulation. Preserve both records with their
original scope. New task/controller bindings require their own revision and
evidence under the recorded parallel-development authorization.

The current scene is **not ready for whole-laboratory acceptance**. Remaining
items include the hand's qualified contact/dynamic description, camera mounting, ordinary
tool solutions for film/underside handling, complete resource quantities,
qualified fabrication services and tooling, exact angular optical accessories, wiring and consumables,
full carried-load space checks, and evidence for installation/support/services.
No owner approval or scene safety qualification is inferred from green checks.

Build and verification instructions are in the
[laboratory package](../../assets/cooling_lab_v1/README.md). The later parallel
development authorization permits the contact runtime described above. Its
isolated sensor actor and stationary tray sequence have recorded execution
evidence; the complete paper task and scene acceptance remain open.

## Current embodiment resource integration

The official G1/Inspire FTP bundle is pinned in `assets/unitree_g1_inspire_v1/`:
URDF, all 93 referenced meshes, repository licenses, and versioned NVIDIA /
Unitree configuration references. The asset inspector at
`viewer/robot_resource_review_v1/index.html` shows the source geometry without
rescaling. It is a static zero-pose preview, not a standing/balance demonstration.
The new selection is bound to all 200 manual-step requirements; execution
bindings remain null. The [integration record](../../assets/unitree_g1_inspire_v1/README.md)
records completed source mapping, collision repair and bounded static checks.
The lab viewer can display each tested posture. Target-interior access,
contact qualification, revised camera installation and carried-object clearance stay
open. Do not reuse the H2 spatial certificate or mix FTP and DFQ joint names.
The owner scene gate remains open.

## 2026-10-26 one-hour development delivery

The owner explicitly authorized scene and operation development in parallel; see `assets/cooling_lab_v1/development_authorization.json`. This changes development sequencing only. Scene acceptance, qualified skill/branch counts and full-campaign requirements remain unchanged.

`simulation/g1_cooling_demo/` now provides an actual G1 29DoF / Inspire FTP floating-base contact runtime. A separate actor reads native-head depth, joint encoders and IMU data; it localizes an empty Bürkle tray, approaches with both hands, applies joint torques to grip, lifts, transfers, places and retracts. The packaged 38-second development episode, all earlier attempts, exact source snapshots, physics/sensor records, independent continuous motor replay and video are linked from `viewer/cooling_demo_v1/index.html`.

This is one empty-tray subskill on a local test workbench. It does not cover the whole paper, loaded walking, assembly, connectors, thin films, configuration switching, recovery or cleanup. The task policy uses timed stages after initial depth localization. Fixed-foot localization, idealized sensors, inferred contact parameters and a non-hardened process boundary are not qualified. **0/11 paper branches and 0 full campaigns remain qualified.** The full laboratory viewer and its initial weather-stock layout are separate review scenes; they are not yet the complete dynamic runtime world.

The initial weather-stock candidate now preserves source components and assigns the previously missing portable weather identities to ordinary bench, shelf and tray locations. Folding and support placements are reconstruction candidates, not verified manipulation or stable-load outcomes. New initial-stock and allocation checks do not grant equipment or owner acceptance.
