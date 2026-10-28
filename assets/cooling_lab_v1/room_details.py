"""Original construction and finish details for authored lab furniture.

Finish colours/roughness are design selections, not measured BRDFs or supplier
certifications. Commercial device imports retain their source materials.
"""
import itertools
import numpy as np
import trimesh
from PIL import Image, ImageFilter
from trimesh.visual.material import PBRMaterial
from geometry_tools import Geometry


class LaboratoryGeometry(Geometry):
    def __init__(self):
        super().__init__()
        self.finishes = {}
        rng = np.random.default_rng(5001)
        for name, rough, metal, amplitude in [('paint', .69, 0, .12),
                ('resin', .46, 0, .16), ('rubber', .88, 0, .20),
                ('steel', .29, .88, .10), ('wall', .88, 0, .08)]:
            h = rng.uniform(55, 200, (256, 256)).astype('uint8')
            if name == 'steel':
                h = np.repeat(h[:, :1], 256, axis=1)
            h = np.array(Image.fromarray(h).filter(ImageFilter.GaussianBlur(.7)), dtype=float) / 255
            dy, dx = np.gradient(h)
            normal = np.stack([-dx*amplitude, -dy*amplitude, np.ones_like(h)], axis=2)
            normal /= np.linalg.norm(normal, axis=2, keepdims=True)
            mr = np.empty((256, 256, 3), dtype='uint8')
            mr[:, :, 0] = 255
            mr[:, :, 1] = np.clip((rough+(h-.5)*.07)*255, 0, 255)
            mr[:, :, 2] = round(metal*255)
            self.finishes[name] = (Image.fromarray(((normal*.5+.5)*255).astype('uint8')), Image.fromarray(mr))

    def add(self, name, mesh, color, role='structure', metal=0, alpha=255):
        super().add(name, mesh, color, role, metal, alpha)
        if role == 'identification_label': return mesh
        # The authoring palette is sRGB, whereas glTF baseColorFactor is linear.
        rgb = np.asarray(color[:3], dtype=float)/255
        linear = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
        finish = 'paint'
        if role.startswith('wall') or role == 'ceiling': finish = 'wall'
        if role == 'worktop': finish = 'resin'
        if any(s in name for s in ['_foot_', '_plinth_', 'seal_', 'gasket_']): finish = 'rubber'
        if metal or any(s in name for s in ['_handle_', '_screw_', '_washer_', '_hinge_', '_kickplate', '_duct', '_bolt_']): finish = 'steel'
        if alpha < 255:
            mesh.visual.material = PBRMaterial(baseColorFactor=[*linear, alpha/255],
                metallicFactor=0, roughnessFactor=.10, alphaMode='BLEND')
            return mesh
        # Face-local metric UVs avoid stretched grain on the thin panel edges.
        mesh.unmerge_vertices()
        normals = np.repeat(mesh.face_normals, 3, axis=0)
        dominant = np.argmax(np.abs(normals), axis=1)
        uv = mesh.vertices[:, :2].copy()
        uv[dominant == 0] = mesh.vertices[dominant == 0][:, [1, 2]]
        uv[dominant == 1] = mesh.vertices[dominant == 1][:, [0, 2]]
        normal, mr = self.finishes[finish]
        mesh.visual = trimesh.visual.TextureVisuals(uv=uv/.20, material=PBRMaterial(
            name='authored_'+finish, baseColorFactor=[*linear, 1.0],
            normalTexture=normal, metallicRoughnessTexture=mr,
            roughnessFactor=1, metallicFactor=1))
        mesh.metadata['finish_basis'] = 'Authored '+finish+' finish; visual parameters unmeasured'
        return mesh

    def box(self, name, size, center, color, role='structure', **kwargs):
        # Small machined/folded edge breaks; unchanged external dimensions.
        bevel = 0 if role in ['floor', 'wall_lower', 'wall_upper', 'window', 'ceiling', 'ceiling_fixture', 'service_raceway'] else min(.0015, min(size)*.12)
        if role == 'worktop': bevel = .002
        if not bevel: return super().box(name, size, center, color, role, **kwargs)
        half = np.array(size)/2
        vertices = []
        for signs in itertools.product([-1, 1], repeat=3):
            for axis in range(3):
                point = half-bevel
                point[axis] = half[axis]
                vertices.append(point*np.array(signs))
        mesh = trimesh.convex.convex_hull(np.array(vertices))
        mesh.apply_translation(center)
        return self.add(name, mesh, color, role, **kwargs)

    def screw(self, name, center, radius=.0035, axis=(0,-1,0)):
        self.cylinder(name+'_washer', radius*1.4, .0008, center, [178,184,185], axis=axis, role='fastener', metal=.85)
        tip = np.asarray(center)+np.asarray(axis)*.001
        self.cylinder(name+'_head', radius, .002, tip, [163,171,175], axis=axis, role='fastener', metal=.85)
        # A physical recessed-looking cross, explicitly an authored fastener.
        for i, length in enumerate([(radius*1.3,.0005),(.0005,radius*1.3)]):
            size = [length[0], .0004, length[1]] if abs(axis[1]) else [length[0],length[1],.0004]
            self.box(name+'_drive_'+str(i),size,tip+np.asarray(axis)*.0011,[35,38,40],'fastener')
