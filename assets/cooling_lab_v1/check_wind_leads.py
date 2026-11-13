"""Inspect actual external wind leads against one another and the rigid sensor.

Geometric checks do not establish cable compliance, sealing, connector
insertion, retention, weather-station stability or robot operation.
"""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from check_weather_assets import load_parts, overlap, cable_clearance, minimum_discrete_bend_radius
from build_weather_assets import cable_mesh


def build():
    record=json.loads((HERE/'wind_lead_assets.json').read_text())
    mechanical_record=json.loads((HERE/'wind_sensor_assets.json').read_text())
    parts=load_parts(record['geometry']);mechanical=load_parts(record['mechanical_geometry'])
    checks=[];clearances=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('same_mechanical_candidate',record['mechanical_geometry']==mechanical_record['geometry'])
    check('no_installation_or_acceptance_credit',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','assembly_qualified','electrical_qualified','owner_acceptance']))
    for name,m in parts.items():check('single_closed_volume_'+name,m.is_volume and len(m.split())==1)
    for lead in record['stored_leads']:
        result=cable_clearance(lead);result['minimum_discrete_bend_radius_m']=minimum_discrete_bend_radius(lead['points_m'])
        clearances.append(dict(id=lead['id'],**result))
        check('continuous_selected_length_'+lead['id'],abs(result['actual_length_m']-lead['length_m'])<1e-8,**result)
        check('nonlocal_self_clearance_'+lead['id'],result['conservative_nonlocal_surface_gap_m']>0)
        check('geometric_bend_screen_'+lead['id'],result['minimum_discrete_bend_radius_m']>3*lead['radius_m'])
        check('exact_endpoints_'+lead['id'],np.allclose(np.array(lead['points_m'])[[0,-1]],lead['endpoints_m'],atol=1e-10))
        check('external_lead_above_reference_plane_'+lead['id'],parts[lead['id']].bounds[0,2]>0,minimum_z_m=float(parts[lead['id']].bounds[0,2]))
    internal=[];external=[]
    for (name,a),(other,b) in itertools.combinations(parts.items(),2):
        v=overlap(a,b)
        if v>.001:internal.append(dict(parts=[name,other],volume_mm3=v))
    for name,a in parts.items():
        for other,b in mechanical.items():
            v=overlap(a,b)
            if v>.001:external.append(dict(parts=[name,other],volume_mm3=v))
    check('no_internal_solid_intersection',not internal,intersections=internal)
    check('no_solid_intersection_with_mechanical_sensor',not external,intersections=external)
    route=np.array(mechanical_record['cable_port']['selected_base_route_m'])
    lead=np.array(record['stored_leads'][0]['points_m'])
    check('sensor_lead_uses_actual_base_route',np.allclose(lead[:len(route)],route,atol=1e-10))
    mast=trimesh.creation.cylinder(.0205,.15,sections=128);mast.apply_translation([-.0255,0,.05])
    check('selected_mast_clear_of_external_leads',max(overlap(mast,m) for m in parts.values())<.001)
    # An uncut lowest rib blocks the proposed route. This is a counterexample
    # to treating a painted or disconnected slot as a real cable opening.
    filled_rib=trimesh.creation.box([.018,.076,.003]);filled_rib.apply_translation([.001,0,.0025])
    blocked=overlap(filled_rib,parts['wind_sensor_lead'])
    check('negative_uncut_base_rib_rejected',blocked>.01,overlap_mm3=blocked)
    for side in ['left','right']:
        for kind in ['hex_cap','relief']:
            name='wind_adapter_'+kind+'_'+side
            check('open_axial_cable_bore_'+name,not parts[name].ray.intersects_any([[-.20,-.30,.0125]],[[1,0,0]])[0])
    check('adapter_tube_is_hollow',not parts['wind_adapter_ribbed_tube'].ray.intersects_any([[-.20,-.30,.0125]],[[1,0,0]])[0])
    for side in ['left','right']:
        z=parts['wind_adapter_hex_cap_'+side].extents[2]
        check('selected_cap_af_'+side,abs(z-.024)<2e-7,actual_m=float(z))
    check('six_contacts_at_selected_pitch',np.allclose(np.diff([parts['plug_contact_'+str(i)].bounds.mean(axis=0)[1] for i in range(1,7)]),.00102,atol=2e-7))
    check('selected_connector_width',abs(parts['modular_plug_body_and_latch'].extents[1]-.00965)<2e-7)
    # Regress the near-vertical frame switch: a dense smooth arc must not gain
    # long diagonal facets when the tangent crosses an arbitrary axis choice.
    t=np.linspace(0,np.pi/2,161);arc=np.column_stack([.02*np.cos(t),np.zeros(len(t)),.02*np.sin(t)])
    arc_mesh=cable_mesh(arc,.0015,[[0,0,1],[-1,0,0]])
    # Closing-cap diagonals span the diameter by design; inspect only edges
    # joining different arc stations, where an artificial frame jump occurs.
    station=np.rint(np.arctan2(arc_mesh.vertices[:,2],arc_mesh.vertices[:,0])/(t[1]-t[0])).astype(int)
    cross_section_edges=np.diff(station[arc_mesh.edges_unique],axis=1).ravel()!=0
    longest=float(arc_mesh.edges_unique_length[cross_section_edges].max())
    check('no_section_flip_through_vertical_arc',longest<.0009,maximum_facet_edge_m=longest)
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'wind_lead_assets.json',HERE/'wind_sensor_assets.json']
    report=dict(passed=True,checks=checks,cable_clearances=clearances,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        installation_qualified=False,electrical_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Selected 3 m total conflicts with the source diagram; split 2.5 + 0.5 m is an explicit reconstruction choice.',
            'All local adapter, relief and cable dimensions are inferred; nominal 50 micrometre cap clearance is not a manufacturing tolerance.',
            'Dense nonlocal centerline clearance excludes local neighbors within 10 mm of arc length. Discrete bend radius is a geometric fold screen, not a vendor bend rating.',
            'Above-plane checks do not demonstrate gravity support. No cable stiffness, seating, thread preload, sealing, electrical behavior or robot handling is tested.'])
    write_json(HERE/'wind_lead_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts),cable_clearances=clearances)))


if __name__=='__main__':build()
