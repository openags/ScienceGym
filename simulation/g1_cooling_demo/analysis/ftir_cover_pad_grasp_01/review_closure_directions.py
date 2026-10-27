import json,sys,numpy as np,fcl,trimesh
from pathlib import Path
sys.path.insert(0,str(Path('viewer/cooling_concept_v2').resolve()))
from source_geometry import hand_manager,set_hand
r=json.load(open('simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_01/pad_grasps.json'));hand=hand_manager('right')
bar=trimesh.creation.cylinder(radius=.004,height=.076,sections=32);T=np.eye(4);T[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0]]);bar.apply_transform(T);cm=trimesh.collision.CollisionManager();cm.add_object('bar',bar);target=cm._objs['bar']['obj']
rows=[]
for j,c in enumerate(r['candidates'][:4]):
 row=dict(candidate=j,tests=[])
 for joint in ['right_index_1_joint','right_thumb_2_joint']:
  part='right_index_force_sensor_3' if 'index' in joint else 'right_thumb_force_sensor_4'
  for delta in [-.02,-.01,0,.01,.02]:
   q=dict(c['q']);q[joint]+=delta;set_hand(hand,'right',q,np.array(c['handle_frame_from_palm']));res=fcl.DistanceResult();fcl.distance(hand._objs[part]['obj'],target,fcl.DistanceRequest(),res);row['tests'].append(dict(joint=joint,delta=delta,pad_gap_m=float(res.min_distance)))
 rows.append(row)
print(json.dumps(rows,indent=2))
Path('simulation/g1_cooling_demo/analysis/ftir_cover_pad_grasp_01/closure_directions.json').write_text(json.dumps(rows,indent=2)+'\n')
