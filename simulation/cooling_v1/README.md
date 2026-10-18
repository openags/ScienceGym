# Cooling manipulation: contact execution workbench

**The whole-paper simulation is unfinished.** This directory adds real MuJoCo
contact execution for four isolated fixtures. It does not supply a continuous
implementation of the 200 manipulation definitions or all 11 paper branches.
The full-campaign gate rejects that claim explicitly.

Open [index.html](index.html) for recorded physics, event seeking, regression
results and the complete source-step coverage table. Videos come from integrated
robot/object states. They are not keyframed robot animations. Each workcell resets
independently; combining its video with another does not establish continuity.

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
resolves them into hash-verified MuJoCo virtual files. The HTML/video viewer can
be opened offline without Python.

Each run preserves a result record, exact input hashes and a 50 Hz state/control
trace. Rendered runs additionally preserve a video and its 10 Hz replay states.
`evaluate.py` checks final goals independently of the command executor's success
messages. Fault tests exercise an open gripper, missing support, blocked button,
wrong bore, obstructed door and untouched initial state. Initial-joint perturbation
seeds are controller tests, not independent scientific experiments or material
robustness measurements. Arm contact checks are sampled, not a proof that every
possible collision is excluded.

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
