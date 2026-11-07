"""Check compiled source self-contacts along a sensor-derived carrying plan.

This supplements source-triangle clearance with the native collision shapes.
Only the robot predictor and its estimated joints are used. It does not check
the physical payload, body tracking, the room, or continuous execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from ftir_hand import ArmIK


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('recording');parser.add_argument('handoff');parser.add_argument('output')
    args=parser.parse_args()
    run,handoff,out=map(Path,[args.recording,args.handoff,args.output])
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(__file__,out/Path(__file__).name)
    model_file=run/'controller_model/world.xml'
    model=mujoco.MjModel.from_xml_path(str(model_file.resolve()));data=mujoco.MjData(model)
    original_disable_flags=int(model.opt.disableflags)
    # The dynamics predictor disables contacts for speed. A collision screen
    # must explicitly re-enable them in this separate diagnostic model.
    model.opt.disableflags &= ~int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
    ik=ArmIK(model)
    initial=np.load(handoff/'handoff.npz')['robot_estimated_qpos']
    plan=json.loads((handoff/'review.json').read_text())['sampled_arm_plan']
    rows=[]
    for segment in ['raise','retract']:
        for i,q in enumerate(plan[segment+'_path']['joint_path']):
            data.qpos[:]=initial;data.qpos[ik.qa]=q
            mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data)
            mujoco.mj_collision(model,data)
            contacts=[dict(parts=[model.geom(g).name for g in c.geom],
                           bodies=[model.body(model.geom_bodyid[g]).name for g in c.geom],
                           distance_m=float(c.dist)) for c in data.contact]
            rows.append(dict(segment=segment,index=i,contacts=contacts))
    worst=min([c['distance_m'] for r in rows for c in r['contacts']]+[0.])
    report=dict(scope=__doc__,model_sha256=sha(model_file),
                handoff_review_sha256=sha(handoff/'review.json'),
                handoff_state_sha256=sha(handoff/'handoff.npz'),script_sha256=sha(__file__),
                rotation_vector_rad=plan['rotation_vector_rad'],samples=len(rows),
                predictor_disable_flags=original_disable_flags,
                diagnostic_disable_flags=int(model.opt.disableflags),
                source_collision_shapes_and_filters_unchanged=True,
                minimum_distance_m=worst,no_source_contact_penetration=worst>=0.,
                within_existing_20um_self_contact_bound=worst>=-.00002,
                physical_execution=False,qualified_carry=False,rows=rows)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)


if __name__=='__main__':main()
