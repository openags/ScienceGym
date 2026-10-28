"""Source-hand alignment/lift clearance and observed robot-only arm preflight."""
import hashlib,json,sys,numpy as np,mujoco,trimesh
from pathlib import Path
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'simulation/g1_cooling_demo'));sys.path.insert(0,str(ROOT/'viewer/cooling_concept_v2'))
from ftir_cover_actor import CoverActor
from source_geometry import fk
from cary_distal_hand import distal_hand_manager

run=ROOT/'simulation/g1_cooling_demo/runs/ftir_cover_09'
m=mujoco.MjModel.from_xml_path(str(run/'controller_model/world.xml'));s=np.load(run/'sensor_observations.npz');i=np.argmin(abs(s['time_s']-2))
packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None
obs=[r['observation'] for r in json.load(open(run/'actor_responses.json')) if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
base=json.load(open(ROOT/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'))
search=HERE/'pad_grasps.json';candidates=json.load(open(search))['candidates']
interfaces=json.load(open(ROOT/'assets/nicolet_6700_v1/interfaces.json'));cover=next(i for i in interfaces['interfaces'] if i['id']=='sample_cover')
scene_info=json.load(open(ROOT/'viewer/cooling_concept_v2/runtime_scene.json'));normal=np.array(next(a for a in scene_info['assets'] if a['id']=='nicolet')['normalization_matrix'])
pivot=(normal@np.r_[cover['pivot_m'],1])[:3];handle=(normal@np.r_[base['closed_handle_center_m'],1])[:3]
revision=json.load(open(ROOT/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json'))
scene=trimesh.load(ROOT/revision['geometry_override']['path'],force='scene',process=False)
obstacles=trimesh.collision.CollisionManager();rest={}
for name in scene.graph.nodes_geometry:
 T,key=scene.graph[name];rest[name]=T;obstacles.add_object(name,scene.geometry[key],T)
hand=distal_hand_manager('right');rows=[]
(HERE/'priors').mkdir(exist_ok=True)
for index,c in enumerate(candidates[:3]):
 prior=dict(base,handle_frame_from_palm=c['handle_frame_from_palm'],nominal_grip_q=c['q'],
   pad_grasp={k:c[k] for k in ['pad_parts','pad_gaps_m','opposition_dot','projected_pad_margin_m','pad_exposed_contact']},
   grasp_origin=f'Central exposed-source-pad search 06 candidate {index}; physical execution unqualified.',
   source_hashes={'assets/nicolet_6700_v1/interfaces.json':hashlib.sha256((ROOT/'assets/nicolet_6700_v1/interfaces.json').read_bytes()).hexdigest(),str(search.relative_to(ROOT)):hashlib.sha256(search.read_bytes()).hexdigest()})
 path=HERE/'priors'/f'{index:02d}.json';path.write_text(json.dumps(prior,indent=2)+'\n')
 actor=CoverActor(m,[5.95,-5.35],path);actor.estimate.update(packet);actor.observations=obs
 try:actor.make_plan(2);reach=dict(passed=True,event=actor.events[-1])
 except Exception as error:reach=dict(passed=False,error=str(error))
 failures=[];G=np.array(c['handle_frame_from_palm'])
 for phase in ['align','lift']:
  for u in np.linspace(0,1,121):
   palm=G.copy();palm[:3,3]+=handle;H=np.eye(4)
   if phase=='align':
    palm[:3,3]+=np.array([0,-.06*(1-u),0]);q={n:actor.open_q[n]+u*(v-actor.open_q[n]) for n,v in c['q'].items()}
   else:
    angle=np.pi/3*u;R=Rotation.from_rotvec([-angle,0,0]).as_matrix();H[:3,:3]=R;H[:3,3]=pivot-R@pivot
    wrist=Rotation.from_rotvec([-(angle-np.pi/12*np.tanh(angle/(np.pi/12))),0,0]).as_matrix()
    palm[:3,:3]=wrist@G[:3,:3];palm[:3,3]=pivot+R@(handle-pivot)+wrist@G[:3,3];q=c['q']
   for name in cover['parts']:obstacles.set_transform(name,H@rest[name])
   frames=fk(q);transform=palm@np.linalg.inv(frames['right_palm_force_sensor'])
   for name in hand._objs:hand.set_transform(name,transform@frames[name])
   hit,pairs=hand.in_collision_other(obstacles,return_names=True)
   if hit:failures.append(dict(phase=phase,u=float(u),parts=[list(p) for p in sorted(pairs)]))
 row=dict(candidate=index,reach=reach,nominal_source_alignment_and_lift_clear=not failures,failures=failures,
          prior_path=str(path.relative_to(ROOT)),prior_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 rows.append(row);print(json.dumps(dict(candidate=index,reach=reach.get('passed'),reach_error=reach.get('error'),failed_clearance_states=len(failures),first_failures=failures[:2])),flush=True)
(HERE/'path_review.json').write_text(json.dumps(dict(scope=__doc__,source_normalization_applied=True,rows=rows,
 limitations=['Nominal lift posture, not loaded finger deformation.','Closing contacts and complete-body/environment clearance require physical review.'],qualified=False),indent=2)+'\n')
