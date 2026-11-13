"""Compare a candidate query cache against original full-room collision output.

Retained poses are diagnostic inputs, not a newly executed robot trajectory.
The compared scene replaces selected plugin registrations only. No shape,
contact parameter, pose or runtime acceptance threshold is changed. Optional
short native continuations compare implementations, not task success.
"""
import argparse
import json
from pathlib import Path
import shutil
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from frozen_collision_plugins import load, sha


def contact_array(data):
    return np.asarray([[*c.geom,c.dist,*c.pos,*c.frame,c.dim,*c.friction,*c.solref,*c.solimp]
                       for c in data.contact])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path);p.add_argument('support',type=Path)
    p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--additional-candidate',type=Path,action='append',default=[])
    p.add_argument('--prepared-run',type=Path)
    p.add_argument('--native-steps',type=int,default=0)
    a=p.parse_args();scene,support,candidate,out=[v.resolve() for v in [a.scene,a.support,a.candidate,a.output]]
    if not 0<=a.native_steps<=1000:p.error('Use at most 1000 native continuation steps per segment')
    binding=json.loads((scene/'binding.json').read_text())
    review=json.loads((support/'review.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']
    world=scene/'world.xml';prepared_contract=None
    if a.prepared_run:
        prepared=a.prepared_run.resolve();prepared_contract=json.loads((prepared/'contract.json').read_text())
        assert prepared_contract['optical_scene_binding']['binding_sha256']==sha(scene/'binding.json')
        assert sha(prepared/'contract.json')==review['prepared_runtime']['contract_sha256']
        world=prepared/'world.xml'
        assert sha(world)==prepared_contract['model_sha256']
    assert sha(world)==review['world_sha256']
    assert sha(support/'trace.npz')==review['trace_sha256']
    replacements=[]
    for path in [candidate,*[p.resolve() for p in a.additional_candidate]]:
        proposed=json.loads((path/'plugin.json').read_text())
        original=json.loads((path/'original_plugin.json').read_text())
        assert sha(path/'original_plugin.json')==proposed['original_receipt_sha256']
        assert any(p['library_sha256']==original['library_sha256'] for p in binding['collision_plugins'])
        assert proposed['geometry_header_arrays_unchanged']
        replacements.append((original,proposed,path))
    assert len({old['plugin_name'] for old,_,_ in replacements})==len(replacements)
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load([*binding['collision_plugins'],*[new for _,new,_ in replacements]],sha(loader))
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),loader]:shutil.copyfile(path,out/path.name)
    xml=ET.parse(world)
    for original,proposed,_ in replacements:
        nodes=xml.getroot().findall("extension/plugin[@plugin='"+original['plugin_name']+"']")
        assert len(nodes)==1;nodes[0].set('plugin',proposed['plugin_name'])
    xml.write(out/'candidate_world.xml',encoding='unicode')
    models=[mujoco.MjModel.from_xml_path(str(p)) for p in [world,out/'candidate_world.xml']]
    data=[mujoco.MjData(m) for m in models]
    fields=['body_mass','body_inertia','body_ipos','body_iquat','geom_type','geom_pos','geom_quat','geom_size',
            'geom_friction','geom_solref','geom_solimp','geom_contype','geom_conaffinity',
            'mesh_vert','mesh_face','qpos0','jnt_range','dof_damping','actuator_gear','actuator_ctrlrange']
    assert all(np.array_equal(getattr(models[0],f),getattr(models[1],f)) for f in fields)
    assert models[0].npluginstate==models[1].npluginstate==0
    with np.load(support/'trace.npz') as z:
        ids=np.unique(np.r_[np.arange(min(32,len(z['time']))),np.linspace(0,len(z['time'])-1,64).astype(int)])
        states=z['qpos'][ids];velocities=z['qvel'][ids];times=z['time'][ids]
        trace={k:z[k].copy() for k in ['time','qpos','qvel','ctrl']}
    comparisons=[]
    for t,q,v in zip(times,states,velocities):
        outputs=[]
        for m,d in zip(models,data):
            mujoco.mj_resetData(m,d);d.qpos[:]=q;d.qvel[:]=v;mujoco.mj_forward(m,d)
            outputs.append((contact_array(d),d.qacc.copy(),d.qfrc_constraint.copy()))
        comparisons.append(dict(time_s=float(t),contacts_exact=np.array_equal(outputs[0][0],outputs[1][0]),
            accelerations_exact=np.array_equal(outputs[0][1],outputs[1][1]),
            constraint_forces_exact=np.array_equal(outputs[0][2],outputs[1][2]),contact_count=int(data[0].ncon)))
    durations=[[],[]]
    for _ in range(100):
        for i,(m,d) in enumerate(zip(models,data)):
            start=time.perf_counter();mujoco.mj_collision(m,d);durations[i].append(time.perf_counter()-start)
    passed=all(all(row[k] for k in ['contacts_exact','accelerations_exact','constraint_forces_exact']) for row in comparisons)
    medians=np.median(durations,axis=1)
    native=[]
    if a.native_steps:
        dt=float(models[0].opt.timestep)
        duration=a.native_steps*dt
        last=int(np.searchsorted(trace['time'],trace['time'][-1]-duration))-1
        assert last>0
        for first in [0,last//2,last]:
            rows=[];walls=[];start=float(trace['time'][first])
            for m,d in zip(models,data):
                mujoco.mj_resetData(m,d);d.time=start
                d.qpos[:]=trace['qpos'][first];d.qvel[:]=trace['qvel'][first]
                d.ctrl[:]=trace['ctrl'][first];mujoco.mj_forward(m,d)
                history=[];begin=time.perf_counter()
                for step in range(a.native_steps):
                    tick=int(np.searchsorted(trace['time'],start+step*dt+1e-10,side='right'))-1
                    d.ctrl[:]=trace['ctrl'][tick];mujoco.mj_step(m,d)
                    history.append((d.qpos.copy(),d.qvel.copy(),d.qacc.copy(),contact_array(d),d.qfrc_constraint.copy()))
                walls.append(time.perf_counter()-begin);rows.append(history)
            exact=all(np.array_equal(x,y) for before,after in zip(*rows) for x,y in zip(before,after))
            native.append(dict(start_time_s=start,steps=a.native_steps,simulated_seconds=duration,
                states_accelerations_contacts_and_forces_exact=exact,baseline_wall_s=walls[0],
                candidate_wall_s=walls[1],speedup=walls[0]/walls[1]))
        passed=bool(passed and all(x['states_accelerations_contacts_and_forces_exact'] for x in native))
    replaced={old['plugin_name']:new for old,new,_ in replacements}
    candidate_plugins=[replaced.get(old['plugin_name'],old) for old in binding['collision_plugins']]
    (out/'candidate_plugins.json').write_text(json.dumps(candidate_plugins,indent=2)+'\n')
    report=dict(scope=__doc__,passed=bool(passed),sampled_states=len(ids),comparisons=comparisons,
        baseline_median_collision_s=float(medians[0]),candidate_median_collision_s=float(medians[1]),
        measured_speedup=float(medians[0]/medians[1]),world_sha256=sha(world),
        candidate_world_sha256=sha(out/'candidate_world.xml'),
        candidate_plugin_receipts_sha256={str(path/'plugin.json'):sha(path/'plugin.json') for _,_,path in replacements},
        candidate_plugins_sha256=sha(out/'candidate_plugins.json'),unchanged_compiled_fields=fields,
        native_continuations=native,
        retained_trace_sha256=review['trace_sha256'],source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        full_continuous_physics_replay_performed=False,qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','sampled_states','baseline_median_collision_s',
        'candidate_median_collision_s','measured_speedup']}),flush=True)
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
