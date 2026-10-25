"""Source-topology M-TPB candidate; all unpublished local dimensions inferred."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review

STEEL=[175,181,183];ZINC=[175,165,120]
LEG_ANGLES=np.array([90,210,330])*np.pi/180


def shaped_tube(stations,radius,wall,dent):
    """Closed annular mesh with matching outer/inner longitudinal profiles."""
    theta=np.linspace(0,2*np.pi,128,endpoint=False);vertices=[]
    for inner in [False,True]:
        for z in stations:
            r=radius(z)-wall*inner-dent(theta,z)
            vertices.extend(np.column_stack([r*np.cos(theta),r*np.sin(theta),np.full(len(theta),z)]))
    n=len(theta);k=len(stations);faces=[]
    for side in range(2):
        for i in range(k-1):
            for j in range(n):
                a=side*k*n+i*n+j;b=side*k*n+i*n+(j+1)%n;c=b+n;d=a+n
                faces.extend([[a,b,c],[a,c,d]])
    for i in [0,k-1]:
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n;c=b+k*n;d=a+k*n
            faces.extend([[a,b,c],[a,c,d]])
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals()
    assert mesh.is_volume and len(mesh.split())==1
    return mesh


def north_south_groove(theta):
    return np.exp(-(np.cos(theta)/.13)**2)


def masts(g):
    stations=[0,.02,1.03,1.045,1.055,1.065,1.075,1.2]
    lower=shaped_tube(stations,lambda z:np.interp(z,[0,1.03,1.045,1.2],[.0205,.0205,.0191,.0191]),.0012,
        lambda t,z:np.interp(z,[0,1.03,1.045,1.2],[0,0,.001,.001])*north_south_groove(t))
    g.add('lower_mast_with_indexing_creases',lower,STEEL,metal=.85,role='inferred_source_mast')
    upper=shaped_tube([1.05,1.055,1.065,1.075,1.09,1.94,1.96,1.98,2.0],lambda z:.0205,.0012,
        lambda t,z:np.interp(z,[1.05,1.055,1.065,1.075,2.0],[0,0,.00045,0,0])*np.exp(-((t-np.pi/2)/.13)**2))
    cutters=[]
    for z in [1.96,1.98]:
        c=trimesh.creation.cylinder(.0034,.06,sections=64);c.apply_transform(trimesh.geometry.align_vectors([0,0,1],[0,1,0]));c.apply_translation([0,0,z]);cutters.append(c)
    upper=trimesh.boolean.difference([upper,*cutters],engine='manifold')
    g.add('upper_mast_with_dimple_and_crossarm_holes',upper,STEEL,metal=.85,role='inferred_source_mast')


def hex_prism(af,length):
    return cq.Workplane('XY').polygon(6,af/np.cos(np.pi/6)).extrude(length).val()


def around_mast(part,angle):
    return part.rotate((0,0,0),(0,0,1),np.degrees(angle))


def fork(x,z,y=0,back=None):
    result=None
    back=x-14 if back is None else back
    for side in [-1,1]:
        part=cq.Solid.makeBox(x+10-back,2,32,cq.Vector(back,y+side*3.1-1,z-16))
        part=part.cut(cq.Solid.makeCylinder(3.4,12,cq.Vector(x,y-6,z),cq.Vector(0,1,0)))
        result=part if result is None else result.fuse(part)
    return result


def radial_clamp(g,name,z):
    outer=[(64*np.cos(a),64*np.sin(a)) for a in LEG_ANGLES]
    inner=[(60*np.cos(a),60*np.sin(a)) for a in LEG_ANGLES]
    body=cq.Workplane('XY').polyline(outer).close().extrude(22).val().translate((0,0,z*1000-11))
    body=body.cut(cq.Workplane('XY').polyline(inner).close().extrude(24).val().translate((0,0,z*1000-12)))
    # Factory hinge forks join the stamped band; legs and brace straps remain
    # separate solids with actual pivot holes. Their local dimensions are inferred.
    for angle in LEG_ANGLES:
        if name=='upper_leg_clamp':
            tabs=fork(84,790,back=58)
        else:
            tabs=fork(72,z*1000,15)
            bridge=cq.Solid.makeBox(27,13.9,8,cq.Vector(56,-1,z*1000-17))
            back=cq.Solid.makeBox(5,21,17,cq.Vector(56,-1,z*1000-17))
            tabs=tabs.fuse(bridge).fuse(back)
        body=body.fuse(around_mast(tabs,angle))
    # Three user-installed radial bolts, each with a real hole and two nuts.
    for i,angle in enumerate(LEG_ANGLES+np.pi/3):
        u=np.array([np.cos(angle),np.sin(angle),0.])
        body=body.cut(cq.Solid.makeCylinder(4.15,30,cq.Vector(*(15*u+[0,0,z*1000])),cq.Vector(*u)))
        shaft=cq.Solid.makeCylinder(3.96875,38.1)
        head=hex_prism(12.7,5.2).translate((0,0,38.1))
        bolt=shaft.fuse(head).rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(0,0,1),np.degrees(angle)).translate(tuple(20.55*u+[0,0,z*1000]))
        solid(g,name+'_radial_bolt_'+str(i+1),bolt,STEEL,metal=.8,role='source_5_16_18_clamp_bolt')
        for side,r in [('inner',23.2),('outer',32.)]:
            nut=hex_prism(12.7,6.8).cut(cq.Solid.makeCylinder(4.05,8,cq.Vector(0,0,-.5)))
            nut=nut.rotate((0,0,0),(0,1,0),90).rotate((0,0,0),(0,0,1),np.degrees(angle)).translate(tuple(r*u+[0,0,z*1000]))
            solid(g,name+'_'+side+'_nut_'+str(i+1),nut,ZINC,metal=.8,role='source_radial_clamp_nut')
    solid(g,name+'_triangular_band',body,ZINC,metal=.8,role='inferred_factory_tri_clamp')


def flattened_leg():
    a=np.array([84.,0.,790.]);b=np.array([510.,0.,22.]);v=b-a;distance=np.linalg.norm(v);v/=distance
    length=distance+24
    stations=[0,40,65,length/2,length-65,length-40,length]
    def skin(inner=False):
        wires=[]
        for z in stations:
            flattened=z<=40 or z>=length-40
            rx=(12. if flattened else 12.7)-(1.2 if inner else 0)
            ry=(1.5 if flattened else 12.7)-(1.2 if inner else 0)
            # Extend the inside beyond both ends so the tube mouths stay open.
            zz=z+(-1 if z==0 and inner else 1 if z==length and inner else 0)
            wires.append(cq.Workplane('XY').ellipse(rx,ry).val().translate((0,0,zz)))
        return cq.Solid.makeLoft(wires,ruled=True)
    leg=skin().cut(skin(True))
    for z in [12,length/2,length-12]:leg=leg.cut(cq.Solid.makeCylinder(3.4,35,cq.Vector(0,-17.5,z),cq.Vector(0,1,0)))
    leg=leg.rotate((0,0,0),(0,1,0),np.degrees(np.arccos(v[2]))).translate(tuple(a-12*v))
    return leg,(a+b)/2


def pivot_hardware(g,name,center,span,angle):
    # Smooth factory pin/bolt hypothesis, with a separate hex nut. Thread
    # engagement and a torque/preload model are intentionally not supplied.
    x,y,z=center;start,end=span
    shaft=cq.Solid.makeCylinder(3.175,end-start,cq.Vector(x,y+start,z),cq.Vector(0,1,0))
    head=cq.Solid.makeCylinder(5,2,cq.Vector(x,y+start-2,z),cq.Vector(0,1,0))
    solid(g,name+'_pivot_bolt',around_mast(shaft.fuse(head),angle),STEEL,metal=.8,role='inferred_factory_pivot')
    nut=hex_prism(11.1125,4.5).cut(cq.Solid.makeCylinder(3.3,6,cq.Vector(0,0,-.5)))
    nut=nut.rotate((0,0,0),(1,0,0),-90).translate((x,y+end-4.7,z))
    solid(g,name+'_pivot_nut',around_mast(nut,angle),ZINC,metal=.8,role='inferred_factory_pivot')


def legs_and_feet(g):
    leg,mid=flattened_leg()
    for i,angle in enumerate(LEG_ANGLES,1):
        solid(g,'leg_'+str(i),around_mast(leg,angle),STEEL,metal=.85,role='inferred_source_nonadjustable_leg')
        plate=cq.Solid.makeBox(80,50,3,cq.Vector(470,-25,0))
        for dx in [-25,25]:
            for y in [-15,15]:plate=plate.cut(cq.Solid.makeCylinder(3.4,5,cq.Vector(510+dx,y,-1)))
        # Foot forks end at the plate instead of passing through the ground.
        tabs=fork(510,22)
        for y in [-3.1,3.1]:tabs=tabs.fuse(cq.Solid.makeBox(24,2,4,cq.Vector(496,y-1,2.5)))
        solid(g,'foot_plate_and_fork_'+str(i),around_mast(plate.fuse(tabs),angle),ZINC,metal=.8,role='inferred_anchored_foot')
        a=np.array([72.,450.]);b=mid[[0,2]];d=b-a;length=np.linalg.norm(d);unit=d/length;normal=np.array([-unit[1],unit[0]])
        outline=[a-8*unit-8*normal,b+8*unit-8*normal,b+8*unit+8*normal,a-8*unit+8*normal]
        brace=cq.Workplane('XZ').polyline([tuple(p) for p in outline]).close().extrude(1.5,both=True).val().translate((0,15,0))
        for x,z in [a,b]:brace=brace.cut(cq.Solid.makeCylinder(3.4,8,cq.Vector(x,11,z),cq.Vector(0,1,0)))
        solid(g,'leg_brace_'+str(i),around_mast(brace,angle),ZINC,metal=.8,role='inferred_factory_brace')
        pivot_hardware(g,'upper_leg_'+str(i),[84,0,790],[-4.3,9.0],angle)
        pivot_hardware(g,'foot_'+str(i),[510,0,22],[-4.3,9.0],angle)
        pivot_hardware(g,'inner_brace_'+str(i),[72,15,450],[-4.3,9.0],angle)
        pivot_hardware(g,'outer_brace_'+str(i),mid,[-14.0,21.2],angle)


def mast_splice(g):
    z=1080.;r=23.8125
    wire=cq.Wire.assembleEdges([
        cq.Edge.makeLine(cq.Vector(-r,35,z),cq.Vector(-r,0,z)),
        cq.Edge.makeThreePointArc(cq.Vector(-r,0,z),cq.Vector(0,-r,z),cq.Vector(r,0,z)),
        cq.Edge.makeLine(cq.Vector(r,0,z),cq.Vector(r,35,z))])
    plane=cq.Plane(origin=(-r,35,z),normal=(0,-1,0),xDir=(1,0,0))
    ub=cq.Workplane(plane).circle(3.175).sweep(wire).val()
    solid(g,'mast_splice_u_bolt',ub,STEEL,metal=.85,role='selected_source_splice_clamp')
    xs=np.linspace(-31,31,161)
    inner=np.maximum(12,np.sqrt(np.maximum(0,20.55**2-xs**2)))
    outline=list(zip(xs,inner))+list(zip(xs[::-1],inner[::-1]+3))
    saddle=cq.Workplane('XY').polyline(outline).close().extrude(14).val().translate((0,0,z-7))
    for x in [-r,r]:
        saddle=saddle.cut(cq.Solid.makeCylinder(3.4,30,cq.Vector(x,0,z),cq.Vector(0,1,0)))
        # Real flat washer seats trim the nearby curved shoulder.
        saddle=saddle.cut(cq.Solid.makeCylinder(7.6,20,cq.Vector(x,15,z),cq.Vector(0,1,0)))
    solid(g,'mast_splice_concave_saddle',saddle,ZINC,metal=.8,role='inferred_source_splice_saddle')
    for side,x in [('left',-r),('right',r)]:
        g.ring('mast_splice_flat_washer_'+side,.0034,.0075,.0012,[x*.001,.0156,z*.001],STEEL,axis=(0,1,0),metal=.8,role='inferred_splice_hardware')
        nut=hex_prism(11.1125,5.5).cut(cq.Solid.makeCylinder(3.3,7,cq.Vector(0,0,-.5)))
        nut=nut.rotate((0,0,0),(1,0,0),-90).translate((x,16.2,z))
        solid(g,'mast_splice_nut_'+side,nut,ZINC,metal=.8,role='inferred_splice_hardware')
    # Source plug sits flush and has an open-bottom slot over optional
    # cross-arm bolts. The reconstructed peg depth and clearance are inferred.
    plug=cq.Solid.makeCylinder(19.2,50,cq.Vector(0,0,1950))
    plug=plug.cut(cq.Solid.makeBox(7,42,39,cq.Vector(-3.5,-21,1949)))
    solid(g,'slotted_flush_mast_plug',plug,[62,66,68],role='inferred_source_mast_plug')


def build():
    g=Geometry();masts(g);radial_clamp(g,'upper_leg_clamp',.799);radial_clamp(g,'lower_brace_clamp',.45);legs_and_feet(g);mast_splice(g)
    geometry=export_review(g,'weather_mtpb_incomplete')
    refs=[Path(__file__),HERE/'tripod_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']
    record=dict(schema_version=1,status='incomplete_tripod_structure',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        selected_dimensions=dict(mast_outer_diameter_m=.041,mast_wall_m=.0012,lower_mast_length_m=1.2,upper_mast_length_m=.95,
            overlap_m=.15,assembled_mast_top_m=2.,top_of_leg_clamp_m=.81,selected_foot_radius_m=.51),
        inferences=['Mast neck, longitudinal creases and localized upper dimple are authored hollow profiles; source supplies topology, not these local dimensions.',
            '5/16-18 shafts and nuts use smooth thread envelopes. The 1/2 inch wrench size is source-supported; nut thickness, shaft length and clearances are selected.',
            'Two 6.8 mm top holes are selected geometry for optional cross-arm bolts; original hole diameter and spacing are unspecified.',
            'Legs use hollow 25.4 mm tubes with selected 40 mm flattened ends and real pivot holes. Factory forks, braces, pins and foot profiles are inferred.',
            'The splice U-bolt preserves 1-5/8 inch nominal inner spacing. Rod diameter, saddle profile, washers, nuts and flush slotted plug are selected local details; retention and sealing remain unqualified.'],
        missing_parts=['Guy and ground kits, foot/guy anchors, level and complete installation'],
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,owner_acceptance=None)
    write_json(HERE/'tripod_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],status=record['status'])))


if __name__=='__main__':build()
