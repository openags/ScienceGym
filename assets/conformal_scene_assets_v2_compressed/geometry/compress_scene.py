"""Official Blender compressed serialization. Geometry and scene are unchanged."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/conformal_lab.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/conformal_lab.blend'),compress=True)
print('COMPRESSED_SAVE_COMPLETE')
