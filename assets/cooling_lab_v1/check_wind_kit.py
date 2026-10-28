"""Check source kit quantities and isolated real hex-drive insertion geometry."""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'wind_kit_assets.json').read_text());mechanical_record=json.loads((HERE/'wind_sensor_assets.json').read_text())
    parts=load_parts(record['geometry']);mechanical=load_parts(mechanical_record['geometry']);checks=[];fits=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('source_kit_count',len(parts)==3 and len([n for n in parts if n.startswith('optional_wood_lag_')])==2)
    for n,m in parts.items():check('single_closed_volume_'+n,m.is_volume and len(m.split())==1)
    check('source_lag_underhead_length',all(abs(parts['optional_wood_lag_'+str(i)].bounds[1,0]-.0807)<2e-7 for i in [1,2]))
    key=parts['supplied_0050_hex_key_candidate'].copy();key.apply_transform(np.linalg.inv(record['key_display_pose']))
    check('selected_key_af',abs(key.extents[1]-.00125)<2e-7,actual_m=float(key.extents[1]))
    # Test only the short tip against each detached set screw. Do not confuse
    # this isolated drive fit with an assembled access path or torque test.
    scene=trimesh.Scene()
    for name in ['cup_set_screw','vane_set_screw']:
        screw=mechanical[name];entry=screw.bounds[1,0];y,z=screw.bounds.mean(axis=0)[1:]
        pose=trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0]);pose[:3,3]=[entry-.0009,y,z]
        placed=key.copy();placed.apply_transform(pose);v=overlap(placed,screw)
        check('isolated_short_tip_fits_'+name,v<.001,overlap_mm3=v,insertion_m=.0009)
        deeper=placed.copy();deeper.apply_translation([-.0004,0,0]);bottomed=overlap(deeper,screw)
        check('negative_tip_bottoming_detected_'+name,bottomed>.001,overlap_mm3=bottomed)
        fits.append(dict(part=name,key_transform=pose.tolist(),insertion_m=.0009,overlap_mm3=v))
        scene.add_geometry(placed,node_name='key__'+name,geom_name='key__'+name)
        scene.add_geometry(screw.copy(),node_name=name,geom_name=name)
    path=HERE/'geometry/weather_wind_key_fit.glb';path.write_bytes(scene.export(file_type='glb'))
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'wind_kit_assets.json',HERE/'wind_sensor_assets.json']
    report=dict(passed=True,checks=checks,isolated_fits=fits,
        fit_geometry=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),parts=len(scene.geometry)),
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        installed_tool_access_qualified=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Only detached screw/key geometry is tested. No hand approach, assembled swing path, preload or torque transmission.',
            'The nominal tool drive is source-supported. Actual AF, leg sizes, bend radius and screw sockets remain selected geometry.'])
    write_json(HERE/'wind_kit_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts))))


if __name__=='__main__':build()
