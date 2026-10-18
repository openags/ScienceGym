# Cooling manipulation: contact execution workbench

**The whole-paper simulation is unfinished: 0 of 11 complete branches accepted.**
The physical workbench now includes a continuous six-layer assembly and return,
a deformable two-film cover, a full-length cabled commercial RTD, and a
model-specific Keithley 2000 button, installed reflector carriage and a cabled
Keithley 2425 plug interface. Each record has its own declared scope;
acceptance of these records does not discharge the complete 200-step definition
set or their 1,317 scheduled manipulation occurrences.

Open [sample.html](sample.html) for recorded videos, acceptance status, event seeking, searchable
paper steps and the five commercial assets. Serve the repository root with
`python simulation/cooling_v1/serve.py`, then visit
`http://localhost:8768/simulation/cooling_v1/sample.html`.
[index.html](index.html) retains the original four fixture demonstrations.
Videos replay recorded robot/object states. Separate workcell records do not
establish continuity between their respective scenes.

| Physical record | Simulation duration | Independent evidence |
| --- | ---: | --- |
| Six rigid layers, assembly and reverse return | 378.198 s | [Three seeds and fault checks](CONTINUOUS_VERIFICATION.json) |
| Two prebonded flexible cover sheets, placement and recovery — rejected after geometric audit | 72.866 s | [Updated cover verification](COVER_VERIFICATION.json), [film/solid intersections](runs/cover/film_geometry_verification.json) |
| Omega P-M RTD, 3.6576 m attached lead, insertion and recovery | 62.920 s | [Nominal trace verification](runs/rtd/verification.json), [perturbed initial arm state](runs/rtd_tests/seed_1/verification.json) |
| Installed reflector carriage, 241 release/slide/lock cycles | 1690.010 s | [495 trace checks](runs/reflector/verification.json), [mechanism faults and load tests](REFLECTOR_VERIFICATION.json) |
| Selected cabled source-meter plug, insertion and return | 61.321 s | [Contact verification](runs/connector/verification.json), [blocked bore](runs/connector_tests/blocked_bore/verification.json), [missing spring](runs/connector_tests/missing_spring/verification.json) |
| Keithley 2000 physical four-wire resistance button | 16.384 s | [Button verification](DMM_VERIFICATION.json) |

The cover's earlier force/position checks missed film triangles crossing the PE
tube wall. An independent triangle/box audit now rejects that record; the
original execution and [earlier receipt](verification_history/cover_before_geometric_audit.json)
remain available. The replacement model must pass this geometry check as well
as load, strain and manipulation checks before the cover can be accepted again.

The integrated candidate uses exact eight-corner meshes for the same tube-wall
cuboids. This exercises the general convex-element collision path: a regression
demonstrates a triangle/box crossing missed by the primitive path in
[MuJoCo 3.16.0](https://github.com/google-deepmind/mujoco/blob/3.16.0/src/engine/engine_collision_flex.c).
Its [continuum support checks](continuum_membrane_tests.json) include 16/50 µm
films, time-step and mesh refinement, and missing-sheet counterexamples. These
static checks do not accept the full robot episode. Historical source versions
needed to reproduce earlier receipts are retained by their SHA-256 identities.
The selected 1 ms model also requires each solver step to converge before its
3,200-iteration limit. All seven static cases pass without exhausting their
limits; half-step, denser mesh and doubled solver-cap comparisons retain the
same 0.3 mm position and 0.02 N support-load tolerances. An exhausted solver
step or numerical warning now stops the robot executor and rejects its record.

Reflector playback contains every recorded adjustment in eight continuous
chapters. Its clock and event links use global simulation time. The local
server implements byte ranges so a browser can seek across the complete
record. Solar-time waits are external process intervals; the 28-minute robot
episode does not establish four-hour mechanical stability. A separate test
checks 60 seconds of retention after a 1 N shear load and slip under a 5 N
overload. The track and disk start mounted.

The RTD trace uses a stiff edge-length string approximation. Every saved edge
stays within 0.21% of its rest length in both accepted runs; bending and torsion
are omitted. The elastic-rod model remains a separate engineering comparison.
The failed small-bore trial first hit an unrelated cable/hand collision and is
retained as an inconclusive fault attempt, not an accepted bore-rejection test.
Neither accepted RTD record includes bath placement or four-wire connections.

[asset_inspector.html](asset_inspector.html) exposes the Keithley 2000, Omega
P-M RTD, Omega KHR-2/2-P, Keithley 2425 and MCC USB-TC meshes, dimensions,
interfaces and source records. The USB-TC has 52 separately numbered terminal
passages and slotted screw heads. Its static clearance checks do not establish
wire retention, screw operation or thermocouple calibration.
These are manufacturer-informed reconstructions, with inferred details labeled
per part. They are not vendor CAD or measured hardware qualifications.

The Panda is pinned to an upstream MuJoCo Menagerie commit, with its source
license and file hashes in [robot_source.json](robot_source.json). The arm uses
joint actuators with source torque limits. No grasp weld, mocap object transport,
or live object-position assignment is used. The controller uses privileged
simulator state, including the observed object-to-hand transform. This is not a
vision policy or a demonstration of learned generalization.

The workcells exercise rigid-layer stacking and button actuation; a rigid probe
insert/withdraw sequence; lid placement/removal; and supported hinged access.
Task-authored fixtures differ from the original equipment. The complete
[physics scope](PHYSICS_SCOPE.json) states mass/friction choices, temporary
carriers, fixture geometry and excluded deformation/material processes.
Original USB-TC and A25 meshes are visual context only. The converted 724 mesh
parts are not 724 physically qualified assets.

## Reproduce

Tested with Python 3.12, MuJoCo 3.16.0 and EGL on Linux. Use a separate virtual
environment. `requirements-tested.txt` records the tested package versions;
`requirements.txt` supplies the runtime dependency constraints.

```bash
python -m pip install -r simulation/cooling_v1/requirements-tested.txt
python simulation/cooling_v1/bootstrap.py
python simulation/cooling_v1/export_assets.py
MUJOCO_GL=egl python simulation/cooling_v1/run_contact.py --scene assembly --render --out runs/assembly
MUJOCO_GL=egl python simulation/cooling_v1/run_contact.py --scene probe --render --out runs/probe
MUJOCO_GL=egl python simulation/cooling_v1/run_contact.py --scene lid --render --out runs/lid
MUJOCO_GL=egl python simulation/cooling_v1/run_contact.py --scene door --render --out runs/door
python simulation/cooling_v1/test_physics.py
python simulation/cooling_v1/campaign.py
python simulation/cooling_v1/build_viewer.py
```

Bootstrap downloads the pinned robot under `/tmp/sciencegym-robot-cache`, or the
directory specified by `SCIENCEGYM_ROBOT_CACHE`. It verifies cached files against
the recorded hashes. Export reconstructs the ignored OBJ cache from the existing
original GLB, preserving root-relative metre coordinates and source part IDs.
The resulting workcell XML uses portable logical asset paths. `load_model.py`
resolves them into hash-verified MuJoCo virtual files. The HTML/video viewer runs without external web services through the included
local HTTP server.

Each run preserves a result record, exact input hashes and a state/control trace
at its declared sampling cadence. New cabled RTD runs also archive their source
files, so later controller changes do not invalidate an earlier source snapshot.
`evaluate.py` checks final goals independently of the command executor's success
messages. Fault tests exercise an open gripper, missing support, blocked button,
wrong bore, obstructed door and untouched initial state. Initial-joint perturbation
seeds are controller tests, not independent scientific experiments or material
robustness measurements. Arm contact checks are sampled, not a proof that every
possible collision is excluded.

To reproduce the accepted cabled RTD model, run:

```bash
python simulation/cooling_v1/run_rtd.py --flex-cable --out runs/rtd_debug/reproduction
python simulation/cooling_v1/verify_rtd.py simulation/cooling_v1/runs/rtd_debug/reproduction
python simulation/cooling_v1/render_device_trace.py simulation/cooling_v1/runs/rtd_debug/reproduction
```

Cover and connector traces are stored as lossless shards; their viewer links
open the archive manifests. Restore them only when a tool requires a single NPZ.

Large traces can be packaged with `trace_store.py RUN_DIRECTORY` into SHA-256
checked binary shards. `trace_store.py RUN_DIRECTORY --restore` reconstructs
the exact original NPZ after a checkout. Packaging never drops frames or changes
recorded precision. Verifiers using `load_trace` read either representation.

The connector record uses a selected four-leaf passive contact model and a
0.6 m lead with no bending/torsion. The pin reaches 9.864 mm insertion depth
and remains supported after the robot opens its hand. A 5 N socket-load guard
stops a blocked bore before adjacent-socket contact. Removing the passive
springs causes misalignment and excessive load during release, and is rejected.
These observations establish neither electrical continuity nor a heater circuit.

## Whole-paper acceptance

```bash
python simulation/cooling_v1/campaign.py --check
```

This command currently returns exit code 2. [campaign_coverage.json](campaign_coverage.json)
enumerates every required definition and branch, their geometry/interface gaps,
and related fixture tests without giving the latter full-step credit. The
remaining implementation includes per-occurrence action/object/tool bindings,
all missing manipulation assets and interfaces, continuous state between
stations and branches, flexible materials/wires or defensible task-specific
substitutes, instrument-specific access and controls, and observation/recovery
logic for each complete operation. Existing paper and equipment acceptance
records remain unchanged.
