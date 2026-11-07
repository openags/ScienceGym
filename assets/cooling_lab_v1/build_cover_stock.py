"""Uncut angle/adhesive stock and distinct ordinary shield hardware for a pair."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_apparatus_mounting import cad_mesh, display
from build_frame_stock import normalized, export
from build_stock_cutplan import load_parts


RESOURCE='additional_reconstructed_materials:film_attachment_stock'


def build():
    template=json.loads((HERE/'apparatus_cover_candidate.json').read_text())
    ledger=json.loads((HERE/'apparatus_cover_sources.json').read_text())
    parts=load_parts(template['geometry']['path']);items=[]
    # Raw L section rests on its lower leg, 250 mm selected purchased cut.
    leg=12.7;gauge=1.5875
    shape=cq.Solid.makeBox(250,leg,gauge).fuse(cq.Solid.makeBox(250,gauge,leg)).clean()
    m=display(normalized(cad_mesh(shape)));raw=trimesh.Scene()
    raw.add_geometry(m,node_name='raw_angle_250mm',geom_name='raw_angle_250mm')
    cuts=[]
    for k,(color,index) in enumerate((c,i) for c in ['white','black'] for i in [1,2,3]):
        # Unrotate the actual finished part; map its width onto the stock's X.
        unrotate=trimesh.transformations.rotation_matrix(-np.radians([30,150,270][index-1]),[0,0,1])
        place=trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1])
        place[:3,3]=[-.125+.001+k*.011+.005,-.076-leg*.001/2,0]
        cuts.append(dict(id=color+'_shield_angle_'+str(index),source_part='shield_angle_'+str(index),
            raw_part='raw_angle_250mm',stock_from_template=(place@unrotate).tolist(),
            finished_length_m=.010,kerf_allowance_m=.001,stock_axis_interval_m=[-.125+.001+k*.011,-.125+.011+k*.011]))
    items.append(export('cover_angle_stock','屏蔽罩固定角铝原料 · 250 mm 未加工角材',raw,
        [dict(id='raw_angle_250mm',parts=['raw_angle_250mm'],kind='uncut_angle_stock')],
        resource_id='consumables:consumable_02',component_label='aluminum angle stock',cuts=cuts,
        scope='Supplier nominal 12.7 × 12.7 × 1.5875 mm 6063-T52 section; selected 250 mm cut stock is not a confirmed paper purchase. Six 10 mm cuts require cutting, deburring and drilling.'))
    hardware=trimesh.Scene();units=[]
    for color in ['white','black']:
        for name in sorted(n for n in parts if n.startswith(('shield_side_screw_','shield_base_screw_','shield_base_washer_'))):
            m=normalized(parts[name]);solid=m.copy();solid.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=8)
            poses,probabilities=trimesh.poses.compute_stable_poses(solid,sigma=0,n_samples=1)
            heights=np.array([np.ptp(trimesh.transform_points(m.vertices,t)[:,2]) for t in poses])
            choices=np.flatnonzero(heights<=heights.min()+.0001);selected=int(choices[np.argmax(probabilities[choices])])
            m.apply_transform(poses[selected]);m=normalized(m)
            if m.extents[0]<m.extents[1]:
                m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]));m=normalized(m)
            i=len(units);m.apply_translation([(i%6)*.022,(i//6)*.018,0]);identity=color+'_'+name
            hardware.add_geometry(m,node_name=identity,geom_name=identity)
            units.append(dict(id=identity,parts=[identity],source_part=name,
                kind='M3_large_washer' if 'washer' in name else 'M3x6_cap_screw',
                resting_pose_scope='Low-height geometric pose for uniform density; dynamic settling and pickup unqualified'))
    items.append(export('cover_mount_hardware','屏蔽罩普通紧固件 · 12 个 M3×6 螺钉 + 6 个垫圈',hardware,units,
        resource_id='consumables:consumable_12',component_label='shield attachment hardware',
        scope='18 independent starting-stock identities for the paired apparatus; no reuse of completed display objects or physical thread credit.'))
    adhesive=trimesh.Scene();units=[];reservations=[]
    bond=ledger['adhesive_candidate']['nominal_adhesive_thickness_mm']*.001
    liner=ledger['adhesive_candidate']['nominal_liner_thickness_mm']*.001
    roles=[(stage,color,layer) for stage,colors in [('BUILD_PAIR',['white','black']),('FIXED_LDPE',['white','black']),('RESTORE_TRACKED',['white'])] for color in colors for layer in ['lower','upper']]
    roles += [('BUILD_PAIR',color,'aperture') for color in ['white','black']]
    for i,(stage,color,layer) in enumerate(roles,1):
        names=[]
        for kind,t,z,shade in [('liner',liner,(i-1)*(bond+liner)+liner/2,(.88,.85,.74,1)),
                              ('adhesive',bond,(i-1)*(bond+liner)+liner+bond/2,(.73,.70,.59,.9))]:
            name=f'raw_{kind}_{i:02d}';m=trimesh.creation.box([.160,.160,t]);m.apply_translation([0,0,z]);m=display(m,shade,0)
            adhesive.add_geometry(m,node_name=name,geom_name=name);names.append(name)
        units.append(dict(id=f'adhesive_sheet_{i:02d}',parts=names,kind='selected_lined_transfer_adhesive_cut_stock'))
        reservations.append(dict(id=f'{stage}_{color}_{layer}',stock_unit=units[-1]['id'],raw_part=f'raw_adhesive_{i:02d}',
            stage=stage,apparatus=color,location=layer,inner_diameter_m=.140 if layer=='aperture' else .107,
            outer_diameter_m=.152 if layer=='aperture' else .127,finished_gauge_m=bond))
    cap=trimesh.creation.box([.160,.160,liner]);cap.apply_translation([0,0,len(roles)*(bond+liner)+liner/2])
    adhesive.add_geometry(display(cap,(.88,.85,.74,1),0),node_name='additional_top_release_liner',geom_name='additional_top_release_liner')
    units[-1]['parts'].append('additional_top_release_liner')
    items.append(export('cover_adhesive_stock','薄膜与顶盖连接胶膜 · 12 张带离型纸的待裁原料',adhesive,units,
        resource_id=RESOURCE,component_label='film attachment adhesive stock',reservations=reservations,
        scope='Selected 160 × 160 mm cuts from 9471LE roll, not a manufacturer pre-cut SKU. 58 μm adhesive / 102 μm liner are typical TDS values. Top release cover and stacking are packaging hypotheses; porous-PE compatibility, application/removal and retry stock unqualified.'))
    out=dict(schema_version=1,items=items,template_geometry=template['geometry'],
        resource_requirements=[dict(id=RESOURCE,label='film attachment adhesive stock',purpose='Ordinary film/ring and shield/aperture attachment; missing paper method reconstructed explicitly',source_basis='Paper says films attached to ring; adhesive choice, sheet dimensions and campaign replacement policy are authored hypotheses')],
        stock_units=sum(len(i['units']) for i in items),campaign_complete=False,owner_acceptance=None,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'apparatus_cover_candidate.json',HERE/'apparatus_cover_sources.json',HERE/'build_frame_stock.py',ROOT/'tasks/directional_cooling_operations_v3/operations.json']],
        limits=['Quantities cover selected nominal initial/replacement attachments only, not retries or repeated validation campaigns',
                'Stock geometry does not qualify cutting, tools, liner release, adhesion, material restraint or robot handling'])
    write_json(HERE/'cover_stock.json',out)
    print(json.dumps(dict(assets=len(items),stock_units=out['stock_units'],adhesive_reservations=len(reservations))))


if __name__=='__main__':build()
