"""Compare CPU and GPU physics on the unchanged laboratory tool model.

The fixed initial motor command is a bounded performance diagnostic. This does
not run the sensor controller, qualify contact fidelity or validate a task.
Compilation and host/device setup are reported separately from warm stepping.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

import mujoco
import mujoco_warp as mjw
import numpy as np
import warp as wp


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--worlds',type=int,nargs='+',default=[1,4])
    p.add_argument('--steps',type=int,default=100)
    a=p.parse_args();run=a.run.resolve();out=a.output.resolve()
    if not 1<=a.steps<=1000 or any(n not in {1,2,4,8} for n in a.worlds):
        p.error('Use 1–1000 steps and at most eight worlds')
    contract=json.loads((run/'contract.json').read_text())
    result=json.loads((run/'result.json').read_text())
    assert sha(run/'world.xml')==contract['model_sha256']
    assert sha(run/'trace.npz')==result['trace_sha256']
    assert not contract.get('collision_plugins'), 'Custom SDFs require a separately validated Warp port'
    out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,out/Path(__file__).name)
    report=dict(scope=__doc__,world_sha256=contract['model_sha256'],source_contract_sha256=sha(run/'contract.json'),
        source_trace_sha256=result['trace_sha256'],versions={n:importlib.metadata.version(n) for n in
            ['mujoco','mujoco-warp','warp-lang','numpy']},script_sha256=sha(__file__),rows=[],
        model_or_acceptance_modified=False,closed_loop_controller_executed=False,qualified_robot_handling=False)
    def save():
        (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        start=time.perf_counter();model=mujoco.MjModel.from_xml_path(str(run/'world.xml'))
        with np.load(run/'trace.npz') as trace:ctrl=trace['ctrl'][0].copy()
        def initial():
            d=mujoco.MjData(model);d.qpos[:]=contract['initial_qpos'];d.qvel[:]=contract['initial_qvel']
            d.ctrl[:]=ctrl;mujoco.mj_forward(model,d);return d
        report.update(model_load_s=time.perf_counter()-start,nq=model.nq,nv=model.nv,ngeom=model.ngeom,
            physics_step_s=float(model.opt.timestep),fixed_control_sha256=hashlib.sha256(ctrl.tobytes()).hexdigest())
        cpu=initial();start=time.perf_counter()
        for _ in range(a.steps):mujoco.mj_step(model,cpu)
        report.update(cpu_wall_s=time.perf_counter()-start,cpu_warning_counts=cpu.warning.number.tolist())
        wp.init();device=wp.get_device('cuda:0')
        report['device']=dict(name=device.name,alias=device.alias,architecture=device.arch)
        with wp.ScopedDevice(device):
            start=time.perf_counter();gpu_model=mjw.put_model(model)
            report['model_transfer_s']=time.perf_counter()-start
            for n in a.worlds:
                start=time.perf_counter()
                data=mjw.put_data(model,initial(),nworld=n,nconmax=512,njmax=2048)
                mjw.step(gpu_model,data);wp.synchronize()
                warm=time.perf_counter()-start
                data=mjw.put_data(model,initial(),nworld=n,nconmax=512,njmax=2048)
                with wp.ScopedCapture() as capture:mjw.step(gpu_model,data)
                wp.synchronize();start=time.perf_counter()
                for _ in range(a.steps):wp.capture_launch(capture.graph)
                wp.synchronize();elapsed=time.perf_counter()-start
                q=data.qpos.numpy();v=data.qvel.numpy()
                path=out/f'worlds_{n}.npz';np.savez_compressed(path,qpos=q,qvel=v)
                row=dict(worlds=n,steps=a.steps,simulated_seconds_per_world=a.steps*float(model.opt.timestep),
                    compilation_and_warmup_s=warm,gpu_wall_s=elapsed,
                    single_world_latency_speedup=report['cpu_wall_s']/elapsed,
                    aggregate_throughput_speedup=n*report['cpu_wall_s']/elapsed,
                    finite=bool(np.isfinite(q).all() and np.isfinite(v).all()),
                    maximum_q_difference_from_cpu=float(np.max(abs(q-cpu.qpos))),
                    maximum_v_difference_from_cpu=float(np.max(abs(v-cpu.qvel))),
                    state_file=path.name,state_sha256=sha(path))
                report['rows'].append(row);save();print(json.dumps(row),flush=True)
                del data
        report['status']='performance_probe_finished_contact_fidelity_unqualified';save()
    except Exception as error:
        report.update(status='backend_probe_failed',error=type(error).__name__+': '+str(error));save();raise


if __name__=='__main__':main()
