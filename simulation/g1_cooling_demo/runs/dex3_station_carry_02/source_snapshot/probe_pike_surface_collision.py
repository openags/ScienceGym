"""Test the actual nonconvex panel surface with MuJoCo's native mesh SDF.

Replace only the panel's convex partition with its original closed source
surface. Keep all vertices, apertures, reference/cap geometry, mass, friction,
compliance and initial states. This comparison does not qualify an asset or
robot operation; SDF surface accuracy needs its own geometric review.
"""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from build_tool_station import absolve_assets, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--duration', type=float, default=.1)
    a = p.parse_args()
    if not .05 <= a.duration <= 3.:
        p.error('Duration must be between 0.05 and 3 seconds')
    source, out = a.source.resolve(), a.output.resolve()
    contract = json.loads((source/'contract.json').read_text())
    assert sha(source/'world.xml') == contract['world_sha256']
    for name, digest in json.loads((source/'model_inputs.json').read_text()).items():
        assert sha(name) == digest
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    xml = ET.parse(source/'world.xml').getroot()
    absolve_assets(xml, source/'world.xml')
    world = xml.find('worldbody')
    cells = [g for g in world.findall('geom') if g.get('name', '').startswith('panel_cell_')]
    if len(cells) != 96:
        raise ValueError('Unexpected source panel partition')
    surface = world.find("geom[@name='source_panel_visual']")
    if surface is None:
        raise ValueError('Original closed source surface is missing')
    for key in ['friction', 'solref', 'solimp']:
        assert len({g.get(key) for g in cells}) == 1
        surface.set(key, cells[0].get(key))
    surface.attrib.update(type='sdf', contype='1', conaffinity='1')
    for geom in cells:
        world.remove(geom)
    ET.indent(xml)
    ET.ElementTree(xml).write(out/'world.xml', encoding='unicode')
    model = mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    baseline = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    for field in ['body_mass', 'body_inertia', 'body_ipos', 'body_iquat', 'qpos0']:
        if not np.array_equal(getattr(model, field), getattr(baseline, field)):
            raise ValueError('Surface collision change altered '+field)
    if model.nu or model.neq:
        raise ValueError('Component must remain passive')
    rows = []
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
        tail_force = []
        worst = None
        samples = []
        for step in range(round(a.duration/model.opt.timestep)):
            mujoco.mj_step(model, data)
            geoms = np.asarray(data.contact.geom)
            bodies = model.geom_bodyid[geoms]
            relevant = np.flatnonzero(np.any(bodies == rid, axis=1) &
                (data.contact.efc_address >= 0))
            load = lateral_load = vertical = 0.
            if len(relevant):
                assert int(model.opt.cone) == int(mujoco.mjtCone.mjCONE_ELLIPTIC)
                assert np.all(data.contact.dim[relevant] == 3)
                addresses = data.contact.efc_address[relevant]
                forces = data.efc_force[addresses[:, None]+np.arange(3)]
                frames = np.asarray(data.contact.frame)[relevant].reshape(-1, 3, 3)
                signs = np.where(bodies[relevant, 1] == rid, 1., -1.)
                vertical = float(np.sum(signs*np.einsum('nij,ni->nj', frames, forces)[:, 2]))
                load = float(np.sum(forces[:, 0]))
                lateral_load = float(np.sum(forces[np.abs(frames[:, 0, 2]) < .2, 0]))
                penetration = max(penetration, -float(np.min(data.contact.dist[relevant])))
                own = np.where(bodies[relevant, 1] == rid, 1, 0)
                optical = max(optical, float(np.sum(forces[geoms[relevant, own] == optical_id, 0])))
                j = int(np.argmax(forces[:, 0]))
                if worst is None or forces[j, 0] > worst['normal_load_n']:
                    ci = int(relevant[j])
                    worst = dict(time_s=float(data.time), normal_load_n=float(forces[j, 0]),
                        geom_names=[model.geom(int(g)).name for g in geoms[ci]],
                        normal=data.contact.frame[ci, :3].tolist(),
                        distance_m=float(data.contact.dist[ci]))
            peak = max(peak, load)
            lateral = max(lateral, lateral_load)
            if np.any(data.xfrc_applied) or np.any(data.qfrc_applied):
                raise ValueError('Unexpected external forces')
            if step >= round(.8*a.duration/model.opt.timestep):
                tail_force.append(vertical)
            samples.append(np.r_[data.time, data.qpos, data.qvel, load, lateral_load, vertical])
        np.savez_compressed(out/(label+'_trace.npz'), samples=np.asarray(samples))
        row = dict(case=label, offset_m=offset, yaw_degrees=yaw, duration_s=float(data.time),
            initial_qpos=initial.tolist(), maximum_normal_load_n=peak,
            maximum_lateral_normal_load_n=lateral, maximum_penetration_m=penetration,
            maximum_optical_face_load_n=optical, mean_final_vertical_support_n=float(np.mean(tail_force)),
            expected_weight_n=float(model.body_mass[rid]*9.81),
            final_speed=float(np.linalg.norm(data.joint('pike_reference_free').qvel)),
            warnings=data.warning.number.tolist(), worst_contact=worst,
            trace_sha256=sha(out/(label+'_trace.npz')), qualified_support=False)
        rows.append(row)
        (out/(label+'.json')).write_text(json.dumps(row, indent=2)+'\n')
        print(json.dumps({k: row[k] for k in ['case', 'maximum_normal_load_n',
            'maximum_lateral_normal_load_n', 'maximum_optical_face_load_n',
            'mean_final_vertical_support_n']}), flush=True)
    result = dict(scope=__doc__, mujoco_version=mujoco.__version__,
        source_world_sha256=contract['world_sha256'], world_sha256=sha(out/'world.xml'),
        source_contract_sha256=sha(source/'contract.json'), script_sha256=sha(__file__),
        model_inputs={n.get('file'): sha(n.get('file')) for n in xml.find('asset') if n.get('file')},
        source_surface_vertices_unchanged=True, explicit_inertia_unchanged=True,
        reference_and_cap_collision_unchanged=True, results=rows,
        qualified_surface_accuracy=False, qualified_support=False, qualified_robot_handling=False)
    (out/'comparison.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
