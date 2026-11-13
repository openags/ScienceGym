"""Inferred working geometry for the Cary internal DRA sample clamp.

The manufacturer manual identifies a spring clip on a round post, but does
not give its section or travel. This reconstruction keeps that arrangement;
the guide bore, return spring, end stop and offset arm are explicitly inferred.
Coordinates are the original DRA's Z-up metres, before laboratory placement.
It is a separate candidate, not a modification of previously reviewed scenes.
"""
import math
import numpy as np
import cadquery as cq
import trimesh
from scipy.spatial.transform import Rotation

PIVOT = np.array([.039, 0., .084])
MAX_GAP = .027
MOVING = ('sample_clamp_slider', 'sample_clamp_arm', 'sample_clamp_contact')
PARTS = ('sample_clamp_post', *MOVING, 'sample_clamp_spring')


def cylinder(radius, start, length):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*start), cq.Vector(0, 1, 0))


def box(size, center):
    return cq.Workplane('XY').box(*size).translate(center).val()


def solids():
    """Use millimetres for CAD booleans, then convert tessellations to metres."""
    guide = cylinder(3.15, (39, -180, 84), 70)
    return {
        'sample_clamp_post': cylinder(3, (39, -168, 84), 48).fuse(
            cylinder(5, (39, -170, 84), 2)),
        'sample_clamp_slider': box((11, 10, 13), (39, -130, 84)).cut(guide),
        'sample_clamp_arm': box((38, 2, 7), (20, -127, 84)).cut(guide),
        'sample_clamp_contact': cylinder(4, (1, -126, 84), 4),
    }


def solid_mesh(solid):
    vertices, faces = solid.tessellate(.035, .08)
    return trimesh.Trimesh(vertices=np.array([v.toTuple() for v in vertices])/1000,
                           faces=faces, process=True)


def moving_transform(gap_m, angle_rad=0.):
    if not 0 <= gap_m <= MAX_GAP:
        raise ValueError('Clamp gap outside reconstructed travel')
    transform = np.eye(4)
    transform[:3, :3] = Rotation.from_euler('y', angle_rad).as_matrix()
    transform[:3, 3] = PIVOT - transform[:3, :3] @ PIVOT + [0, -gap_m, 0]
    return transform


def spring_mesh(gap_m):
    """Compression spring outside the slider, so its force closes the clamp.

    End coils meet the fixed stop and moving slider. Pitch changes with gap;
    this is an explicit shape reconstruction, not simulated elasticity.
    """
    moving_transform(gap_m)
    wire = .00035
    start, stop = -.168 + wire, -.135 - gap_m - wire
    turns, sections, sides = 6, 288, 12
    vertices = []
    for i in range(sections+1):
        a = 2*math.pi*turns*i/sections
        for j in range(sides):
            b = 2*math.pi*j/sides
            r = .0042 + wire*math.cos(b)
            vertices.append([.039+r*math.cos(a),
                             start+(stop-start)*i/sections+wire*math.sin(b),
                             .084+r*math.sin(a)])
    faces = []
    for i in range(sections):
        for j in range(sides):
            a, b = i*sides+j, i*sides+(j+1)%sides
            faces.extend([(a, b, b+sides), (a, b+sides, a+sides)])
    # Fan caps, without adding a centre vertex, close the finite wire.
    for j in range(1, sides-1):
        faces.append((0, j+1, j))
        a = sections*sides
        faces.append((a, a+j, a+j+1))
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def meshes(gap_m, angle_rad=0., rigid=None):
    rigid = rigid if rigid is not None else {n:solid_mesh(s) for n,s in solids().items()}
    transform = moving_transform(gap_m, angle_rad)
    result = {n:m.copy() for n,m in rigid.items()}
    for name in MOVING:
        result[name].apply_transform(transform)
    result['sample_clamp_spring'] = spring_mesh(gap_m)
    return result
