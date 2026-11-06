"""Time native collision queries at a retained complete-laboratory state.

No physical time is advanced, no scene part is removed and no collision setting
is changed in the baseline. Optional contact-omission cases only attribute cost;
their contact filters are never exported as execution scenes or accepted models.
Timings diagnose execution cost, not task success or support forces.
"""
import argparse
import json
from pathlib import Path
import shutil
import time

import mujoco
import numpy as np

from frozen_collision_plugins import load, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene',type=Path)
    p.add_argument('support',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--queries',type=int,default=100)
    p.add_argument('--contact-cost-breakdown',action='store_true')
    a=p.parse_args()
    if not 10<=a.queries<=1000:p.error('Use 10 to 1000 bounded collision queries')
    scene,support,out=[v.resolve() for v in [a.scene,a.support,a.output]]
    binding=json.loads((scene/'binding.json').read_text())
    review=json.loads((support/'review.json').read_text())
    assert sha(scene/'world.xml')==binding['world_sha256']==review['world_sha256']
    assert sha(support/'trace.npz')==review['trace_sha256']
    loader=Path(__file__).with_name('frozen_collision_plugins.py')
    load(binding.get('collision_plugins',[]),sha(loader))
    m=mujoco.MjModel.from_xml_path(str(scene/'world.xml'))
    d=mujoco.MjData(m)
    with np.load(support/'trace.npz') as z:
        d.qpos[:]=z['qpos'][-1];d.qvel[:]=z['qvel'][-1]
    mujoco.set_mjcb_time(time.perf_counter)
    mujoco.mj_forward(m,d)
    def contacts():
        return np.asarray([[*c.geom,c.dist] for c in d.contact])
    original=contacts()
    for _ in range(5):mujoco.mj_collision(m,d)
    for stat in d.timer:stat.duration=0.;stat.number=0
    elapsed=[];same=True
    for _ in range(a.queries):
        start=time.perf_counter();mujoco.mj_collision(m,d);elapsed.append(time.perf_counter()-start)
        same=bool(same and np.array_equal(original,contacts()))
    timers={name:dict(seconds=float(d.timer[value.value].duration),calls=int(d.timer[value.value].number))
            for name,value in vars(mujoco.mjtTimer).items() if name.startswith('mjTIMER_')}
    omissions=[]
    if a.contact_cost_breakdown:
        try:
            for gid in np.flatnonzero(m.geom_type==mujoco.mjtGeom.mjGEOM_SDF):
                mujoco.set_mjcb_contactfilter(lambda model,data,a,b,target=int(gid): int(a==target or b==target))
                durations=[]
                for _ in range(a.queries):
                    start=time.perf_counter();mujoco.mj_collision(m,d);durations.append(time.perf_counter()-start)
                omissions.append(dict(omitted_geom=m.geom(gid).name,contact_count=int(d.ncon),
                    mean_wall_seconds=float(np.mean(durations)),median_wall_seconds=float(np.median(durations)),
                    valid_execution_model=False))
        finally:
            mujoco.set_mjcb_contactfilter(None)
            mujoco.mj_collision(m,d)
        assert np.array_equal(original,contacts())
    mujoco.set_mjcb_time(None)
    out.mkdir(parents=True,exist_ok=False)
    for path in [Path(__file__),loader]:shutil.copyfile(path,out/path.name)
    report=dict(scope=__doc__,world_sha256=binding['world_sha256'],support_review_sha256=sha(support/'review.json'),
        retained_trace_sha256=review['trace_sha256'],mujoco_version=mujoco.__version__,
        queries=a.queries,contact_count=int(d.ncon),all_contact_identities_and_distances_exact=same,
        collision_wall_seconds=dict(mean=float(np.mean(elapsed)),median=float(np.median(elapsed)),maximum=max(elapsed)),
        native_timers=timers,source_sha256={p.name:sha(p) for p in out.glob('*.py')},
        diagnostic_contact_omissions=omissions,
        qualified_robot_handling=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
