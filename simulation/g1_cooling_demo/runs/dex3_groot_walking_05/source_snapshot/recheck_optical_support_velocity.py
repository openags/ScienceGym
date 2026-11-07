"""Replay a full-room support test to correct its specimen velocity indexing.

The original support script reused `address` in its reference/cap loop, so its
specimen speed test read the cap velocity. Retain the original report and use
this independently replayed addendum for the affected stability check. Nothing
here grants robot placement, handling or complete paper qualification.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha
from runtime_collision_plugins import load_collision_plugins


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('baseline',type=Path)
    p.add_argument('original_review',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    binding=json.loads((a.scene/'binding.json').read_text())
    original=json.loads(a.original_review.read_text())
    base=json.loads((a.baseline/'result.json').read_text())
    assert sha(a.scene/'binding.json')==original['binding_sha256']
    assert sha(a.scene/'world.xml')==original['world_sha256']==binding['world_sha256']
    assert sha(a.scene/'initial_state.json')==binding['initial_state_sha256']
    assert sha(a.baseline/'trace.npz')==base['trace_sha256']==original['baseline_trace_sha256']
    assert sha(a.original_review.parent/'trace.npz')==original['trace_sha256']
    for name,digest in json.loads((a.scene/'model_inputs.json').read_text()).items():assert sha(name)==digest
    a.output.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'runtime_collision_plugins.py','build_tool_station.py']:
        shutil.copyfile(Path(__file__).with_name(name),a.output/name)
    load_collision_plugins(binding.get('collision_plugins',[]))
    m=mujoco.MjModel.from_xml_path(str((a.scene/'world.xml').resolve()));d=mujoco.MjData(m)
    initial=json.loads((a.scene/'initial_state.json').read_text())
    d.qpos[:]=initial['qpos'];d.qvel[:]=initial['qvel'];mujoco.mj_forward(m,d)
    with np.load(a.baseline/'trace.npz') as z:controls=z['ctrl'][:30000].copy()
    with np.load(a.original_review.parent/'trace.npz') as z:recorded={k:z[k].copy() for k in ['time','qpos','qvel']}
    assert controls.shape==(30000,m.nu) and abs(m.opt.timestep-.0001)<1e-12
    stats={name:dict(dof_address=int(m.joint(name+'_free').dofadr[0]),peak_speed_m_s=0.,peak_omega_rad_s=0.)
        for name in ['optical_witness_white','pike_reference','pike_reference_cap']}
    errors=dict(qpos=0.,qvel=0.,time=0.);samples=[];external=False
    for i,command in enumerate(controls):
        d.ctrl[:]=command;mujoco.mj_step(m,d)
        external=external or bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        if i>=25000:
            row=[float(d.time)]
            for values in stats.values():
                address=values['dof_address']
                speed=float(np.linalg.norm(d.qvel[address:address+3]))
                omega=float(np.linalg.norm(d.qvel[address+3:address+6]))
                values['peak_speed_m_s']=max(values['peak_speed_m_s'],speed)
                values['peak_omega_rad_s']=max(values['peak_omega_rad_s'],omega)
                row.extend([speed,omega])
            samples.append(row)
        if i%10==0:
            k=i//10
            errors['qpos']=max(errors['qpos'],float(np.max(abs(d.qpos-recorded['qpos'][k]))))
            errors['qvel']=max(errors['qvel'],float(np.max(abs(d.qvel-recorded['qvel'][k]))))
            errors['time']=max(errors['time'],abs(float(d.time)-recorded['time'][k]))
        if i%5000==0:print('velocity_replay_seconds',round(d.time,4),flush=True)
    for values in stats.values():values['stable']=values['peak_speed_m_s']<.005 and values['peak_omega_rad_s']<.02
    checks=dict(original_unaffected_checks=all(v for k,v in original['checks'].items() if k!='stable_last_half_second'),
        exact_retained_state_replay=max(errors.values())<=1e-10,
        correct_specimen_velocity=stats['optical_witness_white']['stable'],
        reference_and_cap_velocity=all(v['stable'] for v in stats.values()),
        no_external_forces=not external,no_numerical_warnings=not np.any(d.warning.number))
    np.savez_compressed(a.output/'tail_velocities.npz',samples=np.asarray(samples),body_order=np.array(list(stats)))
    report=dict(scope=__doc__,original_review_sha256=sha(a.original_review),
        original_review=str(a.original_review.resolve()),world_sha256=original['world_sha256'],
        baseline_trace_sha256=base['trace_sha256'],retained_trace_sha256=original['trace_sha256'],
        maximum_replay_errors=errors,bodies=stats,checks={k:bool(v) for k,v in checks.items()},
        corrected_asset_support_passed=bool(all(checks.values())),
        source_sha256={p.name:sha(p) for p in a.output.glob('*.py')},
        tail_velocities_sha256=sha(a.output/'tail_velocities.npz'),
        qualified_robot_handling=False,qualified_paper_branch=False)
    (a.output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    if not report['corrected_asset_support_passed']:raise SystemExit(1)


if __name__=='__main__':main()
