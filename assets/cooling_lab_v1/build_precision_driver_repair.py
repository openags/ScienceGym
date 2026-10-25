"""Repair the two existing Wiha candidates from inspected catalog/photo data.

Catalog page 20 gives both tools a 40 mm blade and 120 mm overall length,
including the PH00's 2 mm shaft. Local grip/cap and PH00 flute contours remain
inferred. This module does not qualify either tip against an instrument socket.
"""
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry
from build_apparatus_mounting import cad_mesh, display
from build_fastener_tools import loft_x, linear_color, size_label


def phillips_tip():
    # A closed tapered four-flute candidate replaces intersecting flat boxes.
    # Neither the profile nor the blade end is a gauged ISO PH00 reproduction.
    core=loft_x([(0,.12,0),(.8,.30,0),(2.8,.60,0),(3.5,1.,0)])
    pieces=[core]
    for angle in [0,90,180,270]:
        vertices=[]
        for x,outer,half_width in [(0,.40,.07),(.8,.65,.11),(2.8,1.,.22),(3.5,1.,.25)]:
            vertices += [[x,y,z] for y in [0,outer] for z in [-half_width,half_width]]
        fin=trimesh.convex.convex_hull(np.asarray(vertices)*.001)
        fin.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle),[1,0,0]));pieces.append(fin)
    return trimesh.boolean.union(pieces,engine='manifold')


def slotted_tip():
    # Manufacturer catalog: 1.5 x 0.25 mm. Current product photo instead shows
    # 0.23 mm; the ledger must preserve that conflict. Shaft diameter is inferred.
    shape=(cq.Workplane('YZ').rect(1.5,.25).workplane(offset=1).rect(1.5,.25)
           .workplane(offset=5).circle(1).loft(ruled=True).val())
    return cad_mesh(shape)


def driver(kind,*,linear_factors=True):
    assert kind in ['ph00','slotted_1_5']
    g=Geometry();radius=6.35;blade=40.;end=120.;cap=7.;handle=end-blade-cap
    body=loft_x([(blade,radius*.52,.75),(blade+1,radius*.60,1),
        (blade+handle*.35,radius*.66,1),(blade+handle*.60,radius*.94,.3),
        (end-cap-1,radius,0),(end-cap,radius*.98,0)])
    tip=phillips_tip() if kind=='ph00' else slotted_tip();tip_end=3.5 if kind=='ph00' else 6.
    shaft=trimesh.creation.cylinder(.001,(45-tip_end)*.001,sections=96)
    shaft.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));shaft.apply_translation([(45+tip_end)*.0005,0,0])
    body=trimesh.boolean.difference([body,shaft],engine='manifold')
    cap_shape=loft_x([(end-cap,radius*.98,0),(end-cap+.6,radius,0),
        (end-1.3,radius*.97,0),(end-.3,radius*.86,0),(end,radius*.72,0)])
    for name,m,color,metal in [('handle',body,[32,34,39],0),
        ('shaft' if kind=='ph00' else 'round_shaft',shaft,[190,198,207],.85),
        ('phillips_tip_candidate' if kind=='ph00' else 'slotted_blade_1_5x0_25',tip,[190,198,207],.85),
        ('rotating_cap',cap_shape,[175,34,44],0)]:
        # The supplies exporter already converts its byte palette. Ordinary
        # tool export needs linear factors here; never convert a palette twice.
        g.add(name,display(m),linear_color(color) if linear_factors else color,role='ordinary_tool_part',metal=metal)
    size_label(g,'PH00' if kind=='ph00' else '1.5 mm',(end-cap-25)*.001,(end-cap-5)*.001,(radius+.035)*.001)
    return g
