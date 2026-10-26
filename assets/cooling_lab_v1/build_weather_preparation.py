"""Manual-supported low upper-mast inspection, not an executed assembly.

The tripod guide places the upper mast upright beside the base, temporarily
tied to a leg and a brace. Integral sensor leads remain present at full length.
This partial inspection explicitly lists components outside its context; it
is not a complete campaign state or an authorization to develop manipulation.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.optimize import brentq
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from check_weather_assets import load_parts
from build_weather_assets import cable_mesh
from build_weather_station import pose,rotation
from build_cable_ties import installed_tie
from weather_station_retention import slab_projection,enclosing_circle
from weather_station_routes import bezier,joined,length


def build():
    names=['weather_station_assets','weather_assets','wind_lead_assets','ordinary_tools',
           'cable_tie_assets','long_cable_tie_assets']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names}
    station=r['weather_station_assets'];site=np.asarray(station['station_origin_world_m'])
    source=load_parts(station['geometry'])
    for m in source.values():m.apply_translation(-site)
    g=Geometry();parts={};placements=[];dispositions=[]
    offset=np.array([.220,.043,-1.050]);stage=pose(rotation(-30,[0,0,1]),offset)
    def add(identity,mesh,matrix,role):
        m=mesh.copy();m.apply_transform(matrix);parts[identity]=m
        g.scene.add_geometry(m,node_name=identity,geom_name=identity)
        g.parts.append(dict(id=identity,role=role,bounds_m=m.bounds.tolist()))
        return m
    omitted_support=('guy_','turnbuckle_','s_hook_','mast_splice_')
    plug_groups=('temperature_plug__','wind_plug__')
    for n,m in source.items():
        if n.startswith(plug_groups) or n in ['routed__temperature_network_lead','routed__wind_network_lead']:
            dispositions.append(dict(part=n,state='relocated_free_end_or_rerouted_integral_lead'));continue
        if n.startswith(('u30__','logger_ground__')) or (n.startswith('support__') and any(s in n for s in omitted_support)):
            dispositions.append(dict(part=n,state='outside_partial_inspection',reason='Final logger, splice and guy installation are not represented by this low-mast context.'));continue
        fixed=n.startswith('support__') and n not in ['support__upper_mast_with_dimple_and_crossarm_holes','support__slotted_flush_mast_plug']
        matrix=np.eye(4) if fixed else stage
        add(n,m,matrix,'fixed_base' if fixed else 'lowered_upper_mast_component')
        placements.append(dict(part=n,source_geometry=station['geometry']['path'],source_part=n,source_to_preparation=(matrix@pose(translation=-site)).tolist()))
    tray=next(x for x in r['ordinary_tools']['items'] if x['id']=='buerkle_4208_0022')
    tray_origin=np.array([.280,-.150,0.]);tray_matrix=pose(translation=tray_origin)
    for n,m in load_parts(tray['geometry']).items():
        identity='free_plug_tray__'+n;add(identity,m,tray_matrix,'ordinary_catalog_tray')
        placements.append(dict(part=identity,source_geometry=tray['geometry']['path'],source_part=n,source_to_preparation=tray_matrix.tolist()))
    probe=next(x for x in r['weather_assets']['items'] if x['id']=='onset_sthb_m002')
    cable_visual=source['routed__temperature_network_lead'].visual
    free_plugs=[];leads=[]
    for prefix,record,entry_x in [('temperature',probe,.200),('wind',r['wind_lead_assets'],.330)]:
        stock=load_parts(record['geometry']);entry=np.asarray(record['modular_plug']['cable_entry_m'])
        selected={n:m for n,m in stock.items() if n=='modular_plug_body_and_latch' or n.startswith('plug_contact_')}
        R=rotation(-90,[0,0,1]);lowest=min((m.vertices@R.T)[:,2].min() for m in selected.values())
        translation=np.array([entry_x,-.140,.0012-lowest])-np.r_[R@entry][:3]*[1,1,0]
        matrix=pose(R,translation);end=trimesh.transform_points([entry],matrix)[0]
        for n,m in selected.items():
            identity=prefix+'_plug__'+n;add(identity,m,matrix,'original_free_modular_connector')
            placements.append(dict(part=identity,source_geometry=record['geometry']['path'],source_part=n,source_to_preparation=matrix.tolist()))
        free_plugs.append(dict(id=prefix,source_geometry=record['geometry'],source_to_preparation=matrix.tolist(),cable_entry_m=end.tolist(),support='free_plug_tray__formed_tray'))
        previous=next(x for x in station['routed_leads'] if x['id']==prefix+'_network_lead')
        approach=trimesh.transform_points(np.asarray(previous['points_m'][:121]),stage)
        # Keep the adapter exit and both existing mast-tie sections unchanged.
        # Below those sections, a continuous free lead enters the tray above
        # its rim and terminates at the real horizontal connector entry.
        via=np.array([.120 if prefix=='temperature' else entry_x,-.065,.075])
        def candidate(handle):
            return joined(approach,bezier(approach[-1],via,[0,0,-1],[0,-1,0],(.025,handle)),
                bezier(via,end,[0,-1,0],[0,-1,0],(.035,.025)))
        h=brentq(lambda h:length(candidate(h))-.5,.001,.35,xtol=1e-13)
        path=candidate(h);identity='routed__'+previous['id'];mesh=cable_mesh(path,.0015,[[0,0,-1],[0,-1,0]]);mesh.visual=cable_visual.copy()
        add(identity,mesh,np.eye(4),'authored_full_length_free_network_lead')
        leads.append(dict(id=previous['id'],points_m=path.tolist(),endpoints_m=path[[0,-1]].tolist(),radius_m=.0015,length_m=.5,
            solved_handle_m=float(h),scope='Full source length and original adapter exit; authored static free-end shape, not settled cable physics.'))
    ties=[]
    for identity,z,other,product,parameters,bound in [
        ('temporary_leg',.540,'support__leg_3','111-01975',{},.080),
        ('temporary_brace',.425,'support__leg_brace_3','111-05440',dict(stock_length=.390,head_length=.0072,head_width=.0081,width=.0046,thickness=.0014),.110)]:
        matrix=pose(rotation(-90,[0,0,1]),[0,0,z]);selected=['support__upper_mast_with_dimple_and_crossarm_holes',other]
        projected=np.vstack([slab_projection(parts[n],matrix) for n in selected]);circle=enclosing_circle(projected)
        assert circle['diameter_m']<=bound,(identity,circle)
        mesh,detail=installed_tie(projected,trim=False,**parameters)
        stock=r['cable_tie_assets' if product=='111-01975' else 'long_cable_tie_assets']
        mesh.visual=next(iter(load_parts(stock['geometry']).values())).visual.copy()
        name='temporary__'+identity;add(name,mesh,matrix,'ordinary_uncut_temporary_tie')
        ties.append(dict(id=identity,part=name,product='HellermannTyton '+product,plane_to_preparation=matrix.tolist(),
            enclosed_parts=selected,containing_circle=circle,conservative_bundle_diameter_m=bound,**detail))
    geometry=g.export('weather_preparation_candidate')
    refs=[Path(__file__),HERE/'build_cable_ties.py',HERE/'weather_station_retention.py',HERE/'weather_station_routes.py',HERE/'build_weather_assets.py',HERE/'build_weather_station.py',HERE/'check_weather_assets.py',HERE/'geometry_tools.py']+[HERE/(n+'.json') for n in names]
    record=dict(schema_version=1,status='partial_low_mast_inspection_not_assembly_plan',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        station_origin_world_m=site.tolist(),upper_cluster_translation_m=offset.tolist(),upper_cluster_to_preparation=stage.tolist(),rigid_placements=placements,
        original_station_component_dispositions=dispositions,routed_leads=leads,free_plugs=free_plugs,temporary_ties=ties,
        tray_origin_m=tray_origin.tolist(),reuse_candidate_tray_identity='weather_removed_parts_tray',
        source_basis=dict(url='https://www.onsetcomp.com/sites/default/files/resources-documents/12317-B%20MAN-TRIPOD.pdf',
            sha256='60ecc89d71d541b316ae193b1e6519a8693a71b73baee478a7cbbc41e6d4862e',
            pages=[7,8],statement='The guide temporarily holds the upper mast upright beside the base with ties at one leg and one brace; it recommends two people for joining the mast sections.'),
        inferences=['Selected lower-mast position, -30 degree temporary azimuth, ordinary replacement tie sizes and free network lead/tray layout are authored hypotheses. Final north alignment is not established in this temporary view.',
            'This preserves complete sensor leads and mechanical source solids, but does not establish the actual installation order.',
            'Temporary ties retain their full tails. A later cut, support, lift and mast join are not performed or qualified.'],
        limitations=['Partial asset inspection: omitted final-state parts have identities but no claimed physical storage placement in this view.',
            'No tie preload, friction, strength, soil support, payload, stability, two-hand handling or single-robot mast joining is qualified.'],
        staged_in_lab=False,initial_stock_credit=False,installation_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'weather_preparation_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],temporary_ties=len(ties))))


if __name__=='__main__':build()
