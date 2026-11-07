"""Compare complete paired tool attempts after a device-sleep optimization.

Both attempts keep their independent verdicts. Agreement between trajectories
does not establish grasp success or count as a reliability qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(baseline, candidate, output):
    paths=[Path(p).resolve() for p in [baseline,candidate]]
    results=[json.loads((p/'result.json').read_text()) for p in paths]
    for p,r in zip(paths,results):
        assert sha(p/'trace.npz')==r['trace_sha256']
    models=[mujoco.MjModel.from_xml_path(str(p/'world.xml')) for p in paths]
    traces=[dict(np.load(p/'trace.npz')) for p in paths]
    m=models[0]
    assert m.njnt==models[1].njnt
    assert all(m.joint(j).name==models[1].joint(j).name for j in range(m.njnt))
    assert np.array_equal(traces[0]['time'],traces[1]['time']), 'Pair ended at different times'
    bodies={m.body(n).id for n in ['pelvis','tweezer','carrier_tray']}
    for b in range(m.nbody):
        if int(m.body_parentid[b]) in bodies:bodies.add(b)
    qa=[];va=[]
    for j in range(m.njnt):
        if int(m.jnt_bodyid[j]) not in bodies:continue
        nq={0:7,1:4,2:1,3:1}[int(m.jnt_type[j])];nv={0:6,1:3,2:1,3:1}[int(m.jnt_type[j])]
        qa.extend(range(m.jnt_qposadr[j],m.jnt_qposadr[j]+nq))
        va.extend(range(m.jnt_dofadr[j],m.jnt_dofadr[j]+nv))
    errors={}
    for field,indices in [('qpos',qa),('qvel',va),('ctrl',list(range(m.nu)))]:
        errors[field]=float(np.max(abs(traces[0][field][:,indices]-traces[1][field][:,indices])))
    sensors=[dict(np.load(p/'sensors.npz')) for p in paths]
    assert sensors[0].keys()==sensors[1].keys()
    sensor_errors={k:float(np.max(abs(sensors[0][k]-sensors[1][k]))) for k in sensors[0]}
    checks=dict(all_robot_tool_tray_state_and_commands_equal=max(errors.values())<=1e-10,
        all_actor_sensor_packets_equal=max(sensor_errors.values())<=1e-10,
        same_actor_source=sha(paths[0]/'source_snapshot/dex3_tool_actor.py')==sha(paths[1]/'source_snapshot/dex3_tool_actor.py'),
        same_actor_prior=sha(paths[0]/'policy_source/tool_prior.json')==sha(paths[1]/'policy_source/tool_prior.json'))
    report=dict(scope=__doc__,source_runs=[str(p) for p in paths],result_sha256=[sha(p/'result.json') for p in paths],
        script_sha256=sha(__file__),checks=checks,passed=all(checks.values()),
        active_state_errors=errors,sensor_errors=sensor_errors,states=len(traces[0]['time']),
        whole_world_maximum_qpos_difference=float(np.max(abs(traces[0]['qpos']-traces[1]['qpos']))),
        recorded_wall_seconds=[r['wall_seconds'] for r in results],qualified_grasp=False)
    Path(output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('candidate');p.add_argument('output')
    a=p.parse_args();run(a.baseline,a.candidate,a.output)
