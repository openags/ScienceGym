"""Independent exact-mesh inspection of the installed optical initial state."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

from source_geometry import ROOT, ASSETS

HERE=Path(__file__).resolve().parent


def review():
    config=json.loads((HERE/'optical_setup.json').read_text())
    managers={};bounds={};meshes={}
    for identity in ['cary','dra','nicolet','pike']:
        asset=ASSETS[identity]
        assert hashlib.sha256((ROOT/asset['geometry']).read_bytes()).hexdigest()==config['source_geometry_sha256'][identity]
        source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
        manager=trimesh.collision.CollisionManager();managers[identity]=manager;meshes[identity]={}
        base=np.eye(4);base[:3,3]=asset['position_m']
        for name in source.graph.nodes_geometry:
            transform,key=source.graph[name]
            override=config['parts'].get(identity,{}).get(name)
            if override:transform=np.asarray(override['matrix'])@transform
            transform=base@transform
            mesh=source.geometry[key]
            manager.add_object(name,mesh,transform)
            vertex=trimesh.transform_points(mesh.vertices,transform)
            bounds[identity+'::'+name]=[vertex.min(0).tolist(),vertex.max(0).tolist()]
            meshes[identity][name]=(mesh,transform)
    checks=[]
    for accessory,instrument in [('dra','cary'),('pike','nicolet')]:
        hit,pairs,contacts=managers[accessory].in_collision_other(managers[instrument],return_names=True,return_data=True)
        checks.append(dict(accessory=accessory,instrument=instrument,intersections=[list(p) for p in sorted(pairs)],
                           maximum_reported_depth_m=max([float(c.depth) for c in contacts],default=0)))
    # Reference/sample-port relation, kept separate from whole-module fitting.
    for identity,parts in [('dra',['large_PTFE_reference','large_reference_holder','reference_identification']),
                           ('pike',['gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face'])]:
        reference=trimesh.collision.CollisionManager();module=trimesh.collision.CollisionManager()
        for name,(mesh,transform) in meshes[identity].items():
            (reference if name in parts else module).add_object(name,mesh,transform)
        hit,pairs,contacts=reference.in_collision_other(module,return_names=True,return_data=True)
        checks.append(dict(accessory=identity,instrument='own_reference',intersections=[list(p) for p in sorted(pairs)],
                           maximum_reported_depth_m=max([float(c.depth) for c in contacts],default=0)))
    report=dict(scope='Static source-mesh fit only; all contacts retained for explicit review, no installation or optical qualification',
                setup_sha256=hashlib.sha256((HERE/'optical_setup.json').read_bytes()).hexdigest(),
                verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checks=checks,bounds=bounds)
    (HERE/'previews/optical_setup_review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':review()
