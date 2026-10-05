"""Keep persistent paths relative; save native compression without changing geometry."""
import bpy,pathlib
p=pathlib.Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(p/'qha_lab.blend'))
bpy.context.scene.render.filepath='//../previews/preview_01_overview.png'
for screen in bpy.data.screens:
 for area in screen.areas:
  for space in area.spaces:
   if space.type=='FILE_BROWSER' and space.params:
    space.params.directory=b'//'
for img in bpy.data.images:
 if img.filepath and not img.packed_file: raise RuntimeError('Unexpected external image')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'qha_lab.blend'),compress=True)

# RNA directory assignment alone does not clear post-NUL bytes. Finish at SDNA level.
import subprocess,shutil
subprocess.run([shutil.which('python3'),str(p/'finalize_native_buffers.py')],check=True)
