"""Diagnose compiled polygon normals without changing the source solids.

The MuJoCo 3.16.0 compiler can derive a polygon normal from nearly collinear
outline vertices. Compare its result with a complete-loop area normal, with
the loop oriented away from the convex hull interior. This is a component
diagnostic, not a runtime patch or robot-handling qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def array_hash(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def model_arrays(model):
    return {name: array_hash(getattr(model, name)) for name in dir(model)
            if isinstance(getattr(model, name), np.ndarray)}


def repair_outline_normals(model):
    """Use all existing vertices; preserve positions, hulls and inertia."""
    rows = []
    for mid in range(model.nmesh):
        start, count = int(model.mesh_vertadr[mid]), int(model.mesh_vertnum[mid])
        vertices = model.mesh_vert[start:start+count].astype(np.float64)
        interior = vertices.mean(axis=0)
        for pid in range(int(model.mesh_polyadr[mid]),
                         int(model.mesh_polyadr[mid]+model.mesh_polynum[mid])):
            adr, count = int(model.mesh_polyvertadr[pid]), int(model.mesh_polyvertnum[pid])
            ids = model.mesh_polyvert[adr:adr+count].copy()
            points = vertices[ids]
            centered = points-points.mean(axis=0)
            area = np.sum(np.cross(centered, np.roll(centered, -1, axis=0)), axis=0)
            if np.linalg.norm(area) < 1e-18:
                raise ValueError('Degenerate compiled polygon: '+model.mesh(mid).name)
            normal = area/np.linalg.norm(area)
            outward = float(np.dot(normal, points.mean(axis=0)-interior))
            if abs(outward) < 1e-12:
                raise ValueError('Cannot orient compiled polygon against hull interior')
            reversed_loop = outward < 0
            if reversed_loop:
                normal = -normal
                # Keep the first corner, reversing only traversal direction.
                model.mesh_polyvert[adr:adr+count] = np.r_[ids[0], ids[:0:-1]]
            old = model.mesh_polynormal[pid].astype(np.float64)
            angle = float(np.degrees(np.arccos(np.clip(np.dot(old, normal), -1, 1))))
            if angle > .1 or reversed_loop:
                rows.append(dict(mesh=model.mesh(mid).name, polygon=pid,
                    corners=count, original_normal=old.tolist(),
                    whole_loop_outward_normal=normal.tolist(), angle_degrees=angle,
                    reversed_loop=bool(reversed_loop)))
            model.mesh_polynormal[pid] = normal
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--duration', type=float, default=.1)
    args = parser.parse_args()
    if not .05 <= args.duration <= 3.:
        parser.error('Diagnostic duration must be between 0.05 and 3 seconds')
    source, out = args.source.resolve(), args.output.resolve()
    contract = json.loads((source/'contract.json').read_text())
    assert sha(source/'world.xml') == contract['world_sha256']
    for name, digest in json.loads((source/'model_inputs.json').read_text()).items():
        assert sha(name) == digest
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    results = []
    for variant in ['source_compiler', 'whole_loop_normals']:
        model = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
        before = model_arrays(model)
        changes = repair_outline_normals(model) if variant == 'whole_loop_normals' else []
        after = model_arrays(model)
        changed_arrays = [name for name in before if before[name] != after[name]]
        if set(changed_arrays)-{'mesh_polynormal', 'mesh_polyvert'}:
            raise ValueError('Compiler diagnostic unexpectedly changed other model data')
        if model.nu or model.neq:
            raise ValueError('Expected passive component without actuators or equalities')
        mujoco.mj_saveModel(model, str(out/(variant+'.mjb')))
        (out/(variant+'_compiler.json')).write_text(json.dumps(dict(
            changed_arrays=changed_arrays, before=before, after=after,
            corrected_polygons=changes), indent=2)+'\n')
        for label, offset, yaw in [('center_zero', [0., 0.], 0.),
                ('center_selected', [0., 0.], contract['initial_reference_yaw_degrees']),
                ('offset_y_selected', [0., -.0005], contract['initial_reference_yaw_degrees'])]:
            data = mujoco.MjData(model)
            data.joint('pike_reference_cap_free').qpos[:] = [.15, -.01,
                contract['initial_cap_release_gap_m'], 1., 0., 0., 0.]
            data.joint('pike_reference_free').qpos[:] = [.04+offset[0], -.01+offset[1],
                .10200000356417149+contract['reference_port_support_height_m']+
                contract['initial_reference_release_gap_m'],
                0., np.cos(np.deg2rad(yaw)/2), np.sin(np.deg2rad(yaw)/2), 0.]
            initial = data.qpos.copy()
            mujoco.mj_forward(model, data)
            rid = model.body('pike_reference').id
            optical_id = model.geom('pike_reference_optical_face').id
            peak = lateral = penetration = optical = 0.
            worst = None
            samples = []
            for step in range(round(args.duration/model.opt.timestep)):
                mujoco.mj_step(model, data)
                geoms = np.asarray(data.contact.geom)
                bodies = model.geom_bodyid[geoms]
                relevant = np.flatnonzero(np.any(bodies == rid, axis=1) &
                    (data.contact.efc_address >= 0))
                load = lateral_load = 0.
                if len(relevant):
                    assert int(model.opt.cone) == int(mujoco.mjtCone.mjCONE_ELLIPTIC)
                    assert np.all(data.contact.dim[relevant] == 3)
                    forces = data.efc_force[data.contact.efc_address[relevant]]
                    normals = np.asarray(data.contact.frame)[relevant, :3]
                    load = float(np.sum(forces))
                    lateral_load = float(np.sum(forces[np.abs(normals[:, 2]) < .2]))
                    penetration = max(penetration, -float(np.min(data.contact.dist[relevant])))
                    own = np.where(bodies[relevant, 1] == rid, 1, 0)
                    optical = max(optical, float(np.sum(forces[geoms[relevant, own] == optical_id])))
                    j = int(np.argmax(forces))
                    if worst is None or forces[j] > worst['normal_load_n']:
                        ci = int(relevant[j])
                        worst = dict(time_s=float(data.time), normal_load_n=float(forces[j]),
                            geom_names=[model.geom(int(g)).name for g in geoms[ci]],
                            normal=data.contact.frame[ci, :3].tolist(),
                            distance_m=float(data.contact.dist[ci]))
                peak = max(peak, load)
                lateral = max(lateral, lateral_load)
                if np.any(data.xfrc_applied) or np.any(data.qfrc_applied):
                    raise ValueError('Unexpected external forces')
                samples.append(np.r_[data.time, data.qpos, data.qvel, load, lateral_load])
            name = variant+'_'+label
            np.savez_compressed(out/(name+'_trace.npz'), samples=np.asarray(samples))
            row = dict(variant=variant, case=label, offset_m=offset, yaw_degrees=yaw,
                duration_s=float(data.time), initial_qpos=initial.tolist(),
                maximum_normal_load_n=peak, maximum_lateral_normal_load_n=lateral,
                maximum_penetration_m=penetration, maximum_optical_face_load_n=optical,
                final_speed=float(np.linalg.norm(data.joint('pike_reference_free').qvel)),
                warnings=data.warning.number.tolist(), worst_contact=worst,
                trace_sha256=sha(out/(name+'_trace.npz')),
                model_sha256=sha(out/(variant+'.mjb')), qualified_support=False)
            results.append(row)
            (out/(name+'.json')).write_text(json.dumps(row, indent=2)+'\n')
            print(json.dumps({k: row[k] for k in ['variant', 'case', 'maximum_normal_load_n',
                'maximum_lateral_normal_load_n', 'maximum_optical_face_load_n']}), flush=True)
    report = dict(scope=__doc__, mujoco_version=mujoco.__version__,
        sources=['https://github.com/google-deepmind/mujoco/issues/3691',
                 'https://github.com/google-deepmind/mujoco/issues/3701'],
        source_world_sha256=contract['world_sha256'],
        source_contract_sha256=sha(source/'contract.json'), script_sha256=sha(__file__),
        results=results, qualified_support=False, qualified_robot_handling=False)
    (out/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
