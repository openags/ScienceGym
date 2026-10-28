"""Test gold-reference access through the existing open Nicolet sliding window.

The installed IntegratIR and reference meshes are unchanged. This adds the
selected source Inspire hand and terminal wrist housing with the existing
authored reference grip. It excludes upstream arm, physics and grip quality.
Cover installation remains in scope.
"""
import hashlib
import json
from pathlib import Path
import time
import sys

import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
VIEW=ROOT/'viewer/cooling_concept_v2'
sys.path.insert(0,str(VIEW))
from cary_distal_hand import distal_hand_manager
from source_geometry import set_hand
REFERENCE={'gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face'}


def translation(point):
    T=np.eye(4);T[:3,3]=point;return T


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    started=time.monotonic()
    runtime=json.loads((VIEW/'runtime_scene.json').read_text());assets={a['id']:a for a in runtime['assets']}
    setup=json.loads((VIEW/'optical_setup.json').read_text())
    grasp_path=VIEW/'reference_transfer.json';grasp=json.loads(grasp_path.read_text())
    hand=distal_hand_manager('left');palm_from_port=np.linalg.inv(np.array(grasp['reference_in_palm']))
    revision=json.loads((ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json').read_text())
    interface=json.loads((ROOT/'assets/pike_integratir_dtgs_v1/interfaces.json').read_text())
    moving=set(next(x for x in json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())['interfaces'] if x['id']=='sample_access_slider')['parts'])
    env=trimesh.collision.CollisionManager();reference=trimesh.collision.CollisionManager();rest={};source_paths=[]
    reference_vertices=[]
    for identity in ['nicolet','pike']:
        asset=assets[identity];path=ROOT/(revision['geometry_override']['path'] if identity=='nicolet' else asset['geometry']);source_paths.append(path)
        scene=trimesh.load(path,force='scene',process=False)
        for name in scene.graph.nodes_geometry:
            if identity=='pike' and name not in set(interface['module_parts'])|REFERENCE:continue
            T,key=scene.graph[name];override=setup['parts'].get(identity,{}).get(name)
            if override:T=np.asarray(override['matrix'])@T
            T=translation(asset['position_m'])@T
            if identity=='nicolet' and name in moving:T=translation([0,.104,0])@T
            mesh=scene.geometry[key]
            if identity=='pike' and name in REFERENCE:
                rest[name]=T;reference.add_object(name,mesh,T)
                reference_vertices.append(trimesh.transform_points(mesh.vertices,T))
            else:env.add_object(identity+'::'+name,mesh,T)
    rows=[]
    for label,front_offset in [('straight_descent',0.),('front_entry_then_under_cover',-.035)]:
        waypoints=[(0.,front_offset,.180),(0.,front_offset,.030),(0.,0.,.030),(0.,0.,0.)]
        failures=[];supports=[];states=0;hand_failures=[]
        for phase,(a,b) in enumerate(zip(waypoints[:-1],waypoints[1:])):
            for u in np.linspace(0,1,61):
                delta=(1-u)*np.array(a)+u*np.array(b)
                for name,T in rest.items():reference.set_transform(name,translation(delta)@T)
                palm=translation(np.array(setup['ports']['ftir_sample']['position_m'])+delta)@palm_from_port
                set_hand(hand,'left',grasp['grasp']['q'],palm)
                _,hand_pairs=hand.in_collision_other(env,return_names=True)
                if hand_pairs:hand_failures.append(dict(phase=phase,fraction=float(u),offset_m=delta.tolist(),pairs=[list(p) for p in sorted(hand_pairs)]))
                _,pairs,contacts=reference.in_collision_other(env,return_names=True,return_data=True)
                allowed=[];bad=[]
                for pair in sorted(pairs):
                    matching=[c for c in contacts if set(c.names)==set(pair)]
                    depth=max((float(c.depth) for c in matching),default=0.)
                    row=dict(parts=list(pair),maximum_reported_triangle_depth_m=depth)
                    support=(set(pair)=={'gold_reference_shoulder','pike::top_sample_panel'}
                             and phase==2 and u==1. and depth<=1e-6)
                    (allowed if support else bad).append(row)
                if bad:failures.append(dict(phase=phase,fraction=float(u),offset_m=delta.tolist(),contacts=bad))
                if allowed:supports.append(dict(phase=phase,fraction=float(u),contacts=allowed))
                states+=1
        rows.append(dict(variant=label,waypoint_offsets_m=waypoints,states=states,
                         object_clearance_passed=not failures,failures=failures,intended_final_support=supports,
                         distal_hand_clearance_passed=not hand_failures,hand_failures=hand_failures))
        print(label,'failed object',len(failures),'failed hand',len(hand_failures),'of',states,flush=True)
    vertices=np.vstack(reference_vertices)
    report=dict(scope=__doc__,rows=rows,reference_at_port_bounds_m=[vertices.min(0).tolist(),vertices.max(0).tolist()],
                installed_sample_port_world_m=setup['ports']['ftir_sample']['position_m'],
                cover_angle_rad=0.,slider_travel_m=.104,slider_dimensions_inferred=True,
                source_hashes={str(p.relative_to(ROOT)):digest(p) for p in source_paths+[VIEW/'runtime_scene.json',VIEW/'optical_setup.json',grasp_path,VIEW/'source_geometry.py',VIEW/'cary_distal_hand.py',ROOT/'assets/cooling_lab_v1/scene.json']},
                builder_sha256=digest(__file__),seconds=time.monotonic()-started,
                robot_and_hand_clearance_checked=False,distal_hand_checked=True,grasp_physics_validated=False,physics_qualified=False,
                manufacturer_accessory_configuration_verified=False)
    (HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
