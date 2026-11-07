"""Measure ordinary driver access at the actual exported apparatus screws.

This is an asset inspection, not a robot controller or assembly procedure.
Installed-state obstruction may require an earlier assembly stage; a clear
static tool pose does not prove its insertion path, hand access or torque.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from geometry_tools import HERE, ROOT, sha, write_json
from build_stock_cutplan import load_parts
from check_apparatus_frame import solid, intersection_mm3


def socket_spec(name):
    if name.startswith('base_screw_'):return [0,0,1],2.5,1.3
    if name.startswith('platform_screw_'):return [0,0,-1],2,1.1
    if name.startswith('frame_bridge_') and name.endswith('_screw'):return [0,0,1],3,1.3
    if name.startswith('frame_clamp_') and '_screw_' in name:return [1 if '_left_' in name else -1,0,0],3,1.3
    if name.startswith(('frame_lower_pinch_','frame_upper_pinch_')):return [0,1,0],3,2
    if name.startswith('frame_track_') and '_screw_' in name:return [0,0,-1],2.5,1.3
    if name.startswith('frame_carriage_screw_'):return [0,0,-1],2,1.1
    if name.startswith('shield_base_screw_'):return [0,0,-1],2.5,1.3
    if name.startswith('shield_side_screw_'):
        angle=np.radians([30,150,270][int(name.rsplit('_',1)[1])-1]);return [-np.cos(angle),-np.sin(angle),0],2.5,1.3
    return None


def build(configuration='cooler_white'):
    apparatus=json.loads((HERE/'apparatus_stock_reconciliation.json').read_text())
    tools=json.loads((HERE/'fastener_tools.json').read_text());verified=json.loads((HERE/'fastener_tool_checks.json').read_text())
    assert verified['passed']
    for ref in verified['source_artifacts']:assert sha(ROOT/ref['path'])==ref['sha256'],ref
    for item in tools['items']:assert sha(ROOT/item['geometry']['path'])==item['geometry']['sha256'],item['id']
    model=next(r for r in apparatus['items'] if r['id']==configuration)
    assert sha(ROOT/model['geometry']['path'])==model['geometry']['sha256']
    prefix={'cooler_white':'COOLER_WHITE__','cooler_black':'COOLER_BLACK__','cooler_fixed':'COOLER_FIXED_BAND__'}[configuration]
    parts={n.removeprefix(prefix):m for n,m in load_parts(model['geometry']['path']).items()}
    # Work near the local origin so solid Boolean precision does not depend on
    # the legacy source file's metre-scale layout offsets.
    origin=parts['lift_plate'].bounds.mean(axis=0)
    for m in parts.values():m.apply_translation(-origin)
    drivers={i['interface']['nominal_af_mm']:i for i in tools['items'] if i['id'].startswith('wiha')}
    tool_meshes={key:{n:m for n,m in load_parts(i['geometry']['path']).items() if n!='size_label'} for key,i in drivers.items()}
    rows=[];mesh_cache={};unknown=set()
    def volume(a,name):
        if name not in mesh_cache:mesh_cache[name]=solid(parts[name])
        if not mesh_cache[name].is_volume:unknown.add(name);return None
        return intersection_mm3(a,mesh_cache[name])
    for name,fastener in parts.items():
        spec=socket_spec(name)
        if spec is None:continue
        inward,drive,depth=spec;axis=np.asarray(inward,dtype=float)
        center=solid(fastener).center_mass;opening=float((fastener.vertices@axis).min())
        tip=center+axis*(opening-center@axis+(depth-.15)*.001)
        base=trimesh.geometry.align_vectors([1,0,0],-axis);base[:3,3]=tip
        candidates=[]
        for angle in [0,30]:
            matrix=base@trimesh.transformations.rotation_matrix(np.radians(angle),[1,0,0])
            shaft=tool_meshes[drive]['shaft'].copy();shaft.apply_transform(matrix)
            candidates.append((intersection_mm3(shaft,fastener),angle,matrix))
        fit,angle,matrix=min(candidates,key=lambda r:r[0]);obstructions=[];unresolved=[]
        for tool_part,m in tool_meshes[drive].items():
            posed=m.copy();posed.apply_transform(matrix)
            # Bounding boxes retain complete-containment cases that a surface
            # intersection query can miss; solid intersection decides the result.
            contacts=[n for n,m in parts.items() if np.all(np.minimum(posed.bounds[1],m.bounds[1])-np.maximum(posed.bounds[0],m.bounds[0])>1e-10)]
            for other in sorted(contacts):
                if other==name:continue
                overlap=volume(posed,other)
                if overlap is None:unresolved.append(dict(tool_part=tool_part,apparatus_part=other,reason='intersecting mesh is not a positive closed solid'))
                elif overlap>.001:obstructions.append(dict(tool_part=tool_part,apparatus_part=other,intersection_mm3=overlap))
        status='socket_fit_unresolved' if fit>.001 else 'geometry_unresolved' if unresolved else 'installed_state_obstructed' if obstructions else 'static_tool_pose_candidate'
        row=dict(fastener=name,tool=drivers[drive]['id'],inward_axis=axis.tolist(),socket_depth_mm=depth,
            selected_twist_degrees=angle,analysis_from_tool=matrix.tolist(),socket_intersection_mm3=fit,
            obstructions=obstructions,unresolved_contacts=unresolved,status=status)
        rows.append(row);print(json.dumps(dict(fastener=name,status=status,obstructions=len(obstructions))),flush=True)
    assert len(rows)==(34 if configuration=='cooler_fixed' else 36),len(rows)
    wrench_item=next(i for i in tools['items'] if i['id']=='stahlwille_40080808')
    wrench=load_parts(wrench_item['geometry']['path'])['forged_wrench'];jaw=np.array(wrench_item['interface']['open_jaw_center_m'])
    wrench_rows=[]
    for name,part in parts.items():
        if not (name.startswith('frame_bridge_') and name.endswith('_nut')):continue
        center=solid(part).center_mass;poses=[]
        for clocking in range(0,360,60):
            matrix=trimesh.transformations.rotation_matrix(np.radians(clocking-15),[0,0,1]);matrix[:3,3]=center-matrix[:3,:3]@jaw
            posed=wrench.copy();posed.apply_transform(matrix);fit=intersection_mm3(posed,part);obstructions=[];unresolved=[]
            for other,m in parts.items():
                if other==name or np.any(np.minimum(posed.bounds[1],m.bounds[1])-np.maximum(posed.bounds[0],m.bounds[0])<=1e-10):continue
                overlap=volume(posed,other)
                if overlap is None:unresolved.append(other)
                elif overlap>.001:obstructions.append(dict(apparatus_part=other,intersection_mm3=overlap))
            poses.append(dict(clocking_degrees=clocking,analysis_from_tool=matrix.tolist(),nut_intersection_mm3=fit,
                obstructions=obstructions,unresolved_contacts=unresolved,static_wrench_pose_candidate=fit<.001 and not obstructions and not unresolved))
        wrench_rows.append(dict(nut=name,tool=wrench_item['id'],poses=poses,static_candidates=sum(p['static_wrench_pose_candidate'] for p in poses)))
    assert len(wrench_rows)==4
    counts={k:sum(r['status']==k for r in rows) for k in ['static_tool_pose_candidate','installed_state_obstructed','socket_fit_unresolved','geometry_unresolved']}
    files=[Path(__file__),HERE/'fastener_tools.json',HERE/'fastener_tool_checks.json',HERE/'apparatus_stock_reconciliation.json',HERE/'check_apparatus_frame.py']
    report=dict(schema_version=2,status='asset_access_inspection_not_execution',configuration=configuration,
        apparatus_geometry=model['geometry'],source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],
        analysis_origin_in_source_m=origin.tolist(),analysis_axes='Same as source apparatus; source position = analysis position + analysis_origin_in_source_m',
        counts=counts,fasteners=rows,wrench_nuts=wrench_rows,unresolved_meshes=sorted(unknown),
        scope='Authored apparatus screw sockets and four bridge nuts; manufacturer-preassembled jack internals excluded. Actual exported configuration, no table, hand, insertion sweep or torque.',
        interpretation='An obstructed installed-state pose requires a supported earlier assembly state, another ordinary tool or a geometry revision. It is not proof that assembly is impossible.',
        owner_acceptance=None,assembly_qualified=False,robot_use_qualified=False)
    output='tool_access_inspection.json' if configuration=='cooler_white' else 'tool_access_'+configuration+'.json'
    write_json(HERE/output,report);print(json.dumps(dict(configuration=configuration,fasteners=len(rows),wrench_static_candidates=[r['static_candidates'] for r in wrench_rows],**counts)))


if __name__=='__main__':
    for identity in ['cooler_white','cooler_black','cooler_fixed']:build(identity)
