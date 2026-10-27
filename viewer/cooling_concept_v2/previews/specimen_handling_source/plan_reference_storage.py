"""Continue the screened gold-reference lift into protective-cap storage.

Development geometry only. Root translation represents a proposed sidestep;
walking, free-arm entry/exit, dynamics and the full optical procedure still
require integration and independent review. No source asset is overwritten.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from playwright.sync_api import sync_playwright
from scipy.spatial.transform import Rotation

from source_geometry import ROOT, ASSETS, MANIFEST, KIN, fk, robot_meshes
from build_reference_cap_candidate import cap_mesh

HERE = Path(__file__).resolve().parent
REFERENCE = {'gold_reference_holder', 'gold_reference_shoulder', 'diffuse_gold_reference_face'}
CAP_FLOOR = np.array([8.7, 8.3, .850001])
CARRY_STEP_M = .40


def translation(point):
    matrix = np.eye(4)
    matrix[:3, 3] = point
    return matrix


def targets(lift, setup, clearance_height=.0):
    first, last = lift['path']['knots'][0], lift['path']['knots'][-1]
    root = np.array(lift['path']['root']).reshape(4, 4).T
    shifted = root.copy(); shifted[0, 3] -= CARRY_STEP_M
    asset = ASSETS['pike']
    initial = translation(asset['position_m']) @ np.array(setup['parts']['pike']['gold_reference_holder']['matrix']) @ np.array(asset['normalization_matrix'])
    support = np.eye(4); support[:3, :3] = Rotation.from_euler('x', np.pi).as_matrix()
    support[:3, 3] = CAP_FLOOR + [0, 0, .024] - support[:3, :3] @ [.145, -.06, .031]
    delta = support @ np.linalg.inv(initial)
    assert np.max(np.abs(delta[:3, :3] - np.eye(3))) < 1e-10
    final = delta[:3, 3]
    rows = []

    def segment(name, a, b, base_a, base_b, grip_a=1., grip_b=1., count=30):
        for fraction in np.linspace(0, 1, count + 1):
            base = base_a.copy(); base[:3, 3] = base_a[:3, 3] * (1 - fraction) + base_b[:3, 3] * fraction
            rows.append(dict(stage=name, offset=(np.array(a)*(1-fraction)+np.array(b)*fraction).tolist(),
                             root=base.tolist(), closed=float(grip_a*(1-fraction)+grip_b*fraction)))

    # The already screened initial 30 mm lift supplies a continuous IK seed
    # for the downward open-hand approach. Finger closure is checked explicitly.
    segment('lower_open_hand', [0, 0, .03], [0, 0, 0], root, root, 0, 0)
    segment('close_reference_grip', [0, 0, 0], [0, 0, 0], root, root, 0, 1)
    for knot in lift['path']['knots']:
        rows.append(dict(stage='lift_reference', offset=knot['offset'], root=root.tolist(), closed=1., seed=knot['q']))
    carried = np.array(last['offset']) + [-CARRY_STEP_M, 0, 0]
    segment('proposed_carrying_step', last['offset'], carried, root, shifted, count=60)
    lowered = carried.copy(); lowered[2] = clearance_height
    segment('lower_in_front_of_housing', carried, lowered, shifted, shifted)
    outside_corner = lowered.copy(); outside_corner[0] = final[0]
    above_cap = final.copy(); above_cap[2] = lowered[2]
    segment('clear_housing_corner', lowered, outside_corner, shifted, shifted)
    segment('above_protective_cap', outside_corner, above_cap, shifted, shifted)
    segment('seat_reference_in_cap', above_cap, final, shifted, shifted, count=60)
    segment('release_reference', final, final, shifted, shifted, 1, 0)
    segment('withdraw_open_hand', final, final + [0, -.10, .08], shifted, shifted, 0, 0)
    return rows, final


def solve(rows, lift):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell', args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page()
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
        out = page.evaluate('''async ({rows,lift})=>{
          const {HandIK}=await import('./hand_ik.js'),T=await import('three');
          const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json();
          const setup=await(await fetch('./optical_setup.json')).json();
          const kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
          kin.joints.find(j=>j.name==='left_shoulder_roll_joint').limits.lower=.025;
          const ik=new HandIK(kin),q={...lift.path.knots[8].q};
          const palm=new T.Matrix4().fromArray(lift.grasp.palm_matrix.flat()).transpose();
          for(const row of rows){
            const root=new T.Matrix4().fromArray(row.root.flat()).transpose();
            const point=setup.ports.ftir_sample.position_m.map((x,k)=>x+row.offset[k]);
            const target=new T.Matrix4().makeTranslation(...point).multiply(palm).premultiply(root.clone().invert());
            if(row.seed)Object.assign(q,row.seed);
            const solved=ik.iterate(q,'left',new T.Vector3().setFromMatrixPosition(target),target,150);
            for(const [name,value] of Object.entries(lift.grasp.q)){
              const opened=name==='left_index_1_joint'?.4:name==='left_thumb_2_joint'?.10:value;
              q[name]=opened+(value-opened)*row.closed;
            }
            row.q={...q};row.error=solved.error;row.rotationError=solved.rotationError;
          }return rows;
        }''', dict(rows=rows, lift=lift))
        browser.close()
    return out


def geometry(setup, cap_floor=CAP_FLOOR):
    obstacles = trimesh.collision.CollisionManager()
    reference = trimesh.collision.CollisionManager(); reference_rest = {}
    cover = json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
    pivot = np.array(cover['interfaces'][4]['pivot_m']) + np.array(ASSETS['nicolet']['normalization_matrix'])[:3, 3]
    opening = np.eye(4); opening[:3, :3] = Rotation.from_euler('x', -65, degrees=True).as_matrix()
    opening[:3, 3] = pivot - opening[:3, :3] @ pivot
    for identity, asset in ASSETS.items():
        if identity == 'g1' or (identity not in ['nicolet', 'pike'] and np.linalg.norm(np.array(asset['position_m'])[:2] - [9.2, 8.3]) > 1.6): continue
        source = trimesh.load(ROOT/asset['geometry'], force='scene', process=False)
        for name in source.graph.nodes_geometry:
            if identity == 'pike' and name == 'reference_protective_cap': continue
            local, key = source.graph[name]
            if name in setup['parts'].get(identity, {}): local = np.array(setup['parts'][identity][name]['matrix']) @ local
            if identity == 'nicolet' and name in cover['cover_parts']: local = opening @ local
            world = translation(asset['position_m']) @ local; label = identity+'::'+name
            if identity == 'pike' and name in REFERENCE:
                reference.add_object(label, source.geometry[key], world); reference_rest[label] = world
            else: obstacles.add_object(label, source.geometry[key], world)
    arch = trimesh.load(ROOT/MANIFEST['architecture']['path'], force='scene', process=False)
    for name in arch.graph.nodes_geometry:
        if 'ftir_bench' not in name: continue
        local, key = arch.graph[name]; obstacles.add_object('room::'+name, arch.geometry[key], local)
    plate = setup['mount_plate']
    obstacles.add_object(plate['id'], trimesh.Trimesh(vertices=plate['vertices'], faces=plate['faces'], process=False))
    obstacles.add_object('inferred_reference_cap', cap_mesh(), translation(cap_floor))
    return obstacles, reference, reference_rest


def review(rows, setup, final, cap_floor=CAP_FLOOR):
    obstacles, reference, rest = geometry(setup, cap_floor)
    meshes = {n:m for n,m in robot_meshes().items() if 'ankle' not in n}
    robot = trimesh.collision.CollisionManager()
    for name, mesh in meshes.items(): robot.add_object(name, mesh)
    graph = defaultdict(list)
    for j in KIN['joints']:
        w=int(j['type']=='revolute'); graph[j['parent']].append((j['id'],w)); graph[j['id']].append((j['parent'],w))
    adjacent=set()
    for link in meshes:
        stack=[(link,None,0)]
        while stack:
            name,parent,d=stack.pop()
            if d>1:continue
            if name in meshes:adjacent.add(tuple(sorted((link,name))))
            stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)
    checks=[]
    for i,row in enumerate(rows):
        base=np.array(row['root']); world=fk(row['q'])
        for name in meshes: robot.set_transform(name,base@world[name])
        if row['stage'] in ['lower_open_hand','close_reference_grip']: offset=np.zeros(3)
        elif row['stage'] in ['release_reference','withdraw_open_hand']: offset=final
        else: offset=row['offset']
        row['reference_offset']=np.asarray(offset).tolist()
        for name,pose in rest.items(): reference.set_transform(name,translation(offset)@pose)
        _,pairs=robot.in_collision_internal(return_names=True)
        own=sorted(p for p in pairs if tuple(sorted(p)) not in adjacent)
        _,environment=robot.in_collision_other(obstacles,return_names=True)
        _,grasp=robot.in_collision_other(reference,return_names=True)
        _,payload,contacts=reference.in_collision_other(obstacles,return_names=True,return_data=True)
        unexpected=[];support=[]
        for a,b in payload:
            selected=[c for c in contacts if c.names=={a,b}]
            depth=max((float(c.depth) for c in selected),default=float('inf'))
            if a=='pike::gold_reference_holder' and b=='inferred_reference_cap' and depth<1e-6 and np.linalg.norm(np.array(offset)-final)<1e-8:
                support.append(dict(pair=[a,b],depth_m=depth))
            else:unexpected.append([a,b])
        checks.append(dict(index=i,stage=row['stage'],self_intersections=own,environment=sorted(environment),reference_hand=sorted(grasp),reference_environment=unexpected,intended_nonoptical_support=support))
        if i%100==0:print('storage_checked',i,flush=True)
    return checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--clearance-height',type=float,default=0.);parser.add_argument('--solve-only',action='store_true');parser.add_argument('--solved-output');args=parser.parse_args()
    files=['reference_lift_path.json','optical_setup.json','motion_poses.json','hand_ik.js','build_reference_cap_candidate.py','plan_reference_storage.py']
    pins={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files}
    lift=json.loads((HERE/'reference_lift_path.json').read_text()); setup=json.loads((HERE/'optical_setup.json').read_text())
    rows,final=targets(lift,setup,args.clearance_height); rows=solve(rows,lift)
    if args.solved_output:
        Path(args.solved_output).write_text(json.dumps(dict(source_sha256=pins,cap_floor_m=CAP_FLOOR.tolist(),rows=rows,final_offset=final.tolist()),indent=2)+'\n')
    if args.solve_only:
        for stage in dict.fromkeys(r['stage'] for r in rows):
            selected=[r for r in rows if r['stage']==stage]
            print(stage,len(selected),max(r['error'] for r in selected),max(r['rotationError'] for r in selected),flush=True)
        return
    checks=review(rows,setup,final)
    failures={name:sum(bool(c[name]) for c in checks) for name in ['self_intersections','environment','reference_hand','reference_environment']}
    assert all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha for n,sha in pins.items()),'Source changed during planning'
    result=dict(scope=__doc__,source_sha256=pins,clearance_height_m=args.clearance_height,cap_floor_m=CAP_FLOOR.tolist(),reference_storage_offset_m=final.tolist(),rows=rows,checks=checks,
                summary=dict(samples=len(rows),maximum_position_error_m=max(r['error'] for r in rows),maximum_rotation_error_rad=max(r['rotationError'] for r in rows),collision_counts=failures),
                passed=not any(failures.values()) and all(r['error']<.003 and r['rotationError']<.02 for r in rows))
    out=HERE/'previews/reference_storage_path.json'
    if out.exists(): out.rename(out.with_name('reference_storage_path_'+hashlib.sha256(out.read_bytes()).hexdigest()[:12]+'.json'))
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],**result['summary'])),flush=True)


if __name__=='__main__': main()
