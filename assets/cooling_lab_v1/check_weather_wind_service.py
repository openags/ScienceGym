"""Complete 7/16 tool clearance in both weather asset inspection contexts."""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_nut_driver import cylinder_x


def build():
    names=['weather_station_assets','weather_storage_assets','weather_preparation_assets','weather_preparation_checks','wind_driver_assets','wind_driver_checks']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names};checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for n in ['weather_preparation_checks','wind_driver_checks']:check('prior_geometry_'+n,r[n]['passed'])
    station=r['weather_station_assets'];prep=r['weather_preparation_assets'];site=np.asarray(station['station_origin_world_m'])
    installed=load_parts(station['geometry'])
    for m in installed.values():m.apply_translation(-site)
    installed.update({'storage__'+n:m for n,m in load_parts(r['weather_storage_assets']['geometry']).items()})
    contexts={'installed':installed,'preparation':load_parts(prep['geometry'])}
    tool=load_parts(r['wind_driver_assets']['geometry']);socket=cylinder_x(.00825,0,.135)
    inner=trimesh.creation.cylinder(.00559625,.0255,sections=192);inner.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));inner.apply_translation([.01265,0,0])
    socket=trimesh.boolean.difference([socket,inner],engine='manifold')
    envelopes={'socket':socket,'shaft':cylinder_x(.00375,.035,.225),'grip':cylinder_x(.0205,.125,.346)};poses=[]
    for state,parts in contexts.items():
        context={n:m for n,m in parts.items() if not n.endswith('_text')}
        for p in r['wind_driver_checks']['tool_poses']:
            matrix=np.asarray(station['source_transforms']['wind'])@p['tool_to_wind']
            if state=='preparation':matrix=np.asarray(prep['upper_cluster_to_preparation'])@matrix
            nut='wind__'+p['nut'];hits=[];space=[]
            for n,m in tool.items():
                if n=='size_text':continue
                moved=m.copy();moved.apply_transform(matrix)
                for q,b in context.items():
                    v=overlap(moved,b)
                    if not np.isfinite(v) or abs(v)>.001:hits.append(dict(tool_part=n,part=q,overlap_mm3=v))
            check('actual_complete_tool_'+state+'_'+nut,not hits,intersections=hits)
            for n,m in envelopes.items():
                moved=m.copy();moved.apply_transform(matrix)
                for q,b in context.items():
                    if q==nut:continue
                    v=overlap(moved,b)
                    if not np.isfinite(v) or abs(v)>.001:space.append(dict(envelope=n,part=q,overlap_mm3=v))
            check('continuous_turn_and_axial_space_'+state+'_'+nut,not space,intersections=space,excluded_driven_nut=nut)
            poses.append(dict(id=p['nut'],context=state,tool_geometry=r['wind_driver_assets']['geometry'],tool_to_station=matrix.tolist()))
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'check_nut_driver.py']+[HERE/(n+'.json') for n in names]
    failed=[c['name'] for c in checks if not c['passed']]
    report=dict(schema_version=1,passed=not failed,checks=checks,failed=failed,tool_poses=poses,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Actual complete tool and continuous conservative turning/100 mm axial-clearance union in installed and partial low-mast contexts. All fixed instruments, leads, ties and support parts remain; only the separately fitted driven nut is excluded from the turning union. No hand grip, torque, thread motion, stability or robot action.',
        robot_use_qualified=False,torque_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_wind_service_checks.json',report);print(json.dumps(dict(passed=not failed,checks=len(checks),poses=len(poses),failed=failed)))
    if failed:raise AssertionError('Wind service conflicts: '+', '.join(failed))


if __name__=='__main__':build()
