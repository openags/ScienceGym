"""Actual 7/16 tool at both original wind-sensor mast nuts; static geometry."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_nut_driver import cylinder_x


def build():
    r=json.loads((HERE/'wind_driver_assets.json').read_text());wind=json.loads((HERE/'wind_sensor_assets.json').read_text());checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    parts=load_parts(r['geometry']);physical={n:m for n,m in parts.items() if n!='size_text'};context=load_parts(wind['geometry'])
    check('three_physical_domains_and_one_label',len(physical)==3 and len(parts)==4)
    for n,m in physical.items():check('single_closed_'+n,m.is_volume and len(m.split())==1)
    for (n,m),(q,b) in itertools.combinations(physical.items(),2):
        volume=overlap(m,b);check('separate_domains_'+n+'_'+q,np.isfinite(volume) and abs(volume)<.001,overlap_mm3=volume)
    steel=physical['steel_shaft_and_blind_socket'];core=physical['red_molded_core'];grip=physical['black_soft_grip']
    check('source_blade_and_overall',abs(core.bounds[0,0]-.125)<1e-7 and abs(core.bounds[1,0]-.246)<1e-7 and abs(steel.bounds[0,0])<1e-7)
    check('source_grip_envelope',abs(2*np.linalg.norm(grip.vertices[:,1:],axis=1).max()-.041)<3e-5)
    check('independent_smaller_outer_socket',abs(2*np.linalg.norm(steel.vertices[:,1:],axis=1).max()-.0165)<3e-5)
    a=np.arange(6)*np.pi/3
    def points(radius):return np.column_stack([np.full(6,.001),radius*np.cos(a),radius*np.sin(a)])
    check('real_selected_seven_sixteenths_hex_cavity',not steel.contains(points(.00558625)).any() and steel.contains(points(.00560625)).all())
    check('real_selected_blind_depth',not steel.contains([[.0253,0,0]])[0] and steel.contains([[.0255,0,0]])[0])
    socket=cylinder_x(.00825,0,.135)
    inner=trimesh.creation.cylinder(.00559625,.0255,sections=192);inner.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));inner.apply_translation([.01265,0,0])
    socket=trimesh.boolean.difference([socket,inner],engine='manifold')
    bounds={'socket':socket,'shaft':cylinder_x(.00375,.035,.225),'grip':cylinder_x(.0205,.125,.346)}
    fixtures=[];poses=[]
    for side,y in [('left',-.027),('right',.027)]:
        nut='mast_quarter_nut_'+side;matrix=np.eye(4);matrix[:3,3]=[.0168,y,.0515];placed={}
        for n,m in parts.items():placed[n]=m.copy();placed[n].apply_transform(matrix)
        hits=[];space=[]
        for n,m in placed.items():
            if n=='size_text':continue
            for q,b in context.items():
                v=overlap(m,b)
                if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],overlap_mm3=v))
        check('actual_complete_tool_fit_'+side,not hits,intersections=hits)
        for n,m in bounds.items():
            moved=m.copy();moved.apply_transform(matrix)
            for q,b in context.items():
                if q==nut:continue
                v=overlap(moved,b)
                if not np.isfinite(v) or abs(v)>.001:space.append(dict(envelope=n,part=q,overlap_mm3=v))
        check('continuous_rotation_and_axial_space_'+side,not space,intersections=space,excluded_driven_nut=nut,
            scope='Conservative rigid union through 100 mm withdrawal, retaining the fixed U-bolt and a real invariant socket void. No thread motion or tool trajectory is executed.')
        actual=context[nut].copy();actual.apply_transform(np.linalg.inv(matrix))
        check('source_nut_seating_'+side,abs(actual.bounds[1,0]-.00536)<1e-7 and abs(actual.extents[0]-.00556)<1e-7,engagement_m=float(actual.bounds[1,0]))
        bad=placed['steel_shaft_and_blind_socket'].copy();bad.apply_transform(trimesh.transformations.rotation_matrix(np.pi/6,[1,0,0],point=matrix[:3,3]))
        v=overlap(bad,context[nut]);check('negative_wrong_hex_clocking_'+side,v>1,overlap_mm3=v)
        fixture=Geometry()
        for n,m in {**context,**{'tool_'+n:m for n,m in placed.items()}}.items():
            fixture.scene.add_geometry(m,node_name=n,geom_name=n);fixture.parts.append(dict(id=n,role='static_tool_fit',bounds_m=m.bounds.tolist()))
        fixtures.append(dict(nut=nut,geometry=fixture.export('wiha_34142_wind_'+side+'_fit')))
        poses.append(dict(nut=nut,tool_to_wind=matrix.tolist(),tool_geometry=r['geometry']))
    check('no_operation_or_inventory_credit',r['owner_acceptance'] is None and not any(r[k] for k in ['staged_in_lab','initial_stock_credit','torque_qualified','robot_use_qualified']))
    refs=[Path(__file__),HERE/'wind_driver_assets.json',HERE/'wind_sensor_assets.json',HERE/'check_weather_assets.py',HERE/'check_nut_driver.py']
    failed=[c['name'] for c in checks if not c['passed']]
    report=dict(schema_version=1,passed=not failed,checks=checks,failed=failed,fit_geometries=fixtures,tool_poses=poses,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Isolated complete wind instrument and ordinary tool geometry only; complete installed environment, hands, loads and tightening remain unqualified.',
        robot_use_qualified=False,torque_qualified=False,owner_acceptance=None)
    write_json(HERE/'wind_driver_checks.json',report);print(json.dumps(dict(passed=not failed,checks=len(checks),failed=failed)))
    if failed:raise AssertionError('Failed wind tool geometry: '+', '.join(failed))


if __name__=='__main__':build()
