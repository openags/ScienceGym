"""Post-execution diagnosis of which surface contributes to a native grip fit.

The original prediction is computed first. Plant geometry is then loaded by
this evaluator only, to label depth points and display a cross-section.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import inspect_visible_surfaces as v
import mujoco
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(run,time,out):
    run,out=Path(run),Path(out)
    if out.exists():raise FileExistsError(out)
    out.mkdir()
    events=json.loads((run/'result.json').read_text())['actor_last_output']['events']
    baseline=next(e['grip_observations'] for e in events if 'grip_observations' in e)
    cm=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));cd=v.initialize_slider(cm)
    with np.load(run/'sensor_observations.npz') as a:
        i=int(np.argmin(abs(a['time_s']-time)))
        if abs(a['time_s'][i]-time)>1e-7:raise ValueError('No matching sensor packet')
        packet={k:a[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
    depth=v.frame(run,'head_depth_index.json','parts',time,True);rgb=v.frame(run,'head_rgb_index.json','chunks',time)
    packet['depth']=depth;v.StateEstimate(cm,cd).update(packet)
    keys=v.KeyRowObservation(cm,cd).observe(rgb,depth)
    observer=v.SliderRangeObservation(cm,cd,run/'policy_source/slider_push_prior.json',run/'object_shape_source/nicolet_passive_dynamics.glb',baseline)
    prediction=observer.observe(depth,keys)
    R,t=v.register(keys,observer.prior)
    h,w=depth.shape;pc=cm.camera('head_depth').id
    focal=h/(2*np.tan(np.deg2rad(cm.cam_fovy[pc])/2))
    y,x=np.mgrid[:h,:w];good=np.isfinite(depth)&(depth>.05)&(depth<2.)
    rays=np.stack([(x+.5-w/2)*depth/focal,-(y+.5-h/2)*depth/focal,-depth],axis=-1)[good]
    predicted_world=rays@cd.cam_xmat[pc].reshape(3,3).T+cd.cam_xpos[pc]
    local=(predicted_world-t)@R
    mask=(abs(local[:,0]-observer.center[0])<.035)&(abs(local[:,1]-observer.center[1])<.008)
    mask&=(local[:,2]>observer.bounds[0,2]+.0004)&(local[:,2]<observer.bounds[1,2]+.001)
    points=local[mask]
    # Truth becomes accessible only after the native-image prediction above.
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    with np.load(run/'trace.npz') as a:
        ti=max(0,int(np.argmin(abs(a['time']-time)))-1);d.qpos[:]=a['qpos'][ti]
    mujoco.mj_forward(m,d);tc=m.camera('head_depth').id
    imported=json.loads((run/'laboratory_import.json').read_text())
    name=next(p['geom'] for p in imported['parts'] if p['source_part']=='sample_access_slider_grip')
    g=m.geom(name).id;mesh=int(m.geom_dataid[g]);va=m.mesh_vertadr[mesh];fa=m.mesh_faceadr[mesh]
    vertices=m.mesh_vert[va:va+m.mesh_vertnum[mesh]]@d.geom_xmat[g].reshape(3,3).T+d.geom_xpos[g]
    faces=m.mesh_face[fa:fa+m.mesh_facenum[mesh]]
    mesh_world=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    world=rays[mask]@d.cam_xmat[tc].reshape(3,3).T+d.cam_xpos[tc]
    distances=trimesh.proximity.closest_point(mesh_world,world)[1]
    projected=(vertices-d.cam_xpos[tc])@d.cam_xmat[tc].reshape(3,3)@cd.cam_xmat[pc].reshape(3,3).T+cd.cam_xpos[pc]
    registered_mesh=(projected-t)@R
    close=distances<.00025
    mm=(points-observer.center)*1000.;mesh_mm=(registered_mesh-observer.center)*1000.
    np.savez_compressed(out/'cloud.npz',registered_points_m=points,evaluated_grip_distance_m=distances,registered_mesh_vertices_m=registered_mesh)
    fig,ax=plt.subplots(figsize=(8,5))
    ax.scatter(mm[~close,1],mm[~close,2],s=12,c='#d14b40',label='Other surfaces (evaluator labels)')
    ax.scatter(mm[close,1],mm[close,2],s=12,c='#25865b',label='Native grip surface')
    ax.scatter(mesh_mm[:,1],mesh_mm[:,2],s=7,c='#245cbe',alpha=.3,label='Actual grip vertices')
    ax.set(xlabel='Slide-axis offset from requested position (mm)',ylabel='Height from public grip centre (mm)',title=f'Native depth selection at {time:.1f} s')
    ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'cross_section.png',dpi=180);plt.close(fig)
    report=dict(scope=__doc__,run=str(run),time_s=time,original_prediction=prediction,
                selected_points=len(points),points_on_actual_grip=int(close.sum()),
                actual_grip_distance_quantiles_m=np.quantile(distances,[0,.25,.5,.75,1]).tolist(),
                evaluated_actual_slider_m=float(d.joint('nicolet_door_slide').qpos[0]),
                source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(v.__file__),run/'result.json',run/'trace.npz',run/'world.xml']})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('time',type=float);p.add_argument('out');a=p.parse_args();main(a.run,a.time,a.out)
