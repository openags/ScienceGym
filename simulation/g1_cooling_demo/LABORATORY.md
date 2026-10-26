# Contact runtime in the existing laboratory

The contact plant now imports `assets/cooling_lab_v1/scene.json`, including the original architecture and all 81 asset identities. G1 and the white tray bind to the dynamic robot and tray; the other 79 assets stay fixed in their initial poses. The imported 6,537 environment parts retain 5,497,793 source triangles, dimensions and placements. Compiled-vertex comparison against the original GLBs checks the actual model rather than trusting the import receipt. Zero-thickness signs remain visible surfaces without contact volume. Other static parts use MuJoCo's per-mesh convex contact hull, so holes, concave equipment cavities, device articulation and cable mechanics remain unqualified.

The initial recorded episodes are `runs/laboratory_transport_01/` (empty tray) and `runs/laboratory_tool_transport_01/` (tray with a preloaded Bürkle spatula). The current `runs/laboratory_isolated_tool_01/` repeats the loaded route with enforced actor access restrictions. Each lasts 80.54 seconds and uses native-head depth, joint encoders and IMU observations. The actor's model includes the authored architecture as a static map, but excludes loose equipment and the target. Sensor calibration and general localization remain open. This is still a stationary carrier subtask; it grants no walking, tool-loading, branch or campaign qualification.

The current actor runs inside bubblewrap with separate filesystem, process and network namespaces, no effective Linux capabilities, read-only code/model inputs and private temporary storage. Its bundle contains only eight actor modules and the controller model's dependency closure. Robot initialization is separated from world construction so the actor cannot read target setup code. Before stepping the plant, active probes check that plant files, task operations, the evaluator and the parent process are inaccessible, that inputs are read-only, and that GPU rendering works. An independent malformed-packet test requires the actor to reject an extra simulator-object field before control. The isolated run's recorded time, positions, velocities, controls and warm starts are byte-for-byte identical to the earlier loaded run. These access tests are not a kernel/GPU security audit or a sensor-calibration qualification. Earlier unisolated records remain unchanged.

The robot starts at laboratory XY `[3.7, 2.02]`, facing +Y. The white tray starts at `[3.7, 2.53, 0.9005]` on the existing white assembly worktop. These explicit initial staging changes leave the source review scene unchanged and are not credited as robot actions. The work frame maps to the laboratory through the rigid transform in `laboratory_import.json`. No robot base, tray or tool poses are overwritten after initialization. No substitute bench or infinite ground plane remains in the plant.

Serve the repository root on port 8769 and open [the runtime recording page](../../viewer/cooling_lab_runtime_v1/index.html). The clean main video renders recorded physical states in the full room; the expandable depth recording uses the original sensor stream. The 9-minute 39-second [conceptual presentation](../../viewer/cooling_concept_v1/watch.html) remains a separate artifact.

## Reproduce

First restore the existing source GLBs, including the manufacturer CAD derivatives described in [the laboratory asset instructions](../../assets/cooling_lab_v1/README.md#central-support-from-manufacturer-cad). The importer checks their recorded hashes. Generated MSH/PNG inputs go to the ignored `lab_cache/`; this avoids redistributing locally generated manufacturer geometry. Use Linux with bubblewrap, enabled unprivileged namespaces, GPU device access and the dependencies in `requirements.txt`. Sensor actors default to enforced isolation and fail closed if its probe fails. `--unisolated-actor` explicitly selects the historical diagnostic mode. Run from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1
export MUJOCO_GL=egl
python simulation/g1_cooling_demo/run.py --out /tmp/g1-laboratory-new --laboratory --duration 100 --tray --closed-loop --return-to-source --com-align --grip-force 15 --payload --payload-kind spatula
python simulation/g1_cooling_demo/verify_laboratory.py /tmp/g1-laboratory-new
python simulation/g1_cooling_demo/verify_transport.py /tmp/g1-laboratory-new
python simulation/g1_cooling_demo/verify_payload.py /tmp/g1-laboratory-new
python simulation/g1_cooling_demo/verify_isolation.py /tmp/g1-laboratory-new
python simulation/g1_cooling_demo/render_laboratory.py /tmp/g1-laboratory-new --movie
python simulation/g1_cooling_demo/render_depth.py /tmp/g1-laboratory-new
```

The workstation environment is `/tmp/sciencegym-sim-venv/bin/python`. To rebuild the ignored mesh/texture cache for replaying the committed episodes without starting another physical run:

```sh
python - <<'PY'
import sys
sys.path.insert(0, 'simulation/g1_cooling_demo')
from world import build
build('/tmp/sciencegym-lab-cache-preparation', tray=False, laboratory=True)
PY
python simulation/g1_cooling_demo/isolation.py --restore-inputs simulation/g1_cooling_demo/runs/laboratory_isolated_tool_01
```

`model_inputs.json` pins the compiled models, source GLBs, generated meshes and textures, including the isolated actor's model. Its ignored mesh/texture copies are restored by the second command above; recorded model and code bytes are preserved. `trace.npz`, depth chunks, proprioception, actor events and source snapshots preserve the original run. Independent evaluation replays motor commands continuously without pose corrections, checks final support against the original worktop, and checks tool containment at every recorded 100 Hz state. All attempts, including the initial compile failure on a zero-thickness sign, are retained in `laboratory_attempts.json`. These nominal examples are not a preregistered reliability campaign.

The renderer records presentation-only lighting, colour-transfer and texture-origin adjustments separately. It does not alter geometry, sensor evidence, contacts or physical state. Mesh import and contact semantics follow the [MuJoCo mesh reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html#asset-mesh).

## Unloaded walking and stationary handoff

`runs/laboratory_walking_07/` records 12 continuous seconds in the same laboratory, including 1.957 m of forward travel and transfer to stationary balance control at 6.602 s. The independent 500 Hz motor replay passes 13 checks with zero position/velocity discrepancy, including feet-only floor contact, lateral deviation below 0.25 m and stable parking. Ten geometry checks and seven actor-access checks also pass. The recording page includes this second, clean video. This sequence is not yet joined to the tray sequence and grants no carrying, navigation or reliability credit.

The velocity policy and reference code are pinned from [Unitree's official G1 29DoF deployment](https://github.com/unitreerobotics/unitree_rl_lab/tree/4960b84732b0c2ec593dccbfe963fda1bcd7b1e3/deploy/robots/g1_29dof/config/policy/velocity/v0). `locomotion_policy/SOURCE.json` preserves hashes and upstream paths; the upstream Apache-2.0 licence is included. The 480-value input preserves the published term ordering, five-sample histories, encoder mapping, IMU convention and action scaling. The actor receives no root translation, contacts or scene object state. Its authored speed schedule and IMU heading correction are not goal-directed navigation.

The walking plant uses the upstream training configuration's 0.01 kg m² body-joint rotor inertias and training gains, preserving the existing rigid-body inertias, hands and scene geometry. `actuator_adaptation.json` records this difference from the earlier tray plant. The stop transition uses a declared level-foot/IMU gate and the fixed-foot proprioceptive estimator, then the existing torque-based balance controller. Foot-wrench limits rotate with each sole; the pelvis target preserves the observed heading. A 90-degree rotation check gives a maximum motor-torque difference of 1.78e-11 N m. General localization, foot-slip detection and recovery remain open.

All seven development versions remain in `walking_attempts.json`: initial support loss, insufficient movement, route deviation and wall contact, continued travel after stopping, unstable parking, failed controller handoff, and the passing final trial. Trial 02 retains a correction for four unintentionally altered little-finger rotor inertias; the current runner selects the 29 body joints by exact name. These changing versions must not be pooled into a reliability success rate.

```sh
python simulation/g1_cooling_demo/run_walking.py --out /tmp/g1-walking-new --speed .4 --hold-heading --stop-at 6 --duration 12 --park
python simulation/g1_cooling_demo/verify_walking.py /tmp/g1-walking-new
python simulation/g1_cooling_demo/verify_laboratory.py /tmp/g1-walking-new
python simulation/g1_cooling_demo/verify_isolation.py /tmp/g1-walking-new
python simulation/g1_cooling_demo/render_laboratory.py /tmp/g1-walking-new --movie --follow-robot
```

The same dependency and generated-input restoration instructions above apply. Recorded verifier copies are retained separately in `verification_sources/`; the actor and runner snapshots remain unchanged.
