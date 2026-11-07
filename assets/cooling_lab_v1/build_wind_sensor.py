"""Mechanical reconstruction of the selected Onset-modified Davis sensor.

The cup radius in the catalog conflicts with official product photographs.
The primary cup is a source-shaped hypothesis; a literal-radius rotor remains
available separately. Neither is manufacturer CAD or an accepted installation.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import LineString
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import export_review, solid

BLACK=[24,26,29];STEEL=[184,191,199];BRASS=[185,146,63]
HEAD_X=300.;HEAD_Z=375.
ARM_BASE=np.array([3.,0.,75.])
CUP_TURN_RADIUS=60.  # Photo-constrained hypothesis, NOT the published 108 mm.


def port_route_mm():
    """Authored continuous cable path from the hollow arm through the base."""
    ux=.55;uz=np.sqrt(1-ux**2);radius=10.
    center=ARM_BASE+radius*np.array([uz,0,-ux])
    theta=np.linspace(np.arctan2(ux,-uz),np.pi,33)
    arc=center+radius*np.column_stack([np.cos(theta),np.zeros(len(theta)),np.sin(theta)])
    end=arc[-1]
    straight=np.column_stack([np.full(40,end[0]),np.zeros(40),np.linspace(end[2],55,40)])
    t=np.linspace(0,1,161)
    zigzag=np.column_stack([np.full(len(t),end[0]),5*np.sin(np.pi*t)**2*np.sin(2*np.pi*t),55-43*t])
    # Leave the lowest rib through a real notch and turn forward with a
    # selected 10 mm radius. A direct falling Bezier pierced that rib.
    theta=np.linspace(np.pi,1.5*np.pi,41)
    exit_centre=zigzag[-1]+np.array([10.,0,0])
    exit_arc=exit_centre+10*np.column_stack([np.cos(theta),np.zeros(len(theta)),np.sin(theta)])
    return np.vstack([arc,straight[1:],zigzag[1:],exit_arc[1:]])


def d_section(radius,height,flat,base):
    x,y,z=base
    return cq.Solid.makeCylinder(radius,height,cq.Vector(x,y,z)).cut(
        cq.Solid.makeBox(radius+2,2*radius+4,height+2,cq.Vector(x+flat,y-radius-2,z-1)))


def hex_set_screw(length):
    # Source drive is 0.05 inch AF. The 3 mm outer thread envelope is selected.
    body=cq.Solid.makeCylinder(1.5,length)
    socket=cq.Workplane('XY').polygon(6,1.27/np.cos(np.pi/6)).extrude(1.1).val().translate((0,0,length-1.0))
    return body.cut(socket)


def cup_rotor(turn_radius=CUP_TURN_RADIUS):
    # Related Davis 7905L cup diameter is 38.1 mm. The primary radius is an
    # explicit photo-constrained hypothesis; preserve 108 mm as an alternative.
    radius=19.05;centre_radius=turn_radius-radius
    hub=cq.Solid.makeCylinder(9,14,cq.Vector(HEAD_X,0,327))
    for angle in np.arange(3)*2*np.pi/3:
        radial=np.array([np.cos(angle),np.sin(angle),0.])
        tangent=np.array([-np.sin(angle),np.cos(angle),0.])
        outer=cq.Solid.makeSphere(radius,angleDegrees1=-90,angleDegrees2=90)
        outer=outer.cut(cq.Solid.makeBox(100,100,50,cq.Vector(-50,-50,-50)))
        shell=outer.cut(cq.Solid.makeSphere(radius-1.2,angleDegrees1=-90,angleDegrees2=90))
        axis=np.cross([0,0,1],tangent)
        shell=shell.rotate((0,0,0),tuple(axis),90).translate(tuple(np.array([HEAD_X,0,333])+centre_radius*radial))
        # The short radial ribs meet the cup lip. A final hollow cut retains
        # the real open hemisphere instead of filling it with the rib tip.
        rib=cq.Solid.makeCylinder(2.0,centre_radius-radius+1.6-8,cq.Vector(HEAD_X+8*radial[0],8*radial[1],333),cq.Vector(*radial))
        hub=hub.fuse(shell).fuse(rib)
    hub=hub.cut(cq.Solid.makeCylinder(3.1,18,cq.Vector(HEAD_X,0,325)))
    hub=hub.cut(cq.Solid.makeCylinder(1.6,10,cq.Vector(HEAD_X+2,0,333),cq.Vector(1,0,0)))
    return hub


def vane():
    hub=cq.Solid.makeCone(18,10,16,cq.Vector(HEAD_X,0,398))
    # Swept profile and gauge follow the inspected photo as an original
    # hypothesis. The furthest tail is constrained by the approximate radius.
    tail=-np.sqrt(135**2-.9**2)
    fin=(cq.Workplane('XZ').moveTo(tail,60).lineTo(-104,60)
        .spline([(-81,41),(-55,18),(-30,5),(-10,0)],includeCurrent=True)
        .lineTo(-94,0).lineTo(-97,1).close().extrude(.9,both=True).val()
        .translate((HEAD_X,0,410)))
    spar=cq.Solid.makeCylinder(2.8,132,cq.Vector(HEAD_X-98,0,410),cq.Vector(1,0,0))
    body=hub.fuse(fin).fuse(spar)
    body=body.cut(d_section(3.1,20,2.1,[HEAD_X,0,396]))
    body=body.cut(cq.Solid.makeCylinder(1.6,20,cq.Vector(HEAD_X+1,0,405),cq.Vector(1,0,0)))
    return body


def bent_arm():
    direction=np.array([.55,0,np.sqrt(1-.55**2)]);radius=70.;start=ARM_BASE.copy()
    length=(HEAD_Z-start[2]-radius*(1-direction[0]))/direction[2]
    knee=start+length*direction
    angle=np.arctan2(direction[2],direction[0])
    centre=knee+radius*np.array([direction[2],0,-direction[0]])
    middle=centre+radius*np.array([-np.sin(angle/2),0,np.cos(angle/2)])
    finish=centre+np.array([0,0,radius])
    path=cq.Wire.assembleEdges([
        cq.Edge.makeLine(cq.Vector(*start),cq.Vector(*knee)),
        cq.Edge.makeThreePointArc(cq.Vector(*knee),cq.Vector(*middle),cq.Vector(*finish)),
        cq.Edge.makeLine(cq.Vector(*finish),cq.Vector(HEAD_X-10,0,HEAD_Z))])
    plane=cq.Plane(origin=tuple(start),normal=tuple(direction),xDir=(0,1,0))
    tube=cq.Workplane(plane).circle(7.5).circle(6.3).sweep(path).val()
    # Real through-hole for the source #4 cross screw; center and tube gauge
    # are selected local dimensions, not an undisclosed manufacturer's datum.
    pin=start+18*direction
    tube=tube.cut(cq.Solid.makeCylinder(1.6,25,cq.Vector(pin[0],-12.5,pin[2]),cq.Vector(0,1,0)))
    return tube,direction,pin


def housing():
    profile=[(0,347),(14,347),(14,351),(9,356),(8,359),(8,367),(12,370),(12,395),(0,395)]
    body=cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0),(0,1)).val().translate((HEAD_X,0,0))
    body=body.cut(cq.Solid.makeCylinder(5,52,cq.Vector(HEAD_X,0,345)))
    body=body.cut(cq.Solid.makeCylinder(7.6,20,cq.Vector(HEAD_X-20,0,HEAD_Z),cq.Vector(1,0,0)))
    return body


def mounting_base(direction,pin):
    # A source-shaped ribbed saddle with open slots and an actual tube sleeve.
    plate=cq.Solid.makeBox(6,76,100,cq.Vector(-8,-38,0))
    for z in [1,22,44,66,96]:
        plate=plate.fuse(cq.Solid.makeBox(18,76,3,cq.Vector(-8,-38,z)))
    for y in [-34,31]:plate=plate.fuse(cq.Solid.makeBox(16,3,98,cq.Vector(-8,y,1)))
    # Slot ears are retained at the center height rather than painted marks.
    for y in [-27,27]:
        ear=cq.Solid.makeBox(22,20,13,cq.Vector(-8,y-10,45))
        plate=plate.fuse(ear)
        slot=cq.Workplane('YZ').center(y,51.5).slot2D(14,7,0).extrude(30,both=True).val()
        plate=plate.cut(slot)
    # The mast contact is concave, centered 25.5 mm behind the base face.
    sleeve_origin=ARM_BASE-3*direction
    sleeve=cq.Solid.makeCylinder(11,36,cq.Vector(*sleeve_origin),cq.Vector(*direction))
    gusset=(cq.Workplane('XZ').polyline([(-3,63),(-3,108),(20,108),(20,96),(1,63)]).close().extrude(3,both=True).val())
    plate=plate.fuse(sleeve).fuse(gusset)
    bore_origin=ARM_BASE-8*direction
    plate=plate.cut(cq.Solid.makeCylinder(7.65,55,cq.Vector(*bore_origin),cq.Vector(*direction)))
    plate=plate.cut(cq.Solid.makeCylinder(1.6,30,cq.Vector(pin[0],-15,pin[2]),cq.Vector(0,1,0)))
    # A front-open groove follows the actual routed cable instead of a
    # disconnected decorative channel. Its width and entry notch are selected.
    route=port_route_mm();outline=LineString(route[:,1:]).buffer(2.2,quad_segs=8)
    floor=float(route[:,0].min()-2.2)
    groove=(cq.Workplane('YZ').polyline(list(outline.exterior.coords)[:-1]).close()
        .extrude(20-floor).val().translate((floor,0,0)))
    plate=plate.cut(groove)
    # Apply the concave seat after joining the sleeve and gusset as well, so
    # those late-added parts cannot silently occupy the mast's volume.
    return plate.cut(cq.Solid.makeCylinder(20.55,140,cq.Vector(-25.5,0,-2)))


def hex_nut(af,thickness,bore):
    part=cq.Workplane('XY').polygon(6,af/np.cos(np.pi/6)).extrude(thickness).val()
    return part.cut(cq.Solid.makeCylinder(bore,thickness+2,cq.Vector(0,0,-1)))


def installation_hardware(g,pin):
    # #4 x 1-1/8 inch arm screw, nominal selected #4-40 thread envelope.
    shaft=cq.Solid.makeCylinder(1.4224,28.575,cq.Vector(0,0,0))
    head=cq.Solid.makeCylinder(2.8,1.8,cq.Vector(0,0,-1.8))
    for size,corner in [((4.2,.7,.9),(-2.1,-.35,-1.85)),((.7,4.2,.9),(-.35,-2.1,-1.85))]:
        head=head.cut(cq.Solid.makeBox(*size,cq.Vector(*corner)))
    screw=shaft.fuse(head).rotate((0,0,0),(1,0,0),-90).translate((pin[0],-11,pin[2]))
    solid(g,'arm_cross_screw',screw,STEEL,metal=.8,role='selected_arm_fastener')
    teeth=[]
    for i in range(10):
        for offset,r in [(-.16,2.6),(-.10,3.4),(.10,3.4),(.16,2.6)]:
            a=i*2*np.pi/10+offset;teeth.append((r*np.cos(a),r*np.sin(a)))
    washer=cq.Workplane('XY').polyline(teeth).close().extrude(.45).val().cut(cq.Solid.makeCylinder(1.6,2,cq.Vector(0,0,-.5)))
    washer=washer.rotate((0,0,0),(1,0,0),-90).translate((pin[0],11,pin[2]))
    solid(g,'arm_tooth_lock_washer',washer,STEEL,metal=.8,role='selected_arm_fastener')
    nut=hex_nut(6.35,2.38,1.46).rotate((0,0,0),(1,0,0),-90).translate((pin[0],11.45,pin[2]))
    solid(g,'arm_4_40_nut',nut,STEEL,metal=.8,role='selected_arm_fastener')
    # One 1/4-inch U-bolt. Local bend and leg lengths fit the selected 41 mm
    # mast envelope; the manufacturer does not publish these local dimensions.
    z=51.5;cx=-22.2;span=27.
    path=cq.Wire.assembleEdges([
        cq.Edge.makeLine(cq.Vector(24,span,z),cq.Vector(cx,span,z)),
        cq.Edge.makeThreePointArc(cq.Vector(cx,span,z),cq.Vector(cx-span,0,z),cq.Vector(cx,-span,z)),
        cq.Edge.makeLine(cq.Vector(cx,-span,z),cq.Vector(24,-span,z))])
    plane=cq.Plane(origin=(24,span,z),normal=(-1,0,0),xDir=(0,1,0))
    ub=cq.Workplane(plane).circle(3.175).sweep(path).val()
    solid(g,'mast_u_bolt',ub,STEEL,metal=.8,role='selected_mast_fastener')
    for side,y in [('left',-27),('right',27)]:
        g.ring('mast_flat_washer_'+side,.0034,.008,.0014,[.0147,y*.001,z*.001],STEEL,axis=(1,0,0),role='selected_mast_fastener',metal=.8)
        lock=cq.Solid.makeCylinder(5.8,1.2).cut(cq.Solid.makeCylinder(3.3,2,cq.Vector(0,0,-.4)))
        lock=lock.cut(cq.Solid.makeBox(8,.6,2,cq.Vector(0,-.3,-.4)))
        lock=lock.rotate((0,0,0),(0,1,0),90).translate((15.4,y,z))
        solid(g,'mast_split_lock_washer_'+side,lock,STEEL,metal=.8,role='selected_mast_fastener')
        nut=hex_nut(11.1125,5.56,3.3).rotate((0,0,0),(0,1,0),90).translate((16.6,y,z))
        solid(g,'mast_quarter_nut_'+side,nut,STEEL,metal=.8,role='selected_mast_fastener')


def build():
    g=Geometry();arm,direction,pin=bent_arm()
    solid(g,'bent_hollow_arm',arm,BLACK,metal=.5,role='factory_arm')
    solid(g,'stationary_hourglass_housing',housing(),BLACK,role='factory_head')
    solid(g,'mast_saddle_and_sleeve',mounting_base(direction,pin),BLACK,role='inferred_mounting_base')
    solid(g,'three_cup_rotor',cup_rotor(),BLACK,role='removable_rotor')
    solid(g,'vane_with_d_bore',vane(),BLACK,role='removable_vane')
    g.cylinder('lower_speed_shaft',.003,.025,[HEAD_X*.001,0,.3395],STEEL,metal=.8,role='inferred_shaft')
    solid(g,'upper_direction_d_shaft',d_section(3,23,2,[HEAD_X,0,388]),STEEL,metal=.8,role='inferred_shaft')
    for name,z in [('lower',.350),('upper',.393)]:
        g.ring(name+'_bearing_envelope',.00305,.00498,.003,[HEAD_X*.001,0,z],STEEL,metal=.8,role='inferred_bearing')
    for name,length,z,x in [('cup',6.5,333,303),('vane',12.,405,302)]:
        screw=hex_set_screw(length).rotate((0,0,0),(0,1,0),90).translate((x,0,z))
        solid(g,name+'_set_screw',screw,STEEL,metal=.8,role='inferred_set_screw')
    nose=cq.Workplane('XZ').polyline([(0,0),(3,0),(3,5),(2.5,9),(0,15)]).close().revolve(360,(0,0),(0,1)).val()
    nose=nose.rotate((0,0,0),(0,1,0),90).translate((HEAD_X+34,0,410))
    solid(g,'brass_vane_nose',nose,BRASS,metal=.8,role='selected_vane_counterweight')
    installation_hardware(g,pin)
    geometry=export_review(g,'weather_onset_swcf_mechanical')
    alternative=Geometry();solid(alternative,'literal_108mm_cup_rotor',cup_rotor(108.),BLACK,role='conflicting_source_interpretation')
    literal_geometry=export_review(alternative,'weather_wind_literal_radius_alternative')
    refs=[Path(__file__),HERE/'wind_sensor_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']
    record=dict(schema_version=1,status='incomplete_mechanical_candidate',id='onset_swcf_m003',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        rotor_axes=dict(cups=dict(origin_m=[.3,0,.333],axis=[0,0,1],parts=['three_cup_rotor','cup_set_screw','lower_speed_shaft']),
            vane=dict(origin_m=[.3,0,.410],axis=[0,0,1],parts=['vane_with_d_bore','brass_vane_nose','vane_set_screw','upper_direction_d_shaft'])),
        selected_dimensions=dict(cup_turning_radius_m=CUP_TURN_RADIUS*.001,vane_turning_radius_m_approx=.135,related_replacement_cup_diameter_m=.0381,
            arm_outer_diameter_m=.015,arm_wall_m=.0012,selected_mast_diameter_m=.041),
        unresolved_cup_radius=dict(published_onset_radius_m=.108,selected_photo_hypothesis_radius_m=CUP_TURN_RADIUS*.001,
            literal_interpretation_geometry=literal_geometry,manufacturer_error_confirmed=False,
            inference='Official Davis 7905L single-rotor photo and Onset page-1 photo show short ribs. 60 mm is an authored proportion hypothesis, not a recovered dimension or a proven radius/diameter typo.'),
        cable_port=dict(arm_exit_m=(ARM_BASE*.001).tolist(),selected_base_route_m=(port_route_mm()*.001).tolist(),groove_width_m=.0044,
            scope='Selected geometric route and open groove only; no retention or flexible cable qualification'),
        inferences=['Local arm curve, mounting-base profile, shaft/bearing dimensions, 1.2 mm cup wall, 1.8 mm vane gauge and nominal set-screw threads are authored.',
            'The primary 60 mm cup radius follows the short-spoke official photos as a labeled hypothesis; a separate literal 108 mm rotor retains the unresolved catalog interpretation. Neither has passed owner appearance acceptance.',
            'The 470 mm catalog dimension is used as the selected assembled height; the original dimensional datum is unknown.',
            'Arm #4-40 nut AF 6.35 mm, washer tooth geometry and U-bolt local dimensions are selected. The mast nuts retain the manual 7/16 inch wrench size. All threads and lock-washer preload remain simplified.',
            'Bearing envelopes use 20 micrometre nominal radial housing clearance to avoid tessellation-only overlaps; no bearing tolerance or preload claim.',
            'The selected 41 mm mast has 50 micrometre radial saddle clearance and 25 micrometre rear U-bolt clearance before preload. The arm entry is 3 mm forward of the base datum. These are fit hypotheses, not manufacturing tolerances.'],
        companion_candidates=['assets/cooling_lab_v1/wind_lead_assets.json','assets/cooling_lab_v1/wind_kit_assets.json'],
        missing_parts=['Verified manufacturer local dimensions, retention and compliant cable details; complete station support and connection'],
        staged_in_lab=False,assembly_qualified=False,electrical_qualified=False,owner_acceptance=None)
    write_json(HERE/'wind_sensor_assets.json',record)
    print(json.dumps(dict(parts=geometry['parts'],staged_in_lab=False)))


if __name__=='__main__':build()
