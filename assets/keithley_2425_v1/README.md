# Keithley 2425 source meter

Original metric reconstruction of the paper's source meter. The 2425
specification supplies the 238 × 370 × 104 mm bench envelope. The model-specific
service manual supplies the front identity, 125 V differential markings and
jack colors. The series user manual supplies the control and connector layout;
its generic illustration is explicitly distinguished from model-specific facts
in [sources.json](sources.json).

The asset has 236 inspectable meshes and 48 interfaces, including four front
force/sense sockets and six rear measurement/guard sockets. Banana bores are
open geometry. The guards are separate interfaces, not additional heater
force/sense terminals. The display is off.

`build.py` generates the Blender source, GLB, part/interface inventories and
three rendered views. Run it with Blender 2.82 or compatible Blender Python,
then run `python validate.py` with NumPy and trimesh. Validation reads the
exported GLB and checks its envelope, part identities and all ten socket bores.

Button travel, engagement depths, wall thickness, materials and connector
cavity details are inferred. Internal electronics, fan and ventilation
topology remain outside the model. Static geometry checks do not qualify a
physical connection, electrical behavior or complete equipment fidelity.
