"""Render native scene with available CPU backend; no denoiser dependency."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
S=bpy.context.scene
portable=[o for o in bpy.data.objects if '.portable' in o.name]
print('PORTABLE_DUPLICATE_CLEANUP',len(portable))
for o in portable:bpy.data.objects.remove(o,do_unlink=True)
S.cycles.use_denoising=False;S.cycles.samples=96;S.render.use_stamp=False
receipt={'renderer':'Blender Cycles','blender_version':bpy.app.version_string,'device':'CPU','samples':96,'denoising':False,'source_pixels_used':False,'images':[]}
for name in ['overview','handling','metrology']:
 S.camera=bpy.data.objects['CAM.'+name];S.render.filepath=str(P/'evidence'/f'{name}.png');bpy.ops.render.render(write_still=True)
 f=P/'evidence'/f'{name}.png';receipt['images'].append({'path':f'evidence/{name}.png','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'camera':S.camera.name,'resolution':[1920,1280],'kind':'actual CPU path-traced static scene; not measured evidence'})
(P/'review/render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
S.camera=bpy.data.objects['CAM.overview'];S.render.filepath='//../evidence/overview.png';bpy.ops.wm.save_as_mainfile(filepath=str(P/'geometry/arcmorph_lab.blend'))
