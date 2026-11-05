"""Diagnose a release posture using recorded geometry and native contact Jacobians.

This is an offline kinematic screen. Perturbed poses are never fed to a running
plant or actor and do not grant manipulation or release qualification.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from build_tool_station import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording',type=Path)
    p.add_argument('model_run',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    result=json.loads((a.recording/'result.json').read_text())
    contract=json.loads((a.model_run/'contract.json').read_text())
    assert sha(a.recording/'trace.npz')==result['trace_sha256']
    assert sha(a.model_run/'contract.json')==result['actor_contract_sha256']
    assert sha(a.model_run/'world.xml')==contract['model_sha256']
    a.output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,a.output/Path(__file__).name)
    m=mujoco.MjModel.from_xml_path(str((a.model_run/'world.xml').resolve()))
    d=mujoco.MjData(m)
    with np.load(a.recording/'trace.npz') as z:
        recorded_q=z['qpos'][-1].copy();recorded_time=float(z['time'][-1])
    joints=[j for j in range(m.njnt) if m.joint(j).name.startswith('right_hand_')]
    def contacts(with_jacobian=False):
        rows=[]
        for c in d.contact:
            bodies=[int(m.geom_bodyid[g]) for g in c.geom]
            names=[m.body(b).name for b in bodies]
            if not any(n.startswith('right_hand_') for n in names):continue
            row=dict(bodies=names,geoms=[m.geom(g).name for g in c.geom],
                     distance_m=float(c.dist),position_m=c.pos.tolist())
            if with_jacobian:
                hand_index=next(i for i,n in enumerate(names) if n.startswith('right_hand_'))
                jp,jr=np.zeros((3,m.nv)),np.zeros((3,m.nv))
                mujoco.mj_jac(m,d,jp,jr,c.pos,bodies[hand_index])
                normal=c.frame[:3]*(1 if hand_index==1 else -1)
                row['hand_separation_jacobian_m_per_rad']={m.joint(j).name:
                    float(normal@jp[:,m.jnt_dofadr[j]]) for j in joints}
            rows.append(row)
        return rows
    d.qpos[:]=recorded_q;mujoco.mj_forward(m,d)
    native=contacts(True)
    rows=[];joint=m.joint('right_hand_middle_0_joint')
    for delta in [0.,-.01,-.02,-.04,-.06,.01,.02]:
        d.qpos[:]=recorded_q;d.qpos[joint.qposadr[0]]+=delta
        mujoco.mj_forward(m,d)
        rows.append(dict(middle_proximal_delta_rad=delta,contacts=contacts(),
            within_source_range=bool(joint.range[0]<=d.qpos[joint.qposadr[0]]<=joint.range[1])))
    monitor=[json.loads(line) for line in (a.recording/'monitor.jsonl').read_text().splitlines()]
    entry=next(row for row in monitor if row['phase']=='release')['hand_commands_rad']
    final=monitor[-1]['hand_commands_rad']
    report=dict(scope=__doc__,trace_sha256=result['trace_sha256'],
        model_sha256=contract['model_sha256'],contract_sha256=sha(a.model_run/'contract.json'),
        script_sha256=sha(__file__),monitor_sha256=sha(a.recording/'monitor.jsonl'),
        recorded_time_s=recorded_time,native_contacts=native,screen=rows,
        release_entry_commands_rad=entry,final_release_commands_rad=final,
        qualification=False)
    (a.output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(native_contacts=native,screen=[dict(
        middle_proximal_delta_rad=r['middle_proximal_delta_rad'],
        contacts=len(r['contacts']),within_source_range=r['within_source_range']) for r in rows])),flush=True)


if __name__=='__main__':main()
