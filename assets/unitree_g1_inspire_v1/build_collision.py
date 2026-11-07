"""Decompose concave palm collision meshes; preserve source visual geometry."""
import importlib.metadata
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import coacd
import trimesh
from audit import sha

HERE=Path(__file__).resolve().parent


def build():
    coacd.set_log_level('warn')
    params=dict(threshold=.0005,real_metric=True,max_convex_hull=256,resolution=1000,
                mcts_nodes=8,mcts_iterations=25,mcts_max_depth=3,seed=42)
    dest=HERE/'collision_components';dest.mkdir(exist_ok=True)
    def hand(side):
        source=HERE/'vendor/unitree_ros/meshes'/(side+'_base_link.STL')
        mesh=trimesh.load(source,force='mesh')
        files=[]
        components=sorted(mesh.split(),key=lambda p:len(p.faces),reverse=True)
        for component_index,component in enumerate(components):
            # Do not spend the palm's decomposition budget on disconnected
            # screws/motors: preserve every component, with its own partition.
            if len(component.faces)>5000:
                parts=coacd.run_coacd(coacd.Mesh(component.vertices,component.faces),**params)
            else:
                hull=component.convex_hull;parts=[(hull.vertices,hull.faces)]
            for i,(vertices,faces) in enumerate(parts):
                path=dest/f'{side}_component_{component_index:02}_{i:03}.stl'
                piece=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
                assert piece.is_convex
                piece.export(path)
                files.append(dict(path=str(path.relative_to(HERE)),sha256=sha(path),bounds_m=piece.bounds.tolist()))
        print(json.dumps(dict(side=side,pieces=len(files))),flush=True)
        return dict(link=side+'_base_link',source_path=str(source.relative_to(HERE)),source_sha256=sha(source),source_components=len(components),pieces=files)
    with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(hand,['left','right']))
    report=dict(schema_version=1,method='CoACD approximate convex decomposition',version=importlib.metadata.version('coacd'),
      parameters=params,builder_sha256=sha(__file__),items=records,
      source='https://github.com/SarahWeiii/CoACD',scope='Connected components retained. Large shells decomposed with requested 0.5 mm threshold; smaller components use their convex hulls. No global error guarantee.',
      visual_geometry_changed=False,physical_contact_qualified=False)
    (HERE/'collision.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':build()
