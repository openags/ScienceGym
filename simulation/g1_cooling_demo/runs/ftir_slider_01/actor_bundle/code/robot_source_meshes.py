"""Robot-local source triangles from the actor's public robot model.

This reads visual triangle arrays, not the simulator's contact list, collision
approximations, laboratory scene or handled-object state. Mesh centering and
principal-axis transforms introduced by MuJoCo are undone through each geom's
compiled body-local pose.
"""
from collections import defaultdict

import mujoco
import numpy as np
import trimesh


def robot_source_meshes(model):
    root = model.body('pelvis').id
    parts = defaultdict(list)
    for gid in range(model.ngeom):
        bid = int(model.geom_bodyid[gid])
        ancestor = bid
        while ancestor and ancestor != root:
            ancestor = int(model.body_parentid[ancestor])
        if ancestor != root or model.geom_group[gid] != 2:
            continue
        if model.geom_type[gid] != mujoco.mjtGeom.mjGEOM_MESH:
            raise ValueError('Expected original robot visual triangle mesh')
        mid = int(model.geom_dataid[gid])
        va, vn = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
        fa, fn = model.mesh_faceadr[mid], model.mesh_facenum[mid]
        rotation = np.empty(9)
        mujoco.mju_quat2Mat(rotation, model.geom_quat[gid])
        vertices = (model.mesh_vert[va:va+vn].astype(float)
                    @ rotation.reshape(3,3).T + model.geom_pos[gid])
        parts[model.body(bid).name].append(trimesh.Trimesh(
            vertices=vertices, faces=model.mesh_face[fa:fa+fn].copy(), process=False))
    if not parts:
        raise ValueError('No robot source geometry in the supplied model')
    return {name:trimesh.util.concatenate(pieces) for name,pieces in parts.items()}


def source_adjacency(model, body_names):
    """Same assembly/one joint neighbors, matching source URDF review policy."""
    graph = defaultdict(list)
    for bid in range(1,model.nbody):
        parent = int(model.body_parentid[bid])
        weight = int(model.body_jntnum[bid] > 0)
        graph[parent].append((bid,weight))
        graph[bid].append((parent,weight))
    ids = {model.body(name).id:name for name in body_names}
    adjacent = set()
    for start,name in ids.items():
        pending = [(start,-1,0)]
        while pending:
            bid,parent,distance = pending.pop()
            if distance > 1:
                continue
            if bid in ids:
                adjacent.add(tuple(sorted([name,ids[bid]])))
            pending.extend((child,bid,distance+weight)
                           for child,weight in graph[bid] if child != parent)
    return adjacent
