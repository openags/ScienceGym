import json,sys,numpy as np,mujoco,trimesh
from pathlib import Path
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root/'simulation/g1_cooling_demo'));sys.path.insert(0,str(root/'viewer/cooling_concept_v2'))
from ftir_cover_actor import CoverActor
from source_geometry import fk
from cary_distal_hand import distal_hand_manager
class RollingActor(CoverActor):
 def arc(self,u):
  theta=np.pi/3*u;rot=Rotation.from_rotvec(-self.axis*theta).as_matrix();handle=self.pivot+rot@(self.handle-self.pivot)
  palm_rot=Rotation.from_rotvec(-self.axis*(theta-np.pi/12*np.tanh(theta/(np.pi/12)))).as_matrix()
  return handle+palm_rot@(self.grip_position-self.handle),palm_rot@self.grip_rotation
base=json.load(open(root/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'));interfaces=json.load(open(root/'assets/nicolet_6700_v1/interfaces.json'))
cover=next(i for i in interfaces['interfaces'] if i['id']=='sample_cover');parts=set(cover['parts']);pivot=np.array(cover['pivot_m']);handle=np.array(base['closed_handle_center_m']);G=np.array(base['handle_frame_from_palm'])
lab=json.load(open(root/'viewer/cooling_concept_v2/runtime_scene.json'))
normal=np.array(next(a for a in lab['assets'] if a['id']=='nicolet')['normalization_matrix'])
# The passive GLB is already normalized; interfaces remain source-relative.
pivot=(normal@np.r_[pivot,1.])[:3];handle=(normal@np.r_[handle,1.])[:3]
revision=json.load(open(root/'assets/nicolet_6700_mechanism_v1/revisions/passive_dynamics/revision.json'));scene=trimesh.load(root/revision['geometry_override']['path'],force='scene',process=False);obstacles=trimesh.collision.CollisionManager();transforms={}
for name in scene.graph.nodes_geometry:
 T,key=scene.graph[name];transforms[name]=T;obstacles.add_object(name,scene.geometry[key],T)
hand=distal_hand_manager('right');robot=fk(base['nominal_grip_q']);inverse=np.linalg.inv(robot['right_palm_force_sensor']);local={n:inverse@robot[n] for n in hand._objs};rows=[]
for angle in np.linspace(0,-np.pi/3,121):
 rot=Rotation.from_rotvec(np.array([1.,0,0])*angle).as_matrix();H=np.eye(4);H[:3,:3]=rot;H[:3,3]=pivot-rot@pivot
 for name in parts:obstacles.set_transform(name,H@transforms[name])
 theta=-angle;palm_rot=Rotation.from_rotvec(np.array([-1.,0,0])*(theta-np.pi/12*np.tanh(theta/(np.pi/12)))).as_matrix()
 palm=G.copy();palm[:3,:3]=palm_rot@G[:3,:3];palm[:3,3]=pivot+rot@(handle-pivot)+palm_rot@G[:3,3]
 for name,T in local.items():hand.set_transform(name,palm@T)
 hit,pairs,contacts=hand.in_collision_other(obstacles,return_names=True,return_data=True)
 rows.append(dict(angle_rad=float(angle),collision=hit,pairs=[list(p) for p in sorted(pairs)],maximum_triangle_contact_depth_m=max([abs(float(c.depth)) for c in contacts],default=0.)))
b=root/'simulation/g1_cooling_demo/runs/ftir_cover_08';m=mujoco.MjModel.from_xml_path(str(b/'controller_model/world.xml'));s=np.load(b/'sensor_observations.npz');i=np.argmin(abs(s['time_s']-2));packet={k:s[k][i] for k in s.files if k!='right_touch_n'};packet['depth']=None
obs=[r['observation'] for r in json.load(open(b/'actor_responses.json')) if r['time_s']<=2.001 and r.get('observation') and r['observation'].get('handle_fit',{}).get('accepted')][-8:]
a=RollingActor(m,[5.95,-5.35],root/'assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json');a.estimate.update(packet);a.observations=obs
try:a.make_plan(2);reach=dict(passed=True,event=a.events[-1])
except Exception as error:reach=dict(passed=False,error=str(error))
report=dict(scope='Source nominal-hand clearance with rolling limited smoothly to 15 degrees and observed robot-only IK. Normalization applied to both source interfaces. No physical qualification.',geometry=rows,reach=reach,collision_states=sum(r['collision'] for r in rows));(Path(__file__).parent/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(reach=reach,collision_states=report['collision_states'],first_collisions=[r for r in rows if r['collision']][:3])))
