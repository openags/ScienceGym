"""Static ordinary cable-tie placement around actual station cross-sections."""
import numpy as np
import trimesh
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from build_cable_ties import installed_tie


def slab_projection(mesh,matrix,half_width=.0023):
    """Project the triangle-clipped slab, including edges crossing its faces."""
    p=trimesh.transform_points(mesh.vertices,np.linalg.inv(matrix));z=p[:,2]
    inside=p[(z>=-half_width)&(z<=half_width),:2]
    edges=p[mesh.edges_unique];pieces=[inside]
    for level in [-half_width,half_width]:
        a,b=edges[:,0],edges[:,1];d=b[:,2]-a[:,2]
        mask=(np.minimum(a[:,2],b[:,2])<=level)&(np.maximum(a[:,2],b[:,2])>=level)&(np.abs(d)>1e-10)
        a,b,d=a[mask],b[mask],d[mask]
        if len(a):pieces.append((a+(b-a)*((level-a[:,2])/d)[:,None])[:,:2])
    return np.vstack(pieces)


def enclosing_circle(points):
    """Return a verified containing circle; optimizer success alone is unused."""
    p=np.asarray(points)*1000;p=p[ConvexHull(p).vertices]
    centre=(p.min(axis=0)+p.max(axis=0))/2;initial=np.r_[centre,np.linalg.norm(p-centre,axis=1).max()+.001]
    def constraints(x):return x[2]-np.linalg.norm(p-x[:2],axis=1)
    def jac(x):
        delta=p-x[:2];return np.column_stack([delta/np.maximum(np.linalg.norm(delta,axis=1)[:,None],1e-12),np.ones(len(p))])
    result=minimize(lambda x:x[2],initial,jac=lambda x:np.array([0.,0.,1.]),method='SLSQP',
        bounds=[(None,None),(None,None),(0,None)],constraints=[dict(type='ineq',fun=constraints,jac=jac)],options=dict(ftol=1e-10,maxiter=200))
    centre=result.x[:2] if result.success else initial[:2]
    # One micron covers the stored float32 surface and slab interpolation.
    radius=float(np.linalg.norm(p-centre,axis=1).max())+.001
    return dict(centre_plane_m=(centre/1000).tolist(),radius_m=radius/1000,diameter_m=2*radius/1000,
        scope='Verified containing circle of the actual projected bundle; not a load rating.')


def station_ties(parts,leads):
    mast='support__upper_mast_with_dimple_and_crossarm_holes'
    temp='routed__temperature_sensor_lead';wind='routed__wind_sensor_lead'
    temp_net='routed__temperature_network_lead';wind_net='routed__wind_network_lead'
    records={q['id']:q for q in leads};plans=[]
    for prefix in ['temperature','wind']:
        coil=records[prefix+'_sensor_lead']['coil']
        for label,sign in [('lower',-1),('upper',1)]:
            plans.append((prefix+'_coil_'+label,coil['centre_height_m']+sign*(coil['radius_m']-.0003),[mast,'routed__'+prefix+'_sensor_lead']))
    temp_adapter=[n for n in parts if n.startswith('temperature_adapter__')]
    wind_adapter=[n for n in parts if n.startswith('wind_adapter__')]
    plans += [('temperature_adapter_lower',1.360,[mast]+temp_adapter),('temperature_adapter_upper',1.380,[mast]+temp_adapter),
           ('wind_adapter_lower',1.350,[mast]+wind_adapter),('wind_adapter_upper',1.370,[mast]+wind_adapter),
           ('temperature_lead',1.470,[mast,temp]),('wind_lead',1.490,[mast,wind]),
           ('temperature_network',1.260,[mast,temp_net]),('wind_network',1.280,[mast,wind_net])]
    matrices=[]
    for name,z,selection in plans:
        matrix=np.eye(4);matrix[2,3]=z;matrices.append((name,matrix,selection))
    bracket=next(n for n in parts if n.endswith('inclined_mounting_bracket'))
    for i,y in enumerate([-.130,-.075],1):
        matrix=np.eye(4);matrix[:3,:3]=np.array([[1,0,0],[0,0,1],[0,-1,0]]);matrix[1,3]=y
        matrices.append(('rs3_bracket_'+str(i),matrix,[bracket,temp]))
    results=[]
    for name,matrix,selection in matrices:
        projected=[];included=[]
        for n in selection:
            p=slab_projection(parts[n],matrix)
            if len(p):projected.append(p);included.append(n)
        assert len(included)>=2,(name,included)
        points=np.vstack(projected)
        try:mesh,detail=installed_tie(points)
        except Exception as error:raise ValueError('Invalid tie '+name) from error
        mesh.apply_transform(matrix)
        results.append((name,mesh,dict(**detail,plane_to_station=matrix.tolist(),enclosed_parts=included,
            containing_circle=enclosing_circle(points),
            scope='Static strap around actual projected solids; no friction, compression, preload or load retention qualification.')))
    return results
