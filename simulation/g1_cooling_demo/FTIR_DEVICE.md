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

All eleven attempts retain source snapshots, isolated input bundles, lossless
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
Run 11 itself used the earlier full-resolution predictor. A future complete
run still must validate the revised runner.

The official Inspire tactile-hand manual is linked with a content hash in
`analysis/inspire_tactile_definition_01/source.json`. Its tactile arrays report
16-bit raw samples (0–4096), while force-control registers are a separate
interface. The seven scalar Newton channels above remain an inferred simulator
abstraction. Source mesh sizes suggest distinguishing small terminal pads from
larger fingertip pads, but that mapping is not a calibrated register-to-mesh
binding; the rejected large-pad search does not authorize a collision exemption.

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
