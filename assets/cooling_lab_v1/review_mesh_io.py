"""Read authored mesh winding, including negative inner cavity boundaries.

Do not run per-connected-component normal/inversion repair: a sealed hollow
container has a positive exterior and negative interior boundary. Making both
positive silently fills the cavity and doubles occupied volume.
"""
import trimesh
from geometry_tools import ROOT, sha


def load_parts(ref):
    assert sha(ROOT/ref['path'])==ref['sha256'],ref['path']
    scene=trimesh.load(ROOT/ref['path'],force='scene',process=False);parts={}
    for name in scene.graph.nodes_geometry:
        matrix,key=scene.graph[name];mesh=scene.geometry[key].copy()
        mesh.apply_transform(matrix);mesh.merge_vertices(digits_vertex=8)
        assert mesh.is_winding_consistent,'Inconsistent authored winding: '+name
        parts[name]=mesh
    return parts
