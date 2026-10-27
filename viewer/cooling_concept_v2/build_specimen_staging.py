"""Install identified optical witnesses at supported Cary-bench staging positions."""
import hashlib,json
from pathlib import Path
import numpy as np
import trimesh
from source_geometry import ROOT

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'runtime_scene.json';runtime=json.loads(path.read_text());setup=json.loads((HERE/'optical_setup.json').read_text())
    package=ROOT/'assets/cooling_optical_specimens_v1';data=json.loads((package/'manifest.json').read_text())
    review=json.loads((package/'assembly_review.json').read_text());assert review['passed']
    runtime['assets']=[a for a in runtime['assets'] if not a['id'].startswith('optical_witness_')]
    obstacles=trimesh.collision.CollisionManager()
    source=trimesh.load(ROOT/runtime['architecture']['path'],force='scene',process=False);bench=None
    for name in source.graph.nodes_geometry:
        transform,key=source.graph[name];obstacles.add_object('room::'+name,source.geometry[key],transform)
        if name=='cary_bench_top':
            mesh=source.geometry[key].copy();mesh.apply_transform(transform);bench=mesh.bounds
    if bench is None:
        names=[n for n in source.graph.nodes_geometry if 'cary_bench' in n and ('top' in n or 'worktop' in n)];assert len(names)==1,names
        transform,key=source.graph[names[0]];mesh=source.geometry[key].copy();mesh.apply_transform(transform);bench=mesh.bounds
    for asset in runtime['assets']:
        if asset['id']=='g1':continue
        scene=trimesh.load(ROOT/asset['geometry'],force='scene',process=False);base=np.eye(4);base[:3,3]=asset['position_m']
        for name in scene.graph.nodes_geometry:
            transform,key=scene.graph[name]
            if name in setup['parts'].get(asset['id'],{}):transform=np.array(setup['parts'][asset['id']][name]['matrix'])@transform
            obstacles.add_object(asset['id']+'::'+name,scene.geometry[key],base@transform)
    rows=[]
    for i,asset in enumerate(data['assets']):
        position=[3.08+.07*i,8.20,.850001];source=trimesh.load(ROOT/asset['path'],force='scene',process=False);base=np.eye(4);base[:3,3]=position
        witness=trimesh.collision.CollisionManager()
        for name in source.graph.nodes_geometry:
            transform,key=source.graph[name];witness.add_object(name,source.geometry[key],base@transform)
        _,pairs=witness.in_collision_other(obstacles,return_names=True);assert not pairs,sorted(pairs)
        bounds=source.bounds+np.array(position);margin=float(min(*(bounds[0,:2]-bench[0,:2]),*(bench[1,:2]-bounds[1,:2])))
        gap=float(bounds[0,2]-bench[1,2]);assert margin>.05 and 0<=gap<2e-6
        record=dict(id=asset['id'],label=('白色' if i==0 else '黑色')+'铜质光学试片 · 25 mm',resource_id='optical_witness:'+('white' if i==0 else 'black'),station='optics_cary',geometry=asset['path'],geometry_sha256=asset['sha256'],position_m=position,yaw_rad=0,normalized_bounds_m=source.bounds.tolist(),normalization_matrix=np.eye(4).tolist(),scale=[1,1,1],part_count=len(asset['part_names']),part_names=asset['part_names'],status='geometry-reviewed inferred optical specimen; manipulation pending',source_record='assets/cooling_optical_specimens_v1/manifest.json',lineage=asset['lineage'])
        runtime['assets'].append(record);rows.append(dict(id=asset['id'],position_m=position,bench_bounds_m=bench.tolist(),minimum_xy_support_margin_m=margin,nominal_support_gap_m=gap,environment_intersections=[]))
    runtime['development_scene_revision']['optical_specimens']=dict(manifest='assets/cooling_optical_specimens_v1/manifest.json',staging='viewer/cooling_concept_v2/specimen_staging.json',scope='Identity-preserving optical witnesses; inferred dimensions and supports, no executed handling or measurement claim')
    output=dict(scope=__doc__,passed=True,rows=rows,generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),witness_manifest_sha256=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest(),original_scene_sha256=hashlib.sha256((ROOT/'assets/cooling_lab_v1/scene.json').read_bytes()).hexdigest(),optical_setup_sha256=hashlib.sha256((HERE/'optical_setup.json').read_bytes()).hexdigest(),limits='Static non-overlap and rectangular benchtop footprint only; no robot handling, force or optical qualification')
    path.write_text(json.dumps(runtime,indent=2,ensure_ascii=False)+'\n');(HERE/'specimen_staging.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output),flush=True)


if __name__=='__main__':main()
