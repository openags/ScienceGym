"""Extract the supported reference while the other hand holds the clamp clear.

The selected input supplies clamp travel, rotation and the right tool pose.
The left hand clears the optical face, optionally moves the reference laterally
out of the pad's projection, then withdraws it. A zero lateral distance uses
the straight corridor available after the clamp has been parked. This is a
geometric candidate; hand approaches, whole-body reach and forces are separate.
"""
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
import trimesh
from cary_clamp_scene import CaryClampScene,CANDIDATE
from cary_access_scene import translation
from optical_choreography import HERE
from source_geometry import ROOT,robot_meshes,set_hand
from cary_distal_hand import distal_hand_manager
from long_forceps import meshes


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trial',default='01')
    parser.add_argument('--clamp',default='previews/cary_clamp_tool_05/search.json')
    parser.add_argument('--max-candidates',type=int,default=12)
    parser.add_argument('--max-per-pair',type=int,default=0)
    parser.add_argument('--clamp-indices',nargs='+',type=int)
    parser.add_argument('--reference-indices',nargs='+',type=int)
    parser.add_argument('--distances',nargs='+',type=float,default=[.040,.055,.070])
    args=parser.parse_args()
    out=HERE/'previews'/('cary_reference_extraction_'+args.trial);out.mkdir(exist_ok=False)
    clamp=json.loads((HERE/args.clamp).read_text())
    reference_file=clamp['reference_grasps'];reference=json.loads((HERE/reference_file).read_text())
    inputs=['plan_cary_reference_extraction.py','cary_clamp_scene.py','cary_clamp.py',
        'cary_access_scene.py','cary_distal_hand.py','source_geometry.py','long_forceps.py',args.clamp,
        reference_file,'previews/cary_cover_carry_03.json']
    pins={}
    for name in inputs:
        data=(HERE/name).read_bytes();dest=out/'source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        pins[name]=hashlib.sha256(data).hexdigest()
    scene=CaryClampScene(local_only=True)
    cover=json.loads((HERE/inputs[-1]).read_text())['rows'][-1]['cover_matrix']
    scene.set_access(lid=clamp['lid_opening_m'],cover=cover)
    body=robot_meshes();left=distal_hand_manager('left',body);right=distal_hand_manager('right',body)
    tool=trimesh.collision.CollisionManager()
    for name,mesh in meshes(1.).items():tool.add_object(name,mesh)
    tested=0;failures=[];accepted=[];pair_counts={};started=time.monotonic()
    for ci,c in enumerate(clamp['candidates']):
        if args.clamp_indices is not None and ci not in args.clamp_indices:continue
        last=c['rows'][-1];scene.set_clamp(last['gap_m'],last['angle_rad'])
        set_hand(right,'right',c['right_q'],np.array(last['right_palm']))
        for n in tool._objs:tool.set_transform(n,np.array(last['tool_matrix']))
        for ri,angle,distance in itertools.product(c['reference_candidates'],
                [180,135,225,90,270,0,45,315],args.distances):
            if distance==0 and angle!=180:continue
            if args.reference_indices is not None and ri not in args.reference_indices:continue
            if args.max_per_pair and pair_counts.get((ci,ri),0)>=args.max_per_pair:continue
            ref=reference['candidates'][ri];palm=np.array(ref['palm_matrix'])
            side=np.array([np.cos(np.deg2rad(angle)),0,np.sin(np.deg2rad(angle))])*distance
            offset=np.array([0.,-.006,0.]);end=offset+side
            path=[('clear_port_face',np.array([0.,v,0.])) for v in np.linspace(0.,-.006,13)]
            if distance>0:path += [('clear_clamp_pad',offset+side*u) for u in np.linspace(0.,1.,31)[1:]]
            path += [('withdraw_reference',end+np.array([0.,v,0.])) for v in np.linspace(0.,-.07,36)[1:]]
            tested+=1;rows=[];failure={}
            for stage,delta in path:
                pose=translation(delta);scene.set_reference(pose)
                set_hand(left,'left',ref['q'],pose@palm)
                for label,a,b in [('left_environment',left,scene.obstacles),
                                  ('left_right',left,right),('left_tool',left,tool)]:
                    hit,pairs=a.in_collision_other(b,return_names=True)
                    if hit:failure[label]=sorted([sorted(p) for p in pairs])
                collisions=scene.reference_clearance()
                if collisions:failure['reference_environment']=collisions
                if failure:
                    failures.append(dict(clamp_candidate=ci,reference_candidate=ri,
                        angle_deg=angle,distance_m=distance,stage=stage,
                        reference_delta=pose.tolist(),failure=failure))
                    break
                rows.append(dict(stage=stage,reference_delta=pose.tolist(),left_palm=(pose@palm).tolist()))
            if not failure:
                pair_counts[(ci,ri)]=pair_counts.get((ci,ri),0)+1
                accepted.append(dict(clamp_candidate=ci,reference_candidate=ri,
                    angle_deg=angle,distance_m=distance,left_q=ref['q'],rows=rows))
                print('accepted',len(accepted),'clamp',ci,'reference',ri,'direction',angle,'distance',distance,flush=True)
                if len(accepted)>=args.max_candidates:break
        if len(accepted)>=args.max_candidates:break
    report=dict(scope=__doc__,tested=tested,candidates=accepted,rejected_paths=failures,
        source_sha256=pins,clamp_source=args.clamp,reference_source=reference_file,
        lid_opening_m=clamp['lid_opening_m'],cover_matrix=cover,
        geometry_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in [CANDIDATE,scene.cary_geometry]},
        seconds=time.monotonic()-started,maximum_per_pair=args.max_per_pair,
        selected_clamp_indices=args.clamp_indices,selected_reference_indices=args.reference_indices,
        selected_distances_m=args.distances,
        limitations=['Local actual-mesh clearance only, with pre-established grasps.',
                     'No complete humanoid, arm approach, tool closure, retention-force or dynamic qualification.'])
    (out/'search.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=tested,accepted=len(accepted),seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
