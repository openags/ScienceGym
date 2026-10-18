"""Instrumented mechanism jig: contact-driven screw, release, axial pull.

This is a selected-mechanism check, not a Panda manipulation receipt. The jig
guides a driver axially and supplies motor torque. The screw and the free wire
receive no actuation, pose assignments or attachments during simulation.
"""
import argparse
import json
import shutil
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from world import World,vec,HERE
from terminal_mechanism import add_terminal,add_driver,WIRE_DIAMETER,WIRE_DENSITY,PITCH
from trace_store import sha


def build(path,clamp=True,bit=True,friction=True,dt=.0001,noslip=3,pin=3):
    root=ET.Element('mujoco',model='USB-TC selected terminal mechanism jig')
    ET.SubElement(root,'compiler',angle='radian')
    ET.SubElement(root,'option',timestep=str(dt),integrator='implicitfast',solver='Newton',iterations='100',
                  tolerance='1e-10',cone='elliptic',gravity='0 0 -9.81',noslip_iterations=str(noslip),noslip_tolerance='1e-12')
    default=ET.SubElement(root,'default');ET.SubElement(default,'geom',solref='.0005 1',solimp='.9999 .9999 .00001',condim='3')
    w=SimpleNamespace(root=root,assets=ET.SubElement(root,'asset'),w=ET.SubElement(root,'worldbody'))
    w.box=lambda *a,**k:World.box(w,*a,**k);w.cylinder=lambda *a,**k:World.cylinder(w,*a,**k)
    terminal=ET.SubElement(w.w,'body',name='daq_fixture')
    config=add_terminal(w,terminal,pin=pin,visual=False,clamp=clamp,friction=friction)
    entry=np.array(config['wire_entry_m']);axis=np.array(config['insertion_axis']);origin=np.array(config['screw_center_m'])
    driver=ET.SubElement(w.w,'body',name='guided_driver',pos=vec(origin+[0,0,.00023]),gravcomp='1')
    ET.SubElement(driver,'joint',name='driver_z',type='slide',axis='0 0 1',range='-.003 .006',damping='.1')
    ET.SubElement(driver,'inertial',mass='.02',diaginertia='.000001 .000001 .000001',pos='0 0 .03')
    add_driver(w,driver,visual=False,bit=bit)
    ET.SubElement(root.find('actuator'),'motor',name='driver_axial',joint='driver_z',ctrlrange='-.5 .5')
    wirepos=entry+axis*(.005-.010);wirepos[2]=config['wire_floor_m']+WIRE_DIAMETER/2+.000001
    wire=ET.SubElement(w.w,'body',name='wire',pos=vec(wirepos))
    ET.SubElement(wire,'freejoint',name='wire_free')
    w.cylinder(wire,'wire_conductor',WIRE_DIAMETER/2,.010,euler='1.57079632679 0 0',
               rgba=[.7,.3,.1,1],mass=str(WIRE_DENSITY*np.pi*(WIRE_DIAMETER/2)**2*.02),friction='.5 .00001 .000001')
    # A frictionless support ledge carries the initially inserted wire outside
    # the terminal. It does not restrain axial motion or supply pull retention.
    ledge=entry-axis*.009;ledge[2]=config['wire_floor_m']-.001
    w.box(w.w,'staging_ledge',[.003,.009,.001],ledge,
          friction='0 0 0',rgba=[.1,.4,.5,1])
    ET.indent(root);ET.ElementTree(root).write(path,encoding='unicode')
    return config


def run(out,clamp=True,bit=True,friction=True,dt=.0001,noslip=3,pin=3):
    out.mkdir(parents=True,exist_ok=True)
    source_names=['test_terminal_mechanism.py','terminal_mechanism.py','world.py','extended_device_assets.py','device_assets.py',
                  '../../assets/mcc_usb_tc_v1/interfaces.json']
    pins={n:sha(HERE/n) for n in source_names};archive=out/'source_snapshot';archive.mkdir(exist_ok=True)
    archive_paths={n:'source_snapshot/'+n.replace('../','parent/') for n in source_names}
    for n in source_names:
        dest=out/archive_paths[n];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/n,dest)
    config=build(out/'workcell.xml',clamp=clamp,bit=bit,friction=friction,dt=dt,noslip=noslip,pin=pin)
    model=mujoco.MjModel.from_xml_path(str(out/'workcell.xml'));data=mujoco.MjData(model)
    mujoco.mj_forward(model,data)
    initial_intersections=[dict(geoms=[model.geom(g).name for g in c.geom],depth_m=-float(c.dist)) for c in data.contact if c.dist<-.00001]
    if initial_intersections:raise ValueError('Initial mechanism intersection: '+str(initial_intersections))
    normal=0.;trace=[];events=[];maxiter=0;capsteps=0;max_thread=0.;max_capture=0.;peak_contact=0.;status='turning'
    wire=model.body('wire').id;driver=model.actuator('driver_motor').id;axial=model.actuator('driver_axial').id
    prefix=config['prefix'];stopped=None;released=None;baseline=None;pull_started=None;pull_end=None
    initial_wire=None;peak_pull_displacement=0.
    def save():
        row=(float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy(),normal,driver_force,advance,turn,plate,data.xfrc_applied[wire].copy())
        if trace and abs(trace[-1][0]-data.time)<1e-10:trace[-1]=row
        else:trace.append(row)
    for step in range(round(30/dt)):
        data.ctrl[driver]=-2 if status=='turning' else 0
        data.ctrl[axial]=-.12 if status=='turning' else .3
        if status=='pull':data.xfrc_applied[wire,:3]=-np.array(config['insertion_axis'],float)
        else:data.xfrc_applied[wire,:]=0
        mujoco.mj_step(model,data)
        maxiter=max(maxiter,int(np.max(data.solver_niter)));capsteps+=int(np.max(data.solver_niter))>=model.opt.iterations
        advance=float(data.joint(prefix+'_advance').qpos[0]);turn=float(data.joint(prefix+'_turn').qpos[0]);plate=float(data.joint(prefix+'_plate_slide').qpos[0])
        max_thread=max(max_thread,abs(advance-turn*PITCH/(2*np.pi)));max_capture=max(max_capture,abs(plate-advance))
        normal=0.;driver_force=0.
        for i,c in enumerate(data.contact):
            geom_names={model.geom(g).name for g in c.geom};force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force)
            peak_contact=max(peak_contact,float(force[0]))
            if {prefix+'_pressure_plate','wire_conductor'}<=geom_names:normal+=force[0]
            if 'driver_bit' in geom_names:driver_force+=force[0]
        if step%50==0:save()
        if step%round(5/dt)==0:print('MECHANISM',round(data.time,3),status,'advance',advance,'turn',turn,'normal',normal,flush=True)
        if any(w.number for w in data.warning):status='numerical_warning';break
        if data.time>.01 and (max_thread>.00001 or max_capture>.00001):status='constraint_error';break
        if peak_contact>20:status='excess_contact_force';break
        if status=='turning' and normal>=4:
            events.append(dict(event='clamped',time=float(data.time),normal_N=float(normal),advance_m=advance,turn_rad=turn));save();status='retracting';stopped=float(data.time)
        if status=='turning' and data.time>20:
            status='no_clamp_force';break
        if status=='retracting' and data.time-stopped>1:
            released=float(data.time);baseline=data.body('wire').xpos.copy();events.append(dict(event='driver_released',time=released,normal_N=float(normal),driver_contact_N=float(driver_force)));save();status='hold'
        if status=='hold' and data.time-released>1:
            initial_wire=data.body('wire').xpos.copy();pull_started=float(data.time);events.append(dict(event='pull_started',time=pull_started));save();status='pull'
        if status=='pull':
            peak_pull_displacement=max(peak_pull_displacement,float(np.linalg.norm(data.body('wire').xpos-initial_wire)))
            if peak_pull_displacement>.002:
                events.append(dict(event='wire_pulled_out',time=float(data.time),normal_N=float(normal),peak_displacement_m=peak_pull_displacement,applied_pull_N=1.));status='pull_out';break
            if data.time-pull_started>1:
                pull_end=float(data.time);events.append(dict(event='pull_complete',time=pull_end,normal_N=float(normal),peak_displacement_m=peak_pull_displacement,applied_pull_N=1.));status='done';break
    save()
    retained=status=='done' and peak_pull_displacement<.0002 and normal>1 and driver_force<.01
    numerics=not any(w.number for w in data.warning) and capsteps==0 and max_thread<.00001 and max_capture<.00001
    result=dict(status=status,retained=bool(retained),numerics_passed=bool(numerics),events=events,
        maximum_solver_iterations=maxiter,solver_cap_steps=capsteps,warnings=[int(w.number) for w in data.warning],
        max_thread_constraint_error_m=max_thread,max_capture_constraint_error_m=max_capture,peak_contact_N=peak_contact,
        final_wire_m=data.body('wire').xpos.tolist(),configuration=config,clamp_present=clamp,driver_bit_present=bit,thread_friction_present=friction,
        simulated_seconds=float(data.time),engine_version=mujoco.__version__,source_sha256=pins,source_archive=archive_paths,source_unchanged=all(sha(HERE/n)==pins[n] for n in source_names),initial_intersections=initial_intersections,
        timestep_s=dt,noslip_iterations=noslip,noslip_tolerance=1e-12,
        scope='Guided motorized-driver mechanism test with initially inserted free wire and 1 N axial pull. No robot, cable routing, fine-wire transition or electrical qualification.',whole_paper_validated=False)
    np.savez_compressed(out/'physics_trace.npz',time=[r[0] for r in trace],qpos=[r[1] for r in trace],qvel=[r[2] for r in trace],ctrl=[r[3] for r in trace],
        clamp_normal_N=[r[4] for r in trace],driver_contact_N=[r[5] for r in trace],advance_m=[r[6] for r in trace],turn_rad=[r[7] for r in trace],plate_m=[r[8] for r in trace],wire_xfrc=[r[9] for r in trace])
    result['artifact_sha256']={n:sha(out/n) for n in ['physics_trace.npz','workcell.xml']}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='runs/terminal_debug/mechanism');p.add_argument('--no-clamp',action='store_true');p.add_argument('--no-bit',action='store_true');p.add_argument('--no-friction',action='store_true');p.add_argument('--dt',type=float,default=.0001);p.add_argument('--noslip',type=int,default=3);p.add_argument('--pin',type=int,default=3);a=p.parse_args()
    result=run(HERE/a.out,not a.no_clamp,not a.no_bit,not a.no_friction,a.dt,a.noslip,a.pin)
    raise SystemExit(0 if result['retained'] and result['numerics_passed'] else 1)
