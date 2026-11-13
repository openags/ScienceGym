"""Check a passive specimen settling in the complete G1 laboratory.

The standing robot receives a recorded motor-command prefix from the pinned
baseline. This is an open-loop asset diagnostic, not a sensor-driven robot
episode, installation, grasp or paper-branch qualification.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from diagnose_carry_state import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();scene,baseline,out=[v.resolve() for v in [a.scene,a.baseline,a.output]]
    binding=json.loads((scene/'binding.json').read_text());result=json.loads((baseline/'result.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    assert sha(scene/'initial_state.json')==binding['initial_state_sha256']
    assert sha(baseline/'trace.npz')==result['trace_sha256']
    assert sha(baseline/'contract.json')==binding['base_contract_sha256']
    for file,digest in json.loads((scene/'model_inputs.json').read_text()).items():assert sha(file)==digest
    out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,out/Path(__file__).name)
    m=mujoco.MjModel.from_xml_path(str(scene/'world.xml'));d=mujoco.MjData(m)
    initial=json.loads((scene/'initial_state.json').read_text());d.qpos[:]=initial['qpos'];d.qvel[:]=initial['qvel']
    mujoco.mj_forward(m,d)
    with np.load(baseline/'trace.npz') as z:controls=z['ctrl'][:30000].copy();times=z['time'][:30000].copy()
    assert abs(m.opt.timestep-.0001)<1e-12 and controls.shape==(30000,m.nu)
    assert np.max(abs(times-np.arange(30000)*m.opt.timestep))<1e-8
    cid=m.body('optical_witness_white').id;address=m.joint('optical_witness_white_free').dofadr[0]
    mass=float(m.body_mass[cid]);initial_xy=d.body(cid).xpos[:2].copy()
    peak_pen=0.;peak_force=0.;tail_speed=0.;tail_omega=0.;tail_support=[];contacts=set();samples=[]
    specimen_contact_geoms=set()
    external=False
    for i,control in enumerate(controls):
        d.ctrl[:]=control;mujoco.mj_step(m,d);force_z=0.;normal_load=0.
        for ci,c in enumerate(d.contact):
            bodies=m.geom_bodyid[c.geom]
            if sum(b==cid for b in bodies)!=1:continue
            f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f)
            sign=1. if bodies[1]==cid else -1.
            force_z+=float(sign*(c.frame.reshape(3,3).T@f[:3])[2]);normal_load+=float(f[0])
            peak_pen=max(peak_pen,max(0.,-float(c.dist)))
            if f[0]>1e-8:
                contacts.add(m.body(next(b for b in bodies if b!=cid)).name)
                specimen_contact_geoms.add(m.geom(int(c.geom[1 if bodies[1]==cid else 0])).name)
        peak_force=max(peak_force,normal_load)
        external=external or bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        if i>=25000:
            tail_support.append(force_z)
            tail_speed=max(tail_speed,float(np.linalg.norm(d.qvel[address:address+3])))
            tail_omega=max(tail_omega,float(np.linalg.norm(d.qvel[address+3:address+6])))
        if i%10==0:samples.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
        if i%5000==0:print('full_room_support_seconds',round(d.time,4),flush=True)
    mujoco.mj_kinematics(m,d)
    checks=dict(no_external_forces=not external,no_numerical_warnings=not np.any(d.warning.number),
        original_robot_actuators_only=m.nu==43,no_object_equalities=m.neq==0,
        support_is_original_tray=contacts=={'carrier_tray'},bounded_penetration=peak_pen<=.00025,
        only_nonoptical_back_contacts_tray=specimen_contact_geoms=={'optical_copper_witness'},
        optical_face_stays_up=float((d.body(cid).xmat.reshape(3,3)@np.array([0.,0.,-1.]))[2])>.999,
        bounded_contact_load=peak_force<=1.,stable_last_half_second=tail_speed<.005 and tail_omega<.02,
        support_balances_weight=abs(float(np.mean(tail_support))-mass*9.81)<=.05*mass*9.81,
        placement_retained=np.linalg.norm(d.body(cid).xpos[:2]-initial_xy)<.0001)
    np.savez_compressed(out/'trace.npz',time=np.array([s[0] for s in samples]),
        qpos=np.array([s[1] for s in samples]),qvel=np.array([s[2] for s in samples]),ctrl=np.array([s[3] for s in samples]))
    report=dict(scope=__doc__,binding_sha256=sha(scene/'binding.json'),world_sha256=sha(scene/'world.xml'),
        baseline_trace_sha256=result['trace_sha256'],baseline_contract_sha256=binding['base_contract_sha256'],
        source_sha256=sha(__file__),trace_sha256=sha(out/'trace.npz'),simulated_seconds=float(d.time),
        checks={k:bool(v) for k,v in checks.items()},passed_asset_support=bool(all(checks.values())),
        maximum_penetration_m=peak_pen,maximum_normal_load_n=peak_force,
        last_half_second_peak_speed_m_s=tail_speed,last_half_second_peak_angular_speed_rad_s=tail_omega,
        last_half_second_mean_support_n=float(np.mean(tail_support)),mass_kg=mass,
        contact_bodies=sorted(contacts),specimen_contact_geoms=sorted(specimen_contact_geoms),
        qualified_robot_handling=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed_asset_support']:raise SystemExit(1)


if __name__=='__main__':main()
