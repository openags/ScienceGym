"""Compare a declared solver setting on the same complete physical sequence.

This writes a separate benchmark receipt and never replaces canonical evidence.
"""
import os
os.environ.setdefault('MUJOCO_GL','egl')
import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
import numpy as np
from world import HERE
from integrated_world import build
from integrated_control import IntegratedRobot
from run_integrated import execute
from initial_contacts import inspect
from cover_world import SIDE
from control import ExecutionFailure


class ProgressRobot(IntegratedRobot):
    def __init__(self,*args,upward=False,**kwargs):
        self.upward=upward
        self.next_progress=0;self.wall_start=time.monotonic()
        super().__init__(*args,**kwargs)

    def advance(self,duration):
        super().advance(duration)
        if self.data.time>=self.next_progress:
            print('PROGRESS',round(self.data.time,2),'wall',round(time.monotonic()-self.wall_start,1),'contacts',self.data.ncon,flush=True)
            self.next_progress=float(self.data.time)+5

    def grip_cover(self):
        if not self.upward:return super().grip_cover()
        rotation=SIDE@np.diag([-1,-1,1])
        self.finger(.020);p=self.grasp_site('cover')
        self.move(p+[0,-.08,.08],rotation,duration=2)
        self.move(p+[0,-.06,0],rotation,duration=1.5)
        self.move(p,rotation,duration=2);self.finger(0)
        contact=self.contacts('cover')
        if not {'left_finger','right_finger'}<={c['other'] for c in contact if c['force_n']>.05}:
            raise ExecutionFailure('Upward-hand cover annulus not bilaterally held')
        initial=self.position('cover')
        self.move(self.data.site_xpos[self.site]+[0,0,.12],rotation,duration=2)
        if self.position('cover')[2]-initial[2]<.09:raise ExecutionFailure('Upward-hand cover failed lift')
        self.checkpoint('cover_lifted',contacts=contact,position=self.position('cover').tolist())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--noslip',type=int,default=0);parser.add_argument('--upward-hand',action='store_true');parser.add_argument('--impratio',type=float,default=10);args=parser.parse_args()
    out=HERE/'runs/integrated_debug'/(f'noslip_{args.noslip}'+('_upward' if args.upward_hand else '')+('_imp'+str(args.impratio) if args.impratio!=10 else ''))
    out.mkdir(parents=True,exist_ok=True)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source_names=['benchmark_integrated.py','run_integrated.py','integrated_world.py','integrated_control.py','continuous_control.py','continuous_world.py','cover_control.py','evaluate_cover.py','evaluate_continuous.py','membrane.py','contact_safety.py','support_observation.py']
    pins={n:sha(HERE/n) for n in source_names};robot=None;passed=False;failure=None;assessment=None
    try:
        targets=build(out/'workcell.xml');xml=ET.parse(out/'workcell.xml')
        xml.getroot().find('option').set('noslip_iterations',str(args.noslip))
        xml.getroot().find('option').set('impratio',str(args.impratio));xml.write(out/'workcell.xml',encoding='unicode')
        pins['workcell.xml']=sha(out/'workcell.xml')
        initial=inspect(out/'workcell.xml',{n:n+'_stand' for n in targets})
        robot=ProgressRobot(out/'workcell.xml',upward=args.upward_hand)
        assessment=execute(robot,targets,None);passed=assessment['passed']
    except BaseException as error:failure=type(error).__name__+': '+str(error);print(failure,flush=True)
    finally:
        if robot:
            robot.close();np.savez_compressed(out/'physics_trace.npz',time=[s[0] for s in robot.trace],qpos=[s[1] for s in robot.trace],qvel=[s[2] for s in robot.trace],ctrl=[s[3] for s in robot.trace],tree_asleep=robot.sleep_trace)
        if any(sha(HERE/n)!=pins[n] for n in source_names):passed=False;failure='Source changed during benchmark'
        result=dict(status='passed' if passed else 'failed',failure=failure,evaluation=assessment,targets=targets,
                    solver_selection=dict(noslip_iterations=args.noslip,impratio=args.impratio,upward_hand=args.upward_hand),input_sha256=pins,
                    simulated_seconds=float(robot.data.time) if robot else 0,observations=robot.timeline if robot else [],
                    whole_paper_validated=False,canonical_evidence=False,
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
