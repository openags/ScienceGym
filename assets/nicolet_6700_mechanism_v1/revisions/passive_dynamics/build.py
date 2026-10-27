"""Infer a sliding-grip relief from the existing 104 mm door travel.

The initial cover frame blocked its own grip over the final 18 mm of travel.
Remove only that local interference. This is an inferred mechanical detail,
not a manufacturer drawing or measured instrument revision. The already
published movie continues using the parent geometry.
"""
import copy
import hashlib
import json
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
parent = ROOT/'assets/nicolet_6700_mechanism_v1/geometry/nicolet_6700_mechanism.glb'
scene = trimesh.load(parent, force='scene', process=False)
transform, geometry = scene.graph['sample_bay_lid']
original = scene.geometry[geometry]
mesh = original.copy(); mesh.apply_transform(transform)
mesh.merge_vertices(merge_tex=True, merge_norm=True)
mesh.update_faces(mesh.nondegenerate_faces()); mesh.remove_unreferenced_vertices(); mesh.fix_normals()
assert mesh.is_volume
asset = next(a for a in json.loads((ROOT/'assets/cooling_lab_v1/scene.json').read_text())['assets'] if a['id']=='nicolet')
normal = asset['normalization_matrix']
cut = trimesh.creation.box(extents=[.098, .020, .010])
cut.apply_translation([-.011, -.1485+normal[1][3], .251+normal[2][3]])
result = trimesh.boolean.difference([mesh, cut], engine='manifold')
assert result.is_volume
volume_removed = float(mesh.volume-result.volume)
result.apply_transform(trimesh.transformations.inverse_matrix(transform))
result.visual = trimesh.visual.texture.TextureVisuals(material=copy.deepcopy(original.visual.material))
scene.geometry[geometry] = result
(HERE/'geometry').mkdir(exist_ok=True)
path = HERE/'geometry/nicolet_passive_dynamics.glb'; path.write_bytes(scene.export(file_type='glb'))
actual = trimesh.load(path, force='scene', process=False)
before = trimesh.load(parent, force='scene', process=False)
unchanged = []
for name in before.graph.nodes_geometry:
    if name == 'sample_bay_lid': continue
    ta, ka = before.graph[name]; tb, kb = actual.graph[name]
    import numpy as np
    assert np.array_equal(ta, tb) and np.array_equal(before.geometry[ka].vertices, actual.geometry[kb].vertices)
    assert np.array_equal(before.geometry[ka].faces, actual.geometry[kb].faces)
    unchanged.append(name)
receipt = dict(scope=__doc__, source=str(parent.relative_to(ROOT)),
    source_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),
    builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    geometry_override=dict(asset='nicolet', path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
    changed_parts=['sample_bay_lid'], unchanged_parts=unchanged, removed_volume_m3=volume_removed,
    inferred_dimensions=True, manufacturer_cad=False, source_correspondence_passed=True,
    contact_review='Performed separately on the compiled laboratory physics plant; no success implied by this build.')
(HERE/'revision.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(dict(unchanged_parts=len(unchanged), removed_volume_m3=volume_removed)))
