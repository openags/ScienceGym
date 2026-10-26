"""Give remaining wire and unused kit contents actual support on the same cart."""
import json
from pathlib import Path
import numpy as np
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts
from build_weather_anchoring import coil
from build_weather_assets import cable_mesh


def build():
    names=['weather_storage_assets','weather_support_assets','weather_anchoring_assets',
        'wind_kit_assets','wind_kit_checks','weather_assets','weather_asset_checks','ordinary_tools']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names}
    storage=r['weather_storage_assets'];origin=np.array(storage['cart_origin_m']);g=Geometry();placements=[]
    def add(identity,mesh,matrix,role):
        m=mesh.copy();m.apply_transform(matrix);g.scene.add_geometry(m,node_name=identity,geom_name=identity)
        g.parts.append(dict(id=identity,role=role,bounds_m=m.bounds.tolist()));return m
    def translate(p):
        t=np.eye(4);t[:3,3]=p;return t
    def source(identity,ref,name,matrix):
        mesh=load_parts(ref)[name];add(identity,mesh,matrix,'source_preserved_unused_kit_component')
        placements.append(dict(part=identity,source_geometry=ref['path'],source_part=name,source_to_storage=matrix.tolist()))
    wires=[];stock=r['weather_anchoring_assets'];wire_parts=load_parts(stock['geometry'])
    for identity,balance_name,turns,offset in [
        ('guy_wire_remainder','wire_stock_balance',6,[-.21,0,.1835]),
        ('ground_wire_remainder','ground_wire_stock_balance',5,[.09,-.115,.1835])]:
        balance=r['weather_support_assets'][balance_name];src=next(w for w in stock['stored_wires'] if w['id']==balance['source_stock'])
        length=balance['remaining_length_m'];points=coil(length,turns,origin+offset)
        mesh=cable_mesh(points,src['radius_m']);mesh.visual=wire_parts[src['id']].visual.copy()
        add(identity,mesh,np.eye(4),'source_length_remaining_wire_static_spiral')
        wires.append(dict(id=identity,part=identity,source_stock_id=src['id'],source_total_length_m=balance['source_length_m'],
            installed_cut_lengths_m=balance['cuts_m'],remaining_length_m=length,points_m=points.tolist(),radius_m=src['radius_m'],
            storage_container='cart__lower_shelf',selected_turns=turns,material_loss_m=balance['material_loss_m'],
            scope='Authored flat remainder shape; length conservation only, not a cut or cable-bending simulation.'))
    tray=next(x for x in r['ordinary_tools']['items'] if x['id']=='buerkle_4208_0022')
    tray_origin=origin+[.21,.10,.182];tray_parts=load_parts(tray['geometry'])
    for n in tray_parts:source('kit_tray__'+n,tray['geometry'],n,translate(tray_origin))
    contents=[];wind=r['wind_kit_assets'];wind_parts=load_parts(wind['geometry'])
    for n,offset in [('optional_wood_lag_1',[-.075,.018,.0012]),('optional_wood_lag_2',[-.075,.042,.0012]),('supplied_0050_hex_key_candidate',[.070,.062,.0012])]:
        mesh=wind_parts[n];bottom=mesh.bounds[0,2];base=[mesh.bounds[0,0],mesh.bounds.mean(axis=0)[1],bottom]
        identity='wind_kit__'+n;source(identity,wind['geometry'],n,translate(tray_origin+offset-base))
        contents.append(dict(part=identity,kit='weather_wind',storage_container='kit_tray__formed_tray',source_part=n))
    shield=next(x for x in r['weather_assets']['items'] if x['id']=='onset_rs3');shield_parts=load_parts(shield['geometry'])
    for i in range(1,7):
        members=['loose_tie_'+str(i)+'_'+s for s in ['strap','head']]
        bounds=np.array([shield_parts[n].bounds for n in members]);lo=bounds[:,0].min(axis=0);hi=bounds[:,1].max(axis=0)
        matrix=translate(tray_origin+[-.073,-.074+(i-1)*.009,.0012]-[lo[0],(lo[1]+hi[1])/2,lo[2]])
        for n in members:
            identity='rs3_kit__'+n;source(identity,shield['geometry'],n,matrix)
            contents.append(dict(part=identity,kit='weather_radiation_shield',selected_tie=i,storage_container='kit_tray__formed_tray',source_part=n))
    for i in range(1,3):
        n='optional_wall_screw_'+str(i);mesh=shield_parts[n];base=[mesh.bounds.mean(axis=0)[0],mesh.bounds.mean(axis=0)[1],mesh.bounds[0,2]]
        identity='rs3_kit__'+n;source(identity,shield['geometry'],n,translate(tray_origin+[.107+(i-1)*.018,-.040,.0012]-base))
        contents.append(dict(part=identity,kit='weather_radiation_shield',storage_container='kit_tray__formed_tray',source_part=n))
    geometry=g.export('weather_remainders_candidate')
    refs=[Path(__file__),HERE/'build_weather_anchoring.py',HERE/'build_weather_assets.py',HERE/'check_weather_assets.py',HERE/'geometry_tools.py']+[HERE/(n+'.json') for n in names]
    record=dict(schema_version=1,status='unaccepted_wire_and_unused_kit_storage_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        station_origin_world_m=storage['station_origin_world_m'],cart_identity='utility_cart',cart_origin_m=origin.tolist(),
        coordinates='Metres, Z up, relative to the same weather mast; add station_origin_world_m.',
        wires=wires,rigid_placements=placements,unused_kit_contents=contents,tray_origin_m=tray_origin.tolist(),
        additional_tray_identity='weather_unused_kit_tray',
        supplied_rs3_clamp_disposition='Earlier generic clamp geometry is a superseded reference; the selected ordinary NORMA replacement is already installed. It is not a second physical clamp.',
        source_kit_inferences=shield['kit_dimension_inferences'],
        limitations=['Selected source kit shapes are retained, including inferred RS3 ties and optional screws; unknown manufacturer identities are not resolved.',
            'The two temporary upper-mast ties and their removal/cut disposition remain outside this final reference.',
            'Stored wire shape, hand access, bending force, cart motion, soil retention and cleanup remain unqualified.'],
        initial_stock_credit=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_remainders_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],wire_remainders=len(wires),unused_kit_parts=len(contents))))


if __name__=='__main__':build()
