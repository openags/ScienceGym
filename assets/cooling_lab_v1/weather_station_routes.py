"""Authored installed lead shapes with solved lengths; no cable dynamics."""
import numpy as np
from scipy.optimize import brentq
import trimesh
from build_wind_sensor import port_route_mm


def point(matrix,p):return np.asarray(matrix)[:3,:3]@np.asarray(p)+np.asarray(matrix)[:3,3]
def direction(matrix,p):return np.asarray(matrix)[:3,:3]@np.asarray(p)
def unit(v):return np.asarray(v)/np.linalg.norm(v)
def joined(*pieces):
    p=np.vstack(pieces);return p[np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>1e-11]]
def bezier(a,b,initial,final,handles=(.025,.025),count=121):
    a=np.asarray(a);b=np.asarray(b);c=a+unit(initial)*handles[0];d=b-unit(final)*handles[1];t=np.linspace(0,1,count)[:,None]
    return (1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*b
def transformed(matrix,p):return np.asarray(p)@np.asarray(matrix)[:3,:3].T+np.asarray(matrix)[:3,3]
def length(p):return float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())


def sensor_routes(station,weather,wind_leads):
    """Return two complete leads including smooth transitions and excess coils."""
    transforms={k:np.asarray(v) for k,v in station['source_transforms'].items()}
    stored_head=trimesh.transformations.rotation_matrix(-np.pi/2,[0,1,0]);stored_head[:3,3]=[.015,0,.005]
    rs=transforms['temperature_head']@stored_head
    theta=np.linspace(0,np.pi/2,81)
    arc=np.column_stack([np.zeros(len(theta)),-.014*(1-np.cos(theta)),-.014-.014*np.sin(theta)])
    a=np.array([0,0,.0045]);b=np.array([0,0,-.014]);d=np.array([.011,-.035,-.012]);e=np.array([.030,-.140,-.050]);along=unit(e-d)
    local=joined(np.linspace(a,b,41),arc,bezier(arc[-1],d,[0,-1,0],along,(.013,.012)),bezier(d,e,along,[1,0,0],(.035,.018)))
    temp_prefix=transformed(rs,local);temp_end=point(transforms['temperature_adapter'],weather['stored_leads'][0]['endpoints_m'][-1])
    wind_prefix=transformed(transforms['wind'],port_route_mm()*.001)
    wind_end=point(transforms['wind_adapter'],wind_leads['stored_leads'][0]['endpoints_m'][-1])
    results=[]
    for name,target,prefix,initial_end,via,side,turns,end in [
        ('temperature_sensor_lead',2.,temp_prefix,direction(rs,[1,0,0]),[-.052,-.025,1.520],-1,3,temp_end),
        ('wind_sensor_lead',2.5,wind_prefix,direction(transforms['wind'],[1,0,0]),[.055,.065,1.640],1,5,wind_end)]:
        via=np.asarray(via);normal_step=side*.0045;sign=-side
        coil_height=1.80 if side<0 else 1.82
        descent=np.array([side*(.052 if side<0 else .060),0,1.55])
        theta=np.linspace(-np.pi/2,-np.pi/2+sign*2*np.pi*turns,1201)
        def candidate(radius,details=False):
            coil=np.column_stack([np.linspace(side*.027,side*.027+normal_step*turns,len(theta)),radius*np.cos(theta),coil_height+radius*np.sin(theta)])
            coil_tangent=np.column_stack([np.full(len(theta),normal_step/(sign*2*np.pi)),-radius*np.sin(theta),radius*np.cos(theta)])*sign
            route=joined(prefix,
                bezier(prefix[-1],via,initial_end,[0,0,1],(.020,.030) if side<0 else (.025,.030)),
                bezier(via,coil[0],[0,0,1],coil_tangent[0],(.040,.045) if side<0 else (.025,.018)),
                coil,bezier(coil[-1],descent,coil_tangent[-1],[0,0,-1],(.040,.040)),
                bezier(descent,end,[0,0,-1],[0,0,-1],(.040,.040)))
            return (route,coil) if details else route
        radius=brentq(lambda rad:length(candidate(rad))-target,.025,.10,xtol=1e-13)
        path,coil=candidate(radius,True)
        results.append(dict(id=name,points_m=path.tolist(),radius_m=.0015,length_m=target,measured_length_m=length(path),
            endpoints_m=path[[0,-1]].tolist(),coil=dict(points_m=coil.tolist(),radius_m=float(radius),turns=turns,
                axial_pitch_m=abs(normal_step),centre_height_m=coil_height),
            source_length_interpretation='Selected S-THB 2.0 m sensor lead' if side<0 else 'Selected 2.5 m wind sensor lead; source 3 m / 12.2 m total conflict retained',
            scope='Authored continuous rest shape with solved length, not gravity settling, stiffness, strain relief or tie retention qualification.'))
    return results


def network_routes(station,weather,wind_leads,clear_splice=True):
    """Two source-length network leads, with actual gland and plug endpoints."""
    transforms={k:np.asarray(v) for k,v in station['source_transforms'].items()}
    results=[];radius=.014;theta=np.linspace(0,np.pi/2,81)
    for prefix,source,gland_x,plug_number in [('temperature',weather,-.032,2),('wind',wind_leads,.024,6)]:
        lead=source['stored_leads'][1]
        start=point(transforms[prefix+'_adapter'],lead['endpoints_m'][0])
        end=point(transforms[prefix+'_plug'],lead['endpoints_m'][-1])
        bypass=.020 if prefix=='temperature' and clear_splice else 0.
        routed_start=start.copy();routed_start[0]-=bypass;routed_start[2]=1.150
        approach=bezier(start,routed_start,[0,0,-1],[0,0,-1],(.040,.040))
        gland_y=station['selected_layout']['logger_origin_m'][1]+.029
        inside=np.array([gland_x,gland_y,1.130])
        def candidate(turn_z):
            first=np.column_stack([np.full(len(theta),routed_start[0]),start[1]-radius*(1-np.cos(theta)),turn_z-radius*np.sin(theta)])
            last=np.column_stack([np.full(len(theta),gland_x),gland_y+radius-radius*np.sin(theta),turn_z-radius*np.cos(theta)])
            return joined(approach,np.linspace(routed_start,[routed_start[0],start[1],turn_z],121),first,
                bezier(first[-1],last[0],[0,-1,0],[0,-1,0],(.030,.030)),last,
                np.linspace(last[-1],inside,81),bezier(inside,end,[0,0,1],[0,0,1],(.012,.012)))
        turn_z=brentq(lambda z:length(candidate(z))-.5,1.0,1.105,xtol=1e-13);path=candidate(turn_z)
        results.append(dict(id=prefix+'_network_lead',points_m=path.tolist(),radius_m=.0015,length_m=.5,measured_length_m=length(path),
            endpoints_m=path[[0,-1]].tolist(),drip_lowest_z_m=float(np.min(path[:,2])),drip_turn_radius_m=radius,
            selected_splice_bypass_offset_m=bypass,
            selected_gland_axis_m=[gland_x,gland_y],removed_channel_plug='unused_channel_plug_'+str(plug_number),
            scope='Authored 0.5 m continuous static lead with drip loop; no electrical continuity, weatherproofing, retention or cable dynamics qualification.'))
    return results
