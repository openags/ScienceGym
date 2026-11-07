"""Use ordinary tweezers or long forceps to reach the Cary spring-clamp arm.

The reference remains held by the left hand before the clamp withdraws. The
right hand uses a fitted tool grip outside the tight port space. This search
checks source geometry only, not tool strength or friction.
"""
import argparse
import hashlib
import itertools
import json
import time
import fcl
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene, CANDIDATE
from cary_clamp import moving_transform
from optical_choreography import HERE
from source_geometry import ROOT, ASSETS, hand_manager, set_hand
from tweezers_geometry import meshes
from fit_specimen_tool import profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', default='01')
    parser.add_argument('--lid', type=float, default=.20)
    parser.add_argument('--angle', type=float, default=55.)
    parser.add_argument('--degrees', nargs='+', type=float, default=[100, 110, 120, 130, 140])
    parser.add_argument('--tool-grip-id', type=int)
    parser.add_argument('--reference-grasps', default='previews/cary_reference_hand_02.json')
    parser.add_argument('--long-forceps', action='store_true')
    parser.add_argument('--long-grips', default='previews/long_forceps_grips_02/grasps.json')
    parser.add_argument('--max-candidates', type=int, default=12)
    args = parser.parse_args()
    out = HERE/'previews'/f'cary_clamp_tool_{args.trial}'
    out.mkdir(exist_ok=False)
    pinned = {}
    for name in ['fit_cary_clamp_tool.py', 'cary_clamp_scene.py', 'cary_clamp.py',
                 'source_geometry.py', 'cary_access_scene.py', 'tweezers_geometry.py',
                 'fit_specimen_tool.py', 'previews/tweezers_closure.json',
                 args.reference_grasps]+(['previews/cary_tool_grips_01.json'] if args.tool_grip_id is not None else [])+(['long_forceps.py',args.long_grips] if args.long_forceps else []):
        data = (HERE/name).read_bytes()
        path = out/'source'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        pinned[name] = hashlib.sha256(data).hexdigest()
    start = time.monotonic()
    scene = CaryClampScene(local_only=True)
    cover_path = HERE/'previews/cary_cover_carry_03.json'
    cover = json.loads(cover_path.read_text())['rows'][-1]['cover_matrix']
    scene.set_access(lid=args.lid, cover=cover)
    left_source = json.loads((HERE/args.reference_grasps).read_text())
    left = hand_manager('left')
    right = hand_manager('right')
    grip = json.loads((HERE/'previews/tweezers_closure.json').read_text())
    tool_T_palm = np.array(grip['palm_matrix'])
    right_q = profile(1., grip)
    if args.tool_grip_id is not None:
        choices = json.loads((HERE/'previews/cary_tool_grips_01.json').read_text())['candidates']
        selected = next(c for c in choices if c['source_candidate']==args.tool_grip_id)
        assert selected['accepted']
        tool_T_palm = np.array(selected['palm_matrix'])
        right_q = selected['q']
    profiles=[(args.tool_grip_id,dict(q=right_q,palm_matrix=tool_T_palm.tolist()))]
    model_name='ideal_tek_aa'
    tip=np.array([-.06499999761581421,0.,.00575])
    tip_names=['ptfe_spring_arm_-1','ptfe_spring_arm_1']
    tool_meshes=meshes(1.)
    if args.long_forceps:
        from long_forceps import meshes as long_meshes,TIP
        profiles=list(enumerate(json.loads((HERE/args.long_grips).read_text())['candidates']))
        model_name='fst_11000_20';tip=TIP+np.array([.0015,0.,0.]);tip_names=['serrated_arm_-1','serrated_arm_1'];tool_meshes=long_meshes(1.)
    tool = trimesh.collision.CollisionManager()
    for name, mesh in tool_meshes.items():
        tool.add_object(name, mesh)
    reference_candidates = left_source['candidates']
    initial_clamp = scene.raw_to_world @ moving_transform(.014)
    inverse_initial = np.linalg.inv(initial_clamp)
    candidates, failures = [], []
    initial_rejections = dict(tool_collision=0, hand_collision=0, contact_gap=0, no_reference_pair=0)
    obstacles = scene.obstacles
    tested = 0
    for (grip_index,tool_grip),degrees, sign, x, z in itertools.product(profiles,args.degrees, [-1, 1],
                                                [.010, .015, .020, .025, .030], [.0855, .0865, .087]):
        tool_T_palm=np.array(tool_grip['palm_matrix']);right_q=tool_grip['q']
        angle = np.deg2rad(degrees)
        axis = np.array([np.cos(angle), 0., np.sin(angle)])
        normal = np.array([0., sign, 0.])
        local = np.eye(4)
        local[:3, :3] = np.column_stack([axis, normal, np.cross(axis, normal)])
        local[:3, 3] = np.array([x, -.127, z])-local[:3, :3]@tip
        tool_initial = initial_clamp @ local
        scene.set_clamp(.014)
        for name in tool._objs:
            tool.set_transform(name, tool_initial)
        set_hand(right, 'right', right_q, tool_initial @ tool_T_palm)
        tested += 1
        if tool.in_collision_other(obstacles):
            initial_rejections['tool_collision'] += 1
            continue
        if right.in_collision_other(obstacles):
            initial_rejections['hand_collision'] += 1
            continue
        target = obstacles._objs['dra::sample_clamp_arm']['obj']
        distances = []
        for name in tip_names:
            d = fcl.DistanceResult()
            fcl.distance(tool._objs[name]['obj'], target, fcl.DistanceRequest(), d)
            distances.append(float(d.min_distance))
        if max(distances) > .00025:
            initial_rejections['contact_gap'] += 1
            continue
        pairs = []
        for i, c in enumerate(reference_candidates):
            if not c.get('accepted_clearance', True):
                continue
            set_hand(left, 'left', c['q'], np.array(c['palm_matrix']))
            if not left.in_collision_other(obstacles) and not left.in_collision_other(right) and not left.in_collision_other(tool):
                pairs.append(i)
        if not pairs:
            initial_rejections['no_reference_pair'] += 1
            continue
        rows = []
        path = [('pull', float(g), 0.) for g in np.linspace(.014, .027, 14)]
        path += [('rotate', .027, float(a)) for a in np.linspace(0, np.deg2rad(args.angle), 29)]
        path_ok = True
        for phase, gap, rotation in path:
            scene.set_clamp(gap, rotation)
            delta = scene.raw_to_world @ moving_transform(gap, rotation) @ inverse_initial
            world = delta @ tool_initial
            for name in tool._objs:
                tool.set_transform(name, world)
            palm = world @ tool_T_palm
            set_hand(right, 'right', right_q, palm)
            failure = {}
            for label, manager in [('tool', tool), ('right_hand', right)]:
                hit, contacts = manager.in_collision_other(obstacles, return_names=True)
                if hit:
                    failure[label] = sorted([sorted(p) for p in contacts])
            if failure:
                failures.append(dict(degrees=degrees, sign=sign, x=x, z=z,
                    phase=phase, gap_m=gap, angle_rad=rotation, failure=failure))
                path_ok = False
                break
            retained = []
            for i in pairs:
                c = reference_candidates[i]
                set_hand(left, 'left', c['q'], np.array(c['palm_matrix']))
                if not left.in_collision_other(obstacles) and not left.in_collision_other(tool) and not left.in_collision_other(right):
                    retained.append(i)
            pairs = retained
            if not pairs:
                path_ok = False
                break
            rows.append(dict(phase=phase, gap_m=gap, angle_rad=rotation,
                tool_matrix=world.tolist(), right_palm=palm.tolist()))
        if path_ok:
            candidates.append(dict(degrees=degrees, sign=sign, pinch_x_m=x, pinch_z_m=z,
                tool_grip_index=grip_index,
                tip_clearances_m=distances, reference_candidates=pairs, right_q=right_q,
                tool_T_palm=tool_T_palm.tolist(),
                tool_initial=tool_initial.tolist(), rows=rows))
            print('candidate', len(candidates), 'tool angle', degrees, 'reference choices', pairs, flush=True)
            if len(candidates)>=args.max_candidates:break
    report = dict(scope=__doc__, tested=tested, candidates=candidates, rejected_paths=failures,
        initial_rejections=initial_rejections, degrees=args.degrees,
        tool_grip_source_candidate=args.tool_grip_id, reference_grasps=args.reference_grasps,
        tool_model=model_name,long_grips=args.long_grips if args.long_forceps else None,
        lid_opening_m=args.lid, parked_angle_rad=float(np.deg2rad(args.angle)),
        source_sha256=pinned, seconds=time.monotonic()-start,
        geometry_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                        for p in [CANDIDATE, scene.cary_geometry, ASSETS['g1']['geometry'],
                                  ASSETS['tweezers_white']['geometry']]+(['assets/fst_11000_20_v1/clamp_grip.glb'] if args.long_forceps else [])},
        cover_source_sha256=hashlib.sha256(cover_path.read_bytes()).hexdigest(),
        limitations=['No whole-body reach or approach/closure path yet.',
                     'Reference finger fits and tool actuation/retention forces remain unqualified.',
                     'The 55 degree parking angle is an inferred selection, not manufacturer travel.'])
    (out/'search.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(tested=tested, candidates=len(candidates), rejected_paths=len(failures),
                         seconds=report['seconds'])), flush=True)


if __name__ == '__main__':
    main()
