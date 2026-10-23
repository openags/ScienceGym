"""Metric, Z-up geometry for authored furniture and source-based reconstructions."""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def transform(position=(0, 0, 0), yaw=0):
    out = trimesh.transformations.rotation_matrix(yaw, [0, 0, 1])
    out[:3, 3] = position
    return out


class Geometry:
    def __init__(self):
        self.scene = trimesh.Scene()
        self.parts = []

    def add(self, name, mesh, color, role='structure', metal=0, alpha=255):
        rgba = list(color[:3]) + [alpha]
        mesh.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=str(tuple(rgba)) + '_' + str(metal), baseColorFactor=rgba,
            metallicFactor=metal, roughnessFactor=.43,
            alphaMode='BLEND' if alpha < 255 else 'OPAQUE', doubleSided=False))
        mesh.metadata.update(part_id=name, role=role)
        self.scene.add_geometry(mesh, node_name=name, geom_name=name)
        self.parts.append(dict(id=name, role=role, bounds_m=mesh.bounds.tolist()))
        return mesh

    def box(self, name, size, center, color, role='structure', **kwargs):
        mesh = trimesh.creation.box(size); mesh.apply_translation(center)
        return self.add(name, mesh, color, role, **kwargs)

    def rounded_panel(self, name, width, height, depth, center, radius, color, role='structure'):
        # Convex rounded rectangular panel in XZ, with a small molded edge bevel.
        bevel=min(depth*.2,.0007);vertices=[]
        for y,inset in [(-depth/2,bevel),(-depth/2+bevel,0),(depth/2-bevel,0),(depth/2,bevel)]:
            for sx,sz,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
                for theta in np.radians(np.linspace(start,start+90,13)):
                    vertices.append([sx*(width/2-radius)+(radius-inset)*np.cos(theta),y,sz*(height/2-radius)+(radius-inset)*np.sin(theta)])
        mesh=trimesh.convex.convex_hull(np.array(vertices));mesh.apply_translation(center)
        return self.add(name,mesh,color,role)

    def label(self,name,text,width,height,center,background,foreground):
        # Original typeset identification only; not a copied manufacturer logo.
        from PIL import Image, ImageDraw, ImageFont
        picture=Image.new('RGB',(768,256),tuple(background));draw=ImageDraw.Draw(picture)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',90)
        draw.text((384,128),text,font=font,fill=tuple(foreground),anchor='mm')
        x,y,z=center
        vertices=[[x-width/2,y,z-height/2],[x+width/2,y,z-height/2],[x+width/2,y,z+height/2],[x-width/2,y,z+height/2]]
        mesh=trimesh.Trimesh(vertices=vertices,faces=[[0,1,2],[0,2,3]],process=False)
        self.add(name,mesh,[255,255,255],role='identification_label')
        mesh.visual=trimesh.visual.TextureVisuals(uv=[[0,0],[1,0],[1,1],[0,1]],material=PBRMaterial(baseColorTexture=picture,roughnessFactor=.65,metallicFactor=0))
        return mesh

    def cylinder(self, name, radius, length, center, color, axis=(0, 0, 1), role='structure', **kwargs):
        mesh = trimesh.creation.cylinder(radius, length, sections=48)
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
        mesh.apply_translation(center)
        return self.add(name, mesh, color, role, **kwargs)

    def ring(self, name, inner, outer, length, center, color, axis=(0, 0, 1), role='structure', **kwargs):
        mesh = trimesh.creation.annulus(inner, outer, length, sections=64)
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
        mesh.apply_translation(center)
        return self.add(name, mesh, color, role, **kwargs)

    def profile(self, name, radii_heights, color, axis=(0, 0, 1), position=(0, 0, 0), **kwargs):
        mesh = trimesh.creation.revolve(np.asarray(radii_heights), sections=96)
        mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
        mesh.apply_translation(position)
        return self.add(name, mesh, color, **kwargs)

    def tube(self, name, points, radius, color):
        for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
            a, b = np.asarray(a), np.asarray(b); vector = b - a
            self.cylinder(name + '_' + str(i), radius, np.linalg.norm(vector), (a + b) / 2,
                          color, axis=vector / np.linalg.norm(vector), role='routed_service')

    def export(self, stem):
        path = HERE / 'geometry' / (stem + '.glb'); path.parent.mkdir(exist_ok=True)
        path.write_bytes(self.scene.export(file_type='glb'))
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path), parts=len(self.parts),
                    bounds_m=self.scene.bounds.tolist(), axes='+Z up; SI metres',
                    part_records=self.parts)


def imported_scene(path, *, prefix=None, z_up=False):
    source = trimesh.load(ROOT / path, force='scene')
    result = trimesh.Scene()
    conversion = np.eye(4) if z_up else trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    for node in source.graph.nodes_geometry:
        if prefix and not node.startswith(prefix): continue
        matrix, name = source.graph[node]
        mesh = source.geometry[name].copy(); mesh.apply_transform(conversion @ matrix)
        result.add_geometry(mesh, node_name=node, geom_name=node)
    if not result.geometry: raise ValueError('No geometry for ' + str(prefix))
    return result
