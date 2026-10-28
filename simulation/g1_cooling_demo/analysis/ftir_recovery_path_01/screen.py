"""Compare release/withdraw paths using sensors and source instrument geometry.

Instrument placement comes from retained RGB-D observations. Hinge angles
are an explicit 0..16 degree uncertainty sweep, not recorded device truth.
This hand-clearance screen is not a full-body or physical acceptance test.
"""
import json
from pathlib import Path
import sys

import mujoco
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'simulation/g1_cooling_demo'
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE));sys.path.insert(0,str(ROOT/'viewer/cooling_concept_v2'))
from ftir_cover_actor import CoverActor
from ftir_hand import mimic
from cary_distal_hand import distal_hand_manager
from scipy.spatial.transform import Rotation

run=BASE/'runs/ftir_cover_11'
model=mujoco.MjModel.from_xml_path(str(BASE/'runs/ftir_cover_10/controller_model/world.xml'))
model.opt.disableflags|=int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
actor=CoverActor(model,[5.95,-5.32],ROOT/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json')
sensors=np.load(run/'sensor_observations.npz')
def update(t):
    i=np.argmin(abs(sensors['time_s']-t))
    packet={k:sensors[k][i] for k in sensors.files if k!='right_touch_n'};packet['depth']=None
    actor.estimate.update(packet)
responses=json.loads((run/'actor_responses.json').read_text())
actor.observations=[r['observation'] for r in responses if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
update(2.);actor.make_plan(2.);update(19.3)
current=actor.d.site('right_wrist_reference').xpos.copy()
rotation=actor.d.site('right_wrist_reference').xmat.reshape(3,3).copy()
original_q={n:float(actor.d.joint(n).qpos[0]) for n in actor.open_q}
partial=dict(original_q)
for n in ['right_index_1_joint','right_thumb_2_joint']:
    partial[n]=max(float(model.joint(n).range[0]),partial[n]-.08)
revision=json.loads((ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json').read_text())
scene=trimesh.load(ROOT/revision['geometry_override']['path'],force='scene',process=False)
matrix,key=scene.graph['lid_handle_bar'];bar=scene.geometry[key].copy();bar.apply_transform(matrix)
registration=np.eye(4);registration[:3,:3]=actor.rotation
registration[:3,3]=actor.handle-actor.rotation@bar.centroid
interfaces=json.loads((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_text())
cover=set(next(x for x in interfaces['interfaces'] if x['id']=='sample_cover')['parts'])
obstacles=trimesh.collision.CollisionManager();rest={}
for name in scene.graph.nodes_geometry:
    matrix,key=scene.graph[name];rest[name]=registration@matrix
    obstacles.add_object(name,scene.geometry[key],rest[name])
hand=distal_hand_manager('right');data=mujoco.MjData(model)
variants=[('full_open',actor.open_q,0.),('small_open',partial,0.),('small_open_retreat',partial,.02)]
rows=[]
for label,hand_goal,retreat in variants:
    failures=[];ik_failures=[];seed=actor.d.qpos[actor.ik.qa].copy();samples=0
    for phase in ['release','withdraw']:
        for u in np.linspace(0,1,31):
            smooth=u*u*(3-2*u)
            distance=retreat*smooth if phase=='release' else retreat+(.08-retreat)*smooth
            target=current+actor.front*distance
            q,pe,re=actor.ik.solve(actor.d,target,rotation,seed);seed=q
            if pe>.003 or re>.035:ik_failures.append(dict(phase=phase,u=float(u),position_error_m=pe,rotation_error_rad=re))
            data.qpos[:]=actor.d.qpos;data.qpos[actor.ik.qa]=q
            for name,value in hand_goal.items():
                data.joint(name).qpos[0]=original_q[name]+smooth*(value-original_q[name]) if phase=='release' else value
            mimic(model,data);mujoco.mj_kinematics(model,data)
            for name in hand._objs:
                transform=np.eye(4);transform[:3,:3]=data.body(name).xmat.reshape(3,3);transform[:3,3]=data.body(name).xpos
                hand.set_transform(name,transform)
            for angle in np.arange(0,16.1,2):
                rot=Rotation.from_rotvec(-actor.axis*np.radians(angle)).as_matrix()
                hinge=np.eye(4);hinge[:3,:3]=rot;hinge[:3,3]=actor.pivot-rot@actor.pivot
                for name in cover:obstacles.set_transform(name,hinge@rest[name])
                hit,pairs=hand.in_collision_other(obstacles,return_names=True)
                unintended=[sorted(p) for p in pairs if 'lid_handle_bar' not in p]
                if unintended:failures.append(dict(phase=phase,u=float(u),hinge_angle_deg=float(angle),parts=sorted(unintended)))
                samples+=1
    row=dict(variant=label,source_hand_q=hand_goal,simultaneous_retreat_m=retreat,samples=samples,
             failed_clearance_states=len(failures),failures=failures,ik_failures=ik_failures,
             passed=not failures and not ik_failures)
    rows.append(row);print(label,'failed geometry',len(failures),'IK',len(ik_failures),flush=True)
report=dict(scope=__doc__,sensor_time_s=19.3,hinge_uncertainty_deg=[0,16],angle_step_deg=2,rows=rows,
            physical_qualified=False,limitations=['Hand/instrument only; excludes whole-arm, self and room clearance.',
             'Handle contacts are recorded as permissible during release; no dynamic force or penetration acceptance.',
             'Only one retained sensor posture and bounded hinge-angle hypotheses.'])
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
