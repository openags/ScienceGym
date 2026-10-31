"""Recompute RTD support and cable integrity from the recorded physical trace."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
from device_assets import load
from support_observation import support_load
from world import HERE


def verify(directory):
    directory=Path(directory);report=json.loads((directory/'result.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks=[]
    def check(name,passed,**values):checks.append(dict(name=name,passed=bool(passed),**values))
    check('completed_execution',report['status']=='passed',status=report['status'],failure=report['failure'])
    source_root=directory/report['source_archive'] if report.get('source_archive') else HERE
    changed=[name for name,digest in report['input_sha256'].items() if sha(directory/name if name=='workcell.xml' else source_root/name)!=digest]
    check('input_pins',not changed,changed=changed)
    changed=[name for name,digest in report['artifacts_sha256'].items() if sha(directory/name)!=digest]
    check('artifact_pins',not changed,changed=changed)
    model=load(directory/'workcell.xml');model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_WARMSTART);data=mujoco.MjData(model)
    with np.load(directory/'physics_trace.npz') as compressed:
        trace={key:compressed[key] for key in compressed.files}
    times=trace['time']
    check('finite_trace',all(np.isfinite(trace[k]).all() for k in ['time','qpos','qvel','ctrl']))
    check('continuous_time',np.all(np.diff(times)>0) and np.max(np.diff(times))<.01001,
          max_interval_s=float(np.max(np.diff(times))))
    releases=[x for x in report['observations'] if x['label']=='rtd_released_support']
    lifts=[x for x in report['observations'] if x['label']=='grasp_and_lift_observed']
    check('two_distinct_transfers',len(releases)==2 and len(lifts)==2 and
          [x['support'] for x in releases]==['calibration_block','rtd_stand'])
    for event in releases:
        index=int(np.argmin(abs(times-event['time_s'])))
        data.qpos[:]=trace['qpos'][index];data.qvel[:]=trace['qvel'][index];data.ctrl[:]=trace['ctrl'][index]
        mujoco.mj_forward(model,data)
        expected=np.array(report['configuration']['target_m' if event['support']=='calibration_block' else 'park_m'])
        error=float(np.linalg.norm(data.body('rtd').xpos-expected))
        tilt=float(np.arccos(np.clip(data.body('rtd').xmat[8],-1,1)))
        load_obs=support_load(model,data,'rtd',event['support'])
        own_weight=float(model.body('rtd').mass[0])*9.81
        finger_force=0.
        for i,c in enumerate(data.contact):
            if min(c.geom)<0:continue
            names={model.body(int(model.geom_bodyid[g])).name for g in c.geom}
            if 'rtd' in names and names&{'left_finger','right_finger'}:
                f=np.zeros(6);mujoco.mj_contactForce(model,data,i,f);finger_force+=f[0]
        check('released_'+event['support'],error<.001 and tilt<.02 and
              load_obs['vertical_force_n']>.8*own_weight and finger_force<.01,
              time_s=float(times[index]),error_m=error,tilt_rad=tilt,vertical_support_N=load_obs['vertical_force_n'],
              rigid_probe_weight_N=own_weight,finger_force_N=float(finger_force))
    joint=model.joint('rtd_free');address=joint.qposadr[0]
    positions=trace['qpos'][:,address:address+3]
    speed=np.linalg.norm(np.diff(positions,axis=0),axis=1)/np.diff(times)
    check('no_sampled_payload_jump',speed.max()<1.,max_sampled_speed_m_s=float(speed.max()))
    check('no_grasp_weld',not any(model.eq_type[i]==mujoco.mjtEq.mjEQ_WELD for i in range(model.neq)))
    if model.nflex:
        edge=model.flexedge_length0
        check('full_cable_rest_length',abs(float(edge.sum())-3.6576)<1e-5,rest_length_m=float(edge.sum()))
        maximum=0.;worst_time=0.
        # Kinematics and edge lengths do not need contact solving. Inspect
        # every saved sample instead of hiding brief extension spikes.
        for index in range(len(times)):
            data.qpos[:]=trace['qpos'][index]
            mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data);mujoco.mj_flex(model,data)
            strain=float(np.max(np.abs(data.flexedge_length/edge-1)))
            if strain>maximum:maximum=strain;worst_time=float(times[index])
        check('inextensible_cable_approximation',maximum<.01,max_edge_strain=maximum,worst_time_s=worst_time)
    else:
        cable=[i for i in range(model.ngeom) if (model.geom(i).name or '').startswith('rtd_lead_G')]
        length=float(2*model.geom_size[cable,1].sum())
        check('full_elastic_rod_length',len(cable)==report['configuration']['cable_segments'] and abs(length-3.6576)<1e-5,
              rest_length_m=length,segments=len(cable))
        check('elasticity_plugin_present',model.nplugin==1)
        # This rigid-link rod has fixed segment lengths. Verify its serial
        # topology and attachment to the probe instead of applying a flex
        # strain formula to a model with no flex vertices.
        bodies=[int(model.geom_bodyid[i]) for i in cable]
        check('rod_attached_serial_chain',bool(bodies) and model.body_parentid[bodies[0]]==model.body('rtd').id and
              all(model.body_parentid[b]==a for a,b in zip(bodies,bodies[1:])))
    check('limited_gripper_commands',np.max(np.abs(trace['ctrl'][:,7]))<=40.000001)
    result=dict(passed=all(c['passed'] for c in checks),checks=checks,
        scope='Two continuous cabled RTD transfers. No bath immersion, four-wire connection, calibrated temperature or full-paper credit.',
        verifier_sha256=sha(Path(__file__)),result_sha256=sha(directory/'result.json'),engine_version=mujoco.__version__,
        whole_paper_validated=False)
    (directory/'verification.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');args=parser.parse_args();result=verify(args.directory)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
