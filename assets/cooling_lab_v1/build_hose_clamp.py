"""Source-sized ordinary worm-drive clamp in two unqualified static states.

Band paths conserve a selected measured neutral-line length. This is geometry,
not a constitutive strip model, worm contact solver or tightening controller.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from scipy.optimize import brentq
from shapely.geometry import Point,box,LineString
from shapely.geometry.polygon import orient
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_tripod import hex_prism

STEEL=[176,185,191];WIDTH=.009;THICKNESS=.00065;LENGTH=.164


def groove(s,z=0.):
    # Both faces receive the same displacement: stamped, not perforated stock.
    start=.082;stop=.157;pitch=.0015
    a=np.clip((np.asarray(s)-start)/.003,0,1);b=np.clip((stop-np.asarray(s))/.003,0,1)
    taper=(a*a*(3-2*a))*(b*b*(3-2*b))
    transverse=np.cos(np.pi*np.clip(np.asarray(z)/.007,-.5,.5))**2
    return .0001*taper*(.5-.5*np.cos(2*np.pi*(np.asarray(s)-start)/pitch))**2*transverse


def normals(points):
    tangent=np.gradient(points,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    return np.column_stack([tangent[:,1],-tangent[:,0]])


def bezier(a,b,c,d,count=81):
    t=np.linspace(0,1,count)[:,None]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d


def band_path(state):
    if state=='loose':
        obstacle=Point(0,0).buffer(.025,quad_segs=256);clearance=0.
    else:
        obstacle=Point(0,0).buffer(.0205,quad_segs=256).union(box(-.009,.0205,.009,.0235)).convex_hull;clearance=.00015
    contour=orient(obstacle.buffer(clearance+THICKNESS/2,quad_segs=64),sign=1)
    boundary=LineString(contour.exterior.coords);radius=-contour.bounds[1]
    enter=np.array([.012,-np.sqrt(radius**2-.012**2)]);leave=np.array([-.008,-np.sqrt(radius**2-.008**2)])
    first=boundary.project(Point(enter));last=boundary.project(Point(leave));distance=(last-first)%boundary.length
    assert distance>boundary.length/2
    arc=np.array([boundary.interpolate((first+s)%boundary.length).coords[0] for s in np.linspace(0,distance,int(np.ceil(distance/.00012))+1)])
    # The first millimetre is fixed relative to the rigid housing in both
    # states. Its outer face meets the selected ordinary housing saddle.
    anchor=np.column_stack([np.linspace(.008,.009,11),np.full(11,-radius+.0012)])
    tangent=np.array([-arc[0,1],arc[0,0]]);tangent/=np.linalg.norm(tangent)
    entry=bezier(anchor[-1],anchor[-1]+[.0015,0],arc[0]-tangent*.0015,arc[0])
    tangent=np.array([-arc[-1,1],arc[-1,0]]);tangent/=np.linalg.norm(tangent)
    end=np.array([0.,-radius]);exit_curve=bezier(arc[-1],arc[-1]+tangent*.003,end-[.003,0],end)
    prefix=np.vstack([anchor,entry[1:],arc[1:],exit_curve[1:]])
    def candidate(angle):
        theta=np.linspace(0,angle,max(20,int(np.ceil(angle*(radius+.001)/.00012))+1))
        blend=np.clip(theta/.5,0,1);blend=blend**3*(10-15*blend+6*blend**2)
        rr=radius+.002*blend;tail=np.column_stack([rr*np.sin(theta),-rr*np.cos(theta)])
        p=np.vstack([prefix,tail[1:]]);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        centre=p+normals(p)*groove(s)[:,None]
        length=np.linalg.norm(np.diff(centre,axis=0),axis=1).sum()
        return p,s,centre,float(length)
    angle=brentq(lambda a:candidate(a)[-1]-LENGTH,.05,4.8,xtol=1e-13)
    points,s,centre,length=candidate(angle)
    return points,s,dict(state=state,neutral_line_m=centre.tolist(),measured_neutral_length_m=length,
        baseline_length_m=float(s[-1]),housing_translation_m=[0,-radius,0],tail_angle_rad=float(angle),
        nominal_circle_radius_m=radius,clearance_from_selected_obstacle_m=clearance,
        basis='Selected 164 mm neutral line; adjustable static shape, no strip constitutive law or worm-drive kinematics')


def band_mesh(points,s):
    n=normals(points);edge=.00015
    z=np.unique(np.r_[np.linspace(-WIDTH/2+edge,WIDTH/2-edge,19),-WIDTH/2+np.array([0,.00002,.00007]),WIDTH/2-np.array([0,.00002,.00007])])
    radius=np.clip(np.abs(z)-(WIDTH/2-edge),0,edge)
    half=THICKNESS/2-edge+np.sqrt(np.maximum(0,edge**2-radius**2))
    xy=points[:,None,:]+n[:,None,:]*groove(s[:,None],z[None,:])[:,:,None]
    neutral=np.concatenate([xy,np.broadcast_to(z,(len(points),len(z)))[:,:,None]],axis=2)
    surface_normal=np.cross(np.gradient(neutral,axis=0),np.gradient(neutral,axis=1))
    surface_normal/=np.linalg.norm(surface_normal,axis=2)[:,:,None]
    # Offset along the actual stamped surface normal so the selected sheet
    # gauge remains nominally 0.65 mm rather than thinning under a shear.
    vertices=[(neutral+side*half[None,:,None]*surface_normal).reshape(-1,3) for side in [-1,1]]
    count=len(points);width=len(z);layer=count*width;faces=[]
    def quad(a,b,c,d):faces.extend([[a,b,c],[a,c,d]])
    for k in range(2):
        base=k*layer
        for i in range(count-1):
            for j in range(width-1):quad(base+i*width+j,base+(i+1)*width+j,base+(i+1)*width+j+1,base+i*width+j+1)
    for i in range(count-1):
        for j in [0,width-1]:quad(i*width+j,(i+1)*width+j,layer+(i+1)*width+j,layer+i*width+j)
    for i in [0,count-1]:
        for j in range(width-1):quad(i*width+j,i*width+j+1,layer+i*width+j+1,layer+i*width+j)
    m=trimesh.Trimesh(vertices=np.vstack(vertices),faces=faces);m.fix_normals();assert m.is_volume and len(m.split())==1
    return m


def housing():
    outer=(cq.Workplane('YZ').moveTo(.2,-6.5).lineTo(-4.925,-6.5).lineTo(-4.925,-5.2)
        .threePointArc((-10.125,0),(-4.925,5.2)).lineTo(-4.925,6.5).lineTo(.2,6.5).close().extrude(20).val().translate((-9,0,0)))
    base=cq.Solid.makeBox(22,1.1,13,cq.Vector(-11,-.9,-6.5));body=outer.fuse(base)
    body=body.cut(cq.Solid.makeCylinder(4.,26,cq.Vector(-13,-4.5,0),cq.Vector(1,0,0)))
    body=body.cut(cq.Solid.makeBox(26,4.2,9.5,cq.Vector(-13,-.9,-4.75)))
    # Selected short saddle contacts the band's fixed end from the outside.
    saddle=cq.Solid.makeBox(1.5,.25,10.4,cq.Vector(7.5,.625,-5.2))
    for z in [-5.2,4.75]:saddle=saddle.fuse(cq.Solid.makeBox(1.5,.7,.45,cq.Vector(7.5,.175,z)))
    return body.fuse(saddle).clean()


def worm():
    path=cq.Wire.makeHelix(1.5,18,3.1)
    plane=cq.Plane(origin=path.startPoint(),normal=path.Edges()[0].tangentAt(0))
    thread=cq.Workplane(plane).circle(.5).sweep(path).val().rotate((0,0,0),(0,1,0),90).translate((-9.5,-4.5,0))
    shaft=cq.Solid.makeCylinder(2.8,21,cq.Vector(-11,-4.5,0),cq.Vector(1,0,0))
    flange=cq.Solid.makeCylinder(4.25,1,cq.Vector(-12,-4.5,0),cq.Vector(1,0,0))
    head=hex_prism(7,3).rotate((0,0,0),(0,1,0),90).translate((-15,-4.5,0))
    head=head.cut(cq.Solid.makeBox(1.2,12,.9,cq.Vector(-15.2,-10.5,-.45)))
    return shaft.fuse(thread).fuse(flange).fuse(head).clean()


def build():
    models=[];hood=housing();screw=worm()
    for state in ['loose','installed']:
        g=Geometry();p,s,route=band_path(state);mesh=band_mesh(p,s)
        g.add('continuous_stamped_band',mesh,STEEL,metal=.85,role='inferred_static_bent_band')
        translation=np.array(route['housing_translation_m'])*1000
        solid(g,'asymmetric_housing',hood.translate(tuple(translation)),STEEL,metal=.85,role='source_envelope_inferred_housing')
        solid(g,'slotted_hex_worm_screw',screw.translate(tuple(translation)),STEEL,metal=.85,role='source_head_inferred_worm_profile')
        geometry=export_review(g,'norma_torro_35_50_9_'+state)
        models.append(dict(id=state,geometry=geometry,band_route=route,band_volume_m3=float(mesh.volume),
            role='Alternative static state, not simultaneous stock or simulated adjustment'))
    refs=[Path(__file__),HERE/'hose_clamp_sources.json',HERE/'build_supplies.py',HERE/'build_tripod.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_hose_clamp_candidate',items=models,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        band=dict(width_m=WIDTH,thickness_m=THICKNESS,selected_neutral_length_m=LENGTH,selected_edge_round_m=.00015,
            groove_pitch_m=.0015,groove_depth_m=.0001,groove_status='Selected embossed profile; both surfaces displaced without through holes'),
        rigid_head_envelope_m=dict(width_B=.013,height_h=.011,length_L=.026,head_across_flats=.007),
        installed_context=dict(mast_diameter_m=.041,bracket_width_m=.018,bracket_thickness_m=.003,
            bracket_back_y_m=.0205,bracket_front_y_m=.0235,rs3_origin_m=[0,.1735,.0565]),
        inferences=['Total band length, all local closure contours, slot, shaft, worm profile, stamped pitch/depth and clearances are hypotheses.',
            'Two shapes conserve measured neutral-line length. Band volume and longitudinal fibre strains require a material law before simulation.',
            'The housing contacts a selected fixed band end, but factory crimp/weld retention and screw capture remain unqualified.',
            'No preload, worm engagement, clamp force, sensor-bracket retention, installed RS3 assembly or humanoid tool path is qualified.'],
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,worm_drive_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'hose_clamp_assets.json',record)
    print(json.dumps(dict(states=[dict(id=x['id'],parts=x['geometry']['parts'],length_m=x['band_route']['measured_neutral_length_m'],volume_m3=x['band_volume_m3']) for x in models])))


if __name__=='__main__':build()
