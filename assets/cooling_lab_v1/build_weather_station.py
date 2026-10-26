"""Work-in-progress station integration from unchanged reviewed component solids.

Source-preserving rigid placement and authored static cable/retention shapes.
The incomplete station is not laboratory inventory, assembly or a robot task.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts
from build_weather_assets import cable_mesh
from weather_station_routes import sensor_routes,network_routes
from weather_station_retention import station_ties


def pose(rotation=None,translation=(0,0,0)):
    p=np.eye(4)
    if rotation is not None:p[:3,:3]=rotation
    p[:3,3]=translation;return p


def rotation(degrees,axis):return trimesh.transformations.rotation_matrix(np.deg2rad(degrees),axis)[:3,:3]


def build():
    names=['weather_support_assets','weather_site_review','u30_assets','u30_checks','hose_clamp_checks','hose_clamp_assets','weather_assets','wind_sensor_assets','wind_lead_assets','cable_tie_assets']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names}
    site=np.r_[r['weather_site_review']['mast_center_xy_m'],0.];g=Geometry();placements=[]
    def add(group,ref,matrix,select=lambda n:True):
        for name,m in load_parts(ref).items():
            if not select(name):continue
            local=m.copy();local.apply_transform(matrix);identity=group+'__'+name
            # Preserve local float32 vertices even though the site is 20 m
            # from the laboratory origin. World translation stays a matrix.
            g.scene.add_geometry(local,node_name=identity,geom_name=identity,transform=pose(translation=site))
            g.parts.append(dict(id=identity,role='incomplete_station_static_reference',bounds_m=(local.bounds+site).tolist()))
            placements.append(dict(part=identity,group=group,source_geometry=ref['path'],source_part=name,source_to_station=matrix.tolist()))
    # Preserve north-facing wind alignment. Rotating the complete unaccepted
    # tripod/anchoring layout separates its guy lines from the wind arm.
    support_rotation=rotation(30,[0,0,1])
    add('support',r['weather_support_assets']['geometry'],pose(support_rotation,-support_rotation@site))
    logger_origin=np.array([0,-.147,1.1003]);logger=pose(translation=logger_origin)
    removed_plugs={'unused_channel_plug_2','unused_channel_plug_6'}
    add('u30',r['u30_assets']['geometry'],logger,lambda n:n not in removed_plugs)
    # Source manual places the lower logger U-bolt just above the splice.
    # The exact heights and azimuths here remain selected layout candidates.
    rs_rotation=rotation(180,[0,0,1]);rs=pose(rs_rotation,[0,0,1.4])
    add('rs3',r['hose_clamp_checks']['fit_geometry'],rs,lambda n:n!='isolated_mast_segment')
    wind_rotation=rotation(90,[0,0,1]);wind=pose(wind_rotation,[0,.0255,1.6])
    add('wind',r['wind_sensor_assets']['geometry'],wind)
    weather={i['id']:i for i in r['weather_assets']['items']};probe=weather['onset_sthb_m002']
    head_stored=pose(rotation(-90,[0,1,0]),[.015,0,.005])
    rs3_origin=np.asarray(r['hose_clamp_assets']['installed_context']['rs3_origin_m'])
    head=rs@pose(translation=rs3_origin)@np.linalg.inv(head_stored)
    head_names={'probe_receptacle','rh_membrane_cap','sensor_board_envelope','probe_strain_relief_candidate'}
    add('temperature_head',probe['geometry'],head,lambda n:n in head_names)
    upright=rotation(-90,[0,1,0])
    temp_adapter_origin=np.array([-.0323,0,1.39]);temp_stored=np.array([-.100,.150,.007])
    temp_rotation=rotation(-90,[0,0,1])@upright
    temp_adapter=pose(temp_rotation,temp_adapter_origin-temp_rotation@temp_stored)
    add('temperature_adapter',probe['geometry'],temp_adapter,lambda n:n=='inline_adapter_candidate')
    wind_adapter_origin=np.array([.0353,0,1.36]);wind_stored=np.array(r['wind_lead_assets']['adapter']['centre_m'])
    wind_adapter_rotation=rotation(-90,[0,0,1])@upright
    wind_adapter=pose(wind_adapter_rotation,wind_adapter_origin-wind_adapter_rotation@wind_stored)
    add('wind_adapter',r['wind_lead_assets']['geometry'],wind_adapter,lambda n:n.startswith('wind_adapter_'))
    plug_filter=lambda n:n=='modular_plug_body_and_latch' or n.startswith('plug_contact_')
    # Two selected actual plugs occupy separate jacks. Their static cable
    # shapes below do not establish electrical connection or insertion.
    temp_plug=logger@np.asarray(r['u30_checks']['plug_transforms'][0])
    add('temperature_plug',probe['geometry'],temp_plug,plug_filter)
    R=np.array([[0,1,0],[0,0,1],[1,0,0]])
    wind_entry=np.asarray(r['wind_lead_assets']['modular_plug']['cable_entry_m'])
    wind_plug=logger@pose(R,np.array([.036,.030,.067])-R@wind_entry)
    add('wind_plug',r['wind_lead_assets']['geometry'],wind_plug,plug_filter)
    layout=dict(logger_origin_m=logger_origin.tolist(),support_azimuth_rotation_deg=30,
        guy_azimuths_deg=[120,240,0],north_axis=[0,1,0],rs3_clamp_height_m=1.4,wind_origin_m=[0,.0255,1.6],
        temperature_adapter_centre_m=temp_adapter_origin.tolist(),wind_adapter_centre_m=wind_adapter_origin.tolist())
    transforms=dict(temperature_head=head.tolist(),temperature_adapter=temp_adapter.tolist(),
        temperature_plug=temp_plug.tolist(),wind=wind.tolist(),wind_adapter=wind_adapter.tolist(),wind_plug=wind_plug.tolist())
    description=dict(selected_layout=layout,source_transforms=transforms)
    leads=sensor_routes(description,probe,r['wind_lead_assets'])+network_routes(description,probe,r['wind_lead_assets'])
    assert {q['removed_channel_plug'] for q in leads if 'removed_channel_plug' in q}==removed_plugs
    cable_visual=load_parts(probe['geometry'])['probe_lead'].visual
    for lead in leads:
        m=cable_mesh(lead['points_m'],lead['radius_m']);m.visual=cable_visual.copy();name='routed__'+lead['id']
        g.scene.add_geometry(m,node_name=name,geom_name=name,transform=pose(translation=site))
        g.parts.append(dict(id=name,role='authored_installed_lead_shape',bounds_m=(m.bounds+site).tolist()))
    ties=[];tie_visual=next(iter(load_parts(r['cable_tie_assets']['geometry']).values())).visual
    for identity,m,detail in station_ties(g.scene.geometry,leads):
        assert m.is_volume and len(m.split())==1,identity
        assert detail['containing_circle']['diameter_m']<=.080,identity
        m.visual=tie_visual.copy();name='retention__'+identity
        g.scene.add_geometry(m,node_name=name,geom_name=name,transform=pose(translation=site))
        g.parts.append(dict(id=name,role='ordinary_static_cut_cable_tie',bounds_m=(m.bounds+site).tolist()))
        ties.append(dict(id=identity,part=name,product='HellermannTyton 111-01975',**detail,
            cutoff_disposition='Retained length accounted for; physical cutoff storage still required.'))
    geometry=g.export('weather_station_integration_candidate')
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'geometry_tools.py',HERE/'weather_station_routes.py',
        HERE/'build_weather_assets.py',HERE/'build_wind_sensor.py',HERE/'build_cable_ties.py',HERE/'weather_station_retention.py']+[HERE/(n+'.json') for n in names]
    record=dict(schema_version=1,status='incomplete_station_integration',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        station_origin_world_m=site.tolist(),rigid_placements=placements,
        selected_layout=layout,source_transforms=transforms,routed_leads=leads,retention_ties=ties,
        detached_channel_plugs=[dict(source_geometry=r['u30_assets']['geometry']['path'],source_part=n,
            disposition='Removed in this alternative reference; tracked storage placement still required') for n in sorted(removed_plugs)],
        missing=['Physical storage for the cable-tie cutoffs',
            'Tracked storage location for the two removed channel plugs',
            'Logger grounding lead and ordinary terminal connection',
            'Cross-component checks, complete-tool and humanoid space, main-scene inventory integration'],
        scope='Integration work in progress. Source solids and actual lead lengths are retained; routed cable shapes have no stiffness, gravity settling or retention qualification.',
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,electrical_qualified=False,
        structural_load_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_station_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],status=record['status'])))


if __name__=='__main__':build()
