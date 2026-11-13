"""Kinematic poses for the authored presentation, not a dynamics controller."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,mujoco
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];asset=ROOT/'assets/unitree_g1_inspire_v1';xml=ET.parse(asset/'simulation/robot.xml').getroot();xml.find('compiler').set('meshdir',str(asset))
for side in ['left','right']:
 ET.SubElement(xml.find(f".//body[@name='{side}_palm_force_sensor']"),'site',name=side+'_palm')
 ET.SubElement(xml.find(f".//body[@name='{side}_ankle_roll_link']"),'site',name=side+'_sole',pos='.025 0 -.0354')
m=mujoco.MjModel.from_xml_string(ET.tostring(xml,encoding='unicode'));d=mujoco.MjData(m);d.qpos[2]=.7922728974794127-.025;mujoco.mj_kinematics(m,d)
rest={}
for side,sign in [('left',1),('right',-1)]:
 rest.update({side+'_shoulder_pitch_joint':1.0,side+'_shoulder_roll_joint':sign*.3,side+'_elbow_joint':0})
poses={'rest':rest};errors={}
for name,x,span,z in [('work',.43,.15,1.055),('carry',.40,.19,1.04),('push',.39,.18,.94),('inspect',.35,.12,1.13),('low',.42,.16,.95),('lid',.44,.12,1.20)]:
 pose={}
 for side,sign in [('left',1),('right',-1)]:
  names=[side+'_'+j+'_joint' for j in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']];idx=[m.joint(n).qposadr[0] for n in names];limits=np.array([m.joint(n).range for n in names]);sid=m.site(side+'_palm').id
  d.qpos[7:]=0;mujoco.mj_kinematics(m,d);rotation=Rotation.from_euler('x',-45*sign,degrees=True).as_matrix()@d.site_xmat[sid].reshape(3,3);target=np.array([x,sign*span,z]);start=np.array([-1.,sign*.1,0.,.8,0.,.2,0.])
  if name in ['work','low','push','inspect','lid']:
   finger=d.site_xmat[sid].reshape(3,3).T@(d.body(side+'_index_force_sensor_3').xpos-d.site_xpos[sid]);finger[2]=0;finger/=np.linalg.norm(finger);normal=np.array([0.,0.,1.]);local=np.column_stack([finger,np.cross(normal,finger),normal]);forward=np.array([1.,0.,0.]);normal=np.array([0.,0.,-1.]);desired=np.column_stack([forward,np.cross(normal,forward),normal]);rotation=desired@local.T
  def fun(q):
   d.qpos[idx]=q;mujoco.mj_kinematics(m,d);rot=Rotation.from_matrix(rotation@d.site_xmat[sid].reshape(3,3).T).as_rotvec();return np.r_[8*(d.site_xpos[sid]-target),.15*rot,.018*(q-start)]
  result=least_squares(fun,start,bounds=(limits[:,0]+1e-5,limits[:,1]-1e-5),max_nfev=150);pose.update(dict(zip(names,map(float,result.x))));fun(result.x);errors[name+'_'+side]=float(np.linalg.norm(d.site_xpos[sid]-target))
 poses[name]=pose
# Grounded sagittal foot paths; authored walk cycle remains purely kinematic.
gait=[]
for phase in np.linspace(0,1,65):
 q={}
 for side,shift in [('left',0),('right',.5)]:
  u=(phase+shift)%1
  if u<.62:xx=.17-.34*u/.62;zz=0
  else:
   a=(u-.62)/.38;xx=-.17+.34*(a*a*(3-2*a));zz=.065*np.sin(np.pi*a)
  names=[side+'_'+j+'_joint' for j in ['hip_pitch','knee','ankle_pitch']];idx=[m.joint(n).qposadr[0] for n in names];limits=np.array([m.joint(n).range for n in names]);sid=m.site(side+'_sole').id
  d.qpos[7:]=0
  def fun(v):
   d.qpos[idx]=v;mujoco.mj_kinematics(m,d);R=d.site_xmat[sid].reshape(3,3);pitch=np.arctan2(-R[2,0],R[0,0]);return [d.site_xpos[sid,0]-(.025+xx),d.site_xpos[sid,2]-zz,.3*pitch]
  r=least_squares(fun,[-.2,.4,-.2],bounds=(limits[:,0]+1e-5,limits[:,1]-1e-5),max_nfev=70);q.update(dict(zip(names,map(float,r.x))))
 gait.append(q)
stance={}
for side in ['left','right']:
 names=[side+'_'+j+'_joint' for j in ['hip_pitch','knee','ankle_pitch']];idx=[m.joint(n).qposadr[0] for n in names];limits=np.array([m.joint(n).range for n in names]);sid=m.site(side+'_sole').id;d.qpos[7:]=0
 def neutral(v):
  d.qpos[idx]=v;mujoco.mj_kinematics(m,d);R=d.site_xmat[sid].reshape(3,3);return [d.site_xpos[sid,0]-.025,d.site_xpos[sid,2],.3*np.arctan2(-R[2,0],R[0,0])]
 r=least_squares(neutral,[-.2,.4,-.2],bounds=(limits[:,0]+1e-5,limits[:,1]-1e-5));stance.update(dict(zip(names,map(float,r.x))))
poses['stance']=stance
out=dict(kind='authored_kinematic_presentation',root_z_offset_m=-.025,poses=poses,gait=gait,arm_target_errors_m=errors)
from source_geometry import robot_meshes
out['sole_vertices_m']={name:mesh.convex_hull.vertices.tolist() for name,mesh in robot_meshes().items() if name.endswith('ankle_roll_link')}
(Path(__file__).parent/'motion_poses.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(errors))
