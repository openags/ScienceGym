import json,sys,numpy as np,mujoco,itertools,cv2
from pathlib import Path
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(Path('simulation/g1_cooling_demo').resolve()))
from ftir_hand import initialize,ArmIK
from ftir_vision import KeyRowObservation
b=Path('simulation/g1_cooling_demo/runs/ftir_cover_01')
m=mujoco.MjModel.from_xml_path(str((b/'world.xml').resolve()));cm=mujoco.MjModel.from_xml_path(str((b/'controller_model/world.xml').resolve()));ik=ArmIK(cm)
cr=mujoco.Renderer(m,360,640,max_geom=m.ngeom+1000);dr=mujoco.Renderer(m,180,320,max_geom=m.ngeom+1000);dr.enable_depth_rendering();opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.sitegroup[:]=0
prior=json.load(open('assets/nicolet_6700_mechanism_v1/cover_grasp_prior.json'));G=np.array(prior['handle_frame_from_palm']);normal=-np.array(prior['keys'][0]['inward_axis']);row=np.array([1.,0,0]);basis=lambda r,n:np.column_stack([r,np.cross(n,r),n]);src=np.array([k['center_m'] for k in prior['keys']])+normal*.00075
rows=[]
for x,y,pitch,yaw in [(5.83,-5.45,p,y) for p,y in itertools.product([-.3,-.35],[0.,-.15])]+[(5.95,-5.35,-.2,-.2)]:
 d=initialize(m,(x,y));cd=initialize(cm,(x,y))
 for dd,mm in [(d,m),(cd,cm)]:
  dd.joint('waist_pitch_joint').qpos[0]=pitch;dd.joint('waist_yaw_joint').qpos[0]=yaw;mujoco.mj_forward(mm,dd)
 cr.update_scene(d,camera='head_rgb',scene_option=opt);rgb=cr.render().copy();dr.update_scene(d,camera='head_depth',scene_option=opt);dep=dr.render().copy()
 o=KeyRowObservation(cm,cd).observe(rgb,dep);result=dict(x=x,y=y,pitch=pitch,yaw=yaw,observation=o)
 if o.get('accepted'):
  on=np.array(o['outward_normal']);rr=np.array(o['row_direction']);R=basis(rr,on)@basis(row,normal).T;tr=np.mean(np.array([o['buttons'][k['label']] for k in prior['keys']])-src@R.T,axis=0);h=tr+R@np.array(prior['closed_handle_center_m']);p=tr+R@np.array(prior['hinge_pivot_m']);tp=h+R@G[:3,3];rot=R@G[:3,:3];seed=cd.qpos[ik.qa].copy();valid=[]
  for a in np.linspace(0,-np.pi/3,31):
   ar=Rotation.from_rotvec(R[:,0]*a).as_matrix();seed,pe,re=ik.solve(cd,p+ar@(tp-p),ar@rot,seed)
   if pe>.003 or re>.035:break
   valid.append(a)
  result['arc_valid_degrees']=float(-valid[-1]*180/np.pi) if valid else -1;result['last_errors']=[pe,re]
 rows.append(result)
 print(json.dumps(result),flush=True)
 cv2.imwrite('/tmp/cover_view_'+str(len(rows))+'.png',cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR))
cr.close();dr.close()
out=Path('simulation/g1_cooling_demo/analysis/ftir_cover_reach_01');(out/'camera_and_arm_candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
