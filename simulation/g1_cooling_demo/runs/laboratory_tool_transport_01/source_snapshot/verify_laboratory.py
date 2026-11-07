"""Check the compiled plant against the original full-scene source geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import trimesh

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(folder):
    folder = Path(folder).resolve()
    imported = json.loads((folder/'laboratory_import.json').read_text())
    source_path = ROOT/'assets/cooling_lab_v1/scene.json'
    source = json.loads(source_path.read_text())
    model = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    checks = []

    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))

    check('source_scene_pin', sha(source_path) == imported['scene_sha256'])
    check('source_geometry_pins', all(sha(ROOT/p) == h for p,h in imported['source_inputs'].items()))
    expected = {a['id'] for a in source['assets']}
    actual = [a['id'] for a in imported['imported_instances'] if a['id'] != 'architecture']
    actual += [a['instance'] for a in imported['dynamic_bindings']]
    check('all_original_asset_identities_once', set(actual) == expected and len(actual) == len(expected), count=len(actual))
    check('original_architecture_part_count', sum(p['instance']=='architecture' for p in imported['parts']) == source['architecture']['parts'])
    check('no_standalone_table_or_infinite_floor', all(model.geom(i).name not in {'bench_top','review_floor'} for i in range(model.ngeom)))
    movable = {'pelvis', 'carrier_tray'}
    result_path = folder/'result.json'
    rollout = json.loads(result_path.read_text()) if result_path.exists() else {}
    if rollout.get('payload_present'):
        movable.add('buerkle_spatula' if rollout.get('payload_kind') == 'spatula' else 'calibration_copper_stock')
    roots = {model.body(model.jnt_bodyid[j]).name for j in range(model.njnt) if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE}
    check('floating_robot_and_declared_objects', roots == movable and not np.any(model.eq_type == mujoco.mjtEq.mjEQ_WELD))

    # The importer receipt is not trusted as geometric evidence. Reload every
    # original GLB, then compare its transformed vertices with the compiled mesh.
    frame = np.asarray(imported['lab_from_work'])
    records = {a['id']: a for a in source['assets']}
    records['architecture'] = dict(geometry=source['architecture']['path'], position_m=[0,0,0], yaw_rad=0)
    lookup = {(p['instance'], p['source_part']): p for p in imported['parts']}
    worst = 0.; failures = []; planar = []; counted = 0; triangles = 0
    for identifier in sorted({p['instance'] for p in imported['parts']}):
        asset = records[identifier]
        original = trimesh.load(ROOT/asset['geometry'], force='scene', process=False)
        placement = Rotation.from_euler('z', asset['yaw_rad']).as_matrix()
        for node in original.graph.nodes_geometry:
            transform, name = original.graph[node]
            mesh = original.geometry[name]
            expected_vertices = trimesh.transform_points(mesh.vertices, transform)
            expected_vertices = expected_vertices @ placement.T + asset['position_m']
            row = lookup[(identifier, node)]
            geom = model.geom(row['geom']).id
            mid = model.geom_dataid[geom]
            start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
            vertices = model.mesh_vert[start:start+count] @ data.geom_xmat[geom].reshape(3,3).T + data.geom_xpos[geom]
            vertices = vertices @ frame[:3,:3].T + frame[:3,3]
            error = max(float(cKDTree(vertices).query(expected_vertices)[0].max()),
                        float(cKDTree(expected_vertices).query(vertices)[0].max()))
            worst = max(worst, error)
            if error > 5e-6 or model.mesh_facenum[mid] != len(mesh.faces):
                failures.append(dict(instance=identifier, part=node, vertex_error_m=error,
                                     source_faces=len(mesh.faces), compiled_faces=int(model.mesh_facenum[mid])))
            if row['contact'] == 'none_zero_thickness_source_surface':
                planar.append(dict(instance=identifier, part=node))
                if model.geom_contype[geom] or model.geom_conaffinity[geom]:
                    failures.append(dict(instance=identifier, part=node, collision='unexpected_planar_contact'))
            elif not (model.geom_contype[geom] and model.geom_conaffinity[geom]):
                failures.append(dict(instance=identifier, part=node, collision='missing_contact'))
            counted += 1
            triangles += len(mesh.faces)
    check('compiled_source_triangles_and_placement', not failures, source_parts=counted,
          source_triangles=triangles, maximum_vertex_error_m=worst, failures=failures)
    check('only_zero_thickness_surfaces_noncolliding', all(
        p['contact'] in {'none_zero_thickness_source_surface','source_part_convex_hull'} for p in imported['parts']),
        zero_thickness_parts=planar)

    actor_path = folder/'controller_model/world.xml'
    if actor_path.exists():
        actor = mujoco.MjModel.from_xml_path(str(actor_path))
        actor_names = {actor.body(i).name for i in range(actor.nbody)}
        check('controller_excludes_loose_objects', not any('lab_'+name in actor_names for name in expected)
              and not ((movable-{'pelvis'}) & actor_names) and actor.nq == model.nq-7*(len(movable)-1))
        actor_import = json.loads((folder/'controller_model/laboratory_import.json').read_text())
        check('controller_architecture_prior_matches', actor_import['architecture_only']
              and actor_import['scene_sha256'] == imported['scene_sha256']
              and actor_import['lab_from_work'] == imported['lab_from_work'])
    result = dict(passed=all(c['passed'] for c in checks), checks=checks,
                  verifier_sha256=sha(__file__), world_sha256=sha(folder/'world.xml'),
                  import_sha256=sha(folder/'laboratory_import.json'),
                  scope='Source geometry and compiled full-room contact environment, not device, task or campaign qualification',
                  limitations=['Other equipment stays fixed in its initial pose.',
                               'Per-part convex contacts do not qualify concave cavities, covers or cables.',
                               'Initial tray and robot staging is explicit setup, not robot execution.'])
    (folder/'laboratory_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'], checks=len(checks), source_parts=counted,
                          source_triangles=triangles, maximum_vertex_error_m=worst, failures=failures)))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    args = parser.parse_args()
    if not verify(args.folder)['passed']:
        raise SystemExit(1)
