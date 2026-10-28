"""Package/rebuild approximate convex thumb contacts from official STL solids."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil

import coacd
import trimesh

HERE=Path(__file__).resolve().parent
PARAMETERS=dict(threshold=.0001,real_metric=True,max_convex_hull=128,resolution=2000,
                mcts_nodes=8,mcts_iterations=50,mcts_max_depth=4,seed=42,preprocess_mode='off')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out,adopt=None):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use an empty geometry output directory')
    coacd.set_log_level('warn');records=[]
    for side in ['left','right']:
        source=HERE/'vendor/unitree_ros/meshes'/(side+'_thumb_2.STL')
        mesh=trimesh.load(source,force='mesh');dest=out/side;dest.mkdir()
        if adopt:
            receipt=json.loads((Path(adopt)/(side+'.json')).read_text())
            if receipt['parameters']!=PARAMETERS or receipt['source_sha256']!=sha(source):
                raise ValueError('Candidate parameters/source differ from this package')
            files=sorted((Path(adopt)/side).glob('*.stl'))
            if len(files)!=receipt['cells']:raise ValueError('Candidate piece count differs')
            for path in files:shutil.copyfile(path,dest/path.name)
        else:
            parts=coacd.run_coacd(coacd.Mesh(mesh.vertices,mesh.faces),**PARAMETERS)
            for i,(v,f) in enumerate(parts):trimesh.Trimesh(v,f,process=True).export(dest/f'{i:05d}.stl')
        pieces=[];volume=0.
        for path in sorted(dest.glob('*.stl')):
            part=trimesh.load(path,force='mesh')
            # MuJoCo uses this vertex hull regardless of exported triangle
            # topology. Rebuild it explicitly after float32 STL serialization.
            part=part.convex_hull
            if not part.is_convex or not part.is_volume:raise ValueError('Invalid convex piece')
            part.export(path)
            volume+=part.volume
            pieces.append(dict(path=str(path.relative_to(HERE)),sha256=sha(path)))
        records.append(dict(link=side+'_thumb_2',source_path=str(source.relative_to(HERE)),
            source_sha256=sha(source),source_volume_m3=float(mesh.volume),
            single_hull_volume_m3=float(mesh.convex_hull.volume),piece_volume_sum_m3=float(volume),pieces=pieces))
    manifest=dict(schema_version=1,method='CoACD approximate source mesh partition',
        coacd_version=importlib.metadata.version('coacd'),parameters=PARAMETERS,items=records,
        packager_sha256=sha(__file__),adopted_candidate_directory=str(adopt) if adopt else None,
        source_visuals_changed=False,body_inertias_changed=False,joint_limits_changed=False,
        global_error_bound_proved=False,physical_contact_qualified=False,
        exported_triangle_topology_rebuilt_as_vertex_hull=True,
        scope='Replaces each filled thumb-2 hull with source-derived pieces. The 128-piece cap can prevent achieving the requested 0.1 mm metric; selected posture checks do not qualify the full joint range.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),pieces=[len(r['pieces']) for r in records])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--adopt');a=p.parse_args();build(a.out,a.adopt)
