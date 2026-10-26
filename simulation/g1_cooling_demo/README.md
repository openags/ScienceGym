# G1 / Inspire contact development demonstration

This is a **single empty-tray manipulation episode**, not the complete directional-cooling paper demo. The first paper still has **0 of 11 qualified branches, 0 qualified skills and 0 qualified campaigns**. The owner authorized scene and controller development in parallel on 2026-10-26; asset acceptance remains pending.

Open [the presentation page](../../viewer/cooling_demo_v1/index.html) through the repository HTTP server:

```sh
python -m http.server 8769 --bind 127.0.0.1
# http://localhost:8769/viewer/cooling_demo_v1/index.html
```

The page includes the continuous 38-second physics recording, timeline, measured tray trajectory, independent verification and the complete asset-review scene. The manipulation video uses a **local test workbench**, not the full laboratory collision scene.

## Reproduce

Use Python 3.11+ and an EGL-capable OpenGL installation. Install `requirements.txt` into a virtual environment. The current workstation environment is `/tmp/sciencegym-sim-venv/bin/python`.

From the repository root, choose a **new** output directory (existing evidence is never overwritten by the runner):

```sh
export OPENBLAS_NUM_THREADS=1
export MUJOCO_GL=egl
python simulation/g1_cooling_demo/run.py --out /tmp/g1-tray-new-attempt --duration 38 --tray --sensor-actor
python simulation/g1_cooling_demo/verify.py /tmp/g1-tray-new-attempt
python simulation/g1_cooling_demo/render.py /tmp/g1-tray-new-attempt --movie
```

Inspect `result.json` and `verification.json`; executor completion does not imply task qualification. `runs/delivery/` contains the packaged attempt. Model paths in that directory are relative to this repository and work after moving the complete checkout. Source snapshots document the code used by each attempt; execute the current scripts above from the repository, not the snapshot directory in isolation.

## What executes

The existing source-derived Unitree G1 29DoF rev1.0 / Inspire FTP model retains its 41 motors, hand mimic constraints, floating base and source hand collision components. The robot is supported by ordinary ground contacts. No root actuator, base weld, body support force, object pose reset or invisible grasp is used after initialization.

A separate actor process receives only joint encoder positions/velocities, an idealized pelvis IMU, head depth pixels and time. It estimates translation using fixed feet and robot kinematics, finds the tray in the first two seconds of depth images, and sends joint motor torques. Balance control includes joint feedback, constrained inverse dynamics and motor torque limits. The grip uses actual source hand contacts and inward forces converted into joint torques. The hands do not execute a qualified dexterous finger-grasp policy.

The declared tray is Bürkle 4208-0022, 300 × 200 × 50 mm. Its visual mesh comes from the existing ordinary-tools reconstruction. A seeded CoACD decomposition approximates its hollow shell for contact. The selected 1.2 mm sheet, steel density, inertia, friction, compliance, approach offsets and timed trajectory are engineering assumptions; they are not measured device parameters. The custom workbench is a development fixture with ordinary dimensions and no object locks.

The actor does not read object poses, contact enumeration, segmentation, evaluator predicates or success outcomes. Its process separation and strict input schema are implemented; a hardened OS sandbox and sensor calibration are **not** qualified. Initial depth localization is followed by timed approach/grip/lift/transfer/place/retract stages. Grasp-success perception, slip recovery and task-level feedback remain open.

## Evidence and limits

`trace.npz` records physics positions, velocities, motor torques and solver warm starts at 100 Hz; the plant integrates at 500 Hz. `sensor_observations.npz` contains actor proprioception and `head_depth.npz` contains 10 Hz depth frames. `verify.py` independently replays motor torques continuously from the initial state, without state corrections, and checks the resulting trajectory, lift, transfer, stable placement and hand release. Rendering merely visualizes those recorded states. The delivery checks are single-episode development checks, not the contract's 19/20 skill, 9/10 branch or three-campaign acceptance trials.

`attempt_archives/` retains earlier exploratory states, including failed attempts. The oldest diagnostic runs used simulator robot proprioception and did not snapshot code, so they are debugging records, not reproducible qualification evidence. Later sensor attempts include exact source snapshots. The archive retains original model paths, which reference the original workstation; use the packaged delivery directory for portable replay.

Outstanding full-demo work includes accepted assets and room clearances, loaded carrying and walking, assembly, connectors, thin films, configuration changes, recovery, cleanup, all 11 paper branches and independent repeated-run evaluation. No physical hardware run or scientific-result reproduction is claimed.
