"""Independent quantities, shape preservation, resting envelopes and failures."""
import copy
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from build_stock_cutplan import load_parts


def packing_conflicts(units,parts):
    bounds={u['id']:np.array([np.min([parts[n].bounds[0] for n in u['parts']],axis=0),np.max([parts[n].bounds[1] for n in u['parts']],axis=0)]) for u in units}
    conflicts=[]
    for i,a in enumerate(units):
        for b in units[i+1:]:
            aa,bb=bounds[a['id']],bounds[b['id']]
            if np.all(np.minimum(aa[1,:2],bb[1,:2])-np.maximum(aa[0,:2],bb[0,:2])>1e-7):conflicts.append([a['id'],b['id']])
    return conflicts


def build():
    record=json.loads((HERE/'frame_stock.json').read_text());apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    sources={i['id']:load_parts(i['geometry']['path']) for i in apparatus['items']};checks=[]
    def check(name,value,**details):
        checks.append(dict(name=name,passed=bool(value),**details))
        if not value:raise AssertionError(name+' '+str(details))
    for ref in record['source_artifacts']:check('source_'+ref['path'],sha(ROOT/ref['path'])==ref['sha256'])
    check('pair_only_95_stock_units',record['selected_for_pair_only'] and sum(len(i['units']) for i in record['items'])==95)
    for item in record['items']:
        parts=load_parts(item['geometry']['path']);units=item['units'];names=[n for u in units for n in u['parts']]
        check('exact_distinct_stock_parts_'+item['id'],len(names)==len(set(names))==len(parts) and set(names)==parts.keys())
        check('artifact_'+item['id'],sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'])
        for name,m in parts.items():
            s=m.copy();s.merge_vertices(merge_tex=True,merge_norm=True,digits_vertex=8)
            check('closed_positive_stock_'+name,s.is_watertight and s.is_winding_consistent and s.volume>0)
        if item['id']=='frame_profile_stock':
            check('four_profiles_and_four_raw_tubes',len(units)==8 and len(item['tube_cuts'])==4 and len(item['component_groups']['frame extrusion stock'])==4)
            check('separated_horizontal_lengths',not packing_conflicts(units,parts) and all(m.extents[0]>.24 and m.extents[2]<.021 for m in parts.values()))
        elif item['id']=='frame_machining_stock':
            ordered=[parts[n] for n in ['frame_plate_3mm','frame_clamp_block_20mm','frame_carriage_plate_4mm']]
            check('stack_has_real_bearing_planes',abs(ordered[0].bounds[0,2])<1e-8 and all(abs(a.bounds[1,2]-b.bounds[0,2])<1e-8 and np.all(b.bounds[0,:2]>=a.bounds[0,:2]) and np.all(b.bounds[1,:2]<=a.bounds[1,:2]) for a,b in zip(ordered[:-1],ordered[1:])))
            check('three_selected_raw_gauges',np.allclose([m.extents[2] for m in ordered],[.003,.020,.004],atol=1e-8))
        else:
            check('84_hardware_units_and_8_release_liners',len(units)==84 and len(parts)==92 and sum(len(u['parts'])==2 for u in units)==8)
            check('no_overlapping_stock_units',not packing_conflicts(units,parts))
            for u in units:
                m=parts[u['id']];original=sources[u['source_asset']][u['source_part']]
                matrix,_,_=trimesh.registration.procrustes(original.vertices,m.vertices,reflection=False,translation=True,scale=False)
                error=float(np.max(abs(trimesh.transform_points(original.vertices,matrix)-m.vertices)))
                check('unchanged_rigid_hardware_'+u['id'],np.array_equal(m.faces,original.faces) and error<2e-7,maximum_vertex_error_m=error)
                check('supported_nominal_stock_'+u['id'],abs(m.bounds[0,2]-(.00008 if len(u['parts'])==2 else 0))<2e-7)
                if 'lower_pinch' in u['id'] or 'frame_clamp_' in u['id'] and 'screw' in u['id']:
                    check('long_screw_lies_low_'+u['id'],m.extents[2]<.011 and m.extents[0]>.038)
                if len(u['parts'])==2:
                    liner=parts[u['parts'][1]]
                    check('pad_package_has_contacting_liner_'+u['id'],abs(liner.bounds[1,2]-m.bounds[0,2])<1e-8 and np.all(liner.bounds[0,:2]<=m.bounds[0,:2]) and np.all(liner.bounds[1,:2]>=m.bounds[1,:2]))
            # Put two real distinct units at the same XY location; do not
            # replace them with decorative proxy boxes in the failure case.
            bad={n:m.copy() for n,m in parts.items()};a,b=units[:2]
            shift=bad[a['id']].bounds.mean(axis=0)-bad[b['id']].bounds.mean(axis=0)
            for n in b['parts']:bad[n].apply_translation([*shift[:2],0])
            check('negative_overlapped_units_rejected',bool(packing_conflicts(units,bad)))
            duplicated=copy.deepcopy(units);duplicated[-1]['parts']=duplicated[0]['parts']
            listed=[n for u in duplicated for n in u['parts']]
            check('negative_duplicate_physical_part_rejected',len(set(listed))!=len(listed))
    check('20_distinct_machined_outputs',len(record['machining_requirements'])==20 and len({(r['output_template']['asset_id'],r['output_template']['part']) for r in record['machining_requirements']})==20)
    check('no_stock_or_physics_acceptance',record['owner_acceptance'] is None and not record['campaign_allocation_complete'] and all(not i['accepted'] and not i['initial_state_qualified'] for i in record['items']))
    rejected=json.loads((HERE/'frame_stock_layout_rejected.json').read_text());bounds=[]
    check('failed_layout_geometry_pinned',sha(ROOT/rejected['geometry']['path'])==rejected['geometry']['sha256'])
    failed_parts=load_parts(rejected['geometry']['path'])
    for a in rejected['assets']:
        b=np.array([failed_parts[n].bounds for n in a['parts']])
        bounds.append(np.array([b[:,0].min(axis=0),b[:,1].max(axis=0)]))
    check('negative_observed_stock_layout_overlap',np.all(np.minimum(bounds[0][1],bounds[1][1])-np.maximum(bounds[0][0],bounds[1][0])>1e-5))
    report=dict(passed=True,checks=checks,stock_units=95,hardware_units=84,machined_output_parts=20,scene_access_qualified=False,
        scope='Initial-stock nominal quantities, actual rigid shapes, separated resting envelopes and selected blank stack only; no settled dynamics, retention, pickup, machining or campaign completeness',owner_acceptance=None,
        source_artifacts=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in [Path(__file__),HERE/'frame_stock.json',HERE/'apparatus_stock_reconciliation.json',HERE/'frame_stock_layout_rejected.json']])
    write_json(HERE/'frame_stock_checks.json',report)
    print(json.dumps(dict(passed=True,checks=len(checks),stock_units=95)))


if __name__=='__main__':build()
