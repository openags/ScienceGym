"""Ordinary complete-tool and enclosure space in the fully wired station.

Conservative rigid unions establish space only. They are not robot paths,
grasp plans, thread motion, seal compression or contact/dynamics evidence.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_nut_driver import cylinder_x
from check_u30 import rotated
from weather_station_routes import network_routes
from build_weather_assets import cable_mesh


def build():
    names=['weather_station_assets','weather_station_checks','weather_storage_assets','weather_storage_checks',
           'mast_driver_assets','mast_driver_checks','nut_driver_assets','nut_driver_checks','u30_assets','u30_ground_assets']
    r={name:json.loads((HERE/(name+'.json')).read_text()) for name in names};checks=[];poses=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for name,record in r.items():
        for ref in record['source_artifacts']:check('source_'+name+'_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    station=r['weather_station_assets'];origin=np.asarray(station['station_origin_world_m']);context=load_parts(station['geometry'])
    for m in context.values():m.apply_translation(-origin)
    context.update({'storage__'+n:m for n,m in load_parts(r['weather_storage_assets']['geometry']).items()})
    context={n:m for n,m in context.items() if not n.endswith('_text')}
    def intersections(shapes,obstacles,exclude=None):
        hits=[]
        for n,m in shapes.items():
            for q,b in obstacles.items():
                if q==exclude:continue
                v=overlap(m,b)
                if not np.isfinite(v) or abs(v)>.001:hits.append(dict(tool=n,part=q,volume_mm3=v))
        return hits
    def placed(parts,matrix):
        out={n:m.copy() for n,m in parts.items()}
        for m in out.values():m.apply_transform(matrix)
        return out
    u30=r['u30_assets'];logger_origin=np.asarray(station['selected_layout']['logger_origin_m']);opened=context.copy()
    for i,axis in enumerate(u30['latch_axes_m'],1):
        name='u30__latch_clasp_'+str(i);hits=[]
        for angle in [0,.1,.2,.5,1,2,3,4,5,10,20,30,45,60,75,90]:
            moving={name:rotated(context[name],np.asarray(axis)+logger_origin,angle)}
            hits+=intersections(moving,context,name)
        check('sampled_complete_station_clasp_release_'+str(i),not hits,intersections=hits)
        opened[name]=rotated(context[name],np.asarray(axis)+logger_origin,90)
    axis=np.asarray(u30['hinge_axis_m'])+logger_origin;hits=[]
    for angle in [0,.1,.2,.5,1,2,3,4]+list(range(5,111,5)):
        hits+=intersections({'door':rotated(context['u30__hinged_door'],axis,-angle)},opened,'u30__hinged_door')
    check('sampled_complete_station_door_opening',not hits,intersections=hits)
    opened['u30__hinged_door']=rotated(context['u30__hinged_door'],axis,-110)
    contexts={'closed':context,'open':opened}
    tool_ref=r['mast_driver_assets']['geometry'];tool={n:m for n,m in load_parts(tool_ref).items() if not n.endswith('_text')}
    socket=cylinder_x(.00925,0,.055)
    inner=trimesh.creation.cylinder(.00639,.0255,sections=192)
    inner.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));inner.apply_translation([.01265,0,0])
    socket=trimesh.boolean.difference([socket,inner],engine='manifold')
    envelopes={'socket':socket,'shaft':cylinder_x(.00375,.035,.145),'grip':cylinder_x(.0205,.125,.266)}
    sections=[('socket',.00925,0,.035),('shaft',.00375,.035,.125),('grip',.0205,.125,.246)]
    for p in r['mast_driver_checks']['tool_poses']:
        name=p['nut'];matrix=np.asarray(p['tool_transform']);matrix[:3,3]+=logger_origin
        if name==r['u30_ground_assets']['nut_adjustment']['source_part']:matrix[:3,3]+=r['u30_ground_assets']['nut_adjustment']['translation_m']
        lower=name.startswith('mount_1');side=-1 if name.endswith('left') else 1
        offsets=([[0,-.020,0],[0,-.020,-.010],[side*.040,-.020,-.010],[side*.040,-.020,-.040],[side*.040,-.120,-.040]] if lower
                 else [[0,-.020,0],[0,-.020,.025],[0,-.120,.025]])
        for state,obstacles in contexts.items():
            hits=intersections(placed(tool,matrix),obstacles)
            check('complete_driver_fit_'+name+'_'+state,not hits,intersections=hits)
            hits=intersections(placed(envelopes,matrix),obstacles,'u30__'+name)
            check('continuous_turn_and_20mm_axial_space_'+name+'_'+state,not hits,intersections=hits,excluded_driven_nut='u30__'+name)
            for i,(a,b) in enumerate(zip(offsets[:-1],offsets[1:])):
                bounds={}
                for key,radius,start,end in sections:
                    bound=cylinder_x(radius,start,end);bound.apply_transform(matrix);bound.apply_translation(a)
                    moved=bound.copy();moved.apply_translation(np.asarray(b)-a)
                    bounds[key]=trimesh.util.concatenate([bound,moved]).convex_hull
                hits=intersections(bounds,obstacles)
                check('detached_clearance_region_'+name+'_'+state+'_'+str(i),not hits,intersections=hits,
                      from_offset_m=a,to_offset_m=b,scope='Circumscribed complete-tool solid union; all fixed parts retained. Not an executed robot trajectory.')
        poses.append(dict(id=name,tool_geometry=tool_ref,tool_to_station=matrix.tolist(),
            target_part='u30__'+name,detached_clearance_region_offsets_m=offsets))
    # The selected ordinary SW7 driver must also clear the installed leads,
    # adapters, ties and full RS3 assembly, rather than an isolated clamp.
    ref=r['nut_driver_assets']['geometry'];tool={n:m for n,m in load_parts(ref).items() if not n.endswith('_text')}
    rs=next(p for p in station['rigid_placements'] if p['part']=='rs3__slotted_hex_worm_screw')
    matrix=np.asarray(rs['source_to_station'])@np.asarray(r['nut_driver_checks']['tool_transform'])
    hits=intersections(placed(tool,matrix),context)
    check('complete_SW7_driver_fit_installed_RS3',not hits,intersections=hits)
    worst=r['nut_driver_assets']['alternative_literal_inch_socket_diameter_m']/2
    bounds={n:cylinder_x(rad,start,end+.100) for n,rad,start,end in [('socket',worst,0,.032),('shaft',.00275,.032,.125),('grip',.018,.125,.238)]}
    hits=intersections(placed(bounds,matrix),context,'rs3__slotted_hex_worm_screw')
    check('complete_SW7_turn_and_100mm_axial_space',not hits,intersections=hits,
          excluded_driven_screw='rs3__slotted_hex_worm_screw',source_conflict_outer_diameter_m=2*worst)
    poses.append(dict(id='rs3_clamp',tool_geometry=ref,tool_to_station=matrix.tolist(),target_part='rs3__slotted_hex_worm_screw'))
    weather=json.loads((HERE/'weather_assets.json').read_text());probe=next(x for x in weather['items'] if x['id']=='onset_sthb_m002')
    wind=json.loads((HERE/'wind_lead_assets.json').read_text());bad=network_routes(station,probe,wind,clear_mount_driver=False)[1]
    old=cable_mesh(bad['points_m'],bad['radius_m']);pose=next(p for p in poses if p['id']=='mount_1_nut_right')
    steel=load_parts(pose['tool_geometry'])['steel_shaft_and_blind_socket'];steel.apply_transform(pose['tool_to_station']);v=overlap(steel,old)
    check('negative_prior_wind_groove_blocks_actual_driver',v>10,overlap_mm3=v,prior_channel_plug='unused_channel_plug_6')
    check('no_manipulation_or_owner_credit',station['owner_acceptance'] is None and not station['robot_use_qualified'])
    refs=[Path(__file__),HERE/'check_nut_driver.py',HERE/'check_u30.py',HERE/'check_weather_assets.py',HERE/'weather_station_routes.py',HERE/'weather_assets.json',HERE/'wind_lead_assets.json']+[HERE/(name+'.json') for name in names]
    result=dict(schema_version=1,passed=True,checks=checks,tool_poses=poses,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Complete ordinary tools against installed station and storage geometry, plus sampled enclosure articulation. All selected tool solids and flexible leads remain rigid. Hand access, grip, force, flexible-body response and execution are not qualified.',
        torso_and_hand_space_qualified=False,torque_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_service_checks.json',result);print(json.dumps(dict(passed=True,checks=len(checks),tool_poses=len(poses))))


if __name__=='__main__':build()
