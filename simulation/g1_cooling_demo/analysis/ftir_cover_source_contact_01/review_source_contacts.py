import json,numpy as np,mujoco,trimesh,fcl
from pathlib import Path
b=Path('simulation/g1_cooling_demo/runs/ftir_cover_03');m=mujoco.MjModel.from_xml_path(str((b/'world.xml').resolve()));d=mujoco.MjData(m);trace=np.load(b/'trace.npz');imported=json.load(open(b/'laboratory_import.json'));bar=next(r['geom'] for r in imported['parts'] if r['instance']=='nicolet' and r['source_part']=='lid_handle_bar')
names=[bar,'right_index_2_collision_0','right_thumb_4_collision_0']+[f'right_index_force_sensor_{i}_collision_0' for i in range(1,4)]+[f'right_thumb_force_sensor_{i}_collision_0' for i in range(1,5)]
manager=trimesh.collision.CollisionManager();volumes={}
for name in names:
 g=m.geom(name).id;mesh=m.geom_dataid[g];v=m.mesh_vert[m.mesh_vertadr[mesh]:m.mesh_vertadr[mesh]+m.mesh_vertnum[mesh]];f=m.mesh_face[m.mesh_faceadr[mesh]:m.mesh_faceadr[mesh]+m.mesh_facenum[mesh]];shape=trimesh.Trimesh(v,f,process=False);manager.add_object(name,shape);volumes[name]=dict(source_volume_m3=float(shape.volume),hull_volume_m3=float(shape.convex_hull.volume))
rows=[]
for t in [14.5,15.,16.,17.4]:
 i=np.argmin(abs(trace['time']-t));d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
 for name in names:
  tr=np.eye(4);tr[:3,:3]=d.geom(name).xmat.reshape(3,3);tr[:3,3]=d.geom(name).xpos;manager.set_transform(name,tr)
 pairs=[]
 for a,c in [(n,bar) for n in names if n!=bar]+[('right_index_2_collision_0','right_thumb_4_collision_0')]:
  result=fcl.DistanceResult();fcl.distance(manager._objs[a]['obj'],manager._objs[c]['obj'],fcl.DistanceRequest(enable_nearest_points=True),result)
  pairs.append(dict(parts=[a,c],source_gap_m=float(result.min_distance)))
 row=dict(time_s=float(trace['time'][i]),pairs=pairs);rows.append(row);print(json.dumps(row),flush=True)
out=Path('simulation/g1_cooling_demo/analysis/ftir_cover_source_contact_01');out.mkdir(exist_ok=False);(out/'source_review.json').write_text(json.dumps(dict(scope='Held-out exact source triangle distances at failed physical attempt states; not an actor input.',rows=rows,volumes=volumes),indent=2)+'\n')
