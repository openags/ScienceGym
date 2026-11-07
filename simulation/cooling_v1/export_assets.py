"""Convert original GLB triangle meshes to MuJoCo OBJ, without remeshing.

The GLB is Y-up; MuJoCo is Z-up. Root-relative transforms and material colors
are preserved. Visual geometry is deliberately not a convex collision model.
"""
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / 'assets/cooling_scene_assets_v2/geometry/cooling_pilot.glb'


def main():
    raw = SOURCE.read_bytes()
    length, kind = struct.unpack_from('<II', raw, 12)
    doc = json.loads(raw[20:20+length])
    offset = 20 + length
    n, kind = struct.unpack_from('<II', raw, offset)
    binary = raw[offset+8:offset+8+n]
    types = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def array(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype(types[a['componentType']]); width = widths[a['type']]
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = v.get('byteStride', dtype.itemsize * width)
        return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
                          offset=start, strides=(stride, dtype.itemsize)).copy()

    def matrix(node):
        if 'matrix' in node:
            return np.array(node['matrix']).reshape(4, 4).T
        t = np.eye(4)
        t[:3, :3] = Rotation.from_quat(node.get('rotation', [0, 0, 0, 1])).as_matrix() @ np.diag(node.get('scale', [1, 1, 1]))
        t[:3, 3] = node.get('translation', [0, 0, 0])
        return t

    out = HERE / 'geometry'; out.mkdir(exist_ok=True)
    zup = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    parts = []
    original = {p['id']: p for p in json.loads((SOURCE.parent.parent/'parts.json').read_text())['parts']}

    def visit(index, transform, root_name, root_transform):
        node = doc['nodes'][index]; transform = transform @ matrix(node)
        name = node.get('name', '')
        if name and '__' not in name:
            root_name, root_transform = name, transform.copy()
        if 'mesh' in node and name in original:
            relative = np.linalg.inv(root_transform) @ transform
            origin = zup @ relative[:3, 3]
            for k, primitive in enumerate(doc['meshes'][node['mesh']]['primitives']):
                vertices = array(primitive['attributes']['POSITION']) @ relative[:3, :3].T @ zup.T
                faces = array(primitive['indices']).reshape(-1, 3)
                material = doc.get('materials', [{}])[primitive.get('material', 0)]
                rgba = material.get('pbrMetallicRoughness', {}).get('baseColorFactor', [.6, .6, .6, 1])
                filename = f'mesh_{len(parts):04d}.obj'
                lines = ['# Original ScienceGym mesh; root-local Z-up coordinates']
                lines += ['v %.9g %.9g %.9g' % tuple(v) for v in vertices]
                lines += ['f %d %d %d' % tuple(f+1) for f in faces]
                (out/filename).write_text('\n'.join(lines)+'\n')
                parts.append(dict(id=name, root=root_name, file=filename,
                                  file_sha256=hashlib.sha256((out/filename).read_bytes()).hexdigest(),
                                  pos=origin.tolist(), rgba=rgba,
                                  role=original[name]['role'], collision_qualified=False))
        for child in node.get('children', []):
            visit(child, transform, root_name, root_transform)

    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(root, np.eye(4), '', np.eye(4))
    (out/'catalog.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(raw).hexdigest(),
                                                     unit='m', parts=parts), indent=2)+'\n')
    print('Exported original mesh parts:', len(parts), flush=True)


if __name__ == '__main__':
    main()
