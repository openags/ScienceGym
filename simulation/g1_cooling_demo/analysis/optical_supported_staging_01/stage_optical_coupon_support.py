"""Author a supported coupon start without the earlier two-millimetre drop.

Only the initial free-coupon translation changes. Geometry, contact parameters,
robot state, tool/tray and other free objects remain exact. This does not credit
robot placement, fabrication or manipulation and is not a runtime state reset.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from frozen_collision_plugins import load, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--gap',type=float,default=.00002)
    a=p.parse_args()
    if not 0<=a.gap<=.00002:p.error('Supported initial clearance must be 0 to 20 micrometres')
    scene,out=a.scene.resolve(),a.output.resolve()
    binding=json.loads((scene/'binding.json').read_text())
    state=json.loads((scene/'initial_state.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    assert sha(scene/'initial_state.json')==binding['initial_state_sha256']
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load(binding['collision_plugins'],sha(loader))
    m=mujoco.MjModel.from_xml_path(str(scene/'world.xml'));d=mujoco.MjData(m)
    d.qpos[:],d.qvel[:]=state['qpos'],state['qvel'];mujoco.mj_forward(m,d)
    old=d.qpos.copy();normal=d.body('carrier_tray').xmat.reshape(3,3)[:,2].copy()
    gap=float(binding['specimen_initial_support']['initial_release_gap_m'])
    joint=d.joint('optical_witness_white_free')
    joint.qpos[:3]-=(gap-a.gap)*normal
    mujoco.mj_forward(m,d)
    body=m.body('optical_witness_white').id
    bad=[dict(parts=[m.geom(int(g)).name for g in c.geom],distance_m=float(c.dist))
         for c in d.contact if body in m.geom_bodyid[c.geom] and c.dist<0]
    if bad:raise ValueError('Authored coupon initially intersects geometry: '+str(bad))
    qa=int(m.joint('optical_witness_white_free').qposadr[0])
    keep=np.ones(m.nq,dtype=bool);keep[qa:qa+3]=False
    assert np.array_equal(old[keep],d.qpos[keep])
    out.mkdir(parents=True,exist_ok=False)
    for name in ['world.xml','model_inputs.json']:shutil.copyfile(scene/name,out/name)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for path in [Path(__file__),loader]:shutil.copyfile(path,snapshot/path.name)
    state.update(qpos=d.qpos.tolist(),scope=__doc__)
    (out/'initial_state.json').write_text(json.dumps(state,indent=2)+'\n')
    binding.update(upstream_scene=str(scene),upstream_binding_sha256=sha(scene/'binding.json'),
        initial_state_sha256=sha(out/'initial_state.json'),
        source_snapshot_sha256={p.name:sha(p) for p in snapshot.iterdir()},
        coupon_initial_support_revision=dict(scope=__doc__,previous_gap_m=gap,selected_gap_m=a.gap,
            displacement_work_m=(d.qpos[qa:qa+3]-old[qa:qa+3]).tolist(),
            cause='Earlier authored 2 mm drop exceeded the unchanged 20 micrometre other-contact bound during pickup execution',
            source_reported_placement=False,physical_acceptance_unchanged=True,
            robot_tool_tray_and_other_object_states_exact=True),qualified_robot_handling=False)
    binding['specimen_initial_support']['initial_release_gap_m']=a.gap
    (out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    print(json.dumps(binding['coupon_initial_support_revision']),flush=True)


if __name__=='__main__':main()
