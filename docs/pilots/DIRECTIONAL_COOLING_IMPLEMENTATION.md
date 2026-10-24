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
Model acquisition and static inspection do not authorize new manipulation work.

## Delivery order and acceptance

1. **Assets and laboratory.** Decompose and allocate all required resources;
   reconstruct commercial equipment from inspected manufacturer sources;
   represent operational parts and access states; check complete humanoid,
   hand and carried-load geometry. Deliver a source/model comparison and a
   dimensioned interactive scene. The owner must accept this exact revision
   before new manipulation sequences are developed.
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
  radius plus 0.10 m route margin, with a 1.43 m height allowance. No guessed
  wrist adapter is used. The 47-point station screen records each position-only
  IK result and external obstacle conflicts. All 47 now have static
  position candidates with proposed-camera clearance screening after shoulder alignment and unused-arm retraction. The
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
  contact still needs verification; it remains an unaccepted candidate, visible
  on demand. Station IK also screens candidate attachment collisions with other links
  and external obstacles; a separate FCL replay checks every recorded pose.
  Parent-wrist clamp contact stays explicitly unresolved and is not installation
  or transit qualification.
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

## Historical compatibility and remaining work

`selected_reconstruction.json` in the existing task package still selects Panda
and custom tools. It is historical evidence and must not become the humanoid
runtime input. The 20-second H2 foundation reads privileged simulator state and
does not qualify sensor-only manipulation. Preserve both records with their
original scope. New task/controller bindings require their own revision and
evidence after scene acceptance.

The current scene is **not ready for whole-laboratory acceptance**. Remaining
items include the hand's qualified contact/dynamic description, camera mounting, ordinary
tool solutions for film/underside handling, complete resource quantities,
qualified fabrication services and tooling, exact angular optical accessories, wiring and consumables,
full carried-load space checks, and evidence for installation/support/services.
No owner approval or scene safety qualification is inferred from green checks.

Build and verification instructions are in the
[laboratory package](../../assets/cooling_lab_v1/README.md). Runtime observation
isolation, controllers and new manipulation sequences are intentionally deferred
under the owner's asset-first order; static policy tests are not runtime isolation.

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
