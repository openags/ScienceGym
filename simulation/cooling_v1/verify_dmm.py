"""Recompute key travel and contact from the saved device-workcell trace."""
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from world import HERE
from device_assets import load


def main():
    path=HERE/'runs/dmm';receipt=json.loads((path/'result.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
    for filename,pin in receipt['input_sha256'].items():
        p=path/filename if filename=='workcell.xml' else HERE/filename
        checks.append(dict(case='input:'+filename,passed=sha(p)==pin))
    for filename,pin in receipt['artifacts_sha256'].items():checks.append(dict(case='artifact:'+filename,passed=sha(path/filename)==pin))
    m=load(path/'workcell.xml');d=mujoco.MjData(m);trace=np.load(path/'physics_trace.npz')
    target=m.joint('button_Ω4_travel').qposadr[0];q=trace['qpos'];index=int(np.argmax(q[:,target]))
    d.qpos[:]=q[index];d.qvel[:]=trace['qvel'][index];d.ctrl[:]=trace['ctrl'][index];mujoco.mj_forward(m,d)
    loaded=False;forces=[]
    for i,c in enumerate(d.contact):
        names={m.body(int(m.geom_bodyid[g])).name for g in c.geom}
        if names=={'button_Ω4','button_probe'}:
            force=np.zeros(6);mujoco.mj_contactForce(m,d,i,force);forces.append(float(force[0]));loaded|=force[0]>.01
    checks.append(dict(case='target_pressed_by_tool_contact',passed=bool(q[index,target]>.00075 and loaded),
                       travel_m=float(q[index,target]),normal_forces_n=forces,time_s=float(trace['time'][index])))
    others=[]
    for i in range(m.njnt):
        name=m.joint(i).name
        if name.startswith('button_') and name!='button_Ω4_travel':others.append(float(np.max(np.abs(q[:,m.jnt_qposadr[i]]))))
    checks.append(dict(case='other_keys_not_pressed',passed=max(others)<.00025,max_other_travel_m=max(others)))
    checks.append(dict(case='target_returned',passed=bool(abs(q[-1,target])<.0001),final_travel_m=float(q[-1,target])))
    # The physical and visual Ω4 cap must occupy the same panel location.
    geom=m.geom('button_Ω4_key_Ω4').id;body=m.body('button_Ω4').id
    distance=float(np.linalg.norm(d.geom_xpos[geom]-d.xpos[body]))
    checks.append(dict(case='visual_physical_panel_alignment',passed=distance<.003,center_difference_m=distance))
    result=dict(passed=receipt['status']=='passed' and all(c['passed'] for c in checks),checks=checks,
                receipt_sha256=sha(path/'result.json'),verifier_sha256=sha(Path(__file__)),whole_paper_validated=False,
                scope='Physical Ω4 key actuation and release, no neighbouring-key press; not electrical calibration')
    (HERE/'DMM_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
