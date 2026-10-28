"""Inferred supplied U30 ground pigtail, constrained by ordinary terminal drawings."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from scipy.optimize import brentq
import trimesh
from geometry_tools import Geometry,HERE,ROOT,sha,write_json
from build_supplies import solid,export_review
from build_u30 import box,cyl
from build_weather_assets import cable_mesh
from weather_station_routes import joined,bezier,length

BLUE=[42,87,135];TIN=[180,188,191];BRASS=[171,170,150]


def flag_parts(g):
    """Front at Y=0, tab along +Y, wire exits towards -X; dimensions in mm."""
    profile=[(-3.3,-.85),(3.3,-.85),(3.3,1.0),(2.0,1.6),(.7,1.0),(.9,.6),
             (2,.95),(2.9,.65),(2.9,-.45),(-2.9,-.45),(-2.9,.65),(-2,.95),
             (-.9,.6),(-.7,1.0),(-2,1.6),(-3.3,1.0)]
    curled=cq.Workplane('XZ').polyline(profile).close().extrude(10.5).val().translate((0,-.2,0))
    back=box((6.6,1.2,2.4),(0,-11.1,.25))
    barrel=cyl(1.9,8,(-7.3,-12.2,0),(1,0,0)).cut(cyl(.78,8.2,(-7.4,-12.2,0),(1,0,0)))
    contact=curled.fuse(back).fuse(barrel)
    contact=contact.cut(box((5.0,10.7,.94),(0,-5.25,0)))
    contact=contact.cut(cyl(.78,8.3,(-7.4,-12.2,0),(1,0,0)))
    # The housing opening is distinct from the inner metal contact throat.
    housing=cq.Workplane('XY').box(9.4,15.24,5.33).edges().fillet(.45).val().translate((0,-7.62,0))
    flare=cyl(3.04,6.13,(-10.03,-12.2,0),(1,0,0))
    housing=housing.fuse(flare)
    housing=housing.cut(box((7.0,11.8,3.2),(0,-5.8,.4)))
    housing=housing.cut(cyl(2.0,8.6,(-7.4,-12.2,0),(1,0,0)))
    housing=housing.cut(cyl(2.26,3.0,(-10.13,-12.2,0),(1,0,0)))
    solid(g,'flag_tin_brass_contact',contact,TIN,metal=.8,role='reference_constrained_inferred_factory_contact')
    solid(g,'flag_nylon_housing',housing,BLUE,role='reference_constrained_inferred_factory_housing')


def ring_parts(g):
    """Ring lies in XY; wire entry at Y=0 and hole center at Y=22.86 mm."""
    ring=cyl(5.84,.81,(0,22.86,0)).cut(cyl(4.32,1.1,(0,22.86,-.1)))
    neck=(cq.Workplane('XY').polyline([(-2,13),(-2,15),(-4.5,19),(4.5,19),(2,15),(2,13)]).close().extrude(.81).val())
    barrel=cyl(1.8,6.5,(0,7,1.8),(0,1,0)).cut(cyl(.78,6.7,(0,6.9,1.8),(0,1,0)))
    stamp=ring.fuse(neck).fuse(barrel).cut(cyl(4.32,1.1,(0,22.86,-.1)))
    sleeve=cyl(2.1,6.35,(0,5,1.8),(0,1,0)).cut(cyl(1.83,6.55,(0,4.9,1.8),(0,1,0)))
    housing=cyl(3.25,11.5,(0,0,1.8),(0,1,0))
    housing=housing.cut(cyl(2.54,5.1,(0,-.1,1.8),(0,1,0))).cut(cyl(2.15,6.7,(0,4.9,1.8),(0,1,0)))
    solid(g,'ring_tin_copper_stamp',stamp,TIN,metal=.8,role='source_sized_ring_reference')
    solid(g,'ring_tin_brass_sleeve',sleeve,BRASS,metal=.8,role='inferred_factory_crimp_sleeve')
    solid(g,'ring_nylon_housing',housing,BLUE,role='inferred_factory_ring_housing')


def build():
    g=Geometry();flag_parts(g);ring_parts(g)
    origin=np.array([0.,-.147,1.1003]);flag_origin=origin+[-.057,.0259,.073]
    # Plate back face touches the existing washer; the nut shifts by the
    # actual ring thickness in the separate assembled reference.
    ring_origin=np.array([-.026162,-.0304,1.100-.02286])
    R=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    for name,m in g.scene.geometry.items():
        matrix=np.eye(4)
        if name.startswith('flag_'):matrix[:3,3]=flag_origin
        else:matrix[:3,:3]=R;matrix[:3,3]=ring_origin
        m.apply_transform(matrix)
    for p in g.parts:p['bounds_m']=g.scene.geometry[p['id']].bounds.tolist()
    start=flag_origin+[-.00133,-.0122,0] # selected stripped conductor tip
    port=flag_origin+[-.01003,-.0122,0]
    theta=np.linspace(0,np.pi/2,81);radius=.0055
    arc=port+np.column_stack([-radius*np.sin(theta),np.zeros(len(theta)),-radius*(1-np.cos(theta))])
    gland_x=-.018;gland_y=origin[1]+.029;inside=np.array([gland_x,gland_y,1.130])
    prefix=joined(np.linspace(start,port,41),arc,bezier(arc[-1],inside,[0,0,-1],[0,0,-1],(.018,.018)))
    ring_entry=ring_origin+R@np.array([0,0,.0018]);end=ring_origin+R@np.array([0,.01256,.0018])
    turn_radius=.012
    def candidate(turn_z):
        first=np.column_stack([np.full(len(theta),gland_x),gland_y+turn_radius*(1-np.cos(theta)),turn_z-turn_radius*np.sin(theta)])
        last=np.column_stack([np.full(len(theta),ring_entry[0]),ring_entry[1]-turn_radius+turn_radius*np.sin(theta),turn_z-turn_radius*np.cos(theta)])
        return joined(prefix,np.linspace(inside,[gland_x,gland_y,turn_z],151),first,
            bezier(first[-1],last[0],[0,1,0],[0,1,0],(.020,.020)),last,np.linspace(last[-1],end,101))
    turn_z=brentq(lambda z:length(candidate(z))-.400,.950,1.060,xtol=1e-13);path=candidate(turn_z)
    g.add('continuous_ground_conductor',cable_mesh(path,.0007),TIN,metal=.65,role='inferred_factory_ground_conductor')
    sleeve=cyl(1.9,23,(gland_x*1000,gland_y*1000,1102)).cut(cyl(.71,23.2,(gland_x*1000,gland_y*1000,1101.9)))
    solid(g,'black_gland_sleeve',sleeve,[24,25,26],role='source_required_inferred_thicker_black_section')
    geometry=export_review(g,'onset_u30_ground_lead_candidate')
    refs=[Path(__file__),HERE/'u30_ground_sources.json',HERE/'build_u30.py',HERE/'build_supplies.py',HERE/'build_weather_assets.py',HERE/'weather_station_routes.py',HERE/'geometry_tools.py']
    record=dict(schema_version=1,status='unaccepted_inferred_supplied_U30_ground_lead_candidate',geometry=geometry,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        selected_logger_origin_m=origin.tolist(),flag_origin_m=flag_origin.tolist(),ring_origin_m=ring_origin.tolist(),ring_rotation=R.tolist(),
        conductor=dict(id='logger_ground_lead',points_m=path.tolist(),radius_m=.0007,length_m=.400,measured_length_m=length(path),
            endpoints_m=path[[0,-1]].tolist(),source_length_known=False,source_wire_gauge_known=False,drip_lowest_z_m=float(path[:,2].min())),
        removed_channel_plug='unused_channel_plug_3',selected_gland_axis_m=[gland_x,gland_y],
        nut_adjustment=dict(source_part='mount_1_nut_left',translation_m=[0,-.00081,0],reason='Place the selected 0.81 mm ring stamping between existing nut and washer.'),
        scope='Static factory-accessory hypothesis with ordinary terminal dimensional references; Onset OEM identities are unknown. No crimping, electrical continuity, retention or robot task is simulated.',
        staged_in_lab=False,initial_stock_credit=False,electrical_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'u30_ground_assets.json',record);print(json.dumps(dict(parts=geometry['parts'],ground_length_m=length(path),minimum_z_m=float(path[:,2].min()))))


if __name__=='__main__':build()
