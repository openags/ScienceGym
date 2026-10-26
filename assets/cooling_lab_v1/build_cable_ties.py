"""Ordinary source-sized T50I ties and explicitly inferred static bent shapes.

The strap is a continuous serrated solid attached to its molded head. A real
feed opening and an integral pawl remain inspectable. This is not a ratchet,
tensioning, cutting or flexible-body simulation.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from shapely.geometry import MultiPoint,Polygon
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import cad_mesh,export_review
from weather_station_routes import bezier,joined,length

BLACK=[23,25,28]
WIDTH=.0046
THICKNESS=.0012
STOCK_LENGTH=.300


def head_mesh():
    # mm. The feed direction is +Y, the molded root leaves towards +X.
    molded=(cq.Workplane('XZ').rect(7,7.8).workplane(offset=5.8).rect(6.2,6.8).loft(combine=True))
    side_edges=[e for e in molded.val().Edges() if abs(e.tangentAt().y)>.9]
    head=molded.newObject(side_edges).fillet(.25).val()
    opening=cq.Solid.makeBox(3.3,6.2,5.0,cq.Vector(-1.6,-6,-2.5))
    head=head.cut(opening)
    # Integral cantilever topology inferred from the manufacturer's photograph.
    pawl=(cq.Workplane('XY').polyline([(1.75,-4.7),(1.75,-1.6),(.60,-2.8),(.85,-3.2)])
          .close().extrude(4.0).translate((0,0,-2.0)).val())
    return cad_mesh(head.fuse(pawl))


def strap_mesh(points,serrated=True,tip=False):
    """Sweep an eight-corner grooved rectangular section in the XY plane."""
    p=np.asarray(points);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    # All tooth breaks are sampled, rather than aliased by route vertices.
    knots=np.arange(.006,max(.006,s[-1]-.017),.001)
    samples=np.unique(np.r_[np.linspace(0,s[-1],int(np.ceil(s[-1]/.00025))+1),knots,knots+.0002,knots+.0007])
    samples=samples[(samples>=0)&(samples<=s[-1])]
    # Keep neighbouring rings distinct after glTF's float32 conversion.
    kept=[samples[0]]
    for value in samples[1:]:
        if value-kept[-1]>.000025:kept.append(value)
    if s[-1]-kept[-1]<.000025:kept[-1]=s[-1]
    else:kept.append(s[-1])
    samples=np.asarray(kept)
    q=np.column_stack([np.interp(samples,s,p[:,i]) for i in range(2)])
    tangent=np.gradient(q,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    normal=np.column_stack([-tangent[:,1],tangent[:,0]])
    phase=np.mod(samples-.006,.001)
    depth=np.minimum(np.minimum(phase/.0002,1),(.001-phase)/.0003)*.00020
    depth=np.maximum(depth,0) if serrated else np.zeros(len(samples))
    depth[(samples<.006)|(samples>s[-1]-.017)]=0
    # Nonzero base groove avoids duplicate section corners at tooth crests.
    depth+=.000002
    width=np.full(len(samples),WIDTH)
    if tip:width*=1-.65*np.clip((samples-(s[-1]-.016))/.016,0,1)
    vertices=[]
    for xy,n,d,w in zip(q,normal,depth,width):
        for offset,z in [(-THICKNESS/2,-w/2),(THICKNESS/2,-w/2),(THICKNESS/2,w/2),
                         (-THICKNESS/2,w/2),(-THICKNESS/2,w*.36),(-THICKNESS/2+d,w*.36),
                         (-THICKNESS/2+d,-w*.36),(-THICKNESS/2,-w*.36)]:
            vertices.append([*(xy+n*offset),z])
    faces=[]
    for i in range(len(q)-1):
        for j in range(8):
            k=(j+1)%8;a=i*8+j;b=i*8+k;c=(i+1)*8+k;d=(i+1)*8+j
            faces.extend([[a,b,c],[a,c,d]])
    for start,flip in [(0,True),((len(q)-1)*8,False)]:
        # The cross-section is concave. Explicit triangles preserve the groove.
        for f in [(0,1,7),(1,6,7),(1,2,6),(2,5,6),(2,4,5),(2,3,4)]:
            face=[start+x for x in f];faces.append(face[::-1] if flip else face)
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);mesh.fix_normals()
    assert mesh.is_volume
    return mesh


def stock_tie():
    # Straight projected overall length is exactly 300 mm including the head.
    p=np.array([[.0034,-.0006],[STOCK_LENGTH-.0035,-.0006]])
    strap=strap_mesh(p,tip=True)
    return trimesh.boolean.union([head_mesh(),strap],engine='manifold')


def installed_tie(projected_points):
    """Wrap a projected support/bundle envelope, keeping the head outside it.

    Inputs and outputs are metres in the tie plane. The 0.1 mm selected surface
    gap is a geometry allowance, not preload or evidence of physical retention.
    A short flush tail and the removed stock length are explicitly recorded.
    """
    hull=MultiPoint(np.asarray(projected_points)).convex_hull.buffer(.0007,resolution=48)
    perimeter=hull.exterior
    contour=np.array([perimeter.interpolate(s).coords[0] for s in np.linspace(0,perimeter.length,int(np.ceil(perimeter.length/.0004)),endpoint=False)])
    area=np.sum(contour[:,0]*np.roll(contour[:,1],-1)-contour[:,1]*np.roll(contour[:,0],-1))
    if area>0:contour=contour[::-1]
    centre=(np.min(contour[:,0])+np.max(contour[:,0]))/2
    top=float(np.max(contour[:,1]));head_origin=np.array([centre,top+.010])
    upper=contour[:,1]>(np.min(contour[:,1])+top)/2
    right=np.argmin(np.where(upper,np.linalg.norm(contour-[centre+.008,top],axis=1),np.inf))
    left=np.argmin(np.where(upper,np.linalg.norm(contour-[centre-.008,top],axis=1),np.inf))
    indices=[];i=right
    while True:
        indices.append(i)
        if i==left:break
        i=(i+1)%len(contour)
        if len(indices)>len(contour):raise ValueError('Invalid tie perimeter')
    arc=contour[indices]
    tangent=lambda idx:contour[(idx+1)%len(contour)]-contour[(idx-1)%len(contour)]
    root=head_origin+[.0034,-.0006];entry=head_origin+[0,-.0062];end=head_origin+[0,0]
    path=joined(bezier(root,arc[0],[1,0],tangent(right),(.005,.005)),arc,
                bezier(arc[-1],entry,tangent(left),[0,1],(.004,.002)),np.linspace(entry,end,32))
    head=head_mesh();head.apply_translation([*head_origin,0])
    mesh=trimesh.boolean.union([head,strap_mesh(path)],engine='manifold')
    retained=length(path)+.0069 # 7 mm head minus the 0.1 mm molded-root overlap.
    if retained>=STOCK_LENGTH:raise ValueError('Selected tie is too short: '+str(retained))
    enclosed=Polygon(path).buffer(.0007).covers(MultiPoint(np.asarray(projected_points)).convex_hull)
    assert enclosed,'Tie path failed to surround the support/bundle'
    return mesh,dict(head_origin_plane_m=head_origin.tolist(),strap_centreline_plane_m=path.tolist(),
        retained_developed_length_m=retained,cutoff_developed_length_m=STOCK_LENGTH-retained,
        stock_projected_length_m=STOCK_LENGTH,selected_nominal_surface_gap_m=.0001,
        envelope_perimeter_m=float(hull.length),envelope_bounds_m=list(hull.bounds),
        flush_cut=True,ratchet_qualified=False,retention_qualified=False)


def build():
    g=Geometry();m=stock_tie();assert m.is_volume and len(m.split())==1
    g.add('molded_head_pawl_and_serrated_strap',m,BLACK,role='ordinary_nonreleasable_cable_tie')
    geometry=export_review(g,'hellermann_t50i_11101975_cable_tie')
    refs=[Path(__file__),HERE/'cable_tie_sources.json',HERE/'build_supplies.py',HERE/'weather_station_routes.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_ordinary_cable_tie_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        source_dimensions_m=dict(length=.300,width=.0046,head_length=.007,head_width=.0078),
        selected_family_drawing_dimensions_m=dict(thickness=.0012,head_height=.0058),
        selected_details_m=dict(feed_opening_width=.0050,feed_opening_length=.0033,serration_pitch=.001,serration_depth=.0002),
        conservative_bundle_diameter_m=.080,physical_parts=1,
        scope='Source-sized ordinary consumable; family drawing conflicts and inferred local details are recorded. No ratchet, tension, cutting or flexibility validation.',
        staged_in_lab=False,initial_stock_credit=False,retention_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'cable_tie_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],geometry=geometry['path'])))


if __name__=='__main__':build()
