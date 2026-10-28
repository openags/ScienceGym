"""Inspect the actual rigid M-TPB candidate, without installation/load credit."""
import itertools
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap


def build():
    record=json.loads((HERE/'tripod_assets.json').read_text());parts=load_parts(record['geometry']);checks=[]
    def check(name,passed,**details):
        checks.append(dict(name=name,passed=bool(passed),**details))
        if not passed:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    for name,m in parts.items():check('single_closed_connected_volume_'+name,m.is_volume and len(m.split())==1)
    hits=[]
    for (name,a),(other,b) in itertools.combinations(parts.items(),2):
        v=overlap(a,b)
        if v>.001:hits.append(dict(parts=[name,other],volume_mm3=v))
    check('no_unexplained_rigid_overlap',not hits,intersections=hits)
    lower=parts['lower_mast_with_indexing_creases'];upper=parts['upper_mast_with_dimple_and_crossarm_holes'];plug=parts['slotted_flush_mast_plug']
    check('selected_mast_top_within_catalogue_height_range',1.72<=upper.bounds[1,2]<=2.13 and abs(upper.bounds[1,2]-2.)<2e-7)
    check('catalogue_mast_diameter',abs(lower.extents[0]-.041)<2e-7 and abs(upper.extents[0]-.041)<2e-7)
    check('source_top_of_leg_clamp_height',abs(parts['upper_leg_clamp_triangular_band'].bounds[1,2]-.81)<2e-7)
    check('selected_mast_overlap',abs(lower.bounds[1,2]-upper.bounds[0,2]-.15)<2e-7)
    check('mast_lower_bore_is_open',not lower.ray.intersects_any([[0,0,-.01]],[[0,0,1]])[0])
    for z in [1.96,1.98]:
        check('crossarm_hole_and_plug_slot_open_'+str(z),not any(m.ray.intersects_any([[0,-.04,z]],[[0,1,0]])[0] for m in [upper,plug]))
    # A quarter turn misaligns the upper indexing dimple and lower grooves.
    wrong=upper.copy();wrong.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]))
    v=overlap(wrong,lower)
    check('negative_misaligned_indexing_dimple_rejected',v>.001,overlap_mm3=v)
    unswaged=trimesh.creation.annulus(.0193,.0205,.15,sections=128);unswaged.apply_translation([0,0,1.125])
    check('negative_unswaged_lower_mast_rejected',overlap(unswaged,upper)>1)
    radial_bolts=[n for n in parts if '_radial_bolt_' in n]
    radial_nuts=[n for n in parts if ('_inner_nut_' in n or '_outer_nut_' in n)]
    check('source_six_radial_bolts_and_twelve_nuts',len(radial_bolts)==6 and len(radial_nuts)==12)
    for name in radial_bolts:
        angle=np.radians([150,270,390][int(name[-1])-1]);m=parts[name].copy();m.apply_transform(trimesh.transformations.rotation_matrix(-angle,[0,0,1]))
        check('source_half_inch_head_af_'+name,abs(m.extents[1]-.0127)<2e-7,actual_af_m=float(m.extents[1]))
    for i,angle in enumerate(np.radians([90,210,330]),1):
        foot=parts['foot_plate_and_fork_'+str(i)].copy();foot.apply_transform(trimesh.transformations.rotation_matrix(-angle,[0,0,1]))
        check('foot_'+str(i)+'_rests_on_reference_plane',abs(foot.bounds[0,2])<2e-7)
        for dx in [-.025,.025]:
            for y in [-.015,.015]:
                check('actual_foot_anchor_hole_'+str((i,dx,y)),not foot.ray.intersects_any([[.51+dx,y,-.01]],[[0,0,1]])[0])
        leg=parts['leg_'+str(i)].copy();leg.apply_transform(trimesh.transformations.rotation_matrix(-angle,[0,0,1]))
        check('selected_leg_outer_diameter_'+str(i),abs(leg.extents[1]-.0254)<2e-7)
        for x,z in [(.084,.790),(.510,.022),((.084+.510)/2,(.790+.022)/2)]:
            check('real_leg_pivot_bore_'+str((i,x,z)),not leg.ray.intersects_any([[x,-.04,z]],[[0,1,0]])[0])
    mass=sum(m.volume*(1200 if n=='slotted_flush_mast_plug' else 7850) for n,m in parts.items())
    check('no_stock_or_installation_credit',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','owner_acceptance']))
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'tripod_assets.json',HERE/'tripod_sources.json']
    report=dict(passed=True,checks=checks,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        indicative_mass=dict(calculated_kg=float(mass),catalogue_total_kg=12.8*.45359237,
            assumptions='7850 kg/m3 all metal, 1200 kg/m3 plug; unknown alloy, gauge distribution and omitted hardware prevent mass/inertia qualification',qualified=False),
        installation_qualified=False,structural_load_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['All unpublished local geometry and clearances are authored hypotheses; source topology and specific catalogue dimensions are kept separately.',
            'Nominal gaps do not establish friction, clamp preload, hinge retention, stiffness, tipping resistance or ground capacity.',
            'Guy/ground kits, anchors, level, attached devices, cables, soil and complete body/hand/tool access are absent.'])
    write_json(HERE/'tripod_checks.json',report);print(json.dumps(dict(passed=True,checks=len(checks),parts=len(parts),indicative_mass_kg=float(mass))))


if __name__=='__main__':build()
