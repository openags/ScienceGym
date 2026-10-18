"""Robot squeezes a passive brake release, slides the carriage and relocks."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
import numpy as np
import mujoco
from hardware_control import HardwareRobot
from reflector_world import build,TASK,EMITTER,DISK_Z
from world import HERE
from control import DOWN,ExecutionFailure


class ReflectorRobot(HardwareRobot):
    def mechanism(self):
        shoe_contacts=[]
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'flex' for g in c.geom]
            if set(names)!={'brake_shoe','track'}:continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            shoe_contacts.append(float(force[0]))
        return dict(release_travel_m=float(self.data.joint('retainer_travel').qpos[0]),
                    brake_lift_m=float(self.data.joint('brake_lift').qpos[0]),
                    brake_contact_N=sum(shoe_contacts),position_m=self.position('carriage').tolist())

    def check_grasp(self):
        fingers=set()
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'flex' for g in c.geom]
            if not set(names)&{'carriage','retainer_button'}:continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            if force[0]>.02:fingers.update(set(names)&{'left_finger','right_finger'})
        return fingers=={'left_finger','right_finger'}

    def adjust(self,target,index):
        self.active_object='carriage';self.finger(.026)
        p=self.grasp_site('carriage');self.move(p+[0,0,.14],DOWN,duration=1.5)
        self.move(p,DOWN,duration=1.2);self.finger(.010);self.clamp_force=16.;self.advance(.25)
        observed=self.mechanism()
        if not self.check_grasp() or observed['brake_lift_m']<.0015 or observed['brake_contact_N']>.05:
            raise ExecutionFailure('Retainer did not physically release: '+str(observed))
        self.checkpoint('retainer_released',command_index=index,observation=observed)
        start=self.position('carriage');target=np.asarray(target)
        for u in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(target-start)/.005)))+1)[1:]:
            if not self.check_grasp() or self.mechanism()['brake_lift_m']<.0015:raise ExecutionFailure('Carriage lost retained release during slide')
            # Follow the actual curved slot, using the live payload-to-TCP
            # displacement; never write carriage coordinates.
            x=start[0]+u*(target[0]-start[0]);q=x-(EMITTER[0]+self.configuration['guide_reference_xy_m'][0])
            y=EMITTER[1]+self.configuration['guide_reference_xy_m'][1]+np.polynomial.polynomial.polyval(q,self.configuration['guide_coefficients'])
            offset=self.data.site_xpos[self.site]-self.position('carriage')
            self.move(np.array([x,y,target[2]])+offset,DOWN,duration=.25)
        self.finger(.026);self.move(self.data.site_xpos[self.site]+[0,0,.14],DOWN,duration=1.2);self.advance(.3)
        observed=self.mechanism();error=float(np.linalg.norm(self.position('carriage')-target))
        if error>.001 or observed['brake_contact_N']<1 or observed['brake_lift_m']>.0001:
            raise ExecutionFailure('Carriage did not lock at target: '+str(dict(error_m=error,**observed)))
        self.checkpoint('carriage_locked',command_index=index,target_m=target.tolist(),error_m=error,observation=observed)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='runs/reflector_debug');parser.add_argument('--all-commands',action='store_true')
    parser.add_argument('--no-brake',action='store_true');parser.add_argument('--blocked-release',action='store_true');args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True);old=[p for p in out.iterdir() if p.name!='history']
    if old:
        history=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    names=['run_reflector.py','reflector_world.py','hardware_control.py','continuous_control.py','device_assets.py','control.py','world.py','contact_safety.py']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={n:sha(HERE/n) for n in names}
    for name in names:
        target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/name,target)
    shutil.copyfile(TASK/'selected_solar_path.json',out/'source_snapshot/selected_solar_path.json')
    robot=None;configuration=None;passed=False;failure=None;indices=[]
    try:
        configuration=build(out/'workcell.xml',not args.no_brake,args.blocked_release);pins['workcell.xml']=sha(out/'workcell.xml')
        robot=ReflectorRobot(out/'workcell.xml');robot.configuration=configuration
        robot.checkpoint('initial_brake_observed',observation=robot.mechanism())
        if robot.mechanism()['brake_contact_N']<1:raise ExecutionFailure('Initial spring brake lacks preload')
        samples=json.loads((TASK/'selected_solar_path.json').read_text())['samples']
        indices=list(range(len(samples))) if args.all_commands else [0,60,120,180,240]
        for index in indices:
            p=EMITTER+np.array(samples[index]['position_m'])-[0,0,.003]
            robot.adjust(p,index)
        passed=True
    except BaseException as e:failure=type(e).__name__+': '+str(e);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Source changed during execution'
        result=dict(status='passed' if passed else 'failed',failure=failure,configuration=configuration,input_sha256=pins,source_archive='source_snapshot',
                    observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
                    selected_command_indices=indices,whole_paper_validated=False,
                    waiting_model='Commands preserve order and physical state; long solar-time waits are external device-process intervals, not simulated stability tests',
                    scope='Physical carriage release, guided sliding and spring relock; pre-mounted disk/track, no source fabrication or campaign qualification',
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
