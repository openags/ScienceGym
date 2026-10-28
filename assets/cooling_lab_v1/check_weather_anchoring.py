"""Inspect exported anchoring stock; no ground/load/electrical qualification."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap,cable_clearance,minimum_discrete_bend_radius


def build():
    record=json.loads((HERE/'weather_anchoring_assets.json').read_text());parts=load_parts(record['geometry']);checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('separate_exported_parts',len(parts)==49)
    for name,m in parts.items():check('single_closed_connected_volume_'+name,m.is_volume and len(m.split())==1)
    hits=[]
    for (name,a),(other,b) in itertools.combinations(parts.items(),2):
        volume=overlap(a,b)
        if volume>.001:hits.append(dict(parts=[name,other],volume_mm3=volume))
    check('loose_kit_has_no_unexplained_overlap',not hits,intersections=hits)
    for i in range(1,4):
        for label,diameter,length in [('guy',.0127,.750),('foot',.00635,.400)]:
            m=parts[label+'_stake_'+str(i)]
            check('source_diameter_'+label+'_stake_'+str(i),abs(m.extents[1]-diameter)<2e-6,actual_diameter_m=float(m.extents[1]))
            check('selected_length_'+label+'_stake_'+str(i),abs(m.extents[0]-length)<2e-5,actual_length_m=float(m.extents[0]))
        x=(140+(i-1)*65)*.001
        body=parts['turnbuckle_'+str(i)+'_body']
        check('turnbuckle_open_window_'+str(i),not body.ray.intersects_any([[x,0,-.01]],[[0,0,1]])[0])
        check('turnbuckle_axial_bore_'+str(i),not body.ray.intersects_any([[x,-.08,.004]],[[0,1,0]])[0])
        for label,y in [('lower',.047),('upper',-.047)]:
            eye=parts['turnbuckle_'+str(i)+'_eye_'+label]
            check('turnbuckle_eye_open_'+str(i)+'_'+label,not eye.ray.intersects_any([[x,y,-.01]],[[0,0,1]])[0])
        # Both open hook mouths admit a selected 3 mm probe along the gap;
        # this is an isolated clearance check, not assembled chain retention.
        hook=parts['s_hook_'+str(i)]
        for label,dx,dy in [('lower',-.007071,.002929),('upper',.007071,-.002929)]:
            probe=trimesh.creation.cylinder(.0015,.012,sections=32);probe.apply_translation([x+dx,.095+dy,.002])
            check('s_hook_open_mouth_'+str(i)+'_'+label,overlap(hook,probe)<.001)
        for label,y in [('lower',.105),('upper',.085)]:
            probe=trimesh.creation.cylinder(.00635,.012,sections=64);probe.apply_translation([x,y,.002])
            check('source_stake_diameter_fits_isolated_hook_eye_'+str(i)+'_'+label,overlap(hook,probe)<.001,
                scope='Axial insertion envelope through the eye only. Open-mouth assembly path and loaded linkage are not tested.')
    for i in range(1,7):
        x=(120+(i-1)*28)*.001;body=parts['wire_clamp_'+str(i)+'_body']
        for dx in [-.002,.002]:
            probe=trimesh.creation.cylinder(.0015,.020,sections=48);probe.apply_translation([x+dx,.155,.007])
            check('wire_clamp_real_channel_'+str((i,dx)),overlap(body,probe)<.001)
        screw=parts['wire_clamp_'+str(i)+'_screw']
        # The real crossed recess has a clear centre ray entering the head,
        # then a bottom surface rather than a painted-on cross.
        hits=screw.ray.intersects_location([[x,.170,.007]],[[0,-1,0]])[0]
        first=float(np.max(hits[:,1]));check('wire_clamp_recess_depth_'+str(i),abs(first-.1606)<2e-6,first_contact_y_m=first)
    rod=parts['ground_rod'];check('source_four_foot_ground_rod',abs(rod.extents[0]-1.2192)<2e-7)
    clamp=parts['ground_rod_clamp_body']
    for x,r,label in [(.090,.00635,'rod'),(.0818,.0015,'wire')]:
        probe=trimesh.creation.cylinder(r,.016,sections=64);probe.apply_translation([x,.280,.006]);check('ground_clamp_'+label+'_bore',overlap(clamp,probe)<.001)
    wire=trimesh.creation.cylinder(.0015,.016,sections=64);wire.apply_translation([.180,.2921,.005])
    check('mast_ground_wire_groove_is_clear',overlap(wire,parts['ground_mast_saddle'])<.001)
    mast=trimesh.creation.cylinder(.0205,.06,sections=128);mast.apply_translation([.180,.270,.005])
    check('selected_mast_and_ground_wire_are_separate',overlap(mast,wire)<.001)
    check('mast_ground_clamp_clears_selected_mast',all(overlap(mast,m)<.001 for n,m in parts.items() if n.startswith('ground_mast_')))
    for lead in record['stored_wires']:
        result=cable_clearance(lead);bend=minimum_discrete_bend_radius(np.array(lead['points_m']))
        check('uncut_stock_length_'+lead['id'],abs(result['actual_length_m']-lead['length_m'])<1e-8,**result)
        check('nonlocal_stock_coil_gap_'+lead['id'],result['conservative_nonlocal_surface_gap_m']>0)
        check('stock_coil_bend_'+lead['id'],bend>3*lead['radius_m'],minimum_bend_radius_m=bend)
        bounds=parts[lead['id']].bounds[:,2]
        check('flat_coil_rest_plane_'+lead['id'],np.allclose(bounds,[0,2*lead['radius_m']],atol=2e-7),z_bounds_m=bounds.tolist())
    # Filling a turnbuckle window is an explicit bad-geometry counterexample.
    fake=trimesh.creation.box([.013,.060,.006]);fake.apply_translation([.140,0,.004])
    check('negative_solid_turnbuckle_window_rejected',bool(fake.ray.intersects_any([[.140,0,-.01]],[[0,0,1]])[0]))
    check('no_unearned_qualification',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','structural_load_qualified','electrical_grounding_qualified','owner_acceptance']))
    refs=[Path(__file__),HERE/'weather_anchoring_assets.json',HERE/'check_weather_assets.py']
    report=dict(passed=True,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],installation_qualified=False,structural_load_qualified=False,electrical_grounding_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Checks use actual exported loose-kit solids and selected fit probes; no complete installed station or robot motion is tested.',
            'Wire lengths and static coil separation do not establish flexible dynamics, cutting, tension, grounding performance or clamp retention.',
            'Stake length, bend shape, hardware sizes, conductor diameter and ground-wire stock length remain explicitly inferred.'])
    write_json(HERE/'weather_anchoring_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts))))


if __name__=='__main__':build()
