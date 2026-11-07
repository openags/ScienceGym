"""Detached G1 service assets constrained by Unitree's 2024 manual.

The battery drawing supplies three orthographic views. Local dimensions,
materials and connector detail remain inferred; these are inspection assets,
not electrical models or instructions to open a battery enclosure.
"""
import cadquery as cq
import numpy as np
from geometry_tools import Geometry
from build_supplies import solid, curved_tube, top_label, STEEL

CASE = [48, 51, 55]
EDGE = [31, 34, 38]


def rounded(size, center, radius):
    return cq.Workplane('XY').box(*size).edges().fillet(radius).val().translate(center)


def battery():
    g = Geometry()
    # X = 120 mm width; Y = 182 mm insertion length; Z = 80 mm height.
    # End-cap seam and long corner channels follow the manual p.2 views.
    body = rounded((120, 151.6, 80), (0, 15.2, 40), 3)
    for x in [-55, 55]:
        for z in [.3, 79.7]:
            slot = rounded((4, 100, 2), (x, 39, z), .8)
            body = body.cut(slot)
    # Back-face socket pockets really interrupt the housing, not black decals.
    body = body.cut(rounded((38, 9, 12), (0, 90, 29), 1))
    # The rear-view drawing places charging on the viewer's right: -X when
    # looking from +Y. Reusing front-view left/right would mirror this port.
    body = body.cut(rounded((9, 9, 22), (-48, 90, 43), 1))
    for x in [-35, 35]:
        body = body.cut(rounded((13, 7, 29), (x, 91, 29), 3))
    solid(g, 'battery_housing_with_recesses', body, CASE)
    front = rounded((120, 30, 80), (0, -76, 40), 3)
    for x in [-26, 26]:
        front = front.cut(rounded((32, 11, 33), (x, -91, 39), 5))
    front = front.cut(cq.Solid.makeCylinder(10, 6, cq.Vector(0, -93, 68), cq.Vector(0, 1, 0)))
    for z in [27, 34, 41, 48]:
        front = front.cut(cq.Solid.makeCylinder(1.8, 6, cq.Vector(0, -93, z), cq.Vector(0, 1, 0)))
        g.cylinder('unlit_led_'+str(z), .0016, .001, [0, -.0894, z*.001], [91, 99, 103], axis=(0, 1, 0))
    solid(g, 'front_cap_with_latch_pockets', front, CASE)
    for x in [-26, 26]:
        # Separate recessed latch paddles; no release-travel or retention claim.
        solid(g, 'release_latch_'+str(x), rounded((23, 3, 27), (x, -87, 39), 1.4), EDGE)
    g.cylinder('recessed_power_switch', .0086, .0014, [0, -.088, .068], EDGE, axis=(0, 1, 0))
    # Flat side tabs protrude beyond the nominal case width in the drawing.
    # Their 4 mm projection is an inference and excluded from the 120 mm body.
    for sign in [-1, 1]:
        solid(g, 'side_tab_'+str(sign), rounded((5, 26, 3), (sign*61.5, -75, 40), 1), EDGE)
    socket = rounded((37, 7, 11), (0, 87.5, 29), .8)
    socket = socket.cut(rounded((33, 8, 7), (0, 90, 29), .5))
    solid(g, 'recessed_discharge_socket', socket, EDGE)
    # Drawing-derived contact bank, unmeasured count/pitch, no pin assignments.
    for i, x in enumerate(np.linspace(-14, 14, 12)):
        g.box('discharge_contact_'+str(i), [.001, .001, .005], [x*.001, .0863, .029], STEEL, metal=.85)
    charge = rounded((8, 7, 21), (-48, 87.5, 43), .8)
    for z in [39, 47]:
        charge = charge.cut(cq.Solid.makeCylinder(2.1, 9, cq.Vector(-48, 85, z), cq.Vector(0, 1, 0)))
        g.cylinder('charge_contact_'+str(z), .001, .002, [-.048, .086, z*.001], STEEL, axis=(0, 1, 0), metal=.85)
    solid(g, 'recessed_charge_socket', charge, EDGE)
    for x in [-35, 35]:
        solid(g, 'keyed_guide_recess_'+str(x), rounded((10, 1.5, 26), (x, 88.2, 29), .7), EDGE)
    for x in [-53, 53]:
        for z in [7, 73]:
            g.cylinder('back_screw_'+str(x)+'_'+str(z), .002, .0006, [x*.001, .0904, z*.001], STEEL, axis=(0, 1, 0), metal=.85)
    for x in [-15, 15]:
        for z in [17, 41]:
            g.cylinder('connector_retainer_'+str(x)+'_'+str(z), .0024, .0006, [x*.001, .091, z*.001], STEEL, axis=(0, 1, 0), metal=.85)
    top_label(g, 'identification_text', 'G1  /  SPARE', .072, .019, [0, .025, .0801], tuple(CASE), (200, 203, 205))
    return g, dict(case_dimensions_m=[.120, .182, .080],
        state='detached_unpowered_inspection_candidate', articulated=False,
        electrical_qualified=False, installed=False,
        contact_geometry='Drawing-derived, unmeasured; count, pitch and pinout unqualified',
        battery_internals_reconstructed=False)


def charger():
    g = Geometry()
    # Manual p.1 supplies only a small oblique outline, p.3 the envelope.
    # The original 2024 brick is selected explicitly; modern larger chargers
    # are not silently scaled into this version.
    solid(g, 'charger_lower_case', rounded((154, 60, 17.8), (0, 0, 8.9), 2), EDGE)
    solid(g, 'charger_upper_case', rounded((154, 60, 17.8), (0, 0, 27.1), 2), CASE)
    g.cylinder('unlit_status_window', .002, .0004, [.055, 0, .036], [75, 83, 87])
    top_label(g, 'identification_text', 'G1  /  V1.0', .060, .014, [0, 0, .0361], tuple(CASE), (200, 203, 205))
    # Both loose cables are deliberately disconnected. Neither their lengths
    # nor the wall plug geometry is asserted to come from the manual.
    curves=[]
    for side in [-1, 1]:
        t=np.linspace(0, 1, 180)
        p=np.column_stack([side*(.077+.160*t), -.105*np.sin(np.pi*t), .018-.012*np.sin(np.pi*t)])
        curved_tube(g, ('ac' if side<0 else 'dc')+'_loose_cable', p, .003, EDGE)
        g.cylinder(('ac' if side<0 else 'dc')+'_strain_relief', .0045, .016, [side*.081, 0, .018], EDGE, axis=(1, 0, 0))
        curves.append(dict(id='ac' if side<0 else 'dc', points_m=p.tolist(),
            selected_visible_length_m=float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()),
            length_source='authored inspection rest curve; manufacturer cable length not obtained'))
    # Ends are unresolved cable-terminal envelopes, kept visibly unconnected.
    # Do not invent a country plug or claim a verified G1 mating connector.
    for side in [-1, 1]:
        terminal=rounded((22, 13, 12), (side*248, 0, 18), 2)
        terminal=terminal.cut(cq.Solid.makeCylinder(3.2, 5, cq.Vector(side*260, 0, 18), cq.Vector(-side, 0, 0)))
        solid(g, ('ac' if side<0 else 'dc')+'_unresolved_terminal_envelope', terminal, EDGE)
    return g, dict(case_dimensions_m=[.154, .060, .036],
        state='disconnected_inspection_candidate', electrical_qualified=False,
        cables=curves, connectors_qualified=False,
        identity='2024 G1 Battery and Charger User Manual V1.0 envelope',
        limitations='No complete connector or modern charger identity claim; no charging physics')


def models():
    return [('unitree_g1_battery_v10', battery, {}), ('unitree_g1_charger_v10', charger, {})]
