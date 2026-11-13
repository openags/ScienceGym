"""Compare native convex contacts with source triangles at authored coupon poses.

This is a static geometry diagnosis, not an initial-state or execution approval.
The model, other object poses and collision filters remain unchanged.
"""
import argparse
import json
from pathlib import Path
import shutil

import fcl
import mujoco
import numpy as np
import trimesh

from frozen_collision_plugins import load, sha


def source_mesh(model, data, gid):
    mid = int(model.geom_dataid[gid])
    start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
    vertices = model.mesh_vert[start:start+count].astype(float)
    vertices = vertices @ data.geom_xmat[gid].reshape(3, 3).T + data.geom_xpos[gid]
    start, count = model.mesh_faceadr[mid], model.mesh_facenum[mid]
    faces = model.mesh_face[start:start+count].copy()
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def collision_object(mesh):
    geometry = fcl.BVHModel()
    geometry.beginModel(len(mesh.vertices), len(mesh.faces))
    geometry.addSubModel(mesh.vertices, mesh.faces)
    geometry.endModel()
    return fcl.CollisionObject(geometry)


def compare_meshes(first, second):
    a, b = collision_object(first), collision_object(second)
    result = fcl.CollisionResult()
    fcl.collide(a, b, fcl.CollisionRequest(), result)
    distance = fcl.DistanceResult()
    fcl.distance(a, b, fcl.DistanceRequest(enable_nearest_points=True), distance)
    return dict(intersects=bool(result.is_collision), distance_m=float(distance.min_distance),
                nearest_points=[np.asarray(v).tolist() for v in distance.nearest_points])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    scene, out = args.scene.resolve(), args.output.resolve()
    binding = json.loads((scene/'binding.json').read_text())
    state = json.loads((scene/'initial_state.json').read_text())
    assert sha(scene/'world.xml') == binding['world_sha256']
    assert sha(scene/'initial_state.json') == binding['initial_state_sha256']
    loader = Path(__file__).with_name('frozen_collision_plugins.py')
    load(binding['collision_plugins'], sha(loader))
    model = mujoco.MjModel.from_xml_path(str(scene/'world.xml'))
    data = mujoco.MjData(model)
    data.qpos[:], data.qvel[:] = state['qpos'], state['qvel']
    mujoco.mj_forward(model, data)
    original = data.qpos.copy()
    normal = data.body('carrier_tray').xmat.reshape(3, 3)[:, 2].copy()
    previous_gap = binding['specimen_initial_support']['initial_release_gap_m']
    tray = model.geom('tray_contact_6').id
    copper = model.geom('optical_copper_witness').id
    rows = []
    for gap in [.002, .0005, .0003, .0002, .00002]:
        data.qpos[:] = original
        data.joint('optical_witness_white_free').qpos[:3] -= (previous_gap-gap)*normal
        mujoco.mj_forward(model, data)
        first, second = [source_mesh(model, data, gid) for gid in [tray, copper]]
        contacts = [dict(distance_m=float(c.dist), position_m=c.pos.tolist(),
                         normal=c.frame[:3].tolist()) for c in data.contact
                    if set(map(int, c.geom)) == {tray, copper}]
        row = dict(authored_gap_m=gap, native_contacts=contacts,
                   source_triangles=compare_meshes(first, second),
                   convex_hulls=compare_meshes(first.convex_hull, second.convex_hull),
                   mesh_properties=[dict(name=model.geom(gid).name, vertices=len(mesh.vertices),
                       triangles=len(mesh.faces), is_convex=bool(mesh.is_convex),
                       bounds_m=mesh.bounds.tolist())
                       for gid, mesh in [(tray, first), (copper, second)]])
        rows.append(row)
        print(json.dumps(row), flush=True)
    out.mkdir(parents=True, exist_ok=False)
    for path in [Path(__file__), loader]:
        shutil.copyfile(path, out/path.name)
    report = dict(scope=__doc__, scene_binding_sha256=sha(scene/'binding.json'),
                  script_sha256=sha(__file__), rows=rows,
                  qualified_asset_support=False, qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
