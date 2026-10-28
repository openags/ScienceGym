"""Replay a retained contact interval to inspect actual contact wrench vectors."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent;ROOT = HERE.parents[3]


def main(folder):
    folder = Path(folder).resolve();out = HERE/(folder.name+'_forces.json')
    if out.exists():raise FileExistsError(out)
    tr = dict(np.load(folder/'trace.npz'));m = mujoco.MjModel.from_xml_path(str(folder/'world.xml'))
    d = mujoco.MjData(m);begin = int(np.argmin(abs(tr['time']-44.5)))
    end = int(np.argmin(abs(tr['time']-48)))
    d.qpos[:] = tr['qpos'][begin];d.qvel[:] = tr['qvel'][begin];d.time = float(tr['time'][begin])
    mujoco.mj_forward(m,d);d.qacc_warmstart[:] = tr['qacc_warmstart'][begin]
    targets = {int(np.argmin(abs(tr['time']-t))) for t in [45.5,46,46.5,47,47.5]}
    root = m.body('pelvis').id
    def robot(geom):
        b = int(m.geom_bodyid[geom])
        while b and b != root:b = int(m.body_parentid[b])
        return b == root
    maxq = maxv = 0.;rows = []
    for i in range(begin,end):
        maxq = max(maxq,float(np.max(abs(d.qpos-tr['qpos'][i]))))
        maxv = max(maxv,float(np.max(abs(d.qvel-tr['qvel'][i]))))
        d.ctrl[:] = tr['ctrl'][i];mujoco.mj_step(m,d)
        if i not in targets:continue
        contacts = [];total = np.zeros(3)
        for ci,c in enumerate(d.contact):
            a,b = map(int,c.geom);names = [m.geom(a).name,m.geom(b).name]
            if not any('right_index' in n for n in names):continue
            if robot(a) == robot(b):continue
            f = np.zeros(6);mujoco.mj_contactForce(m,d,ci,f)
            # Positive contact-frame force acts on geom2. For a robot geom1
            # this is the applied object force; reverse it for robot geom2.
            applied = c.frame.reshape(3,3).T@f[:3]*(1 if robot(a) else -1)
            total += applied
            contacts.append(dict(parts=names,normal_force_n=float(f[0]),
                friction_components_n=f[1:3].tolist(),force_on_object_world_n=applied.tolist()))
        rows.append(dict(time_s=float(tr['time'][i]),contacts=contacts,
                         total_force_on_object_world_n=total.tolist()))
    maxq = max(maxq,float(np.max(abs(d.qpos-tr['qpos'][end]))))
    maxv = max(maxv,float(np.max(abs(d.qvel-tr['qvel'][end]))))
    report = dict(rows=rows,maximum_replay_position_error=maxq,maximum_replay_velocity_error=maxv,
        interval_s=[float(tr['time'][begin]),float(tr['time'][end])],
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),folder/'trace.npz',folder/'world.xml']},
        scope='Evaluator-only contact-interval motor replay from retained warm-start checkpoint. Does not replace complete independent replay; not an actor input.')
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');main(p.parse_args().folder)
