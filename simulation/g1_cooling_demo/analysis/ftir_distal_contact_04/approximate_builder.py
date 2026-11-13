import sys,json,hashlib,time,importlib.metadata
from pathlib import Path
import coacd,trimesh,numpy as np
root=Path('/home/amax/data/media/xyl_ps/scigym/ScienceGym');sys.path.insert(0,str(root/'simulation/g1_cooling_demo'))
from convex_cells import clean
link=sys.argv[1];out=Path('/tmp/sciencegym-distal-approx')/link;out.mkdir(parents=True,exist_ok=False)
source=root/'assets/unitree_g1_inspire_v1/vendor/unitree_ros/meshes'/(link+'.STL');s=clean(trimesh.load(source,force='mesh'));parts=s.split(only_watertight=False);core=trimesh.util.concatenate([p for p in parts if p.is_watertight and len(p.faces)>20 and abs(p.volume)>1e-10]);assert core.is_volume
core.export(out/'input.ply');params=dict(threshold=.00005,real_metric=True,max_convex_hull=512,resolution=2000,mcts_nodes=8,mcts_iterations=50,mcts_max_depth=4,seed=42,preprocess_mode='off');coacd.set_log_level('warn');started=time.monotonic();print('begin',link,flush=True)
parts=coacd.run_coacd(coacd.Mesh(core.vertices,core.faces),**params);rows=[]
for i,(v,f) in enumerate(parts):
 p=out/f'{i:05d}.stl';m=trimesh.Trimesh(v,f,process=True).convex_hull;m.export(p);rows.append(dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),volume_m3=float(m.volume)))
r=dict(scope='Approximate candidate only; no model integration or global error guarantee.',link=link,source_path=str(source.relative_to(root)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),input_sha256=hashlib.sha256((out/'input.ply').read_bytes()).hexdigest(),source_volume_m3=float(s.volume),input_volume_m3=float(core.volume),parameters=params,pieces=rows,seconds=time.monotonic()-started,coacd_version=importlib.metadata.version('coacd'),qualified=False)
(out/'candidate.json').write_text(json.dumps(r,indent=2)+'\n');print('finished',link,'pieces',len(rows),'seconds',r['seconds'],flush=True)
