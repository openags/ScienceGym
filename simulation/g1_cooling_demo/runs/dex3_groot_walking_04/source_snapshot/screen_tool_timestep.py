"""Bounded timestep sensitivity screen with unchanged recorded motor inputs.

This compares short open-loop segments from one successful pickup, not whole
closed-loop trials. It does not adopt a new timestep, alter any recorded model,
or grant physical/repeatability qualification. Force extrema are sampled at
every native step; q/v comparisons use common 1 ms boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output')
    p.add_argument('--times',type=float,nargs='+',default=[8.,15.,22.]);p.add_argument('--duration',type=float,default=.2)
    a=p.parse_args();run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'trace.npz')==result['trace_sha256'] and sha(run/'world.xml')==contract['model_sha256']
    trace=dict(np.load(run/'trace.npz'));m=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    source_step=float(m.opt.timestep);assert abs(source_step-.0001)<1e-12
    shutil.copyfile(__file__,out/'screen_tool_timestep.py')
    tool={m.body('tweezer').id};robot={m.body('pelvis').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in tool:tool.add(b)
        if m.body_parentid[b] in robot:robot.add(b)
    allowed={m.body(n).id for n in contract['allowed_tool_contact_bodies']}
    joints=[j for j in range(m.njnt) if int(m.jnt_bodyid[j]) in robot and m.jnt_limited[j]]
    qa=m.jnt_qposadr[joints];qlo=m.jnt_range[joints,0];qhi=m.jnt_range[joints,1]
    source_stride=round(.001/source_step);rows=[]
    for requested in a.times:
        first=int(np.argmin(abs(trace['time']-requested)))
        if first%source_stride or first+round(a.duration/source_step)>=len(trace['time']):
            raise ValueError('Segment must start on a recorded control boundary and remain inside the trace')
        reference=None
        for step in [source_step,.0002,.00025,.0005]:
            m.opt.timestep=step;count=round(a.duration/step);stride=round(.001/step)
            assert abs(stride*step-.001)<1e-12 and count%stride==0
            d=mujoco.MjData(m);d.time=float(trace['time'][first]);d.qpos[:]=trace['qpos'][first];d.qvel[:]=trace['qvel'][first]
            d.ctrl[:]=trace['ctrl'][first];mujoco.mj_forward(m,d);d.qacc_warmstart[:]=trace['qacc_warmstart'][first]
            qs=[];vs=[];maximum_force=0.;maximum_penetration=0.;maximum_joint_excess=0.;minimum_finger_load=float('inf')
            started=time.perf_counter()
            for i in range(count):
                tick=i//stride;d.ctrl[:]=trace['ctrl'][first+tick*source_stride]
                mujoco.mj_step(m,d)
                finger={f:0. for f in ['thumb','index','middle']}
                for ci,c in enumerate(d.contact):
                    bs={int(m.geom_bodyid[g]) for g in c.geom}
                    if not(bs&tool and bs&allowed):continue
                    body=m.body(next(iter(bs&allowed))).name;name=next(f for f in finger if f in body)
                    force=np.zeros(6);mujoco.mj_contactForce(m,d,ci,force);finger[name]+=max(0.,float(force[0]))
                    maximum_penetration=max(maximum_penetration,-float(c.dist))
                maximum_force=max(maximum_force,max(finger.values()));minimum_finger_load=min(minimum_finger_load,min(finger.values()))
                maximum_joint_excess=max(maximum_joint_excess,float(np.max(np.maximum(qlo-d.qpos[qa],d.qpos[qa]-qhi),initial=0.)))
                if (i+1)%stride==0:qs.append(d.qpos.copy());vs.append(d.qvel.copy())
            wall=time.perf_counter()-started;qs=np.asarray(qs);vs=np.asarray(vs)
            if reference is None:reference=(qs.copy(),vs.copy(),wall)
            name=f'{requested:.3f}s_dt_{step:.5f}.npz';np.savez_compressed(out/name,qpos=qs,qvel=vs)
            row=dict(start_time_s=float(trace['time'][first]),native_step_s=step,native_steps=count,
                control_period_s=.001,wall_s=wall,speedup_vs_original=reference[2]/wall,
                maximum_q_difference_vs_original=float(np.max(abs(qs-reference[0]))),
                maximum_v_difference_vs_original=float(np.max(abs(vs-reference[1]))),
                maximum_finger_normal_force_n=maximum_force,minimum_finger_normal_force_n=minimum_finger_load,
                maximum_hand_tool_penetration_m=maximum_penetration,maximum_robot_joint_limit_excess_rad=maximum_joint_excess,
                numerical_warnings=d.warning.number.tolist(),samples_file=name,samples_sha256=sha(out/name))
            rows.append(row);print(json.dumps(row),flush=True)
    report=dict(scope=__doc__,mujoco_version=mujoco.__version__,source_result_sha256=sha(run/'result.json'),
        source_trace_sha256=result['trace_sha256'],source_model_sha256=contract['model_sha256'],
        script_sha256=sha(__file__),rows=rows,new_timestep_adopted=False,qualified_physics_or_skill=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
