"""Trace diagnostic rays against actual triangles, including all obstructions.

This is asset geometry evidence, never a calibrated FTIR optical simulation.
Neither poses nor reflection normals are supplied to a robot controller.
"""
import numpy as np
import trimesh


SURFACES = ['m1_face', 'm2_face', 'm3_face', 'alignment_mirror_7004_001', 'm5_face']


def combined_scene(meshes):
    names = list(meshes)
    labels = np.concatenate([np.full(len(meshes[n].faces), i, dtype=int) for i, n in enumerate(names)])
    return trimesh.util.concatenate([meshes[n] for n in names]), names, labels


def trace(combined, names, labels, origin, direction, front_normals, exit_x=-.12):
    origin = np.array(origin, dtype=float); direction = np.array(direction, dtype=float)
    direction /= np.linalg.norm(direction); points = [origin.tolist()]; hits = []
    for expected in SURFACES + [None]:
        loc, _, triangle = combined.ray.intersects_location([origin], [direction])
        distances = (loc-origin) @ direction if len(loc) else np.array([])
        good = np.flatnonzero(distances > 1e-8)
        first = good[np.argmin(distances[good])] if len(good) else None
        if expected is None:
            distance = (exit_x-origin[0])/direction[0] if direction[0] < -1e-8 else -1
            if distance > 0 and (first is None or distances[first] > distance):
                points.append((origin+distance*direction).tolist())
                return dict(passed=True, hit_parts=hits, points_m=points, exit_direction=direction.tolist())
            return dict(passed=False, hit_parts=hits, points_m=points, failure='blocked_exit',
                        obstruction=names[labels[triangle[first]]] if first is not None else None)
        actual = names[labels[triangle[first]]] if first is not None else None
        if actual != expected:
            return dict(passed=False, hit_parts=hits, points_m=points, expected=expected, obstruction=actual,
                        failure='wrong_first_surface' if actual else 'missed_surface')
        normal = combined.face_normals[triangle[first]]
        if np.dot(normal, front_normals[expected]) < .99999:
            return dict(passed=False, hit_parts=hits, points_m=points, expected=expected,
                        obstruction=actual, failure='nonreflective_side_or_back')
        point = loc[first]; points.append(point.tolist()); hits.append(actual)
        direction -= 2*np.dot(direction, normal)*normal
        direction /= np.linalg.norm(direction); origin = point+direction*1e-7


def inspect_angle(meshes, details, degrees, y_offsets=(0,), z_offsets=(0,)):
    transform = trimesh.transformations.rotation_matrix(-np.radians(degrees-20), [0,1,0], details['inspection']['pivot_m'])
    moving = set(details['inspection']['parts']); state = {}
    for name, mesh in meshes.items():
        state[name] = mesh.copy()
        if name in moving: state[name].apply_transform(transform)
    combined, names, labels = combined_scene(state)
    fold = details['nominal_fold_geometry']
    normals = {m['part']:np.array(m['normal']) for m in fold['mirrors']+[fold['sample_surface']]}
    for name in normals:
        if name in moving: normals[name] = transform[:3,:3] @ normals[name]
    source = np.array(fold['points_m'][0]); rays = []
    for dy in y_offsets:
        for dz in z_offsets:
            record = trace(combined, names, labels, source+[0,dy,dz], [-1,0,0], normals)
            rays.append(dict(y_offset_m=dy,z_offset_m=dz,**record))
    return dict(dial_degrees=degrees,passed=all(r['passed'] for r in rays),rays=rays)
