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
actual G1 button contact, accessory installation, sample/tool dynamics and the
full procedure remain to implement and validate. Qualified paper branches and
campaigns remain **zero**.

Technical references: [MuJoCo collision computation](https://mujoco.readthedocs.io/en/latest/computation/)
and [MeshPy/TetGen interface](https://documen.tician.de/meshpy/tri-tet.html).
MeshPy's wrapper is MIT-licensed; its bundled TetGen has separate
[licensing terms](https://documen.tician.de/meshpy/faq.html). This repository
uses the installed offline mesher and does not vendor its implementation.
