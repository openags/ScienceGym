"""Planning scene for identified witness delivery between optical workstations.

The complete frozen laboratory supplies static obstacles. The planning robot
still omits ankle housings; independent full-body, floor and source-FK review
is required after composition. Tools start at the declared FTIR staging.
"""
import gzip
import json
import numpy as np
import trimesh
from optical_choreography import Scene,HERE
from source_geometry import manifest_for_export
from audit_geometry import ARTICULATED,matrix,mesh_scene,joined


class DeliveryScene(Scene):
    def __init__(self):
        super().__init__()
        folder=HERE/'audits/optical_exchange_01'
        manifest=manifest_for_export(folder);receipt=json.loads((folder/'export.json').read_text())
        with gzip.open(folder/'frames.jsonl.gz','rt') as stream:frame=json.loads(next(stream))
        self.obstacles=trimesh.collision.CollisionManager()
        source=mesh_scene(manifest['architecture']['path'])
        for name in source.graph.nodes_geometry:
            transform,key=source.graph[name];self.obstacles.add_object('room::'+name,source.geometry[key],transform)
        explicit={(part['asset'],part['name']):matrix(part['matrix']) for part in frame['parts']}
        for asset in manifest['assets']:
            identity=asset['id']
            if identity in ['g1','tweezers_white'] or identity.startswith('optical_witness_'):continue
            source=mesh_scene(asset['geometry']);group=matrix(frame['groups'][identity])
            if identity in ARTICULATED:
                for name in source.graph.nodes_geometry:
                    transform,key=source.graph[name]
                    self.obstacles.add_object(identity+'::'+name,source.geometry[key],explicit.get((identity,name),group@transform))
            else:self.obstacles.add_object(identity,joined(source),group)
        for item in receipt['scene']['extraGeometry']:
            mesh=trimesh.Trimesh(vertices=np.array(item['vertices']).reshape(-1,3),faces=np.array(item['indices']).reshape(-1,3),process=False)
            self.obstacles.add_object('extra::'+item['id'],mesh,matrix(frame['extra_matrices'][item['id']]))
        self.manifest=manifest
        self.cary_staging={}
        for kind in ['white','black']:
            asset=next(a for a in manifest['assets'] if a['id']=='optical_witness_'+kind)
            pose=np.eye(4);pose[:3,3]=asset['position_m'];self.cary_staging[kind]=pose
        self.specimen_rest=dict(self.cary_staging)
