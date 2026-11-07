# PIKE IntegratIR legacy DLaTGS

This original reconstruction follows figure 1 of PIKE's January 2012 manual,
PN 350-048400-01. It preserves the legacy black enclosure, two metal top panels,
raised detector housing, upper sample port, front sample/reference knob and
purge connection. The 76.2 mm internal sphere and 18 mm sample port are explicit
manufacturer dimensions. The selected 175 × 195 × 165 mm main envelope and
local mechanical dimensions are inferred from the photograph and bay fit.

The paper does not identify the detector or product generation. Selecting this
room-temperature DLaTGS version is a reconstruction choice. Its geometry and
procedure must remain separate from later gold-front 12-degree spheres and
MCT versions with a liquid-nitrogen Dewar.

The gold reference, protective cap and optional window plate are separate named
parts. The top detector connector is represented by an open housing: its exact
contact count, connector family and wiring remain unresolved. No cable-mating
or electrical credit is supplied by that visual envelope.

[sources.json](sources.json) records provenance and missing dimensions.
[interfaces.json](interfaces.json) records the manipulation surfaces and
qualification limits. Build with Blender 2.82 using `blender -b --python
build.py`, then run `python validate.py` in the tested ScienceGym environment.
The GLB, native Blender file and four rendered views are original generated
assets; referenced manufacturer photographs are not redistributed or used as
textures. The packed font license is in [FONT_LICENSE.txt](FONT_LICENSE.txt).
