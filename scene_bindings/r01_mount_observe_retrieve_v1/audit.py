#!/usr/bin/env python3
"""Offline R01 binding audit. Validates declarations, never robot/physics execution."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
SEGMENT = ['TEST01', 'TEST02', 'TEST03', 'BND_FREE', 'OBS01', 'TEST04',
           'LOAD', 'UNLOAD', 'OBS_RESIDUAL', 'RELOAD', 'TEST_REMOVE']
FALSE_CLAIMS = {'robot_execution', 'physics_executed', 'robot_visibility_validated',
                'grasp_validated', 'collision_validated', 'sensor_calibrated',
                'simready_validated', 'runnable_episode'}
REQUIRED_GATES = {'G_INTERFACE_QUALIFICATION', 'G_TRANSPORT_CLIP_GEOMETRY',
                  'G_SENSOR_CONFIGURATION', 'G_OCCLUSION', 'G_STATE_INSTANTIATION',
                  'G_PHYSICS', 'G_SOURCE_REBUILD_INPUT'}
SOURCE_FILES = {'tasks/chiral_operations_v2/operations.json',
                'tasks/chiral_operations_v2/branches.json',
                'tasks/chiral_operations_v2/assets.json',
                'viewer/embodied_r01/frame_manifest.json',
                'viewer/embodied_r01/trajectory.json',
                'viewer/embodied_r01/scripts/build_visual.py',
                'viewer/embodied_r01/render_receipt.json'}
SOURCE_SHA = 'bbcf496ca4c1eaa16a56db472e54d944a8d54bc19c7e00073afe32fe9e6ca915'


def expected_scene_roles(names):
    """Explicit authored role mapping; never accept any merely existing object."""
    return {
        'specimen': {n for n in names if n.startswith('WS_TEST__mounted_')},
        'transport_tray': {'WS_TEST__carrier_base','WS_TEST__carrier_handle_-0.57','WS_TEST__carrier_handle_-0.33'},
        'tester_stage': {'WS_TEST__carrier_base'},
        'guard': {'WS_TEST__guard_front_panel','WS_TEST__guard_handle'},
        'tester_panel': {'WS_TEST__panel_console','WS_TEST__panel_screen','WS_TEST__button_START','WS_TEST__button_STOP'},
        'upper_platen': {'WS_TEST__upper_platen'}, 'lower_platen': {'WS_TEST__lower_platen'},
        'removable_fixture': {'WS_TEST__sidebox_wall_L','WS_TEST__sidebox_wall_R','WS_TEST__sidebox_wall_back','WS_TEST__rotation_lock_arm'},
        'transport_support': {'WS_TEST__carrier_base'},
        'interface_ring': {n for n in names if n.startswith('WS_TEST__mounted_cell_') and '_ring' in n},
        'transport_clip': set(), 'rotation_lock': {'WS_TEST__rotation_lock_arm'},
        'camera': {'WS_TEST__camera_body','WS_TEST__camera_lens'}, 'camera_stand': {'WS_TEST__camera_stand'},
        'box_walls': {'WS_TEST__sidebox_wall_L','WS_TEST__sidebox_wall_R','WS_TEST__sidebox_wall_back'},
    }


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('non-JSON number: ' + value)
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=constant)


def local_file(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('invalid relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('unsafe relative path')
    candidate = root / path
    candidate.resolve().relative_to(root.resolve())
    if not candidate.is_file():
        raise ValueError('missing file: ' + name)
    return candidate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_matrix(value):
    return (isinstance(value, list) and len(value) == 4 and
            all(isinstance(row, list) and len(row) == 4 for row in value) and
            all(type(x) in (int, float) and math.isfinite(x) for row in value for x in row) and
            value[3] == [0, 0, 0, 1])


def audit(root=ROOT, binding=None, inventory=None, excerpt=None, receipt=None):
    """Return actionable issues. Injectable documents support negative-fixture tests."""
    root = Path(root)
    package = root / 'scene_bindings/r01_mount_observe_retrieve_v1'
    issues = []
    counts = {}
    def require(ok, code, at, message):
        if not ok:
            issues.append({'code': code, 'at': at, 'message': message})
        return bool(ok)
    def index(rows, field, label):
        if not isinstance(rows, list):
            raise ValueError(label + ' must be an array')
        ids = [row[field] for row in rows]
        require(len(ids) == len(set(ids)), 'DUPLICATE_ID', label, 'IDs must be unique')
        return dict(zip(ids, rows))
    try:
        b = binding if binding is not None else read_json(package / 'binding.json')
        require(b['source_scene']['snapshot_inventory'] == 'source_evidence/source_inventory.json' and
                b['source_scene']['evidence_manifest'] == 'source_evidence/evidence_manifest.json' and
                b['cameras']['source_review']['receipt'] == 'source_evidence/render_receipt.json',
                'EVIDENCE_REFERENCE', 'source_scene', 'Selected inventory, manifest and receipt must be the exact frozen evidence files')
        inv = inventory if inventory is not None else read_json(local_file(package, b['source_scene']['snapshot_inventory']))
        ex = excerpt if excerpt is not None else read_json(package / 'source_contract_excerpt.json')
        require(digest(package / 'source_contract_excerpt.json') == b['source_scene']['source_contract_excerpt_sha256'],
                'EVIDENCE_HASH', 'source_contract_excerpt.json', 'Frozen extracted source-contract facts changed')
        r = receipt if receipt is not None else read_json(local_file(package, b['cameras']['source_review']['receipt']))
        require(b['schema_version'] == 'sciencegym.r01_task_scene_binding.v1' and b['status'] == 'static_binding_contract_with_open_execution_gates', 'SCHEMA', 'schema_version', 'Unsupported schema')
        require(set(b['claims']) == FALSE_CLAIMS and all(v is False for v in b['claims'].values()),
                'OVERCLAIM', 'claims', 'All execution, sensor, SimReady and robot-feasibility claims must remain false')
        require(b['scope']['operation_ids'] == SEGMENT and b['scope']['branch_id'] == 'R01' and
                b['scope']['condition_id'] == 'cond.R01' and b['scope']['station_id'] == 'WS_TEST',
                'SCOPE', 'scope', 'This audit covers only the declared R01 eleven-operation segment')
        src = index(b['source_inputs'], 'path', 'source_inputs')
        require(set(src) == SOURCE_FILES, 'SOURCE_COVERAGE', 'source_inputs', 'Every task/storyboard source must be pinned')
        for path, record in src.items():
            require(digest(local_file(root, path)) == record['sha256'], 'SOURCE_HASH', path, 'Source drift; review before rebinding')
        ops = index(read_json(root / 'tasks/chiral_operations_v2/operations.json')['operations'], 'id', 'source operations')
        branch = next(x for x in read_json(root / 'tasks/chiral_operations_v2/branches.json')['branches'] if x['id'] == 'R01')
        assets = index(read_json(root / 'tasks/chiral_operations_v2/assets.json')['assets'], 'role_id', 'source roles')
        frames = index(read_json(root / 'viewer/embodied_r01/frame_manifest.json')['frames'], 'id', 'source frames')
        require(branch['operation_sequence'][12:23] == SEGMENT, 'SOURCE_ORDER', 'scope', 'Segment must retain source reference order')
        require(b['source_scene']['sha256'] == ex['source_scene_sha256'] == inv['source_scene_sha256'] == SOURCE_SHA,
                'SCENE_HASH', 'source_scene', 'All evidence must identify the recovered original scene bytes')
        objects = index(inv['objects'], 'name', 'source inventory objects')
        object_names = set(objects)
        require(set(ex['object_ids']) <= object_names, 'SCENE_REFERENCE', 'source_contract_excerpt.object_ids', 'Source sidecar objects must exist in inspected .blend inventory')
        require(ex['source_scene_is_episode_initial_state'] is False, 'OVERCLAIM', 'source_contract_excerpt', 'All-stage source cannot be treated as a valid initial state')
        original_hashes = {s['path']:s['sha256'] for s in inv['source_files']}
        require(all(original_hashes.get(s['path_in_original_package']) == s['sha256'] for s in ex['source_files']),
                'PROVENANCE', 'source_contract_excerpt.source_files', 'Extracted source hashes must agree with the frozen Blender inventory')
        station = next(s for s in inv['stations'] if s['station_id'] == 'WS_TEST')
        require(ex['station']['id'] == 'WS_TEST' and ex['station']['world_center_xy_m'] == station['world_center_xy_m'] and
                ex['station']['authored_yaw_deg'] == station['authored_yaw_deg'] and ex['station']['physical_lab_layout_recovered'] is False,
                'PROVENANCE', 'source_contract_excerpt.station', 'Authored station layout is not recovered physical laboratory geometry')
        affs = index(ex['affordances'], 'id', 'source affordances')
        for aid, aff in affs.items():
            require(aff['implementation'] == 'sidecar display transform only, no joint or sensor', 'OVERCLAIM', aid, 'Source affordances are static display metadata')
            require(set(aff['part_ids']) <= object_names, 'SCENE_REFERENCE', aid, 'Affordance refers to unknown source object')
        gates = index(b['execution_gates'], 'id', 'execution_gates')
        require(set(gates) == REQUIRED_GATES and all(g.get('reason') for g in gates.values()),
                'MISSING_GATE', 'execution_gates', 'Required unresolved execution gates cannot be dropped')
        ports = index(b['ports'], 'id', 'ports')
        locals_ = index(b['local_frames'], 'id', 'local_frames')
        expected_roles = {role for oid in SEGMENT for role in ops[oid]['target_asset_roles']}
        require({p['task_role_id'] for p in ports.values()} == expected_roles and len(ports) == len(expected_roles),
                'ROLE_COVERAGE', 'ports', 'Account for every task target role exactly once')
        for pid, port in ports.items():
            role = port['task_role_id']
            require(role in assets and pid == 'port.' + role, 'ROLE_REFERENCE', pid, 'Task role and stable port ID must agree')
            names = port['scene_object_ids']
            require(isinstance(names, list) and all(isinstance(n, str) for n in names) and set(names) == expected_scene_roles(ex['object_ids']).get(role), 'ROLE_SCENE_IDENTITY', pid, 'Existing geometry must still represent the declared task role')
            require(len(names) == len(set(names)) and set(names) <= object_names and set(names) <= set(ex['object_ids']),
                    'SCENE_REFERENCE', pid, 'Exact, unique source object IDs are required; prefixes are not instances')
            require(isinstance(port['execution_gate_ids'], list) and all(isinstance(x, str) for x in port['execution_gate_ids']) and set(port['execution_gate_ids']) <= set(gates) and 'G_INTERFACE_QUALIFICATION' in port['execution_gate_ids'],
                    'GATE_REFERENCE', pid, 'Interface remains unqualified')
            require(port['physical_interface_pose'] is None and port['implementation'].startswith('metadata_only;'),
                    'OVERCLAIM', pid, 'Do not promote object origins to physical action interfaces')
            expected_affs = {aid for aid, a in affs.items() if set(names) & set(a['part_ids'])}
            require(isinstance(port['source_affordance_ids'], list) and all(isinstance(x, str) for x in port['source_affordance_ids']) and set(port['source_affordance_ids']) == expected_affs,
                    'AFFORDANCE_REFERENCE', pid, 'Affordance references must match source object membership')
            require(port['provenance']['kind'] == 'authored_role_to_proxy_binding' and
                    port['provenance']['task_asset_role_id'] == role and
                    port['provenance']['task_asset_limit'] == assets[role]['source_limit'],
                    'PROVENANCE', pid, 'Keep authored binding and task limitations explicit')
            if role == 'transport_clip':
                require(not names and port['resolution'] == 'explicit_missing_geometry' and port['local_frame_id'] is None
                        and 'G_TRANSPORT_CLIP_GEOMETRY' in port['execution_gate_ids'],
                        'MISSING_GEOMETRY', pid, 'Unidentified transport clip must remain explicitly unresolved')
            else:
                require(bool(names) and port['resolution'] == 'resolved_authored_geometry', 'MISSING_GEOMETRY', pid, 'Known source role needs actual object names')
                fid = port['local_frame_id']
                if require(fid in locals_, 'FRAME_REFERENCE', pid, 'Missing local frame'):
                    frame = locals_[fid]
                    anchor = frame['anchor_object_id']
                    require(anchor in names, 'FRAME_ANCHOR', fid, 'Local frame must belong to its bound role')
                    require(numeric_matrix(frame['matrix_local_to_world']), 'TRANSFORM', fid, 'Finite homogeneous 4x4 local-to-world matrix required')
                    if anchor in objects:
                        require(frame['matrix_local_to_world'] == objects[anchor]['matrix_world'], 'TRANSFORM', fid, 'Frame must match inspected source object origin')
                    require(frame['meaning'] == 'authored_object_origin_not_grasp_or_sensor_frame', 'OVERCLAIM', fid, 'Object origin is not a calibrated interface')
        require(set(locals_) == {p['local_frame_id'] for p in ports.values() if p['local_frame_id']}, 'FRAME_COVERAGE', 'local_frames', 'No missing or orphan local frames')
        sample = b['sample']
        require(sample['physical_object_id'] == branch['physical_object_id'] and sample['condition_id'] == branch['condition_id'] and sample['geometry_role'] == 'port.specimen',
                'STATE_IDENTITY', 'sample', 'Preserve specimen/condition identity')
        require(sample['source_envelope_mm'] == branch['source_parameters']['envelope_mm'] and
                sample['physical_reference_envelope_m'] == [x / 1000 for x in sample['source_envelope_mm']] == ex['source_specimen_reference_m'],
                'UNITS', 'sample', 'Physical reference dimensions must use explicit millimetre-to-metre conversion')
        require(sample['source_total_cycles'] is None and sample['design_total_cycles'] == branch['design_cycles'] == 2,
                'CYCLE_IDENTITY', 'sample', 'Two cycles are authored; source total remains unknown')
        require(sample['source_unit_lineage'] == frames['TEST01']['source_unit_lineage'], 'STATE_IDENTITY', 'sample', 'Keep all eighteen authored half-unit lineage IDs')
        expected_units = {'canonical_length':'m','source_length':'mm','source_to_canonical_length':.001,'angle':'rad',
                          'coordinate_handedness':'right','up_axis':'+Z','transform_direction':'local_to_world','matrix_layout':'row_major_4x4'}
        require(all(b['units'].get(k) == v for k, v in expected_units.items()), 'UNITS', 'units', 'Units, axes and transform conventions must be explicit and compatible')
        require(type(b['display']['nominal_scale']) in (int,float) and b['display']['nominal_scale'] == 1 and
                b['display']['physical_reference_must_not_follow_display'] is True and
                b['display']['illustrative_axial_scale_by_frame'] == {'LOAD':.75,'RELOAD':.75} and b['display']['scientific_deformation'] is False and b['display']['source_explicit_enlargement_factor'] is None,
                'DISPLAY_SCALE', 'display', 'Authored axial display deformation must not alter physical reference dimensions')
        states = index(b['semantic_states'], 'id', 'semantic_states')
        bindings = index(b['bindings'], 'operation_id', 'bindings')
        require(list(bindings) == SEGMENT, 'BINDING_COVERAGE', 'bindings', 'Bind every segment operation exactly once in reference order')
        require(set(states) == {'state.' + oid for oid in SEGMENT}, 'STATE_COVERAGE', 'semantic_states', 'One intended state declaration per keyframe is required')
        for oid, entry in bindings.items():
            if not require(oid in SEGMENT, 'OPERATION_REFERENCE', oid, 'Operation outside supported segment'):
                continue
            op, frame = ops[oid], frames[oid]
            require(entry['frame_id'] == oid and entry['frame_index'] == frame['index'] and entry['frame_image'] == frame['image'],
                    'FRAME_REFERENCE', oid, 'Operation must use its original storyboard keyframe')
            require(entry['station_id'] == op['location_id'] == 'WS_TEST', 'STATION_REFERENCE', oid, 'Operation station differs')
            require(entry['physical_object_id'] == sample['physical_object_id'] == frame['physical_object_id'], 'STATE_IDENTITY', oid, 'Specimen cannot be replaced across mount, observe, repeat and retrieve')
            require(entry['port_ids'] == ['port.' + role for role in op['target_asset_roles']] and set(entry['port_ids']) <= set(ports),
                    'ROLE_COVERAGE', oid, 'Every operation target role must be bound or explicitly gated')
            require(entry['preconditions'] == op['preconditions'] and entry['postconditions'] == op['postconditions'] and entry['source_provenance'] == op['provenance'],
                    'PROVENANCE', oid, 'Keep source-supported stages, authored connectors and unknown parameters intact')
            sid = entry['semantic_state_id']
            if require(sid == 'state.' + oid and sid in states, 'STATE_REFERENCE', oid, 'Missing or wrong semantic state'):
                state = states[sid]
                require(state['physical_object_id'] == sample['physical_object_id'] and state['condition_id'] == sample['condition_id'] and
                        state['source_unit_lineage'] == sample['source_unit_lineage'] and state['boundary'] == branch['boundary'],
                        'STATE_IDENTITY', sid, 'Identity, lineage and free-rotation boundary persist')
                require(state['before'] == frame['sample_state_before'] and state['after'] == frame['sample_state_after'] and
                        state['meaning'] == 'intended authored storyboard pre/postconditions; not measured or executed state',
                        'STATE_SEMANTICS', sid, 'Preserve intended storyboard state without claiming measurements')
                cycles = 1 if oid in ['UNLOAD','OBS_RESIDUAL'] else 2 if oid in ['RELOAD','TEST_REMOVE'] else 0
                require(type(state['completed_cycles_after']) is int and state['completed_cycles_after'] == cycles and state['rendered_pose_may_be_intermediate'] is (oid == 'RELOAD'),
                        'CYCLE_IDENTITY', sid, 'Preserve authored cycle history and grouped RELOAD intermediate-pose caveat')
        camera = b['cameras']['storyboard_review']
        require(camera['role'] == 'authored_review_camera_not_sensor' and camera['intrinsics_calibrated'] is False and camera['robot_visibility_claim'] is False,
                'CAMERA_CLAIM', 'cameras.storyboard_review', 'Review images are not calibrated sensor views')
        expected_cameras = [{'frame_id':oid,'declaration':frames[oid]['camera']} for oid in SEGMENT]
        require(camera['per_frame'] == expected_cameras, 'CAMERA_DECLARATION', 'cameras.storyboard_review', 'Preserve every original camera declaration')
        sensor = b['cameras']['task_camera_proxy']
        require(sensor['port_id'] == 'port.camera' and sensor['scene_objects_are_sensor'] is False and sensor['sensor_configuration'] is None
                and sensor['missing'] == ['optical pose calibration','field of view','near/far clipping','polling rate','resolution','exposure','target visibility verification'] and sensor['gate_id'] == 'G_SENSOR_CONFIGURATION',
                'SENSOR_GATE', 'cameras.task_camera_proxy', 'Mesh body/lens does not supply a sensor or its calibration')
        occ = b['occluders']
        require(occ['storyboard_hidden_prefixes'] == ['WS_TEST__sidebox_','WS_TEST__rotation_lock_'] and
                occ['new_source_review_policy'] == 'retain_all_source_geometry' and occ['occlusion_test_executed'] is False and occ['gate_id'] == 'G_OCCLUSION',
                'OCCLUDER_DECLARATION', 'occluders', 'Declare historical hidden apparatus and retain source geometry for new review')
        # The optional Blender pass supplies a separately hash-bound inspection receipt.
        require(digest(local_file(package, b['source_scene']['evidence_manifest'])) == b['source_scene']['evidence_manifest_sha256'], 'EVIDENCE_HASH', 'evidence_manifest.json', 'Frozen evidence manifest changed')
        evidence_manifest = read_json(local_file(package, b['source_scene']['evidence_manifest']))
        expected_evidence = {'README.md', 'inspect_source.py', 'source_inventory.json',
                             'ws_test_object_names.json', 'render_receipt.json', 'validation.json', 'ws_test_review.png'}
        require({x['path'] for x in evidence_manifest['publication_candidate_files']} == expected_evidence,
                'EVIDENCE_COVERAGE', 'evidence_manifest.json', 'Source snapshot, script, receipt and real render must be covered')
        for entry in evidence_manifest['publication_candidate_files']:
            path = local_file(package / 'source_evidence', entry['path'])
            require(digest(path) == entry['sha256'] and path.stat().st_size == entry['bytes'],
                    'EVIDENCE_HASH', entry['path'], 'Frozen source-inspection evidence changed')
        require(r['status'] == 'complete' and r['render_settings']['engine'] == 'CYCLES' and
                r['render_settings']['cycles_device'] == 'CPU' and r['visibility_overrides'] == [] and
                r['material_overrides'] == [] and r['lighting_overrides'] == [] and
                r['source_unchanged'] is True and r['source_object_transforms_unchanged'] is True and
                r['source_mesh_data_unchanged'] is True and r['source_lighting_unchanged'] is True and
                r['source_visibility_unchanged_except_listed'] is True,
                'RENDER_INTEGRITY', 'source_review', 'CPU review must retain every source occluder, transform, material and light')
        require(r['source_inventory_sha256'] == digest(package / b['source_scene']['snapshot_inventory']) and
                r['script_sha256'] == digest(package / 'source_evidence/inspect_source.py'),
                'EVIDENCE_HASH', 'source_review', 'Receipt must match the inspected inventory and rendering script')
        outputs = r['outputs']
        require(len(outputs) == 2 and {o['path'] for o in outputs} == {'ws_test_review.png','ws_test_review_repeat.png'},
                'RENDER_INTEGRITY', 'source_review.outputs', 'Both fixed-camera renders must be present')
        for output in outputs:
            # Identical second image is intentionally unbundled; check its frozen
            # declaration against the one published image, not a nonexistent file.
            image = local_file(package / 'source_evidence', 'ws_test_review.png')
            require(output['camera_unchanged'] is True and output['sha256'] == digest(image) and output['bytes'] == image.stat().st_size,
                    'RENDER_INTEGRITY', output['path'], 'Published image and frozen identical-repeat declaration must match')
        require(r['repeat_file_hash_identical'] is True and len({o['sha256'] for o in outputs}) == 1,
                'RENDER_REPEAT', 'source_review', 'Recorded identical repeat must be true for both files')
        require(numeric_matrix(r['camera']['matrix_world']) and r['camera_role'].startswith('New fixed human review viewpoint;'),
                'CAMERA_CLAIM', 'source_review', 'Declare the fixed camera as a human review viewpoint')
        require(b['cameras']['source_review']['robot_visibility_claim'] is False and
                b['cameras']['source_review']['role'] == 'authored_fixed_review_view_not_robot_sensor',
                'CAMERA_CLAIM', 'source_review', 'No robot visibility result follows from a source overview')
        require(set(inv['mounted_sample']['object_names']) == set(ports['port.specimen']['scene_object_ids']) and
                len(inv['mounted_sample']['display_station_local_bounds_m']['dimensions']) == 3 and
                all(math.isclose(x,y,rel_tol=0,abs_tol=1e-6) for x,y in zip(inv['mounted_sample']['display_station_local_bounds_m']['dimensions'], sample['physical_reference_envelope_m'])),
                'DISPLAY_SCALE', 'source_inventory.mounted_sample', 'Inspected source bounds must retain their reference scale within 1 micrometre numerical tolerance')
        require(r['source_scene_sha256'] == SOURCE_SHA, 'SCENE_HASH', 'source_review', 'Review must identify the authentic recovered source')
        counts = {'operations':len(bindings), 'task_roles':len(ports), 'resolved_role_bindings':sum(bool(p['scene_object_ids']) for p in ports.values()),
                  'explicit_missing_role_bindings':sum(not p['scene_object_ids'] for p in ports.values()), 'local_frames':len(locals_),
                  'semantic_states':len(states), 'source_station_objects':len(objects), 'source_scene_objects':inv['scene']['object_count'], 'execution_gates':len(gates)}
    except (KeyError, TypeError, ValueError, OSError, StopIteration, AttributeError, IndexError) as exc:
        issues.append({'code':'SCHEMA_OR_INPUT','at':'input','message':str(exc)})
    return {'schema_version':'sciencegym.r01_static_audit.v1', 'passed':not issues,
            'status':'static_contract_pass_with_execution_gates' if not issues else 'static_contract_failed',
            'counts':counts,'issues':issues,
            'meaning':'Checks pinned task data, declared bindings and frozen source-inspection evidence. Does not rerun Blender or establish an executable scene.',
            'not_validated':['physics','grasp/contact','robot reachability','robot sensor visibility','scientific observations','SimReady profile','episode execution']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true', help='print machine-readable results to stdout')
    args = parser.parse_args(argv)
    result = audit(args.root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result['status'])
        print(json.dumps(result['counts'], sort_keys=True))
        for issue in result['issues']:
            print(f"{issue['code']} {issue['at']}: {issue['message']}")
        print(result['meaning'])
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
