"""Separate frame starting-stock candidates from completed display assemblies.

Purchased profiles, uncut tube/plate stock and individual ordinary hardware
are counted independently. Resting poses are geometric hypotheses, not a
settled dynamic state or robot pickup validation.
"""
import json
import re
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_apparatus_mounting import display
from build_stock_cutplan import load_parts


def normalized(mesh):
    m=mesh.copy();m.apply_translation([-m.bounds.mean(axis=0)[0],-m.bounds.mean(axis=0)[1],-m.bounds[0,2]])
    return m


def export(identity,label,scene,units,**extra):
    f=HERE/'geometry'/(identity+'.glb');f.write_bytes(scene.export(file_type='glb',include_normals=True))
    return dict(id=identity,label=label,geometry=dict(path=str(f.relative_to(ROOT)),sha256=sha(f),parts=len(scene.geometry),bounds_m=scene.bounds.tolist()),
                units=units,accepted=False,initial_state_qualified=False,**extra)


def build():
    apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    pair={i['id']:i for i in apparatus['items'] if i['id'] in ['cooler_white','cooler_black']}
    parts={key:load_parts(i['geometry']['path']) for key,i in pair.items()}
    profiles=trimesh.Scene();profile_units=[];tube_cuts=[]
    for color in ['white','black']:
        prefix='COOLER_'+color.upper()+'__';item=pair['cooler_'+color]
        for side in ['left','right']:
            n=prefix+'frame_rail_'+side;m=parts['cooler_'+color][n].copy()
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]));m=normalized(m)
            name='profile_'+color+'_'+side
            profile_units.append(dict(id=name,kind='purchased_340mm_profile',parts=[name],output_template=dict(asset_id=item['id'],part=n),cutting_required=False))
            profiles.add_geometry(m,node_name=name,geom_name=name)
            name='upright_tube_'+color+'_'+side
            m=trimesh.creation.annulus(.007,.010,.250,sections=128)
            m.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]));m=display(normalized(m))
            profiles.add_geometry(m,node_name=name,geom_name=name)
            profile_units.append(dict(id=name,kind='uncut_250mm_tube',parts=[name]))
            joint=next(j for j in item['frame']['joints'] if j['id']=='upright_'+side)
            tube_cuts.append(dict(id=name,raw_length_m=.250,finished_length_m=joint['tube_length_mm']*.001,cut_allowance_m=.001,
                                  output_template=dict(asset_id=item['id'],part=prefix+'frame_tube_'+side)))
    # Eight individually identified lengths, lying along X with 10 mm gaps.
    for i,u in enumerate(profile_units):profiles.geometry[u['id']].apply_translation([0,i*.030,0])
    items=[export('frame_profile_stock','框架型材与立柱原管 · 4 根定尺型材 + 4 根原管',profiles,profile_units,
        resource_id='equipment:COOLER',component_groups={'frame extrusion stock':[u['id'] for u in profile_units if u['kind']=='purchased_340mm_profile'],
        'upright tube stock':[u['id'] for u in profile_units if u['kind']=='uncut_250mm_tube']},tube_cuts=tube_cuts,
        scope='340 mm profile is a selected vendor cut-to-length purchase; 250 mm tubes still require cutting/deburring. Grade, tolerance, storage restraint and dynamic settling are unqualified.')]
    blanks=trimesh.Scene();blank_units=[];z=0
    for name,size in [('frame_plate_3mm',[.350,.200,.003]),('frame_clamp_block_20mm',[.250,.150,.020]),('frame_carriage_plate_4mm',[.100,.050,.004])]:
        m=trimesh.creation.box(size);m.apply_translation([0,0,z+size[2]/2]);z+=size[2]
        blanks.add_geometry(display(m),node_name=name,geom_name=name)
        blank_units.append(dict(id=name,kind='uncut_aluminum_blank',parts=[name],nominal_size_m=size))
    items.append(export('frame_machining_stock','框架连接件加工原料 · 3 种厚度铝坯',blanks,blank_units,
        resource_id='consumables:consumable_02',component_label='aluminum sheet stock',
        scope='Original stock selection, not a manufacturer SKU. Real cutting, bores, threads, splits, facing, workholding and tool allocation remain unqualified.'))
    hardware=trimesh.Scene();hardware_units=[];resting=[]
    structural=re.compile(r'frame_(rail_|tube_|lower_clamp_|upper_clamp_|bridge_(left|right)_[12]$|carriage_(upper|lower)$)')
    for color in ['white','black']:
        item=pair['cooler_'+color];prefix='COOLER_'+color.upper()+'__'
        for n in item['frame']['added_parts']:
            suffix=n.removeprefix(prefix)
            if structural.match(suffix):continue
            m=normalized(parts[item['id']][n]);solid=m.copy();solid.merge_vertices(merge_norm=True,merge_tex=True,digits_vertex=8)
            poses,probabilities=trimesh.poses.compute_stable_poses(solid,sigma=0,n_samples=1)
            if not len(poses):raise ValueError('No geometric resting pose for '+n)
            # A cylindrical screw offers many distinct lying hull facets but
            # only one head-down pose. Choosing the largest single probability
            # unfairly favours standing long screws. Prefer low resting poses,
            # then the highest probability within 0.1 mm of the lowest height.
            heights=np.array([np.ptp(trimesh.transform_points(m.vertices,t)[:,2]) for t in poses])
            candidates=np.flatnonzero(heights<=heights.min()+.0001)
            selected=int(candidates[np.argmax(probabilities[candidates])]);m.apply_transform(poses[selected]);m=normalized(m)
            if m.extents[0]<m.extents[1]:m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]));m=normalized(m)
            name=color+'_'+suffix;members=[name];meshes={name:m}
            if suffix.startswith('frame_bumper_'):
                # Ordinary packaging hypothesis: retain a release liner under
                # the flat adhesive face. Not a confirmed vendor liner gauge.
                m.apply_translation([0,0,.00008]);liner=trimesh.creation.box([.022,.022,.00008]);liner.apply_translation([0,0,.00004])
                meshes[name+'_liner']=display(liner,(.87,.84,.72,1),0);members.append(name+'_liner')
            bounds=np.array([a.bounds for a in meshes.values()]);low=bounds[:,0].min(axis=0);high=bounds[:,1].max(axis=0)
            resting.append(dict(id=name,parts=members,meshes=meshes,low=low,high=high,source_part=n,source_asset=item['id'],
                                resting_transform=poses[selected].tolist(),uniform_density_geometric_probability=float(probabilities[selected]),
                                resting_pose_choice='Lowest geometric resting height within 0.1 mm, then highest individual face probability'))
    assert len(resting)==84,'Two completed references must give 84 separate ordinary hardware/pad units'
    # Shelf pack actual resting envelopes; no overlap or invisible stock pile.
    width=.315;gap=.003;x=gap;y=gap;row_height=0
    for unit in sorted(resting,key=lambda r:(-(r['high']-r['low'])[1],r['id'])):
        size=unit['high']-unit['low']
        if x+size[0]+gap>width:x=gap;y+=row_height+gap;row_height=0
        shift=np.array([x,y,0])-unit['low']
        for name,m in unit['meshes'].items():
            m.apply_translation(shift);hardware.add_geometry(m,node_name=name,geom_name=name)
        hardware_units.append({k:v for k,v in unit.items() if k not in ['meshes','low','high']})
        x+=size[0]+gap;row_height=max(row_height,size[1])
    items.append(export('frame_mount_hardware','框架普通紧固件与底脚 · 84 个独立库存单元',hardware,hardware_units,
        resource_id='consumables:consumable_12',component_label='frame fasteners',nominal_packing_gap_m=gap,
        scope='Geometric resting hypotheses with uniform density; 8 pads retain inferred release liners. No dynamic settling, adhesion, pickup, thread or campaign-reset qualification.'))
    machining=[]
    for color in ['white','black']:
        prefix='COOLER_'+color.upper()+'__';item=pair['cooler_'+color]
        for n in item['frame']['added_parts']:
            suffix=n.removeprefix(prefix)
            if not structural.match(suffix) or suffix.startswith(('frame_rail_','frame_tube_')):continue
            blank='frame_plate_3mm' if suffix.startswith('frame_bridge_') or suffix=='frame_carriage_lower' else 'frame_carriage_plate_4mm' if suffix=='frame_carriage_upper' else 'frame_clamp_block_20mm'
            machining.append(dict(id=color+'_'+suffix,blank=blank,output_template=dict(asset_id=item['id'],part=n),
                output_size_m=parts[item['id']][n].extents.tolist(),manufacturing_qualified=False))
    assert len(machining)==20
    out=dict(schema_version=1,items=items,machining_requirements=machining,selected_for_pair_only=True,
        scene_integration_accepted=False,campaign_allocation_complete=False,owner_acceptance=None,
        source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),HERE/'apparatus_stock_reconciliation.json',HERE/'apparatus_frame_sources.json']],
        limits=['Scene placement and campaign reservations require separate verification; these meshes alone give no starting-stock acceptance','Source drawings and dimensions do not establish tolerances, material grade or commercial compatibility',
                'Cut envelopes, machine tool access and ordinary manufacturing/tool stock still need independent checks','No stock for failed trials or validation resets is allocated'])
    write_json(HERE/'frame_stock.json',out)
    print(json.dumps(dict(stock_assets=len(items),stock_units=sum(len(i['units']) for i in items),hardware_units=len(hardware_units),machined_output_parts=len(machining),hardware_bounds_m=hardware.bounds.tolist())))


if __name__=='__main__':build()
