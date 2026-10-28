# Passive FTIR device development

The complete laboratory contact plant can now import the Nicolet 6700 with a
passive cover hinge, a nested sliding door and four spring-return keys. It keeps
the instrument's existing position and scale. The robot controller does not
receive device joint states, and the device has no actuator. This is a device
development dependency, **not a completed humanoid manipulation branch**.

Build and run the checks from the repository root, using the simulation Python
environment and the pinned `requirements.txt`:

```sh
OPENBLAS_NUM_THREADS=1 MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=1 \
python simulation/g1_cooling_demo/run_ftir_device.py \
  --out simulation/g1_cooling_demo/runs/ftir_device_new
OPENBLAS_NUM_THREADS=1 \
python simulation/g1_cooling_demo/verify_ftir_trace.py \
  simulation/g1_cooling_demo/runs/ftir_device_new
OPENBLAS_NUM_THREADS=1 \
python simulation/g1_cooling_demo/check_device_sensor_boundary.py \
  simulation/g1_cooling_demo/runs/ftir_device_new
```

Use an empty output directory. Building regenerates the content-addressed
`lab_cache/` meshes required by the XML files; the cache is not source geometry.
The instrument variant can be regenerated with
`python assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/build.py`.
The existing conceptual movie continues to use its pinned parent geometry.

## Evidence and failures

- `runs/ftir_device_01`: rejected. The single convex hull of the right housing
  overlaps all four keys by about 8.71 mm. The instrument compiles, but is not
  a usable contact model.
- `runs/ftir_device_02`: rejected. Conforming cells remove that false key
  obstruction. The source slider grip still hits the lid over the last 18 mm
  of its declared travel; the four keys overrun their soft limits to 0.581 mm.
- [Run 03 device checks](runs/ftir_device_03/device_verification.json): all 410
  cover, sliding-door and key configurations clear unintended penetration at
  the declared 2 micrometre numerical tolerance. Four separate diagnostic
  contact presses reach 0.3175 mm and return to within 0.0179 mm of rest.
  A spherical diagnostic probe pushes the actual handle to 54.85 degrees;
  the cover remains at 52.98 degrees after withdrawal. These are separate
  component diagnostics, not a continuous robot procedure.
- [Independent cover replay](runs/ftir_device_03/cover_motor_replay.json): all
  7,200 states reproduce exactly from the recorded probe motor inputs. No
  external body/joint forces are applied, and no unintended device penetration
  exceeds the declared tolerance. The largest intended probe/handle penetration
  is 0.0534 mm; key/probe penetration is 0.0252 mm.
- [Encoder boundary check](runs/ftir_device_03/encoder_boundary_check.json): the
  full plant has six extra device joints, while robot sensor packets retain
  the same 53 encoder joints as the source robot model. Moving all six device
  joints and changing their velocities leaves that encoder packet unchanged.
  This check does not
  replace the separate process-isolation audit.

Source snapshots, failed reports, compiled models and recorded traces remain
in their run directories. The nominal device diagnostic uses a 0.5 ms step;
the complete robot runtime normally uses 2 ms. Timestep sensitivity and physical
parameter uncertainty remain unqualified. TetGen/Qhull emits a precision warning
for a narrow source-derived convex cell; the retained sweep/replay checks cover
the selected cases, not arbitrary contact conditioning.

## Geometry and mechanical assumptions

The operating covers and keys retain the source reconstruction. The passive
variant changes only `sample_bay_lid` to give the sliding grip its inferred
rear relief; all 192 other part meshes/transforms match its parent. The new
slot is a reconstruction inference, not a manufacturer-supplied feature.

MuJoCo uses convex mesh contact geometry. A single convex hull fills the
Nicolet's key wells and hinge recesses. `convex_cells.py` uses conforming
tetrahedralization and volume-preserving adjacent-cell merging for five
critical source parts. It repairs collinear export T junctions by splitting
edges at existing vertices, without filling missing apertures or moving a
vertex. Other fixed parts retain the earlier convex obstacles; connectors
and unused internal details remain unqualified.

Masses, densities, friction, damping, spring rates and joint stops are explicitly
inferred in `ftir_device.json`. The model is not calibrated manufacturer
mechanics. The body/hand motion, perception of the device, grasp of its handle,
accessory installation, sample/tool dynamics and the full procedure remain to
implement and validate. The bounded G1 button attempt below does not change
this status. Qualified paper branches and
campaigns remain **zero**.

## G1 observation and key contact

`run_ftir_press.py` starts the floating G1 at an authored stationary posture
in the existing laboratory. Native head RGB and depth locate the four blue
instrument controls using their object-relative layout. The isolated actor
receives the 53 robot encoder joints, IMU and images. Its model contains the
robot and architecture, without instrument bodies, device joints or reference
trajectories. It derives a right-index approach from the observed BACKGROUND
surface, applies robot motor torques, holds briefly and returns its hand.
This is one mechanical key press, not an acquisition or experimental branch.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=1 \
python simulation/g1_cooling_demo/run_ftir_press.py \
  --out simulation/g1_cooling_demo/runs/ftir_press_new --timestep .002
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_ftir_press.py \
  simulation/g1_cooling_demo/runs/ftir_press_new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_isolation.py \
  simulation/g1_cooling_demo/runs/ftir_press_new
```

- Press 01 fails before reaching: the original left prepared hand intersects
  the hip. Press 02 clears that setup but reaches a shoulder-roll IK limit.
- Press 03 reaches and depresses the key, then fails to withdraw because its
  free-space wrist-orientation condition remains active during contact.
- Press 04 completes press and return, but its independent review rejects
  false palm/thumb collisions and excessively compliant floor contact.
- [Press 05](runs/ftir_press_05/physical_press_review.json) completes 27.622 s
  and replays all 13,812 recorded states exactly. The intended index pad
  depresses BACKGROUND to 0.3214 mm, sustains the pressed/contact condition for
  1.14 s, then releases to 0.0178 mm. Other keys stay untouched. No external
  body/joint forces or device actuators are used. Only the soles/floor and
  intended pad/key contact occur. Maximum numerical penetration is 0.2434 mm
  at a sole and 0.0972 mm at the key, within the declared finite tolerances.
  Source motor and joint bounds, support and numerical checks pass.
- [Press 05 isolation](runs/ftir_press_05/isolation_verification.json) accepts
  a valid recorded RGB-D packet and rejects the same packet with an extra
  synthetic object-pose field. Filesystem, process and network denial probes
  pass, and the exact actor code and model inputs are pinned.
- [Press 06](runs/ftir_press_06/physical_press_review.json) reruns the same
  setup with a 1 ms step and the same camera/control rates. All 27,641 states
  replay exactly and the same independent contact/isolation checks pass.
  Peak key travel is 0.3138 mm, compared with 0.3214 mm at 2 ms; release returns
  to 0.0178 mm in both runs. This is a two-step-size development comparison,
  not a perturbation or repeatability campaign. The combined metrics are in
  `ftir_press_development_review.json`.

The clean [27.625-second press video](runs/ftir_press_05/press.mp4) renders the
recorded plant states without interpolating physics. Its 663 frames map back
to retained trace indices in `press_video.json`. It has no text overlays and
is linked separately from the nine-minute authored workflow on the player.
To export a checked new run, use `render_ftir_press.py RUN_DIRECTORY` with the
same EGL environment variables as above.

The thumb-2 refinement is an approximate source-derived contact representation,
not a visual change or a globally qualified hand model. Sole/floor pairs use an
inferred 4 ms contact time constant and 0.99 impedance; these are numerical
development parameters, not measured floor or shoe properties. Camera optics,
ideal images and fixed-foot state estimation remain uncalibrated. Acquisition
configuration, walking to the instrument, accessory installation, sample and
reference exchange, robust recovery and repeatability are still outside this
single-attempt result. The clean nine-minute cross-station video remains the
separate authored workflow demonstration.

Technical references: [MuJoCo collision computation](https://mujoco.readthedocs.io/en/latest/computation/)
and [MeshPy/TetGen interface](https://documen.tician.de/meshpy/tri-tet.html).
MeshPy's wrapper is MIT-licensed; its bundled TetGen has separate
[licensing terms](https://documen.tician.de/meshpy/faq.html). This repository
uses the installed offline mesher and does not vendor its implementation.

## Sensor-based cover grasp development

`run_ftir_cover.py` starts another isolated actor in the complete laboratory.
It observes the native RGB-D key row, fits the handle cylinder in the depth
image, and uses object-relative hinge dimensions to construct an opening arc.
The grasp prior contains no instrument world placement or plant trajectory.
The complete approach, opening arc and withdrawal receive robot-only IK
preflight. The prepared standing posture is setup, not walking credit.

Seven native scalar touch sensors cover the source right index and thumb pad
meshes. Their bounds derive from those meshes with a 0.1 mm margin. Readings
contain neither contacted-object identities nor device joint state; self
contact can also load them. This is an inferred force abstraction, not a
calibrated reproduction of the manufacturer's tactile arrays. The controller
must establish both pad loads before lifting and releases/withdraws when
contact is lost. Independent review checks the actual handle contacts and
passive cover angle after execution; controller state alone is not success.

The source-pad grasp search in `fit_ftir_cover_pad_grasp.py` requires two
opposing distal tactile pads and whole-hand source-mesh clearance. Its first
16 candidates were invalid: the search had omitted the thumb-1 joint limit
and selected 1.20 rad against the source upper bound of 1.1641 rad. The plant
therefore could not reproduce the planned hand shape. Runs 04–07 preserve
that failure; their opening motion does not qualify the grip. The corrected
search checks nominal and closed configurations, including mimic joints,
and the actor now rejects an out-of-range prior before commanding motors.
The independent verifier also checks commanded grasp limits separately from
the measured joint trajectory.

`refine_ftir_cover_grasp.py` keeps a source-relative palm rotation while
refitting the fingers and palm translation inside those source limits. Its
exact triangle-mesh acceptance checks are separate from the optimization's
surface-point approximation. Whole-body reach and physical execution are
still required after these local geometric searches. Refinement 04 finds
18 local candidates that pass the observed arm-path preflight; candidate 0
is used by runs 08–09. The preceding 12-candidate bounded search failed the
full path screens, and its rejected approach/stance variants are retained.

Retained attempts:

| Run | Observed outcome |
| --- | --- |
| `ftir_cover_01` | Camera view loses enough key-row depth points after settling; no approach. |
| `ftir_cover_02` | Reaches the approach, but the extended thumb hits the case during alignment. |
| `ftir_cover_03` | Simultaneous approach/curl and depth handle fitting reach the grip pose, but the old whole-finger grasp does not load both tactile pads. Recovery completes. |
| `ftir_cover_04` | The new pad-specific grasp establishes two contacts and physically lifts the cover 2.84 degrees, then loses the thumb pad during lift. Recovery completes; the cover closes. |
| `ftir_cover_05` | Bounded tactile load adaptation reaches about 5 N per digit, but continued timed closure and wrist deflection lose the grip before lifting. Recovery completes. |
| `ftir_cover_06` | Sensor-terminated closure and wrist load compensation lift to 28.60 degrees. Pad contact is lost; whole-body support review fails and recovery reaches an arm limit. |
| `ftir_cover_07` | Putting the wrist reaction into the full floating-base balance QP restores the support check and lifts to 37.50 degrees, then loses contact. The hand releases and withdraws, but final arm return fails. The independent prior-limit check also rejects the old grasp. |
| `ftir_cover_08` | The refined grasp passes the source prior/joint-limit checks and lifts to 22.43 degrees. Finger self contacts and loss of pad/handle contact remain; withdrawal reaches an arm limit. This run also fails opening acceptance. |
| `ftir_cover_09` | A smooth 15-degree rolling allowance keeps the nominal hand clear of the cover through the planned arc, but the physical grasp still slips. The lid reaches 22.99 degrees; withdrawal again reaches an arm limit. Support, source limits, isolation and exact replay pass; grasp retention, opening and release fail. |
| `ftir_cover_10` | A grasp centered further inside the source pads reaches about 4.5 N on each digit, but loses contact before the confirmation interval completes. Maximum cover opening is 0.72 degrees; recovery stops at an arm limit. Source limits, support, isolation and exact replay pass. |
| `ftir_cover_11` | With source-derived distal contact cells and lower controller grip targets, the hand establishes grip and lifts to 14.01 degrees, then slips. Recovery stops at an arm limit. Source limits, support, isolation, release and exact motor replay pass; grasp retention, opening and unintended-contact checks fail. |
| `ftir_cover_12` | Encoder-based pad-center compensation and the compact predictor still lose the grasp at 13.96 degrees. Recovery reaches the same arm limit. All 13,266 states replay exactly; source limits, support, release and isolation pass. Opening, retained opposition and unintended-contact checks fail. |
| `ftir_cover_13` | The 3 N preload loses grip before lifting; maximum opening is 0.79 degrees. Staged recovery finishes and the robot settles for five seconds. All 19,126 states replay exactly; source limits, support, release and isolation pass. Opening, retained opposition and unintended-contact checks fail. |

All thirteen reviewed attempts retain source snapshots, isolated input bundles, lossless
sensor records, every physics-step state and motor command, and independent
replay reports. Exact motor replay and the isolation checks pass, while the
opening checks fail. In run 04 the idle left arm clears the bench, but early
sole penetration still exceeds the declared 1 mm tolerance. A smooth initial
COM transfer in run 05 reduces peak sole penetration from 3.856 mm to
0.575 mm, within the same declared tolerance. Runs 02/03 also
include bench contacts. The source-mesh diagnostic for run 03 identifies a
false convex-hull self contact between index-2 and thumb-4; it does not justify
discarding real finger/case contacts.

Run 09 moves the handle center around the observed hinge while commanding
wrist rotation `angle - delta * tanh(angle / delta)`, with `delta = 15 degrees`.
This permits some rolling of the cylindrical handle without using an
attachment. Holding wrist orientation completely fixed instead intersects
the cover front lip from 24.5 degrees. The limited-roll path passes 121
source-mesh states and observed robot-only IK, but this nominal-posture
screen does not include force-dependent finger motion. Its physical failure
is retained. The earlier `ftir_rolling_grasp_01` clearance calculation mixed
raw interface coordinates with a normalized GLB and is rejected;
`ftir_rolling_grasp_02` and `03` apply the asset normalization consistently.
No change to the object-relative hinge/handle prior was needed.

Exact triangle checks in `analysis/ftir_cover_source_contact_02` find real
finger/pad self intersections during run 09 at 18.25–19.0 seconds. Later,
the source index-2/thumb-4 meshes have 0.39–0.84 mm clearance while their
compiled convex hulls still report contact. Both grasp placement/control
and the contact representation need correction; removing false hull
contacts alone cannot be counted as a successful grasp.

`refine_ftir_pad_centers.py` adds an exposed-face margin to the source-relative
grasp search. The previous index contact was only about 0.11 mm from the pad
edge. Search 06 finds 24 local candidates with at least 0.5 mm projected margin;
candidate 0 is used by attempts 10/11. The nearby authored stance
`--initial-xy 5.95 -5.32` passes arm-path preflight where the old stance fails.
This 3 cm setup adjustment is not executed walking. Search 05 and the later
large-pad search 08 have zero accepted candidates; their collision failures
remain recorded. Search 07 corrects small-triangle proximity evaluation by
performing distance queries in millimetres and converting the results back to
metres. The earlier exact FCL distance checks are separate from that numerical
issue. All these searches remain development geometry screens.

The optional `collision_refinements/distal_v1` package replaces two filled
distal-finger hulls with 20,613 source-derived convex cells. The manufacturer
exterior meshes contain intersections that prevent direct tetrahedralization.
The builder fills a demonstrably sealed thumb cavity for collision and applies
1 micrometre index exterior simplification before conforming decomposition.
Source visuals, body inertias, joint bounds and collision filters remain
unchanged. Compiled checks in `analysis/ftir_distal_contact_04` remove selected
false contacts from runs 03/09 and retain their real intersections. The package
does not make run 11 a successful grasp. See its manifest for source hashes,
sampled surface error, sealed-void separation and serialization checks.

Run 11's offline `analysis/ftir_cover_drift_11` examines the saved geometry.
Between 14.5 and 19 seconds, the mean of the two selected source pad centers
moves about 2.46 mm along one wrist-frame axis as the fingers flex. That is
larger than the nominal pad-edge margins. These centers are not pressure
centroids, and the observation alone does not establish the cause of slipping.
It motivates checking finger-dependent grasp centering before another attempt;
recorded instrument states are not controller inputs.

After run 11, the runner keeps the high-resolution contacts in the physical
plant but uses the compact source robot in the actor's kinematic/dynamic
predictor with its unused contact solver disabled. Ten retained sensor-state
comparisons in `analysis/ftir_predictor_contact_01` produce identical estimated
state, mass/bias/passive terms, IK and balance torques, including a wrist load.
That sampled regression takes 0.89 s with the old predictor and 0.044 s with the
compact predictor; it is not a full-run speed benchmark or execution check.
Run 11 itself used the earlier full-resolution predictor. Run 12 exercises the
compact predictor in a full failed attempt, with exact motor replay and
isolation checks. Its failure does not establish a successful grasp.

Run 12 adds encoder-based centering from the selected source pad points. It
latches their wrist-frame midpoint when lifting begins and applies a filtered
wrist correction, bounded to 4 mm and 6 mm/s in the wrist frame. It uses no
instrument state or object-specific contact labels. The grip still slips;
several millimetres of loaded wrist tracking error remain. The source face
points are planning landmarks, not measured tactile pressure centroids.

Run 13 executes a further development variant. A 3 N inferred tangential
opening-effort prior ramps in a separate preload phase; lift requires settled
wrist tracking and both pad loads. The 3 N value is an uncalibrated control
prior, not a manufacturer specification or a live device measurement. The
plant still receives only bounded robot motor torques. It loses grip during
preload, then completes its recovery control sequence and five-second settling
period at 38.25 s. Independent motor replay is exact, and isolation, source
limits, final withdrawal and support pass. Cover opening, retained opposition
and unintended-contact checks fail; this provides no qualification credit.
The cover closes after release, with transient cover/support penetration up to
about 11 micrometres versus the unchanged 2 micrometre device threshold.
The full contact report also retains non-pad thumb/handle contacts. Recovery
control completion does not establish collision-qualified recovery.

The revised retreat first opens the fingers by a small bounded amount while
moving 2 cm away, then retreats another 2 cm. Clear/return waypoints use source
arm joint configurations under the current body estimate. The thumb abducts
before the remaining fingers fold. `analysis/ftir_recovery_path_01`–`04` retain
the rejected alternatives: full finger opening hits the cover lip, an 8 cm
retreat intersects the torso, and simultaneous refolding intersects index and
thumb shells. The final static screen has no excess contact in 558 full-body
states across a 0–16 degree cover-angle sweep at one retained sensor posture.
This is a bounded static screen, not physical recovery qualification.

Runtime profiling in `analysis/ftir_runtime_profile_01` finds approximately
38 ms per unloaded full-plant step, dominated by narrow-phase collision work.
The timings are under concurrent development load. The experimental contained
cell-growth search in `analysis/ftir_distal_contact_06` preserves original-cell
coverage and accepts expansions only inside the source exterior, but its
bounded partial candidates still have more cells than the active package.
They are not adopted. The official pinned G1/Dex3 source comparison in
`analysis/g1_dex3_comparison_01` is also a candidate inspection only; the
selected robot, laboratory and delivered movie are unchanged. Its unloaded
source-model timing excludes the laboratory and is not an end-to-end speed
comparison or evidence of a successful grasp.

The subsequent Dex3 source search intersects the official URDF and MJCF joint
limits, including the differing thumb-1 upper limits. Projected source surfaces
propose grips; exact triangle distances reject bar intersections. Search 02
finds 298 local bar candidates. The whole-instrument roll screen retains 301
placements across 136 distinct hand configurations, but all eight whole-robot
reach/path screens fail. Nearby stance, left-hand folding, alternative arm
seeds and cylinder rolling allowances remain explicit hypotheses, without
walking or execution credit. No Dex3 physics attempt or hardware selection
change has been made.

The fixed-wrist preview in grasp search 02 changes MuJoCo parent filtering,
so its native self-contact rows must not be interpreted as floating-robot
contacts. The instrument screen uses the original floating model instead.
Raw palm/thumb-proximal visual overlap remains recorded near the joint
assembly. Reach screen 03 onward checks native mesh-hull collisions against
original triangles; selected wrist reports are false positives, while real
shoulder/torso intersections and joint limits still reject the paths. A static
triangle check does not repair a runtime hull or establish physical safety.
The later `g1_dex3_comparison_01/reach_frame_correction.json` records a
1.25 mm source-frame offset in those eight rejected hinge-path screens.
The corrected builder transfers the pivot relative to the observed handle;
adoption would require rerunning the paths. Their zero-angle bar/instrument
screens do not use this pivot. The rejected paths are not an infeasibility proof.

Manufacturer-source reinspection in `analysis/nicolet_cover_affordance_01`
identifies a more fundamental unresolved premise. The current 8 mm cylindrical
front bar and its 76 mm span are inferred, not manufacturer CAD or measured
dimensions. The inspected brochure shows the sliding-window grip, and the
guide distinguishes that window from the hinged cover. These sources do not
establish the modeled separate front bar; they also do not prove its absence
on every hardware revision. Further development must resolve the gripping
interface and installed IntegratIR access route before treating this bar-grasp
family as a faithful commercial-device task. The generic transmission example
uses the sliding door, but that does not establish this accessory's access
clearance. Existing assets, movies and failed run snapshots remain evidence;
none gains qualification from the new searches.

`analysis/nicolet_slider_access_01` tests a source-supported alternative access
direction without changing the equipment geometry: the existing sliding door
opens fully while the hinged cover stays closed. A gold-reference-only route
with a 35 mm front offset before descending and translating under the cover
has zero collisions in 183 sampled states; straight descent fails 15 states.
Adding the currently authored Inspire reference grip and terminal wrist in
`nicolet_slider_access_02` fails 141 states on either route. The carried object
fitting through the aperture therefore does not establish robot access. A new
grasp/tool strategy or a source-supported cover-opening strategy is still
required, together with full-arm, dynamic and installation checks.

The official Inspire tactile-hand manual is linked with a content hash in
`analysis/inspire_tactile_definition_01/source.json`. Its tactile arrays report
16-bit raw samples (0–4096), while force-control registers are a separate
interface. The seven scalar Newton channels above remain an inferred simulator
abstraction. Source mesh sizes suggest distinguishing small terminal pads from
larger fingertip pads, but that mapping is not a calibrated register-to-mesh
binding; the rejected large-pad search does not authorize a collision exemption.

Sliding-window development in `analysis/nicolet_slider_push_01` and `02`
keeps the equipment geometry unchanged. A top/front-top index-pad push is an
inferred manipulation strategy for opening a 70 mm access gap before trying
the cover edge. It is not full slider travel, reference exchange or a vendor
procedure. The separate two-pad cover-edge search in
`analysis/nicolet_window_edge_01` rejects all 9,720 placements.

The push search finds locally clear hand paths, but whole-arm entry requires
obstacle avoidance. The first RRT path passes instrument-only checks and then
fails the independent full-room review in 50 entry/return states against the
bench. Adding the existing public architectural map to planning yields a new
path with no additional room intersections in 1,867 sampled states across
6,538 room meshes. The separate 821-state return review retains 2 mm free-space
clearance. Original source foot/shank and foot/floor overlaps remain recorded;
these results do not certify whole-body source clearance or physical motion.
See `nicolet_slider_push_02/geometry_summary.json` for the bound reports.

`robot_source_meshes.py` extracts original visual triangles from the actor's
public robot model, without scene object poses or simulator contacts. Its
geometry agrees with the independently exported source GLB to 65 nanometres,
with identical triangle counts and source adjacency. Planning must still run
from the actor's current sensor estimate and observed device registration.
The retained offline RRT waypoints are diagnostic evidence, not actor inputs.

`run_ftir_slider_scan.py` separately exercises observation and torso preparation
using native RGB/depth, encoders and IMU in the isolated actor. It starts from
an authored stationary pose and does not push the window. Attempt 01 identifies
the key row and turns successfully, but independent replay rejects left-hand
and wrist contact with the bench. The revised preparation places the unused
left shoulder at 0.5 rad after a retained-state clearance screen. Every attempt
keeps its own source snapshot; `physical_scan_review.json` and
`isolation_verification.json` determine its outcome. Neither preparation nor
the geometric arm search qualifies walking, window manipulation or a branch.
Attempt 02 completes 11.15 simulated seconds and passes every-state motor
replay, unchanged contact/support thresholds, motor/joint limits and active
isolation checks. Its actor accepts 39 key-row observations. This is one
preparation pass after one rejected attempt; neither scan pushes the slider.
The observed posture differs from the earlier hypothetical path setup, so the
next actor must recompute its approach from the actual preparation sensors.
The retained two-attempt comparison is
`analysis/nicolet_slider_push_02/preparation_comparison.json`.

## Runtime sliding-window approach

`run_ftir_slider.py` extends the passing observation/torso preparation with
native depth observation of the closed window grip, online arm planning and a
tactile push. It runs in the original complete laboratory. The isolated actor
registers public, unposed device CAD from the observed key row, plans against
that geometry and its public architectural map, and receives seven scalar
touch readings alongside RGB-D, encoders and IMU. No retained RRT trajectory,
device joint state, plant contact list or evaluator output enters the actor.
The architecture includes the bench that rejected the earlier instrument-only
path. The planner keeps the 2 mm free-space clearance margin.

The new `slider_push_prior.json` consistently uses the raw GLB frame for both
key centers and local hand affordances. Its key/grip coordinates differ by
1.25 mm in local Y from the older prepared-mesh prior; mixing those frames
would misregister the contact target. This export changes neither the device
geometry nor its dimensions. The 70 mm push and local hand fits are inferred
strategies, not manufacturer-measured grasp procedures.

`analysis/nicolet_slider_push_03/sensor_plan.json` exercises the same planner
on retained scan-02 sensors. It generates a fresh seven-vertex entry route.
Independent full-room review finds no new intersections in 2,276 sampled
states, while explicitly retaining initial source foot/floor overlaps. This
is geometric planning evidence, not physical execution or whole-body clearance.
The runtime actor separately generates its own plan after observing the device.

The grip gate accepts eight retained closed-window depth frames. Controlled
renders at 4, 10, 30, 70 and 104 mm opening are rejected. The first control test
also incorrectly rejected the closed baseline because it mixed sensor and
integrated-state times; that failed report is preserved. The corrected test
reconstructs the recorded closed RGB and depth arrays exactly before changing
only the window for its labeled counterfactual renders. After `mj_step`, the
sensor/camera fields correspond to the pre-integration pose, while `qpos` and
delivery `time_s` have advanced by the 2 ms step. These are development controls
at one posture, not broad sensor calibration or millimetre accuracy guarantees.

The initial physical push reaches 16.58 mm before losing distal-pad contact
and executing its return sequence. Retained-state diagnosis shows contact
shifting from the intended tactile pad to the index link near 48 seconds.
Its failure is retained in `runs/ftir_slider_01`; return completion does not
qualify the push or its contacts. A subsequent controller correction places
the desired modeled load at the encoder-predicted fingertip point instead of
the wrist. This includes the finger generalized forces and wrist moment; the
plant still receives only source-bounded robot motor torques. The virtual-work
regression passes, and default calls without surface loads produce identical
torques to the retained controller. Physical efficacy requires a new attempt
and independent replay; the algebraic regression does not establish it.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=1 \
python simulation/g1_cooling_demo/run_ftir_slider.py \
  --out simulation/g1_cooling_demo/runs/ftir_slider_new --duration 140
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_ftir_slider.py \
  simulation/g1_cooling_demo/runs/ftir_slider_new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_isolation.py \
  simulation/g1_cooling_demo/runs/ftir_slider_new
```

The independent verifier requires 65–75 mm final travel, at least 50 mm driven
by the intended distal pad, exact motor replay, unchanged contact tolerances,
source motor/joint limits and supported balance. It preserves failed outcomes.
Run 01 replays all 49,197 states with zero position/velocity error and passes
isolation, support and source-limit checks. It fails travel, intended-pad
displacement and unintended-contact requirements: the index link contacts the
window, reaching 0.0332 mm penetration against the unchanged 0.020 mm bound.
The initial report export failed on a NumPy boolean; the retained export log
and source snapshot accompany the corrected verifier and repeated full replay.
Run 02 includes the fingertip load correction and reaches only 8.51 mm before
contact loss. Its 48,627 states replay exactly and isolation/support/source
limits pass, but travel and unintended contact still fail; index/window
penetration reaches 0.1595 mm. The completed two-attempt comparison is
`analysis/nicolet_slider_push_03/push_attempts_01_02.json`.

The controller in attempt 03 projects preload perpendicular to the free slider
axis. The earlier tilted surface normal imposed 0.518 N along that axis, while
contact-interval replays show approximately 0.2–0.26 N axial object reaction;
the window advances beyond the commanded stroke before pad contact is lost.
The projection separates preload from commanded advancement without changing
the geometry, 2 N magnitude or acceptance limits. Attempt 03 still fails after
6.08 mm of window travel. All 48,797 states replay exactly, and isolation,
support and source limits pass. Contact migrates to the index link, lid and
window; those contacts and the short travel fail the unchanged acceptance
checks. At 47 s the slider is only 0.134 mm ahead of the commanded wrist
advance, but finger flexion shifts the pad by about 2.50 mm along the contact
normal while the wrist error is 0.58 mm. Wrist tracking alone therefore does
not establish fingertip tracking.

The current controller adds a Cartesian task at the encoder-predicted pad
point during contact search and pushing. It compensates the measured scalar
tactile load along the estimated public-CAD surface normal; bounded position
admittance pursues the 2 N pressure target. It no longer assumes that a desired
2 N contact load is already present. The force direction remains an inference,
not a measured three-axis wrench. The regression in
`analysis/nicolet_slider_push_04/point_task_regression.json` verifies unchanged
default controller calls, the contact-point Jacobian and the new task response
within source motor bounds. Attempt 04 passes the unchanged independent
physical requirements and process-isolation review. Its 54,052 retained
states replay with zero position and velocity error. Final slider travel is
72.752 mm; the intended distal pad drives 72.587 mm during 11.210 s of
contact. No unintended contact exceeds the existing bounds, and source
joint/motor limits and supported balance pass. This is one development
success from an authored standing pose, not skill reliability qualification.
The observed scalar pressure varies during the stroke; the controller does
not establish constant 2 N pressure.

`runs/ftir_slider_04/slider.mp4` is a clean 1 min 48 s rendering of the
reviewed trace in the original laboratory. The rendering receipt maps all
2,595 frames to retained physical states; it contains no interpolated robot
or object motion. It is a single operation, separate from the authored
5 min 33 s cross-workstation FTIR demonstration.

Original source-triangle checks at 71 retained poses per failed run identify
13 and 10 index-link/window intersections in attempts 01 and 02. These are not
merely native convex-hull false contacts. A separate comparison of 71 existing
object-local hand candidates finds 3.35 mm nominal index-link/window clearance
for the selected pose. Other candidates need fresh current-state arm planning
and physical validation; bending the finger alone does not certify clearance.
These attempts start from authored standing setup. Walking between stations,
full hinged-cover opening, reference/sample exchange and branch repeatability
remain separate requirements; qualified paper branches are still zero.

The optional `run_ftir_slider.py --prior PATH` pins another public object-local
affordance set in the isolated bundle. Attempt 05 uses the clearance-ranked
prior in `analysis/nicolet_slider_push_04/clearance_ranked_prior.json`; the
runtime planner selects candidate 19 and executes its entry in 17.32 s,
compared with 31.50 s for attempt 04. It subsequently loses contact and
executes the abort return, so it is a failed attempt despite its final slider
position falling inside the requested range. Inspection also identifies a
phase-entry bug: converged wrist pose and elapsed seek time could bypass
tactile acquisition. All 39,652 states replay exactly and isolation passes;
the final 70.042 mm travel, 62.385 mm intended-pad-driven displacement,
contact limits and supported balance pass, but the controller abort makes
the attempt fail overall. The five-trial comparison, including every failed
check, is `analysis/nicolet_slider_push_04/push_attempts_01_05.json`.

The current actor fixes the
phase-entry bug by requiring confirmed touch for this
transition and clears confirmation when the load drops below the acquisition
threshold. The retained-case regression passes; attempt 06 tests that guard
with the canonical prior used in the successful attempt 04. Attempt 06 passes
independent physics and isolation checks. Its world and complete trajectory
are byte-identical to attempt 04: the guard preserves the already-correct
nominal sequence. This is not an independent perturbed reliability trial.

The separate `ftir_slider_outcome.py` prototype recenters the same depth fit
at a commanded position without reading the plant slider joint. Its initial
standalone study was not part of the runtime actor. The first labeled seven-position control rejects the true
70 mm state because the fitted height residual is 0.823 mm, outside the
unchanged 0.8 mm gate. Across eight retained observation poses, the unchanged
gate accepts six true-target frames and rejects all 32 non-target controls.
These development measurements retain both false rejections. They do not
establish post-push visibility, online completion detection or calibration.

The labeled static endpoint fixtures in
`analysis/nicolet_slider_push_04/endpoint_views.json` test three possible
post-push torso viewing angles. A proposed baseline-corrected 66–74 mm
sensor guard accepts all six valid fixtures but also one of 18 invalid
fixtures: a true 80 mm opening is estimated at 73.625 mm when only a narrow
part of the grip is in the depth crop. That candidate guard is rejected for
runtime use. The original target observer and physical 65–75 mm acceptance
requirement are unchanged. These fixtures change evaluator-side geometry
for sensor diagnostics; they are not executed posture transitions.

The separate `SliderRangeObservation` prototype additionally requires
observed axial grip extent of at least half its public CAD width, rejecting
a cropped edge that cannot establish slider position. A subsequent labeled
study on run 05 endpoint geometry and four different viewing angles is saved
in `analysis/nicolet_slider_push_04/endpoint_views_02.json`. It accepts 20 of
32 physically in-range fixtures and none of 24 out-of-range fixtures. All
four 70 mm target fixtures pass; the conservative guard also rejects valid
states near the physical range boundaries. Those false rejections remain in
the report.

Attempt 07 integrates that range observer in `ftir_slider_observed_actor.py`.
After pushing and withdrawing, the floating robot turns its torso under motor
control, waits for eight consecutive accepted RGB-D observations, and returns
to its resting orientation. The 117.142-second execution passes physical and
isolation reviews. An independent replay reconstructs the closed baseline and
all eight outcome fits from retained raw camera/encoder/IMU packets; predictions
match exactly and the largest slider-position error is 0.336 mm. The clean
117.167-second recording is `runs/ftir_slider_07/slider.mp4`. This is one
station operation, without calibration, carrying or paper-branch credit.

`run_ftir_approach.py` is the continuous walking-to-station integration entry
point. Its first trial walked from the aisle but failed the posture handoff;
the failed trajectory and all review failures are retained in
`runs/ftir_approach_01`. The current controller initializes and holds the
folded hand posture, preserves the actual parked leg posture, and prepares
only the upper body before native depth registration to the room architecture.
Handoff passes the sensor-derived robot state and the current simulation time
to the station actor. It does not reset the physical robot or device. The
official walking policy's 0.01 kg m² body-joint rotor inertia is an explicit
training-model adaptation, not measured hardware identification. Full
continuous execution and independent review are still required; existing
contact, support and joint-limit criteria remain unchanged.

The retained approach trials 02, 03, 05 and 06 all fail overall. Their
independent process-isolation checks and complete frozen sensor-actor replays
pass integrity checks, with zero motor, response and event differences.
Attempt 02 executes the walking handoff but loses window contact. Attempt 05
has hand self-contact during walking and then hits the instrument/worktop and
catches a drawer handle; it never completes posture preparation. Attempts 03
and 06 lose balance with the fixed arm hold. Attempt 04 was stopped during
bootstrap before physics. See `analysis/nicolet_slider_push_06/approach_status.json`.
The added official `action_manager.h` confirms that upstream action history is
the raw network output, before target processing. Correcting that history does
not make the fixed-arm adaptation pass.

`quasistatic_walking.py` is a separate development controller for short steps
with an authored arm hold. It estimates
support from encoders, IMU and a level-floor assumption, assigns zero model
wrench to the swing foot, and sends only bounded motor torques to the full lab
plant. These in-process probes do not claim process isolation. The stationary
Balance default produces exactly the same torques at nine retained window-task
states after adding the optional support-foot interface.

All short probes are retained under `analysis/quasistatic_walk_*`. Probes
01–03 stop during the first COM transfer because their constrained solve does
not converge. The fixed QP adaptation interval resolves that retained numerical
case without changing tolerances. Probes 04–05 do not meet the COM transfer
gate. Probe 06 lands one foot but stops during the following transfer; the
requested two-foot walk still fails. Its executed prefix has exact motor
replay, no excess contacts, minimum sole load 302.97 N and maximum pelvis tilt
0.00338 rad. These partial results give no complete walking or manipulation
credit. See `analysis/nicolet_slider_push_06/quasistatic_status.json`.

Probe 07 also fails the next transfer despite an OSQP retry. Probe 08 uses
Clarabel 0.11.1 to solve the same constrained quadratic program, with no
constraint softening. It completes two foot placements in 20.282 seconds,
travels 0.13013 m, and passes independent exact motor/contact replay. Minimum
sole load is 302.97 N and maximum pelvis tilt is 0.00396 rad. This is one
short, in-process development probe, not a qualified walking skill. Solver
fixtures, infeasibility rejection, and the unchanged stationary Balance
regression are recorded in `analysis/quasistatic_solver_01`.

`quasistatic_turning.py` adds an in-place change of heading through alternating
foot placements. Each pair of steps rotates at most ten degrees; the torso
tracks the midpoint of the two sole headings. Landing additionally requires
the swing sole's orientation error to be below 0.02 rad. In the same full lab,
the ten-degree probe completes two steps in 20.112 seconds and the ninety-degree
probe completes eighteen steps in 125.612 seconds. Both independently pass
exact motor replay, contact, support, source-limit, final heading and settled
angular-velocity checks. The ninety-degree run has minimum sole load 315.36 N,
maximum pelvis tilt 0.00727 rad and final heading error 0.0000549 rad. These are
in-process development probes, not isolated navigation or reliability trials;
they have not yet been joined to the station-operation actor. See
`analysis/quasistatic_turn_01` and `analysis/quasistatic_turn_02`.

`quasistatic_turn_walk.py` joins a 90-degree turn to a 0.24 m forward request
using the same stance estimator, balance task and continuous simulation clock.
The transition retains the new body heading, sole anchors and COM target;
encoder/IMU settling gates trigger the next step. Development probe
`analysis/quasistatic_turn_walk_01` finishes 22 foot placements in 157.210 s,
with 0.24916 m net forward displacement. Independent physical review passes:
motor replay is exact, minimum sole load is 302.98 N, joint-limit excess is
zero, and the maximum heading error during the forward walk is 0.00425 rad.
Full-laboratory stills and their trace indices are in its `visual_review`
directory. This probe does not establish carrying or a complete interstation task.

The walking arm pose places the wrists behind the pelvis, around 0.55–0.59 m
above the floor. Earlier descriptions calling it a raised-forearm pose were
incorrect; the joint commands have not been changed to match that wording.
The correction and retained image review are in
`analysis/quasistatic_solver_01/posture_description_correction.json`.

Continuous approach 07 applies the short-step controller to the full one-metre
approach without resetting the plant. It completes the walking/posture handoff
but aborts after losing contact late in the window push. It is retained as a
failed 225.380-second attempt. A post-run diagnosis finds maximum window travel
72.168 mm; this evaluator-side measurement is not an actor observation or a
success claim. Independent physical replay passes every physical criterion;
the completion-status check remains failed. All 112,691 native sensor packets
also reproduce the frozen actor's motor commands, retained responses and
events exactly. The handoff follows 1.02048 m of executed travel, with 0.0431 mm
post-run XY estimation error. No visual confirmation was executed, so the
continuous review still fails overall. The selected-controller isolation probe
also passes; its supplemental report preserves the earlier probe, which used
the default walking-controller argument.

Approach 08 is a new execution with a declared contact-loss recovery policy.
After a late push contact loss, the robot first completes its existing motor
withdrawal. Only then may it inspect the window with native RGB-D. It retains
the fault until eight distinct fresh fits satisfy the existing 66–74 mm
interior guard and the torso completes its return. Overload, failed contact
acquisition, early loss and rejected visual confirmation remain failures.
All physical contact, load, support and travel criteria remain unchanged.
See `analysis/quasistatic_solver_01/approach_08_contract.json`. Fault-injection
checks exercise this logic but do not establish physical success.

Approach 08 executes the recovery withdrawal and subsequent camera observation,
but all 121 native outcome frames fail geometry quality; it returns and ends
failed after 245.620 seconds. Independent physics satisfies every criterion
apart from the failed completion status, and process isolation passes. Its
first frozen sensor replay reproduces every motor command and retained
response exactly, but the full event-sequence comparison fails. The original
report is retained. An additional diagnostic replay exactly reproduces the
motor outputs, retained responses and full event tree, with no mismatch examples.
The first replay did not retain its actual event tree, so that original mismatch
cannot be located or declared fixed. New reviews now retain replayed events and
bounded difference locations, and reject nonfinite numeric comparisons. The observed waist angle is
about -0.495865 rad for a -0.5 rad target. Labeled static views also expose
planar-surface aliases at some other angles, including an out-of-range 60 mm
opening incorrectly estimated above 73 mm. These false acceptances remain in
`analysis/slider_outcome_approach_01`.

The current range observer adds visible relief of at least half the public
CAD grip height: 1.500 mm for this 3.000 mm grip. Applying the stricter code
to retained fit outputs removes both labeled false acceptances without losing
the 41 previous correct acceptances in that study. This is a held-fit guard
test, not a new inference or calibration result. New continuous attempt 09
uses a -0.60 rad viewing target, a tighter 0.005 rad pose gate and stronger
waist-posture tracking. Attempt 09 still fails visual confirmation after
245.800 s; process isolation passes. Its independent physical replay passes
every criterion except attempt completion. Frozen sensor replay now reproduces
all motor commands, retained responses and events exactly (maximum errors zero)
from 122,901 packets and 2,459 camera frames. The trial still fails completion;
replay integrity does not turn a failed operation into a successful one.
A native-depth diagnostic at 225.5 s finds that only 59 of the
182 selected points lie within 0.25 mm of the actual grip mesh. This is an
evaluator-side diagnosis of mixed surfaces, not an actor input or a proposed
lower acceptance threshold. Camera-facing surface fits and a denser bounded
fit search also fail the existing criteria; neither is adopted. Its contract and the static collision screen
are retained in the same analysis directory; the latter is not executed motion.

The depth buffer inherited four-sample display anti-aliasing. A retained-pose
diagnostic reproduces the original depth image exactly and then renders the
same geometry with multisampling disabled. At 150 evaluator-labeled grip
pixels, the median pixel-centre projection error drops from 0.231 mm to
0.00147 mm; the 95th percentile drops from 0.658 mm to 0.00288 mm. This is a
numerical rendering check at one pose, not hardware calibration. MuJoCo's
[offscreen rendering documentation](https://mujoco.readthedocs.io/en/latest/programming/samples.html#record)
identifies `visual/quality/offsamples` as the offscreen multisampling setting.
`sensor_rendering.py` now creates an unmixed depth context and restores the
model preference before RGB rendering; new sensor profiles record both values.
The physical model, observer thresholds and prior recordings are unchanged.

Counterfactual observations using this corrected depth still obtain only four
accepted closed-grip frames out of the 42 recorded candidate frames. The
unchanged eight-frame baseline requirement therefore fails before outcome
testing. A separate lower-plane-removal fitter also fails that gate and is
not adopted. These retained failures show that depth sampling alone does not
complete the observer integration.

The remaining failure was traced to the key-cap plane used to register the
grip: its 0.25 mm RANSAC band admitted bevel pixels. Tightening that band to
0.05 mm preserves the support-count and spatial-span requirements and excludes
the bevel. On corrected-depth views at retained approach-09 poses, the fitter
accepts 40 of 42 closed-grip frames, then all eight outcome frames with about
0.27 mm position error. Twelve labeled static openings include both sides of
the allowed interval; none outside it are accepted. These are counterfactual
observation fixtures, not a new robot execution or hardware calibration.
The failed earlier fixtures are retained. Approach 10 used a recorded
contract, the corrected depth context and the tighter key-plane band. It
finishes at 245.990 s but fails the final range guard: all 120 outcome views
identify the grip geometry, while the estimated opening is about 75.05 mm
and the actual opening is 74.7826 mm. The 66–74 mm visual guard correctly
rejects this edge-of-range result. Process isolation passes. Independent
physical replay passes every criterion except attempt completion, including
exact motor replay, intended-pad contact, support and unchanged collision
bounds. Frozen-sensor replay is still running.
The physical gap, collision, support and fresh-frame acceptance criteria are
unchanged.

The grip surface is sloped: its normal projects -0.258819 onto the slider
axis. Normal preload can therefore add opening beyond the nominal wrist
stroke. A new stop estimate intersects the encoder-derived fingertip contact
point with the observed rest plane and the public slider axis. It requires
distal tactile contact and does not read any device joint or plant contact.
Predictions are saved before evaluator comparisons. In retained approaches
09/10, the first loaded 70 mm estimate occurs at actual openings of
68.300/70.236 mm; these are offline checks, not executed stopping behaviour.

Approach 11 is now running with this stop estimate. On reaching 70 mm, it
holds the attained wrist position and rotation, then withdraws from that
pose without finishing an unused nominal stroke. A bounded stop interval,
tactile loss and overload still trigger failure/recovery. The estimate is
only a control stop; eight fresh camera confirmations and the unchanged
independent physical review remain necessary. No new successful movie or
complete paper branch is credited.

To reproduce the current short development probe, install the pinned
requirements, use the retained full lab from approach 06 and a new empty
output directory. Review the execution separately:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl \
python simulation/g1_cooling_demo/check_quasistatic_walking.py \
  simulation/g1_cooling_demo/runs/ftir_approach_06 /tmp/sciencegym-step-new
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl \
python simulation/g1_cooling_demo/verify_quasistatic_walking.py \
  simulation/g1_cooling_demo/runs/ftir_approach_06 /tmp/sciencegym-step-new
```

For a continuous approach, run and review a new directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl \
python simulation/g1_cooling_demo/run_ftir_approach.py \
  --out /tmp/ftir-approach-new --duration 420 --walking-controller quasistatic \
  --prior assets/nicolet_6700_mechanism_v1/slider_push_prior_238_first.json
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_ftir_slider.py /tmp/ftir-approach-new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_isolation.py /tmp/ftir-approach-new
OPENBLAS_NUM_THREADS=1 MUJOCO_GL=egl python simulation/g1_cooling_demo/verify_ftir_approach.py /tmp/ftir-approach-new
```

Large continuous trajectories are versioned as byte-exact chunks. Before
reviewing a cloned attempt with `trace_archive.json`, run its recorded
`restore_command` from the repository root. The archive helper verifies each
part and the complete SHA-256 before publishing the restored `trace.npz`.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl \
python simulation/g1_cooling_demo/run_ftir_slider.py \
  --out /tmp/ftir-observed-new --duration 150 --observe-outcome
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_ftir_slider.py /tmp/ftir-observed-new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_isolation.py /tmp/ftir-observed-new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_slider_outcome.py /tmp/ftir-observed-new
MUJOCO_GL=egl python simulation/g1_cooling_demo/render_ftir_slider.py /tmp/ftir-observed-new
```

The separate offline plane study `analysis/ftir_cover_plane_04` rejects
views with fewer than 500 supporting depth pixels. On development runs
07/08 it accepts 60/59 of 81 frames, with maximum accepted-frame angle errors
of 0.074/0.076 degrees. The gate was selected using those runs, so these are
development results. Applied unchanged to run 09, it accepts 60 of 81 frames
with maximum error 0.070 degrees. This is one additional trajectory with
the same setup, not sensor calibration or broad validation. The estimator
is not integrated into the actor; rejected near-edge/occluded views and
reacquisition remain unresolved.

Reports are under `runs/ftir_cover_*/physical_cover_review.json` and
`isolation_verification.json`. The diagnostic data under
`analysis/ftir_cover_*` records
the geometric and sensing decisions. Sensor predictions are saved
separately before post-prediction plant-state error review; that truth is not fed
back to the actor. Cover opening remains unqualified. Review versions in
runs 01–04 counted whole-finger handle loads; later versions require actual
tactile-pad/handle contacts, so a link-shell contact cannot stand in for a
pad grasp.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=1 \
python simulation/g1_cooling_demo/run_ftir_cover.py \
  --out simulation/g1_cooling_demo/runs/ftir_cover_new --duration 60 --initial-xy 5.95 -5.32
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_ftir_cover.py \
  simulation/g1_cooling_demo/runs/ftir_cover_new
OPENBLAS_NUM_THREADS=1 python simulation/g1_cooling_demo/verify_isolation.py \
  simulation/g1_cooling_demo/runs/ftir_cover_new
```
