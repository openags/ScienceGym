"""Compare native collision pipelines on a preserved failed reference placement.

Short component diagnostics only. Keep geometry, friction, compliance, mass and
initial states fixed; report spurious lateral loads at coplanar cell boundaries.
This does not qualify support, manipulation or the full laboratory.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--margin-sweep', action='store_true',
                   help='Compare explicit numerical reference contact margins instead of collision algorithms')
    p.add_argument('--yaw-sweep', action='store_true',
                   help='Inspect sensitivity to the unprescribed reference rotation around its optical axis')
    a = p.parse_args()
    source, out = a.source.resolve(), a.output.resolve()
    c = json.loads((source/'contract.json').read_text())
    assert sha(source/'world.xml') == c['world_sha256']
    for path, digest in json.loads((source/'model_inputs.json').read_text()).items():
        assert sha(path) == digest
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out/Path(__file__).name)
    rows = []
    variants = [('native_multi', 0, 0.), ('native_single', int(mujoco.mjtDisableBit.mjDSBL_MULTICCD), 0.),
                ('libccd_single', int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD | mujoco.mjtDisableBit.mjDSBL_MULTICCD), 0.),
                ('libccd_multi', int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD), 0.)]
    if a.margin_sweep:
        variants = [('margin_zero', 0, 0.), ('margin_20um', 0, .00002), ('margin_40um', 0, .00004)]
    if a.yaw_sweep:
        variants = [('yaw_'+str(angle), 0, 0.) for angle in [0., .75, 1.875, 5., 11.]]
    for name, disabled, margin in variants:
        m = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
        m.opt.disableflags |= disabled
        if margin:
            m.geom_margin[m.geom_bodyid == m.body('pike_reference').id] = margin
        d = mujoco.MjData(m)
        d.joint('pike_reference_cap_free').qpos[:] = [.15, -.01, c['initial_cap_release_gap_m'], 1, 0, 0, 0]
        d.joint('pike_reference_free').qpos[:] = [.04, -.01,
            .10200000356417149+c['reference_port_support_height_m']+c['initial_reference_release_gap_m'], 0, 1, 0, 0]
        yaw = float(name[4:]) if a.yaw_sweep else 0.
        d.joint('pike_reference_free').qpos[3:] = [0., np.cos(np.deg2rad(yaw)/2), np.sin(np.deg2rad(yaw)/2), 0.]
        mujoco.mj_forward(m, d)
        rid = m.body('pike_reference').id
        peak = lateral = optical = penetration = 0.
        worst = None
        for i in range(1000):
            mujoco.mj_step(m, d)
            geoms = np.asarray(d.contact.geom)
            bodies = m.geom_bodyid[geoms]
            relevant = np.flatnonzero(np.any(bodies == rid, axis=1) & (d.contact.efc_address >= 0))
            if not len(relevant):
                continue
            assert np.all(d.contact.dim[relevant] == 3)
            f = d.efc_force[d.contact.efc_address[relevant]]
            normals = np.asarray(d.contact.frame)[relevant, :3]
            peak = max(peak, float(np.sum(f)))
            lateral = max(lateral, float(np.sum(f[np.abs(normals[:, 2]) < .2])))
            penetration = max(penetration, max(0., -float(np.min(d.contact.dist[relevant]))))
            own = np.where(bodies[relevant, 1] == rid, 1, 0)
            optical = max(optical, float(np.sum(f[geoms[relevant, own] == m.geom('pike_reference_optical_face').id])))
            j = int(np.argmax(f))
            if worst is None or f[j] > worst['normal_force_n']:
                ci = int(relevant[j])
                worst = dict(time_s=float(d.time), normal_force_n=float(f[j]),
                    geoms=[m.geom(int(g)).name for g in geoms[ci]],
                    normal=d.contact.frame[ci, :3].tolist(), position_m=d.contact.pos[ci].tolist())
        row = dict(name=name, disableflags=int(m.opt.disableflags), reference_contact_margin_m=margin,
            reference_yaw_degrees=yaw,
            margin_is_numerical_not_measured_material=True, duration_s=float(d.time),
            maximum_normal_load_n=peak, maximum_lateral_normal_load_n=lateral,
            maximum_optical_face_load_n=optical, maximum_penetration_m=penetration,
            final_speed=float(np.linalg.norm(d.joint('pike_reference_free').qvel)),
            warnings=d.warning.number.tolist(), worst_contact=worst)
        rows.append(row)
        (out/(name+'.json')).write_text(json.dumps(row, indent=2)+'\n')
        print(json.dumps(row), flush=True)
    report = dict(scope=__doc__, source_model_sha256=c['world_sha256'],
        source_contract_sha256=sha(source/'contract.json'), script_sha256=sha(__file__),
        documentation='https://mujoco.readthedocs.io/en/stable/computation.html#convex-collisions',
        variants=rows, qualified_support=False, qualified_paper_branch=False)
    (out/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
