"""Static supplied-ground-lead hypothesis: real openings, routing and stack."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap
from check_u30 import wire_clearance


def build():
    r=json.loads((HERE/'u30_ground_assets.json').read_text());u=json.loads((HERE/'u30_assets.json').read_text());checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in r['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('inferred_unaccepted_accessory',not r['electrical_qualified'] and not r['robot_use_qualified'] and not r['initial_stock_credit'] and r['owner_acceptance'] is None and not r['conductor']['source_length_known'])
    ground=load_parts(r['geometry']);logger=load_parts(u['geometry']);origin=np.asarray(r['selected_logger_origin_m'])
    for m in logger.values():m.apply_translation(origin)
    check('seven_distinct_ground_domains',len(ground)==7)
    for n,m in ground.items():check('connected_solid_'+n,m.is_volume and len(m.split())==1)
    overlaps=[]
    for (n,m),(q,b) in itertools.combinations(ground.items(),2):
        v=overlap(m,b)
        if not np.isfinite(v) or abs(v)>.001:overlaps.append(dict(parts=[n,q],volume_mm3=v))
    check('distinct_factory_material_domains',not overlaps,intersections=overlaps)
    removed=logger.pop(r['removed_channel_plug']);nut_name=r['nut_adjustment']['source_part'];original_nut=logger[nut_name].copy()
    logger[nut_name].apply_translation(r['nut_adjustment']['translation_m']);hits=[]
    for n,m in ground.items():
        for q,b in logger.items():
            if q.endswith('_text'):continue
            v=overlap(m,b)
            if not np.isfinite(v) or abs(v)>.001:hits.append(dict(parts=[n,q],volume_mm3=v))
    check('complete_ground_lead_clears_logger_and_mount',not hits,intersections=hits)
    check('flag_reference_envelope',np.all(np.abs(ground['flag_nylon_housing'].extents-[.01473,.01524,.00608])<[2e-7,2e-7,2e-6]),actual_m=ground['flag_nylon_housing'].extents.tolist(),scope='5.33 mm source front thickness; 6.08 mm selected flare outside diameter is inferred. Circular tessellation can under-sample its Z extrema by up to 2 micrometres; flat X/Y extents use 0.2 micrometres.')
    ring=trimesh.util.concatenate([m for n,m in ground.items() if n.startswith('ring_')])
    check('ring_reference_overall_length_and_width',abs(ring.extents[2]-.02870)<2e-6 and abs(ring.extents[0]-.01168)<2e-6,actual_m=ring.extents.tolist(),circular_tessellation_tolerance_m=2e-6)
    check('ring_bore_is_open',not ground['ring_tin_copper_stamp'].ray.intersects_any([[-.026162,-.1,1.100]],[[0,1,0]])[0])
    plate=ground['ring_tin_copper_stamp'];probe=np.array([-.026162+.005,-.1,1.100])
    locations=plate.ray.intersects_location([probe],[[0,1,0]])[0]
    thickness=float(np.ptp(locations[:,1]));check('source_ring_stamp_thickness',abs(thickness-.00081)<2e-7,actual_m=thickness)
    wire=wire_clearance(r['conductor'])
    check('selected_complete_conductor_length',abs(wire['length_m']-.4)<1e-8,**wire)
    check('conductor_bend_and_nonlocal_clearance',wire['minimum_discrete_bend_radius_m']>3*r['conductor']['radius_m'] and wire['conservative_nonlocal_surface_gap_m']>0)
    body=ground['flag_nylon_housing'];filled=trimesh.creation.box([.0094,.01524,.00533]);filled.apply_translation(np.asarray(r['flag_origin_m'])+[0,-.00762,0])
    check('negative_filled_flag_throat_hits_actual_tab',overlap(filled,logger['ground_connection_tab'])>1)
    check('negative_unremoved_gland_plug_hits_ground_sleeve',overlap(removed,ground['black_gland_sleeve'])>1)
    check('negative_unadjusted_nut_hits_actual_ring',overlap(original_nut,plate)>1)
    nut=logger[nut_name];washer=logger['mount_1_washer_left'];bolt=logger['mount_1_u_bolt']
    ring_front=r['ring_origin_m'][1]-.00081;ring_back=r['ring_origin_m'][1]
    check('ring_between_nut_and_existing_washer',abs(nut.bounds[1,1]-ring_front)<2e-7 and abs(washer.bounds[0,1]-ring_back)<2e-7,
        nut_rear_y_m=float(nut.bounds[1,1]),ring_faces_y_m=[ring_front,ring_back],washer_front_y_m=float(washer.bounds[0,1]))
    protrusion=float(nut.bounds[0,1]-bolt.bounds[0,1]);check('selected_bolt_extends_through_full_nut',protrusion>0,protrusion_m=protrusion,scope='Nominal smooth envelopes only; thread specification, torque and electrical bond remain unqualified.')
    refs=[Path(__file__),HERE/'u30_ground_assets.json',HERE/'u30_assets.json',HERE/'check_u30.py']
    result=dict(schema_version=1,passed=True,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        scope='Complete static grounding accessory and its inferred terminal geometry, actual logger clearance and fastener stack. No electrical continuity, crimp quality, load, sealing or robot-use qualification.',
        electrical_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    write_json(HERE/'u30_ground_checks.json',result);print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':build()
