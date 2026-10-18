"""Independent triangle/solid checks, separate from MuJoCo contact forces.

The separating-axis test covers triangle interiors as well as vertices. A
positive tolerance shrinks every box face by that amount; it is a declared
numerical allowance, not film thickness or permission to cross a tube wall.
Only the represented collision boxes are assessed, at the supplied state.
"""
import numpy as np
import mujoco


def triangle_box_overlap(triangles, half_size):
    """Closed triangle/AABB intersection in box-local coordinates (SAT)."""
    triangles = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    half_size = np.asarray(half_size, dtype=float)
    hits = np.all((triangles.min(axis=1) <= half_size) &
                  (triangles.max(axis=1) >= -half_size), axis=1)
    candidate = np.flatnonzero(hits)
    if not len(candidate):
        return hits
    tri = triangles[candidate]
    edges = np.roll(tri, -1, axis=1) - tri
    normal = np.cross(edges[:, 0], edges[:, 1])
    axes = np.concatenate([normal[:, None],
        np.cross(edges[:, :, None, :], np.eye(3)[None, None]).reshape(-1, 9, 3)], axis=1)
    projection = np.einsum('nvc,nac->nva', tri, axes)
    radius = np.einsum('nac,c->na', np.abs(axes), half_size)
    separated = (projection.min(axis=1) > radius + 1e-15) | (projection.max(axis=1) < -radius - 1e-15)
    hits[candidate] = ~np.any(separated, axis=1)
    return hits


class FilmSolidAudit:
    def __init__(self, model, geom_names, tolerance_m=.0001):
        if not geom_names:
            raise ValueError('A film audit needs explicit solid surfaces')
        self.tolerance = float(tolerance_m)
        self.geoms = [model.geom(name).id for name in geom_names]
        if any(int(model.geom_type[g]) != 6 for g in self.geoms):
            raise ValueError('FilmSolidAudit currently supports box solids only')
        self.names = [model.geom(g).name for g in self.geoms]
        self.sizes = np.array([model.geom_size[g] - self.tolerance for g in self.geoms])
        if np.any(self.sizes <= 0):
            raise ValueError('Tolerance must be smaller than every box half-size')
        self.triangles = []
        self.flex_names = []
        for f in range(model.nflex):
            if model.flex_dim[f] != 2:
                continue
            start, count = model.flex_elemadr[f], model.flex_elemnum[f]
            self.triangles.append(model.flex_elem[start:start+count*3].reshape(-1, 3) + model.flex_vertadr[f])
            self.flex_names.append(mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_FLEX, f))
        if not self.triangles:
            raise ValueError('A film audit needs at least one triangular flex')

    def observe(self, data):
        collisions = []
        for ids, name in zip(self.triangles, self.flex_names):
            tri_world = data.flexvert_xpos[ids]
            lower, upper = tri_world.min(axis=(0, 1)), tri_world.max(axis=(0, 1))
            for g, size, geom_name in zip(self.geoms, self.sizes, self.names):
                rotation = data.geom_xmat[g].reshape(3, 3)
                center = data.geom_xpos[g]
                extent = np.abs(rotation) @ size
                if np.any(lower > center + extent) or np.any(upper < center - extent):
                    continue
                local = (tri_world - center) @ rotation
                hits = np.flatnonzero(triangle_box_overlap(local, size))
                if len(hits):
                    collisions.append(dict(film=name, solid=geom_name,
                                           triangle_ids=hits.tolist()))
        return dict(passed=not collisions, tolerance_m=self.tolerance,
                    intersecting_pairs=collisions,
                    scope='All triangle interiors against declared box solids at this recorded state')
