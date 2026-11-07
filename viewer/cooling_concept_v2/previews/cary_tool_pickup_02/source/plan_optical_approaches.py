"""Plan free-arm approaches around the actual FTIR housing and bench.

Deterministic joint-space BiRRT paths for authored choreography. The full scene
and continuous movie still require independent validation; no dynamics claim.
"""
import gzip,hashlib,json,os,time
from pathlib import Path
from collections import defaultdict
import numpy as np
import trimesh
from playwright.sync_api import sync_playwright
from source_geometry import ROOT,ASSETS,MANIFEST,KIN,fk,robot_meshes

HERE=Path(__file__).resolve().parent


def matrix(a):return np.asarray(a).reshape(4,4).T


def endpoints():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage','--enable-gpu','--use-gl=angle','--use-angle=vulkan','--ignore-gpu-blocklist'],env={**os.environ,'VK_ICD_FILENAMES':'/usr/share/vulkan/icd.d/nvidia_icd.json'})
        page=browser.new_page(viewport={'width':640,'height':360});page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean',timeout=120000)
        page.wait_for_function('document.documentElement.dataset.ready==="true"',timeout=120000)
        frames=page.evaluate("Object.fromEntries(['ftir_open','ftir_close'].map(id=>{const p=concept.phases.find(p=>p.id===id);return [id,{start:auditFrame(p.start),target:auditFrame(p.start+3)}]}))")
        browser.close();return frames


class Space:
    def __init__(self,frames):
        start=frames['start'];target=frames['target'];self.calls=0;self.cache={}
        self.base=matrix(start['groups']['g1'])
        self.q=dict(start['joints']);profile=json.loads((HERE/'grasp_profile.json').read_text())['ftir_cover']
        self.q.update({k:v if any(s in k for s in ['middle','ring','little','thumb_1']) else 0 for k,v in profile['q'].items()})
        for f in ['index','middle','ring','little','thumb']:
            for n in [1,2]:self.q[f'left_{f}_{n}_joint']=0
        self.names=[j['name'] for j in KIN['joints'] if j['name'].startswith('right_') and any(s in j['name'] for s in ['shoulder','elbow','wrist']) and j['type']=='revolute']+['waist_pitch_joint','right_thumb_1_joint']
        limits={j['name']:j['limits'] for j in KIN['joints'] if j['type']=='revolute'}
        self.bounds=np.array([[limits[n]['lower']+.0005,limits[n]['upper']-.0005] for n in self.names])
        self.bounds[self.names.index('right_shoulder_roll_joint'),1]=-.025
        self.bounds[-2]=[0,.4];self.bounds[-1]=[0,limits['right_thumb_1_joint']['upper']]
        self.start=np.array([start['joints'].get(n,0) for n in self.names]);self.goal=np.array([target['joints'].get(n,0) for n in self.names])
        self.scale=np.array([1.]*7+[3.,.5]);self.obstacles=trimesh.collision.CollisionManager()
        # The motion-planning region is explicit. The independent verifier
        # subsequently checks the entire laboratory, including every source asset.
        arch=trimesh.load(ROOT/MANIFEST['architecture']['path'],force='scene',process=False)
        for name in arch.graph.nodes_geometry:
            if 'ftir_bench' not in name:continue
            transform,key=arch.graph[name];self.obstacles.add_object('room::'+name,arch.geometry[key],transform)
        for identity in ['nicolet','pike']:
            source=trimesh.load(ROOT/ASSETS[identity]['geometry'],force='scene',process=False)
            explicit={p['name']:matrix(p['matrix']) for p in start['parts'] if p['asset']==identity}
            for name in source.graph.nodes_geometry:
                transform,key=source.graph[name];world=explicit.get(name,matrix(start['groups'][identity])@transform)
                self.obstacles.add_object(identity+'::'+name,source.geometry[key],world)
        setup=json.loads((HERE/'optical_setup.json').read_text());plate=setup['mount_plate']
        self.obstacles.add_object(plate['id'],trimesh.Trimesh(vertices=plate['vertices'],faces=plate['faces'],process=False))
        self.robot=trimesh.collision.CollisionManager();self.meshes={n:m for n,m in robot_meshes().items() if 'ankle' not in n}
        for name,mesh in self.meshes.items():self.robot.add_object(name,mesh)
        graph=defaultdict(list)
        for j in KIN['joints']:
            w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
        self.adjacent=set()
        for link in self.meshes:
            stack=[(link,None,0)]
            while stack:
                name,parent,d=stack.pop()
                if d>1:continue
                if name in self.meshes:self.adjacent.add(tuple(sorted((link,name))))
                stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)

    def free(self,values):
        key=tuple(np.round(values,6))
        if key in self.cache:return self.cache[key]
        self.calls+=1
        if np.any(values<self.bounds[:,0]-1e-6) or np.any(values>self.bounds[:,1]+1e-6):
            self.last_rejection='joint bounds';return False
        q={**self.q,**dict(zip(self.names,values))};world=fk(q)
        for name in self.meshes:self.robot.set_transform(name,self.base@world[name])
        _,pairs=self.robot.in_collision_internal(return_names=True)
        unexpected=[p for p in pairs if tuple(sorted(p)) not in self.adjacent];ok=not unexpected
        self.last_rejection=dict(self=unexpected)
        if ok:
            hit,pairs=self.robot.in_collision_other(self.obstacles,return_names=True);ok=not hit
            self.last_rejection=dict(environment=list(pairs))
        self.cache[key]=ok;return ok

    def edge(self,a,b):
        steps=max(1,int(np.ceil(np.linalg.norm((b-a)*self.scale)/.045)))
        return all(self.free(a+(b-a)*u/steps) for u in range(1,steps+1))

    def distance(self,a,b):return np.linalg.norm((a-b)*self.scale)


def path_to_root(tree,index):
    result=[]
    while index is not None:
        point,index=tree[index];result.append(point)
    return result[::-1]


def plan(space,seed=20261027):
    if not space.free(space.start):raise RuntimeError('Initial folded-hand state rejected: '+str(space.last_rejection))
    if not space.free(space.goal):raise RuntimeError('Pregrasp endpoint rejected: '+str(space.last_rejection))
    if space.edge(space.start,space.goal):return [space.start,space.goal]
    rng=np.random.default_rng(seed);a=[(space.start,None)];b=[(space.goal,None)];swapped=False
    def extend(tree,target):
        distances=np.array([space.distance(v,target) for v,_ in tree]);index=int(distances.argmin());origin=tree[index][0]
        delta=target-origin;length=space.distance(origin,target)
        point=target if length<=.22 else origin+delta*.22/length
        if not space.edge(origin,point):return None,False
        tree.append((point,index));return len(tree)-1,length<=.22
    for iteration in range(4000):
        if rng.random()<.2:sample=b[-1][0]
        elif rng.random()<.6:
            sample=space.start+(space.goal-space.start)*rng.random()+rng.normal(0,.65,len(space.start))/space.scale
            sample=np.clip(sample,space.bounds[:,0],space.bounds[:,1])
        else:sample=rng.uniform(space.bounds[:,0],space.bounds[:,1])
        ai,_=extend(a,sample)
        if ai is not None:
            for _ in range(80):
                bi,reached=extend(b,a[ai][0])
                if bi is None:break
                if reached:
                    path=path_to_root(a,ai)+path_to_root(b,bi)[::-1][1:]
                    if swapped:path=path[::-1]
                    for _ in range(100):
                        i,j=sorted(rng.choice(len(path),2,replace=False))
                        if j>i+1 and space.edge(path[i],path[j]):path=path[:i+1]+path[j:]
                    return path
        a,b=b,a;swapped=not swapped
        if iteration%100==0:print('rrt',iteration,'nodes',len(a)+len(b),'checks',space.calls,flush=True)
    raise RuntimeError('No free approach path found within the search budget')


def main():
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['main.js','motion_poses.json','grasp_profile.json','optical_setup.json','hand_ik.js']}
    cached=HERE/'previews/optical_approach_inputs.json'
    packet=json.loads(cached.read_text()) if cached.exists() else {}
    if packet.get('source_sha256')==pins:frames=packet['frames']
    else:
        frames=endpoints();cached.write_text(json.dumps(dict(source_sha256=pins,frames=frames),separators=(',',':'))+'\n')
    result={}
    for name,source in frames.items():
        began=time.monotonic();space=Space(source);print('planning',name,flush=True);path=plan(space)
        result[name]=dict(joints=space.names,knots=[p.tolist() for p in path],collision_queries=space.calls,
                          joint_path_length=float(sum(space.distance(a,b) for a,b in zip(path,path[1:]))),
                          seconds=time.monotonic()-began)
        print('planned',name,'knots',len(path),'checks',space.calls,flush=True)
    report=dict(scope=__doc__,source_sha256=pins,paths=result,full_scene_validation_pending=True)
    (HERE/'optical_approach_paths.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'previews/optical_approach_endpoints.json').write_text(json.dumps(frames,separators=(',',':'))+'\n')


if __name__=='__main__':main()
