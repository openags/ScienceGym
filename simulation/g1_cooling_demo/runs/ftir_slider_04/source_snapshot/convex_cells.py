"""Conforming convex cells for operating clearances in closed source meshes.

TetGen fills the supplied piecewise-linear solid; adjacent tetrahedra are
merged only when their convex hull has the same volume. Unlike a single hull,
this retains holes and hinge/key recesses. This is an offline mesh builder.
"""
from collections import deque

import numpy as np
from scipy.spatial import ConvexHull
import trimesh


def clean(mesh):
    mesh = mesh.copy()
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    # Boolean-exported vents contain collinear T junctions. Split their long
    # triangle edges at existing boundary vertices; do not fill a missing
    # opening or move a vertex. Float32 source coordinates allow 0.1 micrometre
    # point-to-edge disagreement.
    for _ in range(8):
        counts = np.bincount(mesh.edges_unique_inverse)
        boundary = mesh.edges_unique[counts == 1]
        if not len(boundary):
            break
        vertices = np.unique(boundary)
        replacements = {}
        for a, b in boundary:
            start, stop = mesh.vertices[[a, b]]
            edge = stop - start
            fractions = (mesh.vertices[vertices] - start) @ edge / np.dot(edge, edge)
            distance = np.linalg.norm(mesh.vertices[vertices] - start - fractions[:, None] * edge, axis=1)
            inside = (fractions > 1e-6) & (fractions < 1-1e-6) & (distance < 1e-7)
            points = vertices[inside][np.argsort(fractions[inside])]
            if not len(points):
                continue
            face_index = np.flatnonzero(np.any(mesh.faces == a, axis=1) & np.any(mesh.faces == b, axis=1))[0]
            if face_index in replacements:
                continue
            face = mesh.faces[face_index]
            c = next(v for v in face if v not in (a, b))
            chain = [a, *points, b]
            if face[(np.flatnonzero(face == a)[0] + 1) % 3] != b:
                chain.reverse()
            replacements[face_index] = [[x, y, c] for x, y in zip(chain[:-1], chain[1:])]
        if not replacements:
            break
        faces = [f for i, f in enumerate(mesh.faces) if i not in replacements]
        faces.extend(f for group in replacements.values() for f in group)
        mesh.faces = np.asarray(faces)
    mesh.fix_normals()
    return mesh


def decompose(mesh, holes=None):
    from meshpy.tet import MeshInfo, Options, build

    mesh = clean(mesh)
    if not mesh.is_volume:
        raise ValueError('Conforming decomposition requires a closed source solid')
    hull = mesh.convex_hull
    if abs(hull.volume - mesh.volume) <= max(1e-15, mesh.volume * 3e-7):
        return [hull]
    info = MeshInfo()
    info.set_points(mesh.vertices)
    info.set_facets(mesh.faces)
    if holes is not None and len(holes):info.set_holes(holes)
    tet = build(info, options=Options('pYQ'))
    points = np.asarray(tet.points)
    elements = np.asarray(tet.elements)
    volumes = abs(np.linalg.det(points[elements[:, 1:]] - points[elements[:, :1]])) / 6
    if abs(volumes.sum() - mesh.volume) > max(1e-14, mesh.volume * 1e-6):
        raise ValueError('Tetrahedralization changed the source solid volume')
    cells = {i: set(map(int, e)) for i, e in enumerate(elements)}
    volume = dict(enumerate(volumes))
    neighbors = {i: set() for i in cells}
    faces = {}
    for i, e in enumerate(elements):
        for omit in range(4):
            f = tuple(sorted(np.delete(e, omit)))
            if f in faces:
                j = faces.pop(f)
                neighbors[i].add(j)
                neighbors[j].add(i)
            else:
                faces[f] = i
    edges = deque((i, j) for i in cells for j in sorted(neighbors[i]) if i < j)
    while edges:
        i, j = edges.popleft()
        if i not in cells or j not in neighbors[i]:
            continue
        joined = cells[i] | cells[j]
        indices = sorted(joined)
        convex = ConvexHull(points[indices])
        expected = volume[i] + volume[j]
        if abs(convex.volume - expected) > max(1e-15, expected * 3e-7):
            continue
        cells[i] = {indices[k] for k in convex.vertices}
        volume[i] = expected
        adjacent = (neighbors[i] | neighbors[j]) - {i, j}
        for k in adjacent:
            neighbors[k].discard(i)
            neighbors[k].discard(j)
            neighbors[k].add(i)
        neighbors[i] = adjacent
        del cells[j], neighbors[j], volume[j]
        edges.extend((i, k) for k in sorted(adjacent))
    result = [trimesh.convex.convex_hull(points[sorted(v)]) for v in cells.values()]
    if abs(sum(p.volume for p in result) - mesh.volume) > max(1e-14, mesh.volume * 2e-6):
        raise ValueError('Convex merge changed the source solid volume')
    return result
