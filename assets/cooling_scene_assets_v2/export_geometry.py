"""Export all authored parts, including Blender curves and lettering, to GLB."""
import bpy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from compact_glb import compact

def export():
    bpy.ops.object.select_all(action='DESELECT')
    curves=[o for o in bpy.context.scene.objects if o.parent and o.type in ('CURVE','FONT')]
    if curves:
        for o in curves:o.select_set(True)
        bpy.context.view_layer.objects.active=curves[0]
        bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.get('part_id') and o.parent:
            o.select_set(True);o.parent.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'geometry/cooling_pilot.glb'),export_format='GLB',export_selected=True,export_extras=True,export_apply=True)
    print('GLB_COMPACTION',compact(ROOT/'geometry/cooling_pilot.glb'))

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'geometry/cooling_pilot.blend'))
    export()
