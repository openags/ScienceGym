"""External leads and source-shaped adapter for the wind sensor candidate.

This is authored geometry, not an Onset CAD export, cable simulation, connector
qualification or laboratory installation. The manual's conflicting 3 m and
12.2 m cable descriptions remain open in the source ledger.
"""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from geometry_tools import Geometry, HERE, ROOT, sha, write_json
from build_supplies import export_review, solid
from build_weather_assets import cable_mesh, rest_coil, modular_plug
from build_wind_sensor import port_route_mm

WHITE=[226,226,213];BLACK=[30,32,34]
ADAPTER_CENTRE=np.array([-.10,-.30,.0125])


def adapter(g):
    # The cream ribbed cylindrical body and hexagonal ends are visible in the
    # Onset page-1 photograph. Every local dimension below is a hypothesis.
    core=cq.Solid.makeCylinder(10,94,cq.Vector(-147,-300,12.5),cq.Vector(1,0,0))
    for a in np.arange(4)*np.pi/2:
        core=core.fuse(cq.Solid.makeCylinder(.5,80,cq.Vector(-140,-300+10*np.cos(a),12.5+10*np.sin(a)),cq.Vector(1,0,0)))
    core=core.cut(cq.Solid.makeCylinder(8.8,96,cq.Vector(-148,-300,12.5),cq.Vector(1,0,0)))
    solid(g,'wind_adapter_ribbed_tube',core,WHITE,role='inferred_inline_adapter')
    for side,x,opening in [('left',-152,-150),('right',-58,-58.1)]:
        cap=cq.Workplane('YZ').polygon(6,24/np.cos(np.pi/6)).extrude(10).val().translate((x,-300,12.5))
        cap=cap.cut(cq.Solid.makeCylinder(10.05,8.1,cq.Vector(opening,-300,12.5),cq.Vector(1,0,0)))
        cap=cap.cut(cq.Solid.makeCylinder(1.6,12,cq.Vector(x-1,-300,12.5),cq.Vector(1,0,0)))
        solid(g,'wind_adapter_hex_cap_'+side,cap,WHITE,role='inferred_inline_adapter')
        start=-160 if side=='left' else -48
        radii=(2.,3.2) if side=='left' else (3.2,2.)
        relief=cq.Solid.makeCone(*radii,8,cq.Vector(start,-300,12.5),cq.Vector(1,0,0))
        relief=relief.cut(cq.Solid.makeCylinder(1.6,10,cq.Vector(start-1,-300,12.5),cq.Vector(1,0,0)))
        solid(g,'wind_adapter_relief_'+side,relief,BLACK,role='inferred_strain_relief')


def build():
    g=Geometry();prefix=port_route_mm()*.001
    prefix_length=float(np.linalg.norm(np.diff(prefix,axis=0),axis=1).sum())
    arm_direction=[-.55,0,-float(np.sqrt(1-.55**2))]
    specs=[
        dict(id='wind_sensor_lead',length_m=2.5,centre=[.15,-.14],turns=4,
            start=prefix[-1],end=[-.040,-.30,.0125],initial=[1,0,0],final=[-1,0,0],angle=np.pi),
        dict(id='wind_network_lead',length_m=.5,centre=[-.265,-.30],turns=1,
            start=[-.160,-.30,.0125],end=[-.13,-.16,.0078],initial=[-1,0,0],final=[1,0,0],angle=0)]
    leads=[]
    for s in specs:
        first=s['id']=='wind_sensor_lead'
        points=rest_coil(s['length_m']-(prefix_length if first else 0),s['centre'],s['turns'],s['start'],s['end'],s['initial'],s['final'],s['angle'])
        initial=arm_direction if first else s['initial']
        if first:points=np.vstack([prefix,points[1:]])
        g.add(s['id'],cable_mesh(points,.0015,[initial,s['final']]),BLACK,role='authored_stored_cable')
        leads.append(dict(id=s['id'],length_m=s['length_m'],radius_m=.0015,points_m=points.tolist(),
            endpoints_m=points[[0,-1]].tolist(),endpoint_tangents=[initial,s['final']],
            installed_in_logger=False,source_length_interpretation='Selected 3 m total = 2.5 m external sensor lead + 0.5 m network lead; source diagram conflicts'))
    adapter(g);plug=modular_plug(g,[-.13,-.16,.0078])
    geometry=export_review(g,'weather_onset_swcf_leads')
    refs=[Path(__file__),HERE/'build_weather_assets.py',HERE/'build_wind_sensor.py',HERE/'wind_sensor_assets.json',
        HERE/'wind_sensor_sources.json',HERE/'weather_sources.json',HERE/'geometry_tools.py',HERE/'build_supplies.py']
    record=dict(schema_version=1,status='unaccepted_external_lead_candidate',id='onset_swcf_m003_leads',geometry=geometry,
        mechanical_geometry=json.loads((HERE/'wind_sensor_assets.json').read_text())['geometry'],
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        stored_leads=leads,modular_plug=plug,base_route_length_m=prefix_length,
        adapter=dict(centre_m=ADAPTER_CENTRE.tolist(),body_outer_diameter_m=.020,body_wall_m=.0012,
            hex_cap_af_m=.024,relief_to_relief_length_m=.120,local_dimensions_inferred=True,
            photo_reference='ONSET_SWCF_MANUAL page 1: cream ribbed cylinder with hexagonal ends'),
        inferences=['3 mm wire diameter and all rest poses are authored. There is no cable stiffness, gravity settling or bend-rating evidence.',
            'Cable exits the hollow arm through the selected front-open base groove; internal factory wiring is outside this external lead reconstruction.',
            'The white cylindrical adapter follows the selected Onset photo, not the different black S-THB adapter. Local dimensions, cavities, reliefs and ribs are inferred.',
            'Separate end caps have nominal 50 micrometre tube clearance; threads, seals and enclosure retention are not modeled.',
            'Selected Cinch round-cable 6P6C envelope does not identify the historical Onset supplier or establish electrical compatibility.'],
        staged_in_lab=False,initial_stock_credit=False,assembly_qualified=False,electrical_qualified=False,owner_acceptance=None)
    write_json(HERE/'wind_lead_assets.json',record)
    print(json.dumps(dict(parts=geometry['parts'],selected_lead_lengths_m=[l['length_m'] for l in leads])))


if __name__=='__main__':build()
