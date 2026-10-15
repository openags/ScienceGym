"""Render isolated inspection groups from the saved native scene."""
import bpy
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VIEWS=[
 ('paired_apparatus',['COOLER_WHITE','COOLER_BLACK'],(.74,-1.15,.85),(0,0,.13),.97),
 ('exploded_stack',['COOLER_EXPLODED'],(1.78,-.78,.65),(1.15,0,.19),.60),
 ('fixed_band',['COOLER_FIXED_BAND'],(2.2,-.7,.6),(1.65,0,.16),.53),
 ('commercial_devices',['KEITHLEY_2425','MCC_USB_TC','THERMO_A25_AC150_HYPOTHESIS'],(.95,-.30,.91),(.13,.93,.32),1.28),
 ('keithley_2425',['KEITHLEY_2425'],(.12,.22,.25),(-.24,.82,.055),.48),
 ('usb_tc',['MCC_USB_TC'],(.26,.40,.27),(.08,.74,.025),.19),
 ('optical_instruments',['AGILENT_CARY_5000','THERMO_NICOLET_6700'],(1.6,.65,1.20),(0,2.05,.18),2.10),
 ('solar_tracker',['EKO_STR_32G'],(1.70,.45,.47),(1.25,1,.14),.49),
]

def render():
    scene=bpy.context.scene;camera=scene.camera
    for name,roots,pos,target,scale in VIEWS:
        for o in scene.objects:
            if o.parent:o.hide_render=o.parent.name not in roots
        camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        scene.render.filepath=str(ROOT/'evidence'/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    for o in scene.objects:
        if o.parent:o.hide_render=False

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'geometry/cooling_pilot.blend'))
    render()
