"""Screen continuous left-arm reference lifts against source geometry.

This planner begins at an already closed grasp. It does not qualify approach,
closure, forces, reference storage, or the full optical procedure. The planning
region is the FTIR bench, Nicolet housing and PIKE accessory. Ankle meshes are
omitted here and must be included by the independent whole-scene reviewer.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from playwright.sync_api import sync_playwright
from scipy.spatial.transform import Rotation

from source_geometry import ROOT, ASSETS, MANIFEST, KIN, fk, robot_meshes

HERE = Path(__file__).resolve().parent
REFERENCE = {'gold_reference_holder', 'gold_reference_shoulder', 'diffuse_gold_reference_face'}


def solve_paths(stances, profiles):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path='/tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell',
            args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page()
        page.goto('http://localhost:8769/viewer/cooling_concept_v2/index.html?clean')
        result = page.evaluate('''async ({stances,profiles})=>{
          const {HandIK}=await import('./hand_ik.js'),T=await import('three');
          const m=await(await fetch('../../assets/cooling_lab_v1/scene.json')).json();
          const poses=await(await fetch('./motion_poses.json')).json();
          const setup=await(await fetch('./optical_setup.json')).json();
          const kin=m.inspection_states.find(s=>s.id==='g1_hands_inspection').kinematics;
          kin.joints.find(j=>j.name==='left_shoulder_roll_joint').limits.lower=.025;
          const ik=new HandIK(kin),out=[];
          for(const s of stances){
            const profile=profiles[s.candidate],q={...poses.poses.rest,...poses.poses.stance,...profile.q,waist_pitch_joint:s.waist};
            const world=ik.forward(q).world;let bottom=Infinity;
            for(const [name,vertices]of Object.entries(poses.sole_vertices_m))for(const v of vertices)bottom=Math.min(bottom,new T.Vector3(...v).applyMatrix4(world.get(name)).z);
            const root=new T.Matrix4().makeRotationZ(s.yaw).setPosition(...s.root_position_m,-bottom),inverse=root.clone().invert();
            const palm=new T.Matrix4().fromArray(profile.palm_matrix.flat()).transpose(),knots=[];
            const offsets=[[0,0,0],[0,0,.08],[0,-.1,.15],[.05,-.2,.15]];
            for(let i=0;i<=60;i++){
              const segment=Math.min(2,Math.floor(i/20)),u=(i-segment*20)/20;
              const offset=offsets[segment].map((x,k)=>x+(offsets[segment+1][k]-x)*u);
              const target=new T.Matrix4().makeTranslation(...setup.ports.ftir_sample.position_m.map((x,k)=>x+offset[k])).multiply(palm).premultiply(inverse);
              const point=new T.Vector3().setFromMatrixPosition(target);
              let error,rotationError;
              if(i===0){error=ik.solve(q,'left',point,target);rotationError=ik.lastRotationError;}
              else ({error,rotationError}=ik.iterate(q,'left',point,target));
              knots.push({offset,q:{...q},error,rotationError});
              if(error>.003||rotationError>.02)break;
            }
            out.push({stance:s,root:root.toArray(),knots});
          }return out;
        }''', dict(stances=stances, profiles=profiles))
        browser.close()
    return result


def main():
    files = ['previews/optical_reference_left_stance.json', 'previews/optical_reference_left_search.json',
             'optical_setup.json', 'motion_poses.json', 'hand_ik.js', 'plan_reference_lift.py']
    pins = {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files}
    stances = json.loads((HERE/files[0]).read_text())['passed']
    profiles = json.loads((HERE/files[1]).read_text())['candidates']
    paths = solve_paths(stances, profiles)
    setup = json.loads((HERE/'optical_setup.json').read_text())
    obstacles = trimesh.collision.CollisionManager()
    reference = trimesh.collision.CollisionManager()
    reference_rest = {}
    for identity in ['nicolet', 'pike']:
        asset = ASSETS[identity]
        source = trimesh.load(ROOT/asset['geometry'], force='scene', process=False)
        base = np.eye(4);base[:3,3] = asset['position_m']
        cover = json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
        pivot = np.array(cover['interfaces'][4]['pivot_m'])+np.array(ASSETS['nicolet']['normalization_matrix'])[:3,3]
        opening = np.eye(4);opening[:3,:3] = Rotation.from_euler('x', -65, degrees=True).as_matrix()
        opening[:3,3] = pivot-opening[:3,:3]@pivot
        for name in source.graph.nodes_geometry:
            local,key = source.graph[name]
            if name in setup['parts'].get(identity, {}):local = np.array(setup['parts'][identity][name]['matrix'])@local
            if identity=='nicolet' and name in cover['cover_parts']:local = opening@local
            transform = base@local
            label = identity+'::'+name
            if identity=='pike' and name in REFERENCE:
                reference.add_object(label, source.geometry[key], transform);reference_rest[label] = transform
            else:obstacles.add_object(label, source.geometry[key], transform)
    arch = trimesh.load(ROOT/MANIFEST['architecture']['path'], force='scene', process=False)
    for name in arch.graph.nodes_geometry:
        if 'ftir_bench' in name:
            transform,key = arch.graph[name];obstacles.add_object('room::'+name, arch.geometry[key], transform)
    plate = setup['mount_plate']
    obstacles.add_object(plate['id'], trimesh.Trimesh(vertices=plate['vertices'],faces=plate['faces'],process=False))
    robot = trimesh.collision.CollisionManager()
    meshes = {n:m for n,m in robot_meshes().items() if 'ankle' not in n}
    for name,mesh in meshes.items():robot.add_object(name,mesh)
    graph = defaultdict(list)
    for j in KIN['joints']:
        weight = int(j['type']=='revolute');graph[j['parent']].append((j['id'],weight));graph[j['id']].append((j['parent'],weight))
    adjacent = set()
    for link in meshes:
        stack = [(link,None,0)]
        while stack:
            name,parent,d = stack.pop()
            if d>1:continue
            if name in meshes:adjacent.add(tuple(sorted((link,name))))
            stack.extend((child,name,d+w) for child,w in graph[name] if child!=parent)
    for path in paths:
        base = np.array(path['root']).reshape(4,4).T
        checks = []
        for index,knot in enumerate(path['knots']):
            world = fk(knot['q'])
            for name in meshes:robot.set_transform(name,base@world[name])
            for name,rest in reference_rest.items():
                transform = rest.copy();transform[:3,3] += knot['offset'];reference.set_transform(name,transform)
            _,pairs = robot.in_collision_internal(return_names=True)
            own = sorted(p for p in pairs if tuple(sorted(p)) not in adjacent)
            _,environment = robot.in_collision_other(obstacles,return_names=True)
            _,grasp = robot.in_collision_other(reference,return_names=True)
            _,payload = reference.in_collision_other(obstacles,return_names=True)
            checks.append(dict(index=index,self_intersections=own,environment=sorted(environment),
                               reference_hand=sorted(grasp),reference_environment=sorted(payload)))
        path['checks'] = checks
        # Initial optical-face/port edge contact is retained and rejects a route;
        # it must be repaired in the source asset instead of waived by a planner.
        path['passed'] = len(path['knots'])==61 and all(
            k['error']<=.003 and k['rotationError']<=.02 for k in path['knots']) and all(
            not any(c[n] for n in ['self_intersections','environment','reference_hand','reference_environment']) for c in checks)
    report = dict(scope=__doc__,source_sha256=pins,candidates=paths,passed=sum(p['passed'] for p in paths))
    (HERE/'previews/reference_lift_paths.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(paths),passed=report['passed'],
                         summary=[dict(stance=p['stance'],knots=len(p['knots']),
                                       rejection_counts={n:sum(bool(c[n]) for c in p['checks']) for n in ['self_intersections','environment','reference_hand','reference_environment']}) for p in paths])),flush=True)


if __name__=='__main__':main()
