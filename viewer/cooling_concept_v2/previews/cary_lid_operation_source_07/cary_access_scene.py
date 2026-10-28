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
    def __init__(self,local_only=False,cover_candidate=False):
        if local_only:
            self.setup=json.loads((HERE/'optical_setup.json').read_text());self.obstacles=trimesh.collision.CollisionManager()
            for identity in ['cary','dra']:
                asset=ASSETS[identity];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
                for name in source.graph.nodes_geometry:
                    node,key=source.graph[name];placed=translation(asset['position_m'])@np.array(self.setup['parts'].get(identity,{}).get(name,{}).get('matrix',np.eye(4)))@node
                    self.obstacles.add_object(identity+'::'+name,source.geometry[key],placed)
        else:super().__init__()
        self.interfaces=json.loads((ROOT/'assets/cary_5000_v1/interfaces.json').read_text())
        self.cary_geometry=('assets/cary_5000_v1/revisions/cover_clearance/prepared_cary_candidate.glb' if cover_candidate=='reliefs' else 'assets/cary_5000_v1/revisions/cover_clearance/prepared_cary_operable_cover.glb') if cover_candidate else ASSETS['cary']['geometry']
        self.cary_source=trimesh.load(ROOT/self.cary_geometry,force='scene',process=False)
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
        if cover_candidate:
            for n in self.cover_names:
                _,key=self.cary_source.graph[n]
                self.obstacles.remove_object('cary::'+n);self.obstacles.add_object('cary::'+n,self.cary_source.geometry[key],self.access_rest[n])
        self.access_matrices={};self.set_access()
        self.moving_access={};self.access_meshes={}
        for identity,names in [('lid',self.lid_names),('cover',self.cover_names)]:
            manager=trimesh.collision.CollisionManager()
            for name in names:
                _,key=self.cary_source.graph[name];mesh=self.cary_source.geometry[key];self.access_meshes[name]=mesh
                manager.add_object('moving::'+name,mesh,self.access_matrices[name])
            self.moving_access[identity]=manager

    def set_access(self,lid=0.,cover=None):
        cover=np.eye(4) if cover is None else np.asarray(cover)
        for name,rest in self.access_rest.items():
            pose=(translation([0,lid,0]) if name in self.lid_names else cover)@rest
            self.obstacles.set_transform('cary::'+name,pose)
            self.access_matrices[name]=pose

    def access_clearance(self,part):
        names=self.lid_names if part=='lid' else self.cover_names
        manager=self.moving_access[part]
        for name in names:
            manager.set_transform('moving::'+name,self.access_matrices[name])
            self.obstacles.remove_object('cary::'+name)
        try:_,pairs,contacts=manager.in_collision_other(self.obstacles,return_names=True,return_data=True)
        finally:
            for name in names:self.obstacles.add_object('cary::'+name,self.access_meshes[name],self.access_matrices[name])
        failures={};bounded={}
        for c in contacts:
            moving=next((n for n in c.names if n.startswith('moving::')),None)
            if moving is None or moving.split('::',1)[1] not in names:continue
            other=next(n for n in c.names if n!=moving)
            pair=tuple(sorted(c.names));depth=abs(float(c.depth));row=dict(parts=list(pair),maximum_reported_depth_m=depth)
            # The nominal side sheets meet the rail and hinge end faces in X.
            # Verify their actual source-mesh normal overlap, rather than
            # accepting FCL's tangential depth for coincident triangle faces.
            moving_name=moving.split('::',1)[1]
            bearing=moving_name.startswith('extension_cover_side_') and (other.startswith('cary::extension_base_rail_') or other=='cary::extension_hinge_bar')
            if bearing:
                static_name=other.split('::',1)[1];node,key=self.cary_source.graph[static_name]
                pose=translation(ASSETS['cary']['position_m'])@np.array(self.setup['parts']['cary'][static_name]['matrix'])@node
                a=trimesh.transform_points(self.access_meshes[moving_name].vertices,self.access_matrices[moving_name]);b=trimesh.transform_points(self.cary_source.geometry[key].vertices,pose)
                overlap=float(min(a[:,0].max(),b[:,0].max())-max(a[:,0].min(),b[:,0].min()))
                if overlap<=1e-6:
                    row['normal_overlap_m']=overlap;bounded[pair]=row;continue
            if depth>1e-7 and depth>failures.get(pair,{}).get('maximum_reported_depth_m',-1):failures[pair]=row
        self.last_bounded_contacts=list(bounded.values())
        return list(failures.values())

    def local_obstacles(self):
        manager=trimesh.collision.CollisionManager()
        sources={'cary':self.cary_source,'dra':trimesh.load(ROOT/ASSETS['dra']['geometry'],force='scene',process=False)}
        for name,record in self.obstacles._objs.items():
            if name.startswith(('cary::','dra::')):
                obj=record['obj'];pose=np.eye(4);pose[:3,:3]=obj.getRotation();pose[:3,3]=obj.getTranslation()
                identity,part=name.split('::',1);source=sources[identity];_,key=source.graph[part]
                manager.add_object(name,source.geometry[key],pose)
        return manager
