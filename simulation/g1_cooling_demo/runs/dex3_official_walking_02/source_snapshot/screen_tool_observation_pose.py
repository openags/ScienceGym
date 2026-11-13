"""Author collision-screened poses that expose the tool to native cameras.

Segmentation is used only by this offline visibility evaluator. It is never
an actor observation. Poses and sampled transitions are design candidates;
no movement, perception accuracy, grasp or branch qualification is claimed.
"""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil

os.environ.setdefault('MUJOCO_GL','egl')
import mujoco
import numpy as np
from PIL import Image
from sensor_rendering import depth_renderer


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source, output):
    source, output=Path(source).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,output/Path(__file__).name)
    shutil.copyfile(Path(__file__).parent/'sensor_rendering.py',output/'sensor_rendering.py')
    model=mujoco.MjModel.from_xml_path(str(source/'world.xml'));data=mujoco.MjData(model)
    contract=json.loads((source/'contract.json').read_text());initial=np.asarray(contract['initial_qpos'])
    tool={model.body('tweezer').id};robot={model.body('pelvis').id}
    for b in range(model.nbody):
        if model.body_parentid[b] in tool:tool.add(b)
        if model.body_parentid[b] in robot:robot.add(b)
    tool_geoms=np.array([g for g in range(model.ngeom) if int(model.geom_bodyid[g]) in tool])
    names=['right_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
    qa=np.array([model.joint(n).qposadr[0] for n in names])
    renderer=mujoco.Renderer(model,height=480,width=640,max_geom=model.ngeom+1000)
    native_depth=depth_renderer(model,480,640)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.sitegroup[:]=0
    def inspect(q):
        data.qpos[:]=q;mujoco.mj_forward(model,data);bad=[]
        for c in data.contact:
            bs={int(model.geom_bodyid[g]) for g in c.geom}
            if not bs&robot:continue
            gs=[model.geom(int(g)).name for g in c.geom]
            bound=.001 if any('ankle_roll_link_collision' in (n or '') for n in gs) and 'lab_part_1515' in gs else .00002
            if c.dist < -bound:bad.append(dict(parts=gs,penetration_m=-float(c.dist),bound_m=bound))
        return bad
    rows=[];candidates=[]
    poses=[('pregrasp',initial[qa].copy())]+[(f'park_{i}',np.array([p,r,0.,e,0.,0.,0.]))
        for i,(p,r,e) in enumerate(itertools.product([.2,.35],[-.25,-.4,-.6],[1.,1.5]))]
    for label,arm in poses:
        q=initial.copy();q[qa]=arm;bad=inspect(q)
        row=dict(label=label,arm_q=arm.tolist(),excessive_robot_contacts=bad)
        if not bad:
            visible={}
            for camera in ['head_rgb','head_depth']:
                renderer.update_scene(data,camera=camera,scene_option=option)
                renderer.enable_segmentation_rendering();seg=renderer.render().copy();renderer.disable_segmentation_rendering()
                mask=(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))&np.isin(seg[:,:,0],tool_geoms)
                visible[camera]=int(mask.sum())
                # Store the ordinary sensor frame, not the evaluator's mask.
                if camera=='head_rgb':Image.fromarray(renderer.render()).save(output/(label+'_rgb.png'))
                else:
                    native_depth.update_scene(data,camera=camera,scene_option=option)
                    depth=native_depth.render().copy()
                    np.save(output/(label+'_depth.npy'),depth)
            row['visible_tool_pixels']=visible
            if label!='pregrasp' and min(visible.values())>30:
                candidates.append(dict(**row,initial_qpos=q.tolist()))
        rows.append(row)
    candidates.sort(key=lambda c:(-min(c['visible_tool_pixels'].values()),np.linalg.norm(np.asarray(c['arm_q'])-initial[qa])))
    for candidate in candidates[:3]:
        start=np.asarray(candidate['initial_qpos']);collisions=[]
        for fraction in np.linspace(0,1,81):
            q=initial.copy();q[qa]=(1-fraction)*start[qa]+fraction*initial[qa]
            bad=inspect(q)
            if bad:collisions.append(dict(fraction=float(fraction),contacts=bad))
        candidate['direct_arm_transition']=dict(samples=81,collision_free_at_samples=not collisions,
            collisions=collisions,continuous_clearance_guaranteed=False,executed=False)
    renderer.close();native_depth.close()
    report=dict(scope=__doc__,source_model_sha256=sha(source/'world.xml'),source_contract_sha256=sha(source/'contract.json'),
        script_sha256=sha(output/Path(__file__).name),depth_renderer_sha256=sha(output/'sensor_rendering.py'),
        depth_multisampling=False,camera_resolution=[640,480],rows=rows,candidates=candidates,
        evaluator_segmentation_given_to_actor=False,qualified_perception=False,qualified_approach=False)
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=len(rows),candidates=len(candidates),best=[{k:v for k,v in c.items() if k not in ['initial_qpos','direct_arm_transition']} for c in candidates[:3]])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args();run(a.source,a.output)
