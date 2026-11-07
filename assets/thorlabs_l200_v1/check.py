"""Check delivered triangles against STEP/drawing facts, without granting fit."""
import json
from pathlib import Path
import numpy as np
import trimesh
from build import HERE, ROOT, artifact, sha, close_collinear_seams


def check():
    source = json.loads((HERE / 'sources.json').read_text())
    model = json.loads((HERE / 'model.json').read_text())
    checks = []

    def require(name, value, **details):
        checks.append(dict(name=name, passed=bool(value), **details))
        if not value:
            raise AssertionError(name + ' ' + str(details))

    for entry in model['source_artifacts'] + [model['geometry'], model['rejected_tessellation']]:
        require('pinned_' + entry['path'], sha(ROOT / entry['path']) == entry['sha256'])
    scene = trimesh.load(ROOT / model['geometry']['path'], force='scene')
    upper_render = scene.geometry['L200_M__solid_000']
    flat_faces = np.all(abs(upper_render.triangles[:, :, 2] - model['source_pose_height_m']) < 1e-7, axis=1)
    require('flat_plate_keeps_flat_render_normals', flat_faces.sum() > 100 and np.all(upper_render.vertex_normals[upper_render.faces[flat_faces], 2] > .999))
    # Render-normal splits are intentional. Only weld identical delivered
    # positions to assess physical mesh closure; do not fill source openings.
    for mesh in scene.geometry.values():
        mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=8)
    parts = {p['id']: p for p in model['parts']}
    require('all_86_source_solids_preserved', set(scene.geometry) == set(parts) and len(parts) == 86)
    transform = np.array(model['source_to_scene_matrix'])
    require('rigid_rotation_and_unit_conversion_only', np.allclose(transform[:3, :3].T @ transform[:3, :3], np.eye(3) * 1e-6, atol=1e-14) and np.linalg.det(transform[:3, :3]) > 0)
    require('plate_and_bottom_bearing_origin', abs(scene.bounds[0, 2]) < 1e-7)
    require('retracted_source_height_matches_rounded_drawing', abs(scene.bounds[1, 2] * 1000 - source['drawing_facts']['retracted_height_mm']) < .05)
    require('no_invented_extended_pose', abs(model['source_pose_height_m'] - .021336) < 1e-7)
    open_meshes = []
    for identity, record in parts.items():
        matrix, geometry = scene.graph[identity]
        mesh = scene.geometry[geometry]
        require('geometry_' + identity,
                np.allclose(matrix, np.eye(4), atol=1e-12) and
                np.allclose(mesh.bounds, record['bounds_m'], atol=1e-9) and
                len(mesh.faces) == record['faces'] and record['step_valid'] and
                mesh.is_winding_consistent and np.isfinite(mesh.vertices).all() and
                abs(mesh.volume / record['step_volume_m3'] - 1) < .005)
        require('topology_report_' + identity, mesh.is_watertight == record['watertight'])
        if not mesh.is_watertight:
            open_meshes.append(identity)
    plate_findings = []
    for index in [0, 1]:
        identity = f'L200_M__solid_{index:03d}'
        record = parts[identity]
        mesh = scene.geometry[identity]
        require('plate_closed_' + str(index), mesh.is_watertight)
        require('plate_nominal_dimensions_' + str(index), np.allclose(mesh.extents[:2], [.1016, .0762], atol=1e-7))
        all_holes = []
        for radius, count, label in [(.0015, 18, 'M3'), (.002, 4, 'M4'), (.003, 7, 'M6')]:
            xy = sorted({tuple(np.round(f['axis_origin_m'][:2], 8)) for f in record['cylindrical_faces']
                         if abs(f['radius_m'] - radius) < 1e-8 and abs(f['axis'][2]) > .999})
            require('drawing_hole_count_' + str(index) + '_' + label, len(xy) == count)
            rays = np.array([[*p, .04] for p in xy])
            blocked = mesh.ray.intersects_any(rays, np.tile([0, 0, -1], (len(rays), 1)))
            require('actual_mesh_open_bores_' + str(index) + '_' + label, not blocked.any())
            all_holes.extend(dict(thread=label, center_xy_m=list(p), nominal_diameter_m=2 * radius) for p in xy)
        slots = np.array([[x, y, .04] for x in [-.0375, .0375] for y in [-.025, 0, .025]])
        require('actual_mesh_open_mount_slots_' + str(index), not mesh.ray.intersects_any(slots, np.tile([0, 0, -1], (6, 1))).any())
        require('solid_plate_positive_ray_control_' + str(index), mesh.ray.intersects_any([[.045, .030, .04]], [[0, 0, -1]])[0])
        # A bounding-box substitute passes envelope checks but loses every hole.
        proxy = trimesh.creation.box(mesh.extents)
        proxy.apply_translation(mesh.bounds.mean(axis=0))
        require('negative_bounding_box_is_not_the_plate_' + str(index), proxy.ray.intersects_any(slots, np.tile([0, 0, -1], (6, 1))).all())
        plate_findings.append(dict(id=identity, holes=all_holes, open_slot_centers_xy_m=slots[:, :2].tolist()))
    repaired = [p['id'] for p in model['parts'] if p['seam_repair']['splits']]
    require('all_delivered_solids_are_closed', not open_meshes)
    require('four_repaired_seams_are_documented', len(repaired) == 4 and sum(parts[n]['seam_repair']['splits'] for n in repaired) == 14 and all(parts[n]['seam_repair']['vertices_moved'] == 0 for n in repaired))
    rejected = trimesh.load(ROOT / model['rejected_tessellation']['path'], force='scene')
    require('negative_raw_tessellation_retained', set(rejected.geometry) == set(repaired) and all(not m.is_watertight for m in rejected.geometry.values()))
    # The repair must not fill an actual opening. A box with a missing face
    # remains open because its boundary contains no collinear T-junction.
    missing_face = trimesh.creation.box()
    missing_face.update_faces(np.arange(len(missing_face.faces)) != 0)
    vertices, faces = missing_face.vertices.copy(), missing_face.faces.copy()
    repair = close_collinear_seams(missing_face)
    require('negative_real_hole_is_not_capped', not missing_face.is_watertight and repair['splits'] == 0 and np.array_equal(vertices, missing_face.vertices) and np.array_equal(faces, missing_face.faces))
    require('source_selection_is_not_installation_acceptance', not model['accepted'] and not model['physical_installation_qualified'] and not model['collision_or_dynamics_qualified'])
    report = dict(schema_version=1, passed=True, checks=checks,
                  scope='Source identity, scale, part retention, volume and actual plate openings; not mounting, collision-shape or actuation qualification',
                  plates=plate_findings, open_meshes=open_meshes,
                  repaired_meshes=repaired,
                  source_coincident_pairs=model['coincident_source_solids'],
                  owner_acceptance=None, installation_qualified=False,
                  source_artifacts=[artifact(p) for p in [Path(__file__), HERE / 'model.json', HERE / 'sources.json', ROOT / model['geometry']['path'], ROOT / model['rejected_tessellation']['path']]])
    (HERE / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, checks=len(checks), source_solids=len(parts), plates=len(plate_findings), open_meshes=len(open_meshes))))


if __name__ == '__main__':
    check()
