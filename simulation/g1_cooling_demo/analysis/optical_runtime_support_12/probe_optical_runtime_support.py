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
from runtime_collision_plugins import load_collision_plugins


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('baseline',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--prepared-run',type=Path,
        help='Check a prepared runtime contact-model revision against its original operation bounds')
    a=p.parse_args();scene,baseline,out=[v.resolve() for v in [a.scene,a.baseline,a.output]]
    binding=json.loads((scene/'binding.json').read_text());result=json.loads((baseline/'result.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    assert sha(scene/'initial_state.json')==binding['initial_state_sha256']
    assert sha(baseline/'trace.npz')==result['trace_sha256']
    assert sha(baseline/'contract.json')==binding['base_contract_sha256']
    for file,digest in json.loads((scene/'model_inputs.json').read_text()).items():assert sha(file)==digest
    world=scene/'world.xml'
    initial=json.loads((scene/'initial_state.json').read_text())
    penetration_bound=.00025
    prepared=None
    if a.prepared_run is not None:
        candidate=a.prepared_run.resolve()
        run_contract=json.loads((candidate/'contract.json').read_text())
        assert run_contract['optical_scene_binding']['binding_sha256']==sha(scene/'binding.json')
        assert sha(candidate/'world.xml')==run_contract['model_sha256']
        for file,digest in json.loads((candidate/'model_inputs.json').read_text()).items():assert sha(file)==digest
        world=candidate/'world.xml'
        initial=dict(qpos=run_contract['initial_qpos'],qvel=run_contract['initial_qvel'])
        penetration_bound=float(run_contract['physical_acceptance']['maximum_other_penetration_m'])
        prepared=dict(path=str(candidate),contract_sha256=sha(candidate/'contract.json'),
            source_optical_world_sha256=binding['world_sha256'],
            contact_solver_revision=run_contract.get('contact_solver_revision'),
            physical_acceptance_changed=False)
    out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,out/Path(__file__).name)
    load_collision_plugins(binding.get('collision_plugins', []))
    shutil.copyfile(Path(__file__).with_name('runtime_collision_plugins.py'), out/'runtime_collision_plugins.py')
    m=mujoco.MjModel.from_xml_path(str(world));d=mujoco.MjData(m)
    d.qpos[:]=initial['qpos'];d.qvel[:]=initial['qvel']
    mujoco.mj_forward(m,d)
    with np.load(baseline/'trace.npz') as z:controls=z['ctrl'][:30000].copy();times=z['time'][:30000].copy()
    assert abs(m.opt.timestep-.0001)<1e-12 and controls.shape==(30000,m.nu)
    assert np.max(abs(times-np.arange(30000)*m.opt.timestep))<1e-8
    cid=m.body('optical_witness_white').id;specimen_address=int(m.joint('optical_witness_white_free').dofadr[0])
    mass=float(m.body_mass[cid]);initial_xy=d.body(cid).xpos[:2].copy()
    peak_pen=0.;peak_force=0.;tail_speed=0.;tail_omega=0.;tail_support=[];contacts=set();samples=[]
    specimen_contact_geoms=set()
    reference_checks={}
    if binding.get('passive_reference_binding'):
        for name in ['pike_reference','pike_reference_cap']:
            body=m.body(name);joint=m.joint(name+'_free')
            reference_checks[name]=dict(body=int(body.id),address=int(joint.dofadr[0]),
                mass_kg=float(m.body_mass[body.id]),initial_xy=d.body(name).xpos[:2].copy(),
                peak_pen=0.,peak_force=0.,tail_speed=0.,tail_omega=0.,tail_support=[],
                contacts=set(),own_geoms=set())
    external=False
    for i,control in enumerate(controls):
        d.ctrl[:]=control;mujoco.mj_step(m,d);force_z=0.;normal_load=0.
        reference_loads={name:[0.,0.] for name in reference_checks}
        for ci,c in enumerate(d.contact):
            bodies=m.geom_bodyid[c.geom]
            for name,stats in reference_checks.items():
                if sum(b==stats['body'] for b in bodies)!=1:continue
                f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f)
                own=1 if bodies[1]==stats['body'] else 0
                reference_loads[name][0]+=float((1. if own==1 else -1.)*(c.frame.reshape(3,3).T@f[:3])[2])
                reference_loads[name][1]+=float(f[0])
                stats['peak_pen']=max(stats['peak_pen'],max(0.,-float(c.dist)))
                if f[0]>1e-8:
                    stats['contacts'].add(m.geom(int(c.geom[1-own])).name)
                    stats['own_geoms'].add(m.geom(int(c.geom[own])).name)
            if sum(b==cid for b in bodies)!=1:continue
            f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f)
            sign=1. if bodies[1]==cid else -1.
            force_z+=float(sign*(c.frame.reshape(3,3).T@f[:3])[2]);normal_load+=float(f[0])
            peak_pen=max(peak_pen,max(0.,-float(c.dist)))
            if f[0]>1e-8:
                contacts.add(m.body(next(b for b in bodies if b!=cid)).name)
                specimen_contact_geoms.add(m.geom(int(c.geom[1 if bodies[1]==cid else 0])).name)
        peak_force=max(peak_force,normal_load)
        for name,stats in reference_checks.items():
            stats['peak_force']=max(stats['peak_force'],reference_loads[name][1])
            if i>=25000:
                stats['tail_support'].append(reference_loads[name][0]);reference_address=stats['address']
                stats['tail_speed']=max(stats['tail_speed'],float(np.linalg.norm(d.qvel[reference_address:reference_address+3])))
                stats['tail_omega']=max(stats['tail_omega'],float(np.linalg.norm(d.qvel[reference_address+3:reference_address+6])))
        external=external or bool(np.any(d.xfrc_applied) or np.any(d.qfrc_applied))
        if i>=25000:
            tail_support.append(force_z)
            tail_speed=max(tail_speed,float(np.linalg.norm(d.qvel[specimen_address:specimen_address+3])))
            tail_omega=max(tail_omega,float(np.linalg.norm(d.qvel[specimen_address+3:specimen_address+6])))
        if i%10==0:samples.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
        if i%5000==0:print('full_room_support_seconds',round(d.time,4),flush=True)
    mujoco.mj_kinematics(m,d)
    checks=dict(no_external_forces=not external,no_numerical_warnings=not np.any(d.warning.number),
        original_robot_actuators_only=m.nu==43,no_object_equalities=m.neq==0,
        support_is_original_tray=contacts=={'carrier_tray'},bounded_penetration=peak_pen<=penetration_bound,
        only_nonoptical_back_contacts_tray=specimen_contact_geoms=={'optical_copper_witness'},
        optical_face_stays_up=float((d.body(cid).xmat.reshape(3,3)@np.array([0.,0.,-1.]))[2])>.999,
        bounded_contact_load=peak_force<=1.,stable_last_half_second=tail_speed<.005 and tail_omega<.02,
        support_balances_weight=abs(float(np.mean(tail_support))-mass*9.81)<=.05*mass*9.81,
        placement_retained=np.linalg.norm(d.body(cid).xpos[:2]-initial_xy)<.0001)
    reference_reports={}
    for name,stats in reference_checks.items():
        reference_contacts=stats['contacts']
        expected_panel = (binding.get('panel_surface_binding') or {}).get('geom')
        intended=(bool(reference_contacts) and (reference_contacts == {expected_panel} if expected_panel else all(n.startswith('optical_panel_cell_') for n in reference_contacts))
                  if name=='pike_reference' else
                  reference_contacts=={binding['passive_reference_binding']['cap_initial_support']['geom']})
        own_checks=dict(intended_support_only=intended,
            no_optical_face_load='pike_reference_optical_face' not in stats['own_geoms'],
            bounded_penetration=stats['peak_pen']<=penetration_bound,bounded_contact_load=stats['peak_force']<=20.,
            stable_last_half_second=stats['tail_speed']<.005 and stats['tail_omega']<.02,
            support_balances_weight=abs(float(np.mean(stats['tail_support']))-stats['mass_kg']*9.81)<=.05*stats['mass_kg']*9.81,
            placement_retained=np.linalg.norm(d.body(name).xpos[:2]-stats['initial_xy'])<.0001)
        checks[name+'_support']=all(own_checks.values())
        reference_reports[name]=dict(checks={k:bool(v) for k,v in own_checks.items()},
            maximum_penetration_m=stats['peak_pen'],maximum_normal_load_n=stats['peak_force'],
            last_half_second_peak_speed_m_s=stats['tail_speed'],
            last_half_second_peak_angular_speed_rad_s=stats['tail_omega'],
            last_half_second_mean_support_n=float(np.mean(stats['tail_support'])),mass_kg=stats['mass_kg'],
            contact_geoms=sorted(reference_contacts),object_contact_geoms=sorted(stats['own_geoms']))
    np.savez_compressed(out/'trace.npz',time=np.array([s[0] for s in samples]),
        qpos=np.array([s[1] for s in samples]),qvel=np.array([s[2] for s in samples]),ctrl=np.array([s[3] for s in samples]))
    report=dict(scope=__doc__,binding_sha256=sha(scene/'binding.json'),world_sha256=sha(world),
        prepared_runtime=prepared,physical_penetration_bound_m=penetration_bound,
        specimen_velocity_dof_address=specimen_address,
        baseline_trace_sha256=result['trace_sha256'],baseline_contract_sha256=binding['base_contract_sha256'],
        source_sha256=sha(__file__),trace_sha256=sha(out/'trace.npz'),simulated_seconds=float(d.time),
        checks={k:bool(v) for k,v in checks.items()},passed_asset_support=bool(all(checks.values())),
        maximum_penetration_m=peak_pen,maximum_normal_load_n=peak_force,
        last_half_second_peak_speed_m_s=tail_speed,last_half_second_peak_angular_speed_rad_s=tail_omega,
        last_half_second_mean_support_n=float(np.mean(tail_support)),mass_kg=mass,
        contact_bodies=sorted(contacts),specimen_contact_geoms=sorted(specimen_contact_geoms),
        reference_and_cap=reference_reports,
        qualified_robot_handling=False,qualified_paper_branch=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    if not report['passed_asset_support']:raise SystemExit(1)


if __name__=='__main__':main()
