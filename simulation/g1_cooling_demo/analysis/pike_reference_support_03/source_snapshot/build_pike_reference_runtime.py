"""Build passive PIKE reference/cap bodies and test their physical support.

The selected commercial-device reconstruction has inferred fit and inertial
parameters. These are component diagnostics, not robot placement, calibrated
device dynamics, optical acquisition, or a completed paper branch.
"""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, HalfspaceIntersection
import trimesh

from build_bare_optical_coupon import source_part
from build_tool_station import absolve_assets, numbers, sha

ROOT = Path(__file__).resolve().parents[2]


def clipped_hull(planes):
    planes = np.asarray(planes)
    fit = linprog([0., 0., 0., -1.],
                  A_ub=np.c_[planes[:, :3], np.linalg.norm(planes[:, :3], axis=1)],
                  b_ub=-planes[:, 3], bounds=[(None, None)]*3+[(0., None)], method='highs')
    if not fit.success or fit.x[-1] < 1e-7:
        raise ValueError('Source partition has no robust interior')
    return trimesh.convex.convex_hull(HalfspaceIntersection(planes, fit.x[:3]).intersections)


def recessed_cells(outer_mesh, polygon, floor_z, partition_offset=(0., 0.)):
    """Partition a convex shell with a polygonal blind recess, without overlap."""
    outer = ConvexHull(outer_mesh.vertices)
    polygon = np.asarray(polygon)
    polygon = polygon[ConvexHull(polygon).vertices]
    center = polygon.mean(axis=0)+np.asarray(partition_offset)
    bore = ConvexHull(polygon)
    if np.max(bore.equations[:, :2]@center+bore.equations[:, 2]) >= -1e-5:
        raise ValueError('Partition center must be strictly inside the source recess')
    cells = [clipped_hull(np.vstack([outer.equations, [0., 0., 1., -floor_z]]))]
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        ra, rb, edge = a-center, b-center, b-a
        planes = [np.array([0., 0., -1., floor_z])]
        for normal, point in [(np.r_[ra[1], -ra[0], 0.], center),
                              (np.r_[-rb[1], rb[0], 0.], center),
                              (np.r_[-edge[1], edge[0], 0.], a)]:
            normal /= np.linalg.norm(normal)
            planes.append(np.r_[normal, -normal[:2]@point])
        cells.append(clipped_hull(np.vstack([outer.equations, planes])))
    expected = outer.volume-ConvexHull(polygon).volume*(outer_mesh.bounds[1, 2]-floor_z)
    if abs(sum(c.volume for c in cells)-expected) > max(1e-14, expected*1e-6):
        raise ValueError('Blind recess partition does not preserve expected volume')
    return cells


def aggregate_inertia(meshes, densities):
    rows = [(m.volume*rho, m.center_mass, m.moment_inertia*rho)
            for m, rho in zip(meshes, densities)]
    mass = sum(row[0] for row in rows)
    center = sum(m*c for m, c, _ in rows)/mass
    moment = sum(I+m*(np.dot(c-center, c-center)*np.eye(3)-np.outer(c-center, c-center))
                 for m, c, I in rows)
    return mass, center, moment


def set_inertia(body, meshes, densities):
    mass, center, I = aggregate_inertia(meshes, densities)
    ET.SubElement(body, 'inertial', mass=str(mass), pos=numbers(center),
                  fullinertia=numbers([I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]))
    return float(mass)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('panel_component', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--release-gap', type=float, default=.002,
                   help='Declared seating diagnostic input; passing it does not qualify larger release gaps')
    p.add_argument('--cap-release-gap', type=float, default=.002)
    p.add_argument('--shoulder-partition-offset', type=float, nargs=2, default=[0., 0.],
                   help='Offset the internal partition rays inside the bore; preserve the external solid')
    a = p.parse_args()
    if not 0 <= a.release_gap <= .002:
        p.error('Release gap must be between zero and the retained 2 mm drop diagnostic')
    if not 0 <= a.cap_release_gap <= .002:
        p.error('Cap release gap must be between zero and 2 mm')
    component, out = a.panel_component.resolve(), a.output.resolve()
    panel_review = json.loads((component/'review.json').read_text())
    assert panel_review['passed_component_support']
    assert sha(component/'world.xml') == panel_review['world_sha256']
    for path, digest in panel_review['source_hashes'].items():
        assert sha(ROOT/path) == digest
    original = ROOT/'assets/cooling_lab_v1/geometry/prepared_pike.glb'
    revision_path = ROOT/'assets/pike_integratir_dtgs_v1/revisions/cap_support/revision.json'
    revision = json.loads(revision_path.read_text())
    candidate = ROOT/revision['complete_asset_candidate']
    assert sha(original) == revision['source_geometry_sha256']
    assert sha(candidate) == revision['complete_asset_candidate_sha256']
    source = trimesh.load(candidate, force='scene', process=False)
    ref_names = ['gold_reference_holder', 'gold_reference_shoulder', 'diffuse_gold_reference_face']
    ref = {name: source_part(source, name) for name in ref_names}
    cap = source_part(source, 'reference_protective_cap')
    origin = np.r_[ref[ref_names[0]].bounds.mean(axis=0)[:2], ref[ref_names[0]].bounds[0, 2]]
    cap_origin = np.r_[cap.bounds.mean(axis=0)[:2], cap.bounds[0, 2]]
    for mesh in ref.values():
        mesh.apply_translation(-origin)
    cap.apply_translation(-cap_origin)
    # The earlier face datum correction buried the face in a solid shoulder.
    # Preserve that recorded 0.05 mm recess, but physically remove the shoulder
    # volume in front of the gold disk. No optical surface is made non-colliding.
    face = ref['diffuse_gold_reference_face']
    face.apply_translation([0., 0., -.00055])
    shoulder = ref['gold_reference_shoulder']
    polygon = np.unique(face.vertices[:, :2], axis=0)
    floor = float(face.bounds[0, 2])
    shoulder_cells = recessed_cells(shoulder, polygon, floor, a.shoulder_partition_offset)
    cutter = trimesh.convex.convex_hull(np.vstack([
        np.c_[polygon, np.full(len(polygon), floor)],
        np.c_[polygon, np.full(len(polygon), shoulder.bounds[1, 2]+.001)]]))
    revised_shoulder = trimesh.boolean.difference([shoulder, cutter], engine='manifold')
    if not revised_shoulder.is_volume:
        raise ValueError('Recessed shoulder visual is not a closed volume')
    if abs(revised_shoulder.volume-sum(c.volume for c in shoulder_cells)) > shoulder.volume*2e-6:
        raise ValueError('Recessed visual and physical shoulder differ in volume')
    cap_ring = cap.vertices[(abs(cap.vertices[:, 2]-cap.bounds[1, 2]) < 1e-7) &
                            (np.linalg.norm(cap.vertices[:, :2], axis=1) < .026)]
    cap_cells = recessed_cells(cap, cap_ring[:, :2], revision['inferred_cap']['floor_thickness_m'])
    if abs(sum(c.volume for c in cap_cells)-cap.volume) > cap.volume*2e-6:
        raise ValueError('Cap collision partition changes its source volume')
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out/'source_snapshot'
    snapshot.mkdir()
    for path in [Path(__file__), Path(__file__).with_name('build_bare_optical_coupon.py'),
                 Path(__file__).with_name('convex_cells.py'), Path(__file__).with_name('build_tool_station.py'),
                 revision_path]:
        shutil.copyfile(path, snapshot/path.name)
    xml = ET.parse(component/'world.xml').getroot()
    absolve_assets(xml, component/'world.xml')
    world, asset = xml.find('worldbody'), xml.find('asset')
    world.remove(world.find("body[@name='optical_witness_white']"))
    ET.SubElement(world, 'geom', name='component_bench', type='plane', size='.5 .3 .02',
                  rgba='.15 .18 .19 1', friction='.3 .002 .0001', solref='.002 1', solimp='.99 .99 .0001')
    bodies = {}
    for name in ['pike_reference', 'pike_reference_cap']:
        bodies[name] = ET.SubElement(world, 'body', name=name)
        ET.SubElement(bodies[name], 'freejoint', name=name+'_free')

    def add_mesh(body, name, mesh, *, visual=False, rgba='.06 .065 .07 1'):
        path = out/(name+'.obj')
        path.write_text(trimesh.exchange.obj.export_obj(mesh, digits=17).rstrip()+'\n')
        ET.SubElement(asset, 'mesh', name=name, file=str(path))
        g = ET.SubElement(body, 'geom', name=name, type='mesh', mesh=name, rgba=rgba,
                          friction='.3 .002 .0001', solref='.002 1', solimp='.99 .99 .0001')
        if visual:
            g.attrib.update(contype='0', conaffinity='0', group='2')
        return g

    rb, cb = bodies['pike_reference'], bodies['pike_reference_cap']
    add_mesh(rb, 'pike_reference_holder', ref['gold_reference_holder'])
    add_mesh(rb, 'pike_reference_shoulder_visual', revised_shoulder, visual=True)
    add_mesh(rb, 'pike_reference_optical_face', face, rgba='.7 .48 .12 1')
    for i, cell in enumerate(shoulder_cells):
        add_mesh(rb, f'pike_reference_shoulder_cell_{i}', cell).set('group', '3')
    add_mesh(cb, 'pike_reference_cap_visual', cap, visual=True)
    for i, cell in enumerate(cap_cells):
        add_mesh(cb, f'pike_reference_cap_cell_{i}', cell).set('group', '3')
    # Effective densities are explicit development inputs, not manufacturer
    # claims about material composition or a measured gold coating thickness.
    ref_mass = set_inertia(rb, [ref['gold_reference_holder'], *shoulder_cells, face],
                          [1400.]*(1+len(shoulder_cells))+[2700.])
    cap_mass = set_inertia(cb, [cap], [1400.])
    ET.indent(xml)
    ET.ElementTree(xml).write(out/'world.xml', encoding='unicode')
    inputs = {n.get('file'): sha(n.get('file')) for n in asset if n.get('file')}
    (out/'model_inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    m = mujoco.MjModel.from_xml_path(str(out/'world.xml'))
    d = mujoco.MjData(m)
    # Optical accessibility is a geometry requirement independent of contact
    # stability: a center ray from in front must reach the gold face first.
    d.joint('pike_reference_free').qpos[:] = [0., 0., .2, 1., 0., 0., 0.]
    d.joint('pike_reference_cap_free').qpos[:] = [.15, -.01, .002, 1., 0., 0., 0.]
    mujoco.mj_forward(m, d)
    groups = m.geom_group.copy()
    m.geom_group[:] = 0
    m.geom_group[m.geom_bodyid == m.body('pike_reference').id] = 5
    # Ignore the visual copy of the shoulder so the ray tests physical solids.
    m.geom_group[m.geom('pike_reference_shoulder_visual').id] = 0
    hit = np.array([-1], dtype=np.int32)
    distance = mujoco.mj_ray(m, d, np.array([0., 0., .3]), np.array([0., 0., -1.]),
                            np.array([0, 0, 0, 0, 0, 1], dtype=np.uint8), 1, -1, hit)
    m.geom_group[:] = groups
    accessible = distance > 0 and m.geom(int(hit[0])).name == 'pike_reference_optical_face'
    if not accessible:
        raise ValueError('Optical face remains obstructed by its holder')
    contract = dict(scope=__doc__, source_manual=revision['source_manual'],
        source_manual_locator='PN 350-048400-01, printed pages 1 and 4-5: reference, protective cap and substitution sequence',
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in [original, candidate, revision_path]},
        source_panel_review_sha256=sha(component/'review.json'),
        source_reference_origin_normalized_m=origin.tolist(), source_cap_origin_normalized_m=cap_origin.tolist(),
        geometry_revision=dict(reason='Remove artificial shoulder occlusion introduced by the earlier optical-face datum correction',
            optical_face_translation_m=[0., 0., -.00055],
            optical_face_recess_m=float(shoulder.bounds[1, 2]-face.bounds[1, 2]),
            shoulder_removed_volume_m3=float(shoulder.volume-revised_shoulder.volume),
            reference_outer_envelope_unchanged=True, optical_face_geometry_unchanged=True,
            dimensions_are_inferred=True, manufacturer_CAD=False),
        optical_face_accessible=bool(accessible),
        masses_kg=dict(pike_reference=ref_mass, pike_reference_cap=cap_mass),
        effective_densities_kg_m3=dict(holder_and_shoulder=1400., gold_face_effective_substrate=2700., cap=1400.),
        dynamics_basis='Unmeasured development inputs; material composition, friction, compliance and inertial parameters require qualification',
        friction=[.3, .002, .0001], solref=[.002, 1.], solimp=[.99, .99, .0001],
        reference_port_support_height_m=float(shoulder.bounds[1, 2]),
        reference_cap_support_height_m=float(ref['gold_reference_holder'].bounds[1, 2]),
        cap_height_m=float(cap.bounds[1, 2]), cap_floor_thickness_m=.003,
        collision_cells=dict(shoulder=len(shoulder_cells), cap=len(cap_cells)),
        shoulder_partition_offset_m=a.shoulder_partition_offset,
        partition_basis='Nonoverlapping convex cells with the same outer hull, blind recess and total volume; only internal cell boundaries change',
        initial_reference_release_gap_m=a.release_gap,
        initial_cap_release_gap_m=a.cap_release_gap,
        support_scope='Only the declared seating gap and offsets; no larger drop, robot transfer or placement reliability qualification',
        world_sha256=sha(out/'world.xml'), model_inputs_sha256=sha(out/'model_inputs.json'),
        source_snapshot_sha256={p.name: sha(p) for p in snapshot.iterdir()},
        qualified_robot_handling=False, qualified_paper_branch=False)
    (out/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    trials, traces = [], {}
    cases = [('port_center', 'port', [0., 0.]), ('port_x', 'port', [.0005, 0.]),
             ('port_y', 'port', [0., -.0005]), ('cap_center', 'cap', [0., 0.]),
             ('cap_x', 'cap', [.0005, 0.]), ('cap_y', 'cap', [0., -.0005])]
    for label, support, offset in cases:
        d = mujoco.MjData(m)
        d.joint('pike_reference_cap_free').qpos[:] = [.15, -.01, a.cap_release_gap, 1., 0., 0., 0.]
        ref_xy = np.array([.04, -.01] if support == 'port' else [.15, -.01])+offset
        z = (panel_review['actual_support_plane_m']+contract['reference_port_support_height_m']+a.release_gap
             if support == 'port' else a.cap_release_gap+contract['cap_height_m']+contract['reference_cap_support_height_m']+a.release_gap)
        d.joint('pike_reference_free').qpos[:] = [*ref_xy, z, 0., 1., 0., 0.]
        mujoco.mj_forward(m, d)
        rid, cid = m.body('pike_reference').id, m.body('pike_reference_cap').id
        aid = int(m.joint('pike_reference_free').dofadr[0])
        max_pen = max_force = tail_speed = tail_omega = 0.
        optical_load = external = False
        native_force_error = 0.
        native_force_comparisons = 0
        supports, tail_support, samples = set(), [], []
        for i in range(30000):
            mujoco.mj_step(m, d)
            force_z = load = 0.
            # Elliptic, three-dimensional contacts store the native contact
            # wrench directly at efc_address. Vectorize the read, and compare
            # against mj_contactForce periodically; physics is unchanged.
            geoms = np.asarray(d.contact.geom)
            bs = m.geom_bodyid[geoms]
            relevant = np.flatnonzero(np.any(bs == rid, axis=1))
            if len(relevant):
                max_pen = max(max_pen, max(0., -float(np.min(d.contact.dist[relevant]))))
            active = relevant[np.asarray(d.contact.efc_address)[relevant] >= 0]
            if len(active):
                if int(m.opt.cone) != int(mujoco.mjtCone.mjCONE_ELLIPTIC) or np.any(d.contact.dim[active] != 3):
                    raise ValueError('Vector contact read requires elliptic 3D contacts')
                addresses = np.asarray(d.contact.efc_address)[active]
                forces = d.efc_force[addresses[:, None]+np.arange(3)]
                frames = np.asarray(d.contact.frame)[active].reshape(-1, 3, 3)
                signs = np.where(bs[active, 1] == rid, 1., -1.)
                force_z = float(np.sum(signs*np.einsum('nij,ni->nj', frames, forces)[:, 2]))
                load = float(np.sum(forces[:, 0]))
                loaded = active[forces[:, 0] > 1e-8]
                own = np.where(bs[loaded, 1] == rid, 1, 0)
                supports.update(m.geom(int(g)).name for g in np.unique(geoms[loaded, 1-own]))
                optical_load |= bool(np.any(geoms[loaded, own] == m.geom('pike_reference_optical_face').id))
                if i % 5000 == 0:
                    for j, ci in enumerate(active):
                        native = np.zeros(6)
                        mujoco.mj_contactForce(m, d, int(ci), native)
                        native_force_error = max(native_force_error, float(np.max(abs(native[:3]-forces[j]))))
                        native_force_comparisons += 1
            max_force = max(max_force, load)
            external |= bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
            if i >= 25000:
                tail_support.append(force_z)
                tail_speed = max(tail_speed, float(np.linalg.norm(d.qvel[aid:aid+3])))
                tail_omega = max(tail_omega, float(np.linalg.norm(d.qvel[aid+3:aid+6])))
            if i % 10 == 0:
                samples.append(np.r_[d.time, d.qpos, d.qvel])
            if i % 5000 == 0:
                print(label, 'seconds', round(float(d.time), 4), flush=True)
        mujoco.mj_kinematics(m, d)
        required_prefix = 'panel_cell_' if support == 'port' else 'pike_reference_cap_cell_'
        checks = dict(no_actuators=m.nu == 0, no_equalities=m.neq == 0, no_external_forces=not external,
            no_numerical_warnings=not np.any(d.warning.number), bounded_penetration=max_pen <= .00025,
            no_optical_surface_load=not optical_load,
            intended_support_only=bool(supports) and all(n.startswith(required_prefix) for n in supports),
            stable_last_half_second=tail_speed < .005 and tail_omega < .02,
            support_balances_weight=abs(float(np.mean(tail_support))-ref_mass*9.81) <= .05*ref_mass*9.81,
            bounded_contact_load=max_force <= 20.,
            vector_force_read_matches_native=native_force_comparisons > 0 and native_force_error < 1e-10,
            placement_retained=np.linalg.norm(d.body(rid).xpos[:2]-ref_xy) < .0001,
            cap_remains_on_bench=abs(float(d.body(cid).xpos[2])) < .00025)
        report = dict(case=label, support=support, offset_m=offset,
            initial_reference_release_gap_m=a.release_gap, passed=bool(all(checks.values())),
            initial_cap_release_gap_m=a.cap_release_gap,
            checks={k: bool(v) for k, v in checks.items()}, maximum_penetration_m=max_pen,
            maximum_normal_load_n=max_force, last_half_second_peak_speed_m_s=tail_speed,
            last_half_second_peak_angular_speed_rad_s=tail_omega,
            last_half_second_mean_support_n=float(np.mean(tail_support)),
            native_force_comparisons=native_force_comparisons,
            maximum_native_force_read_error_n=native_force_error,
            contacted_support_geoms=sorted(supports), final_qpos=d.qpos.tolist())
        trials.append(report)
        traces[label] = np.asarray(samples)
        (out/(label+'.json')).write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(dict(case=label, passed=report['passed'], failed_checks=[k for k, v in checks.items() if not v])), flush=True)
    np.savez_compressed(out/'support_traces.npz', **traces)
    review = dict(scope=__doc__, contract_sha256=sha(out/'contract.json'),
                  world_sha256=contract['world_sha256'], trace_sha256=sha(out/'support_traces.npz'),
                  optical_face_accessible=bool(accessible), trials=trials,
                  passed_component_support=all(t['passed'] for t in trials),
                  qualified_robot_handling=False, qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(review, indent=2)+'\n')
    if not review['passed_component_support']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
