"""Contact-driven cabled plug insertion, release, withdrawal and return."""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
import shutil
from datetime import datetime,timezone
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
from connector_world import build
from hardware_control import HardwareRobot
from control import DOWN,ExecutionFailure
from world import HERE

ROTATION=Rotation.from_euler('z',np.pi/2).as_matrix()@DOWN


class ConnectorRobot(HardwareRobot):
    def contacts(self,body):
        records=[]
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'plug_lead' for g in c.geom]
            if body not in names:continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            records.append(dict(other=names[1-names.index(body)],force_n=float(force[0]),distance_m=float(c.dist)))
        return records

    def audit_contacts(self):
        super().audit_contacts()
        socket_load=0.
        for i,c in enumerate(self.data.contact):
            if min(c.geom)<0:continue
            names={self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom}
            if not any(n.startswith('jack_') for n in names):continue
            if not any(n=='plug' or n.startswith('plug_leaf_') for n in names):continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            socket_load+=max(0.,float(force[0]))
        if socket_load>5.:
            # Preserve the exact stopping state as well as the preceding trace.
            self.trace.append((float(self.data.time),self.data.qpos.copy(),self.data.qvel.copy(),self.data.ctrl.copy()))
            self.checkpoint('socket_force_limit',normal_force_N=socket_load,limit_N=5.)
            raise ExecutionFailure('Socket contact exceeded selected 5 N stop bound')
        for i,c in enumerate(self.data.contact):
            names=[self.model.body(int(self.model.geom_bodyid[g])).name if g>=0 else 'plug_lead' for g in c.geom]
            if not set(names)&{'left_finger','right_finger'}:continue
            other=next((n for n in names if n not in {'left_finger','right_finger'}),None)
            if other in {'plug','hand',None}:continue
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            if force[0]>.05:raise ExecutionFailure('Unintended finger contact: '+str(names)+' '+str(float(force[0])))

    def held_pose(self):
        if not {'left_finger','right_finger'}<={c['other'] for c in self.contacts('plug') if c['force_n']>.02}:raise ExecutionFailure('Plug grip lost')
        body=self.data.body('plug').xmat.reshape(3,3)
        return body.T@(self.data.site_xpos[self.site]-self.position('plug')),body.T@self.data.site_xmat[self.site].reshape(3,3)

    def position_plug(self,target,duration=.5):
        offset,rotation=self.held_pose();self.move(np.asarray(target)+offset,rotation,duration=duration)

    def observe_socket(self,configuration):
        entry=np.array(configuration['entry_m']);tip=self.data.site('plug_tip').xpos
        depth=float(tip[1]-entry[1]);lateral=float(np.linalg.norm((tip-entry)[[0,2]]));normal=0.;fingers=0.
        for i,c in enumerate(self.data.contact):
            if min(c.geom)<0:continue
            names={self.model.body(int(self.model.geom_bodyid[g])).name for g in c.geom}
            force=np.zeros(6);mujoco.mj_contactForce(self.model,self.data,i,force)
            if any(n.startswith('plug_leaf_') for n in names) and 'jack_'+configuration['port'] in names:normal+=force[0]
            if 'plug' in names and names&{'left_finger','right_finger'}:fingers+=force[0]
        return dict(insertion_depth_m=depth,lateral_error_m=lateral,leaf_contact_force_N=float(normal),finger_force_N=float(fingers),speed=float(np.linalg.norm(self.data.body('plug').cvel)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='runs/connector_debug/nominal');parser.add_argument('--no-spring',action='store_true');parser.add_argument('--blocked-bore',action='store_true');args=parser.parse_args()
    out=HERE/args.out;out.mkdir(parents=True,exist_ok=True)
    old=[p for p in out.iterdir() if p.name!='history']
    if old:
        history=out/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');history.mkdir(parents=True)
        for p in old:p.replace(history/p.name)
    names=['run_connector.py','connector_world.py','extended_device_assets.py','device_assets.py','hardware_control.py','continuous_control.py','control.py','world.py','contact_safety.py','geometry/keithley_2425/catalog.json']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={n:sha(HERE/n) for n in names}
    for name in names:
        target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(HERE/name,target)
    robot=None;passed=False;failure=None;configuration=None
    try:
        configuration=build(out/'workcell.xml',bore_radius=.0014 if args.blocked_bore else .002,spring=not args.no_spring);pins['workcell.xml']=sha(out/'workcell.xml')
        robot=ConnectorRobot(out/'workcell.xml');robot.grasp('plug',.012,8.,ROTATION,lift=.10)
        target=np.array(configuration['entry_m'])-[0,.023,0]
        robot.position_plug(target+[0,-.10,.10],2.);robot.position_plug(target+[0,-.10,0],1.)
        for offset in np.linspace(-.10,-.015,21)[1:]:robot.position_plug(target+[0,offset,0],.18)
        for _ in range(3):robot.position_plug(target+[0,-.015,0],.3)
        alignment=robot.observe_socket(configuration);robot.checkpoint('plug_aligned_before_entry',**alignment)
        if alignment['lateral_error_m']>.00015:raise ExecutionFailure('Plug tip not aligned before entry')
        for offset in np.linspace(-.015,0,61)[1:]:
            robot.position_plug(target+[0,offset,0],.08)
            observed=robot.observe_socket(configuration)
            if observed['leaf_contact_force_N']>10:raise ExecutionFailure('Insertion force exceeded selected 10 N bound')
        robot.finger(.026);robot.move(robot.data.site_xpos[robot.site]+[0,0,.12],ROTATION,1.2);robot.advance(2.)
        observed=robot.observe_socket(configuration);robot.checkpoint('plug_released_in_socket',**observed)
        if not (.009<observed['insertion_depth_m']<.011 and observed['lateral_error_m']<.0003 and observed['leaf_contact_force_N']>.1 and observed['finger_force_N']<.01 and observed['speed']<.03):
            raise ExecutionFailure('Plug failed retained insertion: '+str(observed))
        # Withdraw along the socket axis before lifting; a generic vertical
        # grasp-lift routine would pry the pin against the bore wall.
        robot.active_object='plug';robot.finger(.026);p=robot.grasp_site('plug');robot.move(p+[0,0,.10],ROTATION,1.5);robot.move(p,ROTATION,1.2)
        robot.finger(.008);robot.clamp_force=8.;robot.advance(.2)
        robot.position_plug(target+[0,-.08,0],1.8);robot.checkpoint('plug_withdrawn',**robot.observe_socket(configuration))
        park=np.array(configuration['park_m']);robot.position_plug(target+[0,-.08,.10],1.2);robot.position_plug(park+[0,0,.10],2.)
        for height in np.linspace(.10,.0001,30):robot.position_plug(park+[0,0,height],.16)
        robot.finger(.026);robot.move(robot.data.site_xpos[robot.site]+[0,0,.12],ROTATION,1.2);robot.advance(1.)
        error=float(np.linalg.norm(robot.position('plug')-park));robot.checkpoint('plug_returned',error_m=error)
        if error>.002:raise ExecutionFailure('Plug missed return stand')
        passed=True
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace])
        if any(sha(HERE/n)!=pins[n] for n in names):passed=False;failure='Source changed during execution'
        record=dict(status='passed' if passed else 'failed',failure=failure,configuration=configuration,observations=robot.timeline if robot else [],simulated_seconds=float(robot.data.time) if robot else 0,
                    input_sha256=pins,source_archive='source_snapshot',artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()},whole_paper_validated=False,
                    scope='One source-meter socket, selected cabled plug and passive contact leaves. No complete heater circuit or output-control qualification.')
        (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('RESULT',record['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
