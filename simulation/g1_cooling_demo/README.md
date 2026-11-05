# G1 humanoid contact runtime

The latest [23.58-second three-finger tool recording](runs/dex3_tool_grasp_06/overview.mp4)
passes its [independent physical evaluation](runs/dex3_tool_grasp_06/physical_review.json),
[isolated controller replay](runs/dex3_tool_grasp_06/controller_replay.json) and
[source motor torque/speed checks](runs/dex3_tool_grasp_06/source_limit_review.json).
The free tweezer rises 24.98 mm, remains lifted without tray support for 1.95 s,
and is lowered, released and left supported while the hand withdraws.
This single attempt starts at an authored pregrasp. It does not qualify visual
localization, approach, tool use on a specimen, carrying, repeatability or a
paper branch. The earlier walking/window run uses Inspire hands; that result
does not transfer automatically to the three-finger model. There remain
**0 of 11 qualified paper branches and 0 qualified complete campaigns**.

The contact plant now also runs in the existing complete laboratory. The
[laboratory runtime](LABORATORY.md) imports the original room, furniture and
equipment, with G1 and the white tray as dynamic bodies. A separate
[passive FTIR device candidate](FTIR_DEVICE.md) adds contact-driven cover and
key diagnostics in that laboratory. One G1 sliding-window operation now passes
independent contact replay and post-operation visual confirmation; full cover
opening, loaded walking and the full paper campaign remain open.
The [laboratory recording page](../../viewer/cooling_lab_runtime_v1/index.html)
shows the resulting contact subtask with enforced actor access isolation. The
runtime guide records the namespace probes and independent packet-rejection
check. A separate 12-second unloaded walking and stationary-control handoff
recording advances 1.96 m, with independent replay and contact checks. It is
not yet joined to the tray sequence. Sensor calibration and general localization
remain open. The earlier independent workbench tests
below remain unchanged as development evidence.

The current [continuous FTIR measurement film](../../viewer/cooling_concept_v2/measurement_demo.html)
shows 9 minutes 1 second of tool collection, walking to the material bench,
carrying the witness back, gold-reference/sample operations and cleanup in the
full laboratory. Its [delivery record](../../viewer/cooling_concept_v2/measurement_delivery.json)
distinguishes the geometric review from unfinished physical qualification.
The [5 minute 33 second edition](../../viewer/cooling_concept_v2/measurement_demo.html?cut=brief)
retains both walking legs and all operation stages, with a synchronized room
map. The separate [117 second window recording](runs/ftir_slider_07/slider.mp4)
shows a physically executed push, withdrawal, camera confirmation and return.
Its [physical review](runs/ftir_slider_07/physical_slider_review.json) and
[native-sensor replay](runs/ftir_slider_07/visual_outcome_review.json) pass.
That recording starts at an authored station pose; it does not validate the
cross-station film's carrying or complete measurement sequence.

The newer [233.6-second continuous approach recording](runs/ftir_approach_11/slider.mp4)
executes a 1.020 m local aisle approach, sensor-derived station handoff, tactile
window push, withdrawal and native RGB-D outcome confirmation in the original
laboratory. Its [independent physical review](runs/ftir_approach_11/physical_slider_review.json)
and [complete sensor/controller replay](runs/ftir_approach_11/continuous_approach_review.json)
pass: all 116,801 motor outputs and 2,337 retained camera frames were replayed;
the final physical opening is 70.999 mm. The earlier replay stopped on a missing
`rtree` dependency; its failed report is retained under
`replay_attempts/missing_rtree_01/`. The restored environment and corrected
full-output coverage check do not alter the frozen actor or physical trajectory.
This is one local approach and operation, with no carrying, complete branch or
reliability qualification. The recording and timestamp controls are on the
[laboratory recording page](../../viewer/cooling_lab_runtime_v1/index.html).

The earlier workbench presentation contains **80.54 seconds of one uninterrupted simulation**: a standing G1 picks up a tray containing a preloaded laboratory spatula, transports it across the bench, places and releases it, observes it again, picks it up again, returns it to the source and retracts its hands. The same floating robot and objects remain in the scene throughout. This is **one carrier transport subtask**, not the complete directional-cooling paper demo. There are still **0 of 11 qualified paper branches, 0 qualified skills and 0 qualified campaigns**. Parallel scene/controller development is authorized; asset acceptance remains pending.

Serve the repository with `python simulation/cooling_v1/serve.py --port 8769 --bind 127.0.0.1` (including video range requests) and open <http://localhost:8769/viewer/cooling_demo_v1/index.html>. This older workbench page presents the recording, contact close-up, synchronized native head depth, event timeline, measured trajectory and independent verification. Its manipulation world is a **local test bench**, not the complete laboratory collision scene. The room and equipment review is linked separately.

## Full-laboratory tool development

`build_tool_station.py` places the free passive tweezer and ordinary free tray
in the existing room with the complete G1. `runs/tool_station_04/review.json`
passes initial geometry, source inertia/contact preservation, actual bench
height, tray footprint and whole-robot collision checks. This is authored
initial staging; there is no robot placement or grasp credit. The original
optical attachment remains on the bench. The first proposed placement collided
with it; the corrected staging translates the robot/tool/tray by 0.35 m and
0.03 m in laboratory coordinates. Initial images are in that station folder.

`runs/tool_station_05` preserves this geometry while splitting the static room
architecture into smaller bodies for collision broad-phase rejection. The
bounded `analysis/tool_collision_partition_01` comparison retained identical
100-step zero-torque states and reduced measured runtime from 5.43 to 0.84 s.
A broader partition attempt ran out of collision-stack memory; a spatially
grouped variant changed the sampled trajectory. Those alternatives are retained
and are not the selected execution model. The short comparison does not qualify
standing, manipulation or a complete trajectory.

`run_tool_grasp.py` and `tool_grasp_actor.py` execute an isolated full-body
attempt from the declared pregrasp. Own-robot encoders and IMU feed a full-body
load predictor; arm motion compensates the change in the source pad midpoint
as the fingers close. Observed sustained opposing load gates a lift, hold,
lower and release attempt. The actor has no visual tool localization or
executed approach. `verify_tool_grasp.py` separately replays the frozen actor,
physics and native sensors and checks actual loaded lift, contact, tool closure
and released support. Read each attempt's result and review; no tool grasp,
paper branch or repeated-reliability qualification has been established.

The slow `runs/tool_grasp_01` baseline was explicitly interrupted after the
first 174 recorded monitor rows matched `tool_grasp_02` exactly through 1.73 s.
Its interruption record and partial monitor remain; its full in-memory trace
was not saved. `tool_grasp_02` is the separate attempt on the partitioned room,
not a continuation spliced onto that baseline.

`tool_grasp_02` ended after 13.955 simulated seconds with loss of opposing
finger load. Frozen controller replay and continuous physics/native-sensor
replay are exact, but the physical verdict fails: only 0.346 seconds of
bilateral contact, no held lift, and an initial sole-contact excursion beyond
the 1 mm bound. Recorded contacts lie on the finger housings, with an axial
separation of about 12.7 mm; the tool rotates and falls into the tray. See its
`final_review_summary.json`, contact diagnosis and recorded stills. An exact
replay of that failure is not a successful grasp.

### Official three-finger candidate

`fit_dex3_tweezer.py` uses the already pinned official Unitree three-finger
resource in `analysis/g1_dex3_comparison_01`. It fits original source exterior
points and checks the actual supported tool mesh, tray and bench plane.
`dex3_tweezer_fit_01` has no accepted placement; its palm lies below the tool.
Reversing the tool-axis orientation yields 23 local candidates in `_02`.
They are geometric proposals, not executed grasps.

The source visual mesh has a palm/thumb-1 assembly overlap throughout the
221 configurations in `dex3_thumb_interference_01`. It is disclosed rather
than removed. A separate issue in the earlier static-root inspection caused
extra native collision reports. The new `hand_self_check.xml` adds only a
free wrist, preserving the source collision geometry and dynamic parent
filtering. Native collision checks use the manufacturer's collision shapes;
original visual triangles still check external tool and tray intersections.

`build_dex3_tool_station.py` replaces the two official wrist/hand subtrees,
retaining the complete room, other body inertias, free tray and passive tool.
The model has 43 independent motors. The first three station searches fail
reach or collision checks. Rotating the authored tray/tool arrangement by
180 degrees produces five full-body static candidates in
`runs/dex3_tool_station_04`. This is a different initial arrangement, with
no executed rearrangement credit. `dex3_pregrasp_01` opens the chosen hand
before contact and passes initial bounds with no robot/tool contact; its
overview and contact images show the actual original laboratory.

`dex3_tool_grasp_01` fails after 0.129 seconds: gains transferred from the
previous hand cause severe finger oscillation and excessive contact. Its
controller and physical replay reproduce that failure. The subsequent actor
bounds proportional and damping gains using the robot-only coupled hand
inertia and the control period, without changing the plant's mass or armature.
Read the later attempt's own result and independent review before assigning
any execution outcome. This pickup test does not qualify squeezing the tool
on a specimen, perception, approach, carrying, a paper branch or reliability.

`dex3_tool_grasp_02` ends after 14.005 seconds without enough sustained load
to lift. Controller, physics and native sensor replay are exact. Contact and
released-support bounds pass, but the physical verdict fails, including a
3.635 mrad thumb distal-joint excursion beyond its source limit. Its separate
torque/speed check passes; that check does not cover position limits. The
verifier's write-time source-hash issue is documented and reconciled in
`verifier_runtime_provenance.json`, preserving the original report and every
physical metric. Future verifiers capture their hash at import and run from
a frozen source copy.

`dex3_tool_grasp_03` reaches the lift phase but loses the tool. The 16.993-second
attempt and exact-byte trace chunks are retained. Sparse wrench diagnostics
show marginal grip support during lift and infeasible static equilibrium at
the late slipped contact configuration; they are not continuous verification.
The full independent verdict must be read separately. A 4.730 mrad thumb
distal-joint excursion also excludes qualification.

The next setup, `dex3_tool_station_05` / `dex3_pregrasp_03`, selects a source
grasp with the thumb distal joint farther inside its limit, and restricts
authored elbow flexion to at least 0.15 rad inside the original source range.
One of 125 searched poses passes the initial scene checks. The new force
targets are explicit actor-prior inputs and pinned in each run contract;
the physical acceptance limits remain unchanged. Initial setup and controller
changes do not establish grasp success.

`analysis/dex3_device_sleep_02` tests native sleeping only for the unattended
instrument cover; the robot, tool, tray and instrument keys are never allowed
to sleep. A 0.2-second replay preserves all robot/tool/tray states bit for bit
and reduces measured wall time from 12.70 to 6.00 seconds. The separate
`dex3_cover_wake_02` diagnostic drops a free 20 g sphere onto the actual cover:
the sleeping cover wakes on contact, with a maximum 3.2 nm position difference
from the unslept baseline. This added sphere exists only in diagnostic files.
`dex3_pregrasp_04` binds the tested sleep configuration to the next authored
initial scene. Complete execution and independent replay remain required;
the short comparison does not qualify a grasp or a whole-device interaction.

`dex3_tool_grasp_04` and `_05` both lift the tool but fail the independent
released-support condition because a finger retains contact. The paired
sleeping/unslept full trajectories differ; the short sleeping diagnostic is
not a claim of identical full-run behavior. Each run's own physics replay is
exact. `_06` adds bounded extra finger opening, an encoder-derived residual-load
release gate and a 20 mm wrist withdrawal. All sixteen independent physical
checks pass, including actual held lift, released support, source joint limits
and bounded contact. Its frozen execution result remains the original
pre-evaluation record; the separate reviews contain the subsequent verdict.
No earlier failed trace or verdict is overwritten.

## Reproduce

Use Python 3.11+, EGL-capable OpenGL and `requirements.txt`. Current sensor runs also require Linux with bubblewrap and enabled unprivileged namespaces; see [the runtime guide](LABORATORY.md). The workstation environment is `/tmp/sciencegym-sim-venv/bin/python`. Run from the repository root, choosing a new directory so evidence is not overwritten:

```sh
export OPENBLAS_NUM_THREADS=1
export MUJOCO_GL=egl
python simulation/g1_cooling_demo/run.py --out /tmp/g1-continuous-new --duration 100 --tray --closed-loop --return-to-source --com-align --payload --payload-kind spatula --grip-force 15
python simulation/g1_cooling_demo/verify_transport.py /tmp/g1-continuous-new
python simulation/g1_cooling_demo/render_continuous.py /tmp/g1-continuous-new --movie
python simulation/g1_cooling_demo/render_depth.py /tmp/g1-continuous-new
```

The selected episode is `runs/continuous_tool_transport/`. Inspect both `result.json` and `transport_verification.json`; completion is not qualification. Models in this selected directory reference repository-relative paths. Recorded source snapshots identify the exact run version; execute the current tools from the repository, not snapshots in isolation. A metadata-only defect reported an 18 N grip default instead of the 15 N actually passed to the actor; `metadata_correction.json` documents the source lines and original result hash. The original result remains intact. The current writer is fixed.

The previous 38-second initial-localization/timed-trajectory episode remains unchanged in `runs/delivery/` and can be reproduced with `--duration 38 --tray --sensor-actor`, followed by `verify.py` and `render.py --movie`.

## Robot, perception and control

The source-derived Unitree G1 29DoF rev1.0 / Inspire FTP model retains its 41 motors, hand mimic constraints, floating base and original hand collision components. Ordinary ground contact supports the robot. No root actuator, base weld, applied body support force, object reset or invisible grasp is used after initialization. Grip forces are converted to joint motor torques. This is a palm-contact grip; a dexterous finger-grasp policy has not been qualified.

A separate actor process receives only joint encoders, an idealized pelvis IMU, head depth and time. It estimates translation using fixed-foot kinematics. The depth tracker subtracts an estimated robot and known empty-bench background and observes a single carrier in a known workspace. It receives no object poses, segmentation, contact enumeration or evaluator predicates. These fixed-foot/background assumptions, camera calibration and process security are not qualified for a general laboratory.

The author-defined transport policy follows approach, grip, lift, transfer, place, release and retraction stages. Fresh depth observations gate lift confirmation, destination confirmation, placement and release before progression. After placement it estimates the carrier again for the return. Smooth COM alignment supports the off-center second grasp. The final retracted hand targets remain active for an eight-second stability hold. A failed visual gate terminates the episode; **safe recovery is not implemented**. No claim of autonomous paper-to-policy synthesis is made.

## Objects and assumptions

The tray is the existing Bürkle 4208-0022 reconstruction, 300 × 200 × 50 mm. Seeded CoACD decomposition approximates its hollow shell. The 1.2 mm sheet, steel density, inferred mass of approximately 0.951 kg, inertia, friction, compliance, approach offsets and stage times are engineering assumptions, not measured physical parameters.

The selected payload uses the existing Bürkle 5386-0041 spatula reconstruction, 150 × 9 × 3.5 mm. Mesh volume and assumed steel density produce approximately **9.3 g**. Its single convex collision approximation is unqualified. It starts inside the tray, so this episode earns **no robot loading credit**. The separate approximately 0.806 kg copper-stock trials failed; the spatula episode does not validate heavy carrying. Load compensation in copper trials changes commanded joint torques only and adds no physical support force.

## Evidence and limits

`trace.npz` records positions, velocities, motor commands and solver warm starts at 100 Hz, with 500 Hz physics. `sensor_observations.npz` records actor proprioception. `policy_observations.json` and result events retain the depth-based stage decisions. Head depth is recorded at 10 Hz as lossless float32 byte-plane chunks, with bitwise round-trip checks and per-chunk hashes.

`verify_transport.py` independently checks actual lifts, displacement, return accuracy, stable table placement, hand release, payload retention, fresh observed transition evidence and source hashes. It continuously replays recorded motor torques from the initial state without state correction and compares the physics trajectory. Rendering displays those recorded states at 1×, without scene resets or manufactured outcomes. `model_inputs.json` and `manifest.json` pin the selected episode's dependencies and outputs.

`extended_attempts.json` indexes all second-hour development attempts, including a model setup failure, grasp failures, heavy payload failures and failures after transport during parking. `attempts_extended/` retains their available models, snapshots, traces, sensor observations and depth. Legacy depth arrays are losslessly repacked, preserving their original SHA in encoding receipts. These changing controller versions must not be pooled into an acceptance success rate. Original diagnostic model paths can reference the workstation; the selected episode is the portable replay artifact. `attempt_archives/` and `attempts.json` retain the earlier sprint's records.

Full-demo work still includes accepted assets and room clearances, full laboratory dynamics, loaded carrying and walking, assembly, connectors, thin films, configuration changes, recovery and cleanup across all 11 paper branches. The contract requires at least 19/20 for skills, 9/10 per branch and three complete campaigns. These are not yet achieved. No hardware run or scientific-result reproduction is claimed.
