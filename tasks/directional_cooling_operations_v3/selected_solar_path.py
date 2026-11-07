"""NREL SPA track for an explicitly selected site/date, not historical evidence."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from importlib import metadata,util
import hashlib
import json
import numpy as np
from solar_geometry import track_points

HERE=Path(__file__).resolve().parent

def generate():
    profile=json.loads((HERE/'selected_reconstruction.json').read_text())
    cfg=profile['cards']['geometry_card']['site_date_window']['value']
    dist=metadata.distribution('pvlib')
    if dist.version!='0.16.1':raise RuntimeError('Use the pinned pvlib==0.16.1 SPA implementation')
    # spa.py is a standalone NumPy module. Loading it directly avoids pulling
    # unrelated dataframe/HDF5 dependencies into the robotics environment.
    source=Path(dist.locate_file('pvlib/spa.py'))
    spec=util.spec_from_file_location('sciencegym_pvlib_spa',source);spa=util.module_from_spec(spec);spec.loader.exec_module(spa)
    local=datetime.fromisoformat(cfg['date']).replace(tzinfo=ZoneInfo(cfg['timezone']))
    delta=spa.calculate_deltat(local.year,local.month)
    def position(t):return np.asarray(spa.solar_position(np.asarray(t,float),cfg['latitude_deg'],cfg['longitude_deg'],30,1013.25,23,delta,.5667,numthreads=1))
    coarse=np.arange(local.timestamp(),local.timestamp()+86400,60)
    best=coarse[np.argmin(position(coarse)[0])]
    fine=np.arange(best-60,best+61,1);noon=float(fine[np.argmin(position(fine)[0])])
    times=np.arange(noon-7200,noon+7201,60);angles=position(times)
    utc=lambda t:datetime.fromtimestamp(float(t),timezone.utc).isoformat()
    samples=[dict(time_id=utc(t),azimuth_deg=float(a),elevation_deg=float(90-z)) for t,a,z in zip(times,angles[4],angles[0])]
    path=track_points(samples,.15)
    dense=np.arange(times[0],times[-1]+1,1);sun=position(dense)
    dense_samples=[dict(time_id=utc(t),azimuth_deg=float(a),elevation_deg=float(90-z)) for t,a,z in zip(dense,sun[4],sun[0])]
    checks=track_points(dense_samples,.15)
    actual=np.array([s['position_m'] for s in checks['samples']]);commands=np.array([s['position_m'] for s in path['samples']])
    indices=np.minimum(np.searchsorted(times,dense,side='right')-1,len(times)-1)
    held=commands[indices]
    required=np.array([s['required_reflector_radius_m'] for s in checks['samples']])
    margins=.03-required-np.linalg.norm(actual-held,axis=1)
    # Fixed band: width is measured perpendicular to the selected centreline.
    # Distance to a polyline, including the finite endpoint caps, avoids
    # assuming that infinite extension beyond the track also casts a shadow.
    a=commands[:-1,:2];v=np.diff(commands[:,:2],axis=0)
    difference=actual[:,:2,None]-a.T[None,:,:]
    u=np.clip(np.einsum('nij,ji->nj',difference,v)/np.sum(v*v,axis=1),0,1)
    near=a[None,:,:]+u[:,:,None]*v[None,:,:]
    distance=np.linalg.norm(actual[:,:2,None].transpose(0,2,1)-near,axis=2).min(axis=1)
    band_margins=.03-required-distance
    return dict(schema_version='sciencegym.selected_solar_path.v1',scenario=cfg,
        solar_noon_UTC=utc(noon),solar_noon_local=datetime.fromtimestamp(noon,ZoneInfo(cfg['timezone'])).isoformat(),
        parameters=dict(height_above_emitter_m=.15,aperture_radius_m=.025,reflector_radius_m=.03,band_width_m=.06,
                        assumed_altitude_m=30,assumed_pressure_hPa=1013.25,assumed_temperature_C=23,delta_T_s=float(delta)),
        method='pvlib 0.16.1 NREL SPA; apparent sun direction, east/north/up frame',
        reference='https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.spa_python.html',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        inputs_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['selected_reconstruction.json','selected_solar_path.py','solar_geometry.py']},
        command_cadence_s=60,command_count=len(samples),samples=[{**s,**p} for s,p in zip(samples,path['samples'])],
        geometry_checks=dict(passed=bool(margins.min()>0 and band_margins.min()>0),check_period_s=1,
            tracked_zero_order_hold_min_margin_m=float(margins.min()),fixed_band_min_margin_m=float(band_margins.min()),
            worst_track_time_UTC=utc(dense[np.argmin(margins)]),point_count=len(dense),
            centreline_bounds_m=[commands.min(axis=0).tolist(),commands.max(axis=0).tolist()],
            limitation='One-second geometric sampling, 180 solar-limb rays and 1 mm position allowance. Mount occlusion, wind and continuous robot tracking are separate physical checks.'),
        historical_measurement=False,physical_tracking_validated=False)

if __name__=='__main__':
    result=generate();(HERE/'selected_solar_path.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['solar_noon_local','command_count','geometry_checks']},indent=2))
