"""Replay the retained motor inputs and inspect every cover diagnostic state."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np


def verify(folder):
    folder=Path(folder).resolve(); model=mujoco.MjModel.from_xml_path(str(folder/'cover_probe.xml'))
    data=mujoco.MjData(model); trace=dict(np.load(folder/'cover_probe_trace.npz'))
    imported=json.loads((folder/'laboratory_import.json').read_text())
    labels={model.geom(g).id:part['source_part'] for part in imported['parts'] if part['instance']=='nicolet'
            for g in [part['geom']]+part.get('contact_geoms',[])}
    dynamic={i for i in labels if model.body_weldid[model.geom_bodyid[i]]!=0}
    probe=model.geom('diagnostic_probe_contact').id
    handle=next(g for g,n in labels.items() if n=='lid_handle_bar')
    max_q,max_v=0.,0.;pairs={};violations=[];limits={}
    for i in range(len(trace['qpos'])):
        max_q=max(max_q,float(np.max(abs(data.qpos-trace['qpos'][i]))))
        max_v=max(max_v,float(np.max(abs(data.qvel-trace['qvel'][i]))))
        data.ctrl[:]=trace['ctrl'][i]
        mujoco.mj_step(model,data)
        if np.any(data.xfrc_applied) or np.any(data.qfrc_applied):raise ValueError('Unexpected externally applied force')
        for c in data.contact:
            a,b=map(int,c.geom)
            if a not in dynamic and b not in dynamic:continue
            if set((a,b))=={probe,handle}:continue
            key=tuple(sorted([labels.get(a,model.geom(a).name),labels.get(b,model.geom(b).name)]))
            pairs[key]=min(pairs.get(key,0),float(c.dist))
            if c.dist < -2e-6:violations.append(dict(time_s=float(data.time),pair=list(key),distance_m=float(c.dist)))
        for j in range(model.njnt):
            if not model.joint(j).name.startswith('nicolet_'):continue
            q=float(data.qpos[model.jnt_qposadr[j]]);lo,hi=model.jnt_range[j]
            limits[model.joint(j).name]=max(limits.get(model.joint(j).name,0),float(max(lo-q,q-hi,0)))
    device_bodies={model.jnt_bodyid[j] for j in range(model.njnt) if model.joint(j).name.startswith('nicolet_')}
    motors_only_probe=all(model.body(model.jnt_bodyid[int(model.actuator_trnid[a,0])]).name=='diagnostic_probe' for a in range(model.nu))
    checks=dict(exact_motor_replay=max_q<1e-9 and max_v<1e-8,
                no_unintended_device_penetration=not violations, only_diagnostic_probe_actuated=motors_only_probe,
                no_runtime_numerical_warnings=not np.any(data.warning.number),
                passive_stops_respected=all(e < (np.deg2rad(.5) if name.endswith('hinge') else .00005) for name,e in limits.items()))
    report=dict(passed=all(checks.values()), checks=checks, states=len(trace['qpos']),
                maximum_replay_q_error=max_q, maximum_replay_velocity_error=max_v,
                nonprobe_pairs=[dict(parts=list(k),minimum_distance_m=v) for k,v in pairs.items()],
                joint_limit_excess=limits, unintended_contact_states=len(violations), first_violations=violations[:20],
                model_sha256=hashlib.sha256((folder/'cover_probe.xml').read_bytes()).hexdigest(),
                trace_sha256=hashlib.sha256((folder/'cover_probe_trace.npz').read_bytes()).hexdigest(),
                scope='Contact-driven device diagnostic only; no robot manipulation or reliability qualification')
    (folder/'cover_motor_replay.json').write_text(json.dumps(report,indent=2)+'\n')
    shutil.copyfile(__file__,folder/'verify_ftir_trace.py');print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
    if not verify(a.folder)['passed']:raise SystemExit(1)
