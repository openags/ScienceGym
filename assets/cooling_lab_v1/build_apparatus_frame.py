"""Nominal, dimension-led frame and ordinary machined apparatus connections.

These are original reconstructions. The rail SKU is selected, not identified
from the paper. Unspecified radii, clamps and mounting choices are explicit.
No manipulation/controller code or owner acceptance is produced here.
"""
import json
from functools import lru_cache
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.affinity import rotate
from geometry_tools import HERE, ROOT, sha, write_json
from build_apparatus_mounting import cad_mesh, display, replace

AL = (.64, .68, .70, 1)
DARK = (.10, .12, .13, 1)


def section():
    # Labelled nominal dimensions, not a trace of the dimension illustration.
    body = box(-8.5, -8.5, 8.5, 8.5).buffer(1.5, quad_segs=24)
    a = 3.66 - 1.5 / np.sqrt(2)
    b = 5.995 + 3.66 - a
    slot = Polygon([(-2.63, 11), (2.63, 11), (2.63, 8.5), (5.995, 8.5),
                    (5.995, b), (a, 3.66), (-a, 3.66), (-5.995, b),
                    (-5.995, 8.5), (-2.63, 8.5)])
    for angle in [0, 90, 180, 270]:
        body = body.difference(rotate(slot, angle, origin=(0, 0)))
    hole = Point(0, 0).buffer(2.095, quad_segs=96)
    # The four lobes are visible but not dimensioned in the manufacturer
    # drawing. Their centre/radius are authored, independently of area checks.
    for x in [-1.65, 1.65]:
        for y in [-1.65, 1.65]:
            hole = hole.union(Point(x, y).buffer(.85, quad_segs=64))
    return body.difference(hole)


@lru_cache(None)
def rail(length=340):
    m = trimesh.creation.extrude_polygon(section(), length)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, length / 2, 0])
    m.apply_scale(.001)
    assert m.is_watertight
    return m


@lru_cache(None)
def screw(diameter, length, kind='cap'):
    # Under-head plane is Z=0; head is below it and tip points toward +Z.
    if kind == 'button':
        assert diameter == 5
        radius, height, drive, depth = 4.66, 2.63, 3., 1.3
        # Domed outline is inferred inside the published maximum envelope.
        p = [(0, -height), (2.8, -height), (3.7, -2.2), (4.4, -1.4),
             (radius, -.5), (radius, 0), (0, 0)]
        head = cq.Workplane('XZ').polyline(p).close().revolve().val()
    else:
        radius, height, drive, depth = {3: (2.75, 3., 2.5, 1.3), 4: (3.5, 4., 3., 2.)}[diameter]
        head = cq.Solid.makeCylinder(radius, height, cq.Vector(0, 0, -height))
    body = head.fuse(cq.Solid.makeCylinder(diameter / 2, length))
    socket = cq.Workplane('XY').polygon(6, drive / np.cos(np.pi / 6)).extrude(depth).val().translate((0, 0, -height))
    return cad_mesh(body.cut(socket))


@lru_cache(None)
def tnut():
    block = cq.Solid.makeBox(9, 9, 3, cq.Vector(-4.5, -4.5, 0))
    # Deep-side edge break is an explicit reconstruction inference. The sharp
    # envelope's actual rail-web intersection is retained as a negative case.
    block = cq.Workplane(obj=block).faces('>Z').edges().chamfer(.25).val()
    return cad_mesh(block.cut(cq.Solid.makeCylinder(2.5, 3)))


@lru_cache(None)
def nut():
    body = cq.Workplane('XY').polygon(6, 8 / np.cos(np.pi / 6)).extrude(4.7).val()
    return cad_mesh(body.cut(cq.Solid.makeCylinder(2.5, 4.7)))


@lru_cache(None)
def washer():
    return cad_mesh(cq.Solid.makeCylinder(5, 1.1).cut(cq.Solid.makeCylinder(2.65, 1.1)))


@lru_cache(None)
def csk_m3x10():
    body=cq.Solid.makeCone(3.36,1.5,1.86).fuse(cq.Solid.makeCylinder(1.5,8.14,cq.Vector(0,0,1.86)))
    drive=cq.Workplane('XY').polygon(6,2/np.cos(np.pi/6)).extrude(1.1).val()
    return cad_mesh(body.cut(drive))


@lru_cache(None)
def bridge():
    # Two ordinary through-holes on a selected 42 x 20 x 3 mm flat plate.
    p = cq.Solid.makeBox(42, 20, 3, cq.Vector(-10, -10, 0))
    for x in [0, 22]:
        p = p.cut(cq.Solid.makeCylinder(2.75, 3, cq.Vector(x, 0, 0)))
    return cad_mesh(p)


@lru_cache(None)
def lower_clamp():
    # +X outboard; rail's outer face is X=0. Bored split block is a
    # custom experiment part, with two independent ordinary rail fasteners.
    p = cq.Solid.makeBox(35, 50, 20, cq.Vector(0, -25, 0))
    p = p.cut(cq.Solid.makeCylinder(10.1, 20, cq.Vector(15, 0, 0)))
    p = p.cut(cq.Solid.makeBox(21, 1, 20, cq.Vector(15, -.5, 0)))
    for y in [-17, 17]:
        p = p.cut(cq.Solid.makeCylinder(2.75, 35, cq.Vector(0, y, 10), cq.Vector(1, 0, 0)))
    p = p.cut(cq.Solid.makeCylinder(2.2, 25.5, cq.Vector(29, -25, 15), cq.Vector(0, 1, 0)))
    p = p.cut(cq.Solid.makeCylinder(2, 24.5, cq.Vector(29, .5, 15), cq.Vector(0, 1, 0)))
    return cad_mesh(p)


def track_y(x):
    return 30 + 25 * (1 - (x / 197.5) ** 2)


@lru_cache(None)
def upper_clamp(side):
    # A blind 17 mm bore leaves a real 3 mm top shoulder on the tube end.
    p = cq.Solid.makeBox(35, 30, 20, cq.Vector(-15, -15, 0))
    p = p.cut(cq.Solid.makeCylinder(10.1, 17))
    p = p.cut(cq.Solid.makeBox(21, 1, 17, cq.Vector(0, -.5, 0)))
    p = p.cut(cq.Solid.makeCylinder(2.2, 15.5, cq.Vector(14, -15, 10), cq.Vector(0, 1, 0)))
    p = p.cut(cq.Solid.makeCylinder(2, 14.5, cq.Vector(14, .5, 10), cq.Vector(0, 1, 0)))
    for dx in [-3, 3]:
        y = track_y(side * (187.5 + dx)) - 30
        p = p.cut(cq.Solid.makeCylinder(1.5, 3, cq.Vector(dx, y, 17)))
    return cad_mesh(p)


@lru_cache(None)
def bumper():
    theta = np.linspace(0, np.pi / 2, 65)
    profile = np.c_[9.55 * np.sin(theta), 9.6 * (1 - np.cos(theta))]
    profile = np.vstack((profile, [0, 9.6], [0, 0]))
    m = trimesh.creation.revolve(profile, sections=96)
    m.apply_scale(.001)
    return m


def pose(mesh, xyz, axis=(0, 0, 1), side=1):
    m = mesh.copy()
    if side < 0:
        # Mirror the author's geometry, not a negative-scale scene node.
        m.apply_transform(np.diag([-1., 1., 1., 1.]))
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], axis))
    m.apply_translation(np.asarray(xyz) * .001)
    return m


def apply_frame(scene, prefix):
    base = scene.geometry[prefix + 'acrylic_base']
    center = base.bounds.mean(axis=0)[:2]
    base_z = float(base.bounds[0, 2] * 1000)
    assert abs(base_z - 24) < .001
    changes, added, joints = [], [], []
    for name in list(scene.geometry):
        suffix = name.removeprefix(prefix)
        if suffix.startswith(('rail_', 'orange_insert_', 'upright_', 'bracket_bolt', 'reflector_carriage')):
            scene.delete_geometry(name); changes.append(name)
    def add(name, mesh, color=AL, metal=.8):
        mesh = mesh.copy(); mesh.apply_translation([*center, 0])
        full = prefix + name
        scene.add_geometry(display(mesh, color, metal), node_name=full, geom_name=full)
        added.append(full)
        return full
    # Add clearance holes to the already drilled central-support base/foil;
    # regenerate both from dimensions so the two sets are real CAD voids.
    from build_apparatus_mounting import HOLES
    for suffix, height in [('acrylic_base', 6), ('mylar_base', .012)]:
        z = 24 if suffix == 'acrylic_base' else 30
        p = cq.Solid.makeBox(305, 280, height, cq.Vector(-152.5, -140, z))
        for x, y in HOLES:
            p = p.cut(cq.Solid.makeCylinder(1.7, height, cq.Vector(x, y, z)))
        for x in [-140.5, 140.5]:
            for y in [-105, 105]:
                p = p.cut(cq.Solid.makeCylinder(2.75, height, cq.Vector(x, y, z)))
        m = cad_mesh(p);m.apply_translation([*center, 0]);replace(scene, prefix + suffix, m)
    track_name = 'fixed_reflector_band' if prefix + 'fixed_reflector_band' in scene.geometry else 'reflector_track'
    old = scene.geometry[prefix + track_name]
    track_z = float(old.bounds.mean(axis=0)[2] * 1000)
    width = 60 if track_name == 'fixed_reflector_band' else 6
    x = np.linspace(-197.5, 197.5, 121); y = track_y(x)
    outline = np.vstack((np.c_[x, y-width/2], np.c_[x[::-1], (y+width/2)[::-1]]))
    p = cq.Workplane('XY').polyline(outline.tolist()).close().extrude(1.5).val().translate((0, 0, track_z-.75))
    for side in [-1, 1]:
        for dx in [-3, 3]:
            xx = side * (187.5+dx)
            p = p.cut(cq.Solid.makeCylinder(1.7, 1.5, cq.Vector(xx, track_y(xx), track_z-.75)))
    m = cad_mesh(p);m.apply_translation([*center, 0]);replace(scene, prefix+track_name, m)
    for side, tag in [(-1, 'left'), (1, 'right')]:
        add('frame_rail_'+tag, pose(rail(), [side*162.5, 0, 34]))
        for i, yy in enumerate([-105, 105]):
            key = f'frame_bridge_{tag}_{i+1}'
            add(key, pose(bridge(), [side*140.5, yy, 21], side=side))
            add(key+'_rail_screw', pose(screw(5, 8, 'button'), [side*162.5, yy, 21]), DARK)
            add(key+'_tnut', pose(tnut(), [side*162.5, yy, 25.5]))
            add(key+'_panel_screw', pose(screw(5, 16, 'button'), [side*140.5, yy, 21]), DARK)
            add(key+'_washer', pose(washer(), [side*140.5, yy, 30.012]))
            add(key+'_nut', pose(nut(), [side*140.5, yy, 31.112]))
            joints.append(dict(id=key, rail_hole_xyz_mm=[side*162.5, yy, 21], panel_hole_xyz_mm=[side*140.5, yy, 24],
                               tnut_z_mm=[25.5, 28.5], rail_screw_tip_z_mm=29, panel_screw_tip_z_mm=37))
        lower = add('frame_lower_clamp_'+tag, pose(lower_clamp(), [side*172.5, 30, 24], side=side))
        for i, yy in enumerate([13, 47]):
            add(f'frame_clamp_{tag}_screw_{i}', pose(screw(5, 40, 'button'), [side*207.5, yy, 34], axis=(-side, 0, 0)), DARK)
            add(f'frame_clamp_{tag}_tnut_{i}', pose(tnut(), [side*171, yy, 34], axis=(-side, 0, 0)))
        add('frame_lower_pinch_'+tag, pose(screw(4, 40), [side*201.5, 5, 39], axis=(0, 1, 0)))
        upper_bottom = track_z - .75 - 20
        tube_top = upper_bottom + 17
        tube = trimesh.creation.annulus(.007, .010, (tube_top-24)*.001, sections=128)
        add('frame_tube_'+tag, pose(tube, [side*187.5, 30, (24+tube_top)/2]))
        upper = add('frame_upper_clamp_'+tag, pose(upper_clamp(side), [side*187.5, 30, upper_bottom], side=side))
        add('frame_upper_pinch_'+tag, pose(screw(4, 25), [side*201.5, 15, upper_bottom+10], axis=(0, 1, 0)))
        for i, dx in enumerate([-3, 3]):
            xx=side*(187.5+dx);yy=track_y(xx)
            add(f'frame_track_{tag}_screw_{i}', pose(screw(3, 6), [xx, yy, track_z+.75], axis=(0, 0, -1)))
        joints.append(dict(id='upright_'+tag, lower_clamp=lower, upper_clamp=upper,
            tube_xyz_mm=[side*187.5, 30, 24], tube_length_mm=tube_top-24, tube_top_mm=tube_top,
            upper_clamp_bottom_mm=upper_bottom, track_bottom_mm=track_z-.75,
            split_bore_diameter_mm=20.2, tube_diameter_mm=20, clamp_deformation_qualified=False))
        for yy in [-125, 125]:
            add(f'frame_bumper_{tag}_{yy}', pose(bumper(), [side*130, yy, 14.4]), DARK, 0)
    carriage_parts=[]
    if track_name=='reflector_track':
        # Two plain clamp plates straddle the narrow rail. Loosening their
        # ordinary screws is required to reposition the reflector. This is
        # a selected friction clamp, not an implemented travel mechanism.
        reflector=scene.geometry[prefix+'solar_reflector']
        top=float(reflector.bounds[1,2]*1000)
        underside=float(reflector.bounds[0,2]*1000)
        bottom_z=track_z-.75-3
        upper_z=track_z+.75
        upper=cq.Solid.makeBox(20,20,underside-upper_z,cq.Vector(-10,45,upper_z))
        lower=cq.Solid.makeBox(20,20,3,cq.Vector(-10,45,bottom_z))
        disk=cq.Solid.makeCylinder(30,top-underside,cq.Vector(0,55,underside))
        for y in [48,62]:
            bore=cq.Solid.makeCylinder(1.7,20,cq.Vector(0,y,bottom_z-1))
            countersink=cq.Solid.makeCone(1.7,3.36,1.66,cq.Vector(0,y,top-1.66))
            disk=disk.cut(bore).cut(countersink)
            upper=upper.cut(bore).cut(countersink)
            lower=lower.cut(cq.Solid.makeCylinder(1.5,3,cq.Vector(0,y,bottom_z)))
            carriage_parts.append(add('frame_carriage_screw_'+str(y),pose(csk_m3x10(),[0,y,top],axis=(0,0,-1))))
        for suffix,shape in [('upper',upper),('lower',lower)]:
            carriage_parts.append(add('frame_carriage_'+suffix,cad_mesh(shape)))
        m=cad_mesh(disk);m.apply_translation([*center,0]);replace(scene,prefix+'solar_reflector',m)
        joints.append(dict(id='reflector_carriage',selected_method='two screw friction clamp on the track',
            reflector_top_mm=top,reflector_bottom_mm=underside,upper_bottom_mm=upper_z,
            lower_top_mm=track_z-.75,lower_bottom_mm=bottom_z,screw_tip_mm=top-10,
            parts=carriage_parts,actuation_and_clamp_force_qualified=False))
    return dict(removed_legacy_parts=changes, added_parts=added, rebuilt_parts=[prefix+n for n in ['acrylic_base','mylar_base',track_name]]+([prefix+'solar_reflector'] if carriage_parts else []),
        review_parts=added+[prefix+n for n in ['acrylic_base','mylar_base',track_name]]+([prefix+'solar_reflector'] if carriage_parts else []), joints=joints,
        chosen_rail_length_mm=340, inner_rail_span_mm=305, upright_centres_mm=[-187.5,187.5], track_span_mm=395,
        frame_and_rod_connections='nominal_selected_geometry', physical_installation_qualified=False,
        remaining=['Reflector carriage is a nominal two-screw friction clamp; retention, adjustment and complete travel are not qualified',
                   'Clamp elasticity, friction, threads, preload and tube crushing need physical validation',
                   'Bumper adhesion/compression/weather exposure and all structural load capacities are unqualified',
                   'Stock quantities are reviewed separately; machining, ordinary tool allocation and repeat/reset consumption remain unqualified',
                   'Film/shield and terminal/cable installation remain separate unresolved interfaces'])


if __name__ == '__main__':
    print(json.dumps(dict(section_area_mm2=section().area, reference_area_mm2=159.1)))
