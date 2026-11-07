"""Ordinary weather-station anchoring kits with explicit local-size hypotheses.

Loose stock is separate from installed geometry. No soil, cable tension,
electrical continuity, thread engagement or laboratory inventory is granted.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from scipy.optimize import brentq
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_tripod import hex_prism,around_mast
from build_weather_assets import cable_mesh

STEEL=[170,178,184];ZINC=[170,163,128];COPPER=[153,93,57]


def rod_path(points,radius):
    """Continuous swept round stock; points are CQ edges with tangent joins."""
    path=cq.Wire.assembleEdges(points)
    edge=points[0];start=edge.startPoint();normal=edge.tangentAt(0)
    return cq.Workplane(cq.Plane(origin=start,normal=normal)).circle(radius).sweep(path).val()


def j_stake(diameter,length,bend_radius):
    """Selected J-head; diameter is source, length/bend/tip are hypotheses."""
    r=diameter/2;tip=diameter*2;z=length-bend_radius-r
    edges=[cq.Edge.makeLine(cq.Vector(0,0,tip),cq.Vector(0,0,z)),
        cq.Edge.makeThreePointArc(cq.Vector(0,0,z),cq.Vector(-bend_radius,0,z+bend_radius),cq.Vector(-2*bend_radius,0,z))]
    body=rod_path(edges,r)
    return body.fuse(cq.Solid.makeCone(.15,r,tip+.02))


def s_hook():
    # Two tangent 270-degree bends; both mouths are genuinely open.
    r=10.
    # Construct an exact planar S with edges whose endpoints/tangents match.
    a=cq.Edge.makeThreePointArc(cq.Vector(-r,0,-r),cq.Vector(0,0,-2*r),cq.Vector(r,0,-r))
    b=cq.Edge.makeThreePointArc(cq.Vector(r,0,-r),cq.Vector(r/np.sqrt(2),0,-r+r/np.sqrt(2)),cq.Vector(0,0,0))
    c=cq.Edge.makeThreePointArc(cq.Vector(0,0,0),cq.Vector(-r/np.sqrt(2),0,r-r/np.sqrt(2)),cq.Vector(-r,0,r))
    d=cq.Edge.makeThreePointArc(cq.Vector(-r,0,r),cq.Vector(0,0,2*r),cq.Vector(r,0,r))
    return rod_path([a,b,c,d],2.)


def turnbuckle_parts():
    # A forged open body with two real axial bores. Threaded rods remain
    # separate, with clearance-envelope threads and no invented preload.
    outer=cq.Workplane('XZ').moveTo(0,-30).slot2D(60,13,90).extrude(3,both=True).val().translate((0,0,30))
    opening=cq.Workplane('XZ').slot2D(43,7,90).extrude(5,both=True).val()
    body=outer.cut(opening).cut(cq.Solid.makeCylinder(2.65,80,cq.Vector(0,0,-40)))
    eyes=[]
    for sign in [-1,1]:
        ring=cq.Solid.makeTorus(7,2,cq.Vector(0,0,sign*47),cq.Vector(0,1,0))
        shaft=cq.Solid.makeCylinder(2.5,23,cq.Vector(0,0,sign*20),cq.Vector(0,0,sign))
        eyes.append(ring.fuse(shaft))
    return body,eyes[0],eyes[1]


def wire_clamp_parts():
    # Manual p9: single-screw two-leg clamp. Channels have actual material
    # removed; the body cannot be mistaken for a solid block around a wire.
    body=cq.Workplane('XY').rect(14,9).extrude(14).edges('|Z').fillet(2).val().translate((0,0,-7))
    for x in [-2.,2.]:body=body.cut(cq.Solid.makeCylinder(1.6,18,cq.Vector(x,0,-9)))
    body=body.cut(cq.Solid.makeCylinder(1.55,8,cq.Vector(0,5,0),cq.Vector(0,-1,0)))
    # Screw axis ends just above the twin wire channels. No pressure/contact
    # qualification is inferred from this selected loose-kit position.
    screw=cq.Solid.makeCylinder(1.5,2.8,cq.Vector(0,1.8,0),cq.Vector(0,1,0))
    head=cq.Solid.makeCylinder(3,2,cq.Vector(0,4.6,0),cq.Vector(0,1,0))
    head=head.cut(cq.Solid.makeBox(4.4,1.2,.8,cq.Vector(-2.2,5.6,-.4)))
    head=head.cut(cq.Solid.makeBox(.8,1.2,4.4,cq.Vector(-.4,5.6,-2.2)))
    return body,screw.fuse(head)


def guy_collar(g):
    angles=np.radians([90,210,330]);vertices=angles+np.pi/3
    outer=[(64*np.cos(a),64*np.sin(a)) for a in vertices];inner=[(60*np.cos(a),60*np.sin(a)) for a in vertices]
    band=cq.Workplane('XY').polyline(outer).close().extrude(22).val()
    band=band.cut(cq.Workplane('XY').polyline(inner).close().extrude(24).val().translate((0,0,-1)))
    for i,a in enumerate(angles,1):
        u=np.array([np.cos(a),np.sin(a),0.])
        band=band.cut(cq.Solid.makeCylinder(4.15,28,cq.Vector(*(18*u+[0,0,11])),cq.Vector(*u)))
        ring=cq.Solid.makeTorus(10.5,2.5,cq.Vector(58,0,11),cq.Vector(0,1,0))
        shaft=cq.Solid.makeCylinder(3.96875,29,cq.Vector(20.55,0,11),cq.Vector(1,0,0))
        solid(g,'guy_collar_eye_bolt_'+str(i),around_mast(ring.fuse(shaft),a),STEEL,metal=.8,role='inferred_source_eye_bolt')
        for label,r in [('inner',23.2),('outer',32.)]:
            nut=hex_prism(12.7,6.8).cut(cq.Solid.makeCylinder(4.05,8,cq.Vector(0,0,-.5)))
            nut=nut.rotate((0,0,0),(0,1,0),90).translate((r,0,11))
            solid(g,'guy_collar_'+label+'_nut_'+str(i),around_mast(nut,a),ZINC,metal=.8,role='inferred_collar_fastener')
    solid(g,'guy_collar_triangular_band',band,ZINC,metal=.8,role='source_topology_guy_collar')


def grounding_parts(g):
    # Source only specifies 4 ft rod length. Diameter, copper finish and all
    # local clamp dimensions are hypotheses, with no grounding rating.
    length=1219.2;rod=cq.Solid.makeCone(.2,6.35,25).fuse(cq.Solid.makeCylinder(6.35,length-25,cq.Vector(0,0,25)))
    solid(g,'ground_rod',rod.rotate((0,0,0),(0,1,0),90).translate((0,350,6.35)),COPPER,metal=.7,role='source_length_ground_rod')
    clamp=cq.Workplane('XY').ellipse(14,10).extrude(12).val()
    clamp=clamp.cut(cq.Solid.makeCylinder(6.6,14,cq.Vector(0,0,-1)))
    clamp=clamp.cut(cq.Solid.makeCylinder(1.8,14,cq.Vector(-8.2,0,-1)))
    clamp=clamp.cut(cq.Solid.makeCylinder(2.65,18,cq.Vector(0,0,6),cq.Vector(1,0,0)))
    clamp=clamp.cut(cq.Solid.makeCylinder(4.7,10,cq.Vector(13.75,0,6),cq.Vector(1,0,0)))
    solid(g,'ground_rod_clamp_body',clamp.translate((90,280,0)),ZINC,metal=.8,role='inferred_source_ground_clamp')
    bolt=cq.Solid.makeCylinder(2.5,7,cq.Vector(6.8,0,6),cq.Vector(1,0,0))
    head=hex_prism(8,3.5).rotate((0,0,0),(0,1,0),90).translate((13.8,0,6))
    solid(g,'ground_rod_clamp_bolt',bolt.fuse(head).translate((90,280,0)),STEEL,metal=.8,role='inferred_ground_clamp_fastener')
    # Ordinary U-bolt/saddle wire clamp at the mast, drawn separately from it.
    r=23.8125
    edges=[cq.Edge.makeLine(cq.Vector(-r,35,5),cq.Vector(-r,0,5)),
        cq.Edge.makeThreePointArc(cq.Vector(-r,0,5),cq.Vector(0,-r,5),cq.Vector(r,0,5)),
        cq.Edge.makeLine(cq.Vector(r,0,5),cq.Vector(r,35,5))]
    ub=rod_path(edges,3.175)
    solid(g,'ground_mast_u_bolt',ub.translate((180,270,0)),STEEL,metal=.8,role='inferred_source_ground_mast_clamp')
    saddle=cq.Solid.makeBox(65,4,12,cq.Vector(-32.5,23.1,-1))
    for x in [-r,r]:saddle=saddle.cut(cq.Solid.makeCylinder(3.4,10,cq.Vector(x,22,5),cq.Vector(0,1,0)))
    # The wire seat is an actual transverse half-round groove on the mast side.
    saddle=saddle.cut(cq.Solid.makeCylinder(1.8,16,cq.Vector(0,22.1,-3)))
    solid(g,'ground_mast_saddle',saddle.translate((180,270,0)),ZINC,metal=.8,role='inferred_source_ground_mast_clamp')
    for label,x in [('left',-r),('right',r)]:
        nut=hex_prism(11.1125,5.5).cut(cq.Solid.makeCylinder(3.3,7,cq.Vector(0,0,-.5)))
        nut=nut.rotate((0,0,0),(1,0,0),-90).translate((180+x,297.3,5))
        solid(g,'ground_mast_nut_'+label,nut,ZINC,metal=.8,role='inferred_ground_clamp_fastener')


def coil(length,turns,center,pitch=.0035):
    theta=np.linspace(0,2*np.pi*turns,6001)
    # A flat spiral rests on one plane; it does not suspend later turns as an
    # unverified free-standing helix. Spacing and shape remain selected.
    def points(r):
        radii=r+pitch*theta/(2*np.pi)
        return np.column_stack([radii*np.cos(theta),radii*np.sin(theta),np.zeros(len(theta))])+np.array(center)
    r=brentq(lambda r:np.linalg.norm(np.diff(points(r),axis=0),axis=1).sum()-length,.005,.8,xtol=1e-14)
    return points(r)


def build():
    g=Geometry();guy_collar(g)
    for i in range(3):
        x=140+i*65
        for label,part in zip(['body','eye_lower','eye_upper'],turnbuckle_parts()):
            solid(g,'turnbuckle_'+str(i+1)+'_'+label,part.rotate((0,0,0),(1,0,0),90).translate((x,0,4)),STEEL,metal=.8,role='inferred_source_turnbuckle')
        solid(g,'s_hook_'+str(i+1),s_hook().rotate((0,0,0),(1,0,0),90).translate((x,95,2)),STEEL,metal=.8,role='source_topology_open_hook')
    for i in range(6):
        for label,part in zip(['body','screw'],wire_clamp_parts()):
            solid(g,'wire_clamp_'+str(i+1)+'_'+label,part.translate((120+i*28,155,7)),ZINC,metal=.8,role='inferred_source_single_screw_wire_clamp')
    for label,diameter,length,bend,y in [('guy',12.7,750.,12.7,-150),('foot',6.35,400.,9.525,-280)]:
        for i in range(3):
            part=j_stake(diameter,length,bend).rotate((0,0,0),(0,1,0),90).translate((0,y-i*40,diameter/2))
            solid(g,label+'_stake_'+str(i+1),part,STEEL,metal=.8,role='source_diameter_inferred_stake')
    grounding_parts(g)
    leads=[]
    for label,length,radius,turns,center,color in [('uncut_guy_wire',15.24,.0015,10,[.65,.65,.0015],[110,115,111]),('uncut_ground_wire',3.,.0015,4,[1.07,.65,.0015],COPPER)]:
        points=coil(length,turns,center)
        g.add(label,cable_mesh(points,radius),color,metal=.5,role='unprocessed_wire_stock')
        leads.append(dict(id=label,points_m=points.tolist(),length_m=length,radius_m=radius,
            length_status='manufacturer 50 ft stock' if label=='uncut_guy_wire' else 'selected 3 m stock; manufacturer length unspecified',
            diameter_status='selected 3 mm outside envelope; no verified conductor, strand or coating dimensions'))
    geometry=export_review(g,'weather_anchoring_loose_kits')
    refs=[Path(__file__),HERE/'tripod_sources.json',HERE/'build_tripod.py',HERE/'build_weather_assets.py',HERE/'build_supplies.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_loose_anchoring_kits',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],stored_wires=leads,
        kit_counts=dict(guy_collar=1,eye_bolts=3,collar_nuts=6,turnbuckles=3,s_hooks=3,wire_clamps=6,guy_stakes=3,foot_stakes=3,ground_rod=1,ground_rod_clamp=1,ground_mast_clamp=1,guy_wire_stock=1,ground_wire_stock=1),
        source_facts=dict(guy_wire_stock_length_m=15.24,ground_rod_length_m=1.2192,guy_stake_diameter_m=.0127,foot_stake_diameter_m=.00635),
        selected_dimensions=dict(guy_stake_length_m=.750,foot_stake_length_m=.400,ground_rod_diameter_m=.0127,guy_wire_outside_diameter_m=.003,ground_wire_outside_diameter_m=.003,ground_wire_stock_length_m=3.,s_hook_bend_radius_m=.010,s_hook_wire_diameter_m=.004),
        inferences=['J-shaped stake heads, all stake lengths and bends, rod diameter and copper finish are hypotheses; source establishes nominal stake diameters and ground-rod length only.',
            'The source manual shows a single-screw clamp over two wire legs, an open turnbuckle body and S hooks; every local profile, fastener size and coating is authored.',
            'Guy wire is supplied as one uncut 15.24 m piece. The displayed coil is a selected continuous rest shape, without flexible dynamics, tension or a load rating.',
            'Ground-wire length and diameter are selected stock, not a manufacturer specification or proof of electrical suitability.',
            'Smooth thread envelopes, genuine openings and separated solids support geometry review only; clamp force, electrical continuity and retention are unqualified.'],
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,structural_load_qualified=False,electrical_grounding_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_anchoring_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],status=record['status'])))


if __name__=='__main__':build()
