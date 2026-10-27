"""Screen a continuous tweezer-held witness lift from the open FTIR port.

Uses the actual G1/Inspire link meshes, the deformed ordinary tweezers and
the identified annular witness. This development path begins at a held
specimen; approach, release, transfer, dynamics and full-scene review are
separate requirements.
"""
import argparse,hashlib,itertools,json
from collections import defaultdict
from pathlib import Path
import numpy as np,trimesh
from playwright.sync_api import sync_playwright
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,ASSETS,KIN,fk,robot_meshes
from tweezers_geometry import meshes as tool_meshes
from plan_reference_storage import geometry,translation

HERE=Path(__file__).resolve().parent
JOINT_BY_CHILD={j['id']:j for j in KIN['joints']}
PALM_CHAIN=[];link='right_palm_force_sensor'
while link!=KIN['root_link']:
    joint=JOINT_BY_CHILD[link];PALM_CHAIN.insert(0,joint);link=joint['parent']


def palm_fk(q):
    matrix=np.array(KIN['root_matrix'])
    for joint in PALM_CHAIN:
        local=np.array(joint['origin_matrix']);value=q.get(joint['name'],0.)
        if value:
            turn=np.eye(4);turn[:3,:3]=Rotation.from_rotvec(np.array(joint['axis'])*value).as_matrix();local=local@turn
        matrix=matrix@local
    return matrix


def solve(stances,fit,setup):
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page();page.route('**/cooling_concept_v2/main.js',lambda r:r.fulfill(status=200,content_type='application/javascript',body=''))
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
        result=page.evaluate('''async({stances,fit,setup})=>{
          const {HandIK}=await import('./hand_ik.js'),T=await import('three');
          const manifest=await(await fetch('./runtime_scene.json')).json(),poses=await(await fetch('./motion_poses.json')).json();
          const kin=manifest.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
          kin.joints.find(j=>j.name==='right_shoulder_roll_joint').limits.upper=-.025;
          const ik=new HandIK(kin),palm=new T.Matrix4().fromArray(fit.holder_T_tool.flat()).transpose().multiply(new T.Matrix4().fromArray(fit.tool_T_palm.flat()).transpose()),out=[];
          for(const stance of stances){
            const q={...poses.poses.rest,...poses.poses.stance,...fit.carrier_grip_q,waist_pitch_joint:stance.waist};
            const world=ik.forward(q).world;let bottom=Infinity;
            for(const[name,vertices]of Object.entries(poses.sole_vertices_m))for(const v of vertices)bottom=Math.min(bottom,new T.Vector3(...v).applyMatrix4(world.get(name)).z);
            const root=new T.Matrix4().makeRotationZ(stance.yaw).setPosition(...stance.xy,-bottom),inverse=root.clone().invert(),rows=[];
            const offsets=[[0,0,0],[0,0,.06],[0,-.12,.12],[0,-.22,.12]];
            for(let i=0;i<=60;i++){
              const seg=Math.min(2,Math.floor(i/20)),u=(i-seg*20)/20,offset=offsets[seg].map((v,k)=>v+(offsets[seg+1][k]-v)*u);
              const holder=new T.Matrix4().makeTranslation(...setup.ports.ftir_sample.position_m.map((v,k)=>v+offset[k]+(k===2?.000001:0)));
              const target=inverse.clone().multiply(holder).multiply(palm),point=new T.Vector3().setFromMatrixPosition(target);
              let error,rotationError;if(i===0){error=ik.solve(q,'right',point,target);rotationError=ik.lastRotationError;}else({error,rotationError}=ik.iterate(q,'right',point,target,120));
              rows.push({q:{...q},error,rotationError,holder:holder.toArray()});if(error>.0003||rotationError>.003)break;
            }out.push({stance,root:root.toArray(),rows});
          }return out;
        }''',dict(stances=stances,fit=fit,setup=setup));browser.close()
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--from-plan');parser.add_argument('--candidate',type=int,default=6);parser.add_argument('--output',default='previews/specimen_port_paths.json');args=parser.parse_args()
    fit=json.loads((HERE/'previews/specimen_tool_fit.json').read_text());assert fit['passed']
    setup=json.loads((HERE/'optical_setup.json').read_text());stances=[dict(xy=[x,7.85],yaw=yaw,waist=waist) for x,yaw,waist in itertools.product([8.95,9.05,9.15,9.25],[1.4,np.pi/2,1.7],[.15,.3])]
    paths=[json.loads(Path(args.from_plan).read_text())['candidates'][args.candidate]] if args.from_plan else solve(stances,fit,setup)
    obstacles,reference,rest=geometry(setup)
    # The gold standard remains in its protective cap during specimen work.
    reference_data=json.loads((HERE/'reference_transfer.json').read_text());delta=translation(reference_data['segments'][-1]['rows'][-1]['reference_offset'])
    gold_source=trimesh.load(ROOT/ASSETS['pike']['geometry'],force='scene',process=False)
    for name,transform in rest.items():
        _,key=gold_source.graph[name.split('::')[1]];obstacles.add_object(name,gold_source.geometry[key],delta@transform)
    robot=trimesh.collision.CollisionManager();parts={n:m for n,m in robot_meshes().items() if 'ankle' not in n}
    for name,mesh in parts.items():robot.add_object(name,mesh)
    tool=trimesh.collision.CollisionManager();tool_local=tool_meshes(fit['carrier_grip_closure'])
    for name,mesh in tool_local.items():tool.add_object(name,mesh)
    witness=trimesh.collision.CollisionManager();source=trimesh.load(ROOT/'assets/cooling_optical_specimens_v1/witness_white.glb',force='scene',process=False);witness_local={}
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];witness.add_object(name,source.geometry[key],transform);witness_local[name]=transform
    graph=defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute');graph[j['parent']].append((j['id'],w));graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for link in parts:
        stack=[(link,None,0)]
        while stack:
            name,parent,d=stack.pop()
            if d>1:continue
            if name in parts:adjacent.add(tuple(sorted((link,name))))
            stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)
    palm_to_tool=np.linalg.inv(np.array(fit['tool_T_palm']));tool_to_holder=np.linalg.inv(np.array(fit['holder_T_tool']))
    arm=[j for j in KIN['joints'] if j['name'].startswith('right_') and any(s in j['name'] for s in ['shoulder','elbow','wrist']) and j['type']=='revolute']
    limits=np.array([[j['limits']['lower'],min(j['limits']['upper'],-.025) if j['name']=='right_shoulder_roll_joint' else j['limits']['upper']] for j in arm])
    for i,path in enumerate(paths):
        checks=[];base=np.array(path['root']).reshape(4,4).T
        for row in path['rows']:
            desired=np.array(row['holder']).reshape(4,4).T@np.array(fit['holder_T_tool'])@np.array(fit['tool_T_palm'])
            def residual(values):
                q={**row['q'],**{j['name']:float(v) for j,v in zip(arm,values)}};actual=base@palm_fk(q)
                return np.r_[(actual[:3,3]-desired[:3,3])*10,Rotation.from_matrix(desired[:3,:3].T@actual[:3,:3]).as_rotvec()]
            seed=np.clip([row['q'][j['name']] for j in arm],limits[:,0]+1e-9,limits[:,1]-1e-9)
            solved=least_squares(lambda v:np.r_[residual(v),(v-seed)*1e-7],seed,bounds=(limits[:,0],limits[:,1]),ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=80)
            row['q'].update({j['name']:float(v) for j,v in zip(arm,solved.x)})
            error=residual(solved.x);row['refined_error_m']=float(np.linalg.norm(error[:3])/10);row['refined_rotation_error_rad']=float(np.linalg.norm(error[3:]))
            world=fk(row['q']);actual_tool=base@world['right_palm_force_sensor']@palm_to_tool;actual_holder=actual_tool@tool_to_holder
            assert np.max(np.abs(palm_fk(row['q'])-world['right_palm_force_sensor']))<1e-12
            for name in parts:robot.set_transform(name,base@world[name])
            for name in tool_local:tool.set_transform(name,actual_tool)
            for name,local in witness_local.items():witness.set_transform(name,actual_holder@local)
            _,pairs=robot.in_collision_internal(return_names=True);own=sorted(p for p in pairs if tuple(sorted(p)) not in adjacent)
            check=dict(self_intersections=own)
            for label,a,b in [('robot_environment',robot,obstacles),('tool_environment',tool,obstacles),('witness_environment',witness,obstacles),('robot_tool',robot,tool),('robot_witness',robot,witness),('tool_witness',tool,witness)]:
                _,pairs=a.in_collision_other(b,return_names=True);check[label]=sorted(pairs)
            checks.append(check)
        path['checks']=checks;path['passed']=len(path['rows'])==61 and all(not any(c.values()) for c in checks) and all(r['refined_error_m']<1e-7 and r['refined_rotation_error_rad']<1e-6 for r in path['rows'])
        print('candidate',i,'knots',len(path['rows']),'passed',path['passed'],'maximum_error_m',max(r['refined_error_m'] for r in path['rows']),'rejection',next((c for c in checks if any(c.values())),{}),flush=True)
    output=dict(scope=__doc__,candidates=paths,passed=sum(p['passed'] for p in paths),fit_sha256=hashlib.sha256((HERE/'previews/specimen_tool_fit.json').read_bytes()).hexdigest(),planner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if args.from_plan:output['endpoint_source']=dict(path=args.from_plan,sha256=hashlib.sha256(Path(args.from_plan).read_bytes()).hexdigest(),candidate=args.candidate)
    out=HERE/args.output
    if out.exists():out.rename(out.with_name(out.stem+'_'+hashlib.sha256(out.read_bytes()).hexdigest()[:12]+out.suffix))
    out.write_text(json.dumps(output,indent=2)+'\n');print('passed_paths',output['passed'],flush=True)


if __name__=='__main__':main()
