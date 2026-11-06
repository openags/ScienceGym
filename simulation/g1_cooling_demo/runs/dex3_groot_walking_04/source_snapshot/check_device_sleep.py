"""Measure optional native sleeping of unattended instrument mechanisms.

Robot, tool and tray always remain awake. Geometry, constraints and actuator
inputs are unchanged. This bounded comparison is not a grasp qualification;
any adoption needs a fresh run, independent replay and device wake checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(source, output, duration, cover_only=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, output/Path(__file__).name)
    tree = ET.parse(source/'world.xml').getroot()
    option = tree.find('option')
    flag = option.find('flag')
    if flag is None:
        flag = ET.SubElement(option, 'flag')
    flag.set('sleep', 'enable')
    option.set('sleep_tolerance', '0.0000001')
    active = ['pelvis', 'tweezer', 'carrier_tray']
    device = ['nicolet_cover'] + ['nicolet_key_'+str(i) for i in range(4)]
    if cover_only:
        active += device[1:]
        device = device[:1]
    for name in active+device:
        tree.find(".//body[@name='"+name+"']").set('sleep', 'never' if name in active else 'allowed')
    ET.indent(tree)
    ET.ElementTree(tree).write(output/'world.xml', encoding='unicode')
    trace = dict(np.load(source/'trace.npz'))
    original = mujoco.MjModel.from_xml_path(str(source/'world.xml'))
    candidate = mujoco.MjModel.from_xml_path(str(output/'world.xml'))
    same = {}
    for field in ['geom_bodyid','geom_type','geom_size','geom_pos','geom_quat','geom_contype','geom_conaffinity',
                  'geom_friction','geom_solref','geom_solimp','geom_margin','body_mass','body_inertia',
                  'jnt_range','jnt_stiffness','dof_damping','actuator_ctrlrange','mesh_vert','mesh_face']:
        same[field] = bool(np.array_equal(getattr(original,field), getattr(candidate,field)))
    histories, sleeps, timings, errors = [], [], [], []
    steps = min(round(duration/original.opt.timestep), len(trace['time'])-1)
    for model in [original,candidate]:
        data = mujoco.MjData(model)
        data.qpos[:] = trace['qpos'][0]
        data.qvel[:] = trace['qvel'][0]
        mujoco.mj_forward(model,data)
        data.qacc_warmstart[:] = trace['qacc_warmstart'][0]
        values, states = [], []
        started = time.monotonic()
        for i in range(steps):
            data.ctrl[:] = trace['ctrl'][i]
            mujoco.mj_step(model,data)
            values.append(np.r_[data.qpos,data.qvel])
            states.append(data.tree_asleep.copy())
        timings.append(time.monotonic()-started)
        histories.append(np.asarray(values));sleeps.append(np.asarray(states))
        errors.append(float(np.max(abs(histories[-1]-np.c_[trace['qpos'][1:steps+1],trace['qvel'][1:steps+1]]))))
    delta=abs(histories[0]-histories[1]); trees={name:int(candidate.body_treeid[candidate.body(name).id]) for name in active+device}
    body_set={candidate.body(n).id for n in active}
    for b in range(candidate.nbody):
        if int(candidate.body_parentid[b]) in body_set:body_set.add(b)
    indices=[]
    for j in range(candidate.njnt):
        if int(candidate.jnt_bodyid[j]) not in body_set:continue
        nq={0:7,1:4,2:1,3:1}[int(candidate.jnt_type[j])]
        nv={0:6,1:3,2:1,3:1}[int(candidate.jnt_type[j])]
        indices.extend(range(candidate.jnt_qposadr[j],candidate.jnt_qposadr[j]+nq))
        indices.extend(candidate.nq+np.arange(candidate.jnt_dofadr[j],candidate.jnt_dofadr[j]+nv))
    result=dict(scope=__doc__, source_model_sha256=sha(source/'world.xml'), model_sha256=sha(output/'world.xml'),
        source_trace_sha256=sha(source/'trace.npz'),script_sha256=sha(output/Path(__file__).name),
        reference='https://mujoco.readthedocs.io/en/3.15.0/programming/simulation.html#sleeping-islands',
        steps=steps,simulated_seconds=steps*original.opt.timestep,sleep_tolerance_m_s=1e-7,
        exact_compiled_preservation=same,seconds_original_candidate=timings,
        maximum_recorded_replay_error=errors,maximum_state_difference=float(delta.max()),
        maximum_robot_tool_tray_state_difference=float(delta[:,indices].max()),
        active_trees_always_awake=all(bool(np.all(sleeps[1][:,trees[n]]<0)) for n in active),
        device_sleep_step_counts={n:int(np.sum(sleeps[1][:,trees[n]]>=0)) for n in device},
        cover_only=cover_only,device_wake_checks_complete=False,adopted=False,qualified_grasp=False)
    np.savez_compressed(output/'comparison.npz',original=histories[0],candidate=histories[1],tree_asleep=sleeps[1])
    (output/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');p.add_argument('--duration',type=float,default=.2)
    p.add_argument('--cover-only',action='store_true')
    a=p.parse_args();run(a.source,a.output,a.duration,a.cover_only)
