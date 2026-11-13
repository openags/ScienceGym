"""Cary forceps pickup in the existing access episode's complete laboratory.

The additional ordinary tray and long forceps are explicit proposed initial
equipment. Preserve the original short tweezers and both optical witnesses at
their actual access-scene poses. This scene supplies planning geometry only.
"""
import hashlib
import json
import numpy as np
import trimesh
from cary_tool_scene import CaryToolScene
from optical_choreography import HERE
from source_geometry import ROOT
from tweezers_geometry import meshes as short_tool_meshes


class CaryToolPickupScene(CaryToolScene):
    def __init__(self,staging_path='previews/long_forceps_staging_07/staging.json'):
        staging=json.loads((HERE/staging_path).read_text());assert staging['passed']
        closure=json.loads((HERE/staging['profile']).read_text());assert closure['passed']
        super().__init__(closure['palm_matrix'],np.eye(4))
        self.long_staging=staging;self.long_profile=closure
        self.access_episode=json.loads((HERE/'cary_access_episode.json').read_text())
        final=self.access_episode['segments'][-1]['rows'][-1]
        self.set_access(lid=final['lid_m'],cover=final['cover_matrix'])
        initial=self.access_episode['initial_scene']['groups']
        short_pose=np.array(initial['tweezers_white']).reshape(4,4).T
        for name,mesh in short_tool_meshes(0.).items():
            self.obstacles.add_object('tweezers_white::'+name,mesh,short_pose)
        self.specimen_rest={kind:np.array(initial['optical_witness_'+kind]).reshape(4,4).T for kind in self.specimens}
        self.tool_rest=np.array(staging['tool_world_matrix'])
        self.tool_T_palm=np.array(closure['palm_matrix'])
        self.palm_T_tool=np.linalg.inv(self.tool_T_palm)
        assert np.max(abs(self.tool_rest@self.tool_T_palm-np.array(staging['palm_matrix'])))<1e-12
        assert hashlib.sha256((ROOT/staging['tray_geometry']).read_bytes()).hexdigest()==staging['tray_geometry_sha256']
        source=trimesh.load(ROOT/staging['tray_geometry'],force='scene',process=False)
        self.long_tray=trimesh.collision.CollisionManager();self.long_tray_parts={}
        self.long_tray_pose=np.eye(4);self.long_tray_pose[:3,3]=staging['tray_position_m']
        for name in source.graph.nodes_geometry:
            local,key=source.graph[name];pose=self.long_tray_pose@local;mesh=source.geometry[key]
            identity=staging['tray_instance_id']+'::'+name
            self.long_tray.add_object(identity,mesh,pose);self.long_tray_parts[identity]=(mesh,pose)
        _,pairs=self.long_tray.in_collision_other(self.obstacles,return_names=True)
        if pairs:raise ValueError('New tray intersects existing laboratory: '+str(sorted(pairs)))
        for name,(mesh,pose) in self.long_tray_parts.items():self.obstacles.add_object(name,mesh,pose)

    def state(self,base,q,tool_held=False,closure=0.,**options):
        return super().state(base,q,tool_held=tool_held,closure=closure,**options)

    def hand_q(self,closure):
        rows=self.long_profile['rows'];values=[r['closure'] for r in rows]
        if not 0<=closure<=1:raise ValueError('Long-tool closure outside [0,1]')
        return {n:float(np.interp(closure,values,[r['q'][n] for r in rows])) for n in rows[0]['q']}
