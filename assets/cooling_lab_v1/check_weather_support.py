"""Evaluate real installed-pose support solids and preserve all failed fits."""
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts,overlap,minimum_discrete_bend_radius
from check_outdoor_ground import ground_parts


def local_overlap(a,b):
    lower=np.maximum(a.bounds[0],b.bounds[0]);upper=np.minimum(a.bounds[1],b.bounds[1])
    if np.any(upper-lower<=1e-8):return 0.
    # Manifold uses float32 vertices. Work near the candidate contact instead
    # of losing micrometre detail at the outdoor site's 20 m world offset.
    origin=(lower+upper)/2;a=a.copy();b=b.copy();a.apply_translation(-origin);b.apply_translation(-origin)
    return overlap(a,b)


def wire_clearance(wire):
    p=np.array(wire['points_m']);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    samples=np.linspace(0,arc[-1],int(np.ceil(arc[-1]/.00025))+1)
    xyz=np.column_stack([np.interp(samples,arc,p[:,i]) for i in range(3)]);step=float(np.diff(samples).max())
    search_radius=.009;pairs=cKDTree(xyz).query_pairs(search_radius,output_type='ndarray')
    pairs=pairs[abs(samples[pairs[:,0]]-samples[pairs[:,1]])>.010]
    # A mostly straight ground lead may have no nonlocal neighbours within
    # the search radius. Report a lower bound, never an invented exact gap.
    minimum=float(np.linalg.norm(xyz[pairs[:,0]]-xyz[pairs[:,1]],axis=1).min()) if len(pairs) else None
    bound=search_radius if minimum is None else minimum
    return dict(actual_length_m=float(arc[-1]),sample_step_m=step,nonlocal_exclusion_arc_m=.010,
        search_radius_m=search_radius,minimum_sample_distance_m=minimum,minimum_sample_distance_lower_bound_m=bound,
        conservative_nonlocal_surface_gap_m=bound-step-2*wire['radius_m'])


def build():
    record=json.loads((HERE/'weather_support_assets.json').read_text());parts=load_parts(record['geometry']);checks=[]
    def check(name,passed,**details):checks.append(dict(name=name,passed=bool(passed),**details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('expected_separate_parts',len(parts)==113)
    for name,m in parts.items():check('single_closed_volume_'+name,m.is_volume and len(m.split())==1)
    sources={}
    for key,file in [('tripod','tripod_assets.json'),('anchoring_kit','weather_anchoring_assets.json')]:
        sources[key]=load_parts(json.loads((HERE/file).read_text())['geometry'])
    for row in record['rigid_part_transforms']:
        source=sources[row['source']][row['source_part']].copy();source.apply_transform(np.array(row['pose']))
        m=parts[row['part']];check('preserved_stock_geometry_'+row['part'],np.allclose(source.bounds,m.bounds,atol=3e-6,rtol=0) and len(source.faces)==len(m.faces))
    intersections=[]
    for (name,a),(other,b) in itertools.combinations(parts.items(),2):
        if not a.is_volume or not b.is_volume:continue
        v=local_overlap(a,b)
        if not np.isfinite(v) or v>.001:intersections.append(dict(parts=[name,other],volume_mm3=v))
    check('no_unexplained_installed_intersections',not intersections,intersections=intersections)
    for wire in record['installed_wires']:
        clearance=wire_clearance(wire);bend=minimum_discrete_bend_radius(np.array(wire['points_m']))
        check('measured_cut_length_'+wire['id'],abs(clearance['actual_length_m']-wire['length_m'])<1e-8,**clearance)
        check('nonlocal_wire_separation_'+wire['id'],clearance['conservative_nonlocal_surface_gap_m']>0)
        check('wire_minimum_bend_'+wire['id'],bend>3*wire['radius_m'],minimum_bend_radius_m=bend)
        check(('source_free_tail_lengths_' if wire['source_stock']=='uncut_guy_wire' else 'selected_free_tail_lengths_')+wire['id'],wire['upper_tail_m']==.025 and wire['lower_tail_m']==.025)
    stock=record['wire_stock_balance'];check('conserved_unprocessed_guy_stock',abs(sum(stock['cuts_m'])+stock['remaining_length_m']+stock['material_loss_m']-stock['source_length_m'])<1e-9 and stock['remaining_length_m']>0 and not stock['initial_inventory_credit'])
    stock=record['ground_wire_stock_balance'];check('conserved_selected_ground_wire_stock',abs(sum(stock['cuts_m'])+stock['remaining_length_m']+stock['material_loss_m']-stock['source_length_m'])<1e-9 and stock['remaining_length_m']>0 and not stock['initial_inventory_credit'])
    # Soil penetration is deliberately excluded from hardware-vs-hardware
    # collision checks, but any hard path/pad intersection remains a failure.
    ground_record=json.loads((HERE/'outdoor_ground_assets.json').read_text());ground=ground_parts(ground_record['geometry'])
    hard={n:m for n,m in ground.items() if 'walkway' in n or 'bench_pad_' in n};hits=[]
    for name,m in parts.items():
        if not m.is_volume:continue
        for other,h in hard.items():
            v=local_overlap(m,h)
            if v>.001:hits.append(dict(parts=[name,other],volume_mm3=v))
    check('support_clear_of_hard_ground_components',not hits,intersections=hits)
    a=trimesh.creation.box([.001,.001,.001]);b=a.copy();b.apply_translation([.0008,0,0]);a.apply_translation([6,20,2]);b.apply_translation([6,20,2])
    check('negative_known_penetration_retained_at_world_offset',abs(local_overlap(a,b)-.2)<1e-5)
    b.apply_translation([.0003,0,0]);check('separated_small_solids_at_world_offset',local_overlap(a,b)==0.)
    for name,m in parts.items():
        if '_stake_' in name or name=='ground_rod':check('stake_or_rod_tip_within_candidate_soil_depth_'+name,m.bounds[0,2]>=ground_record['design']['soil_bottom_m'])
    check('no_installation_or_execution_credit',not any(record[k] for k in ['staged_in_lab','initial_stock_credit','installation_qualified','structural_load_qualified','ground_retention_qualified','electrical_grounding_qualified','robot_use_qualified','owner_acceptance']))
    refs=[Path(__file__),HERE/'weather_support_assets.json',HERE/'check_weather_assets.py',HERE/'check_outdoor_ground.py',HERE/'outdoor_ground_assets.json']
    passed=all(c['passed'] for c in checks)
    report=dict(passed=passed,checks=checks,source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        installation_qualified=False,structural_load_qualified=False,ground_retention_qualified=False,electrical_grounding_qualified=False,robot_use_qualified=False,owner_acceptance=None,
        limits=['Only static solids, selected reference poses, wire curves and length accounting are evaluated. Geometry clearance is not proof of load transfer or fastening.',
            'Open-hook insertion trajectories, screw tightening, wire clipping, anchor driving and soil interaction remain untested.',
            'Electrical continuity and ground performance remain unqualified. Level, instruments and all installed sensor/power/data cables are still absent.'])
    write_json(HERE/'weather_support_checks.json',report)
    print(json.dumps(dict(passed=passed,checks=len(checks),failed=[c for c in checks if not c['passed']])))
    raise SystemExit(not passed)


if __name__=='__main__':build()
