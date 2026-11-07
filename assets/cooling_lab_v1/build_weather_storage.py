"""Ordinary cart/trays retain the station's real removed plugs and cutoffs.

This is a proposed final storage state, not an executed cleanup or an initial
inventory. The existing reusable cart is relocated here in an alternative
inspection scene; it must not be duplicated in the lab inventory.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts


def build():
    station=json.loads((HERE/'weather_station_assets.json').read_text())
    supplies=json.loads((HERE/'supplies.json').read_text())
    ordinary=json.loads((HERE/'ordinary_tools.json').read_text())
    u30=json.loads((HERE/'u30_assets.json').read_text())
    ties=json.loads((HERE/'cable_tie_assets.json').read_text())
    cart=next(x for x in supplies['items'] if x['id']=='rubbermaid_1997206')
    tray=next(x for x in ordinary['items'] if x['id']=='buerkle_4208_0022')
    cart_origin=np.array([1.05,-1.30,0.]);g=Geometry();placements=[]
    def add(name,mesh,matrix,role):
        m=mesh.copy();m.apply_transform(matrix)
        g.scene.add_geometry(m,node_name=name,geom_name=name)
        g.parts.append(dict(id=name,role=role,bounds_m=m.bounds.tolist()))
        return m
    def translate(point):
        m=np.eye(4);m[:3,3]=point;return m
    def source_group(group,ref,origin):
        matrix=translate(origin)
        for name,mesh in load_parts(ref).items():
            identity=group+'__'+name;add(identity,mesh,matrix,'existing_catalog_reference')
            placements.append(dict(part=identity,source_geometry=ref['path'],source_part=name,source_to_storage=matrix.tolist()))
    source_group('cart',cart['geometry'],cart_origin)
    tray_origins={}
    for kind,y in [('cutoffs',-.105),('plugs',.105)]:
        origin=cart_origin+[.08,y,.772];tray_origins[kind]=origin
        source_group(kind+'_tray',tray['geometry'],origin)
    stock=next(iter(load_parts(ties['geometry']).values()));cutoffs=[]
    flat=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    for i,tie in enumerate(station['retention_ties']):
        retained=tie['retained_developed_length_m'];length=tie['cutoff_developed_length_m']
        plane_x=retained-.0035
        cutter=trimesh.creation.box([length+.001,.03,.03]);cutter.apply_translation([plane_x+(length+.001)/2,-.0006,0])
        mesh=trimesh.boolean.intersection([stock,cutter],engine='manifold');mesh.visual=stock.visual.copy()
        assert mesh.is_volume and len(mesh.split())==1,tie['id']
        matrix=np.eye(4);matrix[:3,:3]=flat
        # The original wide strap face lies on the tray's actual 1.2 mm floor.
        transformed=mesh.copy();transformed.apply_transform(matrix)
        target=tray_origins['cutoffs']+[-length/2,-.052+i*.008,.0012]
        matrix[:3,3]=target-[transformed.bounds[0,0],0,transformed.bounds[0,2]]
        name='cutoff__'+tie['id'];add(name,mesh,matrix,'accounted_actual_stock_tail')
        cutoffs.append(dict(part=name,source_tie=tie['id'],source_stock_geometry=ties['geometry'],
            source_cut_plane_x_m=plane_x,source_to_storage=matrix.tolist(),
            developed_length_m=length,retained_developed_length_m=retained,
            storage_container='cutoffs_tray__formed_tray',physical_state='static_flattened_cut_tail_hypothesis'))
    plugs=[];u30_parts=load_parts(u30['geometry'])
    for i,plug in enumerate(station['detached_channel_plugs']):
        name=plug['source_part'];mesh=u30_parts[name]
        matrix=trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0])
        lying=mesh.copy();lying.apply_transform(matrix);centre=lying.bounds.mean(axis=0)
        target=tray_origins['plugs']+[-.050+i*.050,0,.0012]
        matrix[:3,3]=target-[centre[0],centre[1],lying.bounds[0,2]]
        identity='removed__'+name;add(identity,mesh,matrix,'removed_original_logger_plug')
        placements.append(dict(part=identity,source_geometry=u30['geometry']['path'],source_part=name,source_to_storage=matrix.tolist()))
        plugs.append(dict(part=identity,source_part=name,storage_container='plugs_tray__formed_tray'))
    geometry=g.export('weather_station_storage_candidate')
    refs=[Path(__file__),HERE/'weather_station_assets.json',HERE/'supplies.json',HERE/'supply_sources.json',
        HERE/'ordinary_tools.json',HERE/'ordinary_tools_sources.json',HERE/'u30_assets.json',HERE/'cable_tie_assets.json',
        HERE/'check_weather_assets.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_alternative_final_storage_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        coordinates='Metres, +Z up, relative to weather-station mast; add station_origin_world_m for the site.',
        station_origin_world_m=station['station_origin_world_m'],cart_origin_m=cart_origin.tolist(),
        rigid_placements=placements,cutoffs=cutoffs,removed_plugs=plugs,
        tray_origins_m={k:v.tolist() for k,v in tray_origins.items()},
        inventory_intent=dict(reuse_existing_cart_instance='utility_cart',
            additional_tray_candidates=['weather_cutoff_tray','weather_removed_parts_tray'],
            existing_lab_trays_reassigned=False,initial_stock_credit=False),
        scope='Fourteen actual cut tails and three original removed plugs in two ordinary catalog trays on the existing cart. Static final-state placement only; no cleanup, severing, transport, settling, wind or hand access is qualified.',
        staged_in_lab=False,initial_stock_credit=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_storage_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],cutoffs=len(cutoffs),removed_plugs=len(plugs))))


if __name__=='__main__':build()
