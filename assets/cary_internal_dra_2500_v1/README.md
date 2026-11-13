# Cary internal DRA 2500, legacy 0010081100

This original model follows the manufacturer-authored Cary WinUV manual,
including the black sphere/detector housing, rear optics cover, removable
clocked sphere cap, spring sample clamp and separate PTFE reference plate.
It is the internal accessory with a 110 mm cavity and 16 mm reflectance port.
The source envelope is 140 × 340 × 200 mm and the unpacked mass is 5 kg.

The 4 mm PTFE sphere coating, 19 × 17 mm transmission opening, 11 × 13 mm
reference-beam opening and 44.45 mm reference disk with 6 mm PTFE depth are
source dimensions. Local positions, wall thicknesses, cap carrier, clamp and
spring geometry are inferred. The S/D cap markings represent the manual's
two configurations; the static reconstruction does not qualify optical angles
or a cap-retention mechanism.

[sources.json](sources.json) records the primary manual, its byte identity,
visual reference review and variant choice. Later accessory product tables
and external 150 mm spheres are kept separate. The required legacy extended
compartment is 154 × 212 × 170 mm internally and adds approximately 180 mm
to the instrument depth. Its removable/hinged extension cover is distinct
from the instrument's sliding lid.

The detector interface is described by the manual as a 15-pin D-range
connector with two high-voltage pins. Exact contact layout and mating
dimensions remain unresolved, so the model retains a labeled connector
envelope without fabricated contacts. The retained cable segment is visual
context, not a complete cable manipulation model.

The module's 5 kg source mass exceeds the current Panda's 3 kg payload.
[interfaces.json](interfaces.json) requires a suitably rated handler or a
physically modeled support assist. Its mass must not be reduced to obtain a
successful simulated lift. The commercial module and reference disk remain
separately identified parts; static checks supply no robot-execution credit.

Generated Blender/GLB assets and renders are original. Source documents and
photos are referenced rather than redistributed or applied as textures.
The packed label font license is in [FONT_LICENSE.txt](FONT_LICENSE.txt).

To rebuild, install [requirements.txt](requirements.txt) in a separate Python
environment, run `python prepare_sphere.py`, then `blender -b --python build.py`
with Blender 2.82 and `python validate.py`. The sphere preparation uses robust
solid booleans and a topology-preserving 1 µm simplification bound before GLB
export. The generated mesh file pins its generator and package versions.
