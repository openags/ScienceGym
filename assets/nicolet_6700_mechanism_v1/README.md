# Nicolet operating-clearance variant

This variant preserves the existing instrument envelope, moving parts, labels,
interfaces and materials. Four stationary meshes receive hinge seats, closure
seams and shallow key wells. The clearances are **inferred reconstruction
parameters**, not measured dimensions or manufacturer CAD.

`build.py` derives the artifact from the existing prepared Nicolet. The receipt
records its source hash and verifies all 189 unchanged part meshes and transforms.
The serialized result is checked at 521 cover angles and 124 key travel states.
The original artifact remains intact; only the FTIR measurement viewer selects
this variant. Whole-room and hand-contact review is separate from this local check.

Upstream references, reconstruction basis and source licenses remain in
`../nicolet_6700_v1/sources.json` and `../nicolet_6700_v1/README.md`.
