"""Geometry only: qualified sun vectors in, track positions and shadow checks out.

No ephemeris, weather prediction or historical solar positions are fabricated.
Axes: x east, y north, z up. Azimuth measured eastward from north.
"""
import math

def solar_vector(azimuth_deg,elevation_deg):
    a=math.radians(azimuth_deg);e=math.radians(elevation_deg)
    return (math.cos(e)*math.sin(a),math.cos(e)*math.cos(a),math.sin(e))

def track_points(samples,height_m,emitter_radius_m=.025,reflector_radius_m=.03,
                 position_tolerance_m=.001,solar_half_angle_deg=.2666):
    if not samples or not all(math.isfinite(x) and x>0 for x in (height_m,emitter_radius_m,reflector_radius_m)):
        raise ValueError('Nonempty qualified solar samples and positive finite dimensions required')
    if not math.isfinite(position_tolerance_m) or position_tolerance_m<0:raise ValueError('Invalid positioning tolerance')
    result=[]
    for sample in samples:
        a=sample['azimuth_deg'];e=sample['elevation_deg']
        if not all(math.isfinite(v) for v in (a,e)) or not 0<e<=90:raise ValueError('Sun must be above horizon')
        s=solar_vector(a,e);center=(height_m*s[0]/s[2],height_m*s[1]/s[2])
        # Orthonormal tangent vectors on the apparent solar disk.
        aa=math.radians(a);u=(math.cos(aa),-math.sin(aa),0)
        v=(s[1]*u[2]-s[2]*u[1],s[2]*u[0]-s[0]*u[2],s[0]*u[1]-s[1]*u[0])
        alpha=math.radians(solar_half_angle_deg);spread=0
        for i in range(180):
            theta=2*math.pi*i/180
            ray=[s[k]*math.cos(alpha)+(u[k]*math.cos(theta)+v[k]*math.sin(theta))*math.sin(alpha) for k in range(3)]
            if ray[2]<=0:raise ValueError('Solar disk intersects horizon; this geometry cannot certify shading')
            p=(height_m*ray[0]/ray[2],height_m*ray[1]/ray[2])
            spread=max(spread,math.hypot(p[0]-center[0],p[1]-center[1]))
        required=emitter_radius_m+spread+position_tolerance_m
        result.append({'time_id':sample['time_id'],'position_m':[center[0],center[1],height_m],
                       'sampled_solar_penumbra_radius_m':spread,'required_reflector_radius_m':required,
                       'shade_margin_m':reflector_radius_m-required,'sampled_full_aperture_shade':reflector_radius_m>=required})
    return {'method':'horizontal_plane_ray_intersection_with_180_solar_limb_samples','samples':result,
            'temporal_interpolation_validated':False,'physical_shadow_observed':False,
            'limits':'Sampled geometric test only; does not cover gaps between timestamps, wind, mounting errors beyond supplied tolerance or occluding frame geometry.'}
