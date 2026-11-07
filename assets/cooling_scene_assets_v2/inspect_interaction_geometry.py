"""Blender ray checks for authored openings; no physical contact certification."""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'geometry/cooling_pilot.blend'))
deps=bpy.context.evaluated_depsgraph_get()
checks=[]
for n in range(1,53):
    stem='MCC_USB_TC__pin_%02d'%n
    terminal=bpy.data.objects[stem].evaluated_get(deps)
    hit,point,normal,index=terminal.ray_cast(Vector((0,-.01,-.001)),Vector((0,1,0)),distance=.02)
    if hit:raise ValueError('Conductor-entry axis is blocked in '+stem)
    screw=bpy.data.objects[stem+'_screw'].evaluated_get(deps)
    hit,point,normal,index=screw.ray_cast(Vector((0,0,.005)),Vector((0,0,-1)),distance=.01)
    if not hit or point.z>=.0002:raise ValueError('Driver slot is missing in '+stem)
    checks.append(dict(terminal=stem,wire_entry_axis_open=True,driver_slot_recess_m=round(.00035-point.z,8)))
shell=bpy.data.objects['MCC_USB_TC__USB_B'].evaluated_get(deps)
hit,point,normal,index=shell.ray_cast(Vector((.08,0,.019)),Vector((-1,0,0)),distance=.03)
if hit:raise ValueError('USB Type-B shell opening is filled')
receipt=dict(kind='authored_geometry_ray_checks',native_sha256=hashlib.sha256((ROOT/'geometry/cooling_pilot.blend').read_bytes()).hexdigest(),
    terminal_checks=checks,usb_shell_open=True,passed=True,
    scope='Checks central rays through authored cavities and recesses only. Not clearance metrology, robot insertion, force/contact physics or electrical qualification.')
(ROOT/'geometry/interaction_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('INTERACTION_GEOMETRY_CHECKS_PASSED',len(checks),'terminals and one USB shell')
