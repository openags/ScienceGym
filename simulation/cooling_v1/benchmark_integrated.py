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
from membrane import sheet


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
    parser=argparse.ArgumentParser();parser.add_argument('--noslip',type=int,default=0);parser.add_argument('--upward-hand',action='store_true');parser.add_argument('--impratio',type=float,default=10)
    parser.add_argument('--membrane-sectors',type=int,default=16)
    parser.add_argument('--edge-timeconst',type=float,default=.001)
    parser.add_argument('--edge-damping',type=float,default=0)
    parser.add_argument('--no-sleep',action='store_true')
    args=parser.parse_args()
    out=HERE/'runs/integrated_debug'/(f'noslip_{args.noslip}'+('_upward' if args.upward_hand else '')+('_imp'+str(args.impratio) if args.impratio!=10 else '')+f'_mesh{args.membrane_sectors}_tc{args.edge_timeconst}_ed{args.edge_damping}'+('_awake' if args.no_sleep else ''))
    out.mkdir(parents=True,exist_ok=True)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source_names=['benchmark_integrated.py','run_integrated.py','integrated_world.py','integrated_control.py','continuous_control.py','continuous_world.py','cover_control.py','evaluate_cover.py','evaluate_continuous.py','membrane.py','contact_safety.py','support_observation.py']
    pins={n:sha(HERE/n) for n in source_names};robot=None;passed=False;failure=None;assessment=None
    try:
        targets=build(out/'workcell.xml');xml=ET.parse(out/'workcell.xml')
        xml.getroot().find('option').set('noslip_iterations',str(args.noslip))
        xml.getroot().find('option').set('impratio',str(args.impratio))
        if args.no_sleep:xml.getroot().find('option/flag').set('sleep','disable')
        cover=xml.getroot().find(".//body[@name='cover']")
        for child in list(cover):
            if child.tag=='flexcomp' or '_bonded_annulus_' in child.get('name',''):
                cover.remove(child)
        props=[sheet(cover,'cover_lower',-.003208,sectors=args.membrane_sectors),
               sheet(cover,'cover_upper',.003208,sectors=args.membrane_sectors)]
        cover.find("geom[@name='bonded_mass']").set('mass',str(sum(p['mass_on_parent_kg'] for p in props)))
        for edge in cover.findall('flexcomp/edge'):
            edge.set('solref',f'{args.edge_timeconst} 1')
            edge.set('damping',str(args.edge_damping))
        targets['cover']['film_properties']=props
        xml.write(out/'workcell.xml',encoding='unicode')
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
                    solver_selection=dict(noslip_iterations=args.noslip,impratio=args.impratio,upward_hand=args.upward_hand,membrane_sectors=args.membrane_sectors,edge_timeconst_s=args.edge_timeconst,edge_damping_N_s_m=args.edge_damping,sleep_enabled=not args.no_sleep),input_sha256=pins,
                    simulated_seconds=float(robot.data.time) if robot else 0,observations=robot.timeline if robot else [],
                    whole_paper_validated=False,canonical_evidence=False,
                    artifacts_sha256={n:sha(out/n) for n in ['physics_trace.npz'] if (out/n).exists()})
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',result['status'],failure,flush=True)
    return passed


if __name__=='__main__':raise SystemExit(0 if main() else 1)
