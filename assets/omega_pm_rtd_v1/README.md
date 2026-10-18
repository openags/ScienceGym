# Omega immersion RTD

This asset reconstructs the paper's **P-M-A-1/4-3-1/2-PS-12** from the
[manufacturer's PM ordering table](https://assets.omega.com/pdf/test-and-measurement-equipment/temperature/sensors/rtds/P-Ultra_RTD.pdf).
The successive `3` and `1/2` fields mean a **76.2 mm probe** and **1/2 NPT
mounting thread**. The sheath diameter is **6.35 mm** and cable length **3.6576 m**.

[sources.json](sources.json) distinguishes those documented dimensions from
the inferred fitting envelope, hex size, cable diameter and lead breakout.
No exact vendor CAD or dimensional drawing of this fitting was found. Its
thread is visual geometry and has not been qualified for threaded insertion.

The editable Blender file retains the cable paths; the GLB explicitly meshes
all 16 parts, including four stripped leads. The cable in these files is a
rest shape. The MuJoCo RTD workcell supplies its own articulated cable model.
[geometry_checks.json](geometry_checks.json) measures the exported sheath and
checks exported-part completeness, cable length and separate coil turns.

Build with Blender 2.82+ and `--python-exit-code 1 --python build.py`. Run
`python validate.py` with NumPy and trimesh. Original reconstruction code and
geometry follow the repository license; manufacturer photographs are not
embedded.
