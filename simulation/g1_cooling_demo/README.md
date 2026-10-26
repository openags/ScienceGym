# G1 / Inspire contact runtime

The contact plant now also runs in the existing complete laboratory. The
[laboratory runtime](LABORATORY.md) imports the original room, furniture and
equipment, with G1 and the white tray as dynamic bodies. Other equipment stays
fixed; articulated devices, loaded walking and the full paper campaign remain
open. The [laboratory recording page](../../viewer/cooling_lab_runtime_v1/index.html)
shows the resulting contact subtask with enforced actor access isolation. The
runtime guide records the namespace probes and independent packet-rejection
check. A separate 12-second unloaded walking and stationary-control handoff
recording advances 1.96 m, with independent replay and contact checks. It is
not yet joined to the tray sequence. Sensor calibration and general localization
remain open. The earlier independent workbench tests
below remain unchanged as development evidence.

The requested [full-laboratory conceptual film](../../viewer/cooling_concept_v1/watch.html)
is available separately, with its [paper-operation mapping and reproduction notes](../../viewer/cooling_concept_v1/README.md).

The earlier workbench presentation contains **80.54 seconds of one uninterrupted simulation**: a standing G1 picks up a tray containing a preloaded laboratory spatula, transports it across the bench, places and releases it, observes it again, picks it up again, returns it to the source and retracts its hands. The same floating robot and objects remain in the scene throughout. This is **one carrier transport subtask**, not the complete directional-cooling paper demo. There are still **0 of 11 qualified paper branches, 0 qualified skills and 0 qualified campaigns**. Parallel scene/controller development is authorized; asset acceptance remains pending.

Serve the repository root with `python -m http.server 8769 --bind 127.0.0.1` and open <http://localhost:8769/viewer/cooling_demo_v1/index.html>. The page presents the recording, contact close-up, synchronized native head depth, event timeline, measured trajectory and independent verification. The manipulation world is a **local test bench**, not the complete laboratory collision scene. The room and equipment review is linked separately.

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
