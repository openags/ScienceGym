"""Compare a candidate query cache against original full-room collision output.

Retained poses are diagnostic inputs, not a newly executed robot trajectory.
The compared scene replaces one plugin registration only. No shape, contact
parameter, pose or runtime acceptance threshold is changed.
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
    a=p.parse_args();scene,support,candidate,out=[v.resolve() for v in [a.scene,a.support,a.candidate,a.output]]
    binding=json.loads((scene/'binding.json').read_text())
    review=json.loads((support/'review.json').read_text())
    proposed=json.loads((candidate/'plugin.json').read_text())
    original=json.loads((candidate/'original_plugin.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']==review['world_sha256']
    assert sha(support/'trace.npz')==review['trace_sha256']
    assert sha(candidate/'original_plugin.json')==proposed['original_receipt_sha256']
    assert any(p['library_sha256']==original['library_sha256'] for p in binding['collision_plugins'])
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load([*binding['collision_plugins'],proposed],sha(loader))
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),loader]:shutil.copyfile(path,out/path.name)
    xml=ET.parse(scene/'world.xml')
    nodes=xml.getroot().findall("extension/plugin[@plugin='"+original['plugin_name']+"']")
    assert len(nodes)==1;nodes[0].set('plugin',proposed['plugin_name'])
    xml.write(out/'candidate_world.xml',encoding='unicode')
    models=[mujoco.MjModel.from_xml_path(str(p)) for p in [scene/'world.xml',out/'candidate_world.xml']]
    data=[mujoco.MjData(m) for m in models]
    fields=['body_mass','body_inertia','geom_type','geom_pos','geom_quat','geom_size','mesh_vert','mesh_face','qpos0']
    assert all(np.array_equal(getattr(models[0],f),getattr(models[1],f)) for f in fields)
    with np.load(support/'trace.npz') as z:
        ids=np.unique(np.r_[np.arange(min(32,len(z['time']))),np.linspace(0,len(z['time'])-1,64).astype(int)])
        states=z['qpos'][ids];velocities=z['qvel'][ids];times=z['time'][ids]
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
    report=dict(scope=__doc__,passed=bool(passed),sampled_states=len(ids),comparisons=comparisons,
        baseline_median_collision_s=float(medians[0]),candidate_median_collision_s=float(medians[1]),
        measured_speedup=float(medians[0]/medians[1]),world_sha256=binding['world_sha256'],
        candidate_world_sha256=sha(out/'candidate_world.xml'),candidate_plugin_sha256=sha(candidate/'plugin.json'),
        retained_trace_sha256=review['trace_sha256'],source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        full_continuous_physics_replay_performed=False,qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['passed','sampled_states','baseline_median_collision_s',
        'candidate_median_collision_s','measured_speedup']}),flush=True)
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
