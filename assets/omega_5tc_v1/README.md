# Omega 5TC-TT-K-36-36 visual asset

The source catalogue constrains Type K, 36 AWG / 0.13 mm conductors, PFA
insulation and nominal 1 m length. Its ordering note maps the suffix `36` to
1 m; the model does not interpret it as exactly 36 inches.

Eight separately identified loose probes are selected for the current scene.
The source supplies packs of five, so this selection corresponds to two packs
with two spares not placed. This does not establish complete campaign allocation.

The author-selected rest shape has three coil turns and a 1 m nominal bundle
centerline. Jacket dimensions, wire split/strip lengths, weld shape and finish
are estimates. Visible conductors retain 0.13 mm diameter. Hidden conductor
interiors are omitted; this is static visual geometry, without a flexible cable,
electrical termination, strain-relief or temperature observation model.

```bash
OPENBLAS_NUM_THREADS=1 python assets/omega_5tc_v1/build.py
OPENBLAS_NUM_THREADS=1 python assets/omega_5tc_v1/validate.py
```

The source is linked and hashed in `sources.json`; no catalogue image is
redistributed. Validation checks input identity, selected metric length,
conductor dimensions, separate endpoint parts and closed finite part meshes.
