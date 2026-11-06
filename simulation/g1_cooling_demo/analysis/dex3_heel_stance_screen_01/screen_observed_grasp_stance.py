"""Screen authored stance offsets against a sensor-derived tool grasp target.

Only recorded robot sensors, independently fitted image hypotheses, and the
actor's public model are read. Hypothetical stance offsets are not robot motion
or a clearance check. Every selected setup still needs fresh camera observations,
full scene contact checks and continuous physical execution.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from observations import StateEstimate
from ftir_hand import ArmIK
from verify_tool_grasp import sha


def run(recording,candidate,replay,output):
    recording,candidate,replay,output=map(lambda x:Path(x).resolve(),[recording,candidate,replay,output])
    result=json.loads((recording/'result.json').read_text());receipt=json.loads((replay/'result.json').read_text())
    assert receipt['source_result_sha256']==sha(recording/'result.json')
    assert receipt['actor_contract_sha256']==sha(candidate/'contract.json')
    assert result['sensors_sha256']==sha(recording/'sensors.npz')
    iso=json.loads((candidate/'actor_isolation.json').read_text());assert iso['passed']
    for n in ['observations.py','ftir_hand.py']:assert sha(Path(__file__).with_name(n))==iso['source_modules'][n]
    model_path=candidate/'actor_bundle/model/world.xml'
    assert sha(model_path)==iso['bundled_model_sha256']
    prior=json.loads((candidate/'actor_bundle/model/policy/tool_prior.json').read_text())
    m=mujoco.MjModel.from_xml_path(str(model_path));d=mujoco.MjData(m);d.qpos[:]=prior['initial_robot_qpos'];mujoco.mj_forward(m,d)
    estimate=StateEstimate(m,d)
    with np.load(recording/'sensors.npz') as sensors:
        for i in range(len(sensors['time_s'])):
            packet={k:sensors[k][i] for k in ['time_s','joint_position','joint_velocity','imu_quaternion','imu_gyro']}
            estimate.update(dict(packet,depth=None))
    initial=d.qpos.copy();grasp=prior['grasp_geometry']
    def midpoint():
        w=d.site('right_wrist_reference')
        pts=np.asarray([d.body(x['body']).xpos+d.body(x['body']).xmat.reshape(3,3)@np.asarray(x['point_local_m']) for x in grasp['robot_contact_features']])
        return w.xmat.reshape(3,3).T@(np.asarray([.5,.25,.25])@pts-w.xpos)
    for n,v in grasp['grasp_hand_q'].items():d.joint(n).qpos[0]=v
    mujoco.mj_forward(m,d);closed=midpoint()
    for n,v in grasp['pregrasp_hand_q'].items():d.joint(n).qpos[0]=v
    mujoco.mj_forward(m,d);correction=midpoint()-closed
    events=json.loads((replay/'events.json').read_text());event=next(x for x in events if x.get('kind')=='observed_tool_pose_ambiguity')
    ik=ArmIK(m);ik.low[3]=max(ik.low[3],.15)
    seeds=[initial[ik.qa],[-.8,-.3,.5,.7,0.,.8,.3],[-.8,-.5,0.,1.4,0.,0.,0.],
           [-.6,-.4,-1.5,1.2,1.5,0.,0.],[-.6,-.5,0.,1.2,-1.5,0.,0.],[-1.,-.3,1.5,1.5,1.,0.,0.]]
    rows=[]
    for pose_index,attempt in enumerate(event['attempts']):
        pose=attempt['pose'];T=np.eye(4);T[:3,:3]=pose['rotation_matrix'];T[:3,3]=pose['position_m']
        target=T@np.asarray(grasp['source_tool_from_wrist']);target[:3,3]-=target[:3,:3]@correction
        for dx in np.arange(-.08,.0801,.02):
            for dy in [-.04,-.02,0.,.02,.04]:
                d.qpos[:]=initial;d.qpos[:2]+=[dx,dy];mujoco.mj_forward(m,d)
                solutions=[ik.solve(d,target[:3,3],target[:3,:3],np.clip(q,ik.low,ik.high)) for q in seeds]
                q,pe,re=min(solutions,key=lambda x:x[1]+.15*x[2])
                rows.append(dict(hypothesis_index=pose_index,base_offset_m=[float(dx),float(dy)],
                    position_error_m=pe,rotation_error_rad=re,arm_q=q.tolist(),passed_ik=pe<.0005 and re<.01))
    good=sorted([x for x in rows if x['passed_ik']],key=lambda x:(np.linalg.norm(x['base_offset_m']),x['position_error_m']))
    output.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,output/Path(__file__).name)
    report=dict(scope=__doc__,source_result_sha256=sha(recording/'result.json'),candidate_contract_sha256=sha(candidate/'contract.json'),
        source_sensor_sha256=result['sensors_sha256'],source_events_sha256=sha(replay/'events.json'),
        actor_model_sha256=sha(model_path),script_sha256=sha(__file__),estimated_original_base_qpos=initial[:7].tolist(),
        tested=len(rows),accepted_count=len(good),selected=good[0] if good else None,rows=rows,
        physical_execution=False,collision_checked=False,qualified_approach=False)
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['tested','accepted_count','selected']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['recording','candidate','replay','output']:p.add_argument(n)
    a=p.parse_args();run(a.recording,a.candidate,a.replay,a.output)
