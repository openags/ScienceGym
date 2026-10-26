"""Source-constrained original KNIPEX 95 61 190 inspection candidate.

The locally inferred profiles and pivots are not manufacturer CAD. Independent
closed/open inspection poses do not simulate cutting or a robot action.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,cad_mesh,export_review
from build_weather_assets import cable_mesh

STEEL=[170,175,178];FORGED=[48,51,53];RED=[179,21,32];DARK=[49,52,54]
PIVOT=np.array([18.,0.,0.]);ALPHA=.14


def translate(point):
    matrix=np.eye(4);matrix[:3,3]=point;return matrix


def half_forging(retainer=True):
    # One continuous forged lever crosses the pivot: positive-Y handle owns
    # the negative-Y jaw. The mirrored lever occupies the other shear plane.
    points=[(34,0),(44,0),(50,6),(54,12),(90,14),(140,14.8),(181,14),
        (184,16),(183,19),(143,20),(96,19.6),(56,20),(43,15),
        (32,11),(25,8),(20,8),(14,7),(11,3),(8,1),(4,.4)]
    profile=cq.Workplane('XY').moveTo(0,.1).threePointArc((2,-8),(8,-12.8)).threePointArc((19,-13.6),(28,-7))
    for p in points:profile=profile.lineTo(*p)
    body=profile.close().extrude(4).edges('|Z').fillet(.5).edges('#Z').chamfer(.35).val().translate((0,0,.025))
    # A real single-sided bevel removes material towards the shear edge.
    # Its local width and edge land are photo-based hypotheses, not a sharp
    # zero-thickness texture or a claimed manufacturer grinding angle.
    wedges=[]
    for x,edge in [(-1,.1),(0,.1),(4,.4),(8,1),(11,3)]:
        plane=cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0))
        wedges.append(cq.Workplane(plane).polyline([(edge-3,4.025),(edge,.225),(edge+5,.225),(edge+5,8),(edge-3,8)]).close().val())
    body=body.cut(cq.Solid.makeLoft(wedges,ruled=True))
    # Small adjustable retainer pivot ear visible beside the main joint.
    if retainer:body=body.fuse(cq.Solid.makeCylinder(5.5,4,cq.Vector(30,10,.025)))
    body=body.cut(cq.Solid.makeCylinder(3.1,8,cq.Vector(18,0,-2)))
    # The depicted internal spring has an actual shared recess between the
    # two levers; it is not drawn through solid steel.
    body=body.cut(cq.Solid.makeCylinder(5.,1.65,cq.Vector(18,0,-.025)))
    if retainer:body=body.cut(cq.Solid.makeCylinder(1.6,8,cq.Vector(30,10,-2)))
    # Two source-visible crimp recesses. Their local sizes are hypotheses.
    for x,r in [(35.,1.4),(40.5,2.0)]:body=body.cut(cq.Solid.makeCylinder(r,8,cq.Vector(x,0,-2)))
    return body


def grip_and_core():
    sections=[(65,16.2,3.7,5.2),(73,16.7,5.525,7.1),
        (96,16.5,5.25,7.4),(130,17.0,5.225,7.6),
        (164,17.4,4.8,7.2),(183,17.6,4.2,6.3),(190,17.5,.35,.45)]
    def loft(rows):
        wires=[]
        for x,y,ry,rz in rows:
            plane=cq.Plane(origin=(x,y,0),xDir=(0,1,0),normal=(1,0,0))
            wires.append(cq.Workplane(plane).ellipse(ry,rz).val())
        return cq.Solid.makeLoft(wires,ruled=False)
    # Coplanar full steel grip cores, with a thin separate plastic coating.
    # A thin flat plate hidden in a mostly-plastic grip contradicts the
    # manufacturer's forged-body construction and substantially underweights
    # this product. The section and coating thickness remain hypotheses.
    scale=20/loft(sections).BoundingBox().zlen
    outer=loft([(x,y,ry,rz*scale) for x,y,ry,rz in sections])
    core_rows=[(x,y,ry*.90,rz*scale*.94) for x,y,ry,rz in sections]
    core=loft(core_rows).cut(cq.Solid.makeBox(20,60,60,cq.Vector(187.8,-10,-30)))
    return outer,core


def hex_head(af,height,z):
    points=[(18+af/np.sqrt(3)*np.cos(a),af/np.sqrt(3)*np.sin(a)) for a in np.arange(6)*np.pi/3]
    shape=cq.Workplane('XY').polyline(points).close().extrude(height).val()
    # Turned chamfers intersect the hex to leave circular end faces, as in
    # the source use photos/cutaway. Sizes remain original hypotheses.
    cone=cq.Solid.makeCone(af/2-.2,af/np.sqrt(3),.8,cq.Vector(18,0,0))
    middle=cq.Solid.makeCylinder(af,height-1.6,cq.Vector(18,0,.8))
    top=cq.Solid.makeCone(af/np.sqrt(3),af/2-.2,.8,cq.Vector(18,0,height-.8))
    return shape.intersect(cone.fuse(middle).fuse(top)).translate((0,0,z))


def build():
    source=json.loads((HERE/'wire_rope_cutter_sources.json').read_text())
    g=Geometry();outer,core=grip_and_core();outer_mesh=cad_mesh(outer)
    splitter=cq.Solid.makeBox(132,100,50,cq.Vector(-100,-50,-20))
    membership={'upper_lever':[],'lower_lever':[],'pivot':[]};states={}
    for side,mirror in [('upper',False),('lower',True)]:
        forging=half_forging(retainer=not mirror).fuse(core);head=forging.intersect(splitter);stem=forging.cut(splitter)
        meshes=dict(polished_jaw=cad_mesh(head),forged_arm=cad_mesh(stem))
        # Cut the coating cavity against the actual exported steel triangles.
        # Independently tessellating the same curved CAD boundary can otherwise
        # produce interpenetrating chords across a shared material interface.
        meshes['plastic_grip']=trimesh.boolean.difference([outer_mesh,meshes['forged_arm']],engine='manifold')
        for label,color in [('polished_jaw',STEEL),('forged_arm',FORGED),('plastic_grip',RED)]:
            mesh=meshes[label]
            if mirror:mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[1,0,0]))
            name=side+'_'+label;g.add(name,mesh,color,metal=.8 if label!='plastic_grip' else 0,role='photo_constrained_inferred_lever_component');membership[side+'_lever'].append(name)
    shaft=cq.Solid.makeCylinder(3.,12.025,cq.Vector(18,0,-7.5))
    bolt=shaft.fuse(hex_head(11.,5.475,4.525));solid(g,'main_pivot_bolt',bolt,STEEL,metal=.8,role='inferred_adjustable_pivot_fastener');membership['pivot'].append('main_pivot_bolt')
    nut=hex_head(11.,5.475,-10).cut(cq.Solid.makeCylinder(3.1,7,cq.Vector(18,0,-11)))
    solid(g,'main_pivot_nut',nut,DARK,metal=.75,role='inferred_thread_clearance_nut');membership['pivot'].append('main_pivot_nut')
    for label,z in [('upper',4.025),('lower',-4.525)]:
        washer=cq.Solid.makeCylinder(5.4,.5,cq.Vector(18,0,z)).cut(cq.Solid.makeCylinder(3.1,1,cq.Vector(18,0,z-.25)))
        name=label+'_pivot_washer';solid(g,name,washer,STEEL,metal=.8,role='inferred_pivot_washer');membership['pivot'].append(name)
    theta=np.linspace(0,6*np.pi,721);points=np.column_stack([.018+.0038*np.cos(theta),.0038*np.sin(theta),np.linspace(-.00125,.00125,len(theta))])
    spring=cable_mesh(points,.00025);g.add('internal_spring_reference',spring,STEEL,metal=.75,role='internal_spring_shape_hypothesis_no_stiffness');membership['pivot'].append('internal_spring_reference')
    # The source retainer has a small knurled wheel. Local tooth count and
    # retention contacts are unknown; its pivot is a real bore, not a marker.
    angles=np.arange(48)*2*np.pi/48;outline=[(30+(4.6 if i%2==0 else 4.2)*np.cos(a),10+(4.6 if i%2==0 else 4.2)*np.sin(a)) for i,a in enumerate(angles)]
    wheel=cq.Workplane('XY').polyline(outline).close().extrude(2.2).val().translate((0,0,4.025))
    wheel=wheel.cut(cq.Solid.makeCylinder(1.6,4,cq.Vector(30,10,3.)))
    solid(g,'retainer_wheel',wheel,STEEL,metal=.8,role='source_visible_inferred_retainer');membership['upper_lever'].append('retainer_wheel')
    pin=cq.Solid.makeCylinder(1.5,6.35,cq.Vector(30,10,0)).fuse(cq.Solid.makeCylinder(2.2,.7,cq.Vector(30,10,6.225)))
    solid(g,'retainer_pin',pin,DARK,metal=.7,role='inferred_retainer_pin');membership['upper_lever'].append('retainer_pin')
    closed={n:np.eye(4) for n in g.scene.graph.nodes_geometry};opened={n:np.eye(4) for n in closed}
    for group,sign in [('upper_lever',1),('lower_lever',-1)]:
        matrix=trimesh.transformations.rotation_matrix(sign*ALPHA,[0,0,1],point=PIVOT*.001)
        for n in membership[group]:opened[n]=matrix
    open_g=Geometry();open_g.scene=g.scene.copy();open_g.parts=list(g.parts)
    opened_scene=open_g.scene
    for n,matrix in opened.items():
        original,key=opened_scene.graph[n];opened_scene.graph.update(frame_to=n,matrix=matrix@original,geometry=key)
    for part in open_g.parts:
        matrix,key=opened_scene.graph[part['id']];mesh=opened_scene.geometry[key].copy();mesh.apply_transform(matrix)
        # Do not copy the closed-state bounds into the opened-state manifest.
        part=dict(part,bounds_m=mesh.bounds.tolist())
        states[part['id']]=part
    open_g.parts=list(states.values())
    geometry=export_review(g,'knipex_9561190_wire_rope_cutter_candidate')
    open_geometry=export_review(open_g,'knipex_9561190_wire_rope_cutter_open')
    refs=[Path(__file__),HERE/'wire_rope_cutter_sources.json',HERE/'build_supplies.py',HERE/'build_weather_assets.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='original_tool_geometry_candidate_pending_checks',geometry=geometry,open_geometry=open_geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions=source['manufacturer_facts'],source_differences=source['source_differences'],
        mechanical_groups=membership,pivot_m=(PIVOT*.001).tolist(),
        inspection_states=dict(closed={n:m.tolist() for n,m in closed.items()},opened={n:m.tolist() for n,m in opened.items()}),
        selected_half_opening_rad=ALPHA,manufacturer_joint_range_known=False,
        selected_local_dimensions_m=dict(plate_thickness=.004,shear_plane_gap=.00005,pivot_bore_radius=.0031,pivot_shaft_radius=.003,spring_wire_radius=.00025),
        limitations=['The 60 mm metric envelope has unspecified jaw state; the closed photo/US width interpretation is separate. Actual exported bounds must be checked, not forced to an incompatible pose.',
            'Forged outlines, blade/crimp details, grip lofts, retainer and fasteners are original local-dimension hypotheses.',
            'Internal spring is an unsolved geometric reference; no spring torque, preload, retainer locking or threaded fastening is simulated.',
            'An inspection opening is not a cutting process, grasp or robot action.'],
        staged_in_lab=False,initial_stock_credit=False,cutting_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'wire_rope_cutter_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],closed_bounds_m=geometry['bounds_m'],open_bounds_m=open_geometry['bounds_m'])))


if __name__=='__main__':build()
