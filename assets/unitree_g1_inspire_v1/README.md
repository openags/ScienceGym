# G1 29DoF rev 1.0 + Inspire FTP integration

The complete official source model is placed in the laboratory review. Its
source dimensions and integrated wrist transforms are preserved. This package
provides geometry, articulation and bounded physics checks; no standing,
grasping, sensor-only controller or manipulation sequence is qualified.

- `SOURCE.json` and `VERIFICATION.json`: pinned official URDF, 93 meshes,
  licenses, source hashes, limits/inertial audit and unscaled visual export.
- `kinematics.py` / `kinematics.json`: source-frame tree including 12 finger
  mimic relations. The 53 movable joints have 41 independent coordinates:
  29 body joints and six drivers per hand.
- `simulation/robot.xml`: MuJoCo 3.16 floating-root model with gravity enabled,
  source inertials and joint limits, torque interfaces and joint observations.
  Damping, armature, friction and solver parameters are provisional. Source
  velocity limits are recorded, not enforced by this torque interface.
- `integration.json`: source/MJCF agreement at five hand poses, mimic residuals,
  100 ms zero-torque numerical smoke and a zero-pose penetration regression.
  An unactuated model dropping under gravity is not a standing test.
- `collision_baseline.json` and `simulation/initial_convex_hull_robot.xml`:
  retained original single-hull baseline. Convexification filled palm concavity,
  producing up to 8.61 mm penetration against the thumb at zero angles.
- `collision.json` / `collision_components/`: source-connected-component palm
  decomposition using [CoACD](https://github.com/SarahWeiii/CoACD), 530 left and
  553 right convex pieces. Original visual geometry is unchanged. The final
  zero pose has no penetration exceeding 0.5 mm. The requested decomposition
  threshold is **not a global accuracy guarantee**: the per-component hull cap
  was reached; warnings are retained in `collision_components_build.log`.
  Small source components and other links still use convex hulls. Contact over
  the complete operating range and with objects remains unqualified.
- `collision_refinements/thumb_2_v1/`: an optional runtime replacement for
  the two filled thumb-2 hulls, with 128 source-derived convex pieces per hand.
  The original single hull has about 3.82 times the source solid volume.
  This refinement preserves visuals, inertias, joint limits and collision
  filters. It removes the false initial palm/thumb contact in the FTIR press
  setup. It is still approximate: sampled outward excess is up to 1.12 mm,
  and sampled missing surface distance up to 0.228 mm. Both 128-piece caps
  were reached; the requested 0.1 mm metric is not an achieved global bound.
  The zero-thumb pose still has small false contacts with the approximate
  palm geometry. See the package's correspondence reports and the FTIR run
  contact reviews; full-range hand contact qualification remains open.
- `space.json`: 129 restricted static source-kinematic poses, official wrist
  transforms and a conservative hand-chain radius. The 0.60 m body/hand radius,
  0.10 m route margin and 1.43 m height allowance exclude cameras and dynamic
  loads. A reserved tray envelope does not establish a grasp or carrying skill.
- `../cooling_lab_v1/workspace_checks.json`: 47 separate palm-position access
  points with recorded base/joint coordinates, external box conflicts and
  provisional self-contact checks at a 0.5 mm penetration threshold.
  Position-only IK omits palm orientation, target-instrument internals, balance,
  exact contact qualification, simultaneous two-hand coordination and entry trajectories.
  The current revision has 44 candidates and three unresolved points: Cary
  extension base, bath front and bath front drain. A retained negative fixture
  replays an observed arm-through-torso solution; position error and external
  box checks alone must never qualify it.

Use `assets/cooling_lab_v1/requirements.txt`. The normal laboratory rebuild
checks the saved collision hashes and does not rerun expensive decomposition:

```sh
OPENBLAS_NUM_THREADS=1 python assets/cooling_lab_v1/rebuild_review.py
```

To deliberately regenerate the palm collision approximation first:

```sh
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 python assets/unitree_g1_inspire_v1/build_collision.py
```

Inspect the source model at `viewer/robot_resource_review_v1/index.html` and
the placed, articulated model at `viewer/lab_review_v1/index.html`. The latter
offers one static posture per access point. Neither viewer grants acceptance;
the owner asset/scene gate remains pending.
