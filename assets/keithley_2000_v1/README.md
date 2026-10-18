# Keithley 2000

Manufacturer-specific reconstruction of the missing calibration multimeter.
The [source record](sources.json) separates published dimensions and manual
layouts from inferred detail. This asset does not claim to be vendor CAD.

Open [the GLB](geometry/keithley_2000.glb) or [editable Blender file](geometry/keithley_2000.blend).
Review the [front](evidence/front.png), [rear](evidence/rear.png) and
[three-quarter view](evidence/three_quarter.png). The nine banana sockets have
open bores; front controls and rear connectors have separate part identities.
[interfaces.json](interfaces.json) records local entry points and axes.

The published rack envelope is 213 × 370 × 89 mm; the bench envelope with
handle and feet is 238 × 370 × 104 mm. Front and rear feature locations are
scaled from Figures 2-1 and 2-2 in the manufacturer's Model 2000 manual.
They are image-derived estimates. Connector depth, clearance, button travel
and detailed mechanics still need qualification before contact execution.
The screen is shown powered off.

Rebuild with Blender 2.82 using `blender --background --python-exit-code 1
--python build.py`, then run `python validate.py`. `DejaVuSans.ttf` is loaded
from the system font directory. It is converted into geometry in the GLB.
This package is separate from the pinned older scene so rebuilding it cannot
silently alter existing simulation evidence.
