"""Review a proposed weather-station footprint against the current laboratory.

This generates spatial reservations, not installed equipment or robot paths.
Actual tripod/hardware geometry, soil, loads and manipulation remain open.
"""
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Point,LineString,box,MultiPoint
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts


def build():
    scene=json.loads((HERE/'scene.json').read_text());checks=[]
    zone=next(z for z in scene['zones'] if z['id']=='outdoor');ground=box(*zone['bounds_m'])
    center=np.array([6.,16.8]);guy_radius=3.;anchor_radius=.10;wire_radius=.003
    # These are layout allowances, not unknown vendor wire/anchor dimensions.
    anchors=[center+guy_radius*np.array([math.cos(a),math.sin(a)]) for a in [math.pi/2,7*math.pi/6,11*math.pi/6]]
    wire_lines=[LineString([center,a]) for a in anchors]
    obstacle_rows=[o for o in scene['obstacles'] if o['bounds_m'][0][1]>=12 and o['bounds_m'][1][2]>0]
    obstacles={o['id']:box(o['bounds_m'][0][0],o['bounds_m'][0][1],o['bounds_m'][1][0],o['bounds_m'][1][1]) for o in obstacle_rows}
    corridor=next(c for c in scene['corridors'] if c['id']=='outdoor_cross')
    transit=LineString(corridor['points_m']);corridor_polygon=transit.buffer(corridor['width_m']/2,cap_style='flat')
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for i,(anchor,line) in enumerate(zip(anchors,wire_lines),1):
        footprint=line.buffer(wire_radius).union(Point(anchor).buffer(anchor_radius))
        check('source_guy_anchor_distance_'+str(i),3.-1e-8<=np.linalg.norm(anchor-center)<=4.+1e-8,distance_m=float(np.linalg.norm(anchor-center)))
        check('anchor_reservation_inside_outdoor_area_'+str(i),ground.contains(footprint),boundary_clearance_m=float(ground.boundary.distance(footprint)))
        hits=[name for name,poly in obstacles.items() if footprint.intersects(poly)]
        check('guy_and_anchor_clear_of_furniture_'+str(i),not hits,obstructions=hits,
            minimum_furniture_clearance_m=float(min(footprint.distance(poly) for poly in obstacles.values())))
        check('existing_front_corridor_clear_of_guy_'+str(i),not footprint.intersects(corridor_polygon),minimum_corridor_edge_gap_m=float(footprint.distance(corridor_polygon)))
    # Reserve the actual three leg directions, rather than treating the whole
    # station as a bare central pole. Foot radius is an inference because the
    # product's 0.51 m "footprint" has no published dimensional datum.
    foot_radius=.51
    feet=[center+foot_radius*(a-center)/guy_radius for a in anchors]
    leg_reservations=[LineString([center,f]).buffer(.025).union(Point(f).buffer(.06)) for f in feet]
    station_footprint=Point(center).buffer(.075)
    for p in leg_reservations:station_footprint=station_footprint.union(p)
    preliminary_footprint=station_footprint
    tripod=json.loads((HERE/'tripod_assets.json').read_text());rigid_parts=load_parts(tripod['geometry'])
    outside=[]
    for name,mesh in rigid_parts.items():
        projected=MultiPoint(mesh.vertices[:,:2]+center).convex_hull
        excess=projected.difference(preliminary_footprint).area
        if excess>1e-8:outside.append(dict(part=name,area_m2=float(excess)))
        # Retain each complete projected part hull even if the preliminary
        # frame allowance underestimated a local bolt or foot corner.
        station_footprint=station_footprint.union(projected)
    check('preliminary_frame_reservation_contains_rigid_part_hulls',not outside,uncovered=outside)
    check('tripod_reservation_inside_area',ground.contains(station_footprint))
    check('tripod_reservation_clear_of_furniture',not any(station_footprint.intersects(p) for p in obstacles.values()))
    # A short approach corridor terminates before the tripod. It is a planar
    # reservation only: no target reach, walking, carrying or action is solved.
    approach=LineString([[6,14.2],[6,15.75]])
    half_width=scene['envelope']['transit_radius_m']+scene['envelope']['margin_m']
    approach_reservation=approach.buffer(half_width,cap_style='round')
    physical_reservations=[station_footprint]+[l.buffer(wire_radius).union(Point(a).buffer(anchor_radius)) for l,a in zip(wire_lines,anchors)]
    hits=[i for i,p in enumerate(physical_reservations) if approach_reservation.intersects(p)]
    check('provisional_front_approach_clear_of_station_reservations',not hits,obstructions=hits,
        required_half_width_m=half_width,minimum_centerline_clearance_m=float(min(approach.distance(p) for p in physical_reservations)))
    check('provisional_front_approach_clear_of_furniture',not any(approach_reservation.intersects(p) for p in obstacles.values()))
    # Keep a real negative case: putting the north anchor on the original
    # 20 m boundary leaves no room for its nonzero anchor/working reservation.
    old_anchor=Point(6,20).buffer(anchor_radius)
    check('negative_boundary_anchor_rejected',not ground.contains(old_anchor))
    wind_base_z=1.72;cup_z=wind_base_z+.333
    check('selected_cup_centre_above_two_metres',cup_z>=2,cup_centre_height_m=cup_z,
        scope='Source installation recommendation only; airflow and siting accuracy are not evaluated')
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'scene.json',HERE/'room_architecture.py',HERE/'weather_sources.json',HERE/'wind_sensor_assets.json',HERE/'tripod_assets.json',ROOT/'assets/unitree_g1_inspire_v1/space.json']
    record=dict(schema_version=1,status='spatial_proposal_only_not_staged',
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        reference_sources=[dict(url='https://www.onsetcomp.com/sites/default/files/resources-documents/12317-B%20MAN-TRIPOD.pdf',pages=[2,3,7,8,9,10],sha256='60ecc89d71d541b316ae193b1e6519a8693a71b73baee478a7cbbc41e6d4862e'),
            dict(url='https://www.onsetcomp.com/products/mounting/m-gwa',fact='50 ft / 15.24 m of 6-strand 20 gauge coated guy wire'),
            dict(url='https://www.onsetcomp.com/products/mounting/m-gka',fact='Ground rod length 4 ft / 1.2192 m')],
        area_bounds_m=zone['bounds_m'],mast_center_xy_m=center.tolist(),selected_mast_top_z_m=2.,selected_wind_base_z_m=wind_base_z,
        rigid_tripod_geometry=tripod['geometry'],rigid_projection_method='Union of every current rigid part convex hull in XY, added to conservative leg/foot reservations',
        tripod_feet_xy_m=[f.tolist() for f in feet],selected_foot_radius_m=foot_radius,
        guy_anchors_xy_m=[a.tolist() for a in anchors],selected_guy_attachment_z_m=1.90,selected_anchor_eye_z_m=.10,
        anchor_planar_allowance_radius_m=anchor_radius,guy_planar_allowance_radius_m=wire_radius,
        existing_front_corridor=corridor,provisional_front_approach_xy_m=list(map(list,approach.coords)),
        provisional_approach_half_width_m=half_width,
        checks=checks,spatial_reservations_clear=all(c['passed'] for c in checks),
        ground_conflict=dict(current_surface='room_architecture.py uses the same 120 mm slab and resin texture outdoors as indoors',
            current_surface_compatible_with_stake_installation=False,
            proposed_surface='Level firm earth at the station and anchor sites, with separately modeled ordinary bench footing pads and an explicit walkable surface',
            implemented=False,ground_strength_qualified=False),
        missing=['Tripod stock staging, installed configuration and load qualification; rigid frame is available separately',
            'M-GWA eyelets, S hooks, turnbuckles, wire clamps, continuous routed guys and remaining stock',
            'Foot anchors, three guy anchors, M-GKA rod/clamps/wire and actual ground geometry',
            'Installed U30, shield, sensor leads, drip loops, mast retention and power/data routes',
            'Complete body/hand/carried-object access, ground interaction, structural loads and stability'],
        staged_in_lab=False,installation_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['The entire projected guy line is reserved conservatively; no overhead passage is credited.',
            'The 0.51 m foot radius, anchor envelope and wire envelope are layout choices, not recovered commercial dimensions.',
            'Approach is only a planar clearance allowance using existing restricted transit samples; it is not a robot trajectory or target reach solution.',
            'Current main scene and resin slab are unchanged. No installed station, ground penetration, load capacity or weather accuracy is claimed.'])
    # Native SVG is a footprint diagram, not a rendered equipment substitute.
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="850" viewBox="0 0 1100 850">',
        '<rect width="1100" height="850" fill="#f5f7f5"/>',
        '<text x="50" y="42" font-family="sans-serif" font-size="22">Weather station footprint proposal — not installed</text>',
        '<text x="50" y="72" font-family="sans-serif" font-size="15">12 × 8 m outdoor area; 3 m guy anchors; full projected cable reservations</text>']
    def xy(p):return (70+80*p[0],760-80*(p[1]-12))
    def rect(poly,color,opacity=1):
        x0,y0,x1,y1=poly.bounds;x,y=xy([x0,y1]);svg.append(f'<rect x="{x}" y="{y}" width="{80*(x1-x0)}" height="{80*(y1-y0)}" fill="{color}" opacity="{opacity}"/>')
    rect(ground,'#e1e9de');rect(corridor_polygon,'#c1dce4')
    for name,poly in obstacles.items():
        rect(poly,'#677b83');x,y=xy(poly.centroid.coords[0]);svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="white" font-family="sans-serif" font-size="12">{name}</text>')
    for line in wire_lines:
        p=[xy(v) for v in line.coords];svg.append(f'<line x1="{p[0][0]}" y1="{p[0][1]}" x2="{p[1][0]}" y2="{p[1][1]}" stroke="#bd772b" stroke-width="3"/>')
    for i,a in enumerate(anchors,1):
        x,y=xy(a);svg.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#bd772b"/><text x="{x+12}" y="{y+4}" font-family="sans-serif" font-size="13">A{i}</text>')
    for f in feet:
        x,y=xy(f);c=xy(center);svg.append(f'<line x1="{c[0]}" y1="{c[1]}" x2="{x}" y2="{y}" stroke="#3c4a50" stroke-width="5"/>')
    p=[xy(v) for v in approach.coords];svg.append(f'<line x1="{p[0][0]}" y1="{p[0][1]}" x2="{p[1][0]}" y2="{p[1][1]}" stroke="#5099ad" stroke-width="{half_width*160}" stroke-linecap="round" opacity=".25"/>')
    x,y=xy(center);svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#263e45"/><text x="{x+12}" y="{y+4}" font-family="sans-serif" font-size="13">Mast (6.0, 16.8)</text>')
    svg+=['<text x="50" y="806" font-family="sans-serif" font-size="15">Open ground conflict: existing resin slab cannot be credited as an earth-stake installation.</text>','<text x="50" y="832" font-family="sans-serif" font-size="14">Geometry and static clearances only. Hardware, ground strength, full-body motion and owner acceptance remain open.</text>','</svg>']
    path=HERE/'weather_site_plan.svg';path.write_text('\n'.join(svg)+'\n')
    record['plan_diagram']=dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
    write_json(HERE/'weather_site_review.json',record)
    print(json.dumps(dict(checks=len(checks),spatial_reservations_clear=record['spatial_reservations_clear'],failed=[c for c in checks if not c['passed']],ground_conflict_open=True)))


if __name__=='__main__':build()
