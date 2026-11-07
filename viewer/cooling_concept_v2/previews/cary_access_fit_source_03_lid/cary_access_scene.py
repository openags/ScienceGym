"""Complete laboratory planning scene with independently movable Cary covers."""
import json
import numpy as np
import trimesh
from optical_delivery import DeliveryScene
from optical_choreography import HERE
from source_geometry import ROOT,ASSETS


def translation(xyz):
    value=np.eye(4);value[:3,3]=xyz;return value


class CaryAccessScene(DeliveryScene):
    def __init__(self,local_only=False):
        if local_only:
            self.setup=json.loads((HERE/'optical_setup.json').read_text());self.obstacles=trimesh.collision.CollisionManager()
            for identity in ['cary','dra']:
                asset=ASSETS[identity];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
                for name in source.graph.nodes_geometry:
                    node,key=source.graph[name];placed=translation(asset['position_m'])@np.array(self.setup['parts'].get(identity,{}).get(name,{}).get('matrix',np.eye(4)))@node
                    self.obstacles.add_object(identity+'::'+name,source.geometry[key],placed)
        else:super().__init__()
        self.interfaces=json.loads((ROOT/'assets/cary_5000_v1/interfaces.json').read_text())
        self.cary_source=trimesh.load(ROOT/ASSETS['cary']['geometry'],force='scene',process=False)
        self.cover_names=self.interfaces['extension_cover_parts']
        self.lid_names=self.interfaces['sliding_lid_parts']
        self.access_rest={}
        for name in self.cover_names+self.lid_names:
            local,_=self.cary_source.graph[name]
            explicit=self.setup['parts']['cary'].get(name)
            self.access_rest[name]=translation(ASSETS['cary']['position_m'])@(np.array(explicit['matrix']) if explicit else np.eye(4))@local
        normal=np.array(ASSETS['cary']['normalization_matrix'])
        self.lid_handle=(translation(ASSETS['cary']['position_m'])@normal@np.r_[.185,-.29125,.370,1])[:3]
        n='extension_pull_bar';_,key=self.cary_source.graph[n]
        self.cover_handle=trimesh.transform_points(self.cary_source.geometry[key].vertices,self.access_rest[n]).mean(axis=0)
        self.access_matrices={};self.set_access()
        self.moving_access=trimesh.collision.CollisionManager()
        for name in self.cover_names+self.lid_names:
            _,key=self.cary_source.graph[name]
            self.moving_access.add_object('moving::'+name,self.cary_source.geometry[key],self.access_matrices[name])

    def set_access(self,lid=0.,cover=None):
        cover=np.eye(4) if cover is None else np.asarray(cover)
        for name,rest in self.access_rest.items():
            pose=(translation([0,lid,0]) if name in self.lid_names else cover)@rest
            self.obstacles.set_transform('cary::'+name,pose)
            self.access_matrices[name]=pose

    def access_clearance(self,part):
        names=self.lid_names if part=='lid' else self.cover_names
        for name in self.cover_names+self.lid_names:
            self.moving_access.set_transform('moving::'+name,self.access_matrices[name])
        _,pairs,contacts=self.moving_access.in_collision_other(self.obstacles,return_names=True,return_data=True)
        failures=[]
        for c in contacts:
            moving=next((n for n in c.names if n.startswith('moving::')),None)
            if moving is None or moving.split('::',1)[1] not in names:continue
            other=next(n for n in c.names if n!=moving)
            if other in ['cary::'+n for n in names]:continue
            if abs(float(c.depth))>1e-7:failures.append(dict(parts=sorted(c.names),depth_m=float(c.depth)))
        return failures

    def local_obstacles(self):
        manager=trimesh.collision.CollisionManager()
        sources={identity:trimesh.load(ROOT/ASSETS[identity]['geometry'],force='scene',process=False) for identity in ['cary','dra']}
        for name,record in self.obstacles._objs.items():
            if name.startswith(('cary::','dra::')):
                obj=record['obj'];pose=np.eye(4);pose[:3,:3]=obj.getRotation();pose[:3,3]=obj.getTranslation()
                identity,part=name.split('::',1);source=sources[identity];_,key=source.graph[part]
                manager.add_object(name,source.geometry[key],pose)
        return manager
