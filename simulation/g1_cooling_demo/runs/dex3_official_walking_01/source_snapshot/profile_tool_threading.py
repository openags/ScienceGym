"""Compare native MuJoCo threading on bounded recorded-control segments.

Each segment starts from the same retained q/v/warmstart and replays the same
motor commands. The threaded traces are compared to the unthreaded diagnostic,
not claimed to reproduce the full source run's unrecorded sleep internals.
This measures physics only, under concurrent development load and with timing
callbacks enabled. It does not qualify a controller, full run or robot skill.
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
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('recording');p.add_argument('output')
    p.add_argument('--times',type=float,nargs='+',default=[0.,15.,22.]);p.add_argument('--duration',type=float,default=.2)
    p.add_argument('--threads',type=int,nargs='+',default=[0,2,4]);a=p.parse_args()
    assert a.threads[0]==0 and all(n>=0 for n in a.threads) and a.duration>0
    run=Path(a.recording).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    result=json.loads((run/'result.json').read_text());contract=json.loads((run/'contract.json').read_text())
    assert sha(run/'trace.npz')==result['trace_sha256'] and sha(run/'world.xml')==contract['model_sha256']
    trace=dict(np.load(run/'trace.npz'));model=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
    count=round(a.duration/model.opt.timestep);rows=[]
    shutil.copyfile(__file__,out/'profile_tool_threading.py')
    mujoco.set_mjcb_time(time.perf_counter)
    try:
        for requested in a.times:
            first=int(np.searchsorted(trace['time'],requested))
            if first+count>=len(trace['time']):raise ValueError('Segment exceeds recorded controls')
            reference=None
            for threads in a.threads:
                data=mujoco.MjData(model)
                if threads:mujoco.mju_threadpool(data,threads)
                data.time=float(trace['time'][first]);data.qpos[:]=trace['qpos'][first];data.qvel[:]=trace['qvel'][first]
                data.ctrl[:]=trace['ctrl'][first];mujoco.mj_forward(model,data);data.qacc_warmstart[:]=trace['qacc_warmstart'][first]
                for timer in data.timer:timer.duration=0.;timer.number=0
                positions=np.empty((count,model.nq));velocities=np.empty((count,model.nv));contacts=[]
                started=time.perf_counter()
                for step in range(count):
                    data.ctrl[:]=trace['ctrl'][first+step];mujoco.mj_step(model,data)
                    positions[step]=data.qpos;velocities[step]=data.qvel;contacts.append(int(data.ncon))
                wall=time.perf_counter()-started
                if reference is None:reference=(positions.copy(),velocities.copy(),wall)
                qerr=float(np.max(abs(positions-reference[0])));verr=float(np.max(abs(velocities-reference[1])))
                filename=f'{requested:06.3f}s_threads_{threads}.npz';np.savez_compressed(out/filename,qpos=positions,qvel=velocities,contacts=contacts)
                timers={name:dict(calls=int(data.timer[index].number),wall_s=float(data.timer[index].duration))
                        for name,index in mujoco.mjtTimer.__members__.items() if name!='mjNTIMER'}
                row=dict(start_time_s=float(trace['time'][first]),worker_threads=threads,steps=count,
                         simulated_duration_s=count*float(model.opt.timestep),wall_s=wall,
                         speedup_vs_unthreaded=reference[2]/wall,maximum_q_error_vs_unthreaded=qerr,
                         maximum_v_error_vs_unthreaded=verr,within_existing_replay_tolerance=max(qerr,verr)<=1e-10,
                         numerical_warning_counts=data.warning.number.tolist(),timers=timers,
                         trajectory_file=filename,trajectory_sha256=sha(out/filename))
                rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='timers'}),flush=True)
                del data
    finally:mujoco.set_mjcb_time(None)
    report=dict(scope=__doc__,mujoco_version=mujoco.__version__,source_trace_sha256=result['trace_sha256'],
                model_sha256=contract['model_sha256'],profiler_sha256=sha(__file__),rows=rows,
                full_trajectory_equivalence_evaluated=False,physical_execution_qualified=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
