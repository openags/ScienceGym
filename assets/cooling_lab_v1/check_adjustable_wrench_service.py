"""Static, source-sized tool fit at six actual tripod outer jam nuts.

No robot/controller is involved. A clear pose is not an insertion path,
grasp, counterholding action, fastener tightening or load qualification.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def translation(v):
    m=np.eye(4);m[:3,3]=v;return m


def rotation(degrees,axis):
    return trimesh.transformations.rotation_matrix(np.radians(degrees),axis)


def build():
    tool=json.loads((HERE/'adjustable_wrench_assets.json').read_text())
    binding=json.loads((HERE/'weather_scene_binding.json').read_text())
    station=json.loads((HERE/'weather_station_assets.json').read_text())
    reference=next(i for i in tool['items'] if i['id']=='half_inch_reference')
    parts={n:m for n,m in load_parts(reference['geometry']).items() if not n.endswith('_text')}
    site=np.array(station['station_origin_world_m']);inverse=np.linalg.inv(tool['local_jaw_frame_to_tool'])
    obstacles={}
    for module in binding['modules']:
        for n,m in load_parts(module['geometry']).items():
            if n.endswith('_text'):continue
            m.apply_transform(module['to_world']);m.apply_translation(-site)
            obstacles[module['id']+'/'+n]=m
    scene=json.loads((ROOT/binding['base_scene']['path']).read_text())
    # Include actual nearby lab objects; discard only AABBs outside the whole
    # six-pose search envelope. This is not a substitute for mesh collisions.
    envelope=np.array([[-.3,-.3,.15],[.3,.3,1.1]])
    def broad(a,b):return bool(np.all(np.minimum(a[1],b[1])-np.maximum(a[0],b[0])>1e-8))
    for a in scene['assets']:
        if a['id'] in binding['hide_scene_asset_ids']:continue
        bounds=np.array(a['normalized_bounds_m'])+a['position_m']-site
        if not broad(bounds,envelope):continue
        for n,m in load_parts(dict(path=a['geometry'],sha256=a['geometry_sha256'])).items():
            if n.endswith('_text'):continue
            m.apply_translation(np.array(a['position_m'])-site);obstacles[a['id']+'/'+n]=m
    for n,m in load_parts(scene['architecture']).items():
        if n in binding['hide_architecture_parts'] or n.endswith('_text'):continue
        m.apply_translation(-site)
        if broad(m.bounds,envelope):obstacles['architecture/'+n]=m
    candidates=[];targets=[];checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in tool['source_artifacts']+binding['source_artifacts']:
        check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for clamp,z in [('upper_leg_clamp',.799),('lower_brace_clamp',.45)]:
        for index,degrees in enumerate([180,300,420],1):
            target='station/support__'+clamp+'_outer_nut_'+str(index)
            radial=np.array([np.cos(np.radians(degrees)),np.sin(np.radians(degrees)),0.])
            nut_centre=.0354*radial+[0,0,z]
            # 7.62 mm jaw is 0.82 mm thicker than the 6.8 mm nut. Its rear
            # face is 0.01 mm outside the band; this is a static fit datum.
            centre=nut_centre+.00042*radial
            target_rows=[]
            for clock in range(0,360,60):
                matrix=translation(centre)@rotation(degrees,[0,0,1])@rotation(90,[0,1,0])@rotation(clock,[0,0,1])@translation([.015,.00635,0])@inverse
                hits=[];examined=0;placed={}
                for n,m in parts.items():
                    mesh=m.copy();mesh.apply_transform(matrix);placed[n]=mesh
                    for other,obstacle in obstacles.items():
                        if not broad(mesh.bounds,obstacle.bounds):continue
                        examined+=1
                        if mesh.is_volume and obstacle.is_volume:
                            volume=overlap(mesh,obstacle);hit=not np.isfinite(volume) or abs(volume)>.001
                            detail=dict(intersection_mm3=volume)
                        else:
                            manager=trimesh.collision.CollisionManager();manager.add_object('tool',mesh)
                            hit=manager.in_collision_single(obstacle);detail=dict(surface_intersection=bool(hit))
                        if hit:hits.append(dict(tool_part=n,obstacle=other,**detail))
                # Independently measure the actual target hex across the
                # jaw-normal direction in the selected wrench frame.
                fastener=obstacles[target].copy();fastener.apply_transform(np.linalg.inv(matrix@np.array(tool['local_jaw_frame_to_tool'])))
                ylo,yhi=fastener.bounds[:,1];axial=fastener.bounds[:,2]
                engagement=max(0.,min(axial[1],.00381)-max(axial[0],-.00381))
                # The rear 0.01 mm of the nut lies behind the jaw face so
                # that the jaw clears the band. Record overlap explicitly;
                # do not falsely require the nut to sit inside a closed box.
                datum_fit=abs(yhi)<1e-7 and abs(ylo+.0127)<1e-7 and engagement>=.0067
                row=dict(id=clamp+'_'+str(index)+'_'+str(clock),target=target,clock_deg=clock,to_world=(translation(site)@matrix).tolist(),
                    actual_target_jaw_y_m=[float(ylo),float(yhi)],actual_target_axial_m=axial.tolist(),axial_engagement_m=float(engagement),datum_fit=bool(datum_fit),
                    clear=not hits,narrow_phase_pairs=examined,intersections=hits)
                candidates.append(row);target_rows.append(row)
            clear=[r['id'] for r in target_rows if r['clear'] and r['datum_fit']]
            targets.append(dict(target=target,clear_candidate_ids=clear,selected_candidate_id=clear[0] if clear else None))
            check('actual_nut_has_static_tool_candidate_'+target,bool(clear),clear_candidate_ids=clear)
    check('all_selected_poses_fit_actual_hexes',all(r['datum_fit'] for r in candidates))
    result=dict(schema_version=1,passed=all(c['passed'] for c in checks),checks=checks,targets=targets,candidates=candidates,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'adjustable_wrench_assets.json',HERE/'adjustable_wrench_checks.json',HERE/'weather_scene_binding.json',HERE/'weather_station_assets.json',HERE/'check_weather_assets.py']],
        scope='Six actual outer nuts; six discrete clockings each. Whole tool against complete selected station/storage/remaining stock and nearby lab geometry. No approach or rotation sweep.',
        limitations=['Exact contact clearance and fastener dimensions are inferred, not manufacturing tolerances. The selected 6.7 mm minimum axial overlap is a geometry screening threshold, not a rated engagement requirement.','Inner jam nuts, paired counterholding, insertion/removal, hand clearance, torque and load remain unqualified.'],
        selected_tool_state='half_inch_reference',robot_use_qualified=False,torque_qualified=False,owner_acceptance=None)
    write_json(HERE/'adjustable_wrench_service_checks.json',result)
    print(json.dumps(dict(passed=result['passed'],checks=len(checks),targets=targets,clear=sum(r['clear'] and r['datum_fit'] for r in candidates))))
    if not result['passed']:raise AssertionError([c['name'] for c in checks if not c['passed']])


if __name__=='__main__':build()
