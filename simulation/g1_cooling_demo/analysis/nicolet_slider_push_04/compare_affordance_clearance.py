"""Compare source index-link clearance for previously reachable local grips.

Only object-local hand poses are exported. Earlier hypothetical reach is a
candidate filter, never an arm trajectory or proof of current-state reach.
"""
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];ROOT=BASE.parents[1]
sys.path.insert(0,str(BASE))
from robot_source_meshes import robot_source_meshes
from ftir_hand import mimic


def main():
    output=HERE/'affordance_clearance.json';prior_out=HERE/'clearance_ranked_prior.json'
    if output.exists() or prior_out.exists():raise FileExistsError('Use a new diagnostic output')
    parent=ROOT/'assets/nicolet_6700_mechanism_v1/slider_push_prior.json'
    fit_path=HERE.parent/'nicolet_slider_push_02/review.json'
    reach_path=HERE.parent/'nicolet_slider_push_02/joint_entry.json'
    prior=json.loads(parent.read_text());fits=json.loads(fit_path.read_text())
    reach=json.loads(reach_path.read_text())
    ids=sorted({r['candidate'] for r in reach['rows'] if r.get('endpoint_passed')}|{238})
    shape=ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/geometry/nicolet_passive_dynamics.glb'
    scene=trimesh.load(shape,force='scene',process=False)
    objects={};bounds={}
    for name in ['sample_access_slider_grip','sample_access_sliding_window']:
        T,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(T)
        objects[name]=trimesh.collision.CollisionManager();objects[name].add_object(name,mesh)
        bounds[name]=mesh.bounds
    offset=bounds['sample_access_slider_grip'].mean(0)-np.array(fits['grip_bounds_port_frame_m']).mean(0)
    model_path=BASE/'runs/ftir_slider_scan_02/controller_model/world.xml'
    m=mujoco.MjModel.from_xml_path(str(model_path));d=mujoco.MjData(m)
    source=robot_source_meshes(m);index=trimesh.collision.CollisionManager()
    index.add_object('right_index_2',source['right_index_2'])
    rows=[];export=[]
    for ident in ids:
        fit=fits['candidates'][ident]
        if not fit['passed_distal_path']:raise ValueError('Candidate is not a locally clear hand path')
        d.qpos[:]=m.qpos0
        for name,value in fit['q'].items():
            joint=m.joint(name)
            if m.jnt_limited[joint.id] and not m.jnt_range[joint.id,0]<=value<=m.jnt_range[joint.id,1]:
                raise ValueError('Finger value outside source range')
            d.joint(name).qpos[0]=value
        mimic(m,d);mujoco.mj_kinematics(m,d)
        wrist=d.site('right_wrist_reference');W=np.eye(4);W[:3,:3]=wrist.xmat.reshape(3,3);W[:3,3]=wrist.xpos
        link=d.body('right_index_2');L=np.eye(4);L[:3,:3]=link.xmat.reshape(3,3);L[:3,3]=link.xpos
        palm=np.array(fit['palm_in_port_frame']);palm[:3,3]+=offset
        index.set_transform('right_index_2',palm@np.linalg.inv(W)@L)
        distances={name:float(index.min_distance_other(obj)) for name,obj in objects.items()}
        intersects={name:bool(index.in_collision_other(obj)) for name,obj in objects.items()}
        rows.append(dict(candidate=ident,index_joint_rad=fit['q']['right_index_1_joint'],
                         tilt_rad=fit['tilt_rad'],roll_rad=fit['roll_rad'],
                         index_link_source_distance_m=distances,index_link_source_intersections=intersects))
        export.append(dict(id=ident,hand_q=fit['q'],palm_in_device=palm.tolist(),
            outward_surface_normal=fit['outward_surface_normal'],source_pad=fit['source_pad'],
            surface_m=(np.array(fit['surface_in_port_frame'])+offset).tolist(),pad_gap_m=fit['pad_gap_m']))
    scores={r['candidate']:min(r['index_link_source_distance_m'].values()) for r in rows}
    export.sort(key=lambda r:(-scores[r['id']],r['id']))
    prior['candidates']=export
    prior['scope']='Development prior ranked by source index-link clearance. Object-local hand poses only; current-state arm paths and physical robustness must be verified separately.'
    prior_out.write_text(json.dumps(prior,indent=2)+'\n')
    deps=[Path(__file__),BASE/'robot_source_meshes.py',BASE/'ftir_hand.py',parent,fit_path,reach_path,shape,model_path,prior_out]
    report=dict(rows=rows,ranked_candidate_ids=[r['id'] for r in export],
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        shape_changed=False,current_state_whole_arm_reach_checked=False,physical_execution=False,
        scope=__doc__)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(candidates=len(rows),best=[next(r for r in rows if r['candidate']==c['id']) for c in export[:5]],
                         current=next(r for r in rows if r['candidate']==238))),flush=True)


if __name__=='__main__':main()
