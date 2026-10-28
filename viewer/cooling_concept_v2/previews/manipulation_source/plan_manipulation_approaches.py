"""Collision-plan free-hand approaches using the actual stationary work scene.

Paths join the lowered idle posture to existing collision-free pregrasps.
Both arms, waist and thumb opposition are planned together for apparatus
handling. Cover paths also plan the three unused fingers and inactive-arm yaw.
This is choreography planning, not dynamics or whole-film qualification. The
independent reviewer must include the floor and ankle meshes omitted here.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import time

import numpy as np
import trimesh
from playwright.sync_api import sync_playwright

from plan_optical_approaches import plan
from source_geometry import ROOT, ASSETS, MANIFEST, KIN, fk, robot_meshes

HERE=Path(__file__).resolve().parent
SOURCES=['main.js','motion_poses.json','hand_ik.js','grasp_profile.json','optical_setup.json','optical_approach_paths.json']


def matrix(value):return np.asarray(value).reshape(4,4).T


def capture_inputs():
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    dest=HERE/'previews/manipulation_approach_inputs.json'
    old=json.loads(dest.read_text()) if dest.exists() else {}
    if old.get('source_sha256')==pins:return old
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',
            args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],
            env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':640,'height':360})
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        frames=page.evaluate('''()=>{
          const result={};
          for(const p of concept.phases){
            if(p.action==='pick')result[p.id]={phase:p.id,kind:'carry',start:auditFrame(p.start),target:auditFrame(p.start+2)};
            else if(p.action==='place')result[p.id]={phase:p.id,kind:'carry',start:auditFrame(p.end-.00001),target:auditFrame(p.start+6.8)};
            else if(p.action?.startsWith('lid_')||p.action?.startsWith('cover_')){
              result[p.id+'_entry']={phase:p.id,kind:'lid',start:auditFrame(p.start),target:auditFrame(p.start+2)};
              result[p.id+'_exit']={phase:p.id,kind:'lid',start:auditFrame(p.end-.00001),target:auditFrame(p.start+10.8)};
            }
          }
          return {frames:result,extraGeometry:concept.extraGeometry,sourceHashes:concept.sourceHashes};
        }''')
        browser.close()
    packet=dict(source_sha256=pins,**frames)
    dest.write_text(json.dumps(packet,separators=(',',':'))+'\n')
    return packet


class Geometry:
    def __init__(self):
        self.scenes={}
        self.meshes={n:m for n,m in robot_meshes().items() if 'ankle' not in n}
        self.adjacent=set();graph=defaultdict(list)
        for j in KIN['joints']:
            w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
        for link in self.meshes:
            stack=[(link,None,0)]
            while stack:
                name,parent,d=stack.pop()
                if d>1:continue
                if name in self.meshes:self.adjacent.add(tuple(sorted((link,name))))
                stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)

    def scene(self,path):
        if path not in self.scenes:self.scenes[path]=trimesh.load(ROOT/path,force='scene',process=False)
        return self.scenes[path]


class Space:
    def __init__(self,source,extras,geometry):
        start,target=source['start'],source['target'];self.calls=0;self.cache={};self.geometry=geometry
        self.base=matrix(start['groups']['g1']);self.q=dict(start['joints']);self.kind=source['kind']
        arms=[j['name'] for j in KIN['joints'] if j['type']=='revolute' and any(j['name'].startswith(s+'_') for s in ['left','right']) and any(n in j['name'] for n in ['shoulder','elbow','wrist'])]
        self.names=(arms+['waist_pitch_joint','left_thumb_1_joint','right_thumb_1_joint'] if self.kind=='carry' else
                    [n for n in arms if n.startswith('right_')]+['waist_pitch_joint','right_thumb_1_joint','left_shoulder_yaw_joint','right_unused_finger_fold'])
        limits={j['name']:j['limits'] for j in KIN['joints'] if j['type']=='revolute'}
        def value(q,name):return q.get('right_middle_1_joint' if name=='right_unused_finger_fold' else name,0)
        self.start=np.array([value(start['joints'],n) for n in self.names]);self.goal=np.array([value(target['joints'],n) for n in self.names])
        self.bounds=np.array([[limits[n]['lower']+.0005,limits[n]['upper']-.0005] if n in limits else [0,1.1] for n in self.names])
        self.bounds[self.names.index('waist_pitch_joint')]=[0,.40]
        for i,name in enumerate(self.names):
            if 'thumb' in name:self.bounds[i]=[0,limits[name]['upper']]
            elif name=='left_shoulder_yaw_joint' and self.kind=='lid':self.bounds[i]=[0,.6]
        self.scale=np.array([3 if n=='waist_pitch_joint' else .5 if 'thumb' in n or 'fold' in n else 1 for n in self.names])
        self.robot=trimesh.collision.CollisionManager()
        for name,mesh in geometry.meshes.items():self.robot.add_object(name,mesh)
        self.obstacles=trimesh.collision.CollisionManager();self.roi=np.array([self.base[:3,3]+[-1.35,-1.35,-.1],self.base[:3,3]+[1.35,1.35,2.]])
        def near(bounds):return bool(np.all(bounds[1]>=self.roi[0]) and np.all(bounds[0]<=self.roi[1]))
        def world_bounds(bounds,transform):
            corners=np.array(list(itertools.product(*np.array(bounds).T)))
            vertices=trimesh.transform_points(corners,transform);return np.array([vertices.min(0),vertices.max(0)])
        def add(name,mesh,transform):
            if near(world_bounds(mesh.bounds,transform)):self.obstacles.add_object(name,mesh,transform)
        roles={p['id']:p['role'] for p in MANIFEST['architecture']['part_records']}
        arch=geometry.scene(MANIFEST['architecture']['path'])
        for name in arch.graph.nodes_geometry:
            if roles.get(name)=='floor':continue
            transform,key=arch.graph[name];add('room::'+name,arch.geometry[key],transform)
        explicit={}
        for part in target['parts']:explicit.setdefault(part['asset'],{})[part['name']]=matrix(part['matrix'])
        for identity,asset in ASSETS.items():
            if identity=='g1':continue
            base=matrix(target['groups'][identity])
            if identity not in explicit and not near(world_bounds(asset['normalized_bounds_m'],base)):continue
            scene=geometry.scene(asset['geometry'])
            for name in scene.graph.nodes_geometry:
                local,key=scene.graph[name];transform=explicit.get(identity,{}).get(name,base@local)
                add(identity+'::'+name,scene.geometry[key],transform)
        for item in extras:
            mesh=trimesh.Trimesh(vertices=np.array(item['vertices']).reshape(-1,3),faces=np.array(item['indices']).reshape(-1,3),process=False)
            add('extra::'+item['id'],mesh,matrix(target['extra_matrices'][item['id']]))

    def values_to_q(self,values):
        q={**self.q,**dict(zip(self.names,values))}
        if self.kind=='lid':
            fold=q.pop('right_unused_finger_fold')
            for finger in ['middle','ring','little']:q['right_'+finger+'_1_joint']=fold
        return q

    def free(self,values):
        key=tuple(np.round(values,6))
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if np.any(values<self.bounds[:,0]-1e-6) or np.any(values>self.bounds[:,1]+1e-6):
            self.last_rejection='joint bounds';return False
        world=fk(self.values_to_q(values))
        for name in self.geometry.meshes:self.robot.set_transform(name,self.base@world[name])
        _,pairs=self.robot.in_collision_internal(return_names=True)
        unexpected=[p for p in pairs if tuple(sorted(p)) not in self.geometry.adjacent]
        self.last_rejection=dict(self=unexpected);ok=not unexpected
        if ok:
            hit,pairs=self.robot.in_collision_other(self.obstacles,return_names=True);ok=not hit
            self.last_rejection=dict(environment=sorted(pairs))
        self.cache[key]=ok;return ok

    def distance(self,a,b):return np.linalg.norm((b-a)*self.scale)

    def edge(self,a,b):
        steps=max(1,int(np.ceil(self.distance(a,b)/.045)))
        return all(self.free(a+(b-a)*i/steps) for i in range(1,steps+1))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phases',default='.*');args=parser.parse_args()
    packet=capture_inputs();geometry=Geometry();output=HERE/'previews/manipulation_paths';output.mkdir(exist_ok=True)
    for name,source in packet['frames'].items():
        if not re.search(args.phases,name):continue
        started=time.monotonic();space=Space(source,packet['extraGeometry'],geometry)
        print('planning',name,'obstacles',len(space.obstacles._objs),flush=True)
        try:
            route=plan(space)
            result=dict(passed=True,joints=space.names,knots=[v.tolist() for v in route],
                        generalized_finger_joint={'right_unused_finger_fold':['right_'+f+'_1_joint' for f in ['middle','ring','little']]} if space.kind=='lid' else {},
                        maximum_edge_step=.045,roi=space.roi.tolist(),obstacle_count=len(space.obstacles._objs),
                        path_length=sum(space.distance(a,b) for a,b in zip(route,route[1:])))
        except RuntimeError as error:result=dict(passed=False,error=str(error))
        result.update(name=name,scope=__doc__,source_sha256=packet['source_sha256'],
                      input_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
                      planner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      rrt_sha256=hashlib.sha256((HERE/'plan_optical_approaches.py').read_bytes()).hexdigest(),
                      collision_queries=space.calls,seconds=time.monotonic()-started)
        (output/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print('result',name,result['passed'],space.calls,'seconds',round(result['seconds'],1),result.get('error',''),flush=True)


if __name__=='__main__':main()
