"""Independently re-evaluate a continuous trace, without trusting action labels."""
import mujoco
import numpy as np
from support_observation import support_load,designated_surfaces


def evaluate(robot,targets,assembled_times):
    model=robot.model;data=mujoco.MjData(model)
    failures=[];checks=[]

    def inspect(name,target,support,at):
        trace=min(robot.trace,key=lambda row:abs(row[0]-at))
        data.qpos[:]=trace[1];data.qvel[:]=trace[2];data.ctrl[:]=trace[3]
        mujoco.mj_forward(model,data)
        load=support_load(model,data,name,support,designated_surfaces(name,support))
        force=load['vertical_force_n']
        error=float(np.linalg.norm(data.body(name).xpos-target))
        tilt=float(np.arccos(np.clip(data.body(name).xmat.reshape(3,3)[2,2],-1,1)))
        speed=float(np.linalg.norm(data.body(name).cvel))
        enough_surfaces=name!='shield' or support!='assembly_base' or len(load['loaded_support_geoms'])>=3
        passed=error<.003 and tilt<.035 and speed<.03 and force>load['body_weight_n']*.8 and enough_surfaces
        row=dict(body=name,time_s=float(trace[0]),support=support,position_error_m=error,
                 tilt_rad=tilt,speed=speed,support_force_n=force,load=load,passed=passed)
        checks.append(row)
        if not passed:failures.append(row)

    for at in assembled_times:
        for name,p in targets.items():inspect(name,np.asarray(p['assembled']),p['support'],at)
    for name,p in targets.items():inspect(name,np.asarray(p['park']),name+'_stand',robot.trace[-1][0])
    continuity=[]
    q=np.array([row[1] for row in robot.trace])
    for name in targets:
        joint=model.joint(name+'_free').id;adr=model.jnt_qposadr[joint]
        maximum=float(np.linalg.norm(np.diff(q[:,adr:adr+3],axis=0),axis=1).max())
        # Sampled continuity evidence, not a proof of the absence of tiny writes.
        continuity.append(dict(body=name,max_translation_per_20ms_m=maximum,passed=maximum<.020))
    return dict(passed=not failures and all(c['passed'] for c in continuity) and bool(assembled_times),
                checks=checks,continuity=continuity,whole_paper_validated=False,
                scope='Bound rigid-layer assembly and return only; no source operation or branch automatically credited')
